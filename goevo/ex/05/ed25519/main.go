// 슬라이드 p5-v113-ed25519 — 표준으로 온 crypto/ed25519, Go 1.13
package main

import (
	"bytes"
	"crypto/ed25519"
	"fmt"
)

func main() {
	// A fixed seed makes the key, and so the signature, reproducible.
	seed := bytes.Repeat([]byte{7}, ed25519.SeedSize)
	priv := ed25519.NewKeyFromSeed(seed)
	pub := priv.Public().(ed25519.PublicKey)

	msg := []byte("Go 1.13")
	sig := ed25519.Sign(priv, msg) // deterministic by design

	fmt.Printf("public key: %x...\n", pub[:8])
	fmt.Printf("signature:  %x... (%d bytes)\n", sig[:8], len(sig))
	fmt.Println("verify:", ed25519.Verify(pub, msg, sig))
	other := []byte("Go 1.12")
	fmt.Println("tampered:", ed25519.Verify(pub, other, sig))
}
