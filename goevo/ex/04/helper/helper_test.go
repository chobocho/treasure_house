// 슬라이드 p4-v19-helper — t.Helper(일부러 실패), Go 1.9
package helper

import "testing"

func checkPlain(t *testing.T, got, want int) {
	if got != want {
		t.Errorf("got %d, want %d", got, want) // reported here
	}
}

func checkHelper(t *testing.T, got, want int) {
	t.Helper() // report the caller's line instead
	if got != want {
		t.Errorf("got %d, want %d", got, want)
	}
}

func TestPlain(t *testing.T) {
	checkPlain(t, 1+1, 3)
}

func TestHelper(t *testing.T) {
	checkHelper(t, 1+1, 3)
}
