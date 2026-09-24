// 슬라이드 p4-v17-subtests — 하위 테스트와 하위 벤치마크, Go 1.7
package subtests

import (
	"fmt"
	"reflect"
	"strings"
	"testing"
)

func TestSplit(t *testing.T) {
	cases := []struct {
		name, in, sep string
		want          []string
	}{
		{"simple", "a,b,c", ",", []string{"a", "b", "c"}},
		{"trailing", "a,b,", ",", []string{"a", "b", ""}},
		{"nosep", "abc", "/", []string{"abc"}},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := strings.Split(c.in, c.sep)
			if !reflect.DeepEqual(got, c.want) {
				t.Fatalf("got %q, want %q", got, c.want)
			}
		})
	}
}

func BenchmarkJoin(b *testing.B) {
	for _, n := range []int{10, 1000} {
		parts := make([]string, n)
		b.Run(fmt.Sprintf("n=%d", n), func(b *testing.B) {
			for i := 0; i < b.N; i++ {
				strings.Join(parts, ",")
			}
		})
	}
}
