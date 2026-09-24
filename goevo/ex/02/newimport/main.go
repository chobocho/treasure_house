// 슬라이드 p2-v10-hierarchy — Go 1 의 새 경로, Go 1
package main

import (
	"fmt"
	"net/http"
	"unicode/utf8"
)

func main() {
	fmt.Println(utf8.RuneLen('語'), http.StatusOK)
}
