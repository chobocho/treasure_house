// 슬라이드 p7-v121-pgo — default.pgo 와 탈가상화, Go 1.21
package main

import (
	"flag"
	"fmt"
	"os"
	"runtime/debug"
	"runtime/pprof"
)

type Shape interface{ Area() float64 }

type Circle struct{ R float64 }
type Square struct{ S float64 }

func (c Circle) Area() float64 { return 3 * c.R * c.R }
func (s Square) Area() float64 { return s.S * s.S }

func total(shapes []Shape) (t float64) {
	for _, s := range shapes {
		t += s.Area() // hot interface call, almost always Circle
	}
	return t
}

func main() {
	prof := flag.String("cpuprofile", "", "write a CPU profile here")
	n := flag.Int("n", 10, "rounds")
	flag.Parse()
	if *prof != "" {
		f, _ := os.Create(*prof)
		pprof.StartCPUProfile(f)
		defer pprof.StopCPUProfile()
	}
	shapes := []Shape{Square{1}}
	for i := 0; i < 99; i++ {
		shapes = append(shapes, Circle{1})
	}
	var sum float64
	for i := 0; i < *n; i++ {
		sum += total(shapes)
	}
	fmt.Println(sum)
	bi, _ := debug.ReadBuildInfo()
	for _, s := range bi.Settings {
		if s.Key == "-pgo" {
			fmt.Println("built with -pgo =", s.Value)
		}
	}
}
