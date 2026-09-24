// 슬라이드 p5-v115-panicprint — 파생 타입의 패닉 값도 찍힌다, Go 1.15
package main

type Code int // underlying type int

type Reason string // underlying type string

func main() {
	defer func() {
		panic(Reason("disk full")) // panics while panicking
	}()
	panic(Code(42))
}
