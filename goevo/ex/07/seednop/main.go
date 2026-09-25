// 슬라이드 p7-v124-seednop — rand.Seed 는 무동작, Go 1.24
package main

import (
	"fmt"
	"math/rand"
)

func main() {
	rand.Seed(42) // deprecated since Go 1.20
	a := []int{rand.Intn(1000), rand.Intn(1000)}
	rand.Seed(42)
	b := []int{rand.Intn(1000), rand.Intn(1000)}
	same := a[0] == b[0] && a[1] == b[1]
	fmt.Println("same sequence after the same Seed:", same)
}
