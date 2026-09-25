// 슬라이드 p7-v121-context — WithoutCancel·AfterFunc·Cause, Go 1.21
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

var errSlow = errors.New("backend too slow")

func main() {
	parent, cancel := context.WithCancel(context.Background())
	detached := context.WithoutCancel(parent) // values yes, cancel no
	done := make(chan struct{})
	stop := context.AfterFunc(parent, func() { close(done) })
	cancel()
	<-done
	fmt.Println(parent.Err(), detached.Err(), stop())

	ctx, cancel2 := context.WithTimeoutCause(context.Background(),
		time.Millisecond, errSlow)
	defer cancel2()
	<-ctx.Done()
	fmt.Println(ctx.Err())
	fmt.Println(context.Cause(ctx))
}
