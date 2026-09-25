// 슬라이드 p8-v127-infer — 대입 문맥 어디서나 함수 타입 추론, Go 1.27
package main

import "fmt"

func Format[T any](v T) string { return fmt.Sprintf("value: %v", v) }

type IntFormatter func(int) string

func main() {
	formatters := []IntFormatter{Format} // composite literal
	fn := IntFormatter(Format)           // conversion
	ch := make(chan IntFormatter, 1)
	ch <- Format // channel send
	fmt.Println(formatters[0](1), fn(2), (<-ch)(3))
}
