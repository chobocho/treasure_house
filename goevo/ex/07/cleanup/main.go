// 슬라이드 p7-v124-cleanup — AddCleanup 과 SetFinalizer, Go 1.24
package main

import (
	"fmt"
	"runtime"
	"slices"
	"time"
)

type Node struct {
	next *Node
	buf  []byte
}

func cycle() *Node {
	a, b := &Node{buf: make([]byte, 64)}, &Node{buf: make([]byte, 64)}
	a.next, b.next = b, a // a cycle
	return a
}

func main() {
	ran := make(chan string, 4)

	f := cycle()
	runtime.SetFinalizer(f, func(*Node) { ran <- "finalizer" })

	c := cycle()
	// The argument must not point at c, or c would never be freed.
	send := func(name string) { ran <- name }
	runtime.AddCleanup(c, send, "cleanup")
	runtime.AddCleanup(c, send, "cleanup 2")

	f, c = nil, nil
	for i := 0; i < 3; i++ {
		runtime.GC()
		time.Sleep(20 * time.Millisecond)
	}
	close(ran)
	var got []string
	for s := range ran {
		got = append(got, s)
	}
	slices.Sort(got) // cleanups run in no particular order
	fmt.Println("ran:", got)
}
