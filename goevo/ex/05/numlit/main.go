// 슬라이드 p5-v113-numlit — 새 숫자 리터럴, Go 1.13
package main

import "fmt"

func main() {
	const budget = 1_000_000 // digit separators
	mask := 0b1010_0110      // binary
	perm := 0o755            // octal with 0o
	old := 0755              // octal the old way, still valid
	half := 0x1p-1           // hexadecimal floating point
	z := 0b11i               // imaginary suffix on any literal

	fmt.Println(budget, mask, perm, old == perm, half, z)
}
