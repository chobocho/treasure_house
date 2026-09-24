// 슬라이드 p2-v10-copystruct — 안 보이는 필드가 있는 구조체 값, Go 1
package p

import "fmt"

type Struct struct {
	Public int
	secret int
}

func NewStruct(a int) Struct { // Note: not a pointer.
	return Struct{a, a * 2}
}

func (s Struct) String() string {
	return fmt.Sprintf("{%d (secret %d)}", s.Public, s.secret)
}
