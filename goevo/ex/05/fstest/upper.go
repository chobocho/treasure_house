// 슬라이드 p5-v116-fstest — fs.FS 를 구현하는 쪽, Go 1.16
package fstest

import (
	"bytes"
	"io/fs"
)

// Upper wraps an FS and upper-cases every file it reads.
type Upper struct{ FS fs.FS }

// Open is the only method fs.FS requires.
func (u Upper) Open(name string) (fs.File, error) {
	return u.FS.Open(name)
}

// ReadFile makes Upper an fs.ReadFileFS with different contents.
func (u Upper) ReadFile(name string) ([]byte, error) {
	b, err := fs.ReadFile(u.FS, name)
	return bytes.ToUpper(b), err
}
