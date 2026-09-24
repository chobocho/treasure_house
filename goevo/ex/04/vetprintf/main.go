// 슬라이드 p4-v16-vet — Printf 에 함수 값(일부러 틀림), Go 1.6
package main

import "fmt"

func name() string { return "gopher" }

func main() {
	fmt.Printf("hello, %s\n", name) // meant name()
}
