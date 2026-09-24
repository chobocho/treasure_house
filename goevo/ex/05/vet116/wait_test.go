// 슬라이드 p5-v116-vet — 고루틴 안의 t.Fatal, Go 1.16
package vet116

import "testing"

func TestAsync(t *testing.T) {
	done := make(chan bool)
	go func() {
		defer close(done)
		if 1+1 != 2 {
			t.Fatal("broken") // ends the goroutine, not the test
		}
	}()
	<-done
}
