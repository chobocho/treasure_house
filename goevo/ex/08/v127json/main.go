// 슬라이드 p8-v127-json — encoding/json/v2 의 엄격한 기본값, Go 1.27
package main

import (
	jsonv1 "encoding/json"
	"encoding/json/v2"
	"fmt"
)

type Point struct{ X, Y int }

func main() {
	dup := []byte(`{"X":1,"X":2}`)
	bad := []byte("{\"X\":1,\"note\":\"\xff\"}")

	var p Point
	fmt.Println("v1 dup:", jsonv1.Unmarshal(dup, &p), p)
	fmt.Println("v2 dup:", json.Unmarshal(dup, &p))

	var m map[string]any
	fmt.Println("v1 utf8:", jsonv1.Unmarshal(bad, &m))
	fmt.Println("v2 utf8:", json.Unmarshal(bad, &m) != nil)

	out, _ := json.Marshal(map[string]int{"b": 2, "a": 1},
		json.Deterministic(true))
	fmt.Println(string(out))
}
