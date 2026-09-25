// 슬라이드 p7-v124-osroot — 디렉터리 밖으로 못 나가는 os.Root, Go 1.24
package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	dir, _ := os.MkdirTemp("", "root")
	defer os.RemoveAll(dir)
	up := filepath.Join(dir, "uploads")
	os.Mkdir(up, 0o755)
	os.WriteFile(filepath.Join(up, "a.txt"), []byte("hi"), 0o644)
	os.WriteFile(filepath.Join(dir, "secret"), []byte("s"), 0o600)
	os.Symlink("../secret", filepath.Join(up, "link"))

	root, err := os.OpenRoot(up)
	if err != nil {
		panic(err)
	}
	defer root.Close()
	names := []string{"a.txt", "../secret", "link", "/etc/hosts"}
	for _, name := range names {
		f, err := root.Open(name) // user-controlled name
		if err != nil {
			fmt.Println("refused:", err)
			continue
		}
		fmt.Println("opened:", name)
		f.Close()
	}
	b, _ := os.ReadFile(filepath.Join(up, "link")) // os follows it
	fmt.Printf("os.ReadFile(link) = %q\n", b)
}
