// 슬라이드 p5-v116-notifyctx — 신호가 오면 취소되는 context, Go 1.16
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
)

func main() {
	bg := context.Background()
	ctx, stop := signal.NotifyContext(bg, os.Interrupt)
	defer stop()

	// Send ourselves an interrupt, as Ctrl-C would.
	p, _ := os.FindProcess(os.Getpid())
	p.Signal(os.Interrupt)

	<-ctx.Done()
	fmt.Println("stopped:", ctx.Err())
}
