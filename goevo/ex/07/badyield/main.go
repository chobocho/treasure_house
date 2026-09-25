// 슬라이드 p7-v123-yield — false 뒤에도 yield 를 부르면, Go 1.23
package main

import (
	"fmt"
	"iter"
)

// careless ignores yield's result: a bug the runtime catches.
func careless() iter.Seq[int] {
	return func(yield func(int) bool) {
		yield(1)
		yield(2)
	}
}

func main() {
	for v := range careless() {
		fmt.Println("got", v)
		break
	}
}
