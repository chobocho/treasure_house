// 슬라이드 p6-v118-fuzz — 퍼징할 함수(버그 하나), Go 1.18
package abbrev

// Abbrev shortens s to at most n bytes.
// Bug: it may cut a multi-byte rune in half.
func Abbrev(s string, n int) string {
	if n < 0 {
		n = 0
	}
	if len(s) <= n {
		return s
	}
	return s[:n]
}
