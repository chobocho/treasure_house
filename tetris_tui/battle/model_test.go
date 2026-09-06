package battle

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/ai"
	"treasure/tetris_tui/core"
	"treasure/tetris_tui/ui"
)

func headless(t *testing.T, mode Mode, opts ...Option) Model {
	t.Helper()
	opts = append([]Option{WithSeed(1), WithoutTimer()}, opts...)
	m := New(mode, opts...)
	m2, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 40})
	return m2.(Model)
}

func key(name string) tea.KeyPressMsg {
	switch name {
	case "left":
		return tea.KeyPressMsg{Code: tea.KeyLeft}
	case "right":
		return tea.KeyPressMsg{Code: tea.KeyRight}
	case "down":
		return tea.KeyPressMsg{Code: tea.KeyDown}
	case "space":
		return tea.KeyPressMsg{Code: tea.KeySpace}
	case "enter":
		return tea.KeyPressMsg{Code: tea.KeyEnter}
	case "esc":
		return tea.KeyPressMsg{Code: tea.KeyEscape}
	}
	r := []rune(name)[0]
	return tea.KeyPressMsg{Code: r, Text: name}
}

// 모드마다 누가 어느 자리에 앉는지가 다르다. 규칙과 화면은 완전히 같다.
func TestWhoSitsWhere(t *testing.T) {
	cases := []struct {
		mode        Mode
		leftHuman   bool
		rightHuman  bool
		leftDriver  bool
		rightDriver bool
	}{
		{Local2P, true, true, false, false},
		{VsAI, true, false, false, true},
		{AIvsAI, false, false, true, true},
	}
	for _, c := range cases {
		m := headless(t, c.mode)
		if (m.Driver(Left) != nil) != c.leftDriver {
			t.Errorf("모드 %d: 왼쪽 드라이버 유무가 틀렸다", c.mode)
		}
		if (m.Driver(Right) != nil) != c.rightDriver {
			t.Errorf("모드 %d: 오른쪽 드라이버 유무가 틀렸다", c.mode)
		}
	}
}

// 2인용은 두 자리가 서로 다른 키를 쓴다. 한 키가 양쪽을 움직이면 게임이 안 된다.
func TestLocal2PUsesTwoKeyMaps(t *testing.T) {
	m := headless(t, Local2P)
	lx := m.Match().Game(Left).Stats().X
	rx := m.Match().Game(Right).Stats().X

	m2, _ := m.Update(key("a")) // 왼쪽 자리의 왼쪽
	if got := m2.(Model).Match().Game(Left).Stats().X; got != lx-1 {
		t.Errorf("a 를 눌렀는데 왼쪽 x 가 %d 다", got)
	}
	if got := m2.(Model).Match().Game(Right).Stats().X; got != rx {
		t.Errorf("a 를 눌렀는데 오른쪽도 %d 로 움직였다", got)
	}

	m3, _ := m2.Update(key("left")) // 오른쪽 자리의 왼쪽
	if got := m3.(Model).Match().Game(Right).Stats().X; got != rx-1 {
		t.Errorf("← 를 눌렀는데 오른쪽 x 가 %d 다", got)
	}
	if got := m3.(Model).Match().Game(Left).Stats().X; got != lx-1 {
		t.Errorf("← 를 눌렀는데 왼쪽이 %d 로 또 움직였다", got)
	}
}

// AI 자리에는 사람의 키가 안 먹는다.
func TestAISeatIgnoresKeys(t *testing.T) {
	m := headless(t, VsAI)
	rightX := m.Match().Game(Right).Stats().X
	leftX := m.Match().Game(Left).Stats().X

	m2, _ := m.Update(key("left"))
	if got := m2.(Model).Match().Game(Right).Stats().X; got != rightX {
		t.Errorf("AI 자리가 키에 반응했다: %d → %d", rightX, got)
	}
	if got := m2.(Model).Match().Game(Left).Stats().X; got != leftX-1 {
		t.Errorf("사람 자리가 ← 에 반응하지 않았다: %d → %d", leftX, got)
	}
}

// 이 파일에서 실제로 밟은 함정. **모델은 값이지만 판은 포인터다.**
//
// Update 가 모델을 복사해도 두 복사본은 같은 *core.Game 을 가리킨다.
// 그래서 "업데이트 전의 모델"에서 판 상태를 읽으면 업데이트 **후**의 값이 나온다.
// 예전 값을 비교하려면 Update 를 부르기 전에 숫자를 따로 붙잡아 둬야 한다.
func TestTheModelIsAValueButTheGameIsShared(t *testing.T) {
	m := headless(t, Local2P)
	before := m.Match().Game(Left).Stats().X // 숫자를 미리 붙잡는다

	m2, _ := m.Update(key("a"))

	if m.Match() != m2.(Model).Match() {
		t.Fatal("이 테스트의 전제가 깨졌다 — 두 모델이 다른 대전을 가리킨다")
	}
	if got := m.Match().Game(Left).Stats().X; got == before {
		t.Error("옛 모델에서 읽었는데 옛 값이 나왔다 — 판이 공유되지 않는다는 뜻이다")
	}
	if got := m2.(Model).Match().Game(Left).Stats().X; got != before-1 {
		t.Errorf("새 모델의 x 가 %d — %d 를 기대했다", got, before-1)
	}
}

// §5.3 의 핵심. 탐색은 Update 안에서 돌지 않는다 —
// 드라이버가 "지금 생각할 때"라고 하면 모델은 **Cmd** 를 돌려준다.
func TestSearchRunsInACommandNotInUpdate(t *testing.T) {
	m := headless(t, VsAI)
	var cmd tea.Cmd
	var mm tea.Model = m
	for i := 0; i < 200; i++ {
		mm, cmd = mm.Update(TickMsg{})
		if cmd != nil {
			break
		}
	}
	if cmd == nil {
		t.Fatal("AI 가 탐색 Cmd 를 한 번도 안 띄웠다")
	}
	msg := cmd()
	batch, ok := msg.(tea.BatchMsg)
	if ok {
		if len(batch) == 0 {
			t.Fatal("빈 Batch 가 나왔다")
		}
		msg = batch[0]()
	}
	mv, ok := msg.(AIMoveMsg)
	if !ok {
		t.Fatalf("AIMoveMsg 가 아니라 %T 가 나왔다", msg)
	}
	if mv.Seat != Right {
		t.Errorf("결과가 %d번 자리 것이다 — 오른쪽이어야 한다", mv.Seat)
	}
	if !mv.OK {
		t.Error("빈 판인데 둘 수 없다고 한다")
	}
}

// 탐색 Cmd 는 다른 고루틴에서 돈다. 진행 중인 판을 들여다보면 자료 경쟁이다.
// 그래서 사본(ai.Snapshot)만 넘긴다 — Cmd 를 실행해도 판이 안 바뀌어야 한다.
func TestSearchCommandDoesNotTouchTheBoard(t *testing.T) {
	m := headless(t, VsAI)
	var cmd tea.Cmd
	var mm tea.Model = m
	for i := 0; i < 200; i++ {
		mm, cmd = mm.Update(TickMsg{})
		if cmd != nil {
			break
		}
	}
	if cmd == nil {
		t.Fatal("탐색 Cmd 가 없다")
	}
	g := mm.(Model).Match().Game(Right)
	before := core.BoardHash(g.Board())
	stats := g.Stats()
	cmd()
	if core.BoardHash(g.Board()) != before {
		t.Error("탐색 Cmd 가 판을 바꿨다")
	}
	if g.Stats() != stats {
		t.Error("탐색 Cmd 가 stats 를 바꿨다")
	}
}

// 결과가 오면 드라이버가 목표를 세우고, 그 뒤로 키를 눌러 조각을 옮긴다.
func TestAIMoveMsgMakesTheAIPlay(t *testing.T) {
	m := headless(t, VsAI)
	var mm tea.Model = m
	var cmd tea.Cmd
	for i := 0; i < 200; i++ {
		mm, cmd = mm.Update(TickMsg{})
		if cmd != nil {
			break
		}
	}
	if cmd == nil {
		t.Fatal("탐색 Cmd 가 없다")
	}
	msg := cmd()
	if batch, ok := msg.(tea.BatchMsg); ok {
		msg = batch[0]()
	}
	mm, _ = mm.Update(msg)

	g := mm.(Model).Match().Game(Right)
	pieces := g.Stats().Pieces
	for i := 0; i < 300; i++ {
		mm, _ = mm.Update(TickMsg{})
		if mm.(Model).Match().Game(Right).Stats().Pieces != pieces {
			return // 조각이 하나 굳었다
		}
	}
	t.Error("목표를 받았는데 AI 가 조각을 못 놨다")
}

// AI vs AI 는 사람 없이 한 판이 끝까지 간다.
// 여기서는 짧게 — 두 자리 모두 조각을 놓는지만 본다.
func TestAIvsAIBothSeatsPlay(t *testing.T) {
	m := headless(t, AIvsAI, WithLevel("max"))
	mm := runMatch(t, m, 600)
	for _, s := range []Seat{Left, Right} {
		if got := mm.Match().Game(s).Stats().Pieces; got < 3 {
			t.Errorf("%d번 자리가 조각을 %d개만 놨다", s, got)
		}
	}
}

// runMatch 는 Cmd 를 직접 실행해 가며 틱을 n 번 돌린다.
// tea.Program 없이 모델을 굴리는 방법 — 8부의 테스트 전략이 이것이다.
func runMatch(t *testing.T, m Model, ticks int) Model {
	t.Helper()
	var mm tea.Model = m
	for i := 0; i < ticks; i++ {
		var cmd tea.Cmd
		mm, cmd = mm.Update(TickMsg{})
		for _, msg := range drain(cmd) {
			mm, _ = mm.Update(msg)
		}
	}
	return mm.(Model)
}

// drain 은 Cmd 가 만드는 메시지를 전부 꺼낸다. Batch 는 펼친다.
func drain(cmd tea.Cmd) []tea.Msg {
	if cmd == nil {
		return nil
	}
	msg := cmd()
	if batch, ok := msg.(tea.BatchMsg); ok {
		var out []tea.Msg
		for _, c := range batch {
			out = append(out, drain(c)...)
		}
		return out
	}
	if _, ok := msg.(TickMsg); ok {
		return nil // 틱은 우리가 직접 넣는다
	}
	return []tea.Msg{msg}
}

// 공격이 실제로 상대에게 간다. 왼쪽에 테트리스 자리를 심어 두고 확인한다.
func TestAttackReachesTheOpponent(t *testing.T) {
	m := headless(t, Local2P)
	g := m.Match().Game(Left)
	g.Paint(append(rep(".#########", 4), "#########."))
	g.SetPiece(core.PieceI)
	mm := m
	for _, k := range []string{"w", "a", "a", "a", "a", "a", "a", "f"} {
		x, _ := mm.Update(key(k))
		mm = x.(Model)
	}
	if got := g.Stats().Clear; got != 4 {
		t.Fatalf("테트리스가 안 났다 — 지운 줄 %d:\n%v", got, g.Board().Rows()[core.Vis-6:])
	}
	m2, _ := mm.Update(TickMsg{})
	if got := m2.(Model).Match().Game(Right).Stats().Pending; got != 4 {
		t.Errorf("상대의 대기줄이 %d — 4 여야 한다", got)
	}
}

// 라운드가 끝나면 Enter 로 다음 라운드. 대전이 끝났으면 처음부터 다시.
func TestEnterStartsTheNextRound(t *testing.T) {
	m := headless(t, Local2P)
	m.Match().Game(Left).Paint(rep("##########", core.H))
	m.Match().Game(Left).SetPiece(core.PieceO)
	m2, _ := m.Update(TickMsg{})
	if _, _, over := m2.(Model).Match().RoundOver(); !over {
		t.Fatal("라운드가 안 끝났다")
	}
	m3, _ := m2.Update(key("enter"))
	if m3.(Model).Match().Round() != 2 {
		t.Errorf("Enter 를 눌렀는데 라운드가 %d 다", m3.(Model).Match().Round())
	}
	if _, _, over := m3.(Model).Match().RoundOver(); over {
		t.Error("새 라운드가 끝난 상태다")
	}
}

// 라운드가 끝난 뒤에도 드라이버는 새 라운드에서 처음부터 시작해야 한다.
func TestNextRoundResetsTheDrivers(t *testing.T) {
	m := headless(t, VsAI)
	m.Driver(Right).SetTarget(ai.Move{Rot: 1, X: 2}, true)
	m.Match().Game(Left).Paint(rep("##########", core.H))
	m.Match().Game(Left).SetPiece(core.PieceO)
	m2, _ := m.Update(TickMsg{})
	m3, _ := m2.Update(key("enter"))
	if m3.(Model).Driver(Right).Thinking() {
		t.Error("새 라운드인데 드라이버가 생각 중이다")
	}
}

func TestRestartResetsTheMatch(t *testing.T) {
	m := headless(t, Local2P)
	m.Match().Game(Left).Paint(rep("##########", core.H))
	m.Match().Game(Left).SetPiece(core.PieceO)
	m2, _ := m.Update(TickMsg{})
	m3, _ := m2.Update(key("r"))
	mm := m3.(Model)
	if mm.Match().Wins(Right) != 0 || mm.Match().Round() != 1 {
		t.Errorf("다시 시작이 덜 됐다: %d승, 라운드 %d", mm.Match().Wins(Right), mm.Match().Round())
	}
}

func TestQuitKey(t *testing.T) {
	_, cmd := headless(t, Local2P).Update(key("esc"))
	if cmd == nil {
		t.Fatal("esc 가 무시됐다")
	}
	if _, ok := cmd().(tea.QuitMsg); !ok {
		t.Errorf("Quit 이 아니라 %T", cmd())
	}
}

func TestPauseStopsBothSeats(t *testing.T) {
	m := headless(t, Local2P)
	m2, _ := m.Update(key("p"))
	for _, s := range []Seat{Left, Right} {
		if got := m2.(Model).Match().Game(s).Stats().State; got != core.StatePause {
			t.Errorf("%d번 자리의 상태가 %d 다", s, got)
		}
	}
	el := m2.(Model).Match().Game(Left).Stats().Elapsed
	m3, _ := m2.Update(TickMsg{})
	if got := m3.(Model).Match().Game(Left).Stats().Elapsed; got != el {
		t.Errorf("일시정지 중에 시간이 흘렀다: %d → %d", el, got)
	}
}

// 틱은 늘 다시 예약돼야 한다 — AI 의 Cmd 와 함께 Batch 로 나간다.
func TestTickIsAlwaysRescheduled(t *testing.T) {
	m := New(VsAI, WithSeed(1))
	m2, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 40})
	var mm tea.Model = m2
	for i := 0; i < 60; i++ {
		var cmd tea.Cmd
		mm, cmd = mm.Update(TickMsg{})
		if cmd == nil {
			t.Fatalf("%d번째 틱에서 사슬이 끊겼다", i)
		}
	}
}

// ── 화면 ──────────────────────────────────────────────────────────────

func TestViewShowsBothSeats(t *testing.T) {
	got := headless(t, Local2P).View().Content
	for _, want := range []string{"1P", "2P", "다음", "점수"} {
		if !strings.Contains(got, want) {
			t.Errorf("화면에 %q 가 없다", want)
		}
	}
	if strings.Count(got, "다음") != 2 {
		t.Errorf("패널이 둘이 아니다:\n%s", got)
	}
}

func TestVsAIShowsTheLevel(t *testing.T) {
	got := headless(t, VsAI, WithLevel("easy")).View().Content
	if !strings.Contains(got, "쉬움") {
		t.Errorf("난이도 이름이 안 보인다:\n%s", got)
	}
}

func TestViewNeverOverflows(t *testing.T) {
	minW, minH := ui.MinSize(2)
	for _, sz := range []tea.WindowSizeMsg{{Width: minW, Height: minH}, {Width: 100, Height: 40}} {
		m := New(Local2P, WithSeed(1), WithoutTimer())
		m2, _ := m.Update(sz)
		got := m2.(Model).View().Content
		w, h := lipgloss.Size(got)
		if w > sz.Width || h > sz.Height {
			t.Errorf("%d×%d 터미널에 %d×%d 화면을 그렸다", sz.Width, sz.Height, w, h)
		}
	}
}

func TestTooSmallForTwoSeats(t *testing.T) {
	minW, minH := ui.MinSize(2)
	m := New(Local2P, WithSeed(1), WithoutTimer())
	m2, _ := m.Update(tea.WindowSizeMsg{Width: minW - 1, Height: minH})
	got := m2.(Model).View().Content
	if !strings.Contains(got, "터미널") {
		t.Errorf("안내가 없다:\n%s", got)
	}
}

func TestRoundResultIsShown(t *testing.T) {
	m := headless(t, Local2P)
	m.Match().Game(Left).Paint(rep("##########", core.H))
	m.Match().Game(Left).SetPiece(core.PieceO)
	m2, _ := m.Update(TickMsg{})
	got := m2.(Model).View().Content
	if !strings.Contains(got, "Enter") {
		t.Errorf("다음 라운드 안내가 없다:\n%s", got)
	}
}
