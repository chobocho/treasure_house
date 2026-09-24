// 슬라이드 p4-v17-lostcancel — 버린 cancel(일부러 틀림), Go 1.7
package main

import (
	"context"
	"fmt"
	"time"
)

func main() {
	ctx, _ := context.WithTimeout(context.Background(), time.Second)
	fmt.Println(ctx.Err())
}
