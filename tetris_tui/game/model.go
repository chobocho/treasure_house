// Package game 은 1인용 테트리스의 Bubble Tea 모델이다.
//
// 여기서 2~5부에서 배운 것들이 처음으로 한자리에 모인다:
// Model/Update/View(2부), 틱 재예약(2부 04_tick), 창 크기(2부 05_window),
// 스타일과 Join(3부), 그리고 코어의 규칙(4부).
//
// 이 패키지에는 **규칙이 한 줄도 없다.** 회전이 되는지, 줄이 지워지는지,
// 점수가 얼마인지는 전부 core 가 안다. 여기가 아는 것은 "어떤 키가 어떤 뜻인가"와
// "지금 화면을 어떻게 그릴 것인가"뿐이다.
package game

import (
	"time"

	tea "charm.land/bubbletea/v2"

	"treasure/tetris_tui/core"
	"treasure/tetris_tui/ui"
)

// TickMs 는 한 틱이 게임 시간으로 몇 밀리초인지.
//
// 33ms ≈ 초당 30프레임. 더 촘촘히 하면 터미널이 다시 그리는 비용만 늘고,
// 더 성기게 하면 레벨이 높을 때 조각이 뚝뚝 끊겨 떨어진다.
// 코어가 dt 를 100ms 로 자르므로 이 값이 그보다 크면 시간이 사라진다.
const TickMs = 33

// TickInterval 은 실제로 기다리는 시간. 게임 시간과 실제 시간을 1:1 로 맞춘다.
const TickInterval = TickMs * time.Millisecond

// SoftReleaseMs 는 소프트드롭을 자동으로 놓기까지 기다리는 시간.
//
// 왜 이런 게 필요한가. 터미널은 키를 **뗀 것을 알려 주지 않는다.**
// 그래서 "누르고 있는 동안 빨리 떨어진다"를 그대로 구현할 수가 없다.
// 대신 마지막으로 ↓ 를 받은 뒤 이만큼 조용하면 놓은 것으로 친다.
// OS 의 키 자동반복 간격(보통 30~50ms)보다 넉넉히 크게 잡아야
// 누르고 있는 도중에 끊기지 않는다.
const SoftReleaseMs = 120

// TickMsg 는 시간이 한 칸 흘렀다는 신호.
//
// 타입이 곧 사건의 이름이다. 안에 시각을 담지 않는 이유는 결정론 때문이다 —
// 기록 도구가 이 메시지를 직접 만들어 넣을 때 시각이 없어야 결과가 재현된다.
type TickMsg struct{}

// Model 은 1인용 게임 화면.
//
// 함정 하나: 모델은 값이지만 g 는 **포인터**다. 그래서 Update 가 모델을 복사해도
// 두 복사본이 같은 판을 가리킨다. 1인용에서는 문제가 없지만(복사본이 하나뿐이므로),
// 7부의 두 자리에서는 이 성질이 버그의 원천이 된다.
type Model struct {
	g    *core.Game
	keys ui.KeyMap

	seed uint32

	w, h int

	timer bool // tea.Tick 을 걸 것인가 (기록·테스트에서는 끈다)
	help  bool
	quit  bool

	softIdle int // 마지막 ↓ 이후 흐른 시간(ms)
	softOn   bool
}

// Option 은 New 에 넘기는 설정. 함수형 옵션은 Go 에서 "기본값이 있는 생성자"를
// 만드는 관례다 — 인자를 늘려도 기존 호출부가 안 깨진다.
type Option func(*Model)

// WithSeed 는 시드를 지정한다. 지정하지 않으면 시계에서 뽑는다.
func WithSeed(seed uint32) Option {
	return func(m *Model) { m.seed = seed }
}

// WithoutTimer 는 tea.Tick 을 걸지 않게 한다.
//
// 기록 도구와 테스트가 이 모드로 돌린다. tea.Tick 은 실제로 잠들기 때문에
// 300프레임을 기록하려면 10초를 기다려야 하고, 무엇보다 결과가 시계에 좌우된다.
// 시간의 출처를 갈아 끼울 수 있게 만들어 두는 것 — 이게 모델을 시험 가능하게 하는 요령이다.
func WithoutTimer() Option {
	return func(m *Model) { m.timer = false }
}

// WithKeys 는 키 배치를 지정한다. 2인용의 왼쪽 자리가 WASD 를 쓴다.
func WithKeys(km ui.KeyMap) Option {
	return func(m *Model) { m.keys = km }
}

// New 는 1인용 모델을 만든다.
func New(opts ...Option) Model {
	m := Model{
		keys:  ui.Arrows,
		seed:  uint32(time.Now().UnixNano()),
		timer: true,
	}
	for _, o := range opts {
		o(&m)
	}
	m.g = core.New(m.seed)
	return m
}

// Tick 은 시간 진행을 예약하는 Cmd.
//
// 04_tick 에서 본 그대로다. 이 함수를 한 군데 모아 두면
// "예약을 빠뜨렸다"를 눈으로 잡기 쉬워진다.
func Tick() tea.Cmd {
	return tea.Tick(TickInterval, func(time.Time) tea.Msg { return TickMsg{} })
}

// Game 은 진행 중인 판. 기록 도구와 테스트가 들여다본다.
func (m Model) Game() *core.Game { return m.g }

// nextSeed 는 다시 시작할 때 쓸 시드를 만든다.
//
// 같은 시드로 다시 시작하면 죽은 판을 그대로 반복하게 된다.
// 시계를 쓰면 기록이 재현되지 않는다. 그래서 LCG 로 한 칸 굴린다 —
// 결정론적이면서 매번 다른 판이 나온다.
func nextSeed(s uint32) uint32 { return s*1664525 + 1013904223 }
