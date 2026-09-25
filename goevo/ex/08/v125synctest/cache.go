// 슬라이드 p8-v125-synctest — testing/synctest 정식판, Go 1.25
package cache

import (
	"sync"
	"time"
)

// Cache forgets each entry after its TTL, using a real timer.
type Cache struct{ m sync.Map }

func (c *Cache) Put(k, v string, ttl time.Duration) {
	c.m.Store(k, v)
	time.AfterFunc(ttl, func() { c.m.Delete(k) })
}

func (c *Cache) Get(k string) (any, bool) { return c.m.Load(k) }
