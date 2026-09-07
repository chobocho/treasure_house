package term

import "strconv"

// 이스케이프 시퀀스 — 터미널에게 시키는 말.
//
// 터미널과 프로그램 사이에는 "그림을 그리는 API" 가 없다. 오가는 것은 바이트뿐이다.
// 그래서 글자로 볼 바이트와 명령으로 볼 바이트를 가르는 표시가 필요한데, 그 표시가
// ESC(0x1B)다. ESC 로 시작하는 짧은 바이트열이 곧 명령이다.
//
// 아래 상수들은 설명이 아니라 우리가 실제로 터미널에 써 보내는 바이트 그 자체다.
// 한 글자만 틀려도 터미널은 그걸 명령이 아닌 글자로 알고 화면에 찍어 버린다.
const (
	// ESC 는 이스케이프 문자 한 개. 뒤에 무엇이 오느냐로 명령의 종류가 갈린다.
	ESC = "\x1b"
	// CSI(Control Sequence Introducer) = ESC + '['. 화면 제어 명령의 대부분이 이 접두사를 쓴다.
	// 뒤에 숫자 매개변수가 ';' 로 이어지고, 마지막 한 글자가 명령 이름이다.
	CSI = ESC + "["
)

// 그리기·지우기. 매개변수가 없거나 고정이라 상수로 둘 수 있는 것들.
const (
	// SGR(Select Graphic Rendition) 0번 = 색과 굵기 등 모든 꾸밈을 초기 상태로.
	// 그리기가 끝날 때마다 이걸 붙이지 않으면 꾸밈이 다음 줄로 새어 나간다.
	Reset = CSI + "0m"
	// ED(Erase in Display) 2번 = 화면 전체 지우기. 커서는 움직이지 않는다.
	ClearScreen = CSI + "2J"
	// EL(Erase in Line) 2번 = 커서가 있는 줄 전체 지우기.
	ClearLine = CSI + "2K"
	// EL 0번(생략형) = 커서 자리부터 줄 끝까지. 렌더러가 줄을 다시 쓸 때 쓰는 것이 이쪽이다.
	// 줄 전체를 지우고 다시 쓰면 지운 순간이 눈에 보여 깜빡인다.
	ClearToEOL = CSI + "K"
	// CUP(Cursor Position) 매개변수 생략 = 1행 1열.
	CursorHome = CSI + "H"

	// DEC 개별 모드(DECSET/DECRST). '?' 가 붙는 것이 표준이 아니라 DEC 확장이라는 표시다.
	// 25 = 커서 보이기. 그리는 동안 커서가 화면을 돌아다니면 그 자체가 깜빡임으로 보인다.
	HideCursor = CSI + "?25l"
	ShowCursor = CSI + "?25h"

	// 1049 = 대체 화면 버퍼. 들어갈 때 원래 화면을 저장하고, 나올 때 그대로 되돌린다.
	// TUI 프로그램을 끝냈을 때 셸 화면이 그대로 남아 있는 이유가 이것이다.
	EnterAltScreen = CSI + "?1049h"
	ExitAltScreen  = CSI + "?1049l"
)

// 마우스. 1002 는 버튼을 누른 채 움직일 때만 보고(button-event),
// 1003 은 그냥 움직여도 보고(any-event)다. 1006 은 좌표를 적는 방식이다.
//
// 1006(SGR 인코딩)을 반드시 같이 켜야 한다. 옛 방식은 좌표를 바이트 하나에
// 32를 더해 담아서 223칸을 넘으면 무너지고, 버튼을 뗀 사건에서 어느 버튼이었는지도 잃는다.
// 끌 때는 켠 순서의 역순으로 — 인코딩을 먼저 끄고 추적을 끈다.
const (
	EnableMouse     = CSI + "?1002h" + CSI + "?1006h"
	DisableMouse    = CSI + "?1006l" + CSI + "?1002l"
	EnableMouseAll  = CSI + "?1003h" + CSI + "?1006h"
	DisableMouseAll = CSI + "?1006l" + CSI + "?1003l"
)

const (
	// 2004 = 괄호 붙은 붙여넣기. 켜면 붙여넣기의 앞뒤를 ESC[200~ … ESC[201~ 로 감싸 준다.
	// 이게 없으면 붙여넣은 여러 줄이 "사용자가 엔터를 여러 번 친 것"과 구분되지 않는다.
	EnablePaste  = CSI + "?2004h"
	DisablePaste = CSI + "?2004l"

	// 1004 = 포커스 사건. 창이 앞으로 올 때 ESC[I, 뒤로 갈 때 ESC[O 가 온다.
	EnableFocus  = CSI + "?1004h"
	DisableFocus = CSI + "?1004l"

	// 2026 = 동기화 출력. 한 프레임을 다 쓸 때까지 터미널이 화면 갱신을 미룬다.
	// 지원하지 않는 터미널은 모르는 모드로 보고 조용히 무시하므로 넣어도 해롭지 않다.
	BeginSync = CSI + "?2026h"
	EndSync   = CSI + "?2026l"
)

// CursorTo 는 커서를 (row, col) 로 옮긴다. 좌표는 화면 왼쪽 위가 (1,1)인 1부터 세는 좌표다.
//
// 0 이하가 들어오면 1 로 올린다. 0부터 세는 습관 때문에 생기는 한 칸 어긋남이
// 화면 전체를 밀어 버리는 것보다, 조용히 맨 위·맨 왼쪽으로 붙는 편이 낫다.
func CursorTo(row, col int) string {
	if row < 1 {
		row = 1
	}
	if col < 1 {
		col = 1
	}
	// 문자열 덧셈 대신 []byte 에 이어 붙인다. 이 함수는 한 프레임에 줄 수만큼 불린다.
	b := make([]byte, 0, 12)
	b = append(b, CSI...)
	b = strconv.AppendInt(b, int64(row), 10)
	b = append(b, ';')
	b = strconv.AppendInt(b, int64(col), 10)
	b = append(b, 'H')
	return string(b)
}

// CursorUp 은 커서를 n 줄 올린다(CUU). n 이 0 이하면 빈 문자열 —
// "안 움직임"을 시퀀스로 표현하지 않는 편이, 받는 쪽에서 매개변수 0을 1로 해석하는
// ECMA-48 의 기본값 규칙에 걸리지 않아 안전하다.
func CursorUp(n int) string { return move(n, 'A') }

// CursorDown 은 커서를 n 줄 내린다(CUD).
func CursorDown(n int) string { return move(n, 'B') }

func move(n int, cmd byte) string {
	if n < 1 {
		return ""
	}
	b := make([]byte, 0, 8)
	b = append(b, CSI...)
	b = strconv.AppendInt(b, int64(n), 10)
	b = append(b, cmd)
	return string(b)
}

// CursorToCol 은 줄은 그대로 두고 col 열로만 옮긴다(CHA).
// 줄 단위 diff 렌더러가 "이 줄의 1열로" 갈 때 쓴다 — 행 번호를 다시 계산할 필요가 없다.
func CursorToCol(col int) string {
	if col < 1 {
		col = 1
	}
	b := make([]byte, 0, 8)
	b = append(b, CSI...)
	b = strconv.AppendInt(b, int64(col), 10)
	b = append(b, 'G')
	return string(b)
}
