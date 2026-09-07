// 06_style — 꾸미기.
//
// style 패키지는 Lip Gloss 가 하는 일의 부분집합이다. 스타일이 값이라는 것이 핵심이라,
// 전역에 선언해 두고 여기저기서 조금씩 바꿔 써도 서로 간섭하지 않는다.
//
// 색 수준은 프로그램이 시작할 때 ColorProfileMsg 로 알려 준다. 그 값을 스타일에
// 넣어 두면, 24비트를 못 내는 터미널에서는 알아서 가장 가까운 색으로 내려 맞춘다.
package main

import (
	"fmt"
	"os"

	"treasure/boricha/style"
	"treasure/boricha/tea"
)

type model struct {
	prof style.Profile
	sel  int
}

var samples = []struct {
	name string
	make func(style.Style) style.Style
}{
	{"굵게", func(s style.Style) style.Style { return s.Bold(true) }},
	{"밑줄", func(s style.Style) style.Style { return s.Underline(true) }},
	{"분홍 글씨", func(s style.Style) style.Style { return s.Foreground("205") }},
	{"파란 바탕", func(s style.Style) style.Style { return s.Background("4").Padding(0, 1) }},
	{"둥근 테두리", func(s style.Style) style.Style {
		return s.Border(style.RoundedBorder).Padding(0, 1).BorderForeground("205")
	}},
	{"가운데 정렬", func(s style.Style) style.Style {
		return s.Width(24).Align(style.Center).Border(style.NormalBorder)
	}},
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.ColorProfileMsg:
		m.prof = msg.Profile
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "down", "j":
			m.sel = (m.sel + 1) % len(samples)
		case "up", "k":
			m.sel = (m.sel - 1 + len(samples)) % len(samples)
		}
	}
	return m, nil
}

func (m model) View() string {
	base := style.New().Profile(m.prof)
	title := base.Bold(true).Foreground("205").Render("보리차 스타일 전시")
	head := base.Faint(true).Render(fmt.Sprintf("이 터미널의 색 수준: %s", m.prof))

	var rows []string
	for i, s := range samples {
		mark := "  "
		if i == m.sel {
			mark = "▸ "
		}
		label := base.Width(14).Render(mark + s.name)
		demo := s.make(base).Render("보리차 tea")
		rows = append(rows, style.JoinHorizontal(style.Top, label, demo))
	}
	body := style.JoinVertical(style.Left, rows...)
	help := base.Faint(true).Render("↑/↓ 고르기   q 끝내기")

	return style.JoinVertical(style.Left, title, head, "", body, "", help)
}

func main() {
	if _, err := tea.NewProgram(model{}, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
