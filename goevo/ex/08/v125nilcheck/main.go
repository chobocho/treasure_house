// 슬라이드 p8-v125-nilcheck — 늦춰졌던 nil 검사 버그 수정, Go 1.25
package main

import "os"

// The program from the Go 1.25 release notes: it uses f
// before checking err. Go 1.21-1.24 printed nothing and
// exited 0; the spec says f.Name() must panic here.
func main() {
	f, err := os.Open("nonExistentFile")
	name := f.Name()
	if err != nil {
		return
	}
	println(name)
}
