// 슬라이드 p7-v122-goversion — go/version 패키지, Go 1.22
package main

import (
	"fmt"
	"go/version"
	"sort"
)

func main() {
	vs := []string{"go1.21.0", "go1.9", "go1.21rc2", "go1.21", "go1.10"}
	sort.Slice(vs, func(i, j int) bool {
		return version.Compare(vs[i], vs[j]) < 0
	})
	fmt.Println(vs) // go1.10 after go1.9; go1.21 < go1.21rc2 < go1.21.0

	for _, v := range []string{"go1.22.3", "go1.21rc2", "1.22", "go1"} {
		fmt.Printf("%-10s valid=%-5v lang=%q\n",
			v, version.IsValid(v), version.Lang(v))
	}
}
