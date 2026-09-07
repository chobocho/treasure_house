package tea

import "treasure/boricha/input"

// 조합키. input 의 것을 그대로 쓴다.
const (
	ModShift = input.ModShift
	ModAlt   = input.ModAlt
	ModCtrl  = input.ModCtrl
)

// 특수키 코드. 대부분은 msg.String() 으로 비교하는 편이 읽기 좋지만,
// 코드로 직접 견주고 싶을 때를 위해 열어 둔다.
const (
	KeyUp        = input.KeyUp
	KeyDown      = input.KeyDown
	KeyLeft      = input.KeyLeft
	KeyRight     = input.KeyRight
	KeyHome      = input.KeyHome
	KeyEnd       = input.KeyEnd
	KeyPgUp      = input.KeyPgUp
	KeyPgDown    = input.KeyPgDown
	KeyInsert    = input.KeyInsert
	KeyDelete    = input.KeyDelete
	KeyEnter     = input.KeyEnter
	KeyTab       = input.KeyTab
	KeyEscape    = input.KeyEscape
	KeySpace     = input.KeySpace
	KeyBackspace = input.KeyBackspace
	KeyF1        = input.KeyF1
	KeyF2        = input.KeyF2
	KeyF3        = input.KeyF3
	KeyF4        = input.KeyF4
	KeyF5        = input.KeyF5
	KeyF6        = input.KeyF6
	KeyF7        = input.KeyF7
	KeyF8        = input.KeyF8
	KeyF9        = input.KeyF9
	KeyF10       = input.KeyF10
	KeyF11       = input.KeyF11
	KeyF12       = input.KeyF12
)

// 마우스 버튼과 동작.
const (
	MouseNone       = input.MouseNone
	MouseLeft       = input.MouseLeft
	MouseMiddle     = input.MouseMiddle
	MouseRight      = input.MouseRight
	MouseWheelUp    = input.MouseWheelUp
	MouseWheelDown  = input.MouseWheelDown
	MouseWheelLeft  = input.MouseWheelLeft
	MouseWheelRight = input.MouseWheelRight
	MouseBackward   = input.MouseBackward
	MouseForward    = input.MouseForward

	MousePress   = input.MousePress
	MouseRelease = input.MouseRelease
	MouseMotion  = input.MouseMotion
)
