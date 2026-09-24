// 슬라이드 p5-v114-preempt — 함수 호출 없는 루프도 선점된다, Go 1.14
package main

import (
	"fmt"
	"runtime"
	"time"
)

var counter uint64

func main() {
	runtime.GOMAXPROCS(1) // one P: the spinner and main must share it

	go func() {
		for { // no function calls: no cooperative preemption point
			counter++
		}
	}()

	time.Sleep(50 * time.Millisecond) // the spinner takes the only P
	fmt.Println("main is running again")
	runtime.GC() // a GC needs every goroutine to stop, too
	fmt.Println("GC finished")
}
