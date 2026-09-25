// 슬라이드 p8-v127-randn — rand/v2 의 제네릭 메서드 N, Go 1.27
package main

import (
	"fmt"
	"math/rand/v2"
	"time"
)

type Weekday uint8

func main() {
	// A fixed seed gives the same output every run.
	r := rand.New(rand.NewPCG(1, 2))
	// Before 1.27: the function rand.N, or r.UintN plus a conversion.
	var d Weekday = r.N(Weekday(7))
	var t time.Duration = r.N(10 * time.Second)
	var n int64 = r.N(int64(1000))
	fmt.Println(d, t, n)
}
