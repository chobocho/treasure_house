// 슬라이드 p5-v114-small — NumError.Unwrap·FMA·Lmsgprefix, Go 1.14
package main

import (
	"errors"
	"fmt"
	"log"
	"math"
	"os"
	"strconv"
)

func main() {
	_, err := strconv.ParseInt("99999999999999999999", 10, 64)
	fmt.Println(err)
	fmt.Println("is ErrRange:", errors.Is(err, strconv.ErrRange))

	x, y, z := 0.1, 10.0, -1.0
	fmt.Println(x*y+z, math.FMA(x, y, z)) // one rounding vs two

	l := log.New(os.Stdout, "app: ", log.Lshortfile)
	l.Println("prefix at line start")
	l.SetFlags(log.Lshortfile | log.Lmsgprefix)
	l.Println("prefix before message")
}
