// 슬라이드 p8-v127-stdver — go test 가 stdversion 을 기본으로, Go 1.27
package last

import "strings"

// Ext returns the extension after the last dot.
// strings.CutLast is new in Go 1.27, but go.mod says go 1.26.
func Ext(name string) string {
	_, ext, _ := strings.CutLast(name, ".")
	return ext
}
