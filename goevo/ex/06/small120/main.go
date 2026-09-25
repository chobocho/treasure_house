// 슬라이드 p6-v120-small — DateOnly·CutPrefix·Swap, Go 1.20
package main

import (
	"fmt"
	"strings"
	"sync"
	"time"
)

func main() {
	t := time.Date(2023, 2, 1, 9, 30, 0, 0, time.UTC)
	fmt.Println(t.Format(time.DateOnly), "|", t.Format(time.TimeOnly))
	fmt.Println(t.Format(time.DateTime))
	later := t.Add(time.Hour)
	fmt.Println(t.Compare(later), later.Compare(t), t.Compare(t))

	// CutPrefix: TrimPrefix plus "was it there?".
	rest, ok := strings.CutPrefix("--verbose", "--")
	fmt.Printf("%q %v\n", rest, ok)

	var m sync.Map
	m.Store("k", 1)
	prev, loaded := m.Swap("k", 2)
	fmt.Println(prev, loaded, m.CompareAndSwap("k", 2, 3))
	v, _ := m.Load("k")
	fmt.Println(v)
}
