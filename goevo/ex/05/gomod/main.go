// 슬라이드 p5-v111-modules — GOPATH 밖의 모듈, Go 1.11
package main

import (
	"fmt"
	"go/build"
	"os"
	"strings"
)

func main() {
	wd, _ := os.Getwd()
	gopath := build.Default.GOPATH
	fmt.Println("working dir:", wd)
	fmt.Println("GOPATH:     ", gopath)
	fmt.Println("inside GOPATH/src?",
		strings.HasPrefix(wd, gopath+"/src/"))
}
