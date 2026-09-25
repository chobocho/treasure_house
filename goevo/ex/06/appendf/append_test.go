// 슬라이드 p6-v119-append — Sprintf 와 Appendf 의 할당, Go 1.19
package main

import (
	"fmt"
	"testing"
)

var out []byte

func BenchmarkSprintf(b *testing.B) {
	buf := make([]byte, 0, 64)
	for i := 0; i < b.N; i++ {
		buf = append(buf[:0], fmt.Sprintf("id=%d", i)...)
	}
	out = buf
}

func BenchmarkAppendf(b *testing.B) {
	buf := make([]byte, 0, 64)
	for i := 0; i < b.N; i++ {
		buf = fmt.Appendf(buf[:0], "id=%d", i)
	}
	out = buf
}
