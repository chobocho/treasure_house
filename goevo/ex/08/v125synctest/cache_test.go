// 슬라이드 p8-v125-synctest — testing/synctest 정식판, Go 1.25
package cache

import (
	"testing"
	"testing/synctest"
	"time"
)

func TestExpire(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		start := time.Now() // the bubble's fake clock
		t.Log("start:", start.UTC().Format(time.DateTime))

		c := new(Cache)
		c.Put("k", "v", time.Hour)

		time.Sleep(time.Hour - time.Nanosecond)
		synctest.Wait() // let the timer goroutine settle
		_, ok := c.Get("k")
		t.Log("1ns before TTL, present:", ok)

		time.Sleep(time.Nanosecond)
		synctest.Wait()
		_, ok = c.Get("k")
		t.Log("at TTL, present:", ok, "- elapsed", time.Since(start))
	})
}
