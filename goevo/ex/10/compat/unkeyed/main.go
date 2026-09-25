// 슬라이드 p10-compat-literal — 이름 없는 리터럴과 vet, Go 1.1
package main

import (
	"fmt"
	"net"
)

// Compiles today, but breaks again the day TCPAddr gains a field.
var unkeyed = &net.TCPAddr{net.IPv4(18, 26, 4, 9), 80, ""}

// Keyed: new fields take their zero value.
var keyed = &net.TCPAddr{IP: net.IPv4(18, 26, 4, 9), Port: 80}

func main() {
	fmt.Println(unkeyed, keyed)
}
