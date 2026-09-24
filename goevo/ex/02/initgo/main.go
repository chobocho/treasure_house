// 슬라이드 p2-v10-initgo — init 안에서 고루틴이 바로 돈다, Go 1
package main

import "fmt"

var PackageGlobal int

func initializationFunction(c chan int) {
	c <- 42
}

func init() {
	c := make(chan int)
	go initializationFunction(c)
	PackageGlobal = <-c // before Go 1 this deadlocked
}

func main() {
	fmt.Println("PackageGlobal =", PackageGlobal)
}
