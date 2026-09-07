package render

import (
	"reflect"
	"testing"
)

// 프레임은 "화면에 보일 줄들" 이다. View() 가 준 문자열을 화면 크기에 맞춰 자른 것.
//
// 왜 여기서 자르는가. 터미널은 폭을 넘는 줄을 스스로 다음 줄로 감아 버린다.
// 그러면 우리가 세어 둔 줄 번호와 실제 화면의 줄 번호가 어긋나고,
// 줄 단위로 커서를 옮기는 렌더러가 엉뚱한 줄을 고쳐 쓴다. TUI 깜빡임 버그 1위가 이것이다.
func TestNewFrame(t *testing.T) {
	cases := []struct {
		name string
		view string
		w, h int
		want []string
	}{
		{"그대로", "ab\ncd", 10, 5, []string{"ab", "cd"}},
		{"폭 넘는 줄은 자른다", "abcdef", 3, 5, []string{"abc"}},
		{"높이 넘는 줄은 버린다", "a\nb\nc\nd", 10, 2, []string{"a", "b"}},
		{"한글은 두 칸으로 세어 자른다", "한글", 3, 5, []string{"한"}},
		{"꾸밈은 칸을 안 먹는다", "\x1b[31mabcdef\x1b[0m", 3, 5, []string{"\x1b[31mabc\x1b[0m"}},
		{"빈 화면", "", 10, 3, []string{""}},
		{"끝의 빈 줄도 한 줄", "a\n", 10, 3, []string{"a", ""}},
	}
	for _, c := range cases {
		got := NewFrame(c.view, c.w, c.h).Lines
		if !reflect.DeepEqual(got, c.want) {
			t.Errorf("%s: NewFrame(%q,%d,%d) = %q, 원하는 값 %q", c.name, c.view, c.w, c.h, got, c.want)
		}
	}
}

func TestFrameLine(t *testing.T) {
	f := NewFrame("a\nb", 10, 5)
	if f.Height() != 2 {
		t.Errorf("Height() = %d, 원하는 값 2", f.Height())
	}
	if f.Line(0) != "a" || f.Line(1) != "b" {
		t.Errorf("줄이 %q", f.Lines)
	}
	// 없는 줄을 물으면 빈 줄이다. 화면이 줄어들었을 때 diff 가 범위를 넘어 죽지 않게.
	if f.Line(5) != "" {
		t.Errorf("Line(5) = %q, 원하는 값 \"\"", f.Line(5))
	}
	if f.Line(-1) != "" {
		t.Errorf("Line(-1) = %q, 원하는 값 \"\"", f.Line(-1))
	}
}
