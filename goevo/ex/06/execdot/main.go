// 슬라이드 p6-v119-execdot — PATH 의 "." 은 오류, Go 1.19
package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
)

func main() {
	dir, err := os.MkdirTemp("", "execdot")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)
	os.Chdir(dir)
	// A program named "tool" sits in the current directory ...
	os.WriteFile("tool", []byte("#!/bin/sh\n"), 0o755)
	// ... and PATH lists "." (explicitly, or as an empty entry).
	os.Setenv("PATH", ".")

	path, err := exec.LookPath("tool")
	fmt.Printf("path=%q\n", path)
	fmt.Println("err:", err)
	fmt.Println("ErrDot:", errors.Is(err, exec.ErrDot))
}
