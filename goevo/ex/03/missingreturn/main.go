// 슬라이드 p3-v11-terminating — 규칙은 문법만 본다, Go 1.1
package main

import "fmt"

// x%2 is 0 or 1, but the compiler does not reason about values:
// an if without else is not a terminating statement.
func parity(x int) string {
	if x%2 == 0 {
		return "even"
	}
	if x%2 == 1 {
		return "odd"
	}
}

// a break makes the loop non-terminating, too
func loop() int {
	for {
		break
	}
}

func main() {
	fmt.Println(parity(3), loop())
}
