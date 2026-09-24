// 슬라이드 p5-v117-gobuild — arm64 이고 purego 가 아닐 때, Go 1.17

//go:build arm64 && !purego

package main

const impl = "fast path for arm64"
