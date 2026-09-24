// 슬라이드 p5-v116-ioutil — io/ioutil 의 새 자리, Go 1.16
package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	dir, _ := os.MkdirTemp("", "demo") // was ioutil.TempDir
	defer os.RemoveAll(dir)

	p := filepath.Join(dir, "a.txt")
	os.WriteFile(p, []byte("hello\n"), 0o644) // was ioutil.WriteFile
	b, _ := os.ReadFile(p)                    // was ioutil.ReadFile
	fmt.Printf("%q\n", b)

	all, _ := io.ReadAll(strings.NewReader("abc")) // was ioutil.ReadAll
	n, _ := io.Copy(io.Discard, strings.NewReader("xyz"))
	fmt.Println(string(all), n)

	entries, _ := os.ReadDir(dir) // []os.DirEntry, not []fs.FileInfo
	for _, e := range entries {
		fmt.Println(e.Name(), e.IsDir())
	}
}
