// 슬라이드 p4-v110-builder — 할당 수 비교, Go 1.10
package main

import (
	"bytes"
	"strings"
	"testing"
)

var parts = strings.Fields("the quick brown fox jumps over a lazy dog")

func BenchmarkConcat(b *testing.B) {
	for i := 0; i < b.N; i++ {
		s := ""
		for _, p := range parts {
			s += p
		}
	}
}

func BenchmarkBuffer(b *testing.B) {
	for i := 0; i < b.N; i++ {
		var buf bytes.Buffer
		for _, p := range parts {
			buf.WriteString(p)
		}
		_ = buf.String() // String copies the bytes
	}
}

func BenchmarkBuilder(b *testing.B) {
	for i := 0; i < b.N; i++ {
		var sb strings.Builder
		for _, p := range parts {
			sb.WriteString(p)
		}
		_ = sb.String()
	}
}

func BenchmarkBuilderGrow(b *testing.B) {
	for i := 0; i < b.N; i++ {
		var sb strings.Builder
		sb.Grow(64) // one allocation up front
		for _, p := range parts {
			sb.WriteString(p)
		}
		_ = sb.String()
	}
}
