// 슬라이드 p6-v120-ecdh — crypto/ecdh 로 X25519 키 합의, Go 1.20
package main

import (
	"bytes"
	"crypto/ecdh"
	"crypto/rand"
	"fmt"
)

func main() {
	curve := ecdh.X25519()
	alice, err := curve.GenerateKey(rand.Reader)
	if err != nil {
		panic(err)
	}
	bob, _ := curve.GenerateKey(rand.Reader)

	// Each side combines its private key with the other's public key.
	s1, _ := alice.ECDH(bob.PublicKey())
	s2, _ := bob.ECDH(alice.PublicKey())
	fmt.Println("same secret:", bytes.Equal(s1, s2), len(s1), "bytes")
	fmt.Println("public key:", len(alice.PublicKey().Bytes()), "bytes")

	// A NIST curve through the same interface.
	p, _ := ecdh.P256().GenerateKey(rand.Reader)
	fmt.Println("P-256 public:", len(p.PublicKey().Bytes()), "bytes")
}
