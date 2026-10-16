// 수 — 정수와 실수, 그리고 2^53 너머. 읽을 타입을 내가 정한다.
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// region: numbers
type Req struct {
	Headcount int `json:"headcount"`
}

func main() {
	a, _ := json.Marshal(30)
	b, _ := json.Marshal(30.0) // float64 30 — .0 없이 쓴다
	fmt.Println("쓰기 30     :", string(a))
	fmt.Println("쓰기 30.0   :", string(b))

	var r Req // int 필드에 30.0 을 읽히면 거절한다
	err := json.Unmarshal([]byte(`{"headcount":30.0}`), &r)
	fmt.Println("int 에 30.0 :", err)

	big := "9007199254740993" // 2^53 + 1
	var n int64
	json.Unmarshal([]byte(big), &n)
	fmt.Println("int64 로    :", n)
	var x any // 타입을 안 정하면 float64 가 된다
	json.Unmarshal([]byte(big), &x)
	fmt.Printf("any 로      : %T %.0f\n", x, x)
	d := json.NewDecoder(strings.NewReader(big))
	d.UseNumber() // 수를 원문 문자열 그대로 둔다
	d.Decode(&x)
	fmt.Printf("UseNumber   : %T %v\n", x, x)
}

// endregion
