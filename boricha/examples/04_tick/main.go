// 04_tick — 시간을 다루기. 그리고 이 덱에서 가장 자주 걸려 넘어지는 함정.
//
// tea.Tick 은 **한 번만** 울린다. 되풀이하려면 그 사건을 받은 자리에서 다시 걸어야 한다.
// "왜 시계가 한 번만 가지?" 는 Bubble Tea 를 처음 쓰는 사람이 거의 예외 없이 겪는다.
//
// 되풀이를 기본으로 두지 않은 이유가 있다. 그러면 멈추는 방법을 따로 만들어야 하고,
// 모델이 사라진 뒤에도 도는 시계가 남는다. 다시 거는 쪽이 통제하기 쉽다.
package main

import (
	"fmt"
	"os"
	"strings"
	"time"

	"treasure/boricha/tea"
)

type tickMsg time.Time

type model struct {
	ticks  int
	now    time.Time
	paused bool
}

// tick 은 "다음 울림" 을 예약한다. Init 과 Update 두 곳에서 같은 함수를 쓴다.
func tick() tea.Cmd {
	return tea.Tick(200*time.Millisecond, func(t time.Time) tea.Msg { return tickMsg(t) })
}

func (m model) Init() tea.Cmd { return tick() }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tickMsg:
		if m.paused {
			// 멈춤 상태에서는 다시 걸지 않는다 → 시계가 자연히 멎는다.
			return m, nil
		}
		m.ticks++
		m.now = time.Time(msg)
		return m, tick() // ← 재예약. 이 줄을 지우면 화면이 한 번 바뀌고 멈춘다.
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case " ", "space":
			m.paused = !m.paused
			if !m.paused {
				return m, tick() // 다시 시작할 때는 여기서 다시 건다
			}
		}
	}
	return m, nil
}

func (m model) View() string {
	bar := strings.Repeat("█", m.ticks%30)
	state := "도는 중"
	if m.paused {
		state = "멈춤"
	}
	return fmt.Sprintf("보리차 우리는 중… (%s)\n\n%-30s\n\n울림 %d번   %s\n\nspace 멈춤/재개   q 끝내기",
		state, bar, m.ticks, m.now.Format("15:04:05.000"))
}

func main() {
	if _, err := tea.NewProgram(model{}, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
