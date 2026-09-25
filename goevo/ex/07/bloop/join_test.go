// 슬라이드 p7-v124-bloop — testing.B.Loop, Go 1.24
package join

import (
	"strings"
	"testing"
)

// calls counts how often each benchmark function body starts.
var calls = map[string]int{}

func setup(name string) []string { // imagine something expensive
	calls[name]++
	return strings.Fields("a b c d e f g h")
}

func BenchmarkOld(b *testing.B) {
	parts := setup("old") // runs again for every b.N round
	b.ResetTimer()
	for range b.N {
		strings.Join(parts, ",") // result unused: may be optimized away
	}
	b.ReportMetric(float64(calls["old"]), "setups")
}

func BenchmarkLoop(b *testing.B) {
	parts := setup("loop") // the function body runs exactly once
	for b.Loop() {
		strings.Join(parts, ",") // kept alive by b.Loop
	}
	b.ReportMetric(float64(calls["loop"]), "setups")
}
