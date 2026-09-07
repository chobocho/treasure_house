package widgets

import (
	"time"

	"treasure/boricha/style"
	"treasure/boricha/tea"
)

// SpinnerSet 은 돌아가는 그림 한 벌과 그 속도다.
//
// 한 벌 안의 그림은 폭이 모두 같아야 한다. 들쭉날쭉하면 돌 때마다 옆의 글자가
// 밀렸다 당겨졌다 해서, 돌아가는 것이 아니라 화면이 흔들리는 것처럼 보인다.
type SpinnerSet struct {
	Frames []string
	FPS    time.Duration
}

// 미리 만들어 둔 그림들.
//
// 점자(U+2800 대) 그림은 폭이 1칸이라 안전하다. 달 이모지는 2칸이므로
// 옆에 글을 붙일 때 그만큼 자리를 비워야 한다 — width 패키지가 그 계산을 해 준다.
var (
	SpinnerLine    = SpinnerSet{[]string{"|", "/", "-", "\\"}, 100 * time.Millisecond}
	SpinnerDot     = SpinnerSet{[]string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}, 80 * time.Millisecond}
	SpinnerMiniDot = SpinnerSet{[]string{"⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"}, 90 * time.Millisecond}
	SpinnerPulse   = SpinnerSet{[]string{"█", "▓", "▒", "░"}, 120 * time.Millisecond}
	SpinnerMoon    = SpinnerSet{[]string{"🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"}, 160 * time.Millisecond}
	SpinnerTea     = SpinnerSet{[]string{"🫖", "🍵"}, 400 * time.Millisecond}
)

// SpinnerTickMsg 는 그림을 한 칸 돌리라는 사건이다.
//
// tag 를 밖으로 내보내지 않는다. 이 사건은 Spinner 가 스스로 만들고 스스로 받는
// 내부 신호라, 앱이 직접 만들 일이 없다.
type SpinnerTickMsg struct{ tag int }

// Spinner 는 "일하는 중" 을 보여 주는 작은 그림이다.
type Spinner struct {
	Set   SpinnerSet
	Style style.Style

	frame int
	// tag 는 울림에 붙이는 번호표다. 아래 Update 의 설명을 볼 것.
	tag int
}

func NewSpinner() Spinner { return Spinner{Set: SpinnerDot} }

// Tick 은 다음 울림을 예약한다. Init 에서 한 번 부르고, 그 뒤로는 Update 가 이어 건다.
func (s Spinner) Tick() tea.Cmd {
	tag := s.tag
	return tea.Tick(s.Set.FPS, func(time.Time) tea.Msg { return SpinnerTickMsg{tag: tag} })
}

// Update 는 울림을 받아 그림을 한 칸 돌리고 다음 울림을 예약한다.
//
// 번호표(tag)가 하는 일. Tick 을 실수로 두 번 걸면 시계가 둘이 되고, 그 둘이 각각
// 자기를 다시 예약하므로 시계가 계속 불어난다(그림은 두 배, 네 배로 빨라진다).
// 울림마다 발행 시점의 번호를 적어 두고 지금 기대하는 번호만 받아들이면,
// 뒤늦게 온 중복은 그 자리에서 조용히 끊긴다.
func (s Spinner) Update(msg tea.Msg) (Spinner, tea.Cmd) {
	m, ok := msg.(SpinnerTickMsg)
	if !ok || m.tag != s.tag {
		return s, nil
	}
	s.frame = (s.frame + 1) % len(s.Set.Frames)
	s.tag++
	return s, s.Tick()
}

func (s Spinner) View() string { return s.Style.Render(s.Set.Frames[s.frame]) }
