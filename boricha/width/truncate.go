package width

import (
	"strings"
	"unicode/utf8"
)

// Truncate 는 문자열을 w칸 이하로 자른다.
//
// 두 칸짜리 글자를 반으로 자를 수는 없다. 한 칸만 남았는데 한글이 오면 그 글자는 통째로 뺀다.
// 꾸밈 시퀀스는 칸을 안 먹으므로 자르지 않고 전부 남긴다 — 특히 끝의 초기화(\e[0m)를
// 잃으면 색이 다음 줄로 새어 나가 화면 전체가 물든다.
func Truncate(s string, w int) string {
	if w < 0 {
		w = 0
	}
	var b strings.Builder
	b.Grow(len(s))
	cur, full := 0, false
	for i := 0; i < len(s); {
		if n := ansiSeqLen(s[i:]); n > 0 {
			b.WriteString(s[i : i+n])
			i += n
			continue
		}
		r, size := utf8.DecodeRuneInString(s[i:])
		if !full {
			if rw := RuneWidth(r); cur+rw <= w {
				b.WriteString(s[i : i+size])
				cur += rw
			} else {
				// 한 번 넘치면 그 뒤는 다 버린다. 들어가는 글자만 골라 담으면
				// 잘린 것이 아니라 글자가 빠진 다른 문장이 된다.
				full = true
			}
		}
		i += size
	}
	return b.String()
}

// splitAt 은 정확히 w칸에서 문자열을 둘로 나눈다. Wrap 이 긴 낱말을 쪼갤 때 쓴다.
// Truncate 와 달리 뒤쪽을 버리지 않고 돌려준다.
func splitAt(s string, w int) (head, tail string) {
	cur := 0
	for i := 0; i < len(s); {
		if n := ansiSeqLen(s[i:]); n > 0 {
			i += n
			continue
		}
		r, size := utf8.DecodeRuneInString(s[i:])
		rw := RuneWidth(r)
		if cur+rw > w {
			if i == 0 {
				// 첫 글자조차 안 들어간다(예: 폭 1에 한글). 그래도 한 글자는 떼어 낸다 —
				// 안 그러면 부르는 쪽이 영원히 제자리를 돈다.
				return s[:size], s[size:]
			}
			return s[:i], s[i:]
		}
		cur += rw
		i += size
	}
	return s, ""
}

// Pad 는 오른쪽에 공백을 채워 w칸으로 만든다. 이미 w칸 이상이면 그대로 둔다
// (자르는 것은 Truncate 의 일이다 — 한 함수가 늘리기도 하고 줄이기도 하면
// 부르는 쪽이 결과의 폭을 예측하지 못한다).
func Pad(s string, w int) string {
	d := w - StringWidth(s)
	if d <= 0 {
		return s
	}
	return s + strings.Repeat(" ", d)
}

// Wrap 은 글을 w칸 폭으로 접는다. 이미 들어 있는 줄바꿈은 그대로 지킨다.
//
// 낱말 단위로 접되, 낱말 하나가 폭보다 길면 통째로 쪼갠다. 안 쪼개면 그 줄이 폭을 넘고,
// 터미널이 제멋대로 다음 줄로 감아 버려 우리가 세어 둔 줄 수가 어긋난다.
// 그 어긋남이 렌더러의 줄 단위 diff 를 무너뜨린다 — 6부의 깜빡임 버그가 여기서 시작된다.
//
// 딱 하나 예외가 있다. 폭이 1인데 두 칸짜리 글자가 오면 담을 방법이 없다.
// 그럴 때는 그 글자가 홀로 한 줄을 차지하며 한 칸을 넘친다. 글자를 조용히 버리는 쪽보다
// 넘치는 쪽이 낫다 — 버리면 읽는 사람이 글이 사라진 것을 알아채지 못한다.
func Wrap(s string, w int) []string {
	if w < 1 {
		return []string{s}
	}
	var out []string
	for _, para := range strings.Split(s, "\n") {
		out = append(out, wrapLine(para, w)...)
	}
	return out
}

func wrapLine(s string, w int) []string {
	if s == "" {
		return []string{""}
	}
	var out []string
	cur, curw := "", 0
	flush := func() {
		out = append(out, cur)
		cur, curw = "", 0
	}
	for _, word := range strings.Split(s, " ") {
		ww := StringWidth(word)
		if ww > w {
			if cur != "" {
				flush()
			}
			for StringWidth(word) > w {
				var head string
				head, word = splitAt(word, w)
				out = append(out, head)
			}
			cur, curw = word, StringWidth(word)
			continue
		}
		switch {
		case cur == "":
			cur, curw = word, ww
		case curw+1+ww <= w: // +1 은 사이에 들어갈 공백
			cur += " " + word
			curw += 1 + ww
		default:
			flush()
			cur, curw = word, ww
		}
	}
	// 마지막 조각. 딱 하나 예외 — 긴 낱말을 쪼개다 정확히 떨어져 남은 것이 없을 때는
	// 빈 줄을 하나 더 붙이지 않는다.
	if cur != "" || len(out) == 0 {
		out = append(out, cur)
	}
	return out
}
