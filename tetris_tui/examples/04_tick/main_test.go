package main

import (
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
)

func rune2key(r rune) tea.KeyPressMsg {
	return tea.KeyPressMsg{Code: r, Text: string(r)}
}

// Init 이 첫 틱을 예약해야 시계가 움직이기 시작한다.
func TestInitSchedulesFirstTick(t *testing.T) {
	cmd := model{running: true}.Init()
	if cmd == nil {
		t.Fatal("Init 이 틱을 예약하지 않았다")
	}
	if _, ok := cmd().(tickMsg); !ok {
		t.Errorf("tickMsg 가 아니라 %T", cmd())
	}
}

// 이 예제의 핵심이자 초보자가 가장 많이 밟는 함정:
// tea.Tick 은 *한 번만* 보낸다. 받은 자리에서 다시 예약하지 않으면 시계가 한 번 뛰고 멈춘다.
func TestTickReschedulesItself(t *testing.T) {
	m2, cmd := model{running: true}.Update(tickMsg(time.Now()))
	if cmd == nil {
		t.Fatal("틱을 받고 다음 틱을 예약하지 않았다 — 시계가 한 번 뛰고 멈춘다")
	}
	if _, ok := cmd().(tickMsg); !ok {
		t.Errorf("다시 예약한 게 tickMsg 가 아니라 %T", cmd())
	}
	if m2.(model).ticks != 1 {
		t.Errorf("틱 수가 %d 다", m2.(model).ticks)
	}
}

// 멈춘 상태에서는 틱이 와도 세지 않고, 다시 예약하지도 않는다.
func TestPausedTickIsDropped(t *testing.T) {
	m2, cmd := model{running: false, ticks: 7}.Update(tickMsg(time.Now()))
	if cmd != nil {
		t.Error("멈춘 상태인데 다음 틱을 예약했다")
	}
	if m2.(model).ticks != 7 {
		t.Errorf("멈춘 상태인데 틱이 %d 로 늘었다", m2.(model).ticks)
	}
}

// space 로 다시 시작할 때는 틱 사슬이 끊겨 있으므로 새로 예약해 줘야 한다.
func TestSpaceTogglesAndRestartsChain(t *testing.T) {
	m2, cmd := model{running: true}.Update(tea.KeyPressMsg{Code: tea.KeySpace})
	if m2.(model).running {
		t.Error("space 로 멈추지 않았다")
	}
	if cmd != nil {
		t.Error("멈추면서 틱을 예약했다")
	}

	m3, cmd := m2.Update(tea.KeyPressMsg{Code: tea.KeySpace})
	if !m3.(model).running {
		t.Error("space 로 다시 시작하지 않았다")
	}
	if cmd == nil {
		t.Fatal("다시 시작하면서 틱 사슬을 잇지 않았다 — 시계가 영영 멈춘다")
	}
	if _, ok := cmd().(tickMsg); !ok {
		t.Errorf("tickMsg 가 아니라 %T", cmd())
	}
}

func TestResetKey(t *testing.T) {
	m2, _ := model{ticks: 99, running: true}.Update(rune2key('r'))
	if m2.(model).ticks != 0 {
		t.Errorf("r 을 눌렀는데 %d 다", m2.(model).ticks)
	}
}

// 화면은 틱 수와 그것이 뜻하는 경과 시간을 함께 보여 준다.
// 중력(gravity)이 바로 이 계산이라 미리 눈에 익혀 둔다.
func TestViewShowsElapsed(t *testing.T) {
	got := model{ticks: 10, running: true}.View().Content
	if !strings.Contains(got, "10") {
		t.Errorf("틱 수가 없다:\n%s", got)
	}
	if !strings.Contains(got, "1.0") {
		t.Errorf("경과 초(10틱 × 100ms = 1.0초)가 없다:\n%s", got)
	}
}

func TestViewShowsPausedState(t *testing.T) {
	if !strings.Contains(model{running: false}.View().Content, "멈춤") {
		t.Error("멈춤 표시가 없다")
	}
	if !strings.Contains(model{running: true}.View().Content, "진행") {
		t.Error("진행 표시가 없다")
	}
}

func TestQuitKey(t *testing.T) {
	_, cmd := model{running: true}.Update(rune2key('q'))
	if cmd == nil {
		t.Fatal("q 가 무시됐다")
	}
	if _, ok := cmd().(tea.QuitMsg); !ok {
		t.Errorf("Quit 이 아니라 %T", cmd())
	}
}

// 틱 간격은 상수 하나로 정해져 있어야 한다 — 화면 계산과 예약이 어긋나면 안 된다.
func TestTickIntervalIsOneTenthSecond(t *testing.T) {
	if tickEvery != 100*time.Millisecond {
		t.Errorf("틱 간격이 %v 다", tickEvery)
	}
}
