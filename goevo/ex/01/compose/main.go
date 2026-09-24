// 슬라이드 p1-compose — 상속 대신 합성과 인터페이스, 1.27.1 에서의 동작
package main

import (
	"fmt"
	"strings"
)

// Any type with a Write method is a writer; nothing is declared.
type writer interface {
	Write(p []byte) (int, error)
}

type Logger struct {
	strings.Builder // embedded: its methods are promoted
	prefix          string
}

func (l *Logger) Log(s string) {
	l.WriteString(l.prefix + s + "\n")
}

func emit(w writer, s string) { w.Write([]byte(s)) }

func main() {
	l := &Logger{prefix: "[log] "}
	l.Log("started")
	emit(l, "raw bytes\n") // *Logger satisfies writer implicitly
	fmt.Print(l.String())
}
