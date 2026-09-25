// 슬라이드 p8-v126-astype — errors.AsType: 제네릭 As, Go 1.26
package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
)

type RetryError struct{ After int }

func (e *RetryError) Error() string {
	return fmt.Sprint("retry after ", e.After)
}

func fetch(i int) error {
	switch i {
	case 0:
		return fmt.Errorf("fetch: %w", &RetryError{After: 3})
	case 1:
		_, err := os.Open("/no/such/file")
		return fmt.Errorf("fetch: %w", err)
	}
	return nil
}

func main() {
	for i := range 3 {
		err := fetch(i)

		var re *RetryError
		if errors.As(err, &re) {
			fmt.Println("As:    ", re.After)
		}

		if re, ok := errors.AsType[*RetryError](err); ok {
			fmt.Println("AsType:", re.After)
		} else if pe, ok := errors.AsType[*fs.PathError](err); ok {
			fmt.Println("AsType: path error on", pe.Path)
		} else {
			fmt.Println("AsType: no match for", err)
		}
	}
}
