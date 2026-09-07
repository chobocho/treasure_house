package input

import (
	"reflect"
	"testing"
)

func key(code rune, mod KeyMod) Msg { return KeyMsg{Code: code, Mod: mod} }

func text(s string, mod KeyMod) Msg {
	r := []rune(s)
	return KeyMsg{Code: r[0], Text: s, Mod: mod}
}

// 파서의 계약은 딱 하나다: 이 바이트열이 들어오면 이 사건들이 나온다.
// 그래서 표로 적는다. 표의 각 줄은 실제 터미널이 보내는 바이트 그대로다.
var decodeCases = []struct {
	name string
	in   string
	want []Msg
}{
	// ── 보통 글자 ────────────────────────────────────────────────
	{"글자 하나", "a", []Msg{text("a", 0)}},
	{"글자 여러 개", "abc", []Msg{text("a", 0), text("b", 0), text("c", 0)}},
	{"대문자", "A", []Msg{text("A", 0)}},
	{"숫자와 기호", "1!", []Msg{text("1", 0), text("!", 0)}},
	{"공백", " ", []Msg{text(" ", 0)}},

	// ── 한글과 이모지 (UTF-8 여러 바이트) ────────────────────────
	{"한글 한 글자", "한", []Msg{text("한", 0)}},
	{"한글 두 글자", "한글", []Msg{text("한", 0), text("글", 0)}},
	{"이모지", "🍵", []Msg{text("🍵", 0)}},
	{"한글과 영문 섞기", "a한b", []Msg{text("a", 0), text("한", 0), text("b", 0)}},

	// ── 제어 문자 ────────────────────────────────────────────────
	{"엔터", "\r", []Msg{key(KeyEnter, 0)}},
	{"탭", "\t", []Msg{key(KeyTab, 0)}},
	{"백스페이스(DEL)", "\x7f", []Msg{key(KeyBackspace, 0)}},
	{"ctrl+백스페이스(BS)", "\x08", []Msg{key(KeyBackspace, ModCtrl)}},
	{"ctrl+c", "\x03", []Msg{key('c', ModCtrl)}},
	{"ctrl+a", "\x01", []Msg{key('a', ModCtrl)}},
	{"ctrl+z", "\x1a", []Msg{key('z', ModCtrl)}},
	{"ctrl+space(NUL)", "\x00", []Msg{key(KeySpace, ModCtrl)}},
	{"ctrl+백슬래시", "\x1c", []Msg{key('\\', ModCtrl)}},
	{"줄바꿈은 ctrl+j", "\n", []Msg{key('j', ModCtrl)}},

	// ── CSI 화살표 ───────────────────────────────────────────────
	{"위", "\x1b[A", []Msg{key(KeyUp, 0)}},
	{"아래", "\x1b[B", []Msg{key(KeyDown, 0)}},
	{"오른쪽", "\x1b[C", []Msg{key(KeyRight, 0)}},
	{"왼쪽", "\x1b[D", []Msg{key(KeyLeft, 0)}},
	{"home(CSI H)", "\x1b[H", []Msg{key(KeyHome, 0)}},
	{"end(CSI F)", "\x1b[F", []Msg{key(KeyEnd, 0)}},

	// ── SS3 (커서 키 응용 모드) ──────────────────────────────────
	{"SS3 위", "\x1bOA", []Msg{key(KeyUp, 0)}},
	{"SS3 왼쪽", "\x1bOD", []Msg{key(KeyLeft, 0)}},
	{"SS3 F1", "\x1bOP", []Msg{key(KeyF1, 0)}},
	{"SS3 F4", "\x1bOS", []Msg{key(KeyF4, 0)}},

	// ── CSI 숫자 ~ 계열 ──────────────────────────────────────────
	{"insert", "\x1b[2~", []Msg{key(KeyInsert, 0)}},
	{"delete", "\x1b[3~", []Msg{key(KeyDelete, 0)}},
	{"pgup", "\x1b[5~", []Msg{key(KeyPgUp, 0)}},
	{"pgdown", "\x1b[6~", []Msg{key(KeyPgDown, 0)}},
	{"home(1~)", "\x1b[1~", []Msg{key(KeyHome, 0)}},
	{"end(4~)", "\x1b[4~", []Msg{key(KeyEnd, 0)}},
	{"F1(11~)", "\x1b[11~", []Msg{key(KeyF1, 0)}},
	{"F5(15~)", "\x1b[15~", []Msg{key(KeyF5, 0)}},
	{"F6(17~)", "\x1b[17~", []Msg{key(KeyF6, 0)}},
	{"F10(21~)", "\x1b[21~", []Msg{key(KeyF10, 0)}},
	{"F12(24~)", "\x1b[24~", []Msg{key(KeyF12, 0)}},

	// ── 조합키 (매개변수 ;N) ─────────────────────────────────────
	// N-1 이 비트묶음이다: 1=shift, 2=alt, 4=ctrl
	{"shift+tab", "\x1b[Z", []Msg{key(KeyTab, ModShift)}},
	{"shift+오른쪽", "\x1b[1;2C", []Msg{key(KeyRight, ModShift)}},
	{"alt+왼쪽", "\x1b[1;3D", []Msg{key(KeyLeft, ModAlt)}},
	{"ctrl+위", "\x1b[1;5A", []Msg{key(KeyUp, ModCtrl)}},
	{"ctrl+alt+위", "\x1b[1;7A", []Msg{key(KeyUp, ModCtrl|ModAlt)}},
	{"ctrl+alt+shift+위", "\x1b[1;8A", []Msg{key(KeyUp, ModCtrl|ModAlt|ModShift)}},
	{"ctrl+delete", "\x1b[3;5~", []Msg{key(KeyDelete, ModCtrl)}},

	// ── ESC 접두 = alt ───────────────────────────────────────────
	{"alt+a", "\x1ba", []Msg{key('a', ModAlt)}},
	{"alt+enter", "\x1b\r", []Msg{key(KeyEnter, ModAlt)}},
	{"alt+한", "\x1b한", []Msg{key('한', ModAlt)}},

	// ── 마우스 (SGR 1006) ────────────────────────────────────────
	// "\e[<b;x;yM" 은 누름, 소문자 m 은 뗌. 좌표는 1부터 오므로 0부터로 바꾼다.
	{"왼쪽 누름", "\x1b[<0;10;5M", []Msg{MouseMsg{X: 9, Y: 4, Button: MouseLeft, Action: MousePress}}},
	{"왼쪽 뗌", "\x1b[<0;10;5m", []Msg{MouseMsg{X: 9, Y: 4, Button: MouseLeft, Action: MouseRelease}}},
	{"가운데 누름", "\x1b[<1;1;1M", []Msg{MouseMsg{X: 0, Y: 0, Button: MouseMiddle, Action: MousePress}}},
	{"오른쪽 누름", "\x1b[<2;1;1M", []Msg{MouseMsg{X: 0, Y: 0, Button: MouseRight, Action: MousePress}}},
	{"휠 위", "\x1b[<64;3;4M", []Msg{MouseMsg{X: 2, Y: 3, Button: MouseWheelUp, Action: MousePress}}},
	{"휠 아래", "\x1b[<65;3;4M", []Msg{MouseMsg{X: 2, Y: 3, Button: MouseWheelDown, Action: MousePress}}},
	{"왼쪽 끌기", "\x1b[<32;7;8M", []Msg{MouseMsg{X: 6, Y: 7, Button: MouseLeft, Action: MouseMotion}}},
	{"버튼 없이 움직임", "\x1b[<35;7;8M", []Msg{MouseMsg{X: 6, Y: 7, Button: MouseNone, Action: MouseMotion}}},
	{"ctrl+왼쪽 누름", "\x1b[<16;2;2M", []Msg{MouseMsg{X: 1, Y: 1, Button: MouseLeft, Action: MousePress, Mod: ModCtrl}}},
	{"세 자리 좌표", "\x1b[<0;200;100M", []Msg{MouseMsg{X: 199, Y: 99, Button: MouseLeft, Action: MousePress}}},

	// ── 붙여넣기 (괄호 붙은 붙여넣기) ────────────────────────────
	{"붙여넣기", "\x1b[200~hi\x1b[201~", []Msg{PasteMsg("hi")}},
	{"여러 줄 붙여넣기", "\x1b[200~a\nb\x1b[201~", []Msg{PasteMsg("a\nb")}},
	{"한글 붙여넣기", "\x1b[200~보리차\x1b[201~", []Msg{PasteMsg("보리차")}},
	{"빈 붙여넣기", "\x1b[200~\x1b[201~", []Msg{PasteMsg("")}},
	{"붙여넣기 앞뒤 글자", "x\x1b[200~y\x1b[201~z",
		[]Msg{text("x", 0), PasteMsg("y"), text("z", 0)}},

	// ── 포커스 ───────────────────────────────────────────────────
	{"포커스 얻음", "\x1b[I", []Msg{FocusMsg{}}},
	{"포커스 잃음", "\x1b[O", []Msg{BlurMsg{}}},

	// ── 모르는 시퀀스 ────────────────────────────────────────────
	// 버리지 않고 그대로 돌려준다. 새 터미널이 무엇을 보내는지 볼 유일한 창이다.
	{"모르는 CSI", "\x1b[999z", []Msg{UnknownMsg("\x1b[999z")}},
	{"모르는 CSI 뒤에 글자", "\x1b[999za", []Msg{UnknownMsg("\x1b[999z"), text("a", 0)}},

	// ── 섞여 오는 경우 ───────────────────────────────────────────
	{"키를 빨리 여러 개", "\x1b[A\x1b[Ba", []Msg{key(KeyUp, 0), key(KeyDown, 0), text("a", 0)}},
	{"화살표와 한글", "\x1b[C한", []Msg{key(KeyRight, 0), text("한", 0)}},
}

func TestDecode(t *testing.T) {
	for _, c := range decodeCases {
		var d Decoder
		got := append(d.Feed([]byte(c.in)), d.Flush()...)
		if !reflect.DeepEqual(got, c.want) {
			t.Errorf("%s: Feed(%q)\n  나온 값  %#v\n  원하는 값 %#v", c.name, c.in, got, c.want)
		}
	}
}

// 바이트는 한 덩어리로 오지 않는다. 커널은 read 한 번에 무엇이든 줄 수 있고,
// 방향키 세 바이트가 두 번에 나뉘어 오는 일도 흔하다.
// **어디서 잘려도 결과가 같아야 한다** — 이것이 파서의 진짜 계약이다.
func TestDecodeSplitAtEveryBoundary(t *testing.T) {
	for _, c := range decodeCases {
		b := []byte(c.in)
		for cut := 0; cut <= len(b); cut++ {
			var d Decoder
			got := d.Feed(b[:cut])
			got = append(got, d.Feed(b[cut:])...)
			got = append(got, d.Flush()...)
			if !reflect.DeepEqual(got, c.want) {
				t.Errorf("%s: %q 를 %d 에서 자름\n  나온 값  %#v\n  원하는 값 %#v",
					c.name, c.in, cut, got, c.want)
				break
			}
		}
	}
}

// 한 바이트씩 흘려 넣어도 같아야 한다. 위 시험의 가장 지독한 형태다.
func TestDecodeByteByByte(t *testing.T) {
	for _, c := range decodeCases {
		var d Decoder
		var got []Msg
		for _, one := range []byte(c.in) {
			got = append(got, d.Feed([]byte{one})...)
		}
		got = append(got, d.Flush()...)
		if !reflect.DeepEqual(got, c.want) {
			t.Errorf("%s: 한 바이트씩\n  나온 값  %#v\n  원하는 값 %#v", c.name, got, c.want)
		}
	}
}

// ESC 한 바이트만 와 있을 때는 아직 아무것도 알 수 없다.
// 뒤에 '[' 가 오면 화살표고, 아무것도 안 오면 esc 키다.
// 그 "아무것도 안 옴" 을 판정하는 시계는 Reader 가 들고 있고,
// Decoder 는 Flush 를 받는 순간 확정한다.
func TestLoneEscapeNeedsFlush(t *testing.T) {
	var d Decoder
	if got := d.Feed([]byte{0x1b}); len(got) != 0 {
		t.Errorf("ESC 하나에 벌써 %#v 를 냈다", got)
	}
	if !d.Pending() {
		t.Error("Pending() 이 거짓 — 판단을 미룬 바이트가 있는데도")
	}
	got := d.Flush()
	want := []Msg{key(KeyEscape, 0)}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("Flush() = %#v, 원하는 값 %#v", got, want)
	}
	if d.Pending() {
		t.Error("Flush 뒤에도 Pending() 이 참")
	}
}

// ESC 다음에 또 ESC 가 오면, 앞의 것은 더 기다릴 필요가 없다.
// 어떤 시퀀스도 ESC ESC 로 시작하지 않기 때문이다.
func TestEscapeEscape(t *testing.T) {
	var d Decoder
	got := d.Feed([]byte("\x1b\x1b"))
	if want := []Msg{key(KeyEscape, 0)}; !reflect.DeepEqual(got, want) {
		t.Errorf("Feed(ESC ESC) = %#v, 원하는 값 %#v", got, want)
	}
	got = d.Flush()
	if want := []Msg{key(KeyEscape, 0)}; !reflect.DeepEqual(got, want) {
		t.Errorf("Flush() = %#v, 원하는 값 %#v", got, want)
	}
}

// 붙여넣기 도중에 Flush 가 오면(50 ms 조용했다는 뜻) 아직 끝난 것이 아니다.
// 붙여넣기는 끝 표시가 올 때까지 기다려야 한다 — 시간으로 끊으면 글이 두 동강 난다.
func TestFlushDuringPasteKeepsWaiting(t *testing.T) {
	var d Decoder
	d.Feed([]byte("\x1b[200~보리"))
	if got := d.Flush(); len(got) != 0 {
		t.Errorf("붙여넣는 중인데 Flush 가 %#v 를 냈다", got)
	}
	got := d.Feed([]byte("차\x1b[201~"))
	if want := []Msg{PasteMsg("보리차")}; !reflect.DeepEqual(got, want) {
		t.Errorf("= %#v, 원하는 값 %#v", got, want)
	}
}

// 반쪽짜리 UTF-8 은 나머지를 기다린다. 한글 한 글자는 3바이트인데,
// 그 중간에서 read 가 끊기는 일은 실제로 일어난다.
func TestPartialUTF8Waits(t *testing.T) {
	b := []byte("한") // ED 95 9C
	var d Decoder
	if got := d.Feed(b[:2]); len(got) != 0 {
		t.Errorf("반쪽 UTF-8 에 벌써 %#v 를 냈다", got)
	}
	got := d.Feed(b[2:])
	if want := []Msg{text("한", 0)}; !reflect.DeepEqual(got, want) {
		t.Errorf("= %#v, 원하는 값 %#v", got, want)
	}
}

// 끝내 완성되지 않는 UTF-8(잘못된 바이트)은 버려야 한다.
// 안 그러면 그 뒤의 모든 입력이 영원히 막힌다.
func TestBrokenUTF8IsDropped(t *testing.T) {
	var d Decoder
	got := append(d.Feed([]byte{0xff, 'a'}), d.Flush()...)
	want := []Msg{text("a", 0)}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("= %#v, 원하는 값 %#v", got, want)
	}
}

func TestMouseString(t *testing.T) {
	cases := []struct {
		m    MouseMsg
		want string
	}{
		{MouseMsg{X: 1, Y: 2, Button: MouseLeft, Action: MousePress}, "left press (1,2)"},
		{MouseMsg{X: 0, Y: 0, Button: MouseRight, Action: MouseRelease}, "right release (0,0)"},
		{MouseMsg{X: 5, Y: 6, Button: MouseWheelUp, Action: MousePress}, "wheelup press (5,6)"},
		{MouseMsg{X: 1, Y: 1, Button: MouseNone, Action: MouseMotion}, "none motion (1,1)"},
		{MouseMsg{X: 1, Y: 1, Button: MouseLeft, Action: MousePress, Mod: ModCtrl}, "ctrl+left press (1,1)"},
	}
	for _, c := range cases {
		if got := c.m.String(); got != c.want {
			t.Errorf("%+v.String() = %q, 원하는 값 %q", c.m, got, c.want)
		}
	}
}
