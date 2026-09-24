// 슬라이드 p1-csp — 통신으로 공유한다(CSP 계보), 1.27.1 에서의 동작
package main

import "fmt"

// generate sends 2, 3, 4, ... on ch.
func generate(ch chan<- int) {
	for i := 2; ; i++ {
		ch <- i
	}
}

// filter copies values from in to out, dropping multiples of p.
func filter(in <-chan int, out chan<- int, p int) {
	for {
		if i := <-in; i%p != 0 {
			out <- i
		}
	}
}

// The concurrent prime sieve: a chain of filter goroutines.
func main() {
	ch := make(chan int)
	go generate(ch)
	for n := 0; n < 10; n++ {
		p := <-ch
		fmt.Print(p, " ")
		next := make(chan int)
		go filter(ch, next, p)
		ch = next
	}
	fmt.Println()
}
