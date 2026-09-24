// 슬라이드 p4-v110-fields — bytes.Fields 조각의 용량, Go 1.10
package main

import (
	"bytes"
	"fmt"
)

func main() {
	in := []byte("ab cd ef")
	f := bytes.Fields(in)
	fmt.Println("len, cap of f[0]:", len(f[0]), cap(f[0]))

	// With cap == len, append must copy: the input is safe.
	f[0] = append(f[0], 'X')
	fmt.Printf("input: %s\n", in)
	fmt.Printf("f[0]:  %s\n", f[0])
}
