// 패키지 compresslib — 압축 대백과사전의 Go 구현.
//
// 다섯 언어가 같은 바이트를 내야 하므로 알고리즘은 파이썬 참조와 한
// 줄씩 같다. 다른 것은 오류를 다루는 방식뿐이다.
//
// Go 답게 하려면 Encode/Decode 가 (결과, error) 를 돌려줘야 한다.
// 그런데 복호기 안쪽은 "여기서 더 못 간다" 는 자리가 수십 군데라, 그
// 전부를 error 로 위로 나르면 알고리즘이 오류 처리에 묻힌다 — 가르치는
// 글에 실릴 코드로는 최악이다. 그래서 안쪽은 fail() 로 panic 하고,
// 밖으로 나가는 Encode/Decode 만 recover 해서 error 로 바꾼다. 파서
// 계열에서 흔히 쓰는 방식이고, panic 이 패키지 밖으로 새 나가지 않는다.
package compresslib

import "fmt"

// codecError 는 우리가 던진 panic 임을 알아보는 표식이다. 진짜 버그로
// 인한 panic(nil 참조 따위)까지 삼키면 안 되므로 타입을 따로 둔다.
type codecError struct{ msg string }

func (e codecError) Error() string { return e.msg }

func fail(format string, args ...any) {
	panic(codecError{fmt.Sprintf(format, args...)})
}

// guard 는 defer 로 걸어 두고, 우리가 던진 panic 만 error 로 바꾼다.
func guard(err *error) {
	if r := recover(); r != nil {
		if ce, ok := r.(codecError); ok {
			*err = ce
			return
		}
		panic(r)
	}
}
