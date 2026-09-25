// 슬라이드 p7-v124-wasmexport — go:wasmexport 로 함수 내보내기, Go 1.24
package main

// add is callable from the WebAssembly host after the module starts.
//
//go:wasmexport add
func add(a, b int32) int32 { return a + b }

func main() {}
