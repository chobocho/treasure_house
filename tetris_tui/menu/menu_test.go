package menu

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/battle"
	"treasure/tetris_tui/game"
)

func key(name string) tea.KeyPressMsg {
	switch name {
	case "up":
		return tea.KeyPressMsg{Code: tea.KeyUp}
	case "down":
		return tea.KeyPressMsg{Code: tea.KeyDown}
	case "enter":
		return tea.KeyPressMsg{Code: tea.KeyEnter}
	case "esc":
		return tea.KeyPressMsg{Code: tea.KeyEscape}
	}
	r := []rune(name)[0]
	return tea.KeyPressMsg{Code: r, Text: name}
}

func sized(t *testing.T) Model {
	t.Helper()
	m := New(1, "hard", 3)
	m2, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 40})
	return m2.(Model)
}

// 메뉴에 보이는 모드와 이름으로 만들 수 있는 모드가 같아야 한다.
// 어긋나면 메뉴에는 있는데 골라도 안 켜지는 줄이 생긴다.
func TestEveryEntryCanBeBuilt(t *testing.T) {
	for _, e := range Entries() {
		if _, ok := Build(e.Mode, 1, "hard", 3); !ok {
			t.Errorf("메뉴에 있는 모드 %q 를 만들 수 없다", e.Mode)
		}
		if e.Label == "" || e.Desc == "" {
			t.Errorf("모드 %q 의 이름이나 설명이 비었다", e.Mode)
		}
	}
	if len(Entries()) != len(ModeNames()) {
		t.Errorf("메뉴 %d줄, 이름 %d개 — 같아야 한다", len(Entries()), len(ModeNames()))
	}
}

func TestBuildReturnsTheRightScreen(t *testing.T) {
	cases := map[string]any{
		"1p":    game.Model{},
		"2p":    battle.Model{},
		"ai":    battle.Model{},
		"aivai": battle.Model{},
	}
	for mode, want := range cases {
		got, ok := Build(mode, 1, "hard", 3)
		if !ok {
			t.Fatalf("%q 를 못 만들었다", mode)
		}
		if _, isGame := got.(game.Model); isGame {
			if _, wantGame := want.(game.Model); !wantGame {
				t.Errorf("%q 가 1인용 화면을 냈다", mode)
			}
			continue
		}
		if _, isBattle := got.(battle.Model); !isBattle {
			t.Errorf("%q 가 %T 를 냈다", mode, got)
		}
	}
}

func TestBuildRejectsUnknownMode(t *testing.T) {
	if _, ok := Build("없는모드", 1, "hard", 3); ok {
		t.Error("없는 모드가 만들어졌다")
	}
}

// 고른 모드의 설정이 실제로 전달돼야 한다.
func TestLevelAndBestOfArePassedThrough(t *testing.T) {
	got, ok := Build("ai", 1, "easy", 5)
	if !ok {
		t.Fatal("ai 모드를 못 만들었다")
	}
	b := got.(battle.Model)
	if b.Driver(battle.Right).Level().Name != "easy" {
		t.Errorf("난이도가 %q 다", b.Driver(battle.Right).Level().Name)
	}
	if b.Match().BestOf() != 5 {
		t.Errorf("판수가 %d 다", b.Match().BestOf())
	}
}

func TestArrowsMoveTheSelection(t *testing.T) {
	m := sized(t)
	n := len(Entries())
	m2, _ := m.Update(key("down"))
	if m2.(Model).Selected() != 1 {
		t.Errorf("↓ 뒤 선택이 %d 다", m2.(Model).Selected())
	}
	// 위로 한 번 더 올라가면 맨 아래로 돌아온다
	m3, _ := m.Update(key("up"))
	if got := m3.(Model).Selected(); got != n-1 {
		t.Errorf("맨 위에서 ↑ 를 눌렀는데 %d 다 — %d 를 기대했다", got, n-1)
	}
	// 맨 아래에서 아래로 가면 맨 위로
	m4, _ := m3.Update(key("down"))
	if got := m4.(Model).Selected(); got != 0 {
		t.Errorf("맨 아래에서 ↓ 를 눌렀는데 %d 다", got)
	}
}

// Enter 를 누르면 고른 화면으로 바뀐다. 새 모델의 Init 도 함께 돌아야
// 그 화면의 첫 틱이 예약된다 — 안 그러면 시간이 안 흐른다.
func TestEnterSwitchesToTheChosenScreen(t *testing.T) {
	m := sized(t)
	m2, cmd := m.Update(key("enter"))
	if _, still := m2.(Model); still {
		t.Fatal("Enter 를 눌렀는데 메뉴 그대로다")
	}
	if _, isGame := m2.(game.Model); !isGame {
		t.Errorf("첫 항목이 1인용이 아니라 %T 를 냈다", m2)
	}
	if cmd == nil {
		t.Error("새 화면의 Init 이 안 불렸다 — 시간이 안 흐른다")
	}
}

// 숫자 키로도 고를 수 있어야 한다. 메뉴에 그렇게 적혀 있기 때문이다.
func TestNumberKeysPickDirectly(t *testing.T) {
	m := sized(t)
	m2, _ := m.Update(key("3"))
	if _, still := m2.(Model); still {
		t.Fatal("3 을 눌렀는데 메뉴 그대로다")
	}
	if _, isBattle := m2.(battle.Model); !isBattle {
		t.Errorf("세 번째 항목이 대전이 아니라 %T 를 냈다", m2)
	}
}

func TestOutOfRangeNumberIsIgnored(t *testing.T) {
	m := sized(t)
	m2, _ := m.Update(key("9"))
	if _, still := m2.(Model); !still {
		t.Error("범위 밖 숫자에 화면이 바뀌었다")
	}
}

func TestQuitKeys(t *testing.T) {
	for _, k := range []string{"esc", "q"} {
		_, cmd := sized(t).Update(key(k))
		if cmd == nil {
			t.Fatalf("%s 가 무시됐다", k)
		}
		if _, ok := cmd().(tea.QuitMsg); !ok {
			t.Errorf("%s 가 Quit 이 아니라 %T", k, cmd())
		}
	}
}

func TestViewListsEveryMode(t *testing.T) {
	got := sized(t).View().Content
	for _, e := range Entries() {
		if !strings.Contains(got, e.Label) {
			t.Errorf("메뉴에 %q 가 없다:\n%s", e.Label, got)
		}
	}
}

func TestViewFitsTheTerminal(t *testing.T) {
	for _, sz := range []tea.WindowSizeMsg{{Width: 40, Height: 12}, {Width: 100, Height: 40}} {
		m := New(1, "hard", 3)
		m2, _ := m.Update(sz)
		got := m2.(Model).View().Content
		w, h := lipgloss.Size(got)
		if w > sz.Width || h > sz.Height {
			t.Errorf("%d×%d 터미널에 %d×%d 화면을 그렸다", sz.Width, sz.Height, w, h)
		}
	}
}

func TestViewBeforeAnySize(t *testing.T) {
	if New(1, "hard", 3).View().Content == "" {
		t.Error("크기를 모를 때 화면이 비었다")
	}
}

// 라벨에 한글이 섞이면 %-18s 는 룬 수로 채워서 설명 열이 줄마다 어긋난다.
// 네 줄의 설명이 같은 칸에서 시작해야 한다 — 칸 수는 lipgloss.Width 로 센다(색 이스케이프 제외).
func TestViewDescriptionColumnIsAligned(t *testing.T) {
	got := New(1, "hard", 3).View().Content // 이스케이프는 lipgloss.Width 가 알아서 뺀다
	col := -1
	for _, e := range Entries() {
		for _, line := range strings.Split(got, "\n") {
			at := strings.Index(line, e.Desc)
			if at < 0 {
				continue
			}
			c := lipgloss.Width(line[:at])
			if col < 0 {
				col = c
			} else if c != col {
				t.Errorf("%q 의 설명이 %d칸에서 시작한다 (첫 줄은 %d칸):\n%s", e.Label, c, col, got)
			}
		}
	}
	if col < 0 {
		t.Fatal("설명을 하나도 못 찾았다")
	}
}
