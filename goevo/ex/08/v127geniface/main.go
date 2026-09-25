// 슬라이드 p8-v127-geniface — 인터페이스를 못 채운다, Go 1.27
package main

type I interface{ M() }

type T struct{}

func (T) M[P any]() {}

func main() {
	T{}.M[int]()  // fine: an instantiated call
	var _ I = T{} // T has no method M() — only the generic M[P]
}
