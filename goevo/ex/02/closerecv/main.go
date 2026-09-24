// 슬라이드 p2-v10-close — 받기 전용 채널은 닫을 수 없다, Go 1
package main

func main() {
	var c chan int
	var csend chan<- int = c
	var crecv <-chan int = c
	close(c)     // legal
	close(csend) // legal
	close(crecv) // illegal since Go 1
}
