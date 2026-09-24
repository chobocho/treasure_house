// 슬라이드 p2-v10-copystruct — 다른 패키지의 구조체를 값으로 복사, Go 1
package main

import (
	"fmt"

	"ex/02/copystruct/p"
)

func main() {
	myStruct := p.NewStruct(23)
	copyOfMyStruct := myStruct
	fmt.Println(myStruct, copyOfMyStruct)
}
