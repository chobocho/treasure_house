// 슬라이드 p3-v12-cover — 일부러 두 갈래만 시험한다, Go 1.2
package grade

import "testing"

func TestGrade(t *testing.T) {
	for score, want := range map[int]string{95: "A", 75: "B"} {
		if got := Grade(score); got != want {
			t.Errorf("Grade(%d) = %q, want %q", score, got, want)
		}
	}
}
