// 슬라이드 p8-v125-skid — ecdsa 원시 키와 x509 키 식별자, Go 1.25
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"fmt"
	"math/big"
)

func main() {
	// A fixed private scalar: the key and its id never change.
	d := make([]byte, 32)
	for i := range d {
		d[i] = byte(i + 1)
	}
	key, err := ecdsa.ParseRawPrivateKey(elliptic.P256(), d)
	if err != nil {
		fmt.Println(err)
		return
	}
	pub, _ := key.PublicKey.Bytes() // uncompressed point, no math/big
	fmt.Printf("public key: %d bytes, starts %#x\n", len(pub), pub[0])

	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "demo CA"},
		IsCA:         true, BasicConstraintsValid: true,
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl,
		&key.PublicKey, key)
	if err != nil {
		fmt.Println(err)
		return
	}
	cert, _ := x509.ParseCertificate(der)
	s256, s1 := sha256.Sum256(pub), sha1.Sum(pub)
	fmt.Printf("SubjectKeyId  %x\n", cert.SubjectKeyId)
	fmt.Printf("SHA-256[:20]  %x\n", s256[:20])
	fmt.Printf("SHA-1         %x\n", s1)
}
