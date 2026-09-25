// 슬라이드 p7-v121-small2 — AvailableBuffer 외 둘, Go 1.21
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"reflect"
	"strconv"
)

func main() {
	var buf bytes.Buffer
	for i := 0; i < 3; i++ {
		b := strconv.AppendInt(buf.AvailableBuffer(), int64(i*i), 10)
		buf.Write(append(b, ' ')) // no temporary slice
	}
	fmt.Printf("%q\n", buf.String())

	b := binary.NativeEndian.AppendUint16(nil, 0x0102)
	fmt.Println(b, "(little-endian on arm64)")

	m := map[string]int{"a": 1}
	reflect.ValueOf(m).Clear() // same as the clear built-in
	fmt.Println(len(m))
}
