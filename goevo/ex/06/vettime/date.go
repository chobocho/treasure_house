// 슬라이드 p6-v120-vet — yyyy-dd-mm 시각 형식, Go 1.20
package vettime

import "time"

// ISODate meant yyyy-mm-dd; 2006-02-01 is yyyy-dd-mm.
func ISODate(t time.Time) string { return t.Format("2006-02-01") }
