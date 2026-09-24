// 슬라이드 p4-v19-monotonic — 단조 시계, Go 1.9
package main

import (
	"fmt"
	"strings"
	"time"
)

func main() {
	t := time.Now() // wall clock + monotonic reading
	fmt.Println("m= in String:", strings.Contains(t.String(), " m="))

	later := t.Add(90 * time.Minute) // both readings move
	fmt.Println("Sub:", later.Sub(t))

	w := t.Round(0) // Round(0) strips the monotonic reading
	fmt.Println("after Round(0):", strings.Contains(w.String(), " m="))
	fmt.Println("Equal:", t.Equal(w), " ==:", t == w)
}
