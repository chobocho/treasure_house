// 슬라이드 p8-v125-jsonv2 — 실험 encoding/json/v2, Go 1.25
package main

import (
	jsonv1 "encoding/json"
	"encoding/json/v2"
	"fmt"
)

type User struct {
	Name  string
	Tags  []string
	Admin bool
}

func main() {
	u := User{Name: "gopher"} // Tags is a nil slice
	b1, _ := jsonv1.Marshal(u)
	b2, _ := json.Marshal(u)
	fmt.Printf("v1 marshal: %s\nv2 marshal: %s\n", b1, b2)

	in := []byte(`{"name":"eve","admin":true}`) // lower-case keys
	var x1, x2 User
	err1 := jsonv1.Unmarshal(in, &x1)
	err2 := json.Unmarshal(in, &x2)
	fmt.Printf("v1 unmarshal: %+v %v\n", x1, err1)
	fmt.Printf("v2 unmarshal: %+v %v\n", x2, err2)

	dup := []byte(`{"Admin":false,"Admin":true}`) // duplicate name
	fmt.Println("v1 duplicate:", jsonv1.Unmarshal(dup, &x1))
	fmt.Println("v2 duplicate:", json.Unmarshal(dup, &x2))
}
