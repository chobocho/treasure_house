// 슬라이드 p5-v111-wasm — _js 파일은 GOOS=js 에서만, Go 1.11
package main

import "syscall/js"

func where() string {
	return js.Global().Get("navigator").Get("userAgent").String()
}
