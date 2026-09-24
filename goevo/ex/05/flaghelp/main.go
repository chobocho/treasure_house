// 슬라이드 p5-v115-flag — -h 로 도움말을 부르면 종료 코드 0, Go 1.15
package main

import (
	"flag"
	"fmt"
)

func main() {
	flag.Usage = func() { // the default prints the temp binary's path
		out := flag.CommandLine.Output()
		fmt.Fprintln(out, "usage: flaghelp [-n count]")
		flag.PrintDefaults()
	}
	n := flag.Int("n", 3, "how many times")
	flag.Parse()
	for i := 0; i < *n; i++ {
		fmt.Print("go ")
	}
	fmt.Println()
}
