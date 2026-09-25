// 슬라이드 p6-v118-tilde — ~ 가 없는 제약, Go 1.18
package main

import "fmt"

type Exact interface{ int | float64 }

type Loose interface{ ~int | ~float64 }

func Twice[N Exact](x N) N  { return x * 2 }
func Twice2[N Loose](x N) N { return x * 2 }

type Celsius float64

func main() {
	fmt.Println(Twice2(Celsius(21)))
	fmt.Println(Twice(Celsius(21)))
}
