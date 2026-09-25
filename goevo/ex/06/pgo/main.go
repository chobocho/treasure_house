// 슬라이드 p6-v120-pgo — 프로파일을 먹여 인라인을 더 과감하게, Go 1.20
package main

import (
	"flag"
	"fmt"
	"os"
	"runtime/pprof"
)

// mix is too big for the normal inlining budget of 80:
// the call to rare alone costs 57.
func mix(x uint64) uint64 {
	x ^= x >> 33
	x *= 0xff51afd7ed558ccd
	x ^= x >> 33
	x *= 0xc4ceb9fe1a85ec53
	x ^= x >> 33
	if x == 0 {
		return rare()
	}
	return x
}

//go:noinline
func rare() uint64 { return 1 }

func main() {
	prof := flag.String("cpuprofile", "", "write a CPU profile here")
	n := flag.Int("n", 1000, "iterations")
	flag.Parse()
	if *prof != "" {
		f, _ := os.Create(*prof)
		pprof.StartCPUProfile(f)
		defer pprof.StopCPUProfile()
	}
	var sum uint64
	for i := 0; i < *n; i++ {
		sum += mix(uint64(i)) // the hot call site
	}
	fmt.Printf("%x\n", sum)
}
