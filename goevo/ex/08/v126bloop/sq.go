// 슬라이드 p8-v126-bloop — 벤치마크할 작은 함수, Go 1.26
package sq

// Point is small; returning it by value should not allocate.
type Point struct{ X, Y int }

func Scale(p Point, k int) *Point {
	q := Point{p.X * k, p.Y * k}
	return &q
}
