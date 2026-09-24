// 슬라이드 p1-naming — 소문자 이름을 밖에서 부르면, 1.27.1 에서의 동작
package main

import (
	"fmt"

	"ex/01/export/shape"
)

func main() {
	c := shape.Circle{Radius: 2}
	fmt.Println(shape.Area(c))
	fmt.Println(c.cached)
	fmt.Println(shape.perimeter(c))
}
