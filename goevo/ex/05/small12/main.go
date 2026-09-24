// 슬라이드 p5-v112-small — ReplaceAll·UserHomeDir·StringWriter, Go 1.12
package main

import (
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	fmt.Println(strings.ReplaceAll("a-b-c-d", "-", "+"))
	fmt.Println(strings.Replace("a-b-c-d", "-", "+", -1)) // before

	home, err := os.UserHomeDir()
	fmt.Println(home, err)

	var w io.StringWriter = os.Stdout
	w.WriteString("io.StringWriter: os.Stdout has WriteString\n")
}
