// 슬라이드 p8-v126-allocs — Errorf·ReadAll 의 할당, Go 1.26
package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"runtime"
	"testing"
)

var sinkErr error

func main() {
	e := testing.AllocsPerRun(100, func() { sinkErr = errors.New("x") })
	f := testing.AllocsPerRun(100, func() { sinkErr = fmt.Errorf("x") })
	fmt.Println("errors.New:", e, "allocs; fmt.Errorf:", f, "allocs")

	// io.ReadAll of 1 MiB from a reader that hides its size.
	data := bytes.Repeat([]byte("go"), 1<<19)
	var m0, m1 runtime.MemStats
	runtime.ReadMemStats(&m0)
	b, err := io.ReadAll(io.MultiReader(bytes.NewReader(data)))
	runtime.ReadMemStats(&m1)
	fmt.Println("read", len(b), "bytes, err", err)
	fmt.Println("len == cap:", len(b) == cap(b))
	mib := float64(m1.TotalAlloc-m0.TotalAlloc) / (1 << 20)
	fmt.Printf("allocated in total: %.0f MiB\n", mib)
}
