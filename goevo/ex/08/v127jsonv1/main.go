// 슬라이드 p8-v127-jsonv1 — v2 위에서 도는 encoding/json, Go 1.27
package main

import (
	"encoding/json"
	"fmt"
)

type Point struct{ X, Y int }

func main() {
	var p Point
	for _, in := range []string{`{"X":"one"}`, `{"X":1,}`, `[1,2]`} {
		err := json.Unmarshal([]byte(in), &p)
		fmt.Printf("%-12s %v\n", in, err)
	}
}
