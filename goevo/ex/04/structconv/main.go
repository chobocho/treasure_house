// 슬라이드 p4-v18-structconv — 태그만 다른 구조체 변환, Go 1.8
package main

import (
	"encoding/json"
	"fmt"
)

type dbUser struct {
	Name string `db:"name"`
}

type apiUser struct {
	Name string `json:"user_name"`
}

func main() {
	d := dbUser{Name: "gopher"}
	a := apiUser(d) // legal: tags are ignored in conversions
	b, _ := json.Marshal(a)
	fmt.Println(string(b))
}
