package input

import (
	"strings"
	"unicode"
)

// Msg 는 이 파서가 만들어 내는 사건이다.
//
// tea.Msg 와 같은 것인데 왜 여기에 또 두는가. 의존 방향이 tea → input 이라
// 이 패키지에서 tea 를 import 하면 순환이 된다. Go 는 순환 import 를 아예 금지한다.
// 그래서 여기서는 별칭(= any)으로 두고, tea 쪽에서 자기 이름을 붙인다.
// 별칭이므로 두 이름은 컴파일러에게 완전히 같은 타입이다 — 변환이 필요 없다.
//
// Bubble Tea 는 이 모두를 한 패키지에 넣어 이 문제를 피했다. 층을 나눈 대가가 이 한 줄이다.
type Msg = any

// KeyMod 는 함께 눌린 조합키의 묶음이다. 비트 하나씩 맡는다.
type KeyMod int

const (
	ModShift KeyMod = 1 << iota
	ModAlt
	ModCtrl
)

// Contains 는 o 의 비트가 전부 들어 있는지 본다.
// m.Contains(ModAlt|ModCtrl) 는 둘 다 있어야 참이다.
func (m KeyMod) Contains(o KeyMod) bool { return m&o == o }

// 특수키 코드 — 화살표, 기능키처럼 글자가 아닌 키들.
//
// 왜 rune 하나로 표현하는가. 키 하나를 "글자냐 특수키냐" 로 나눠 두 필드에 담으면,
// 쓰는 쪽이 늘 두 갈래로 분기해야 한다. 대신 유니코드가 절대 쓰지 않을 번호
// (마지막 코드포인트 U+10FFFF 너머)를 빌려 오면, 글자든 특수키든 Code 하나만 보면 된다.
// Bubble Tea v2 도 같은 방법을 쓴다(ultraviolet 의 KeyExtended = unicode.MaxRune+1).
const (
	keySpecial = unicode.MaxRune + iota // 경계 표시. 이 값보다 커야 특수키다.
	KeyUp
	KeyDown
	KeyRight
	KeyLeft
	KeyHome
	KeyEnd
	KeyPgUp
	KeyPgDown
	KeyInsert
	KeyDelete
	KeyF1
	KeyF2
	KeyF3
	KeyF4
	KeyF5
	KeyF6
	KeyF7
	KeyF8
	KeyF9
	KeyF10
	KeyF11
	KeyF12
)

// 제어 문자로 오는 키들은 유니코드 안에 자기 자리가 이미 있다.
// 새 번호를 만들지 않고 그 자리를 그대로 쓴다 — 터미널이 보내는 바이트 그 자체다.
const (
	KeyBackspace = rune(0x7f) // DEL. 백스페이스가 0x08 이 아니라 0x7f 인 것이 관례다.
	KeyTab       = rune('\t') // 0x09
	KeyEnter     = rune('\r') // 0x0D. 줄바꿈(0x0A)이 아니다 — ICRNL 을 껐기 때문이다.
	KeyEscape    = rune(0x1b)
	KeySpace     = rune(' ')
)

// Key 는 눌린 키 하나.
type Key struct {
	// Code 는 눌린 키. 글자면 그 글자, 특수키면 위의 상수.
	Code rune
	// Text 는 화면에 찍힐 글자. 특수키나 조합키면 비어 있다.
	//
	// Code 와 따로 두는 이유: 입력창은 "이 키가 글자로 들어가야 하나" 만 알면 되는데,
	// Code 만 봐서는 ctrl+a 와 a 를 구별하려고 Mod 까지 봐야 한다. Text 가 비어 있는지가
	// 곧 그 판단이다.
	Text string
	// Mod 는 함께 눌린 조합키.
	Mod KeyMod
}

// 특수키의 이름표. 이 이름들은 Bubble Tea 와 글자 하나까지 같다 —
// 이 덱을 읽고 나서 진짜 Bubble Tea 로 옮겨 갈 때 switch 문을 고치지 않아도 되게.
var keyNames = map[rune]string{
	KeyEnter:     "enter",
	KeyTab:       "tab",
	KeyBackspace: "backspace",
	KeyEscape:    "esc",
	KeySpace:     "space",
	KeyUp:        "up",
	KeyDown:      "down",
	KeyLeft:      "left",
	KeyRight:     "right",
	KeyHome:      "home",
	KeyEnd:       "end",
	KeyPgUp:      "pgup",
	KeyPgDown:    "pgdown",
	KeyInsert:    "insert",
	KeyDelete:    "delete",
	KeyF1:        "f1",
	KeyF2:        "f2",
	KeyF3:        "f3",
	KeyF4:        "f4",
	KeyF5:        "f5",
	KeyF6:        "f6",
	KeyF7:        "f7",
	KeyF8:        "f8",
	KeyF9:        "f9",
	KeyF10:       "f10",
	KeyF11:       "f11",
	KeyF12:       "f12",
}

// String 은 키를 사람이 읽고 switch 로 비교할 이름으로 만든다.
//
// 조합키 순서는 언제나 ctrl → alt → shift 다. 순서를 고정해 두지 않으면
// "ctrl+shift+x" 와 "shift+ctrl+x" 가 둘 다 나와 비교문이 조용히 어긋난다.
func (k Key) String() string {
	var b strings.Builder
	if k.Mod.Contains(ModCtrl) {
		b.WriteString("ctrl+")
	}
	if k.Mod.Contains(ModAlt) {
		b.WriteString("alt+")
	}
	if k.Mod.Contains(ModShift) {
		b.WriteString("shift+")
	}
	if name, ok := keyNames[k.Code]; ok {
		b.WriteString(name)
	} else {
		b.WriteRune(k.Code)
	}
	return b.String()
}

// KeyMsg 는 키 하나가 눌렸다는 사건. Program 의 Update 로 이 타입이 들어온다.
//
// Key 와 따로 두는 이유: 사건(Msg)과 값(Key)은 다른 것이다. 위젯 안에서
// Key 를 필드로 들고 다닐 때 그것이 "지금 막 일어난 사건" 처럼 보이면 안 된다.
type KeyMsg Key

func (k KeyMsg) String() string { return Key(k).String() }
