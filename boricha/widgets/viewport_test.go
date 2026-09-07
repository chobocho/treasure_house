package widgets

import (
	"fmt"
	"strings"
	"testing"

	"treasure/boricha/tea"
	"treasure/boricha/width"
)

func lines(n int) string {
	out := make([]string, n)
	for i := range out {
		out[i] = fmt.Sprintf("줄 %d", i)
	}
	return strings.Join(out, "\n")
}

// 화면은 언제나 정확히 Height 줄, Width 칸이다.
// 이 계약이 깨지면 뷰포트를 담은 화면 전체의 줄 수가 어긋난다.
func TestViewportShapeIsFixed(t *testing.T) {
	for _, n := range []int{0, 1, 3, 20} {
		v := NewViewport(12, 5).SetContent(lines(n))
		got := strings.Split(v.View(), "\n")
		if len(got) != 5 {
			t.Errorf("내용 %d줄일 때 화면이 %d줄, 원하는 값 5줄", n, len(got))
			continue
		}
		for i, l := range got {
			if w := width.StringWidth(l); w != 12 {
				t.Errorf("내용 %d줄, 화면 줄 %d 이 %d칸, 원하는 값 12칸: %q", n, i, w, l)
			}
		}
	}
}

func TestViewportScrolls(t *testing.T) {
	v := NewViewport(20, 3).SetContent(lines(10))
	if !strings.Contains(v.View(), "줄 0") || strings.Contains(v.View(), "줄 3") {
		t.Errorf("처음 화면 = %q", v.View())
	}
	if !v.AtTop() || v.AtBottom() {
		t.Error("처음인데 AtTop/AtBottom 이 이상하다")
	}

	v = v.LineDown(2)
	if !strings.Contains(v.View(), "줄 2") || strings.Contains(v.View(), "줄 1") {
		t.Errorf("두 줄 내린 화면 = %q", v.View())
	}
	if v.AtTop() {
		t.Error("내렸는데 AtTop 이 참")
	}

	// 끝을 넘어 내려가지 않는다. 넘어가면 빈 화면이 보인다.
	v = v.LineDown(100)
	if !v.AtBottom() {
		t.Error("끝까지 내렸는데 AtBottom 이 거짓")
	}
	if !strings.Contains(v.View(), "줄 9") {
		t.Errorf("맨 아래 화면에 마지막 줄이 없다: %q", v.View())
	}
	v2 := v.LineDown(1)
	if v2.YOffset != v.YOffset {
		t.Error("맨 아래에서 더 내려갔다")
	}
	v = v.LineUp(100)
	if !v.AtTop() {
		t.Error("맨 위로 못 갔다")
	}
}

// 내용이 화면보다 짧으면 스크롤이 없다.
func TestViewportShortContent(t *testing.T) {
	v := NewViewport(20, 5).SetContent(lines(2))
	if !v.AtTop() || !v.AtBottom() {
		t.Error("짧은 내용인데 위도 아래도 아니라고 한다")
	}
	if got := v.LineDown(3).YOffset; got != 0 {
		t.Errorf("짧은 내용인데 %d 만큼 내려갔다", got)
	}
	if p := v.ScrollPercent(); p != 1 {
		t.Errorf("ScrollPercent = %v, 원하는 값 1", p)
	}
}

func TestViewportScrollPercent(t *testing.T) {
	v := NewViewport(20, 5).SetContent(lines(15))
	if p := v.ScrollPercent(); p != 0 {
		t.Errorf("맨 위에서 %v", p)
	}
	if p := v.GotoBottom().ScrollPercent(); p != 1 {
		t.Errorf("맨 아래에서 %v", p)
	}
}

// 폭보다 긴 줄은 접는다. 안 접으면 터미널이 감아 버려 줄 수가 어긋난다.
func TestViewportWrapsLongLines(t *testing.T) {
	v := NewViewport(10, 5).SetContent("보리차는 Bubble Tea 가 아니다")
	if v.TotalLines() < 2 {
		t.Errorf("접히지 않았다: %d줄", v.TotalLines())
	}
	for _, l := range strings.Split(v.View(), "\n") {
		if w := width.StringWidth(l); w != 10 {
			t.Errorf("줄 %q 이 %d칸", l, w)
		}
	}
}

// 키와 마우스 휠로도 움직인다.
func TestViewportKeysAndWheel(t *testing.T) {
	v := NewViewport(20, 3).SetContent(lines(30))
	v, _ = v.Update(tea.KeyMsg{Code: 'j', Text: "j"})
	if v.YOffset != 1 {
		t.Errorf("j 뒤 = %d", v.YOffset)
	}
	v, _ = v.Update(tea.KeyMsg{Code: tea.KeyPgDown})
	if v.YOffset != 4 {
		t.Errorf("pgdown 뒤 = %d, 원하는 값 4 (한 화면 3줄)", v.YOffset)
	}
	v, _ = v.Update(tea.KeyMsg{Code: tea.KeyHome})
	if v.YOffset != 0 {
		t.Errorf("home 뒤 = %d", v.YOffset)
	}
	v, _ = v.Update(tea.MouseMsg{Button: tea.MouseWheelDown, Action: tea.MousePress})
	if v.YOffset != 3 {
		t.Errorf("휠 아래 뒤 = %d, 원하는 값 3", v.YOffset)
	}
	v, _ = v.Update(tea.MouseMsg{Button: tea.MouseWheelUp, Action: tea.MousePress})
	if v.YOffset != 0 {
		t.Errorf("휠 위 뒤 = %d", v.YOffset)
	}
}

func TestViewportKeyBindings(t *testing.T) {
	v := NewViewport(20, 3)
	bs := v.KeyBindings()
	if len(bs) < 4 {
		t.Fatalf("배치가 %d개", len(bs))
	}
	// 도움말에 적힌 키가 실제로 먹어야 한다. 두 곳이 어긋나지 않는지 확인한다.
	v = v.SetContent(lines(30))
	for _, b := range bs {
		for _, k := range b.Keys {
			before := v
			after, _ := v.Update(tea.KeyMsg{Code: keyCodeFor(k), Text: textFor(k)})
			if after.YOffset == before.YOffset && b.Help[1] != "맨 위로" {
				// 맨 위에서 "위로" 계열은 안 움직이는 것이 맞다
				if !strings.Contains(b.Help[1], "위") {
					t.Errorf("도움말에 있는 키 %q 가 아무 일도 안 한다", k)
				}
			}
			v = before
		}
	}
}

func keyCodeFor(k string) rune {
	switch k {
	case "up":
		return tea.KeyUp
	case "down":
		return tea.KeyDown
	case "pgup":
		return tea.KeyPgUp
	case "pgdown":
		return tea.KeyPgDown
	case "home":
		return tea.KeyHome
	case "end":
		return tea.KeyEnd
	}
	return rune(k[0])
}

func textFor(k string) string {
	if len(k) == 1 {
		return k
	}
	return ""
}
