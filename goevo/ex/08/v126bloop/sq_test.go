// 슬라이드 p8-v126-bloop — b.Loop 안의 인라인, Go 1.26
package sq

import "testing"

func BenchmarkScale(b *testing.B) {
	p := Point{1, 2}
	for b.Loop() {
		Scale(p, 3) // inlined: &q need not escape
	}
}
