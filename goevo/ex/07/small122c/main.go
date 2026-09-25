// 슬라이드 p7-v122-small3 — AppendEncode·JSON 의 \b \f, Go 1.22
package main

import (
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
)

func main() {
	buf := []byte("b64=")
	buf = base64.StdEncoding.AppendEncode(buf, []byte("go"))
	buf = append(buf, " hex="...)
	buf = hex.AppendEncode(buf, []byte("go"))
	fmt.Println(string(buf))

	out, _ := json.Marshal("a\bb\fc")
	fmt.Println(string(out))
}
