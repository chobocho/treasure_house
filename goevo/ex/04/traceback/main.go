// 슬라이드 p4-v16-traceback — 패닉 때 찍히는 고루틴, Go 1.6
package main

func main() {
	ready := make(chan bool)
	go func() {
		ready <- true
		select {} // an idle helper goroutine
	}()
	<-ready
	panic("boom")
}
