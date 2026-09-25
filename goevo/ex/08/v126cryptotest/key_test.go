// 슬라이드 p8-v126-cryptotest — cryptotest.SetGlobalRandom, Go 1.26
package key

import (
	"testing"
	"testing/cryptotest"
)

func TestSeed1(t *testing.T) {
	cryptotest.SetGlobalRandom(t, 1)
	t.Log(Fingerprint(), Fingerprint())
}

func TestSeed1Again(t *testing.T) {
	cryptotest.SetGlobalRandom(t, 1)
	t.Log(Fingerprint(), Fingerprint())
}

func TestSeed2(t *testing.T) {
	cryptotest.SetGlobalRandom(t, 2)
	t.Log(Fingerprint(), Fingerprint())
}
