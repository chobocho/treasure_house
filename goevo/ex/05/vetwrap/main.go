// 슬라이드 p5-v111-vet — printf 를 감싼 함수도 검사한다, Go 1.11
package main

import (
	"fmt"
	"os"
)

func logf(format string, args ...interface{}) {
	fmt.Fprint(os.Stderr, "[app] ")
	fmt.Fprintf(os.Stderr, format, args...)
}

func main() {
	logf("user %s logged in\n", 42)
	logf("%d items\n", 3)
}
