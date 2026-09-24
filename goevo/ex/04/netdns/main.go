// 슬라이드 p4-v15-netdns — Go DNS 해석기, Go 1.5
package main

import (
	"fmt"
	"net"
)

func main() {
	// localhost comes from /etc/hosts: no network needed.
	addrs, err := net.LookupHost("localhost")
	fmt.Println(addrs, err)
}
