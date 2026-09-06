package game

import (
	tea "charm.land/bubbletea/v2"

	"treasure/tetris_tui/core"
	"treasure/tetris_tui/ui"
)

// Init 은 첫 틱을 예약한다. 타이머를 껐으면 아무것도 안 한다.
func (m Model) Init() tea.Cmd {
	if !m.timer {
		return nil
	}
	return Tick()
}

// Update 는 키와 틱을 받아 판을 굴린다.
//
// 이 함수의 모양이 Bubble Tea 프로그램의 전부다: 메시지 종류로 분기하고,
// 바뀐 모델과 (필요하면) 다음 Cmd 를 돌려준다. 규칙은 core 가, 그림은 View 가 맡는다.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height

	case TickMsg:
		m.advance()
		if !m.timer {
			return m, nil
		}
		// 이 한 줄이 빠지면 중력이 한 번 뛰고 영영 멈춘다.
		// 일시정지 중에도 사슬은 이어 둔다 — 끊으면 정지를 풀어도 시간이 안 흐른다.
		return m, Tick()

	case tea.KeyPressMsg:
		return m.press(msg.String())
	}
	return m, nil
}

// advance 는 시간을 한 틱만큼 진행시킨다.
func (m *Model) advance() {
	// 소프트드롭의 "키를 뗌"을 시간으로 흉내 낸다.
	// 터미널이 알려 주지 않는 사건을 타임아웃으로 대신 만드는 것 —
	// TUI 에서 흔히 쓰는 편법이고, 정직하게 말해 두는 편이 낫다.
	if m.softOn {
		m.softIdle += TickMs
		if m.softIdle >= SoftReleaseMs {
			m.g.Release(core.ActSoft)
			m.softOn = false
		}
	}
	m.g.Update(TickMs)
}

// press 는 키 하나를 처리한다.
func (m Model) press(key string) (tea.Model, tea.Cmd) {
	switch ui.LookupGlobal(key) {
	case ui.GlobalQuit:
		m.quit = true
		return m, tea.Quit
	case ui.GlobalPause:
		m.g.Press(core.ActPause)
		return m, nil
	case ui.GlobalRestart:
		m.seed = nextSeed(m.seed)
		m.g.Init(m.seed)
		m.softOn, m.softIdle = false, 0
		return m, nil
	case ui.GlobalHelp:
		m.help = !m.help
		return m, nil
	}

	act, ok := m.keys.Lookup(key)
	if !ok {
		return m, nil
	}
	m.apply(act)
	return m, nil
}

// apply 는 조작 하나를 코어에 넣는다.
//
// 좌우와 소프트드롭이 서로 다르게 처리되는 이유가 이 함수의 전부다.
// 터미널에는 "키를 뗐다"가 없으므로, 코어의 DAS/ARR(누른 채로 두면 자동반복)를
// 그대로 쓰면 한 번 누른 조각이 혼자 벽까지 미끄러져 간다.
//
//	좌우      : 누르자마자 놓는다. 반복은 OS 의 키 자동반복에 맡긴다.
//	소프트드롭 : 눌러 둔 채로 두고, 한동안 조용하면 타임아웃으로 놓는다.
//	나머지    : 한 번짜리 동작이라 누르기만 하면 된다.
func (m *Model) apply(act core.Action) {
	switch act {
	case core.ActLeft, core.ActRight:
		m.g.Press(act)
		m.g.Release(act)
	case core.ActSoft:
		if !m.softOn {
			m.g.Press(core.ActSoft)
			m.softOn = true
		}
		m.softIdle = 0
	default:
		m.g.Press(act)
	}
}
