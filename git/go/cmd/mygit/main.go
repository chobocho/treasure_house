// mygit 명령 — mygit.Run 을 진짜 표준 스트림에 잇는다.
package main

import (
	"os"

	"mygit"
)

func main() {
	code, out, err := mygit.Run(os.Args[1:], "", nil, nil)
	os.Stdout.Write(out)
	os.Stderr.Write(err)
	os.Exit(code)
}
