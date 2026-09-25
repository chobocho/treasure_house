// 슬라이드 p7-v122-loopvartest — 잘못 통과하던 시험, Go 1.22
package even

import "testing"

func TestAllEvenBuggy(t *testing.T) {
	testCases := []int{1, 2, 4, 6}
	for _, v := range testCases {
		t.Run("sub", func(t *testing.T) {
			t.Parallel() // runs after the loop has finished
			if v&1 != 0 {
				t.Fatal("odd v", v)
			}
		})
	}
}
