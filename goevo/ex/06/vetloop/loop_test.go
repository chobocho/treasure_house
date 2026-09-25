// 슬라이드 p6-v120-vet — t.Parallel 뒤 루프 변수 포착, Go 1.20
package vetloop

import "testing"

func TestAll(t *testing.T) {
	for _, tc := range []string{"a", "b", "c"} {
		t.Run(tc, func(t *testing.T) {
			t.Parallel()
			if tc == "" { // before Go 1.22: every subtest may see "c"
				t.Fatal("empty")
			}
		})
	}
}
