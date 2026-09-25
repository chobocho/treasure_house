// 슬라이드 p6-v118-contracts — 2019 초안의 contract 문법, Go 1.18
package main

import "fmt"

contract Sequence(T) {
	T string, []byte
}

func IndexByte(type T Sequence)(s T, b byte) int {
	for i := 0; i < len(s); i++ {
		if s[i] == b {
			return i
		}
	}
	return -1
}

func main() {
	fmt.Println(IndexByte("draft", 'a'))
}
