// 슬라이드 p6-v118-small — TryLock·AppendRune·reflect.Pointer, Go 1.18
package main

import (
	"fmt"
	"reflect"
	"sync"
	"unicode/utf8"
)

func main() {
	var mu sync.Mutex
	fmt.Println(mu.TryLock(), mu.TryLock()) // second try fails
	mu.Unlock()

	b := []byte("go")
	b = utf8.AppendRune(b, '→')
	b = utf8.AppendRune(b, '고')
	fmt.Println(string(b), len(b))

	t := reflect.TypeOf(&b)
	fmt.Println(t.Kind() == reflect.Pointer,
		reflect.Ptr == reflect.Pointer)
}
