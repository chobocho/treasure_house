// 슬라이드 p1-naming — 대문자로 시작하면 공개, 1.27.1 에서의 동작
package shape

type Circle struct {
	Radius float64 // exported
	cached float64 // not exported
}

func Area(c Circle) float64 { return 3 * c.Radius * c.Radius }

func perimeter(c Circle) float64 { return 6 * c.Radius }
