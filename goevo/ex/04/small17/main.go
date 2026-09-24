// 슬라이드 p4-v17-small — 작은 변화 셋, Go 1.7
package main

import (
	"encoding/json"
	"fmt"
	"reflect"
	"time"
)

func main() {
	fmt.Println(time.Duration(0)) // "0s", not "0"

	b, _ := json.Marshal(map[int]string{10: "ten", 2: "two"})
	fmt.Println(string(b)) // integer keys become strings

	t := reflect.StructOf([]reflect.StructField{
		{Name: "ID", Type: reflect.TypeOf(0), Tag: `json:"id"`},
	})
	fmt.Println(t)
}
