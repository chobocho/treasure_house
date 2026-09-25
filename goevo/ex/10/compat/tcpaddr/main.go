// 슬라이드 p10-compat-literal — 이름 없는 리터럴이 깨진 일, Go 1.1
package main

import (
	"fmt"
	"net"
)

// Compiled under Go 1, when TCPAddr had two fields (IP, Port).
var myAddr = &net.TCPAddr{
	net.IPv4(18, 26, 4, 9),
	80,
}

func main() {
	fmt.Println(myAddr)
}
