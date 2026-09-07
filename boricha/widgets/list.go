package widgets

import (
	"strconv"
	"strings"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/width"
)

// Item 은 목록에 들어갈 수 있는 것이다.
//
// 인터페이스로 둔 이유. 목록이 다루는 것은 "제목이 있고, 설명이 있고, 걸러질 수 있는 것"
// 이지 특정 구조체가 아니다. 앱은 자기 타입에 이 세 메서드만 붙이면 그대로 넣을 수 있다.
//
// FilterValue 를 Title 과 따로 둔 이유는, 화면에 보이는 글과 검색되는 글이 다를 수 있어서다.
// 예: 화면에는 "☐ 우유 사기" 라고 보이지만 걸러질 때는 "우유 사기" 만 보게 하는 것.
type Item interface {
	Title() string
	Description() string
	FilterValue() string
}

// StringItem 은 가장 단순한 항목 — 문자열 하나가 곧 제목이자 검색어다.
type StringItem string

func (s StringItem) Title() string       { return string(s) }
func (s StringItem) Description() string { return "" }
func (s StringItem) FilterValue() string { return string(s) }

// List 는 고를 수 있는 목록이다. 화면보다 항목이 많으면 굴러가고, / 로 거를 수 있다.
type List struct {
	Title           string
	Width, Height   int
	ShowStatus      bool // 맨 아래 "3/8" 줄
	ShowDescription bool // 항목마다 설명을 한 줄 더
	Cursor          string

	TitleStyle    style.Style
	ItemStyle     style.Style
	SelectedStyle style.Style
	DescStyle     style.Style
	StatusStyle   style.Style
	FilterInput   TextInput

	items     []Item
	cursor    int // 걸러진 목록에서의 자리
	offset    int // 맨 위에 보이는 항목의 자리
	filtering bool
	filter    string
}

func NewList(items []Item, w, h int) List {
	fi := NewTextInput()
	fi.Prompt = "거르기: "
	fi.Width = w - width.StringWidth(fi.Prompt)
	return List{
		Width: w, Height: h, ShowStatus: true, Cursor: "▸ ",
		items:         items,
		FilterInput:   fi,
		SelectedStyle: style.New().Bold(true),
		DescStyle:     style.New().Faint(true),
		StatusStyle:   style.New().Faint(true),
		TitleStyle:    style.New().Bold(true),
	}
}

func (l List) Items() []Item       { return l.items }
func (l List) Index() int          { return l.cursor }
func (l List) Filtering() bool     { return l.filtering }
func (l List) FilterValue() string { return l.filter }

// SetItems 는 항목을 갈아 끼운다. 커서가 범위를 벗어나면 끌어당긴다 —
// 목록이 줄어드는 일(할 일을 지운다든가)은 늘 있고, 그때 커서가 허공을 가리키면 안 된다.
func (l List) SetItems(items []Item) List {
	l.items = items
	return l.clamp()
}

// VisibleItems 는 거르기를 통과한 항목들이다.
//
// 걸러진 목록을 따로 저장하지 않고 매번 만든다. 저장해 두면 items 나 filter 중
// 하나만 바뀌었을 때 갱신을 잊는 자리가 생긴다. 목록이 수천 개가 되면 그때 가서
// 캐시를 붙이면 된다 — 지금은 정확한 쪽이 낫다.
func (l List) VisibleItems() []Item {
	if l.filter == "" {
		return l.items
	}
	needle := strings.ToLower(l.filter)
	out := make([]Item, 0, len(l.items))
	for _, it := range l.items {
		if strings.Contains(strings.ToLower(it.FilterValue()), needle) {
			out = append(out, it)
		}
	}
	return out
}

// SelectedItem 은 지금 고른 항목. 없으면 nil 이다.
func (l List) SelectedItem() Item {
	vis := l.VisibleItems()
	if l.cursor < 0 || l.cursor >= len(vis) {
		return nil
	}
	return vis[l.cursor]
}

func (l List) Select(i int) List {
	l.cursor = i
	return l.clamp()
}

func (l List) clamp() List {
	n := len(l.VisibleItems())
	if l.cursor >= n {
		l.cursor = n - 1
	}
	if l.cursor < 0 {
		l.cursor = 0
	}
	// 커서가 보이도록 창을 민다.
	per := l.perPage()
	if per > 0 {
		if l.cursor < l.offset {
			l.offset = l.cursor
		}
		if l.cursor >= l.offset+per {
			l.offset = l.cursor - per + 1
		}
		if max := n - per; l.offset > max {
			l.offset = max
		}
	}
	if l.offset < 0 {
		l.offset = 0
	}
	return l
}

// perPage 는 한 화면에 들어가는 항목 수다.
// 제목·거르기 줄·상태줄이 차지하는 만큼을 빼고 남은 것을 항목 높이로 나눈다.
func (l List) perPage() int {
	body := l.Height - l.chromeLines()
	if body < 0 {
		body = 0
	}
	return body / l.itemLines()
}

func (l List) chromeLines() int {
	n := 0
	if l.Title != "" {
		n++
	}
	if l.filtering {
		n++
	}
	if l.ShowStatus {
		n++
	}
	return n
}

func (l List) itemLines() int {
	if l.ShowDescription {
		return 2
	}
	return 1
}

func (l List) KeyBindings() []Binding {
	return []Binding{
		NewBinding("↑/k", "위로", "up", "k"),
		NewBinding("↓/j", "아래로", "down", "j"),
		NewBinding("/", "거르기", "/"),
		NewBinding("enter", "고르기", "enter"),
	}
}

// Update 는 두 가지 모드로 갈린다.
//
// 거르는 중에는 키가 **전부 입력창으로** 간다. 그러지 않으면 "java" 를 칠 때
// j 가 이동으로 먹혀 목록만 움직이고 글자는 안 들어간다. 실제로 겪기 전에는
// 놓치기 쉬운 자리다.
func (l List) Update(msg tea.Msg) (List, tea.Cmd) {
	if l.filtering {
		return l.updateFiltering(msg)
	}
	km, ok := msg.(tea.KeyMsg)
	if !ok {
		return l, nil
	}
	switch km.String() {
	case "up", "k":
		l.cursor--
	case "down", "j":
		l.cursor++
	case "home", "g":
		l.cursor = 0
	case "end", "G":
		l.cursor = len(l.VisibleItems()) - 1
	case "pgup":
		l.cursor -= l.perPage()
	case "pgdown":
		l.cursor += l.perPage()
	case "/":
		l.filtering = true
		l.FilterInput = l.FilterInput.SetValue(l.filter).Focus()
		return l, nil
	case "esc":
		// 거르기를 푼다. 걸러 놓은 것을 잊고 다른 항목을 찾을 때 쓴다.
		l.filter = ""
		return l.clamp(), nil
	}
	return l.clamp(), nil
}

func (l List) updateFiltering(msg tea.Msg) (List, tea.Cmd) {
	if km, ok := msg.(tea.KeyMsg); ok {
		switch km.String() {
		case "enter":
			// 거른 결과는 남기고 입력만 끝낸다.
			l.filtering = false
			l.FilterInput = l.FilterInput.Blur()
			return l.clamp(), nil
		case "esc":
			// 없던 일로 되돌린다.
			l.filtering = false
			l.filter = ""
			l.FilterInput = l.FilterInput.Reset().Blur()
			return l.clamp(), nil
		}
	}
	var cmd tea.Cmd
	l.FilterInput, cmd = l.FilterInput.Update(msg)
	l.filter = l.FilterInput.Value()
	// 거르는 말이 바뀔 때마다 커서를 맨 위로 되돌린다.
	// 남겨 두면 방금 걸러 낸 목록의 엉뚱한 자리를 가리킨다.
	l.cursor = 0
	l.offset = 0
	return l.clamp(), cmd
}

// View 는 언제나 정확히 Height 줄, Width 칸을 돌려준다.
func (l List) View() string {
	out := make([]string, 0, l.Height)
	pad := func(s string) string { return width.Pad(width.Truncate(s, l.Width), l.Width) }

	if l.Title != "" {
		out = append(out, l.TitleStyle.Render(pad(l.Title)))
	}
	if l.filtering {
		out = append(out, pad(l.FilterInput.View()))
	}

	vis := l.VisibleItems()
	per := l.perPage()
	for i := 0; i < per; i++ {
		n := l.offset + i
		if n >= len(vis) {
			out = append(out, pad(""))
			if l.ShowDescription {
				out = append(out, pad(""))
			}
			continue
		}
		mark := strings.Repeat(" ", width.StringWidth(l.Cursor))
		st := l.ItemStyle
		if n == l.cursor {
			mark = l.Cursor
			st = l.SelectedStyle
		}
		out = append(out, st.Render(pad(mark+vis[n].Title())))
		if l.ShowDescription {
			out = append(out, l.DescStyle.Render(pad(mark+vis[n].Description())))
		}
	}

	if l.ShowStatus {
		s := "0/0"
		if len(vis) > 0 {
			s = strconv.Itoa(l.cursor+1) + "/" + strconv.Itoa(len(vis))
		}
		if l.filter != "" {
			s += "  (거르는 중: " + l.filter + ")"
		}
		out = append(out, l.StatusStyle.Render(pad(s)))
	}

	// 나누어떨어지지 않아 남은 줄을 채운다. 모양이 흔들리면 옆이 전부 밀린다.
	for len(out) < l.Height {
		out = append(out, pad(""))
	}
	return strings.Join(out[:l.Height], "\n")
}
