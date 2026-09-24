// 슬라이드 p4-v16-small — time.Parse 와 없는 날, Go 1.6
package main

import (
	"fmt"
	"time"
)

func main() {
	days := []string{"2016-02-29", "2015-02-29", "2015-04-31"}
	for _, s := range days {
		_, err := time.Parse("2006-01-02", s)
		fmt.Println(s, "->", err)
	}
}
