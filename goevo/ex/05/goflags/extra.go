// 슬라이드 p5-v111-gorun — 태그가 있을 때만 들어오는 파일, Go 1.11

//go:build extra

package main

func init() { features = append(features, "extra") }
