// 슬라이드 p5-v113-numfmt — 라이브러리도 새 리터럴을 읽고 쓴다, Go 1.13
package main

import (
	"fmt"
	"strconv"
)

func main() {
	// base 0: the prefix decides, underscores are allowed.
	for _, s := range []string{"0b1010_1010", "0o17", "0x_FF", "1_0"} {
		n, err := strconv.ParseInt(s, 0, 64)
		fmt.Println(s, "->", n, err)
	}
	_, err := strconv.ParseInt("1_000", 10, 64) // not with base 10
	fmt.Println(err)

	fmt.Printf("%O %x %X\n", 64, 1.0, 0.5) // new verbs for 1.13
}
