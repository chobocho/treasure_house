package showcase

import (
	"strings"
	"testing"
	"time"

	"treasure/boricha/tea"
	"treasure/boricha/testkit"
	"treasure/boricha/widgets"
	"treasure/boricha/width"
)

// 시험은 빨라야 돌아간다. testkit 의 기다리기는 진짜 잠이라,
// 0.4초짜리 그림을 그대로 두면 각본 한 걸음마다 0.4초를 먹는다.
func fast() Model {
	return New().SetSpinner(widgets.SpinnerSet{Frames: []string{"-", "|"}, FPS: time.Millisecond})
}

func run(t *testing.T, script string) (Model, testkit.Result) {
	t.Helper()
	r, err := testkit.RunScript(fast(), script)
	if err != nil {
		t.Fatal(err)
	}
	return r.Final.(Model), r
}

// 탭은 그저 필드 하나다. tab 을 누르면 돌아가고, 끝에서 처음으로 감긴다.
func TestTabCycles(t *testing.T) {
	m, _ := run(t, `80x24 <tab>`)
	if m.tab != tabColor {
		t.Errorf("tab 한 번 = %v", m.tab)
	}
	m, _ = run(t, `80x24 <tab> <tab> <tab> <tab>`)
	if m.tab != tabStyle {
		t.Errorf("네 번 = %v, 원하는 값 처음", m.tab)
	}
	m, _ = run(t, `80x24 <shift+tab>`)
	if m.tab != tabKeys {
		t.Errorf("shift+tab 한 번 = %v, 원하는 값 마지막", m.tab)
	}
}

// 눌린 키는 이름으로 쌓이고, 여덟 개까지만 남는다.
func TestKeysTabRecords(t *testing.T) {
	m, _ := run(t, `80x24 <tab> <tab> <tab> a b c`)
	if len(m.keys) != 3 {
		t.Fatalf("키가 %d개: %v", len(m.keys), m.keys)
	}
	if strings.Join(m.keys, ",") != "a,b,c" {
		t.Errorf("= %v", m.keys)
	}

	m, _ = run(t, `80x24 abcdefghijkl`)
	if len(m.keys) != 8 {
		t.Errorf("키가 %d개 — 여덟 개까지만 남아야 한다", len(m.keys))
	}
	if m.keys[0] != "e" {
		t.Errorf("가장 오래된 것이 %q", m.keys[0])
	}
}

// 어느 탭에서든 화면이 주어진 크기를 넘지 않는다.
// 색 탭은 256칸짜리 표를 그리므로 좁은 화면에서 넘치기 쉽다.
func TestAllTabsFit(t *testing.T) {
	for _, size := range []string{"80x24", "60x20", "100x30"} {
		_, r := run(t, size+` <tab> <tab> <tab> <tab>`)
		for i, f := range r.Frames {
			lines := strings.Split(f, "\n")
			if len(lines) != r.Rows {
				t.Errorf("%s 프레임 %d 이 %d줄", size, i, len(lines))
			}
			for j, l := range lines {
				if w := width.StringWidth(l); w != r.Cols {
					t.Errorf("%s 프레임 %d 줄 %d 이 %d칸", size, i, j, w)
				}
			}
		}
	}
}

// 글자 폭 탭의 눈금(┤)이 모두 같은 자리에 있어야 한다.
// 이 탭 자체가 width 패키지에 대한 살아 있는 시험이다.
func TestWidthTabRulerLinesUp(t *testing.T) {
	m, _ := run(t, `80x24 <tab> <tab>`)
	body := m.widthTab(m.styleBase())
	type row struct {
		start, ruler int
	}
	var rows []row
	for _, line := range strings.Split(body, "\n") {
		i := strings.Index(line, "│")
		j := strings.Index(line, "┤")
		if i < 0 || j < 0 {
			continue
		}
		rows = append(rows, row{width.StringWidth(line[:i]), width.StringWidth(line[i:j]) - 1})
	}
	if len(rows) < 5 {
		t.Fatalf("눈금이 %d개뿐이다", len(rows))
	}
	for i, r := range rows {
		if r.start != rows[0].start {
			t.Errorf("줄 %d 의 눈금이 %d칸에서 시작, 첫 줄은 %d칸 — 열이 어긋났다", i, r.start, rows[0].start)
		}
	}
	// 눈금 길이는 그 줄이 밝힌 칸 수와 같아야 한다.
	wants := []int{6, 9, 6, 4, 3, 6} // 보리차·green tea·한a글b·🍵🫖·é±─·　전각
	for i, r := range rows {
		if i < len(wants) && r.ruler != wants[i] {
			t.Errorf("줄 %d 의 눈금이 %d칸, 원하는 값 %d칸", i, r.ruler, wants[i])
		}
	}
}

// 마우스 사건도 받는다.
func TestMouse(t *testing.T) {
	r, err := testkit.RunScript(fast(), `80x24 <tab> <tab> <tab>`)
	if err != nil {
		t.Fatal(err)
	}
	m := r.Final.(Model)
	m2, _ := m.Update(tea.MouseMsg{X: 3, Y: 4, Button: tea.MouseLeft, Action: tea.MousePress})
	if got := m2.(Model).mouse; got != "left press (3,4)" {
		t.Errorf("= %q", got)
	}
}

var _ tea.Model = Model{}
