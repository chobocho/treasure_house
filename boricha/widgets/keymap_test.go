package widgets

import "testing"

// 키 배치를 값으로 두면, 도움말 줄과 실제 동작이 **같은 곳** 에서 나온다.
// 그러지 않으면 키를 바꿀 때마다 도움말 고치는 것을 잊는다 — 반드시 잊는다.
func TestBindingMatches(t *testing.T) {
	b := NewBinding("↑/k", "위로", "up", "k")
	for _, k := range []string{"up", "k"} {
		if !b.Matches(k) {
			t.Errorf("%q 가 안 맞는다고 한다", k)
		}
	}
	for _, k := range []string{"down", "K", "ctrl+k", ""} {
		if b.Matches(k) {
			t.Errorf("%q 가 맞는다고 한다", k)
		}
	}
}

// 꺼 둔 배치는 맞지 않는다. 상황에 따라 쓸 수 없는 키(빈 목록에서의 "지우기")를
// 도움말에서도 숨기고 동작도 막는 일을 한 곳에서 처리하려는 것이다.
func TestBindingEnabled(t *testing.T) {
	b := NewBinding("d", "지우기", "d")
	if !b.Enabled() {
		t.Error("새로 만든 배치가 꺼져 있다")
	}
	off := b.SetEnabled(false)
	if off.Matches("d") {
		t.Error("꺼 둔 배치가 맞는다고 한다")
	}
	if !b.Matches("d") {
		t.Error("원본까지 꺼졌다 — 값이 아니라 참조로 다뤄지고 있다")
	}
}

func TestBindingHelp(t *testing.T) {
	b := NewBinding("↑/k", "위로", "up", "k")
	if b.Help[0] != "↑/k" || b.Help[1] != "위로" {
		t.Errorf("도움말 = %v", b.Help)
	}
}
