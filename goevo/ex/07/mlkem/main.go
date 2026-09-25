// 슬라이드 p7-v124-mlkem — 양자 내성 키 교환 crypto/mlkem, Go 1.24
package main

import (
	"bytes"
	"crypto/mlkem"
	"fmt"
)

func main() {
	// Receiver: makes a key pair and publishes the encapsulation key.
	dk, err := mlkem.GenerateKey768()
	if err != nil {
		panic(err)
	}
	ekBytes := dk.EncapsulationKey().Bytes()

	// Sender: derives a shared key and a ciphertext from ekBytes.
	ek, err := mlkem.NewEncapsulationKey768(ekBytes)
	if err != nil {
		panic(err)
	}
	senderKey, ciphertext := ek.Encapsulate()

	// Receiver: recovers the same shared key from the ciphertext.
	receiverKey, err := dk.Decapsulate(ciphertext)
	if err != nil {
		panic(err)
	}
	fmt.Println("encapsulation key:", len(ekBytes), "bytes")
	fmt.Println("ciphertext:       ", len(ciphertext), "bytes")
	fmt.Println("shared key:       ", len(senderKey), "bytes, equal =",
		bytes.Equal(senderKey, receiverKey))
}
