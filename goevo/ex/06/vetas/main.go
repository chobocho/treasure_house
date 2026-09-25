// 슬라이드 p6-v119-small2 — errors.As 의 둘째 인자가 *error, Go 1.19
package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
)

func main() {
	_, err := os.Open("/no/such/file")
	var target error
	if errors.As(err, &target) { // always true: every error is an error
		fmt.Println("matched:", target)
	}
	var pe *fs.PathError // what was meant
	fmt.Println(errors.As(err, &pe))
}
