package main

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
)

func rune2key(r rune) tea.KeyPressMsg {
	return tea.KeyPressMsg{Code: r, Text: string(r)}
}

// Cmd 는 "지금 하는 일"이 아니라 "나중에 메시지를 만들어 줄 함수"다.
// 부르기 전에는 아무 일도 일어나지 않는다 — 이게 Update 를 순수하게 유지하는 장치다.
func TestCmdIsJustAFunction(t *testing.T) {
	calls := 0
	cmd := func() tea.Msg { calls++; return doneMsg{} }
	if calls != 0 {
		t.Fatal("Cmd 를 만들기만 했는데 실행됐다")
	}
	_ = cmd()
	if calls != 1 {
		t.Errorf("호출 횟수가 %d 다", calls)
	}
}

// Batch 는 여러 Cmd 를 한 덩어리로 묶는다. 순서는 보장하지 않는다 —
// 결과는 BatchMsg 라는 Cmd 슬라이스로 나온다.
func TestBatchProducesBatchMsg(t *testing.T) {
	m2, cmd := (model{}).Update(rune2key('b'))
	if cmd == nil {
		t.Fatal("b 가 Cmd 를 만들지 않았다")
	}
	batch, ok := cmd().(tea.BatchMsg)
	if !ok {
		t.Fatalf("BatchMsg 가 아니라 %T", cmd())
	}
	if len(batch) != 2 {
		t.Errorf("묶인 Cmd 가 %d개다", len(batch))
	}
	if !strings.Contains(m2.(model).status, "동시") {
		t.Errorf("상태가 %q 다", m2.(model).status)
	}
}

// Sequence 는 앞의 Cmd 가 끝나야 다음을 시작한다. 순서가 중요할 때 쓴다.
func TestSequenceIsOrdered(t *testing.T) {
	_, cmd := (model{}).Update(rune2key('s'))
	if cmd == nil {
		t.Fatal("s 가 Cmd 를 만들지 않았다")
	}
	// Sequence 는 내부 타입을 돌려주므로 타입 이름 대신 "BatchMsg 가 아니다"로 가른다.
	if _, isBatch := cmd().(tea.BatchMsg); isBatch {
		t.Error("Sequence 인데 BatchMsg 가 나왔다")
	}
}

// AI 가 생각하는 흉내: Cmd 가 시간을 잡아먹고 결과 메시지를 돌려준다.
// 이 시간 동안에도 Update 는 계속 다른 메시지를 처리한다 — 화면이 안 얼어붙는다.
func TestThinkingCmdReturnsMove(t *testing.T) {
	m2, cmd := (model{}).Update(rune2key('t'))
	if !m2.(model).thinking {
		t.Error("생각 중 표시가 안 켜졌다")
	}
	if cmd == nil {
		t.Fatal("생각하는 Cmd 가 없다")
	}
	msg, ok := cmd().(moveMsg)
	if !ok {
		t.Fatalf("moveMsg 가 아니라 %T", cmd())
	}
	if msg.col < 0 || msg.col > 9 {
		t.Errorf("열이 %d 다 — 0~9 여야 한다", msg.col)
	}
}

func TestMoveMsgClearsThinking(t *testing.T) {
	m2, _ := model{thinking: true}.Update(moveMsg{col: 4})
	m := m2.(model)
	if m.thinking {
		t.Error("결과가 왔는데 생각 중 표시가 남아 있다")
	}
	if len(m.log) == 0 || !strings.Contains(m.log[0], "4") {
		t.Errorf("기록에 결과가 없다: %v", m.log)
	}
}

// 기록은 상한이 있다 — 무한히 쌓으면 화면 밖으로 넘친다.
func TestLogIsCapped(t *testing.T) {
	var m tea.Model = model{}
	for i := 0; i < logMax+3; i++ {
		m, _ = m.Update(doneMsg{})
	}
	if n := len(m.(model).log); n != logMax {
		t.Errorf("기록이 %d줄이다 — %d줄이어야 한다", n, logMax)
	}
}

// 생각하는 중에 t 를 또 누르면 무시된다. 안 그러면 Cmd 가 겹쳐 결과가 두 번 온다.
func TestNoDoubleThinking(t *testing.T) {
	_, cmd := model{thinking: true}.Update(rune2key('t'))
	if cmd != nil {
		t.Error("생각 중인데 또 생각하기 시작했다")
	}
}

func TestViewShowsHelpAndStatus(t *testing.T) {
	got := model{status: "대기"}.View().Content
	for _, want := range []string{"b", "s", "t", "q", "대기"} {
		if !strings.Contains(got, want) {
			t.Errorf("%q 가 화면에 없다:\n%s", want, got)
		}
	}
}

func TestQuitKey(t *testing.T) {
	_, cmd := (model{}).Update(rune2key('q'))
	if cmd == nil {
		t.Fatal("q 가 무시됐다")
	}
	if _, ok := cmd().(tea.QuitMsg); !ok {
		t.Errorf("Quit 이 아니라 %T", cmd())
	}
}
