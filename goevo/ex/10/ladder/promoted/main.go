// 슬라이드 p10-ladder-5 — 끌어올린 필드를 구조체 리터럴에서, Go 1.27
package main

import "fmt"

type Base struct{ ID int }

type User struct {
	Base
	Name string
}

func main() {
	u := User{ID: 7, Name: "gopher"}
	fmt.Println(u.ID, u.Name)
}
