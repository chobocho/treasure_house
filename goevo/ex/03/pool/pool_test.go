// 슬라이드 p3-v13-pool — 시험과 B.RunParallel 벤치마크, Go 1.3
package pool

import "testing"

func TestLabel(t *testing.T) {
	for i := 0; i < 3; i++ {
		if got := Label(7); got != "id-7" {
			t.Fatalf("Label(7) = %q", got)
		}
	}
}

func BenchmarkLabel(b *testing.B) {
	b.RunParallel(func(pb *testing.PB) {
		// runs on GOMAXPROCS goroutines, sharing b.N iterations
		for pb.Next() {
			Label(42)
		}
	})
}
