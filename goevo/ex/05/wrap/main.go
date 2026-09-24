// 슬라이드 p5-v113-wrap — %w 로 감싸고 errors.Is 로 찾는다, Go 1.13
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("not found")

func find(id int) error {
	return fmt.Errorf("find user %d: %w", id, ErrNotFound)
}

func load(id int) error {
	if err := find(id); err != nil {
		return fmt.Errorf("load profile: %w", err)
	}
	return nil
}

func main() {
	err := load(7)
	fmt.Println(err)
	fmt.Println("== ErrNotFound:    ", err == ErrNotFound)
	fmt.Println("errors.Is:         ", errors.Is(err, ErrNotFound))

	fmt.Println("chain:")
	for e := err; e != nil; e = errors.Unwrap(e) {
		fmt.Printf("  %T: %v\n", e, e)
	}
}
