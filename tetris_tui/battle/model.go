package battle

import (
	"time"

	tea "charm.land/bubbletea/v2"

	"treasure/tetris_tui/ai"
	"treasure/tetris_tui/ui"
)

// Mode 는 누가 어느 자리에 앉는가.
//
// 세 모드가 같은 모델·같은 규칙·같은 화면을 쓴다. 달라지는 것은 자리마다
// human 이 true 인지 drv 가 붙어 있는지뿐이다. 이렇게 나눠야
// "AI 는 사람과 다른 규칙으로 논다"는 의심이 생길 여지가 없다.
type Mode int

const (
	Local2P Mode = iota // 한 키보드에 두 사람
	VsAI                // 왼쪽 사람, 오른쪽 AI
	AIvsAI              // 둘 다 AI (기록·시연용)
)

const (
	TickMs       = 33
	TickInterval = TickMs * time.Millisecond

	// 소프트드롭의 "키를 뗌"을 흉내 내는 타임아웃. 1인용과 같은 값을 쓴다.
	SoftReleaseMs = 120
)

// TickMsg 는 시간이 한 칸 흘렀다는 신호.
type TickMsg struct{}

// AIMoveMsg 는 탐색이 끝나 수가 정해졌다는 신호.
//
// 어느 자리의 결과인지 담아야 한다. 두 AI 가 동시에 생각할 수 있고,
// 결과가 도착하는 순서는 보장되지 않기 때문이다.
type AIMoveMsg struct {
	Seat Seat
	Move ai.Move
	OK   bool
}

// Model 은 대전 화면.
type Model struct {
	mode  Mode
	match *Match

	human [Seats]bool
	keys  [Seats]ui.KeyMap
	names [Seats]string
	drv   [Seats]*Driver

	softOn   [Seats]bool
	softIdle [Seats]int

	w, h   int
	seed   uint32
	level  Level
	bestOf int
	help   bool
	timer  bool
}

// Option 은 New 에 넘기는 설정.
type Option func(*Model)

// WithSeed 는 시드를 지정한다.
func WithSeed(seed uint32) Option { return func(m *Model) { m.seed = seed } }

// WithoutTimer 는 tea.Tick 을 걸지 않게 한다 — 기록·테스트용.
func WithoutTimer() Option { return func(m *Model) { m.timer = false } }

// WithLevel 은 AI 난이도를 고른다. 모르는 이름이면 그냥 무시한다 —
// 화면이 이미 떠 있는데 난이도 하나 때문에 프로그램이 죽으면 안 된다.
func WithLevel(name string) Option {
	return func(m *Model) {
		if l, ok := LevelByName(name); ok {
			m.level = l
		}
	}
}

// WithBestOf 는 몇 판제인지 정한다.
func WithBestOf(n int) Option {
	return func(m *Model) {
		if n >= 1 {
			m.bestOf = n
		}
	}
}

// New 는 대전 모델을 만든다.
func New(mode Mode, opts ...Option) Model {
	m := Model{
		mode:   mode,
		seed:   uint32(time.Now().UnixNano()),
		bestOf: 3,
		timer:  true,
	}
	if lv, ok := LevelByName("hard"); ok {
		m.level = lv
	}
	for _, o := range opts {
		o(&m)
	}
	m.match = NewMatch(m.seed, m.bestOf)

	switch mode {
	case Local2P:
		m.human = [Seats]bool{true, true}
		m.keys = [Seats]ui.KeyMap{ui.Wasd, ui.Arrows}
		m.names = [Seats]string{"1P", "2P"}
	case VsAI:
		m.human = [Seats]bool{true, false}
		m.keys = [Seats]ui.KeyMap{ui.Arrows, {}}
		m.names = [Seats]string{"사람", "AI " + m.level.Short}
	case AIvsAI:
		m.names = [Seats]string{"AI 최종", "AI " + m.level.Short}
	}

	// AI 자리마다 드라이버를 붙인다. 시드를 다르게 줘야 두 AI 의 실수가
	// 똑같은 순간에 똑같이 일어나지 않는다.
	for s := Seat(0); s < Seats; s++ {
		if m.human[s] {
			continue
		}
		lv := m.level
		if mode == AIvsAI && s == Left {
			// 왼쪽은 언제나 최종 가중치. 난이도 차이가 눈에 보여야 시연이 된다.
			if top, ok := LevelByName("max"); ok {
				lv = top
			}
		}
		m.drv[s] = NewDriver(lv, m.seed+uint32(s)*2654435761)
	}
	return m
}

// Tick 은 시간 진행을 예약하는 Cmd.
func Tick() tea.Cmd {
	return tea.Tick(TickInterval, func(time.Time) tea.Msg { return TickMsg{} })
}

// Match 는 진행 중인 대전. 기록 도구와 테스트가 들여다본다.
func (m Model) Match() *Match { return m.match }

// Driver 는 한 자리의 AI 손. 사람 자리면 nil.
func (m Model) Driver(s Seat) *Driver { return m.drv[s] }

// seatTitle 은 패널 위에 새길 이름.
//
// 승수를 여기 붙이지 않는다. 패널의 속 폭이 12칸뿐이라 "AI 어려움 0승"은
// 줄바꿈이 되고, 그러면 두 패널의 높이가 달라져 화면이 어긋난다.
// 승수는 아래 seatNote 로 내린다.
func (m Model) seatTitle(s Seat) string { return m.names[s] }
