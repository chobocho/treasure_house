// 슬라이드 p5-v113-small — ToValidUTF8·IsZero·Duration 단위, Go 1.13
package main

import (
	"fmt"
	"reflect"
	"strings"
	"time"
)

type Config struct {
	Name string
	Port int
}

func main() {
	bad := "caf\xe9 ok \xff\xfe!"
	fmt.Printf("%q\n", strings.ToValidUTF8(bad, "?"))

	fmt.Println(reflect.ValueOf(Config{}).IsZero(),
		reflect.ValueOf(Config{Port: 80}).IsZero())

	d := 1500 * time.Microsecond
	fmt.Println(d, d.Milliseconds(), d.Microseconds())
}
