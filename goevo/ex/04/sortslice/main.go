// 슬라이드 p4-v18-sortslice — sort.Slice, Go 1.8
package main

import (
	"fmt"
	"sort"
)

type person struct {
	name string
	age  int
}

// Before 1.8: a named type with three methods per ordering.
type byAge []person

func (s byAge) Len() int           { return len(s) }
func (s byAge) Less(i, j int) bool { return s[i].age < s[j].age }
func (s byAge) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }

func main() {
	people := []person{
		{"ann", 30}, {"bob", 25}, {"cat", 30}, {"dan", 25},
	}

	old := append([]person(nil), people...)
	sort.Sort(byAge(old))

	// Since 1.8: one call and a less function.
	sort.SliceStable(people, func(i, j int) bool {
		return people[i].age < people[j].age
	})
	fmt.Println(old)
	fmt.Println(people)
}
