// 슬라이드 p5-v113-whether — %v 와 %w, 그리고 Is 메서드, Go 1.13
package main

import (
	"errors"
	"fmt"
)

var ErrPermission = errors.New("permission denied")

// HTTPError matches ErrPermission when its status is 403.
type HTTPError struct{ Status int }

func (e HTTPError) Error() string {
	return fmt.Sprintf("http %d", e.Status)
}

func (e HTTPError) Is(target error) bool {
	return target == ErrPermission && e.Status == 403
}

func main() {
	base := HTTPError{Status: 403}
	wrapped := fmt.Errorf("fetch: %w", base)
	opaque := fmt.Errorf("fetch: %v", base)

	fmt.Println(wrapped, "|", opaque) // same text
	fmt.Println("wrapped:", errors.Is(wrapped, ErrPermission))
	fmt.Println("opaque: ", errors.Is(opaque, ErrPermission))
	fmt.Println("404:    ", errors.Is(HTTPError{404}, ErrPermission))
}
