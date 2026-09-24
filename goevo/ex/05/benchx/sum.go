// 슬라이드 p5-v112-benchtime — 벤치마크 대상, Go 1.12
package benchx

// Sum adds 1..n.
func Sum(n int) int {
	s := 0
	for i := 1; i <= n; i++ {
		s += i
	}
	return s
}
