// 슬라이드 p5-v113-as — errors.As 로 사슬에서 타입을 꺼낸다, Go 1.13
package main

import (
	"errors"
	"fmt"
	"os"
)

func readConfig(name string) error {
	_, err := os.Open(name)
	if err != nil {
		return fmt.Errorf("config: %w", err)
	}
	return nil
}

func main() {
	err := readConfig("missing.toml")
	fmt.Println(err)

	// A type assertion sees only the outer error.
	_, ok := err.(*os.PathError)
	fmt.Println("type assertion:", ok)

	var pe *os.PathError
	if errors.As(err, &pe) {
		fmt.Println("errors.As: op =", pe.Op, "path =", pe.Path)
	}
	fmt.Println("errors.Is(err, os.ErrNotExist):",
		errors.Is(err, os.ErrNotExist))
}
