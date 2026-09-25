// 슬라이드 p7-v121-maps — maps 패키지, Go 1.21
package main

import (
	"fmt"
	"maps"
)

func main() {
	stock := map[string]int{"apple": 3, "pear": 0, "fig": 5}
	backup := maps.Clone(stock)
	fmt.Println(maps.Equal(stock, backup))

	maps.DeleteFunc(stock, func(k string, v int) bool { return v == 0 })
	fmt.Println(stock, maps.Equal(stock, backup)) // fmt sorts keys

	maps.Copy(stock, map[string]int{"kiwi": 2, "fig": 6})
	fmt.Println(stock)

	same := maps.EqualFunc(stock, map[string]string{
		"apple": "3", "fig": "6", "kiwi": "2",
	}, func(n int, s string) bool { return fmt.Sprint(n) == s })
	fmt.Println(same)
}
