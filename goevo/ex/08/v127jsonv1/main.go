// 슬라이드 p8-v127-jsonv1 — v2 위에서 도는 encoding/json, Go 1.27
package main

import (
	"encoding/json"
	"fmt"
)

type P struct {
	X int8
	S []int
	M map[string]int
}

func main() {
	inputs := []string{
		`{"X":"one"}`, `{"X":300}`, `{"X":1.5}`, `{"S":{}}`,
		`{"M":[]}`, `{"X":1,}`, `{"X":1}x`, `{"X":`, `[1,2]`,
	}
	for _, in := range inputs {
		var p P
		err := json.Unmarshal([]byte(in), &p)
		fmt.Printf("%-12s %v\n", in, err)
	}
}
