// 슬라이드 p3-v11-terminating — return 규칙 완화, Go 1.1
package main

import "fmt"

// ends in an if-else whose branches both return
func sign(x int) string {
	if x < 0 {
		return "-"
	} else {
		return "+"
	}
}

// ends in a for loop with no condition and no break
func firstSquareOver(n int) int {
	for i := 0; ; i++ {
		if i*i > n {
			return i
		}
	}
}

// ends in a call to panic
func mustPositive(x int) int {
	if x > 0 {
		return x
	}
	panic("not positive")
}

func main() {
	fmt.Println(sign(-3), firstSquareOver(50), mustPositive(7))
}
