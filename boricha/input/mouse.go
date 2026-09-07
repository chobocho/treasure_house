package input

import "strconv"

// MouseButton 은 어느 버튼이 관여했는가. 휠도 버튼으로 온다.
type MouseButton int

const (
	MouseNone MouseButton = iota
	MouseLeft
	MouseMiddle
	MouseRight
	MouseWheelUp
	MouseWheelDown
	MouseWheelLeft
	MouseWheelRight
	MouseBackward
	MouseForward
)

var mouseButtonNames = map[MouseButton]string{
	MouseNone: "none", MouseLeft: "left", MouseMiddle: "middle", MouseRight: "right",
	MouseWheelUp: "wheelup", MouseWheelDown: "wheeldown",
	MouseWheelLeft: "wheelleft", MouseWheelRight: "wheelright",
	MouseBackward: "backward", MouseForward: "forward",
}

// MouseAction 은 무슨 일이 일어났는가.
type MouseAction int

const (
	MousePress MouseAction = iota
	MouseRelease
	MouseMotion
)

var mouseActionNames = map[MouseAction]string{
	MousePress: "press", MouseRelease: "release", MouseMotion: "motion",
}

// MouseMsg 는 마우스 사건 하나.
//
// X, Y 는 0부터 세는 화면 좌표다. 터미널은 1부터 세어 보내지만, 여기서 한 번만
// 0부터로 바꿔 둔다. 화면 버퍼도 슬라이스도 전부 0부터 세기 때문에,
// 이 변환을 쓰는 쪽마다 하게 두면 반드시 어딘가에서 한 칸이 어긋난다.
type MouseMsg struct {
	X, Y   int
	Button MouseButton
	Action MouseAction
	Mod    KeyMod
}

func (m MouseMsg) String() string {
	s := ""
	if m.Mod.Contains(ModCtrl) {
		s += "ctrl+"
	}
	if m.Mod.Contains(ModAlt) {
		s += "alt+"
	}
	if m.Mod.Contains(ModShift) {
		s += "shift+"
	}
	return s + mouseButtonNames[m.Button] + " " + mouseActionNames[m.Action] +
		" (" + strconv.Itoa(m.X) + "," + strconv.Itoa(m.Y) + ")"
}

// sgrMouse 는 "0;10;5" 같은 매개변수를 MouseMsg 로 바꾼다.
//
// SGR 1006 인코딩을 쓰는 이유. 원래 방식(X10)은 좌표를 바이트 하나에 32를 더해 담는다.
// 그래서 223칸을 넘는 창에서 무너지고, 버튼을 뗀 사건에서는 어느 버튼이었는지를 잃는다.
// 1006 은 숫자를 십진수 글자로 적고 누름(M)/뗌(m)을 마지막 글자로 구분해서 둘 다 푼다.
//
// 첫 숫자는 비트 묶음이다:
//
//	하위 2비트  버튼 (0 왼쪽, 1 가운데, 2 오른쪽, 3 없음)
//	4           shift
//	8           alt
//	16          ctrl
//	32          움직이는 중
//	64          휠 (하위 2비트가 위/아래/왼/오른)
//	128         곁버튼 8·9 (뒤로/앞으로)
func sgrMouse(params []byte, release bool) Msg {
	f := splitParams(params)
	if len(f) < 3 {
		return UnknownMsg("\x1b[<" + string(params))
	}
	code, x, y := f[0], f[1], f[2]

	m := MouseMsg{X: x - 1, Y: y - 1}
	if code&4 != 0 {
		m.Mod |= ModShift
	}
	if code&8 != 0 {
		m.Mod |= ModAlt
	}
	if code&16 != 0 {
		m.Mod |= ModCtrl
	}

	low := code & 3
	switch {
	case code&64 != 0:
		m.Button = [...]MouseButton{MouseWheelUp, MouseWheelDown, MouseWheelLeft, MouseWheelRight}[low]
	case code&128 != 0:
		m.Button = [...]MouseButton{MouseBackward, MouseForward, MouseNone, MouseNone}[low]
	default:
		m.Button = [...]MouseButton{MouseLeft, MouseMiddle, MouseRight, MouseNone}[low]
	}

	switch {
	case release:
		m.Action = MouseRelease
	case code&32 != 0:
		m.Action = MouseMotion
	default:
		m.Action = MousePress
	}
	return m
}
