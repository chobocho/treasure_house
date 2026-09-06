// Package menu 는 시작 화면이다. 모드를 고르면 **그 모델로 바뀐다.**
//
// Bubble Tea 에서 화면을 바꾸는 방법이 이 파일의 요점이다. 창을 새로 띄우지 않는다.
// Update 가 자기 자신이 아니라 **다른 모델**을 돌려주면, 그 순간부터 프로그램은
// 그 모델을 쓴다. 화면 전환이 곧 값의 교체다.
//
// 한 가지만 잊지 말 것: 새 모델의 Init() 을 직접 불러서 그 Cmd 를 함께 돌려줘야 한다.
// Bubble Tea 는 프로그램이 시작할 때 한 번만 Init 을 부르기 때문에,
// 바꿔 낀 모델의 첫 틱은 우리가 예약해 줘야 한다. 이걸 빠뜨리면 시간이 안 흐른다.
package menu

import (
	"fmt"
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/battle"
	"treasure/tetris_tui/game"
	"treasure/tetris_tui/ui"
)

// Entry 하나 = 메뉴 한 줄.
type Entry struct {
	Mode  string
	Label string
	Desc  string
}

// entries 는 메뉴에 보이는 모드들. 순서가 곧 화면 순서이고 숫자 키 번호다.
var entries = []Entry{
	{"1p", "1인용", "혼자 쌓는다"},
	{"2p", "2인용 (한 키보드)", "왼쪽 WASD · 오른쪽 화살표"},
	{"ai", "AI 와 1:1", "사람 대 8특징 AI"},
	{"aivai", "AI 대 AI", "구경만 한다"},
}

// Entries 는 메뉴 줄의 사본.
func Entries() []Entry {
	out := make([]Entry, len(entries))
	copy(out, entries)
	return out
}

// ModeNames 는 쓸 수 있는 모드 이름들.
func ModeNames() []string {
	out := make([]string, 0, len(entries))
	for _, e := range entries {
		out = append(out, e.Mode)
	}
	return out
}

// Build 는 모드 이름으로 화면 하나를 만든다.
//
// 깃발(-mode)로 들어오든 메뉴에서 고르든 이 함수를 지난다.
// 두 길이 갈라지면 "메뉴로 들어갈 때만 나는 버그"가 생긴다.
func Build(mode string, seed uint32, level string, bestOf int) (tea.Model, bool) {
	switch mode {
	case "1p":
		return game.New(game.WithSeed(seed)), true
	case "2p":
		return battle.New(battle.Local2P,
			battle.WithSeed(seed), battle.WithBestOf(bestOf)), true
	case "ai":
		return battle.New(battle.VsAI,
			battle.WithSeed(seed), battle.WithLevel(level), battle.WithBestOf(bestOf)), true
	case "aivai":
		return battle.New(battle.AIvsAI,
			battle.WithSeed(seed), battle.WithLevel(level), battle.WithBestOf(bestOf)), true
	}
	return nil, false
}

// Model 은 메뉴 화면.
type Model struct {
	sel    int
	seed   uint32
	level  string
	bestOf int
	w, h   int
}

// New 는 메뉴를 만든다.
func New(seed uint32, level string, bestOf int) Model {
	return Model{seed: seed, level: level, bestOf: bestOf}
}

// Selected 는 지금 고른 줄 번호.
func (m Model) Selected() int { return m.sel }

func (m Model) Init() tea.Cmd { return nil }

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height

	case tea.KeyPressMsg:
		key := msg.String()
		switch key {
		case "up", "k":
			m.sel = (m.sel - 1 + len(entries)) % len(entries)
			return m, nil
		case "down", "j":
			m.sel = (m.sel + 1) % len(entries)
			return m, nil
		case "enter", "space":
			return m.start(m.sel)
		case "q", "esc", "ctrl+c":
			return m, tea.Quit
		}
		// 숫자 키로 바로 고르기. 메뉴에 번호를 적어 뒀으니 눌리면 먹어야 한다.
		if len(key) == 1 && key[0] >= '1' && key[0] <= '9' {
			return m.start(int(key[0] - '1'))
		}
	}
	return m, nil
}

// start 는 고른 줄의 화면으로 바꾼다.
func (m Model) start(i int) (tea.Model, tea.Cmd) {
	if i < 0 || i >= len(entries) {
		return m, nil
	}
	next, ok := Build(entries[i].Mode, m.seed, m.level, m.bestOf)
	if !ok {
		return m, nil
	}
	// 새 화면에 지금 창 크기를 알려 준다. 안 알려 주면 첫 프레임이
	// "창 크기를 기다리는 중"으로 뜨고, 다음 크기 변화가 올 때까지 그대로 있는다.
	if m.w > 0 && m.h > 0 {
		next, _ = next.Update(tea.WindowSizeMsg{Width: m.w, Height: m.h})
	}
	// 그리고 그 화면의 Init 을 직접 부른다 — 이게 빠지면 시간이 안 흐른다.
	return next, next.Init()
}

var (
	titleStyle = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#00F0F0"))
	selStyle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#F0F000"))
)

func (m Model) View() tea.View {
	var b strings.Builder
	b.WriteString(titleStyle.Render("Bubble Tea 테트리스"))
	b.WriteString("\n\n")

	for i, e := range entries {
		// %-18s 는 룬 수로 채워서 한글 라벨은 열이 어긋난다. 칸 수로 채운다.
		label := lipgloss.NewStyle().Width(18).Render(e.Label)
		line := fmt.Sprintf("  %d) %s %s", i+1, label, e.Desc)
		if i == m.sel {
			line = selStyle.Render(fmt.Sprintf("▶ %d) %s %s", i+1, label, e.Desc))
		}
		b.WriteString(line)
		b.WriteByte('\n')
	}

	b.WriteString("\n")
	b.WriteString(ui.DimStyle.Render(fmt.Sprintf(
		"AI 난이도 %s · %d판제 · 시드 %d", m.level, m.bestOf, m.seed)))
	b.WriteString("\n")
	b.WriteString(ui.DimStyle.Render("↑↓ 고르기 · Enter 시작 · 숫자 키로 바로 · q 나가기"))

	out := b.String()
	if m.w == 0 || m.h == 0 {
		return tea.NewView(out + "\n")
	}
	out = lipgloss.NewStyle().MaxWidth(m.w).MaxHeight(m.h).Render(out)
	v := tea.NewView(lipgloss.Place(m.w, m.h, lipgloss.Center, lipgloss.Center, out))
	v.AltScreen = true
	return v
}
