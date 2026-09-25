// 슬라이드 p6-v118-plusbuild — 반대 조건, Go 1.18

//go:build !linux && !android
// +build !linux,!android

package main

func osName() string { return "other" }
