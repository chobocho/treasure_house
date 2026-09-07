package width

import "testing"

// 터미널은 글자를 "칸" 으로 센다. 한글은 두 칸, 영문은 한 칸.
// 이 표가 틀리면 상자도 표도 전부 어긋난다 — 이 패키지가 덱 전체를 떠받친다.
func TestRuneWidth(t *testing.T) {
	cases := []struct {
		r    rune
		want int
		why  string
	}{
		{'a', 1, "영문"},
		{'Z', 1, "영문"},
		{'1', 1, "숫자"},
		{' ', 1, "공백"},
		{'한', 2, "한글 음절"},
		{'글', 2, "한글 음절"},
		{'漢', 2, "한자"},
		{'あ', 2, "히라가나"},
		{'　', 2, "전각 공백 U+3000"},
		{'？', 2, "전각 물음표"},
		{'🍵', 2, "이모지"},
		{'─', 1, "박스 그리기 — 모호(A)는 1칸으로 본다"},
		{'①', 1, "동그라미 숫자도 모호(A)"},
		{'é', 1, "라틴 확장도 모호(A)"},
		{0x0301, 0, "결합 악센트는 앞 글자에 얹힌다"},
		{0x200b, 0, "너비 0 공백"},
		{0x1160, 0, "한글 자모 중성 — 앞 초성에 얹힌다"},
		{0x11A8, 0, "한글 자모 종성"},
		{'\t', 0, "제어 문자"},
		{'\n', 0, "제어 문자"},
		{0x1b, 0, "ESC"},
		{0, 0, "NUL"},
		{0x7f, 0, "DEL"},
	}
	for _, c := range cases {
		if got := RuneWidth(c.r); got != c.want {
			t.Errorf("RuneWidth(%q/U+%04X) = %d, 원하는 값 %d — %s", c.r, c.r, got, c.want, c.why)
		}
	}
}

func TestStringWidth(t *testing.T) {
	cases := []struct {
		s    string
		want int
	}{
		{"", 0},
		{"abc", 3},
		{"한글", 4},
		{"a한b", 4},
		{"보리차", 6},
		{"한a글b", 6},
		{"🍵🍵", 4},
		{"é", 1}, // e + 결합 악센트 = 한 칸
		// ANSI 시퀀스는 화면에 아무 칸도 차지하지 않는다.
		{"\x1b[31m한\x1b[0m", 2},
		{"\x1b[1;32mabc\x1b[0m", 3},
		{"\x1b[38;5;205m보리차\x1b[0m", 6},
		{"\x1b[0m", 0},
	}
	for _, c := range cases {
		if got := StringWidth(c.s); got != c.want {
			t.Errorf("StringWidth(%q) = %d, 원하는 값 %d", c.s, got, c.want)
		}
	}
}

func TestUnicodeVersion(t *testing.T) {
	if UnicodeVersion() == "" {
		t.Error("어느 판의 유니코드 표인지 말할 수 없으면 표를 믿을 근거가 없다")
	}
}

func TestTruncate(t *testing.T) {
	cases := []struct {
		s    string
		w    int
		want string
	}{
		{"abcdef", 3, "abc"},
		{"abc", 5, "abc"},
		{"abc", 0, ""},
		{"abc", -1, ""},
		{"", 5, ""},
		// 한글은 반 칸으로 자를 수 없다. 두 칸이 안 들어가면 통째로 뺀다.
		{"한글", 4, "한글"},
		{"한글", 3, "한"},
		{"한글", 2, "한"},
		{"한글", 1, ""},
		{"a한b", 2, "a"},
		{"a한b", 3, "a한"},
		{"a한b", 4, "a한b"},
		// 꾸밈 시퀀스는 칸을 안 먹으므로 자르지 않는다.
		// 특히 끝의 초기화(\e[0m)를 잃으면 색이 다음 줄로 새어 나간다.
		{"\x1b[31mabcdef\x1b[0m", 3, "\x1b[31mabc\x1b[0m"},
		{"\x1b[31m한글\x1b[0m", 2, "\x1b[31m한\x1b[0m"},
	}
	for _, c := range cases {
		if got := Truncate(c.s, c.w); got != c.want {
			t.Errorf("Truncate(%q, %d) = %q, 원하는 값 %q", c.s, c.w, got, c.want)
		}
	}
}

func TestPad(t *testing.T) {
	cases := []struct {
		s    string
		w    int
		want string
	}{
		{"abc", 5, "abc  "},
		{"abc", 3, "abc"},
		{"abc", 2, "abc"}, // 이미 넘으면 그대로 둔다 — 자르는 것은 Truncate 의 일
		{"한", 5, "한   "},
		{"한글", 4, "한글"},
		{"", 3, "   "},
		{"\x1b[31mab\x1b[0m", 4, "\x1b[31mab\x1b[0m  "},
	}
	for _, c := range cases {
		if got := Pad(c.s, c.w); got != c.want {
			t.Errorf("Pad(%q, %d) = %q, 원하는 값 %q", c.s, c.w, got, c.want)
		}
	}
}

func TestWrap(t *testing.T) {
	cases := []struct {
		s    string
		w    int
		want []string
	}{
		{"hello world", 5, []string{"hello", "world"}},
		{"hello world", 11, []string{"hello world"}},
		{"hello world", 20, []string{"hello world"}},
		{"", 5, []string{""}},
		{"a\nb", 5, []string{"a", "b"}},
		{"긴 줄 넘기기", 4, []string{"긴", "줄", "넘기", "기"}}, // "긴 줄" 은 사이 공백까지 5칸이라 못 들어간다
		// 한 낱말이 폭보다 길면 통째로 쪼갠다 — 안 그러면 줄이 폭을 넘어 터미널이 감싼다.
		{"aaaaa", 2, []string{"aa", "aa", "a"}},
		{"한글한글", 4, []string{"한글", "한글"}},
		{"보리차 좋다", 6, []string{"보리차", "좋다"}},
		{"abc", 0, []string{"abc"}}, // 폭이 말이 안 되면 그대로 돌려준다
	}
	for _, c := range cases {
		got := Wrap(c.s, c.w)
		if len(got) != len(c.want) {
			t.Errorf("Wrap(%q, %d) = %q, 원하는 값 %q", c.s, c.w, got, c.want)
			continue
		}
		for i := range got {
			if got[i] != c.want[i] {
				t.Errorf("Wrap(%q, %d) = %q, 원하는 값 %q", c.s, c.w, got, c.want)
				break
			}
		}
	}
}

// 감싼 결과는 어느 줄도 폭을 넘지 않아야 한다. 이것이 Wrap 의 존재 이유다.
// 폭 1은 뺀다 — 두 칸짜리 글자를 한 칸에 담는 방법은 없다(바로 아래 시험이 그 경우를 못박는다).
// 폭 1에 한글이 오는 경우. 담을 수도 없고 없앨 수도 없으니, 넘치는 쪽을 택했다.
// 글자를 조용히 버리면 읽는 사람이 글이 사라진 것을 눈치채지 못한다.
func TestWrapWidthOneWithWideRune(t *testing.T) {
	got := Wrap("한글", 1)
	if len(got) != 2 || got[0] != "한" || got[1] != "글" {
		t.Errorf("Wrap(\"한글\", 1) = %q, 원하는 값 [\"한\" \"글\"]", got)
	}
}

func TestWrapNeverExceedsWidth(t *testing.T) {
	texts := []string{
		"보리차는 Bubble Tea 가 아니다 — 하지만 같은 모양으로 만들 수 있다",
		"aaaa bbbb cccc dddd", "한글한글한글한글한글", "🍵🍵🍵🍵 tea",
	}
	for _, s := range texts {
		for w := 2; w <= 20; w++ {
			for _, line := range Wrap(s, w) {
				if got := StringWidth(line); got > w {
					t.Errorf("Wrap(%q, %d) 의 줄 %q 가 %d칸", s, w, line, got)
				}
			}
		}
	}
}
