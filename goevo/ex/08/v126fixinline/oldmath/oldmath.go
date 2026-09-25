// 슬라이드 p8-v126-fixinline — //go:fix inline 을 단 옛 API, Go 1.26
package oldmath

import "ex/08/v126fixinline/newmath"

// Sub returns x - y.
//
// Deprecated: the parameter order is confusing.
//
//go:fix inline
func Sub(y, x int) int {
	return newmath.Sub(x, y)
}

// Neg returns -x.
//
// Deprecated: use newmath.Sub(0, x).
//
//go:fix inline
func Neg(x int) int {
	return newmath.Sub(0, x)
}

//go:fix inline
const Pi = newmath.Pi
