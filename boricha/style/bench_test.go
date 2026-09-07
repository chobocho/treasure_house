package style

import "testing"

// 스타일은 값이라 프레임마다 복사된다. 그 비용을 재 둔다.
//
//	go test -bench . -benchmem ./style/

func BenchmarkRenderPlain(b *testing.B) {
	s := New()
	for i := 0; i < b.N; i++ {
		_ = s.Render("보리차 한 잔")
	}
}

func BenchmarkRenderStyled(b *testing.B) {
	s := New().Profile(ANSI256).Bold(true).Foreground("205").Background("236").
		Padding(1, 2).Border(RoundedBorder).Width(40).Align(Center)
	for i := 0; i < b.N; i++ {
		_ = s.Render("보리차 한 잔")
	}
}

// 스타일 하나를 여덟 번 고치는 값 복사 비용.
func BenchmarkStyleCopy(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = New().Bold(true).Italic(true).Underline(true).
			Foreground("205").Background("236").Padding(1).Margin(1).Width(20)
	}
}

func BenchmarkJoinHorizontal(b *testing.B) {
	left := New().Width(20).Height(10).Border(NormalBorder).Render("보리차")
	right := New().Width(30).Height(6).Border(RoundedBorder).Render("green tea")
	for i := 0; i < b.N; i++ {
		_ = JoinHorizontal(Top, left, right)
	}
}
