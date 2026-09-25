// 슬라이드 p7-v123-linkname — 내부 기호 linkname 금지, Go 1.23
package main

import (
	"fmt"
	_ "unsafe" // required for go:linkname
)

// gcount is internal to the runtime and not marked for linkname.
//
//go:linkname gcount runtime.gcount
func gcount() int32

func main() { fmt.Println(gcount() > 0) }
