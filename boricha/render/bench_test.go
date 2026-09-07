package render

import (
	"io"
	"strings"
	"testing"
)

// 렌더러는 초당 60번 돈다. 그 한 번이 얼마나 걸리는지 재 둔다.
//
//	go test -bench . -benchmem ./render/

// 80×24 짜리 화면 하나. 한글이 섞인 실제 앱 화면과 비슷하게 만든다.
func benchView(mark int) string {
	lines := make([]string, 24)
	for i := range lines {
		lines[i] = "│ 보리차 목록 항목 " + strings.Repeat("─", 40) + " │"
	}
	lines[mark%24] = "│ ▸ 고른 줄 " + strings.Repeat("━", 44) + " │"
	return strings.Join(lines, "\n")
}

func BenchmarkNewFrame(b *testing.B) {
	v := benchView(0)
	for i := 0; i < b.N; i++ {
		_ = NewFrame(v, 80, 24)
	}
}

func BenchmarkDiffNoChange(b *testing.B) {
	f := NewFrame(benchView(0), 80, 24)
	for i := 0; i < b.N; i++ {
		_ = Diff(f, f)
	}
}

// 한 줄만 바뀌는 경우 — 실제 앱에서 가장 흔한 프레임이다.
func BenchmarkFlushOneLineChanged(b *testing.B) {
	r := New(io.Discard, 80, 24)
	r.Write(benchView(0))
	_ = r.Flush()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		r.Write(benchView(i))
		_ = r.Flush()
	}
}

// 아무것도 안 바뀐 경우 — 화면이 멈춰 있는 대부분의 시간이 이것이다.
func BenchmarkFlushUnchanged(b *testing.B) {
	r := New(io.Discard, 80, 24)
	v := benchView(0)
	r.Write(v)
	_ = r.Flush()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		r.Write(v)
		_ = r.Flush()
	}
}
