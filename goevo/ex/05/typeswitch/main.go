// 슬라이드 p5-v111-typeswitch — 가드 변수를 한 번도 안 쓰면, Go 1.11
package main

import "fmt"

func kind(v interface{}) string {
	switch x := v.(type) {
	case int:
		return "int"
	case string:
		return "string"
	}
	return "other"
}

func main() {
	fmt.Println(kind(1), kind("a"), kind(2.5))
}
