// 슬라이드 p6-v118-netip — 비교 가능한 netip.Addr, Go 1.18
package main

import (
	"fmt"
	"net/netip"
)

func main() {
	a := netip.MustParseAddr("192.0.2.7")
	b := netip.AddrFrom4([4]byte{192, 0, 2, 7})
	fmt.Println(a == b) // comparable: == works

	seen := map[netip.Addr]int{a: 1} // usable as a map key
	seen[b]++
	fmt.Println(len(seen), seen[a])

	p := netip.MustParsePrefix("192.0.2.0/24")
	fmt.Println(p.Contains(a), p.Bits(), a.Next())

	ap := netip.AddrPortFrom(a, 8080)
	fmt.Println(ap, ap.Port())
}
