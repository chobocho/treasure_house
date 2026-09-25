// 슬라이드 p7-v122-loopvarfile — 이 파일만 go1.22 의미로, Go 1.22
//go:build go1.22

package main

func perIteration() []int {
	var ps []*int
	for i := 0; i < 3; i++ {
		ps = append(ps, &i)
	}
	return []int{*ps[0], *ps[1], *ps[2]}
}
