// 슬라이드 p3-v14-testmain — TestMain 이 시험 실행 전후를 쥔다, Go 1.4
package store

import (
	"fmt"
	"os"
	"testing"
)

func TestMain(m *testing.M) {
	fmt.Println("setup: open DB once")
	DB = map[string]int{"answer": 42}

	code := m.Run() // runs every Test, Benchmark and Example

	fmt.Println("teardown: close DB, exit code", code)
	DB = nil
	os.Exit(code)
}

func TestGet(t *testing.T) {
	if got := Get("answer"); got != 42 {
		t.Fatalf("Get = %d", got)
	}
}

func TestMissing(t *testing.T) {
	if got := Get("nope"); got != 0 {
		t.Fatalf("Get = %d", got)
	}
}
