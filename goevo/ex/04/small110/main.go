// 슬라이드 p4-v110-small — 작은 변화 셋, Go 1.10
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"strings"
)

func main() {
	for _, x := range []float64{0.5, 1.5, 2.5, -2.5} {
		fmt.Println(x, math.Round(x), math.RoundToEven(x))
	}

	r := rand.New(rand.NewSource(1)) // fixed seed: same every run
	s := []string{"a", "b", "c", "d", "e"}
	r.Shuffle(len(s), func(i, j int) { s[i], s[j] = s[j], s[i] })
	fmt.Println(s)

	var v struct{ Name string }
	in := `{"Name":"go","Nmae":"typo"}`
	dec := json.NewDecoder(strings.NewReader(in))
	dec.DisallowUnknownFields()
	fmt.Println(dec.Decode(&v))
}
