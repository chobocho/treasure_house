// 슬라이드 p6-v120-errjoin — errors.Join 과 %w 여럿, Go 1.20
package main

import (
	"errors"
	"fmt"
	"io/fs"
)

var errEmpty = errors.New("empty name")

func validate(name string, size int) error {
	var errs []error
	if name == "" {
		errs = append(errs, errEmpty)
	}
	if size < 0 {
		errs = append(errs, fmt.Errorf("size %d: %w", size,
			fs.ErrInvalid))
	}
	return errors.Join(errs...) // nil when errs is empty
}

func main() {
	err := validate("", -1)
	fmt.Printf("%v\n---\n", err) // one line per error
	fmt.Println(errors.Is(err, errEmpty), errors.Is(err, fs.ErrInvalid))
	fmt.Println(validate("ok", 1) == nil)

	// Two %w verbs: the result unwraps to both operands.
	e2 := fmt.Errorf("save: %w; cleanup: %w", errEmpty, fs.ErrClosed)
	multi := e2.(interface{ Unwrap() []error })
	fmt.Println(len(multi.Unwrap()), errors.Is(e2, fs.ErrClosed))
}
