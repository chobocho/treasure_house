// 03_keys — 키 입력이 정확히 어떤 모양으로 들어오는지 눈으로 본다.
//
// 테트리스를 만들다 보면 "왜 이 키가 안 먹지?"에 반드시 부딪힌다.
// 답은 거의 항상 "내가 상상한 이름과 실제 이름이 다르다"이다.
// 그래서 규칙을 외우는 대신, 눌러 보고 확인하는 도구를 먼저 만든다.
//
// tea.KeyPressMsg 는 네 조각으로 되어 있다:
//
//	String()  "left", "ctrl+c", "a" — 사람이 읽는 이름. switch 에 쓸 것.
//	Code      눌린 키 (rune). 'a' 같은 문자이거나 tea.KeyLeft 같은 특수값.
//	Text      실제로 입력된 문자. 특수 키·조합 키에서는 **빈 문자열**이다.
//	Mod       ctrl/alt/shift 비트. tea.ModCtrl 등과 & 로 검사한다.
//
//	go run ./examples/03_keys
package main

import (
	"fmt"
	"os"
	"strings"

	tea "charm.land/bubbletea/v2"
)

// 기록 상한. 없으면 화면 밖으로 넘쳐 흐르고, 터미널이 스크롤되면서
// 이전 화면이 지저분하게 남는다 — 상한은 TUI 의 기본 예의다.
const histMax = 12

type model struct {
	hist []string // 최신이 앞
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		// 이 예제에서는 q 도 "그냥 키"로 보여 줘야 하므로 ctrl+c 만 종료로 쓴다.
		if msg.String() == "ctrl+c" {
			return m, tea.Quit
		}
		m.hist = append([]string{describe(msg)}, m.hist...)
		if len(m.hist) > histMax {
			m.hist = m.hist[:histMax]
		}
	}
	return m, nil
}

// 키 하나를 한 줄로 풀어 쓴다.
// Code 는 rune 이라 %q 로 찍으면 '\x1b' 같은 특수값도 안전하게 보인다.
func describe(k tea.KeyPressMsg) string {
	text := k.Text
	if text == "" {
		text = "(없음)" // 특수 키와 조합 키는 여기가 반드시 빈다
	}
	return fmt.Sprintf("%-12s Code=%q(%d)  Text=%-8s Mod=%s",
		k.String(), k.Code, k.Code, text, mods(k.Mod))
}

func mods(m tea.KeyMod) string {
	var on []string
	if m&tea.ModCtrl != 0 {
		on = append(on, "ctrl")
	}
	if m&tea.ModAlt != 0 {
		on = append(on, "alt")
	}
	if m&tea.ModShift != 0 {
		on = append(on, "shift")
	}
	if len(on) == 0 {
		return "-"
	}
	return strings.Join(on, "+")
}

func (m model) View() tea.View {
	var b strings.Builder
	b.WriteString("키를 눌러 보세요. ctrl+c 로 끝냅니다.\n\n")
	if len(m.hist) == 0 {
		b.WriteString("  (아무 키나 눌러 보세요 — 화살표, ctrl 조합, 한글도 됩니다)\n")
	}
	for _, line := range m.hist {
		b.WriteString("  " + line + "\n")
	}
	return tea.NewView(b.String())
}

func main() {
	if _, err := tea.NewProgram(model{}).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
