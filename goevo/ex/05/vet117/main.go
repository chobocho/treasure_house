// 슬라이드 p5-v117-vet — 무시되는 Is, 신호를 잃는 채널, Go 1.17
package main

import (
	"errors"
	"fmt"
	"os"
	"os/signal"
)

type MyError struct{ hint string }

func (m MyError) Error() string { return m.hint }

// Is has the wrong parameter type, so errors.Is never calls it.
func (MyError) Is(target interface{}) bool { return true }

func main() {
	x, y := MyError{"A"}, MyError{"B"}
	fmt.Println(errors.Is(x, y))

	c := make(chan os.Signal) // unbuffered: a signal can be dropped
	signal.Notify(c, os.Interrupt)
}
