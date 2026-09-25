// 슬라이드 p7-v124-vettests — vet 의 tests 분석기가 잡는 것, Go 1.24
package sum

import (
	"fmt"
	"testing"
)

func Testadd(t *testing.T) { // never runs: lower-case after Test
	if Add(1, 2) != 3 {
		t.Fatal("bad")
	}
}

func ExampleSub() { // documents a function that does not exist
	fmt.Println(Add(3, -1))
	// Output: 2
}
