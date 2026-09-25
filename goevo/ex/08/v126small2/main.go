// 슬라이드 p8-v126-small2 — x509 용도 이름·ast.ParseDirective, Go 1.26
package main

import (
	"crypto/x509"
	"fmt"
	"go/ast"
	"go/token"
)

func main() {
	// KeyUsage and ExtKeyUsage print their RFC 5280 names.
	ku := x509.KeyUsageDigitalSignature
	eku := x509.ExtKeyUsageServerAuth
	fmt.Println(ku, "|", eku, "|", eku.OID())

	// ParseDirective understands the //tool:name args convention.
	for _, c := range []string{
		"//go:generate stringer -type=Op",
		"//mytool:check strict fast",
		"// go:build not a directive (space)",
	} {
		d, ok := ast.ParseDirective(token.NoPos, c)
		if !ok {
			fmt.Printf("%-38q no directive\n", c)
			continue
		}
		args, _ := d.ParseArgs()
		fmt.Printf("%-38q tool=%s name=%s args=%d\n",
			c, d.Tool, d.Name, len(args))
	}
}
