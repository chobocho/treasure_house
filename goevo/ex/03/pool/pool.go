// 슬라이드 p3-v13-pool — sync.Pool 로 버퍼 재사용, Go 1.3
package pool

import (
	"bytes"
	"strconv"
	"sync"
)

var bufs = sync.Pool{
	// New runs only when the pool has nothing to hand out
	New: func() interface{} { return new(bytes.Buffer) },
}

// Label formats "id-<n>" using a pooled buffer.
func Label(n int) string {
	b := bufs.Get().(*bytes.Buffer)
	b.Reset() // a reused buffer still holds old bytes
	b.WriteString("id-")
	b.WriteString(strconv.Itoa(n))
	s := b.String()
	bufs.Put(b)
	return s
}
