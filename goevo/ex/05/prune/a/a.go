// 슬라이드 p5-v117-prune — 직접 의존 a 는 b 를 가져온다, Go 1.17
package a

import "example.com/b"

// Name reports the chain a -> b.
func Name() string { return "a uses " + b.Name() }
