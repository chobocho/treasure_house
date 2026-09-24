// 슬라이드 p5-v117-small — math.MaxInt·UnixMilli·QuotedPrefix, Go 1.17
package main

import (
	"fmt"
	"math"
	"strconv"
	"time"
)

func main() {
	fmt.Println(math.MaxInt, math.MinInt == -math.MaxInt-1)
	var u uint = math.MaxUint
	fmt.Println(u)

	t := time.UnixMilli(1629072000123).UTC() // 1.17's release day
	fmt.Println(t, t.UnixMicro())

	q, err := strconv.QuotedPrefix(`"a \"quoted\" word" and the rest`)
	fmt.Println(q, err)
}
