// 슬라이드 p5-v114-overlap — 겹치는 메서드 집합의 임베딩, Go 1.14
package main

import (
	"fmt"
	"io"
	"strings"
)

// Both embedded interfaces declare Close() error.
type ReadWriteCloser interface {
	io.ReadCloser
	io.WriteCloser
}

type buffer struct{ strings.Builder }

func (b *buffer) Read(p []byte) (int, error) { return 0, io.EOF }
func (b *buffer) Close() error               { return nil }

func main() {
	var rwc ReadWriteCloser = &buffer{}
	fmt.Fprint(rwc, "diamond embedding works")
	fmt.Println(rwc.(*buffer).String(), rwc.Close())
}
