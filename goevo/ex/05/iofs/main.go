// 슬라이드 p5-v116-iofs — fs.FS 하나로 디스크·메모리·embed 를, Go 1.16
package main

import (
	"bytes"
	"fmt"
	"io/fs"
	"os"
	"testing/fstest"
)

// countLines only needs read access to a tree of files.
func countLines(fsys fs.FS) (int, error) {
	n := 0
	walk := func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		b, err := fs.ReadFile(fsys, p)
		n += bytes.Count(b, []byte("\n"))
		return err
	}
	err := fs.WalkDir(fsys, ".", walk)
	return n, err
}

func main() {
	disk := os.DirFS("notes") // a directory on disk
	mem := fstest.MapFS{      // a tree in memory
		"x.txt":     {Data: []byte("a\nb\nc\n")},
		"sub/y.txt": {Data: []byte("d\n")},
	}
	fmt.Println(countLines(disk))
	fmt.Println(countLines(mem))
}
