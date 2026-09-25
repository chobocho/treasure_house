// 슬라이드 p8-v126-greentea — Green Tea GC 가 기본값, Go 1.26
package main

import (
	"fmt"
	"runtime"
	"runtime/debug"
)

type node struct {
	left, right *node
	val         int
}

// build makes a tree of many small objects: the kind of heap the
// Green Tea collector scans page by page.
func build(depth int) *node {
	if depth == 0 {
		return &node{val: 1}
	}
	return &node{left: build(depth - 1), right: build(depth - 1)}
}

func sum(n *node) int {
	if n == nil {
		return 0
	}
	return n.val + sum(n.left) + sum(n.right)
}

func main() {
	exp := "(default)"
	if bi, ok := debug.ReadBuildInfo(); ok {
		for _, s := range bi.Settings {
			if s.Key == "GOEXPERIMENT" {
				exp = s.Value
			}
		}
	}
	fmt.Println("GOEXPERIMENT:", exp)

	t := build(16)
	runtime.GC()
	fmt.Println("leaves:", sum(t))
}
