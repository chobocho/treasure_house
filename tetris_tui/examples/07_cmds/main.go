// 07_cmds — Cmd 는 "지금 하는 일"이 아니라 "나중에 올 메시지의 주문서"다.
//
// Update 안에서 시간이 걸리는 일을 하면 그동안 화면이 얼어붙는다.
// 키도 안 먹고, 중력도 안 돌고, 상대 판도 멈춘다. 해결책은 하나다:
// **오래 걸리는 일은 Cmd 로 밖에 내보내고, 결과를 메시지로 받는다.**
//
// 6부의 AI 가 정확히 이 구조로 돌아간다. ai.Best() 는 수십 밀리초를 먹지만
// Update 안에서 부르지 않는다 — Cmd 로 내보내고 aiMoveMsg 로 돌려받는다.
//
// 조합 도구 둘:
//
//	tea.Batch(a, b)     둘을 동시에 띄운다. 도착 순서는 보장하지 않는다.
//	tea.Sequence(a, b)  a 가 끝나야 b 를 시작한다. 순서가 중요할 때.
//
//	go run ./examples/07_cmds
package main

import (
	"fmt"
	"math/rand"
	"os"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
)

const logMax = 8

// 아무 결과도 없는 "끝났다" 신호.
type doneMsg struct{}

// AI 가 고른 수. 6부의 aiMoveMsg 가 이것의 진짜 판이다.
type moveMsg struct{ col int }

type model struct {
	status   string
	log      []string
	thinking bool
}

func (m model) Init() tea.Cmd { return nil }

// 생각하는 척하는 Cmd. 진짜 AI 라면 여기서 ai.Best() 를 부른다.
//
// 이 함수 안의 코드는 Update 와 **다른 고루틴**에서 돈다.
// 그래서 모델을 건드리면 안 된다 — 필요한 값은 인자로 복사해서 넘기고,
// 결과는 오직 반환하는 메시지로만 전달한다. 이게 규칙의 전부다.
func think(delay time.Duration) tea.Cmd {
	return func() tea.Msg {
		time.Sleep(delay)
		return moveMsg{col: rand.Intn(10)}
	}
}

func note(text string) tea.Cmd {
	return func() tea.Msg { return noteMsg(text) }
}

type noteMsg string

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "b":
			m.status = "동시에 둘 실행 (Batch)"
			return m, tea.Batch(note("Batch: 첫째"), note("Batch: 둘째"))
		case "s":
			m.status = "차례대로 둘 실행 (Sequence)"
			return m, tea.Sequence(note("Sequence: 첫째"), note("Sequence: 둘째"))
		case "t":
			if m.thinking {
				// 이미 생각 중이면 무시한다. 안 그러면 Cmd 가 겹쳐서
				// 결과가 두 번 오고, 조각이 두 번 움직인다.
				return m, nil
			}
			m.thinking = true
			m.status = "AI 가 생각하는 중…"
			return m, think(300 * time.Millisecond)
		case "q", "ctrl+c", "esc":
			return m, tea.Quit
		}

	case moveMsg:
		m.thinking = false
		m.status = "대기"
		m = m.push(fmt.Sprintf("AI 가 고른 열: %d", msg.col))

	case noteMsg:
		m = m.push(string(msg))

	case doneMsg:
		m = m.push("끝")
	}
	return m, nil
}

// 기록 한 줄 추가. 값 리시버라 새 모델을 돌려준다 — 이 파일의 모든 상태 변경이 이 모양이다.
func (m model) push(line string) model {
	m.log = append([]string{line}, m.log...)
	if len(m.log) > logMax {
		m.log = m.log[:logMax]
	}
	return m
}

func (m model) View() tea.View {
	var b strings.Builder
	fmt.Fprintf(&b, "상태: %s\n\n", m.status)
	for _, line := range m.log {
		b.WriteString("  " + line + "\n")
	}
	b.WriteString("\nb 동시(Batch) · s 차례대로(Sequence) · t 생각하기 · q 끝내기\n")
	return tea.NewView(b.String())
}

func main() {
	if _, err := tea.NewProgram(model{status: "대기"}).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
