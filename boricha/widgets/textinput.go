package widgets

import (
	"strings"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/width"
)

// TextInput 은 한 줄짜리 입력창이다.
//
// 한글을 다루는 데 필요한 두 가지가 여기 다 들어 있다.
//
//	① 값은 []rune 으로 들고 다닌다. 바이트로 세면 백스페이스 한 번에 글자가 깨진다
//	   ("보리차" 는 9바이트, 3룬이다).
//	② 화면에서의 자리는 **칸** 으로 센다. 룬 하나가 두 칸일 수 있기 때문이다.
//
// 이 둘을 섞으면(룬 개수로 화면 자리를 계산하거나 그 반대로) 한글이 든 순간
// 커서가 글자 위가 아니라 엉뚱한 곳에서 깜빡인다.
type TextInput struct {
	Prompt      string // 입력창 앞에 붙는 것. 보통 "> "
	Placeholder string // 비었을 때 보여 줄 안내 글
	CharLimit   int    // 룬 개수 제한. 0 이면 제한 없음
	Width       int    // 보이는 칸 수(프롬프트 제외). 0 이면 제한 없음

	PromptStyle      style.Style
	TextStyle        style.Style
	PlaceholderStyle style.Style
	CursorStyle      style.Style

	value   []rune
	pos     int // 커서 앞에 있는 룬의 개수
	focused bool
}

func NewTextInput() TextInput {
	return TextInput{
		Prompt:           "> ",
		Width:            20,
		PlaceholderStyle: style.New().Faint(true),
		CursorStyle:      style.New().Reverse(true),
	}
}

func (t TextInput) Value() string    { return string(t.value) }
func (t TextInput) Position() int    { return t.pos }
func (t TextInput) Focused() bool    { return t.focused }
func (t TextInput) Focus() TextInput { t.focused = true; return t }
func (t TextInput) Blur() TextInput  { t.focused = false; return t }

// SetValue 는 값을 통째로 바꾸고 커서를 끝으로 보낸다.
func (t TextInput) SetValue(s string) TextInput {
	t.value = []rune(s)
	if t.CharLimit > 0 && len(t.value) > t.CharLimit {
		t.value = t.value[:t.CharLimit]
	}
	t.pos = len(t.value)
	return t
}

func (t TextInput) Reset() TextInput {
	t.value, t.pos = nil, 0
	return t
}

// Update 는 키를 받아 글을 고친다.
//
// 초점이 없으면 아무것도 안 받는다. 화면에 입력창이 둘 이상일 때, 어느 쪽이 키를
// 가져갈지 정하는 규칙이 이 한 줄이다.
func (t TextInput) Update(msg tea.Msg) (TextInput, tea.Cmd) {
	if !t.focused {
		return t, nil
	}
	switch msg := msg.(type) {
	case tea.PasteMsg:
		return t.insert([]rune(string(msg))), nil
	case tea.KeyMsg:
		switch msg.String() {
		case "left", "ctrl+b":
			if t.pos > 0 {
				t.pos--
			}
		case "right", "ctrl+f":
			if t.pos < len(t.value) {
				t.pos++
			}
		case "home", "ctrl+a":
			t.pos = 0
		case "end", "ctrl+e":
			t.pos = len(t.value)
		case "backspace":
			if t.pos > 0 {
				t.value = cut(t.value, t.pos-1, t.pos)
				t.pos--
			}
		case "delete", "ctrl+d":
			if t.pos < len(t.value) {
				t.value = cut(t.value, t.pos, t.pos+1)
			}
		case "ctrl+u":
			// 커서 앞을 전부 지운다. 셸에서 온 관습이다.
			t.value = cut(t.value, 0, t.pos)
			t.pos = 0
		case "ctrl+k":
			t.value = cut(t.value, t.pos, len(t.value))
		case "ctrl+w":
			from := wordStart(t.value, t.pos)
			t.value = cut(t.value, from, t.pos)
			t.pos = from
		default:
			// Text 가 비어 있지 않다는 것이 곧 "글자로 넣어도 되는 키" 라는 뜻이다.
			// 이 판단을 Mod 로 하려 들면 alt+a 와 a 를 가르는 코드가 여기저기 흩어진다.
			if msg.Text != "" {
				return t.insert([]rune(msg.Text)), nil
			}
		}
	}
	return t, nil
}

// insert 는 커서 자리에 룬들을 끼워 넣는다.
func (t TextInput) insert(r []rune) TextInput {
	if t.CharLimit > 0 {
		room := t.CharLimit - len(t.value)
		if room <= 0 {
			return t
		}
		if len(r) > room {
			r = r[:room]
		}
	}
	// 새 슬라이스를 만든다. 원본 배열에 append 하면 이 모델의 복사본들이
	// 같은 배열을 나눠 갖게 되어, 값 의미론이 조용히 깨진다.
	next := make([]rune, 0, len(t.value)+len(r))
	next = append(next, t.value[:t.pos]...)
	next = append(next, r...)
	next = append(next, t.value[t.pos:]...)
	t.value = next
	t.pos += len(r)
	return t
}

func cut(v []rune, from, to int) []rune {
	next := make([]rune, 0, len(v)-(to-from))
	next = append(next, v[:from]...)
	return append(next, v[to:]...)
}

// wordStart 는 커서 앞 낱말의 시작 자리를 찾는다.
// 먼저 공백을 건너뛰고, 그다음 공백이 아닌 것을 건너뛴다 — 셸의 ctrl+w 와 같은 규칙이다.
func wordStart(v []rune, pos int) int {
	i := pos
	for i > 0 && v[i-1] == ' ' {
		i--
	}
	for i > 0 && v[i-1] != ' ' {
		i--
	}
	return i
}

// View 는 입력창을 그린다. 결과의 폭은 언제나 프롬프트 + Width 다.
//
// 폭이 흔들리면 옆에 놓인 것이 전부 밀린다. 그래서 모자라면 공백으로 채우고,
// 넘치면 옆으로 밀어(가로 스크롤) 커서가 보이는 구간만 그린다.
func (t TextInput) View() string {
	prompt := t.PromptStyle.Render(t.Prompt)

	if len(t.value) == 0 && t.Placeholder != "" {
		s := t.Placeholder
		if t.Width > 0 {
			s = width.Pad(width.Truncate(s, t.Width), t.Width)
		}
		return prompt + t.PlaceholderStyle.Render(s)
	}

	start := t.window()
	var b strings.Builder
	b.WriteString(prompt)
	w := 0
	for i := start; i < len(t.value); i++ {
		rw := width.RuneWidth(t.value[i])
		if t.Width > 0 && w+rw > t.Width {
			break
		}
		s := string(t.value[i])
		if i == t.pos && t.focused {
			b.WriteString(t.CursorStyle.Render(s))
		} else {
			b.WriteString(t.TextStyle.Render(s))
		}
		w += rw
	}
	// 커서가 글 끝에 있으면 그 자리에 빈 칸 하나를 커서로 그린다.
	if t.pos >= len(t.value) && t.focused && (t.Width == 0 || w < t.Width) {
		b.WriteString(t.CursorStyle.Render(" "))
		w++
	}
	if t.Width > w {
		b.WriteString(strings.Repeat(" ", t.Width-w))
	}
	return b.String()
}

// window 는 화면에 보일 구간의 시작 룬 번호를 고른다.
//
// 규칙 하나: **커서는 언제나 보인다.** 그 조건을 지키면서 왼쪽 글을 최대한 많이 보인다.
// 커서 앞의 글이 Width-1 칸 안에 들어올 때까지 시작점을 오른쪽으로 민다
// (한 칸은 커서 자신의 몫이다).
//
// 상태로 들고 다니지 않고 매번 다시 계산한다. 값(value, pos, Width)만으로 정해지므로
// 결과가 늘 같고, 스크롤 위치가 어긋나 커서가 사라지는 종류의 버그가 아예 없다.
func (t TextInput) window() int {
	if t.Width <= 0 {
		return 0
	}
	start := 0
	for start < t.pos && width.StringWidth(string(t.value[start:t.pos])) > t.Width-1 {
		start++
	}
	return start
}
