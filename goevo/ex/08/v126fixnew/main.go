// 슬라이드 p8-v126-fixnew — go fix -newexpr, Go 1.26
package main

import (
	"encoding/json"
	"fmt"
)

type Request struct {
	URL      string
	Attempts *int    // optional
	Label    *string // optional
}

func newInt(x int) *int { return &x }

func newString(s string) *string { return &s }

func main() {
	data, err := json.Marshal(&Request{
		URL:      "https://go.dev",
		Attempts: newInt(10),
		Label:    newString("retry"),
	})
	fmt.Println(string(data), err)
}
