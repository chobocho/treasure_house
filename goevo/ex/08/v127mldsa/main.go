// 슬라이드 p8-v127-mldsa — 양자 내성 서명 ML-DSA(FIPS 204), Go 1.27
package main

import (
	"crypto/mldsa"
	"fmt"
)

func main() {
	params := mldsa.MLDSA44()
	seed := make([]byte, mldsa.PrivateKeySize) // fixed seed, demo only
	key, err := mldsa.NewPrivateKey(params, seed)
	if err != nil {
		panic(err)
	}
	msg := []byte("Go 1.27")
	sig, err := key.SignDeterministic(msg, nil)
	if err != nil {
		panic(err)
	}
	pub := key.PublicKey()
	fmt.Println(params, len(pub.Bytes()), "byte key,",
		len(sig), "byte sig")
	fmt.Println("verify:", mldsa.Verify(pub, msg, sig, nil))
	msg[0] = 'g'
	fmt.Println("tampered:", mldsa.Verify(pub, msg, sig, nil) != nil)
}
