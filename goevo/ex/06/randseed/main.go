// 슬라이드 p6-v120-rand — 전역 난수 생성기의 자동 씨앗, Go 1.20
package main

import (
	"fmt"
	"math/rand"
)

func main() {
	// The sequence every Go program got before 1.20: seed 1.
	seed1 := rand.New(rand.NewSource(1))
	same := true
	for i := 0; i < 5; i++ {
		if rand.Int63() != seed1.Int63() {
			same = false
		}
	}
	fmt.Println("global generator == Seed(1):", same)
}
