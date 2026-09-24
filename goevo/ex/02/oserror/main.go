// 슬라이드 p2-v10-error — os.Error 가 내장 error 로, Go 1
package main

import (
	"fmt"
	"os"
)

func open(name string) os.Error { // r60: os.Error
	_, err := os.Open(name)
	return err
}

func main() {
	fmt.Println(open("nope"))
}
