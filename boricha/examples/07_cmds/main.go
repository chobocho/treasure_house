// 07_cmds — 명령: 순수하지 않은 일을 순수한 자리 밖으로 밀어내기.
//
// Update 는 순수해야 한다. 같은 사건에 늘 같은 결과를 내야 시험할 수 있기 때문이다.
// 그런데 파일을 읽고, 시계를 보고, 그물 너머에 묻는 일은 순수하지 않다.
// 그래서 Update 는 그 일을 하지 않고 "이 일을 해 달라" 는 함수(Cmd)를 돌려준다.
//
// Batch 는 한꺼번에(순서 없음), Sequence 는 차례로(순서 있음).
// b 와 s 를 각각 눌러 도착 순서가 어떻게 다른지 보라.
package main

import (
	"fmt"
	"os"
	"strings"
	"time"

	"treasure/boricha/tea"
)

type doneMsg struct {
	name string
	at   time.Time
}

// work 는 "d 만큼 걸리는 일" 을 흉내 낸다. 진짜라면 여기서 HTTP 를 부르거나
// 파일을 읽을 것이다. 중요한 것은 이 함수가 **다른 고루틴에서** 돈다는 점이다 —
// 그동안에도 화면은 멀쩡히 돌아가고 키도 받는다.
func work(name string, d time.Duration) tea.Cmd {
	return func() tea.Msg {
		time.Sleep(d)
		return doneMsg{name: name, at: time.Now()}
	}
}

type model struct {
	log   []string
	start time.Time
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case doneMsg:
		ms := msg.at.Sub(m.start).Milliseconds()
		m.log = append(append([]string{}, m.log...), fmt.Sprintf("%4dms  %s", ms, msg.name))
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "b":
			m.log, m.start = nil, time.Now()
			// 셋이 동시에 돈다. 300ms 짜리를 먼저 넣어도 100ms 짜리가 먼저 도착한다.
			return m, tea.Batch(
				work("느린 일 (300ms)", 300*time.Millisecond),
				work("보통 일 (200ms)", 200*time.Millisecond),
				work("빠른 일 (100ms)", 100*time.Millisecond),
			)
		case "s":
			m.log, m.start = nil, time.Now()
			// 앞의 것이 끝나야 다음이 시작한다. 그래서 넣은 순서대로 도착한다.
			return m, tea.Sequence(
				work("첫째 (300ms)", 300*time.Millisecond),
				work("둘째 (200ms)", 200*time.Millisecond),
				work("셋째 (100ms)", 100*time.Millisecond),
			)
		}
	}
	return m, nil
}

func (m model) View() string {
	var b strings.Builder
	b.WriteString("명령 실습\n")
	b.WriteString(strings.Repeat("─", 34) + "\n")
	b.WriteString("b  Batch — 한꺼번에 (순서 없음)\n")
	b.WriteString("s  Sequence — 차례로 (순서 있음)\n")
	b.WriteString("q  끝내기\n\n")
	if len(m.log) == 0 {
		b.WriteString("(b 나 s 를 눌러 보세요)")
	}
	for _, l := range m.log {
		b.WriteString(l + "\n")
	}
	return b.String()
}

func main() {
	if _, err := tea.NewProgram(model{}, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
