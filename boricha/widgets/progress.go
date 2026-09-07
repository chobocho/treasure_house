package widgets

import (
	"strconv"
	"strings"

	"treasure/boricha/style"
	"treasure/boricha/width"
)

// Progress 는 진행 막대다.
//
// 상태를 안 들고 있다는 점이 다른 부품과 다르다. 진행률은 앱이 알고 있는 것이므로
// 그때그때 넘겨받아 그리기만 한다. Update 도 필요 없다.
// 부품이라고 해서 반드시 모델일 필요는 없다는 예이기도 하다.
//
// (Bubbles 의 progress 는 값이 부드럽게 따라오는 애니메이션까지 한다.
// 그건 용수철 물리를 흉내 내는 별도 라이브러리가 필요해서 여기서는 뺐다.)
type Progress struct {
	Width       int
	Full, Empty rune
	ShowPercent bool

	FullStyle    style.Style
	EmptyStyle   style.Style
	PercentStyle style.Style
}

func NewProgress(w int) Progress {
	return Progress{Width: w, Full: '█', Empty: '░'}
}

// 퍼센트 표시가 차지하는 칸 수. " 100%" 처럼 앞에 공백 하나를 두고 네 칸에 오른쪽 맞춤이다.
// 늘 같은 폭이라 값이 바뀌어도 막대 길이가 흔들리지 않는다.
const percentWidth = 5

// View 는 진행률(0~1)을 막대로 그린다.
//
// 범위를 벗어난 값은 잘라 맞춘다. 진행률은 대개 나눗셈으로 나오는데,
// 분모가 0이면 무한대나 NaN 이 나온다. 그걸 그대로 곱하면 막대 길이가 음수가 되어
// strings.Repeat 이 그 자리에서 죽는다.
func (p Progress) View(pct float64) string {
	if !(pct >= 0) { // NaN 도 여기서 걸린다 (NaN >= 0 은 거짓)
		pct = 0
	}
	if pct > 1 {
		pct = 1
	}

	barW := p.Width
	if p.ShowPercent {
		barW -= percentWidth
	}
	if barW < 0 {
		barW = 0
	}

	// 내림한다. 반 칸을 그릴 수 없으므로, 99%에서 "다 찼다" 고 보이는 것보다
	// 한 칸 모자라 보이는 편이 정직하다.
	full := int(pct * float64(barW))
	if full > barW {
		full = barW
	}
	bar := p.FullStyle.Render(strings.Repeat(string(p.Full), full)) +
		p.EmptyStyle.Render(strings.Repeat(string(p.Empty), barW-full))

	if !p.ShowPercent {
		return bar
	}
	n := strconv.Itoa(int(pct * 100))
	out := bar + " " + p.PercentStyle.Render(width.Pad(strings.Repeat(" ", 4-len(n)-1)+n+"%", 4))
	// 폭이 퍼센트 표시보다도 좁으면 막대가 0칸이어도 넘친다.
	// 약속한 폭을 넘기느니 잘라 낸다 — 넘치면 그 줄이 터미널에서 감겨 화면이 밀린다.
	return width.Truncate(out, p.Width)
}
