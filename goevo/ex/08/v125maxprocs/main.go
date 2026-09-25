// 슬라이드 p8-v125-maxprocs — 컨테이너를 아는 GOMAXPROCS, Go 1.25
package main

import (
	"fmt"
	"os"
	"runtime"
)

// show prints "NumCPU" instead of the number, so the capture
// does not depend on how many cores this machine has.
func show(step string) {
	n, v := runtime.GOMAXPROCS(0), "NumCPU"
	if n != runtime.NumCPU() {
		v = fmt.Sprint(n)
	}
	fmt.Printf("%-27s GOMAXPROCS = %s\n", step, v)
}

func main() {
	fmt.Printf("env GOMAXPROCS=%q\n", os.Getenv("GOMAXPROCS"))
	show("start")
	runtime.GOMAXPROCS(1) // manual: turns the defaults off
	show("after GOMAXPROCS(1)")
	runtime.SetDefaultGOMAXPROCS() // new in 1.25
	show("after SetDefaultGOMAXPROCS")
}
