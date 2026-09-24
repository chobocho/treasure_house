// 슬라이드 p9-v128-encodedlen — 넘치는 EncodedLen 의 지금 모습, Go 1.28
package main

import (
	"encoding/base32"
	"encoding/base64"
	"fmt"
	"math"
)

func main() {
	n := math.MaxInt - 10 // encoded length does not fit in int
	fmt.Println("base64:", base64.StdEncoding.EncodedLen(n))
	fmt.Println("base32:", base32.StdEncoding.EncodedLen(n))
}
