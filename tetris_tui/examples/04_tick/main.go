// 04_tick — 시간을 다루는 법. 테트리스의 중력이 바로 이 패턴이다.
//
// Bubble Tea 에는 "매 프레임 도는 루프"가 없다. 시간이 흐르게 하려면
// tea.Tick 으로 "이 시간 뒤에 이 메시지를 보내 달라"고 예약한다.
//
// 초보자가 반드시 한 번 밟는 함정:
//
//	tea.Tick 은 **한 번만** 보낸다.
//	받은 자리에서 다시 예약하지 않으면 시계가 한 번 뛰고 영영 멈춘다.
//
// 그래서 tickMsg 를 처리하는 곳의 return 에 늘 doTick() 이 붙어 있다.
// 5부의 중력도, 7부의 두 판 동시 진행도 전부 이 사슬 위에 있다.
//
//	go run ./examples/04_tick
package main

import (
	"fmt"
	"os"
	"time"

	tea "charm.land/bubbletea/v2"
)

// 틱 간격을 상수 하나로 고정한다. 예약하는 쪽과 경과 시간을 계산하는 쪽이
// 서로 다른 숫자를 쓰면 화면의 시계가 조용히 틀려진다.
const tickEvery = 100 * time.Millisecond

// 메시지 타입은 이렇게 얇아도 된다. 중요한 건 "이 타입이 곧 사건의 이름"이라는 것.
type tickMsg time.Time

type model struct {
	ticks   int
	running bool
}

// tea.Tick 은 (기간, 시각→메시지 함수) 를 받아 Cmd 를 만든다.
// 이 함수를 한 군데 모아 두면 "예약을 빠뜨렸다"를 눈으로 잡기 쉬워진다.
func doTick() tea.Cmd {
	return tea.Tick(tickEvery, func(t time.Time) tea.Msg { return tickMsg(t) })
}

func (m model) Init() tea.Cmd {
	if m.running {
		return doTick() // 사슬의 첫 고리
	}
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tickMsg:
		if !m.running {
			// 멈춘 동안에는 사슬을 잇지 않는다. 이어 두면 멈춰도 타이머가 계속 돈다.
			return m, nil
		}
		m.ticks++
		return m, doTick() // ← 이 한 줄이 빠지면 시계가 죽는다

	case tea.KeyPressMsg:
		switch msg.String() {
		case " ", "space":
			m.running = !m.running
			if m.running {
				// 멈춰 있는 동안 사슬이 끊겼으므로 여기서 새로 시작해 준다.
				return m, doTick()
			}
			return m, nil
		case "r":
			m.ticks = 0
		case "q", "ctrl+c", "esc":
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	state := "멈춤"
	if m.running {
		state = "진행 중"
	}
	// 틱 수 × 간격 = 경과 시간. 중력도 똑같이 "몇 틱 지났나"로 계산한다.
	sec := float64(m.ticks) * tickEvery.Seconds()
	return tea.NewView(fmt.Sprintf(
		"틱: %d   경과: %.1f초   상태: %s\n\n간격 %v · space 멈춤/재개 · r 되돌리기 · q 끝내기\n",
		m.ticks, sec, state, tickEvery))
}

func main() {
	if _, err := tea.NewProgram(model{running: true}).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
