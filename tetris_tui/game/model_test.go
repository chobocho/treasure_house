package game

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/core"
	"treasure/tetris_tui/ui"
)

// 모델을 헤드리스로 만든다. 터미널도, 프로그램도, tea.Tick 도 없다.
// 이 파일의 모든 테스트가 이 한 줄로 시작한다 — Bubble Tea 모델이 값이라 가능한 일이다.
func headless(t *testing.T) Model {
	t.Helper()
	m := New(WithSeed(1), WithoutTimer())
	m2, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 40})
	return m2.(Model)
}

func key(name string) tea.KeyPressMsg {
	switch name {
	case "left":
		return tea.KeyPressMsg{Code: tea.KeyLeft}
	case "right":
		return tea.KeyPressMsg{Code: tea.KeyRight}
	case "up":
		return tea.KeyPressMsg{Code: tea.KeyUp}
	case "down":
		return tea.KeyPressMsg{Code: tea.KeyDown}
	case "space":
		return tea.KeyPressMsg{Code: tea.KeySpace}
	case "esc":
		return tea.KeyPressMsg{Code: tea.KeyEscape}
	case "f1":
		return tea.KeyPressMsg{Code: tea.KeyF1}
	case "ctrl+c":
		return tea.KeyPressMsg{Code: 'c', Mod: tea.ModCtrl}
	}
	r := []rune(name)[0]
	return tea.KeyPressMsg{Code: r, Text: name}
}

func TestNewStartsAGame(t *testing.T) {
	m := New(WithSeed(7))
	if m.Game() == nil {
		t.Fatal("판이 없다")
	}
	if m.Game().Stats().State != core.StatePlay {
		t.Errorf("상태가 %d 다", m.Game().Stats().State)
	}
}

// 같은 시드는 같은 판. 기록과 재현이 여기에 달려 있다.
func TestSeedIsHonoured(t *testing.T) {
	a := New(WithSeed(42)).Game().Stats()
	b := New(WithSeed(42)).Game().Stats()
	c := New(WithSeed(43)).Game().Stats()
	if a.Piece != b.Piece {
		t.Error("같은 시드인데 첫 조각이 다르다")
	}
	if a == c {
		t.Skip("시드 42 와 43 의 첫 상태가 우연히 같다")
	}
}

// 타이머를 끄면 Init 이 Cmd 를 안 만든다. 기록 도구가 이 상태로 돌린다.
func TestWithoutTimerSchedulesNothing(t *testing.T) {
	if cmd := New(WithoutTimer()).Init(); cmd != nil {
		t.Error("타이머를 껐는데 Cmd 가 나왔다")
	}
	if cmd := New().Init(); cmd == nil {
		t.Fatal("타이머가 켜졌는데 Cmd 가 없다")
	}
}

// 04_tick 에서 배운 것: 틱을 받으면 다음 틱을 다시 예약해야 한다.
func TestTickReschedulesItself(t *testing.T) {
	m := New(WithSeed(1))
	_, cmd := m.Update(TickMsg{})
	if cmd == nil {
		t.Fatal("틱을 받고 다음 틱을 예약하지 않았다 — 중력이 한 번 뛰고 멈춘다")
	}
	if _, ok := cmd().(TickMsg); !ok {
		t.Errorf("다시 예약한 게 TickMsg 가 아니라 %T", cmd())
	}
}

// 틱은 코어의 시간을 TickMs 만큼 진행시킨다.
func TestTickAdvancesGameTime(t *testing.T) {
	m := headless(t)
	before := m.Game().Stats().Elapsed
	m2, _ := m.Update(TickMsg{})
	if got := m2.(Model).Game().Stats().Elapsed; got != before+TickMs {
		t.Errorf("경과 시간이 %d — %d 를 기대했다", got, before+TickMs)
	}
}

func TestMoveKeys(t *testing.T) {
	m := headless(t)
	x0 := m.Game().Stats().X
	m2, _ := m.Update(key("left"))
	if got := m2.(Model).Game().Stats().X; got != x0-1 {
		t.Errorf("← 를 눌렀는데 x 가 %d — %d 를 기대했다", got, x0-1)
	}
	m3, _ := m2.Update(key("right"))
	if got := m3.(Model).Game().Stats().X; got != x0 {
		t.Errorf("→ 를 눌렀는데 x 가 %d 다", got)
	}
}

// 터미널은 키를 **뗀 것**을 알려 주지 않는다. 그래서 좌우는 누르는 즉시 놓아
// 코어의 DAS 자동반복이 켜지지 않게 한다. 켜 두면 한 번 누른 뒤 조각이
// 혼자 벽까지 미끄러져 간다.
func TestLeftRightDoNotStartAutoRepeat(t *testing.T) {
	m := headless(t)
	m2, _ := m.Update(key("left"))
	x := m2.(Model).Game().Stats().X
	for i := 0; i < 20; i++ { // 660ms — DAS(170ms) 가 켜졌다면 벽까지 갔을 시간
		m2, _ = m2.Update(TickMsg{})
	}
	if got := m2.(Model).Game().Stats().X; got != x {
		t.Errorf("키를 한 번 눌렀는데 조각이 %d 에서 %d 로 혼자 움직였다", x, got)
	}
}

// 소프트드롭은 반대다. 누르는 즉시 놓아 버리면 아무 일도 안 일어나므로,
// "잠깐 눌린 채로 두었다가 시간이 지나면 놓는" 타임아웃을 쓴다.
func TestSoftDropFallsThenReleases(t *testing.T) {
	m := headless(t)
	y0 := m.Game().Stats().Y
	m2, _ := m.Update(key("down"))
	m2, _ = m2.Update(TickMsg{})
	m2, _ = m2.Update(TickMsg{})
	if got := m2.(Model).Game().Stats().Y; got <= y0 {
		t.Errorf("소프트드롭 중인데 y 가 %d → %d 다", y0, got)
	}
	// 더 이상 안 누르면 얼마 뒤 저절로 놓여야 한다.
	y1 := m2.(Model).Game().Stats().Y
	for i := 0; i < SoftReleaseMs/TickMs+2; i++ {
		m2, _ = m2.Update(TickMsg{})
	}
	y2 := m2.(Model).Game().Stats().Y
	m3, _ := m2.Update(TickMsg{})
	if got := m3.(Model).Game().Stats().Y; got != y2 {
		t.Errorf("소프트드롭이 안 놓였다 — y 가 %d 에서 %d 로 계속 떨어진다", y2, got)
	}
	_ = y1
}

func TestHardDropLocks(t *testing.T) {
	m := headless(t)
	pieces := m.Game().Stats().Pieces
	m2, _ := m.Update(key("space"))
	if got := m2.(Model).Game().Stats().Pieces; got != pieces+1 {
		t.Errorf("하드드롭 뒤 조각 수가 %d 다", got)
	}
}

func TestRotateAndHold(t *testing.T) {
	m := headless(t)
	first := m.Game().CurrentPiece()
	m2, _ := m.Update(key("c"))
	if p, _ := m2.(Model).Game().Hold(); p != first {
		t.Errorf("홀드에 %d 가 들어갔다 — %d 여야 한다", p, first)
	}
	m3, _ := m2.Update(key("up"))
	if m3.(Model).Game().Stats().Rot == 0 && m3.(Model).Game().Stats().Piece != core.PieceO {
		t.Error("↑ 를 눌렀는데 회전이 안 됐다")
	}
}

// 일시정지 중에는 틱이 와도 시간이 안 흐른다.
func TestPauseStopsTime(t *testing.T) {
	m := headless(t)
	m2, _ := m.Update(key("p"))
	if m2.(Model).Game().Stats().State != core.StatePause {
		t.Fatal("일시정지가 안 됐다")
	}
	el := m2.(Model).Game().Stats().Elapsed
	m3, _ := m2.Update(TickMsg{})
	if got := m3.(Model).Game().Stats().Elapsed; got != el {
		t.Errorf("일시정지 중에 시간이 %d → %d 로 흘렀다", el, got)
	}
	m4, _ := m3.Update(key("p"))
	if m4.(Model).Game().Stats().State != core.StatePlay {
		t.Error("일시정지가 안 풀렸다")
	}
}

// 일시정지 중에도 틱 사슬은 이어져야 한다. 안 그러면 정지를 푼 뒤 시간이 안 흐른다.
func TestPausedTickStillRescheduled(t *testing.T) {
	m := New(WithSeed(1))
	m2, _ := m.Update(key("p"))
	_, cmd := m2.Update(TickMsg{})
	if cmd == nil {
		t.Fatal("일시정지 중에 틱 사슬이 끊겼다 — 정지를 풀어도 시간이 안 흐른다")
	}
}

func TestQuitKeys(t *testing.T) {
	for _, k := range []string{"esc", "ctrl+c"} {
		_, cmd := headless(t).Update(key(k))
		if cmd == nil {
			t.Fatalf("%s 가 무시됐다", k)
		}
		if _, ok := cmd().(tea.QuitMsg); !ok {
			t.Errorf("%s 가 Quit 이 아니라 %T 를 만들었다", k, cmd())
		}
	}
}

// r 은 새 판을 시작한다. 시드가 바뀌므로 같은 판이 반복되지 않는다.
func TestRestart(t *testing.T) {
	m := headless(t)
	m2, _ := m.Update(key("space"))
	m2, _ = m2.Update(key("space"))
	if m2.(Model).Game().Stats().Pieces < 3 {
		t.Fatal("조각이 안 놓였다")
	}
	m3, _ := m2.Update(key("r"))
	s := m3.(Model).Game().Stats()
	if s.Pieces != 1 || s.Score != 0 {
		t.Errorf("다시 시작이 덜 됐다: 조각 %d, 점수 %d", s.Pieces, s.Score)
	}
	if !m3.(Model).Game().Board().Empty() {
		t.Error("판이 안 비었다")
	}
}

func TestRestartChangesTheSeed(t *testing.T) {
	m := headless(t)
	first := m.Game().Next(5)
	m2, _ := m.Update(key("r"))
	second := m2.(Model).Game().Next(5)
	same := true
	for i := range first {
		if first[i] != second[i] {
			same = false
			break
		}
	}
	if same {
		t.Error("다시 시작했는데 조각 순서가 똑같다 — 시드가 안 바뀌었다")
	}
}

func TestHelpToggle(t *testing.T) {
	m := headless(t)
	if strings.Contains(m.View().Content, ui.Wasd.Name) {
		t.Skip("이 화면에는 WASD 이름이 원래 있다")
	}
	m2, _ := m.Update(key("f1"))
	if !strings.Contains(m2.(Model).View().Content, "홀드") {
		t.Errorf("F1 도움말에 조작 설명이 없다:\n%s", m2.(Model).View().Content)
	}
	m3, _ := m2.Update(key("f1"))
	if m3.(Model).View().Content == m2.(Model).View().Content {
		t.Error("F1 을 다시 눌렀는데 화면이 그대로다")
	}
}

// 게임 오버 뒤에는 조작이 안 먹지만 r 로는 다시 시작할 수 있어야 한다.
func TestGameOverThenRestart(t *testing.T) {
	m := headless(t)
	m.Game().Paint(rep("##########", core.H))
	m.Game().SetPiece(core.PieceO)
	if m.Game().Stats().State != core.StateOver {
		t.Fatal("게임 오버 상태를 못 만들었다")
	}
	if !strings.Contains(m.View().Content, "게임 오버") {
		t.Errorf("화면에 게임 오버 표시가 없다:\n%s", m.View().Content)
	}
	m2, _ := m.Update(key("r"))
	if m2.(Model).Game().Stats().State != core.StatePlay {
		t.Error("r 로 다시 시작이 안 된다")
	}
}

func rep(row string, n int) []string {
	out := make([]string, n)
	for i := range out {
		out[i] = row
	}
	return out
}

// ── 화면 ──────────────────────────────────────────────────────────────

// 05_window 의 교훈: 첫 WindowSizeMsg 전에도 View 가 불린다.
func TestViewBeforeAnySize(t *testing.T) {
	got := New(WithSeed(1)).View().Content
	if got == "" {
		t.Error("크기를 모를 때 화면이 비었다")
	}
}

func TestTooSmallTellsTheUserWhatIsNeeded(t *testing.T) {
	minW, minH := ui.MinSize(1)
	m := New(WithSeed(1))
	m2, _ := m.Update(tea.WindowSizeMsg{Width: minW - 1, Height: minH})
	got := m2.(Model).View().Content
	if !strings.Contains(got, "터미널") {
		t.Errorf("안내가 없다:\n%s", got)
	}
	for _, want := range []string{itoa(minW), itoa(minH), itoa(minW - 1)} {
		if !strings.Contains(got, want) {
			t.Errorf("안내에 %q 가 없다:\n%s", want, got)
		}
	}
}

func TestExactMinimumSizeIsEnough(t *testing.T) {
	minW, minH := ui.MinSize(1)
	m := New(WithSeed(1))
	m2, _ := m.Update(tea.WindowSizeMsg{Width: minW, Height: minH})
	if strings.Contains(m2.(Model).View().Content, "터미널을 키워") {
		t.Error("딱 최소 크기인데 안내가 떴다")
	}
}

// 화면이 터미널보다 크면 스크롤이 생겨 이전 프레임이 지저분하게 남는다.
func TestViewNeverOverflowsTheTerminal(t *testing.T) {
	for _, sz := range []tea.WindowSizeMsg{{Width: 36, Height: 24}, {Width: 80, Height: 24}, {Width: 200, Height: 60}} {
		m := New(WithSeed(1))
		m2, _ := m.Update(sz)
		got := m2.(Model).View().Content
		w, h := lipgloss.Size(got)
		if w > sz.Width || h > sz.Height {
			t.Errorf("%d×%d 터미널에 %d×%d 화면을 그렸다", sz.Width, sz.Height, w, h)
		}
	}
}

func TestViewShowsBoardAndPanel(t *testing.T) {
	got := headless(t).View().Content
	for _, want := range []string{"다음", "홀드", "점수", "레벨"} {
		if !strings.Contains(got, want) {
			t.Errorf("화면에 %q 가 없다", want)
		}
	}
	if !strings.Contains(got, ui.Cell) {
		t.Error("떨어지는 조각이 안 보인다")
	}
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var b []byte
	for n > 0 {
		b = append([]byte{byte('0' + n%10)}, b...)
		n /= 10
	}
	if neg {
		return "-" + string(b)
	}
	return string(b)
}
