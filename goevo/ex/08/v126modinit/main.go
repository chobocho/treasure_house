// 슬라이드 p8-v126-modinit — go mod init 의 go 줄, Go 1.26
package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func main() {
	dir, err := os.MkdirTemp("", "modinit")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)

	out, err := exec.Command("go", "version").Output()
	if err != nil {
		panic(err)
	}
	fmt.Print("toolchain: ", string(out))

	cmd := exec.Command("go", "mod", "init", "example.com/hello")
	cmd.Dir = dir
	if msg, err := cmd.CombinedOutput(); err != nil {
		panic(string(msg))
	}
	mod, err := os.ReadFile(filepath.Join(dir, "go.mod"))
	if err != nil {
		panic(err)
	}
	fmt.Println("new go.mod:")
	lines := strings.Split(strings.TrimSpace(string(mod)), "\n")
	for _, line := range lines {
		fmt.Println(strings.TrimRight("  "+line, " "))
	}
}
