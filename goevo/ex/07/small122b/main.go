// 슬라이드 p7-v122-small2 — Delete 의 꼬리·sql.Null[T], Go 1.22
package main

import (
	"database/sql"
	"fmt"
	"slices"
)

func main() {
	s := []*int{new(int), new(int), new(int), new(int)}
	s = slices.Delete(s, 1, 3)
	full := s[:cap(s)] // look past the new length
	fmt.Println(len(s), full[2] == nil, full[3] == nil)

	defer func() { fmt.Println("recovered:", recover()) }()
	var n sql.Null[int]
	n.Scan(int64(7))
	fmt.Println(n.V, n.Valid)
	_ = slices.Insert([]int{1}, 5) // out of range, even with no values
}
