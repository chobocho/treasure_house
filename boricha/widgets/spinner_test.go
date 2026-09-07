package widgets

import (
	"testing"

	"treasure/boricha/tea"
	"treasure/boricha/width"
)

func TestSpinnerAdvances(t *testing.T) {
	s := NewSpinner()
	first := s.View()
	s2, cmd := s.Update(SpinnerTickMsg{})
	if cmd == nil {
		t.Error("다음 울림을 예약하지 않았다 — 한 칸 돌고 멈춘다")
	}
	if s2.View() == first {
		t.Errorf("그림이 안 바뀌었다: %q", first)
	}
	// 원본은 그대로다. 부품도 값이다.
	if s.View() != first {
		t.Error("원본이 바뀌었다")
	}
}

// 한 바퀴 돌면 처음으로 돌아온다.
func TestSpinnerWraps(t *testing.T) {
	s := NewSpinner()
	first := s.View()
	for i := 0; i < len(s.Set.Frames); i++ {
		s, _ = s.Update(SpinnerTickMsg{tag: i})
	}
	if s.View() != first {
		t.Errorf("한 바퀴 뒤 = %q, 원하는 값 %q", s.View(), first)
	}
}

// 뒤늦게 온 중복 울림은 무시한다.
//
// 왜 이런 것이 필요한가. Init 에서 Tick 을 걸고 어딘가에서 또 걸면 시계가 둘이 된다.
// 그러면 그림이 두 배로 빨리 돌고, 그 둘이 서로를 다시 예약해 시계가 계속 불어난다.
// 울림마다 번호표를 붙이고 기대하는 번호만 받아들이면 그 자리에서 끊긴다.
func TestSpinnerIgnoresStaleTick(t *testing.T) {
	s := NewSpinner()
	s, _ = s.Update(SpinnerTickMsg{tag: 0}) // 받아들인다 → tag 1 로
	after := s.View()

	s2, cmd := s.Update(SpinnerTickMsg{tag: 0}) // 뒤늦게 온 같은 번호
	if s2.View() != after {
		t.Error("중복 울림에 그림이 또 돌았다")
	}
	if cmd != nil {
		t.Error("중복 울림에 시계를 또 걸었다 — 시계가 불어난다")
	}
}

// 다른 사건에는 반응하지 않는다.
func TestSpinnerIgnoresOtherMsgs(t *testing.T) {
	s := NewSpinner()
	before := s.View()
	s2, cmd := s.Update(tea.KeyMsg{Code: 'a'})
	if s2.View() != before || cmd != nil {
		t.Error("키 사건에 반응했다")
	}
}

// 미리 만들어 둔 그림들이 모두 쓸 만한지 본다.
func TestSpinnerSets(t *testing.T) {
	sets := map[string]SpinnerSet{
		"Line": SpinnerLine, "Dot": SpinnerDot, "MiniDot": SpinnerMiniDot,
		"Pulse": SpinnerPulse, "Moon": SpinnerMoon, "Tea": SpinnerTea,
	}
	for name, set := range sets {
		if len(set.Frames) < 2 {
			t.Errorf("%s: 그림이 %d장", name, len(set.Frames))
		}
		if set.FPS <= 0 {
			t.Errorf("%s: FPS 가 %v", name, set.FPS)
		}
		// 한 벌 안의 그림은 폭이 모두 같아야 한다.
		// 폭이 들쭉날쭉하면 돌 때마다 옆의 글자가 밀렸다 당겨졌다 한다.
		w0 := width.StringWidth(set.Frames[0])
		for i, f := range set.Frames {
			if w := width.StringWidth(f); w != w0 {
				t.Errorf("%s: %d번째 그림 %q 이 %d칸, 첫 장은 %d칸", name, i, f, w, w0)
			}
		}
	}
}
