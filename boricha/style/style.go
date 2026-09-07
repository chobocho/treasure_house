package style

// Position 은 남는 자리를 어느 쪽으로 몰지 정한다. 0 이 왼쪽/위, 1 이 오른쪽/아래다.
//
// 왜 실수인가. 0.25 처럼 중간값을 쓸 수 있게 하려고다. 상수 세 개짜리 열거형이었다면
// "3분의 1 지점" 같은 요구가 올 때마다 상수를 늘려야 한다.
type Position float64

const (
	Top    Position = 0
	Left   Position = 0
	Center Position = 0.5
	Bottom Position = 1
	Right  Position = 1
)

// Style 은 "어떻게 그릴지" 를 담은 값이다.
//
// **값이라는 것이 이 타입의 전부다.** 모든 메서드가 값 수신자를 쓰고 고쳐진 복사본을
// 돌려준다. 그래서 스타일을 전역 변수에 두고 여기저기서 조금씩 바꿔 써도 서로 간섭하지 않는다.
// 포인터였다면 한 곳에서 .Bold(true) 를 부르는 순간 다른 모든 곳의 글씨가 굵어진다.
//
// 대가는 복사 비용이다. 이 구조체는 300바이트쯤 되고, 한 프레임에 수십 번 복사된다 —
// 터미널 한 화면이 2,000칸도 안 되는 것에 비하면 없는 비용이다.
type Style struct {
	profile Profile

	bold, faint, italic, underline, reverse, strike bool
	fg, bg                                          Color

	padTop, padRight, padBottom, padLeft int
	marTop, marRight, marBottom, marLeft int

	width, height int
	align, valign Position

	border                                   Border
	hasBorder                                bool
	bordTop, bordRight, bordBottom, bordLeft bool
	borderFg                                 Color
}

// New 는 아무 꾸밈도 없는 스타일을 만든다.
//
// 색 프로필의 기본값은 NoColor 다. "환경을 알아서 보고 정해 주는" 기본값을 두지 않은 이유는,
// 그러면 같은 코드가 터미널에 따라 다른 문자열을 내놓아 시험이 흔들리기 때문이다.
// 프로필을 정하는 것은 프로그램을 띄우는 쪽(tea.Program)의 일이다.
func New() Style { return Style{} }

// Profile 은 낼 수 있는 색 수준을 정한다.
func (s Style) Profile(p Profile) Style { s.profile = p; return s }

func (s Style) Bold(v bool) Style          { s.bold = v; return s }
func (s Style) Faint(v bool) Style         { s.faint = v; return s }
func (s Style) Italic(v bool) Style        { s.italic = v; return s }
func (s Style) Underline(v bool) Style     { s.underline = v; return s }
func (s Style) Reverse(v bool) Style       { s.reverse = v; return s }
func (s Style) Strikethrough(v bool) Style { s.strike = v; return s }

func (s Style) Foreground(c Color) Style { s.fg = c; return s }
func (s Style) Background(c Color) Style { s.bg = c; return s }

// Padding 은 내용과 테두리 사이의 빈 자리다. 배경색이 여기까지 덮는다.
//
// 인자 개수에 따라 CSS 처럼 해석한다:
//
//	1개  네 방향 모두
//	2개  위아래, 좌우
//	3개  위, 좌우, 아래
//	4개  위, 오른쪽, 아래, 왼쪽 (시계 방향)
func (s Style) Padding(v ...int) Style {
	s.padTop, s.padRight, s.padBottom, s.padLeft = sides(v)
	return s
}

// Margin 은 테두리 바깥의 빈 자리다. 배경색이 여기는 덮지 않는다 —
// 그 차이가 패딩과 여백을 나누는 유일한 이유다.
func (s Style) Margin(v ...int) Style {
	s.marTop, s.marRight, s.marBottom, s.marLeft = sides(v)
	return s
}

func sides(v []int) (top, right, bottom, left int) {
	switch len(v) {
	case 1:
		return v[0], v[0], v[0], v[0]
	case 2:
		return v[0], v[1], v[0], v[1]
	case 3:
		return v[0], v[1], v[2], v[1]
	case 4:
		return v[0], v[1], v[2], v[3]
	}
	return 0, 0, 0, 0
}

// Width 는 내용과 패딩을 합친 폭을 못박는다. 내용이 더 넓으면 접는다(줄바꿈).
func (s Style) Width(w int) Style { s.width = w; return s }

// Height 는 줄 수를 못박는다. 모자라면 빈 줄로 채운다.
func (s Style) Height(h int) Style { s.height = h; return s }

// Align 은 폭이 남을 때 글을 어느 쪽으로 붙일지.
func (s Style) Align(p Position) Style { s.align = p; return s }

// AlignVertical 은 높이가 남을 때 글을 위·가운데·아래 어디에 둘지.
func (s Style) AlignVertical(p Position) Style { s.valign = p; return s }

// Border 는 테두리를 두른다. sides 로 어느 변을 그릴지 고를 수 있다
// (Padding 과 같은 규칙: 위, 오른쪽, 아래, 왼쪽).
func (s Style) Border(b Border, sides ...bool) Style {
	s.border = b
	s.hasBorder = true
	switch len(sides) {
	case 0:
		s.bordTop, s.bordRight, s.bordBottom, s.bordLeft = true, true, true, true
	case 1:
		v := sides[0]
		s.bordTop, s.bordRight, s.bordBottom, s.bordLeft = v, v, v, v
	case 2:
		s.bordTop, s.bordBottom = sides[0], sides[0]
		s.bordRight, s.bordLeft = sides[1], sides[1]
	case 3:
		s.bordTop, s.bordBottom = sides[0], sides[2]
		s.bordRight, s.bordLeft = sides[1], sides[1]
	default:
		s.bordTop, s.bordRight, s.bordBottom, s.bordLeft = sides[0], sides[1], sides[2], sides[3]
	}
	return s
}

// BorderForeground 는 테두리만 다른 색으로 칠한다.
func (s Style) BorderForeground(c Color) Style { s.borderFg = c; return s }
