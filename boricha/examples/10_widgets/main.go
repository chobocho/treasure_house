// 10_widgets — 부품 여섯 개를 한 화면에.
//
// 부품은 앱과 똑같은 모양(값 모델·Update·View)이므로, 부모가 하는 일은
// "사건을 지금 초점이 있는 부품에게 넘기고, 돌려받은 값을 자기 필드에 다시 넣는" 것뿐이다.
//
//	m.input, cmd = m.input.Update(msg)
//	              ↑ 이 대입을 잊으면 입력이 한 글자도 안 들어간다.
//	                컴파일도 되고 경고도 없다. 값 의미론의 대가다.
//
// tab 으로 부품을 옮겨 다니고, ? 로 도움말을 펼친다.
package main

import (
	"fmt"
	"os"
	"strings"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/widgets"
)

type pane int

const (
	paneInput pane = iota
	paneList
	paneViewport
	paneCount
)

var paneNames = [...]string{"입력창", "목록", "뷰포트"}

type model struct {
	w, h  int
	prof  style.Profile
	focus pane

	spin  widgets.Spinner
	prog  widgets.Progress
	input widgets.TextInput
	list  widgets.List
	view  widgets.Viewport
	help  widgets.Help

	pct  float64
	logs []string
}

func newModel() model {
	sp := widgets.NewSpinner()
	sp.Set = widgets.SpinnerTea

	ti := widgets.NewTextInput()
	ti.Prompt = "차 이름: "
	ti.Placeholder = "여기에 적어 보세요"
	// 목록·뷰포트와 상자 폭을 맞춘다. 프롬프트가 9칸이므로 34 - 9 = 25.
	// 이걸 안 맞추면 위아래 상자의 폭이 한 칸 어긋나 JoinVertical 이 빈칸을 덧댄다.
	ti.Width = 25
	ti = ti.Focus()

	items := []widgets.Item{
		widgets.StringItem("보리차 — 볶은 보리"),
		widgets.StringItem("녹차 — 덖은 찻잎"),
		widgets.StringItem("홍차 — 완전 발효"),
		widgets.StringItem("우롱차 — 반 발효"),
		widgets.StringItem("메밀차 — 볶은 메밀"),
		widgets.StringItem("둥굴레차 — 뿌리"),
		widgets.StringItem("black tea"),
		widgets.StringItem("green tea"),
	}
	ls := widgets.NewList(items, 34, 10)
	ls.Title = "차 고르기 (/ 로 거르기)"

	vp := widgets.NewViewport(34, 8)
	vp = vp.SetContent(strings.Join([]string{
		"보리차는 Bubble Tea 가 아니다.",
		"",
		"하지만 같은 모양으로 만들 수 있다. 터미널 드라이버부터 입력 파서, 줄 단위 diff 렌더러, 글자 폭 표, 꾸미기, 그리고 이 부품들까지 전부 표준 라이브러리만으로 쌓아 올렸다.",
		"",
		"↑/↓ 또는 j/k 로 이 글을 움직여 보세요. 마우스 휠도 됩니다.",
		"",
		"이 뷰포트는 넣은 글을 폭에 맞춰 미리 접어 둡니다. 접지 않으면 긴 줄을 터미널이 스스로 감아 버려, 우리가 센 줄 수와 화면의 줄 수가 어긋납니다.",
	}, "\n"))

	return model{
		spin: sp, prog: widgets.NewProgress(30), input: ti,
		list: ls, view: vp, help: widgets.NewHelp(),
		pct: 0.35,
	}
}

func (m model) Init() tea.Cmd { return m.spin.Tick() }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
	case tea.ColorProfileMsg:
		m.prof = msg.Profile
		m.help = m.help.Profile(msg.Profile)
		m.spin.Style = style.New().Profile(msg.Profile).Foreground("205")
		m.prog.FullStyle = style.New().Profile(msg.Profile).Foreground("205")
		m.list.SelectedStyle = style.New().Profile(msg.Profile).Bold(true).Foreground("205")
	case tea.KeyMsg:
		// 거르는 중에는 tab 조차 목록이 가져가야 한다 — 글자를 치는 중이니까.
		if !m.list.Filtering() {
			switch msg.String() {
			case "ctrl+c":
				return m, tea.Quit
			case "tab":
				m.focus = (m.focus + 1) % paneCount
				m.input = m.input.Blur()
				if m.focus == paneInput {
					m.input = m.input.Focus()
				}
				return m, nil
			case "?":
				m.help.ShowAll = !m.help.ShowAll
				return m, nil
			case "+":
				m.pct = clamp(m.pct + 0.05)
				return m, nil
			case "-":
				m.pct = clamp(m.pct - 0.05)
				return m, nil
			}
		}
	}

	// 돌아가는 그림은 초점과 상관없이 늘 돈다.
	var cmds []tea.Cmd
	var cmd tea.Cmd
	m.spin, cmd = m.spin.Update(msg)
	cmds = append(cmds, cmd)

	// 나머지는 초점이 있는 부품에게만 넘긴다.
	switch m.focus {
	case paneInput:
		m.input, cmd = m.input.Update(msg)
	case paneList:
		m.list, cmd = m.list.Update(msg)
	case paneViewport:
		m.view, cmd = m.view.Update(msg)
	}
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

func clamp(v float64) float64 {
	if v < 0 {
		return 0
	}
	if v > 1 {
		return 1
	}
	return v
}

func (m model) View() string {
	base := style.New().Profile(m.prof)
	box := base.Border(style.RoundedBorder).Padding(0, 1)
	on := box.BorderForeground("205")

	frame := func(p pane, s string) string {
		if m.focus == p {
			return on.Render(s)
		}
		return box.Render(s)
	}

	head := base.Bold(true).Render(m.spin.View()+" 보리차 부품 전시장") + "   " +
		base.Faint(true).Render(fmt.Sprintf("초점: %s", paneNames[m.focus]))
	bar := m.prog.View(m.pct)

	left := style.JoinVertical(style.Left,
		frame(paneInput, m.input.View()),
		frame(paneList, m.list.View()),
	)
	right := frame(paneViewport, m.view.View())

	bindings := []widgets.Binding{
		widgets.NewBinding("tab", "부품 옮기기", "tab"),
		widgets.NewBinding("+/-", "진행 막대", "+", "-"),
		widgets.NewBinding("?", "도움말 펼치기", "?"),
		widgets.NewBinding("ctrl+c", "끝내기", "ctrl+c"),
	}
	switch m.focus {
	case paneList:
		bindings = append(m.list.KeyBindings(), bindings...)
	case paneViewport:
		bindings = append(m.view.KeyBindings(), bindings...)
	}

	return style.JoinVertical(style.Left,
		head, bar, "",
		style.JoinHorizontal(style.Top, left, right),
		"", m.help.View(bindings),
	)
}

func main() {
	p := tea.NewProgram(newModel(), tea.WithAltScreen(), tea.WithMouse())
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
