// 슬라이드 p8-v126-cryptotest — 키를 만들어 지문을 낸다, Go 1.26
package key

import (
	"crypto/ecdh"
	"crypto/sha256"
	"fmt"
)

// Fingerprint makes a fresh key and returns a short fingerprint.
// It takes no io.Reader: the randomness is implicit.
func Fingerprint() string {
	k, err := ecdh.X25519().GenerateKey(nil)
	if err != nil {
		panic(err)
	}
	sum := sha256.Sum256(k.PublicKey().Bytes())
	return fmt.Sprintf("%x", sum[:6])
}
