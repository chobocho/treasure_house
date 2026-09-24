// 슬라이드 p2-v10-equality — 구조체·배열의 같음, map 키로, Go 1
package main

import "fmt"

type Day struct {
	long  string
	short string
}

func main() {
	Christmas := Day{"Christmas", "XMas"}
	Thanksgiving := Day{"Thanksgiving", "Turkey"}
	holiday := map[Day]bool{
		Christmas:    true,
		Thanksgiving: true,
	}
	fmt.Printf("Christmas is a holiday: %t\n", holiday[Christmas])
	fmt.Println([2]int{1, 2} == [2]int{1, 2})
}
