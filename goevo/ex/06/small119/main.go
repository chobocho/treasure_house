// 슬라이드 p6-v119-small — JoinPath·TextVar·Abs, Go 1.19
package main

import (
	"flag"
	"fmt"
	"math"
	"net/netip"
	"net/url"
	"time"
)

func main() {
	u, _ := url.JoinPath("https://example.com/api/", "v1", "../v2")
	fmt.Println(u)

	// Any encoding.TextUnmarshaler can be a flag now.
	fs := flag.NewFlagSet("demo", flag.ContinueOnError)
	var addr netip.Addr
	def := netip.MustParseAddr("127.0.0.1")
	fs.TextVar(&addr, "addr", def, "listen address")
	fs.Parse([]string{"-addr", "::1"})
	fmt.Println(addr, addr.Is6())

	d := time.Duration(math.MinInt64)
	fmt.Println(d.Abs() == time.Duration(math.MaxInt64))
}
