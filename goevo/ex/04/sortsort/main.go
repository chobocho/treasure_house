// 슬라이드 p4-v16-sort — sort.Sort 와 sort.Stable, Go 1.6
package main

import (
	"fmt"
	"sort"
)

type item struct {
	key  int
	name byte
}

type byKey []item

func (s byKey) Len() int           { return len(s) }
func (s byKey) Less(i, j int) bool { return s[i].key < s[j].key }
func (s byKey) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }

func show(s []item) {
	for _, it := range s {
		fmt.Printf("%c", it.name)
	}
	fmt.Println()
}

func main() {
	var a, b byKey
	for i := 0; i < 20; i++ { // keys 0,1,0,1,...; names a..t
		it := item{i % 2, byte('a' + i)}
		a, b = append(a, it), append(b, it)
	}
	sort.Sort(a)   // equal keys: order not specified
	sort.Stable(b) // equal keys keep their input order
	show(a)
	show(b)
}
