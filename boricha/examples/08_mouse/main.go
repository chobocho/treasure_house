// 08_mouse — 마우스.
//
// 마우스는 기본으로 꺼져 있다. 켜면 터미널이 클릭과 움직임을 이스케이프 시퀀스로
// 보내 주는데, 그 대신 터미널 자체의 선택·복사가 막힌다(shift 를 누른 채 끌면 대개 살아난다).
// 그 맞바꿈이 싫은 사용자도 있으므로, 켤지 말지는 프로그램이 정할 일이다.
//
// 우리는 SGR 1006 인코딩만 받는다. 옛 방식은 좌표를 바이트 하나에 담아서
// 223칸을 넘는 창에서 무너지고, 버튼을 뗀 사건에서 어느 버튼이었는지도 잃는다.
package main

import (
	"fmt"
	"os"
	"strings"

	"treasure/boricha/tea"
	"treasure/boricha/width"
)

type model struct {
	w, h   int
	events []string
	marks  map[[2]int]rune
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "c":
			m.marks = nil
		}
	case tea.MouseMsg:
		next := make([]string, 0, len(m.events)+1)
		next = append(next, m.events...)
		next = append(next, msg.String())
		if len(next) > 8 {
			next = next[len(next)-8:]
		}
		m.events = next

		// 클릭한 자리에 표시를 남긴다. 맵도 값처럼 다루려면 새로 만들어야 한다 —
		// 맵은 참조라서 그냥 쓰면 이전 모델의 맵까지 같이 바뀐다.
		if msg.Action == tea.MousePress && msg.Button == tea.MouseLeft {
			marks := map[[2]int]rune{}
			for k, v := range m.marks {
				marks[k] = v
			}
			marks[[2]int{msg.X, msg.Y}] = '●'
			m.marks = marks
		}
	}
	return m, nil
}

func (m model) View() string {
	if m.w < 20 || m.h < 12 {
		return "창이 너무 작습니다"
	}
	grid := make([][]rune, m.h)
	for y := range grid {
		grid[y] = []rune(strings.Repeat(" ", m.w))
	}
	for pos, ch := range m.marks {
		x, y := pos[0], pos[1]
		if x >= 0 && x < m.w && y >= 0 && y < m.h {
			grid[y][x] = ch
		}
	}

	head := []string{
		"마우스 실습 — 아무 데나 눌러 보세요",
		"휠도 굴려 보고, 누른 채 끌어도 보세요",
		"c 표시 지우기   q 끝내기",
		strings.Repeat("─", 40),
	}
	for i, e := range m.events {
		head = append(head, fmt.Sprintf("%d. %s", i+1, e))
	}
	for i, line := range head {
		if i >= m.h {
			break
		}
		r := []rune(width.Pad(width.Truncate(line, m.w), m.w))
		copy(grid[i], r)
	}

	out := make([]string, m.h)
	for y, row := range grid {
		out[y] = strings.TrimRight(string(row), " ")
	}
	return strings.Join(out, "\n")
}

func main() {
	p := tea.NewProgram(model{}, tea.WithAltScreen(), tea.WithMouse())
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
