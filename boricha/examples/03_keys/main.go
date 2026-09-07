// 03_keys — 키가 어떻게 오는지 눈으로 보기.
//
// 0단계의 00_raw 는 바이트를 그대로 보여 줬다. 여기서는 그 바이트가 파서를 거쳐
// "ctrl+c", "shift+tab", "한" 같은 이름이 되어 도착한다.
// 방향키를 눌러 보고, alt 나 ctrl 을 섞어 눌러 보고, 한글도 쳐 보라.
package main

import (
	"fmt"
	"os"
	"strings"

	"treasure/boricha/tea"
)

const keep = 12 // 최근 몇 개를 보여 줄까

type model struct {
	keys []string
	n    int
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	key, ok := msg.(tea.KeyMsg)
	if !ok {
		return m, nil
	}
	if key.String() == "ctrl+c" {
		return m, tea.Quit
	}

	// 슬라이스를 그대로 append 하면 복사본끼리 같은 배열을 나눠 갖게 된다.
	// 값 의미론을 지키려면 여기서 새 슬라이스를 만들어야 한다 — 흔히 놓치는 자리다.
	next := make([]string, 0, len(m.keys)+1)
	next = append(next, m.keys...)
	next = append(next, describe(key))
	if len(next) > keep {
		next = next[len(next)-keep:]
	}
	m.keys = next
	m.n++
	return m, nil
}

// describe 는 키 하나를 "이름 (코드·글자)" 로 풀어 쓴다.
func describe(k tea.KeyMsg) string {
	s := fmt.Sprintf("%-16s", k.String())
	if k.Text != "" {
		s += fmt.Sprintf("글자 %q", k.Text)
	} else {
		s += fmt.Sprintf("코드 U+%04X", k.Code)
	}
	if k.Mod != 0 {
		s += fmt.Sprintf("  조합 %d", int(k.Mod))
	}
	return s
}

func (m model) View() string {
	var b strings.Builder
	b.WriteString("눌린 키 (ctrl+c 로 끝내기)\n")
	b.WriteString(strings.Repeat("─", 40) + "\n")
	for _, k := range m.keys {
		b.WriteString("  " + k + "\n")
	}
	for i := len(m.keys); i < keep; i++ {
		b.WriteString("\n")
	}
	b.WriteString(fmt.Sprintf("\n모두 %d번", m.n))
	return b.String()
}

func main() {
	if _, err := tea.NewProgram(model{}, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
