// 슬라이드 p8-v126-cryptorand — rand 인자를 무시하는 암호 API, Go 1.26
package main

import (
	"bytes"
	"crypto/ecdh"
	"fmt"
)

// zeros is a "random" source that always returns the same bytes.
// Tests used to pass readers like this to get fixed keys.
type zeros struct{}

func (zeros) Read(p []byte) (int, error) {
	for i := range p {
		p[i] = 7
	}
	return len(p), nil
}

func main() {
	k1, err := ecdh.P256().GenerateKey(zeros{})
	if err != nil {
		panic(err)
	}
	k2, err := ecdh.P256().GenerateKey(zeros{})
	if err != nil {
		panic(err)
	}
	fmt.Println("same key from the same reader:",
		bytes.Equal(k1.Bytes(), k2.Bytes()))
}
