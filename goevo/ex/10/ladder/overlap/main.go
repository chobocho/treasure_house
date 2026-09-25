// 슬라이드 p10-ladder-2 — 겹치는 인터페이스 메서드, Go 1.14
package main

import (
	"fmt"
	"io"
)

type ReadCloseWriteCloser interface {
	io.ReadCloser
	io.WriteCloser // Close appears twice
}

func main() { fmt.Println(ReadCloseWriteCloser(nil) == nil) }
