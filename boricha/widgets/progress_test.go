package widgets

import (
	"testing"

	"treasure/boricha/width"
)

func TestProgressBar(t *testing.T) {
	p := NewProgress(10)
	cases := []struct {
		pct  float64
		want string
	}{
		{0, "░░░░░░░░░░"},
		{0.5, "█████░░░░░"},
		{1, "██████████"},
		{0.04, "░░░░░░░░░░"}, // 반 칸은 그릴 수 없다 — 내림한다
		{0.99, "█████████░"},
		// 범위를 벗어난 값은 잘라 맞춘다. 나누기에서 나온 NaN·음수로 화면이 깨지지 않게.
		{-1, "░░░░░░░░░░"},
		{2, "██████████"},
	}
	for _, c := range cases {
		if got := p.View(c.pct); got != c.want {
			t.Errorf("View(%v) = %q, 원하는 값 %q", c.pct, got, c.want)
		}
	}
}

// 퍼센트를 함께 보이면 그만큼 막대가 짧아진다. 전체 폭은 그대로여야 한다.
func TestProgressWithPercent(t *testing.T) {
	p := NewProgress(15)
	p.ShowPercent = true
	cases := []struct {
		pct  float64
		want string
	}{
		{0, "░░░░░░░░░░   0%"},
		{0.5, "█████░░░░░  50%"},
		{1, "██████████ 100%"},
	}
	for _, c := range cases {
		got := p.View(c.pct)
		if got != c.want {
			t.Errorf("View(%v) = %q, 원하는 값 %q", c.pct, got, c.want)
		}
		if w := width.StringWidth(got); w != 15 {
			t.Errorf("View(%v) 가 %d칸, 원하는 값 15칸", c.pct, w)
		}
	}
}

// 폭이 아무리 작아도 죽지 않아야 한다.
func TestProgressTinyWidth(t *testing.T) {
	for w := 0; w <= 6; w++ {
		p := NewProgress(w)
		p.ShowPercent = true
		got := p.View(0.5)
		if got == "" && w > 5 {
			t.Errorf("폭 %d 에서 빈 문자열", w)
		}
		if width.StringWidth(got) > w && w > 0 {
			t.Errorf("폭 %d 인데 %d칸: %q", w, width.StringWidth(got), got)
		}
	}
}

// 채움·빈칸 글자를 바꿔 쓸 수 있다.
func TestProgressCustomRunes(t *testing.T) {
	p := NewProgress(6)
	p.Full, p.Empty = '=', '-'
	if got := p.View(0.5); got != "===---" {
		t.Errorf("= %q, 원하는 값 %q", got, "===---")
	}
}
