// 슬라이드 p7-v124-rsamin — 1024비트 미만 RSA 키 거절, Go 1.24
package main

import (
	"crypto/rand"
	"crypto/rsa"
	"fmt"
)

func main() {
	key, err := rsa.GenerateKey(rand.Reader, 512)
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	fmt.Println("generated a", key.N.BitLen(), "bit key")
}
