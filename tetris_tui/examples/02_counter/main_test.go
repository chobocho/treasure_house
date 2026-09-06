package main

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
)

func rune2key(r rune) tea.KeyPressMsg {
	return tea.KeyPressMsg{Code: r, Text: string(r)}
}

func TestStartsAtZero(t *testing.T) {
	if !strings.Contains((model{}).View().Content, "0") {
		t.Error("처음 화면에 0 이 없다")
	}
}

func TestUpAndDown(t *testing.T) {
	cases := []struct {
		key  tea.KeyPressMsg
		from int
		want int
	}{
		{tea.KeyPressMsg{Code: tea.KeyUp}, 0, 1},
		{rune2key('k'), 3, 4},
		{rune2key('+'), -1, 0},
		{tea.KeyPressMsg{Code: tea.KeyDown}, 0, -1},
		{rune2key('j'), 3, 2},
		{rune2key('-'), 1, 0},
	}
	for _, c := range cases {
		m2, _ := model{n: c.from}.Update(c.key)
		if got := m2.(model).n; got != c.want {
			t.Errorf("%q: %d → %d, %d 를 기대했다", c.key.String(), c.from, got, c.want)
		}
	}
}

func TestResetKey(t *testing.T) {
	m2, _ := model{n: 42}.Update(rune2key('r'))
	if got := m2.(model).n; got != 0 {
		t.Errorf("r 을 눌렀는데 %d 다", got)
	}
}

// 경계값: 음수와 큰 수도 그대로 보여야 한다. 화면 폭 때문에 잘리면 안 된다.
func TestExtremeValuesRender(t *testing.T) {
	for _, n := range []int{-1, -999999, 999999} {
		got := model{n: n}.View().Content
		if !strings.Contains(got, itoa(n)) {
			t.Errorf("%d 이 화면에 없다:\n%s", n, got)
		}
	}
}

func itoa(n int) string {
	neg := n < 0
	if neg {
		n = -n
	}
	if n == 0 {
		return "0"
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

// 이 예제의 진짜 교훈. Update 는 모델의 *복사본*을 받는다.
// 원본은 절대 바뀌지 않는다 — 이걸 모르면 "왜 안 변하지?"로 하루를 날린다.
func TestModelIsCopiedNotMutated(t *testing.T) {
	orig := model{n: 5}
	m2, _ := orig.Update(tea.KeyPressMsg{Code: tea.KeyUp})
	if orig.n != 5 {
		t.Errorf("원본이 바뀌었다: %d", orig.n)
	}
	if m2.(model).n != 6 {
		t.Errorf("반환된 모델이 안 바뀌었다: %d", m2.(model).n)
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

func TestHelpTextIsShown(t *testing.T) {
	got := (model{}).View().Content
	for _, want := range []string{"↑", "↓", "r", "q"} {
		if !strings.Contains(got, want) {
			t.Errorf("도움말에 %q 가 없다:\n%s", want, got)
		}
	}
}
