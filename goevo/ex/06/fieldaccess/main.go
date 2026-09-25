// 슬라이드 p6-v118-limits — 공통 필드도 못 읽는다, Go 1.18
package main

import "fmt"

type Cat struct{ Name string }
type Dog struct{ Name string }

func Names[T Cat | Dog](xs []T) []string {
	var r []string
	for _, x := range xs {
		r = append(r, x.Name) // every type in the set has Name
	}
	return r
}

func main() {
	fmt.Println(Names([]Cat{{"nabi"}}))
}
