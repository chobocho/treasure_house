// 슬라이드 p4-v17-deadline — 시한과 표준 라이브러리, Go 1.7
package main

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

func slow(ctx context.Context) error {
	select {
	case <-time.After(time.Second): // the real work
		return nil
	case <-ctx.Done(): // the caller gave up
		return ctx.Err()
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(),
		10*time.Millisecond)
	defer cancel()
	fmt.Println("slow:", slow(ctx))

	// net/http carries a context on every request (not sent here).
	req, _ := http.NewRequest("GET", "http://example.invalid/", nil)
	req = req.WithContext(ctx)
	fmt.Println("request ctx:", req.Context().Err())
}
