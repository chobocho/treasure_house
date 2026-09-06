package battle

import (
	tea "charm.land/bubbletea/v2"

	"treasure/tetris_tui/ai"
	"treasure/tetris_tui/core"
	"treasure/tetris_tui/ui"
)

// Init 은 첫 틱을 예약한다.
func (m Model) Init() tea.Cmd {
	if !m.timer {
		return nil
	}
	return Tick()
}

// Update 는 키·틱·탐색 결과를 받는다.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height

	case TickMsg:
		return m.tick()

	case AIMoveMsg:
		// 탐색이 끝났다. 드라이버가 목표를 세우고, 그다음부터 키를 누르기 시작한다.
		if d := m.drv[msg.Seat]; d != nil {
			d.SetTarget(msg.Move, msg.OK)
		}
		return m, nil

	case tea.KeyPressMsg:
		return m.press(msg.String())
	}
	return m, nil
}

// tick 은 시간을 한 칸 진행시키고, AI 자리가 할 일을 모은다.
//
// 여기가 §5.3 의 패턴이 실제로 사는 곳이다. 탐색은 **이 함수 안에서 돌지 않는다.**
// 드라이버가 "생각할 때"라고 하면 Cmd 를 하나 만들어 돌려주고, 결과는 나중에
// AIMoveMsg 로 돌아온다. 그동안에도 Update 는 계속 키와 틱을 처리한다 —
// 그래서 AI 가 생각하는 동안에도 사람의 판이 멈추지 않는다.
func (m Model) tick() (tea.Model, tea.Cmd) {
	m.releaseSoftDrops()
	m.match.Advance(TickMs)

	var cmds []tea.Cmd
	for s := Seat(0); s < Seats; s++ {
		d := m.drv[s]
		if d == nil {
			continue
		}
		step := d.Tick(m.match.Game(s), TickMs)
		switch step.Kind {
		case StepPlan:
			// 판의 **사본**을 넘긴다. Cmd 는 다른 고루틴에서 돌기 때문에
			// 진행 중인 판을 들여다보면 그 자리에서 자료 경쟁이다.
			cmds = append(cmds, thinkCmd(s, ai.SnapshotOf(m.match.Game(s)), d.Level().Weights))
		case StepPress:
			m.applyTo(s, step.Act)
		}
	}
	if m.timer {
		cmds = append(cmds, Tick())
	}
	if len(cmds) == 0 {
		return m, nil
	}
	return m, tea.Batch(cmds...)
}

// thinkCmd 는 탐색 하나를 Cmd 로 감싼다.
//
// 이 함수가 돌려주는 함수 안에서는 모델을 건드리면 안 된다. 필요한 것은
// 전부 인자로 복사해서 들어왔고, 결과는 오직 반환하는 메시지로만 나간다.
func thinkCmd(seat Seat, snap ai.Snapshot, w ai.Weights) tea.Cmd {
	return func() tea.Msg {
		var s ai.Searcher
		mv, _, ok := s.BestOf(snap, w)
		return AIMoveMsg{Seat: seat, Move: mv, OK: ok}
	}
}

// releaseSoftDrops 는 사람 자리의 소프트드롭 타임아웃을 돌린다.
func (m *Model) releaseSoftDrops() {
	for s := Seat(0); s < Seats; s++ {
		if !m.softOn[s] {
			continue
		}
		m.softIdle[s] += TickMs
		if m.softIdle[s] >= SoftReleaseMs {
			m.match.Game(s).Release(core.ActSoft)
			m.softOn[s] = false
		}
	}
}

// press 는 키 하나를 처리한다.
//
// 두 자리의 키맵을 차례로 뒤진다. 자리마다 키가 겹치지 않는다는 것은
// ui 패키지의 테스트가 지켜 준다 — 겹치면 한 번의 입력이 양쪽을 동시에 움직인다.
func (m Model) press(key string) (tea.Model, tea.Cmd) {
	switch ui.LookupGlobal(key) {
	case ui.GlobalQuit:
		return m, tea.Quit
	case ui.GlobalPause:
		for s := Seat(0); s < Seats; s++ {
			m.match.Game(s).Press(core.ActPause)
		}
		return m, nil
	case ui.GlobalRestart:
		m.match.Restart()
		m.resetSeats()
		return m, nil
	case ui.GlobalHelp:
		m.help = !m.help
		return m, nil
	}

	// 라운드가 끝났을 때의 Enter — 다음 라운드로, 대전이 끝났으면 처음부터.
	if key == "enter" {
		if _, _, over := m.match.RoundOver(); over {
			if _, done := m.match.MatchOver(); done {
				m.match.Restart()
			} else {
				m.match.NextRound()
			}
			m.resetSeats()
		}
		return m, nil
	}

	for s := Seat(0); s < Seats; s++ {
		if !m.human[s] {
			continue
		}
		if act, ok := m.keys[s].Lookup(key); ok {
			m.applyTo(s, act)
			return m, nil
		}
	}
	return m, nil
}

// applyTo 는 한 자리에 조작 하나를 넣는다.
//
// 1인용과 같은 규칙이다: 좌우는 누르자마자 놓아 코어의 DAS 를 끄고,
// 소프트드롭은 눌러 둔 채로 두었다가 타임아웃으로 놓는다.
func (m *Model) applyTo(s Seat, act core.Action) {
	g := m.match.Game(s)
	switch act {
	case core.ActLeft, core.ActRight:
		g.Press(act)
		g.Release(act)
	case core.ActSoft:
		if !m.softOn[s] {
			g.Press(core.ActSoft)
			m.softOn[s] = true
		}
		m.softIdle[s] = 0
	default:
		g.Press(act)
	}
}

// resetSeats 는 라운드가 바뀔 때 자리별 상태를 처음으로 돌린다.
func (m *Model) resetSeats() {
	for s := Seat(0); s < Seats; s++ {
		m.softOn[s], m.softIdle[s] = false, 0
		if m.drv[s] != nil {
			m.drv[s].Reset()
		}
	}
}
