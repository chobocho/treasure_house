// 슬라이드 p6-v119-append — fmt.Append 와 binary.AppendUvarint, Go 1.19
package main

import (
	"encoding/binary"
	"fmt"
)

func main() {
	buf := make([]byte, 0, 64)
	buf = fmt.Appendf(buf, "id=%d ", 42) // no string in between
	buf = fmt.Append(buf, "ok", true)
	buf = fmt.Appendln(buf)
	fmt.Printf("%q\n", buf)

	var b []byte
	b = binary.AppendUvarint(b, 300)
	b = binary.BigEndian.AppendUint16(b, 0xCAFE)
	fmt.Printf("% x\n", b)
}
