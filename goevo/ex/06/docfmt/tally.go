// 슬라이드 p6-v119-docfmt — 1.19 이전 흔했던 주석 모양, Go 1.19

// Package tally counts things.
//
// Usage
//
// Call New, then Add:
//   - one item at a time
//   - or many at once
//
// Example:
//	t := tally.New()
package tally

// New returns an empty counter.
func New() map[string]int { return map[string]int{} }
