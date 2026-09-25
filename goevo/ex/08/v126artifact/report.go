// 슬라이드 p8-v126-artifact — 시험이 남길 산출물을 만드는 코드, Go 1.26
package report

import "fmt"

// Render returns a small text report.
func Render(n int) string {
	return fmt.Sprintf("items: %d\nstatus: ok\n", n)
}
