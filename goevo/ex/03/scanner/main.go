// 슬라이드 p3-v11-scanner — bufio.Scanner, Go 1.1
package main

import (
	"bufio"
	"fmt"
	"strings"
)

const input = "first line\r\nsecond line\nlast line without newline"

func main() {
	// default split: lines, terminator (\n or \r\n) stripped
	sc := bufio.NewScanner(strings.NewReader(input))
	for n := 1; sc.Scan(); n++ {
		fmt.Printf("%d %q\n", n, sc.Text())
	}
	if err := sc.Err(); err != nil {
		fmt.Println("error:", err)
	}

	// another split function: words
	words := bufio.NewScanner(strings.NewReader(input))
	words.Split(bufio.ScanWords)
	count := 0
	for words.Scan() {
		count++
	}
	fmt.Println("words:", count)

	// a pathologically long line stops the scan with an error
	huge := strings.Repeat("x", bufio.MaxScanTokenSize+1)
	long := bufio.NewScanner(strings.NewReader(huge))
	for long.Scan() {
	}
	fmt.Println("error:", long.Err())
}
