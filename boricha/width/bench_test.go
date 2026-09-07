package width

import "testing"

// 이 패키지의 함수들은 한 프레임에 수백 번 불린다.
// "충분히 빠른가" 를 말하려면 숫자가 있어야 한다 — 느낌이 아니라.
//
//	go test -bench . -benchmem ./width/

var benchLine = "│ 보리차 — 볶은 보리                    │ green tea · steamed leaf │"

func BenchmarkRuneWidthASCII(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = RuneWidth('a')
	}
}

func BenchmarkRuneWidthHangul(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = RuneWidth('한')
	}
}

func BenchmarkStringWidth(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = StringWidth(benchLine)
	}
}

func BenchmarkStringWidthStyled(b *testing.B) {
	s := "\x1b[1;38;5;205m" + benchLine + "\x1b[0m"
	for i := 0; i < b.N; i++ {
		_ = StringWidth(s)
	}
}

func BenchmarkTruncate(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = Truncate(benchLine, 40)
	}
}
