// 슬라이드 p8-v127-stdver — go test 가 stdversion 을 기본으로, Go 1.27
package last

import "testing"

func TestExt(t *testing.T) {
	if got := Ext("deck.tar.gz"); got != "gz" {
		t.Fatalf("Ext = %q", got)
	}
}
