// 슬라이드 p8-v126-signal — NotifyContext 의 원인(cause), Go 1.26
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(),
		syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// Send ourselves SIGTERM, as a process manager would.
	syscall.Kill(os.Getpid(), syscall.SIGTERM)
	<-ctx.Done()

	fmt.Println("Err:  ", ctx.Err())
	fmt.Println("Cause:", context.Cause(ctx))
}
