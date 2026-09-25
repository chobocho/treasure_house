// 슬라이드 p7-v124-kdf — crypto/hkdf·pbkdf2·sha3, Go 1.24
package main

import (
	"crypto/hkdf"
	"crypto/pbkdf2"
	"crypto/sha256"
	"crypto/sha3"
	"fmt"
)

func main() {
	secret, salt := []byte("shared secret"), []byte("salt")

	k1, err := hkdf.Key(sha256.New, secret, salt, "enc key", 16)
	fmt.Printf("hkdf   %x %v\n", k1, err)

	k2, err := pbkdf2.Key(sha256.New, "password", salt, 4096, 16)
	fmt.Printf("pbkdf2 %x %v\n", k2, err)

	sum := sha3.Sum256([]byte("go"))
	fmt.Printf("sha3   %x\n", sum[:16])
}
