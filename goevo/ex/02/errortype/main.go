// 슬라이드 p2-v10-error — 내장 error 와 errors 패키지, Go 1
package main

import (
	"errors"
	"fmt"
	"os"
)

var ErrEmpty = errors.New("empty name")

func open(name string) error {
	if name == "" {
		return ErrEmpty
	}
	_, err := os.Open(name)
	return err
}

func main() {
	fmt.Println(open(""))
	err := open("nope")
	fmt.Printf("%T\n%v\n", err, err)
}
