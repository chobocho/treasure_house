// 슬라이드 p6-v118-vetgen — vet 이 타입 집합의 원소마다 검사, Go 1.18
package main

import "fmt"

// Print is fine for ~int, wrong for ~string.
func Print[T ~int | ~string](t T) {
	fmt.Printf("%d\n", t)
}

func main() {
	Print(7)
}
