// 슬라이드 p6-v119-netctx — 시간 초과와 context 오류, Go 1.19
package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"os"
	"time"
)

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0") // loopback only
	if err != nil {
		panic(err)
	}
	defer ln.Close()

	// 1. A dial whose context deadline has already passed.
	ctx, cancel := context.WithDeadline(context.Background(),
		time.Unix(1, 0))
	defer cancel()
	var d net.Dialer
	_, err = d.DialContext(ctx, "tcp", ln.Addr().String())
	report("dial", err)

	// 2. A read whose connection deadline has already passed.
	c, err := net.Dial("tcp", ln.Addr().String())
	if err != nil {
		panic(err)
	}
	defer c.Close()
	c.SetReadDeadline(time.Unix(1, 0))
	_, err = c.Read(make([]byte, 1))
	report("read", err)
}

func report(what string, err error) {
	var ne net.Error
	fmt.Printf("%s: timeout=%v ctx=%v os=%v\n", what,
		errors.As(err, &ne) && ne.Timeout(),
		errors.Is(err, context.DeadlineExceeded),
		errors.Is(err, os.ErrDeadlineExceeded))
}
