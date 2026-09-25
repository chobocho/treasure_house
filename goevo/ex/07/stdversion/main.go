// 슬라이드 p7-v123-stdversion — go 줄보다 새 API 를 잡는 vet, Go 1.23
package main

import (
	"fmt"
	"reflect"
)

func main() {
	fmt.Println(reflect.TypeFor[int]()) // added in Go 1.22
}
