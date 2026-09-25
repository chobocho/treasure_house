// 슬라이드 p8-v127-uuid — 표준 라이브러리의 uuid, Go 1.27
package main

import (
	"fmt"
	"uuid"
)

func main() {
	u := uuid.MustParse("F81D4FAE-7DEC-11D0-A765-00A0C91E6BF6")
	fmt.Println(u) // canonical lower-case form
	fmt.Println("version:", u[6]>>4)

	a, b := uuid.NewV7(), uuid.NewV7()
	fmt.Println("v7 version:", a[6]>>4, "sorted:", a.Compare(b) < 0)
	fmt.Println("v4 version:", uuid.New()[6]>>4)

	_, err := uuid.Parse("not-a-uuid")
	fmt.Println(err != nil, uuid.Nil(), uuid.Max())
}
