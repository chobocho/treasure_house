// 슬라이드 p3-v14-internal — 바깥에서는 lib 만 쓴다, Go 1.4
package main

import (
	"fmt"

	"ex/03/intpkg/lib"
)

func main() {
	fmt.Println(lib.Masked())
}
