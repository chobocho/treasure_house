// 슬라이드 p5-v117-shuffle — -shuffle 과 T.Setenv, Go 1.17
package shuffle

import (
	"os"
	"testing"
)

func TestFirst(t *testing.T) {
	if n := Record("first"); n != 1 {
		t.Errorf("first ran as step %d", n) // hidden order dependency
	}
}

func TestSecond(t *testing.T) { Record("second") }

func TestThird(t *testing.T) {
	t.Setenv("APP_MODE", "test") // restored after the test
	t.Log("APP_MODE =", os.Getenv("APP_MODE"))
}
