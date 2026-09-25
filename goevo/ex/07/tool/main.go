// 슬라이드 p7-v124-tool — go:generate 가 모듈의 도구를 부른다, Go 1.24
package main

//go:generate go tool stamp version.go

import "fmt"

func main() { fmt.Println("app") }
