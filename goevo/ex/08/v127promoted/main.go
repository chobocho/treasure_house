// 슬라이드 p8-v127-promoted — 끌어올린 필드를 리터럴 키로, Go 1.27
package main

import "fmt"

type Habitat struct {
	Burrow string
}

type Gopher struct {
	Name    string
	Habitat // embedded
}

func main() {
	g := Gopher{
		Name:   "Gopher",
		Burrow: "Burrow #42", // a promoted field as the key
	}
	fmt.Printf("%+v\n", g)
}
