// 슬라이드 p5-v116-fstest — testing/fstest.TestFS 가 잡는 실수, Go 1.16
package fstest

import (
	"testing"
	"testing/fstest"
)

func TestUpper(t *testing.T) {
	mem := fstest.MapFS{"a.txt": {Data: []byte("hi")}}
	if err := fstest.TestFS(Upper{mem}, "a.txt"); err != nil {
		t.Fatal(err)
	}
}
