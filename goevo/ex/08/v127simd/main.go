// 슬라이드 p8-v127-simd — 이식 가능한 simd 패키지(실험), Go 1.27
package main

import (
	"fmt"
	"simd"
)

// dot adds a[i]*b[i], one vector at a time. The vector length is
// whatever this machine has; the code does not name it.
func dot(a, b []float32) float32 {
	var acc simd.Float32s
	for len(a) > 0 {
		va, n := simd.LoadFloat32sPart(a)
		vb, _ := simd.LoadFloat32sPart(b)
		acc = va.MulAdd(vb, acc)
		a, b = a[n:], b[n:]
	}
	out := make([]float32, acc.Len())
	acc.Store(out)
	var sum float32
	for _, x := range out {
		sum += x
	}
	return sum
}

func main() {
	a := []float32{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	b := []float32{1, 1, 1, 1, 1, 1, 1, 1, 1, 1}
	fmt.Println("lanes:", simd.Float32s{}.Len(), "dot:", dot(a, b))
}
