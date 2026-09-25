// 슬라이드 p7-v124-weak — 약한 포인터 weak.Pointer, Go 1.24
package main

import (
	"fmt"
	"runtime"
	"weak"
)

type Image struct{ pixels []byte }

// cache holds images without keeping them alive.
var cache = map[string]weak.Pointer[Image]{}

func load(name string) *Image {
	if img := cache[name].Value(); img != nil {
		fmt.Println(name, "from cache")
		return img
	}
	fmt.Println(name, "loaded")
	img := &Image{make([]byte, 1<<20)}
	cache[name] = weak.Make(img)
	return img
}

func main() {
	a := load("cat.png")
	b := load("cat.png") // still strongly referenced by a
	fmt.Println(a == b)
	runtime.KeepAlive(a)
	a, b = nil, nil
	runtime.GC() // nothing else points at the image now
	load("cat.png")
}
