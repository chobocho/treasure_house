// 슬라이드 p7-v121-wasip1 — 그 밖의 GOOS, Go 1.21
//go:build !wasip1

package main

import "runtime"

func where() string { return runtime.GOOS + "/" + runtime.GOARCH }
