// 슬라이드 p5-v117-shuffle — 순서에 몰래 기대는 코드, Go 1.17
package shuffle

var log []string

// Record appends a step to the shared log.
func Record(step string) int {
	log = append(log, step)
	return len(log)
}
