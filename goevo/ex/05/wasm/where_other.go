// 슬라이드 p5-v111-wasm — js 가 아닌 모든 곳, Go 1.11

//go:build !js

package main

import "runtime"

func where() string { return runtime.GOOS + "/" + runtime.GOARCH }
