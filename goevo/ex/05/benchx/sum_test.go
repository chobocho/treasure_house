// 슬라이드 p5-v112-benchtime — b.N 을 모아 끝에 찍는다, Go 1.12
package benchx

import (
	"fmt"
	"os"
	"testing"
)

var seen []int // every b.N the framework tried

func BenchmarkSum(b *testing.B) {
	seen = append(seen, b.N)
	for i := 0; i < b.N; i++ {
		Sum(100)
	}
}

func TestMain(m *testing.M) {
	code := m.Run()
	fmt.Println("b.N values:", seen)
	os.Exit(code)
}
