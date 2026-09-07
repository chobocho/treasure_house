// Package width 는 "이 글자가 터미널에서 몇 칸을 차지하는가" 를 답한다.
//
// 터미널은 글자를 고정폭 격자에 찍는다. 그런데 그 격자의 한 칸에 들어가는 글자가 있고
// 두 칸을 먹는 글자가 있다. 한글·한자·가나·이모지가 두 칸이다.
// 이 사실을 모르면 상자가 어긋나고 표가 밀린다 — 한국어 TUI 에서 가장 자주 보는 버그다.
//
// Go 표준 라이브러리에는 이 답이 없다. rune 은 코드포인트일 뿐 "칸" 을 모른다.
// 그래서 유니코드가 정해 둔 East_Asian_Width 속성 표를 직접 싣는다(width/table.go).
package width

import (
	"sort"
	"unicode/utf8"
)

// UnicodeVersion 은 실려 있는 폭 표가 어느 판에서 왔는지 돌려준다.
// 판이 올라가면 새 이모지의 폭이 달라진다 — 그래서 판을 밝힐 수 있어야 한다.
func UnicodeVersion() string { return unicodeVersion }

// RuneWidth 는 글자 하나가 차지하는 칸 수를 돌려준다. 0, 1, 2 중 하나다.
//
// 규칙(위에서부터 먼저 맞는 것을 쓴다):
//
//	제어 문자           → 0  (화면에 아무것도 안 찍힌다)
//	Z (결합·서식 문자)  → 0  (앞 글자에 얹힌다)
//	W, F (넓음·전각)    → 2
//	나머지              → 1  (A(모호) 포함 — 아래 설명)
//
// A(Ambiguous)를 1로 정한 이유. ①, é, ─ 같은 글자는 동아시아 글꼴에서는 두 칸,
// 서양 글꼴에서는 한 칸으로 그려진다. 유니코드는 "문맥에 따라 다르다" 고만 말하고
// 결정을 프로그램에 미룬다. 우리는 1을 고른다 — 박스 그리기 문자(─│┌)가 여기 속하는데,
// 그것들을 2로 보면 우리가 그리는 모든 상자가 두 배로 벌어지기 때문이다.
// Bubble Tea/Lip Gloss 가 쓰는 go-runewidth 도 서양 로케일에서는 1이다(LANG 이 ko·ja·zh 면 2).
//
// 이분 탐색이라 O(log n), n = 678. 표는 읽기만 하므로 여러 고루틴이 동시에 불러도 안전하다.
func RuneWidth(r rune) int {
	// 제어 문자. C0(0x00–0x1F), DEL(0x7F), C1(0x80–0x9F).
	if r < 0x20 || (r >= 0x7f && r < 0xa0) {
		return 0
	}
	switch class(r) {
	case 'Z':
		return 0
	case 'W', 'F':
		return 2
	}
	return 1
}

// class 는 표에서 r 이 속한 부류를 찾는다. 없으면 0.
func class(r rune) byte {
	// sort.Search 는 "조건이 처음 참이 되는 자리" 를 준다.
	// hi >= r 인 첫 구간을 찾은 뒤, 그 구간이 정말 r 을 담는지 한 번 더 본다.
	i := sort.Search(len(widthRanges), func(i int) bool { return widthRanges[i].hi >= r })
	if i < len(widthRanges) && widthRanges[i].lo <= r {
		return widthRanges[i].class
	}
	return 0
}

// StringWidth 는 문자열이 차지하는 칸 수를 돌려준다.
//
// 꾸밈 시퀀스(\e[31m 같은 것)는 세지 않는다. 화면에 아무 칸도 차지하지 않기 때문이다.
// 이 처리를 빼먹으면 색을 입힌 줄이 실제보다 훨씬 넓다고 계산되어, 정렬이 전부 무너진다.
func StringWidth(s string) int {
	w := 0
	for i := 0; i < len(s); {
		if n := ansiSeqLen(s[i:]); n > 0 {
			i += n
			continue
		}
		r, size := utf8.DecodeRuneInString(s[i:])
		w += RuneWidth(r)
		i += size
	}
	return w
}

// ansiSeqLen 은 s 가 이스케이프 시퀀스로 시작하면 그 바이트 길이를, 아니면 0 을 돌려준다.
//
// 여기서 알아보는 것은 두 가지다.
//   - CSI: ESC [ … 마지막 바이트(0x40–0x7E). 색·커서 명령이 전부 이 꼴이다.
//   - OSC: ESC ] … BEL 또는 ST(ESC \). 창 제목 바꾸기 같은 것.
//
// 그 밖의 ESC 는 두 바이트짜리로 본다. 완벽한 파서는 아니지만,
// 우리가 만들어 내는 시퀀스는 전부 위 두 가지다.
func ansiSeqLen(s string) int {
	if len(s) < 2 || s[0] != 0x1b {
		return 0
	}
	switch s[1] {
	case '[':
		for i := 2; i < len(s); i++ {
			if s[i] >= 0x40 && s[i] <= 0x7e {
				return i + 1
			}
		}
		return len(s) // 끝나지 않은 시퀀스 — 남은 전부를 시퀀스로 본다
	case ']':
		for i := 2; i < len(s); i++ {
			if s[i] == 0x07 {
				return i + 1
			}
			if s[i] == 0x1b && i+1 < len(s) && s[i+1] == '\\' {
				return i + 2
			}
		}
		return len(s)
	}
	return 2
}
