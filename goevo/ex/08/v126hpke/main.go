// 슬라이드 p8-v126-hpke — crypto/hpke (RFC 9180), Go 1.26
package main

import (
	"crypto/ecdh"
	"crypto/hpke"
	"fmt"
)

func main() {
	msg := []byte("hello, Go 1.26")
	info := []byte("goevo demo")
	kdf, aead := hpke.HKDFSHA256(), hpke.AES128GCM()

	for _, c := range []struct {
		name string
		kem  hpke.KEM
	}{
		{"DHKEM(X25519)", hpke.DHKEM(ecdh.X25519())},
		{"MLKEM768X25519 (post-quantum hybrid)", hpke.MLKEM768X25519()},
	} {
		priv, err := c.kem.GenerateKey()
		if err != nil {
			panic(err)
		}
		// Seal returns the encapsulated key followed by the ciphertext.
		ct, err := hpke.Seal(priv.PublicKey(), kdf, aead, info, msg)
		if err != nil {
			panic(err)
		}
		pt, err := hpke.Open(priv, kdf, aead, info, ct)
		fmt.Printf("%s\n  kem id %#04x, sealed %d bytes -> %q %v\n",
			c.name, c.kem.ID(), len(ct), pt, err)

		ct[len(ct)-1] ^= 1 // tamper with the tag
		_, err = hpke.Open(priv, kdf, aead, info, ct)
		fmt.Println("  tampered:", err)
	}
}
