// 슬라이드 p5-v116-small — flag.Func·net.ErrClosed·log.Default, Go 1.16
package main

import (
	"errors"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"strings"
)

func main() {
	var tags []string
	fs := flag.NewFlagSet("demo", flag.ExitOnError)
	fs.Func("tag", "add a tag (repeatable)", func(s string) error {
		tags = append(tags, strings.ToLower(s))
		return nil
	})
	fs.Parse([]string{"-tag", "Go", "-tag", "EMBED"})
	fmt.Println(tags)

	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	ln.Close()
	_, err := ln.Accept()
	fmt.Println(errors.Is(err, net.ErrClosed))

	log.Default().SetOutput(os.Stdout)
	log.Default().SetFlags(0)
	log.Println("log.Default is the standard logger")
}
