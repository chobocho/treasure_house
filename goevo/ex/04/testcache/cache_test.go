// 슬라이드 p4-v110-testcache — 테스트 결과 캐시, Go 1.10
package testcache

import (
	"strings"
	"testing"
)

func TestUpper(t *testing.T) {
	if got := strings.ToUpper("go"); got != "GO" {
		t.Fatalf("got %q", got)
	}
}
