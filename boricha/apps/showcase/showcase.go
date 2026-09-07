// Package showcase 는 세 번째 응용 프로그램 — 보리차가 할 수 있는 것을 한자리에 모은 전시장이다.
//
// 여기서 새로 배우는 것은 **화면 나누기** 다. 탭마다 다른 것을 보여 주는데,
// 탭은 그저 모델의 필드 하나다. 화면 전환을 위해 새 프로그램을 띄우거나
// 상태를 어딘가에 저장할 필요가 없다 — Update 가 필드 하나를 바꾸면 그것이 전환이다.
package showcase

import (
	"fmt"
	"strings"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/widgets"
	"treasure/boricha/width"
)

type tab int

const (
	tabStyle tab = iota
	tabColor
	tabWidth
	tabKeys
	tabCount
)

var tabNames = [...]string{"꾸미기", "색", "글자 폭", "입력"}

// Model 은 전시장의 상태다.
type Model struct {
	tab   tab
	w, h  int
	prof  style.Profile
	help  widgets.Help
	spin  widgets.Spinner
	keys  []string
	mouse string
}

func New() Model {
	sp := widgets.NewSpinner()
	sp.Set = widgets.SpinnerTea
	return Model{help: widgets.NewHelp(), spin: sp, w: 80, h: 24}
}

// SetSpinner 는 돌아가는 그림을 바꾼다.
//
// 시험과 기록을 위해 열어 둔 문이다. testkit 은 시계를 흉내 내지 않고 **진짜로**
// 기다리므로, 0.4초짜리 그림을 단 앱은 각본 한 걸음마다 0.4초를 먹는다.
// 시험이 느려지면 사람이 안 돌리게 되고, 안 돌리는 시험은 없는 것과 같다.
func (m Model) SetSpinner(s widgets.SpinnerSet) Model { m.spin.Set = s; return m }

func (m Model) Init() tea.Cmd { return m.spin.Tick() }

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
	case tea.ColorProfileMsg:
		m.prof = msg.Profile
		m.help = m.help.Profile(msg.Profile)
		m.spin.Style = style.New().Profile(msg.Profile).Foreground("205")
	case tea.MouseMsg:
		m.mouse = msg.String()
	case tea.PasteMsg:
		m.keys = pushKey(m.keys, fmt.Sprintf("붙여넣기 %d글자", len([]rune(string(msg)))))
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "tab", "right":
			m.tab = (m.tab + 1) % tabCount
			return m, nil
		case "shift+tab", "left":
			m.tab = (m.tab - 1 + tabCount) % tabCount
			return m, nil
		case "?":
			m.help.ShowAll = !m.help.ShowAll
			return m, nil
		}
		m.keys = pushKey(m.keys, msg.String())
	}
	var cmd tea.Cmd
	m.spin, cmd = m.spin.Update(msg)
	return m, cmd
}

func pushKey(k []string, s string) []string {
	next := append(append([]string{}, k...), s)
	if len(next) > 8 {
		next = next[len(next)-8:]
	}
	return next
}

func (m Model) bindings() []widgets.Binding {
	return []widgets.Binding{
		widgets.NewBinding("tab/→", "다음 탭", "tab", "right"),
		widgets.NewBinding("shift+tab/←", "이전 탭", "shift+tab", "left"),
		widgets.NewBinding("?", "도움말", "?"),
		widgets.NewBinding("q", "끝내기", "q"),
	}
}

func (m Model) View() string {
	base := m.styleBase()
	head := base.Bold(true).Render(m.spin.View() + " 보리차 전시장")

	// 탭 줄. 고른 탭만 뒤집어 그린다.
	var tabs []string
	for i, n := range tabNames {
		s := base.Padding(0, 1)
		if tab(i) == m.tab {
			s = s.Reverse(true).Bold(true)
		}
		tabs = append(tabs, s.Render(fmt.Sprintf("%d %s", i+1, n)))
	}

	var body string
	switch m.tab {
	case tabStyle:
		body = m.styleTab(base)
	case tabColor:
		body = m.colorTab(base)
	case tabWidth:
		body = m.widthTab(base)
	default:
		body = m.keysTab(base)
	}

	return style.JoinVertical(style.Left,
		head,
		style.JoinHorizontal(style.Top, tabs...),
		"",
		body,
		"",
		m.help.View(m.bindings()),
	)
}

// styleBase 는 이 모델이 쓰는 밑바탕 스타일이다. 시험이 View 를 통째로 만들지 않고
// 탭 하나만 그려 볼 수 있게 열어 둔다.
func (m Model) styleBase() style.Style { return style.New().Profile(m.prof) }

func (m Model) styleTab(base style.Style) string {
	rows := []string{
		style.JoinHorizontal(style.Top,
			base.Width(14).Render("테두리 넷"),
			base.Border(style.NormalBorder).Padding(0, 1).Render("보통"),
			base.Border(style.RoundedBorder).Padding(0, 1).Render("둥근"),
			base.Border(style.ThickBorder).Padding(0, 1).Render("굵은"),
			base.Border(style.DoubleBorder).Padding(0, 1).Render("두 줄"),
		),
		"",
		style.JoinHorizontal(style.Top,
			base.Width(14).Render("정렬"),
			base.Width(16).Border(style.NormalBorder).Align(style.Left).Render("왼쪽"),
			base.Width(16).Border(style.NormalBorder).Align(style.Center).Render("가운데"),
			base.Width(16).Border(style.NormalBorder).Align(style.Right).Render("오른쪽"),
		),
		"",
		style.JoinHorizontal(style.Top,
			base.Width(14).Render("글꼴 효과"),
			base.Bold(true).Render("굵게")+"  "+
				base.Faint(true).Render("흐리게")+"  "+
				base.Underline(true).Render("밑줄")+"  "+
				base.Reverse(true).Render("반전")+"  "+
				base.Italic(true).Render("기울임"),
		),
	}
	return strings.Join(rows, "\n")
}

func (m Model) colorTab(base style.Style) string {
	var lines []string
	lines = append(lines, base.Faint(true).Render(
		fmt.Sprintf("이 터미널의 색 수준: %s — 낼 수 없는 색은 가장 가까운 색으로 내려 맞춘다", m.prof)))
	lines = append(lines, "")

	// 16색
	var row []string
	for i := 0; i < 16; i++ {
		row = append(row, base.Background(style.Color(fmt.Sprint(i))).Render("  "))
	}
	lines = append(lines, base.Width(12).Render("16색")+strings.Join(row, ""))

	// 256색 정육면체를 여섯 줄로
	for r := 0; r < 6; r++ {
		row = row[:0]
		for g := 0; g < 6; g++ {
			for b := 0; b < 6; b++ {
				n := 16 + 36*r + 6*g + b
				row = append(row, base.Background(style.Color(fmt.Sprint(n))).Render(" "))
			}
		}
		label := ""
		if r == 0 {
			label = "256색"
		}
		lines = append(lines, base.Width(12).Render(label)+strings.Join(row, ""))
	}

	// 24비트 그러데이션
	row = row[:0]
	for i := 0; i < 36; i++ {
		v := i * 255 / 35
		row = append(row, base.Background(style.Color(fmt.Sprintf("#%02x%02x%02x", v, 60, 255-v))).Render(" "))
	}
	lines = append(lines, base.Width(12).Render("24비트")+strings.Join(row, ""))
	return strings.Join(lines, "\n")
}

func (m Model) widthTab(base style.Style) string {
	// "é±─" 는 셋 다 East_Asian_Width 가 모호(A)다 — 우리는 1칸으로 센다.
	// 동그라미 숫자(U+2460 부터)도 모호지만 여기 넣지 않았다. D2Coding 은 그것을
	// 두 칸짜리로 그려서, 표와 글꼴이 어긋나는 실물 사례가 되기 때문이다.
	// 그 이야기는 덱의 글자 폭 편에서 따로 다룬다.
	samples := []string{"보리차", "green tea", "한a글b", "🍵🫖", "é±─", "　전각"}
	var lines []string
	lines = append(lines, base.Faint(true).Render(
		fmt.Sprintf("유니코드 %s 의 East_Asian_Width 표에서 잰다", width.UnicodeVersion())))
	lines = append(lines, "")
	lines = append(lines, base.Bold(true).Render(
		width.Pad("글", 12)+width.Pad("바이트", 8)+width.Pad("룬", 6)+width.Pad("칸", 6)+"자로 재 보기"))
	for _, s := range samples {
		w := width.StringWidth(s)
		// 눈금은 "│" 에서 시작해 w칸을 긋고 "┤" 로 닫는다.
		// 앞의 네 칸(글·바이트·룬·칸)이 모두 32칸으로 맞춰져 있으므로,
		// 모든 줄의 "│" 가 같은 자리에 서면 폭 계산이 맞은 것이다.
		ruler := "│" + strings.Repeat("─", w) + "┤"
		lines = append(lines, width.Pad(s, 12)+
			width.Pad(fmt.Sprint(len(s)), 8)+
			width.Pad(fmt.Sprint(len([]rune(s))), 6)+
			width.Pad(fmt.Sprint(w), 6)+ruler)
	}
	lines = append(lines, "")
	lines = append(lines, base.Faint(true).Render("눈금이 모두 같은 자리에서 시작하고, 그 길이가 곧 칸 수다"))
	return strings.Join(lines, "\n")
}

func (m Model) keysTab(base style.Style) string {
	var lines []string
	lines = append(lines, base.Faint(true).Render("아무 키나 눌러 보세요. 마우스도 움직여 보세요."))
	lines = append(lines, "")
	for _, k := range m.keys {
		lines = append(lines, "  "+k)
	}
	for i := len(m.keys); i < 8; i++ {
		lines = append(lines, "")
	}
	lines = append(lines, "")
	lines = append(lines, "마우스: "+m.mouse)
	return strings.Join(lines, "\n")
}
