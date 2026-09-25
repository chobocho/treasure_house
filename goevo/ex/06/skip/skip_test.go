// 슬라이드 p6-v120-gotools — go test -skip, Go 1.20
package skip

import "testing"

func TestFast(t *testing.T) {}

func TestSlowNetwork(t *testing.T) {}

func TestTable(t *testing.T) {
	for _, name := range []string{"small", "huge"} {
		t.Run(name, func(t *testing.T) {})
	}
}
