// 슬라이드 p8-v126-fixinline — 옛 API 를 부르는 쪽, Go 1.26
package main

import (
	"fmt"

	"ex/08/v126fixinline/oldmath"
)

func main() {
	nine := oldmath.Sub(1, 10)
	fmt.Println(nine, oldmath.Neg(nine), oldmath.Pi)
}
