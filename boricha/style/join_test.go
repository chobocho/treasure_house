package style

import "testing"

func TestJoinHorizontal(t *testing.T) {
	cases := []struct {
		name string
		pos  Position
		in   []string
		want string
	}{
		{"같은 높이", Top, []string{"a", "b"}, "ab"},
		{"짧은 쪽을 채운다", Top, []string{"a\nb", "c"}, "ac\nb "},
		{"아래로 붙이기", Bottom, []string{"a\nb", "c"}, "a \nbc"},
		{"가운데로 붙이기", Center, []string{"a\nb\nc", "x"}, "a \nbx\nc "},
		{"한글 폭", Top, []string{"한\n글", "ab"}, "한ab\n글  "},
		{"빈 덩어리", Top, []string{"", "a"}, "a"},
		{"하나뿐", Top, []string{"ab"}, "ab"},
	}
	for _, c := range cases {
		if got := JoinHorizontal(c.pos, c.in...); got != c.want {
			t.Errorf("%s: = %q, 원하는 값 %q", c.name, got, c.want)
		}
	}
}

func TestJoinVertical(t *testing.T) {
	cases := []struct {
		name string
		pos  Position
		in   []string
		want string
	}{
		{"왼쪽", Left, []string{"a", "bb"}, "a \nbb"},
		{"오른쪽", Right, []string{"a", "bb"}, " a\nbb"},
		{"가운데", Center, []string{"a", "bbb"}, " a \nbbb"},
		{"여러 줄끼리", Left, []string{"a\nb", "cc"}, "a \nb \ncc"},
	}
	for _, c := range cases {
		if got := JoinVertical(c.pos, c.in...); got != c.want {
			t.Errorf("%s: = %q, 원하는 값 %q", c.name, got, c.want)
		}
	}
}

func TestPlace(t *testing.T) {
	cases := []struct {
		name       string
		w, h       int
		hpos, vpos Position
		in, want   string
	}{
		{"왼쪽 위", 4, 2, Left, Top, "x", "x   \n    "},
		{"가운데", 5, 3, Center, Center, "x", "     \n  x  \n     "},
		{"오른쪽 아래", 3, 2, Right, Bottom, "x", "   \n  x"},
		{"이미 큰 것은 그대로", 1, 1, Left, Top, "abc", "abc"},
	}
	for _, c := range cases {
		if got := Place(c.w, c.h, c.hpos, c.vpos, c.in); got != c.want {
			t.Errorf("%s: = %q, 원하는 값 %q", c.name, got, c.want)
		}
	}
}
