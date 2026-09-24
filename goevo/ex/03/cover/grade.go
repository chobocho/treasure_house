// 슬라이드 p3-v12-cover — go test -cover 로 잰 시험 범위, Go 1.2
package grade

// Grade maps a score to a letter.
func Grade(score int) string {
	switch {
	case score >= 90:
		return "A"
	case score >= 70:
		return "B"
	case score >= 50:
		return "C"
	}
	return "F"
}
