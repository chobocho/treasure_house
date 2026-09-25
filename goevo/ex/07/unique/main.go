// 슬라이드 p7-v123-unique — unique 로 값 정규화, Go 1.23
package main

import (
	"fmt"
	"strings"
	"unique"
)

type Addr struct {
	Zone string
	Port int
}

func main() {
	a := strings.Repeat("eth", 2) // built at run time
	b := "etheth"
	ha, hb := unique.Make(a), unique.Make(b)
	fmt.Println(ha == hb, ha.Value()) // pointer comparison

	h1 := unique.Make(Addr{"eth0", 80})
	h2 := unique.Make(Addr{"eth0", 80})
	h3 := unique.Make(Addr{"eth1", 80})
	fmt.Println(h1 == h2, h1 == h3, h1.Value().Port)
}
