// 슬라이드 p7-v124-fips — FIPS 140-3 모드, Go 1.24
package main

import (
	"crypto/fips140"
	"crypto/sha256"
	"fmt"
)

func main() {
	fmt.Println("FIPS 140-3 mode:", fips140.Enabled())
	sum := sha256.Sum256([]byte("go"))
	fmt.Printf("sha256: %x\n", sum[:8])
}
