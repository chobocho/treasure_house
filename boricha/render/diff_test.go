package render

import (
	"reflect"
	"testing"
)

// diff 는 "다시 써야 할 줄 번호" 만 돌려준다.
//
// 화면 전체를 매번 다시 그리면 깜빡인다. 지운 순간과 다시 그린 순간 사이에
// 터미널이 화면을 한 번 보여 주면 사람 눈에 검은 줄이 스친다.
// 달라진 줄만 고쳐 쓰면 그 틈이 아예 생기지 않는다.
func TestDiff(t *testing.T) {
	f := func(lines ...string) Frame { return Frame{Lines: lines} }
	cases := []struct {
		name     string
		old, new Frame
		want     []int
	}{
		{"같으면 아무것도 안 쓴다", f("a", "b"), f("a", "b"), nil},
		{"가운데 한 줄", f("a", "b", "c"), f("a", "X", "c"), []int{1}},
		{"여러 줄", f("a", "b", "c"), f("X", "b", "Y"), []int{0, 2}},
		{"처음 그리기", f(), f("a", "b"), []int{0, 1}},
		{"줄이 늘었다", f("a"), f("a", "b"), []int{1}},
		// 줄이 줄면 남은 자리를 지워야 한다. 안 지우면 지난 프레임의 글이 화면에 남는다.
		{"줄이 줄었다", f("a", "b", "c"), f("a"), []int{1, 2}},
		{"전부 사라졌다", f("a", "b"), f(), []int{0, 1}},
	}
	for _, c := range cases {
		if got := Diff(c.old, c.new); !reflect.DeepEqual(got, c.want) {
			t.Errorf("%s: = %v, 원하는 값 %v", c.name, got, c.want)
		}
	}
}
