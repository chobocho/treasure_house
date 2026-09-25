// 슬라이드 p6-v118-constraint — 제약은 인터페이스, 합집합과 ~, Go 1.18
package main

import "fmt"

// Number is a constraint: an interface that lists a set of types.
type Number interface {
	~int | ~int64 | ~float64
}

// Sum may use + because every type in Number's type set has it.
func Sum[N Number](xs ...N) N {
	var total N
	for _, x := range xs {
		total += x
	}
	return total
}

// Celsius is not float64, but its underlying type is.
type Celsius float64

func main() {
	fmt.Println(Sum(1, 2, 3))
	fmt.Println(Sum(1.5, 2.25))
	fmt.Printf("%v %T\n", Sum[Celsius](20, 1.5), Sum[Celsius])
}
