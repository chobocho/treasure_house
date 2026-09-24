// 슬라이드 p3-v14-testmain — 시험 전체가 공유하는 자원, Go 1.4
package store

// DB stands in for an expensive shared resource.
var DB map[string]int

// Get reads a key from DB.
func Get(k string) int { return DB[k] }
