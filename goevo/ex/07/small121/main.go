// 슬라이드 p7-v121-small — ErrUnsupported·BoolFunc·Testing, Go 1.21
package main

import (
	"errors"
	"flag"
	"fmt"
	"syscall"
	"testing"
)

func main() {
	fmt.Println(errors.Is(syscall.ENOSYS, errors.ErrUnsupported))
	fmt.Println(errors.Is(syscall.ENOENT, errors.ErrUnsupported))

	fs := flag.NewFlagSet("demo", flag.ContinueOnError)
	fs.BoolFunc("v", "verbose; may repeat", func(s string) error {
		fmt.Println("-v seen, value", s)
		return nil
	})
	fs.Parse([]string{"-v", "-v=false"})

	fmt.Println("inside go test?", testing.Testing())
}
