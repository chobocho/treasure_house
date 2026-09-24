// 슬라이드 p3-v11-intsize — 64비트 플랫폼의 int 는 64비트, Go 1.1
package main

import (
	"fmt"
	"strconv"
)

func main() {
	fmt.Println("int bits:", strconv.IntSize)

	x := ^uint32(0) // 0xffffffff
	i := int(x)     // -1 on 32-bit systems, 4294967295 on 64-bit
	fmt.Println("int(x):       ", i)
	fmt.Println("int(int32(x)):", int(int32(x))) // -1 everywhere
}
