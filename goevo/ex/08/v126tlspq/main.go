// 슬라이드 p8-v126-tlspq — TLS 의 새 양자 내성 혼합 키 교환, Go 1.26
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"math/big"
	"net"
)

func cert() tls.Certificate {
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1),
	}
	pub := &key.PublicKey
	der, _ := x509.CreateCertificate(rand.Reader, tmpl, tmpl, pub, key)
	return tls.Certificate{Certificate: [][]byte{der}, PrivateKey: key}
}

func main() {
	certs := []tls.Certificate{cert()}
	a, b := net.Pipe()
	srv := tls.Server(a, &tls.Config{Certificates: certs})
	go srv.Handshake()

	// The client offers only the NIST-curve hybrid and plain P-256.
	cli := tls.Client(b, &tls.Config{
		InsecureSkipVerify: true, // self-signed demo certificate
		CurvePreferences: []tls.CurveID{
			tls.SecP256r1MLKEM768, tls.CurveP256,
		},
	})
	if err := cli.Handshake(); err != nil {
		panic(err)
	}
	st := cli.ConnectionState()
	fmt.Println("TLS 1.3:", st.Version == tls.VersionTLS13)
	fmt.Println("key exchange:", st.CurveID)
}
