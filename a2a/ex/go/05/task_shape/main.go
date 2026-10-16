// SDK 의 Task 타입에는 어떤 필드가 있는가 — reflect 로 구조체를 훑는다.
//
//	go run ./05/task_shape
package main

import (
	"fmt"
	"reflect"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

// region: shape
// fields 는 구조체의 필드를 선언된 차례로 찍는다. json 태그의 이름이
// 와이어의 이름이고, encoding/json 도 이 차례로 적는다.
func fields(v any) {
	t := reflect.TypeOf(v)
	fmt.Println(t.Name())
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		tag := strings.Split(f.Tag.Get("json"), ",")
		fmt.Printf("  %d. %s: %s (%s)\n", i+1, tag[0], f.Type, f.Name)
	}
}

func main() {
	fields(a2a.Task{})
	fields(a2a.TaskStatus{})
}

// endregion
