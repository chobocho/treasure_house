package style

import (
	"strings"
	"testing"

	"treasure/boricha/width"
)

// 스타일은 값이다. 메서드는 자기를 고치지 않고 고쳐진 복사본을 돌려준다.
//
// 이 성질 하나로 스타일을 전역 변수에 담아 두고 여기저기서 조금씩 바꿔 쓸 수 있다.
// 포인터였다면 한 곳에서 .Bold(true) 를 부른 순간 다른 모든 곳의 글씨가 굵어진다.
func TestStyleIsAValue(t *testing.T) {
	base := New().Profile(ANSI).Foreground("1")
	bold := base.Bold(true)

	if got := base.Render("x"); got != "\x1b[31mx\x1b[0m" {
		t.Errorf("원본이 바뀌었다: %q", got)
	}
	if got := bold.Render("x"); got != "\x1b[1;31mx\x1b[0m" {
		t.Errorf("복사본 = %q", got)
	}
}

func TestRenderPlain(t *testing.T) {
	cases := []struct{ in, want string }{
		{"hi", "hi"},
		{"", ""},
		{"한글", "한글"},
		// 여러 줄이면 가장 넓은 줄에 맞춰 오른쪽을 채운다.
		// 그래야 이 덩어리를 옆 덩어리와 나란히 붙일 수 있다.
		{"a\nbb", "a \nbb"},
		{"한\nab", "한\nab"},
	}
	for _, c := range cases {
		if got := New().Render(c.in); got != c.want {
			t.Errorf("Render(%q) = %q, 원하는 값 %q", c.in, got, c.want)
		}
	}
}

// 여러 조각을 넘기면 공백으로 이어 붙인다 (fmt.Sprintln 이 아니라 Sprint 쪽).
func TestRenderJoinsParts(t *testing.T) {
	if got := New().Render("a", "b"); got != "a b" {
		t.Errorf("= %q, 원하는 값 %q", got, "a b")
	}
}

func TestSGRComposition(t *testing.T) {
	cases := []struct {
		name string
		s    Style
		want string
	}{
		{"굵게", New().Profile(ANSI).Bold(true), "\x1b[1mx\x1b[0m"},
		{"흐리게", New().Profile(ANSI).Faint(true), "\x1b[2mx\x1b[0m"},
		{"기울임", New().Profile(ANSI).Italic(true), "\x1b[3mx\x1b[0m"},
		{"밑줄", New().Profile(ANSI).Underline(true), "\x1b[4mx\x1b[0m"},
		{"반전", New().Profile(ANSI).Reverse(true), "\x1b[7mx\x1b[0m"},
		{"취소선", New().Profile(ANSI).Strikethrough(true), "\x1b[9mx\x1b[0m"},
		// 꾸밈 → 글자색 → 배경색 순서로 한 시퀀스에 모은다.
		// 나눠 보내도 결과는 같지만, 한 번에 보내면 바이트가 줄고 읽기도 쉽다.
		{"섞기", New().Profile(ANSI).Bold(true).Underline(true).Foreground("2").Background("0"),
			"\x1b[1;4;32;40mx\x1b[0m"},
		{"256색", New().Profile(ANSI256).Foreground("205"), "\x1b[38;5;205mx\x1b[0m"},
		{"24비트", New().Profile(TrueColor).Foreground("#ff00ff"), "\x1b[38;2;255;0;255mx\x1b[0m"},
		// 색을 못 내는 터미널에서는 시퀀스를 아예 안 보낸다.
		{"색 없음", New().Profile(NoColor).Bold(true).Foreground("1"), "x"},
	}
	for _, c := range cases {
		if got := c.s.Render("x"); got != c.want {
			t.Errorf("%s: = %q, 원하는 값 %q", c.name, got, c.want)
		}
	}
}

// 여러 줄에 꾸밈을 걸면 줄마다 열고 닫는다.
// 줄 끝에서 닫지 않으면, 줄 단위 diff 렌더러가 그 줄만 다시 그릴 때 색이 남거나 사라진다.
func TestSGRPerLine(t *testing.T) {
	got := New().Profile(ANSI).Bold(true).Render("a\nb")
	want := "\x1b[1ma\x1b[0m\n\x1b[1mb\x1b[0m"
	if got != want {
		t.Errorf("= %q, 원하는 값 %q", got, want)
	}
}

func TestPadding(t *testing.T) {
	cases := []struct {
		name string
		s    Style
		in   string
		want string
	}{
		{"좌우 1", New().Padding(0, 1), "hi", " hi "},
		{"위아래 1·좌우 2", New().Padding(1, 2), "hi", "      \n  hi  \n      "},
		{"네 방향 따로", New().Padding(1, 2, 0, 3), "x", "      \n   x  "},
		{"값 하나면 네 방향 모두", New().Padding(1), "x", "   \n x \n   "},
		{"한글도 칸으로 센다", New().Padding(0, 1), "한", " 한 "},
	}
	for _, c := range cases {
		if got := c.s.Render(c.in); got != c.want {
			t.Errorf("%s: = %q, 원하는 값 %q", c.name, got, c.want)
		}
	}
}

func TestWidthAndAlign(t *testing.T) {
	cases := []struct {
		name string
		s    Style
		want string
	}{
		{"왼쪽(기본)", New().Width(6), "hi    "},
		{"오른쪽", New().Width(6).Align(Right), "    hi"},
		{"가운데", New().Width(6).Align(Center), "  hi  "},
		{"가운데 홀수", New().Width(7).Align(Center), "  hi   "},
		{"폭이 내용보다 작으면 접는다", New().Width(1), "h\ni"},
	}
	for _, c := range cases {
		if got := c.s.Render("hi"); got != c.want {
			t.Errorf("%s: = %q, 원하는 값 %q", c.name, got, c.want)
		}
	}
}

func TestHeight(t *testing.T) {
	cases := []struct {
		name string
		s    Style
		want string
	}{
		{"위(기본)", New().Height(3), "hi\n  \n  "},
		{"아래", New().Height(3).AlignVertical(Bottom), "  \n  \nhi"},
		{"가운데", New().Height(3).AlignVertical(Center), "  \nhi\n  "},
	}
	for _, c := range cases {
		if got := c.s.Render("hi"); got != c.want {
			t.Errorf("%s: = %q, 원하는 값 %q", c.name, got, c.want)
		}
	}
}

func TestBorder(t *testing.T) {
	cases := []struct {
		name string
		s    Style
		in   string
		want string
	}{
		{"보통", New().Border(NormalBorder), "hi", "┌──┐\n│hi│\n└──┘"},
		{"둥근", New().Border(RoundedBorder), "hi", "╭──╮\n│hi│\n╰──╯"},
		{"아스키", New().Border(ASCIIBorder), "hi", "+--+\n|hi|\n+--+"},
		{"두 줄", New().Border(DoubleBorder), "hi", "╔══╗\n║hi║\n╚══╝"},
		{"한글 내용", New().Border(NormalBorder), "한글", "┌────┐\n│한글│\n└────┘"},
		{"여러 줄", New().Border(NormalBorder), "a\nbb", "┌──┐\n│a │\n│bb│\n└──┘"},
		// 변을 골라 그릴 수 있다. 위·오른쪽·아래·왼쪽 순서다(CSS 와 같다).
		{"위만", New().Border(NormalBorder, true, false, false, false), "hi", "──\nhi"},
		{"왼쪽만", New().Border(NormalBorder, false, false, false, true), "hi", "│hi"},
		{"위아래만", New().Border(NormalBorder, true, false, true, false), "hi", "──\nhi\n──"},
	}
	for _, c := range cases {
		if got := c.s.Render(c.in); got != c.want {
			t.Errorf("%s: = %q\n원하는 값 %q", c.name, got, c.want)
		}
	}
}

// 테두리는 패딩 바깥, 여백 안쪽에 그린다. 순서가 이 하나로 정해진다.
func TestPipelineOrder(t *testing.T) {
	got := New().Padding(0, 1).Border(NormalBorder).Margin(0, 1).Render("hi")
	want := " ┌────┐ \n │ hi │ \n └────┘ "
	if got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 배경색은 패딩까지 덮지만 여백은 덮지 않는다.
// 이 차이가 패딩과 여백을 나누는 유일한 이유다.
func TestBackgroundCoversPaddingNotMargin(t *testing.T) {
	got := New().Profile(ANSI).Background("4").Padding(0, 1).Margin(0, 1).Render("x")
	want := " \x1b[44m x \x1b[0m "
	if got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

func TestBorderForeground(t *testing.T) {
	got := New().Profile(ANSI).Border(NormalBorder).BorderForeground("1").Render("x")
	want := "\x1b[31m┌─┐\x1b[0m\n\x1b[31m│\x1b[0mx\x1b[31m│\x1b[0m\n\x1b[31m└─┘\x1b[0m"
	if got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 결과의 모든 줄은 폭이 같아야 한다. 안 그러면 옆에 붙인 덩어리가 계단처럼 어긋난다.
func TestRenderedBlockIsRectangular(t *testing.T) {
	styles := []Style{
		New().Padding(1, 2).Border(RoundedBorder).Width(20),
		New().Border(NormalBorder).Align(Center).Width(9),
		New().Margin(1, 1).Height(4),
	}
	for i, s := range styles {
		for _, in := range []string{"보리차", "a\nbb\nccc", "한글 섞인 text"} {
			lines := strings.Split(s.Render(in), "\n")
			w0 := width.StringWidth(lines[0])
			for j, l := range lines {
				if got := width.StringWidth(l); got != w0 {
					t.Errorf("스타일 %d, 입력 %q: 줄 %d 이 %d칸, 첫 줄은 %d칸", i, in, j, got, w0)
					break
				}
			}
		}
	}
}
