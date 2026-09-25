// 슬라이드 p8-v125-flightrec — 트레이스 비행 기록기, Go 1.25
package main

import (
	"bytes"
	"fmt"
	"runtime/trace"
	"sync"
	"time"
)

func main() {
	fr := trace.NewFlightRecorder(trace.FlightRecorderConfig{
		MinAge:   2 * time.Second, // keep at least the last 2 s
		MaxBytes: 4 << 20,         // but no more than 4 MiB
	})
	if err := fr.Start(); err != nil {
		fmt.Println(err)
		return
	}
	defer fr.Stop()
	fmt.Println("recording:", fr.Enabled())

	other := trace.NewFlightRecorder(trace.FlightRecorderConfig{})
	fmt.Println("second recorder:", other.Start())

	// Some work that the program later decides was "too slow".
	var wg sync.WaitGroup
	for i := range 4 {
		d := time.Duration(i) * time.Millisecond
		wg.Go(func() { time.Sleep(d) })
	}
	wg.Wait()

	// Something went wrong: snapshot the ring buffer.
	var buf bytes.Buffer
	n, err := fr.WriteTo(&buf)
	fmt.Println("snapshot written:", n > 0, err)
	head, _, _ := bytes.Cut(buf.Bytes()[:16], []byte{0})
	fmt.Printf("trace header: %q\n", head)
}
