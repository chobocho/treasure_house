// 슬라이드 p8-v126-secret — 실험을 켜지 않은 빌드, Go 1.26

//go:build !goexperiment.runtimesecret

package main

import "fmt"

func main() {
	fmt.Println("runtime/secret needs GOEXPERIMENT=runtimesecret")
}
