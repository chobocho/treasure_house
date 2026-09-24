// 슬라이드 p5-v117-small2 — ParseIP 앞자리 0·IsPrivate·Swap, Go 1.17
package main

import (
	"fmt"
	"net"
	"sync/atomic"
)

func main() {
	// Is 010 octal (8) or decimal (10)? Now: neither.
	fmt.Println(net.ParseIP("10.0.0.1"), net.ParseIP("010.0.0.1"))
	for _, s := range []string{"10.1.2.3", "8.8.8.8", "fd00::1"} {
		fmt.Println(s, net.ParseIP(s).IsPrivate())
	}

	var v atomic.Value
	v.Store("v1")
	old := v.Swap("v2")
	ok := v.CompareAndSwap("v2", "v3")
	fmt.Println(old, ok, v.Load())
}
