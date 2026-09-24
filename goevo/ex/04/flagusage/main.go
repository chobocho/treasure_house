// 슬라이드 p4-v15-flag — flag 사용법 메시지, Go 1.5
package main

import (
	"flag"
	"os"
)

func main() {
	fs := flag.NewFlagSet("demo", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)
	// A word in `backquotes` becomes the operand name.
	fs.Int("cpu", 1, "run `N` processes in parallel")
	fs.String("out", "", "write the result to `file`")
	fs.Bool("v", false, "verbose output")
	fs.PrintDefaults()
}
