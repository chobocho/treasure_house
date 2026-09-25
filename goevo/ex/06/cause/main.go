// 슬라이드 p6-v120-cause — 취소에 이유를 달기: WithCancelCause, Go 1.20
package main

import (
	"context"
	"errors"
	"fmt"
)

var errQuota = errors.New("quota exceeded")

func main() {
	ctx, cancel := context.WithCancelCause(context.Background())
	cancel(errQuota) // cancel, and say why

	<-ctx.Done()
	fmt.Println("Err:  ", ctx.Err())          // still just "canceled"
	fmt.Println("Cause:", context.Cause(ctx)) // the reason
	fmt.Println(errors.Is(context.Cause(ctx), errQuota))

	// Children inherit the cause.
	child, stop := context.WithCancel(ctx)
	defer stop()
	fmt.Println("child:", context.Cause(child))

	// Cancelled without a cause: Cause falls back to Err.
	plain, cancel2 := context.WithCancelCause(context.Background())
	cancel2(nil)
	fmt.Println("nil cause:", context.Cause(plain))
}
