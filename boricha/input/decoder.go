package input

import (
	"bytes"
	"unicode/utf8"
)

// 붙여넣기의 앞뒤 표시. 터미널이 DEC 모드 2004 로 켜졌을 때만 보내 준다.
const (
	pasteStart = "\x1b[200~"
	pasteEnd   = "\x1b[201~"
)

// Decoder 는 바이트를 사건으로 바꾸는 상태 기계다.
//
// 핵심 어려움은 "바이트가 한 덩어리로 오지 않는다" 는 것이다. read 한 번이
// 방향키의 세 바이트 중 두 개만 줄 수도 있고, 키 열 개를 한꺼번에 줄 수도 있다.
// 그래서 Feed 는 해석되는 만큼만 사건으로 만들고, 나머지는 안에 남겨 둔다.
// 어디서 잘려 들어와도 결과가 같다는 것이 이 타입의 유일한 계약이다.
//
// 시간 개념은 여기 없다. ESC 하나만 와 있을 때 "esc 키였다" 고 판정하는 시계는
// Reader 가 들고 있고, Decoder 는 Flush 를 받는 순간 확정한다. 상태 기계와 시계를
// 갈라 놓으면 이 파일 전체를 시계 없이 시험할 수 있다.
type Decoder struct {
	buf     []byte // 아직 사건이 되지 못한 나머지
	inPaste bool   // 붙여넣기 안쪽인가
	paste   []byte // 붙여넣기로 모으는 중인 글
}

// Feed 는 새로 읽은 바이트를 넣고, 그것으로 만들 수 있는 사건을 전부 돌려준다.
func (d *Decoder) Feed(p []byte) []Msg {
	d.buf = append(d.buf, p...)
	return d.drain(false)
}

// Flush 는 "더 안 온다" 고 알린다. 판단을 미뤄 두었던 ESC 가 esc 키로 확정된다.
//
// 붙여넣기 도중이면 아무것도 확정하지 않는다 — 붙여넣기는 끝 표시로만 끝난다.
// 시간으로 끊으면 큰 글을 붙여넣을 때 글이 두 동강 난다.
func (d *Decoder) Flush() []Msg { return d.drain(true) }

// Pending 은 판단을 미뤄 둔 바이트가 있는지. Reader 가 시계를 걸지 말지 정하는 데 쓴다.
func (d *Decoder) Pending() bool { return len(d.buf) > 0 || d.inPaste }

// drain 은 버퍼 앞에서부터 해석되는 만큼 사건을 뽑아낸다.
// final 이 참이면 더 기다리지 않고, 애매한 것은 그 자리에서 확정하거나 버린다.
func (d *Decoder) drain(final bool) []Msg {
	var out []Msg
	for len(d.buf) > 0 {
		if d.inPaste {
			done, msg := d.eatPaste()
			if msg != nil {
				out = append(out, msg)
			}
			if !done {
				return out
			}
			continue
		}
		msg, n := d.one(final)
		if n == 0 {
			break // 바이트가 더 필요하다
		}
		d.buf = d.buf[n:]
		if msg != nil {
			out = append(out, msg)
		}
	}
	return out
}

// eatPaste 는 붙여넣기 끝 표시를 찾을 때까지 글을 모은다.
//
// 끝 표시가 아직 없으면, 끝 표시가 걸쳐 있을 가능성 때문에 마지막 5바이트는 남겨 둔다
// (끝 표시는 6바이트이므로, 5바이트까지는 그 앞부분일 수 있다).
func (d *Decoder) eatPaste() (done bool, msg Msg) {
	if i := bytes.Index(d.buf, []byte(pasteEnd)); i >= 0 {
		d.paste = append(d.paste, d.buf[:i]...)
		d.buf = d.buf[i+len(pasteEnd):]
		d.inPaste = false
		m := PasteMsg(string(d.paste))
		d.paste = d.paste[:0]
		return true, m
	}
	if keep := len(pasteEnd) - 1; len(d.buf) > keep {
		cut := len(d.buf) - keep
		d.paste = append(d.paste, d.buf[:cut]...)
		d.buf = d.buf[cut:]
	}
	return false, nil
}

// one 은 버퍼 앞에서 사건 하나를 읽는다.
// 돌려주는 n 이 0 이면 "바이트가 더 필요하다", n>0 이면 그만큼 소비했다는 뜻이다.
// msg 가 nil 이면서 n>0 이면 "소비했지만 사건은 아니다"(예: 붙여넣기 시작 표시).
func (d *Decoder) one(final bool) (Msg, int) {
	b := d.buf
	switch c := b[0]; {
	case c == 0x1b:
		return d.escape(final)
	case c == 0x7f:
		// 백스페이스는 0x08(BS)이 아니라 0x7f(DEL)로 온다. 유닉스 터미널의 오랜 관례다.
		return KeyMsg{Code: KeyBackspace}, 1
	case c == 0x08:
		// 진짜 0x08 이 오면 ctrl+백스페이스로 본다. 터미널마다 다르니 절대적이지는 않다.
		return KeyMsg{Code: KeyBackspace, Mod: ModCtrl}, 1
	case c == '\t':
		return KeyMsg{Code: KeyTab}, 1
	case c == '\r':
		return KeyMsg{Code: KeyEnter}, 1
	case c == 0x00:
		// NUL 은 ctrl+space(와 ctrl+@)로 온다. 둘을 구별할 방법이 없다.
		return KeyMsg{Code: KeySpace, Mod: ModCtrl}, 1
	case c < 0x20:
		// 제어 문자는 "글자의 상위 비트를 지운 것" 이다.
		// 0x01 → 'a'(0x61), 0x1c → '\\'(0x5c). 그래서 0x60 이나 0x40 을 더하면 원래 글자가 나온다.
		if c <= 0x1a {
			return KeyMsg{Code: rune(c) + 0x60, Mod: ModCtrl}, 1
		}
		return KeyMsg{Code: rune(c) + 0x40, Mod: ModCtrl}, 1
	}
	return d.rune(final)
}

// rune 은 UTF-8 글자 하나를 떼어 낸다.
//
// 한글 한 글자는 3바이트, 이모지는 4바이트다. 그 중간에서 read 가 끊기는 일은
// 실제로 일어나므로, 다 오지 않았으면 기다린다. 끝내 안 오면(또는 애초에 잘못된
// 바이트면) 버린다 — 안 버리면 그 뒤의 모든 입력이 영원히 막힌다.
func (d *Decoder) rune(final bool) (Msg, int) {
	b := d.buf
	if !utf8.FullRune(b) {
		if final {
			return nil, len(b)
		}
		return nil, 0
	}
	r, size := utf8.DecodeRune(b)
	if r == utf8.RuneError && size == 1 {
		return nil, 1
	}
	return KeyMsg{Code: r, Text: string(r)}, size
}

// escape 는 ESC 로 시작하는 것을 해석한다. 이 함수가 파서의 심장이다.
//
// ESC 하나는 그 자체로 esc 키일 수도 있고, 더 긴 시퀀스의 시작일 수도 있다.
// 바이트만 봐서는 구별할 수 없다 — 이것이 터미널 입력의 근본적인 모호함이다.
func (d *Decoder) escape(final bool) (Msg, int) {
	b := d.buf
	if len(b) == 1 {
		if final {
			return KeyMsg{Code: KeyEscape}, 1 // 뒤가 없었다 → esc 키였다
		}
		return nil, 0 // 아직 모른다. Reader 가 50 ms 를 세어 준다.
	}
	switch b[1] {
	case '[':
		return d.csi(final)
	case 'O':
		return d.ss3(final)
	case 0x1b:
		// ESC ESC. 어떤 시퀀스도 이렇게 시작하지 않으므로 앞의 것은 기다릴 필요가 없다.
		return KeyMsg{Code: KeyEscape}, 1
	}
	// ESC + 무언가 = alt + 그 무언가.
	// 옛 터미널이 8번째 비트를 못 써서 생긴 관례다(meta 키 → ESC 접두).
	// 뒤를 따로 해석해서 ModAlt 만 얹는다.
	sub := Decoder{buf: b[1:]}
	msg, n := sub.one(final)
	if n == 0 {
		return nil, 0
	}
	if k, ok := msg.(KeyMsg); ok {
		k.Mod |= ModAlt
		k.Text = "" // 조합키는 글자로 찍히지 않는다
		return k, n + 1
	}
	return msg, n + 1
}

// ss3 는 ESC O 로 시작하는 세 바이트짜리 키를 해석한다.
//
// 왜 두 가지 방식이 있는가. 터미널에는 "커서 키 응용 모드(DECCKM)" 라는 것이 있어서,
// 켜져 있으면 화살표를 ESC[A 대신 ESCOA 로 보낸다. 어느 쪽이 올지 우리가 정할 수 없으니
// 둘 다 받는다. F1~F4 도 이쪽으로 온다.
func (d *Decoder) ss3(final bool) (Msg, int) {
	b := d.buf
	if len(b) < 3 {
		if final {
			return UnknownMsg(string(b)), len(b)
		}
		return nil, 0
	}
	if code, ok := ss3Keys[b[2]]; ok {
		return KeyMsg{Code: code}, 3
	}
	return UnknownMsg(string(b[:3])), 3
}

var ss3Keys = map[byte]rune{
	'A': KeyUp, 'B': KeyDown, 'C': KeyRight, 'D': KeyLeft,
	'H': KeyHome, 'F': KeyEnd,
	'P': KeyF1, 'Q': KeyF2, 'R': KeyF3, 'S': KeyF4,
}

// csi 는 ESC [ 로 시작하는 시퀀스를 해석한다.
//
// 문법은 ECMA-48 이 정해 두었다:
//
//	ESC [ (매개변수 0x30–0x3F)* (중간 0x20–0x2F)* (마지막 0x40–0x7E)
//
// 마지막 바이트 하나가 명령의 이름이고, 앞의 숫자들이 인자다.
// 이 문법을 그대로 코드로 옮기면, 모르는 시퀀스도 "어디서 끝나는지" 는 알 수 있다.
// 그래서 처음 보는 시퀀스가 와도 그 길이만큼만 건너뛰고 다음 키로 넘어갈 수 있다.
func (d *Decoder) csi(final bool) (Msg, int) {
	b := d.buf
	i := 2
	for i < len(b) && b[i] >= 0x30 && b[i] <= 0x3f {
		i++
	}
	params := b[2:i]
	for i < len(b) && b[i] >= 0x20 && b[i] <= 0x2f {
		i++
	}
	if i >= len(b) {
		if final {
			return UnknownMsg(string(b)), len(b)
		}
		return nil, 0 // 마지막 바이트가 아직 안 왔다
	}
	fin := b[i]
	n := i + 1
	if fin < 0x40 || fin > 0x7e {
		// 문법에 맞지 않는다. 여기까지만 버리고 이 바이트부터 다시 본다.
		return UnknownMsg(string(b[:i])), i
	}

	// 마우스는 매개변수가 '<' 로 시작한다 (SGR 1006 인코딩).
	if len(params) > 0 && params[0] == '<' && (fin == 'M' || fin == 'm') {
		return sgrMouse(params[1:], fin == 'm'), n
	}

	nums := splitParams(params)
	mod := KeyMod(0)
	if len(nums) >= 2 {
		mod = modFromParam(nums[1])
	}

	switch fin {
	case 'A', 'B', 'C', 'D', 'H', 'F', 'P', 'Q', 'R', 'S':
		if code, ok := csiFinalKeys[fin]; ok {
			return KeyMsg{Code: code, Mod: mod}, n
		}
	case 'Z':
		// CSI Z 는 shift+tab 전용 시퀀스다(백탭).
		return KeyMsg{Code: KeyTab, Mod: ModShift}, n
	case 'I':
		return FocusMsg{}, n
	case 'O':
		return BlurMsg{}, n
	case '~':
		if len(nums) == 0 {
			break
		}
		switch nums[0] {
		case 200:
			d.inPaste = true
			return nil, n
		case 201:
			// 시작 없이 온 끝 표시. 조용히 버린다.
			return nil, n
		}
		if code, ok := csiTildeKeys[nums[0]]; ok {
			return KeyMsg{Code: code, Mod: mod}, n
		}
	}
	return UnknownMsg(string(b[:n])), n
}

var csiFinalKeys = map[byte]rune{
	'A': KeyUp, 'B': KeyDown, 'C': KeyRight, 'D': KeyLeft,
	'H': KeyHome, 'F': KeyEnd,
	'P': KeyF1, 'Q': KeyF2, 'R': KeyF3, 'S': KeyF4,
}

// CSI n ~ 계열. 번호가 띄엄띄엄한 것은 역사의 흔적이다 —
// 16, 22 번은 애초에 배정된 적이 없다(VT220 의 기능키 배열에서 비어 있던 자리).
var csiTildeKeys = map[int]rune{
	1: KeyHome, 2: KeyInsert, 3: KeyDelete, 4: KeyEnd, 5: KeyPgUp, 6: KeyPgDown,
	7: KeyHome, 8: KeyEnd,
	11: KeyF1, 12: KeyF2, 13: KeyF3, 14: KeyF4, 15: KeyF5,
	17: KeyF6, 18: KeyF7, 19: KeyF8, 20: KeyF9, 21: KeyF10,
	23: KeyF11, 24: KeyF12,
}

// modFromParam 은 CSI 의 두 번째 매개변수를 조합키 묶음으로 바꾼다.
//
// 규칙은 "1 을 뺀 값이 비트묶음" 이다: 1=shift, 2=alt, 4=ctrl.
// 그래서 ctrl+shift 는 1+4=5, 거기에 1을 더해 매개변수 6 으로 온다.
// 1 을 더해 두는 이유는 ECMA-48 에서 매개변수 0 이 "생략" 과 같기 때문이다.
func modFromParam(p int) KeyMod {
	if p < 2 {
		return 0
	}
	bits := p - 1
	var m KeyMod
	if bits&1 != 0 {
		m |= ModShift
	}
	if bits&2 != 0 {
		m |= ModAlt
	}
	if bits&4 != 0 {
		m |= ModCtrl
	}
	return m
}

// splitParams 는 "1;5" 같은 매개변수를 숫자 목록으로 바꾼다.
// 빈 자리는 0 이다 — ECMA-48 이 "생략은 기본값" 이라 정해 두었고, 그 기본값이 명령마다 다르다.
func splitParams(p []byte) []int {
	if len(p) == 0 {
		return nil
	}
	out := make([]int, 0, 4)
	cur, has := 0, false
	for _, c := range p {
		switch {
		case c >= '0' && c <= '9':
			cur = cur*10 + int(c-'0')
			has = true
		case c == ';':
			out = append(out, cur)
			cur, has = 0, false
		default:
			// '?', ':' 등 우리가 안 쓰는 부호는 건너뛴다
		}
	}
	if has || len(out) > 0 {
		out = append(out, cur)
	}
	return out
}
