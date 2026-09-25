// 슬라이드 p6-v118-fuzz — 퍼즈 테스트와 씨앗 말뭉치, Go 1.18
package abbrev

import (
	"testing"
	"unicode/utf8"
)

func FuzzAbbrev(f *testing.F) {
	// Seed corpus: run by every plain `go test`.
	f.Add("hello", 3)
	f.Add("", 0)
	f.Fuzz(func(t *testing.T, s string, n int) {
		if !utf8.ValidString(s) {
			t.Skip("only valid UTF-8 input")
		}
		got := Abbrev(s, n)
		if len(got) > len(s) || !utf8.ValidString(got) {
			t.Errorf("Abbrev(%q, %d) = %q", s, n, got)
		}
	})
}
