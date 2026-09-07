// Package bugs 는 이 덱을 만들면서 **실제로 겪은** 함정 셋을 그대로 재현한다.
//
// 왜 버그를 코드로 남기는가. "이렇게 하면 안 됩니다" 라고 글로만 적으면 읽는 사람은
// 그 장면을 상상해야 한다. 상상한 장면은 대개 실제보다 얌전하다.
// 여기 있는 모델들은 진짜로 고장 나 있고, tools/record 와 tmux 가 그 화면을 찍어 온다.
// 덱에 실리는 "고치기 전" 그림은 전부 이 파일에서 나온 것이다.
//
// 모델마다 fixed 를 참으로 주면 고친 판이 된다. 같은 각본을 두 판으로 돌려
// 나란히 놓으면 그것이 곧 before/after 다.
package bugs

import (
	"fmt"
	"os"
	"strings"
	"time"

	"treasure/boricha/tea"
	"treasure/boricha/term"
	"treasure/boricha/width"
)

// ── 함정 1. 글자 폭을 len 으로 세기 ─────────────────────────────────
//
// 한글 한 글자는 UTF-8 로 3바이트, 화면에서는 2칸이다. len() 은 바이트를 센다.
// 그래서 len 으로 표를 맞추면 한글이 든 줄만 왼쪽으로 한참 밀린다.
// 한국어 TUI 에서 상자가 깨지는 원인의 거의 전부가 이것이다.

type widthModel struct {
	fixed bool
	sel   int
}

// NewWidth 는 표 정렬 함정을 보여 주는 모델을 만든다.
func NewWidth(fixed bool) tea.Model { return widthModel{fixed: fixed} }

var teaRows = []struct{ name, from string }{
	{"보리차", "볶은 보리"},
	{"green tea", "steamed leaf"},
	{"둥굴레차", "뿌리"},
	{"black tea", "fully oxidised"},
	{"메밀차", "볶은 메밀"},
}

func (m widthModel) Init() tea.Cmd { return nil }

func (m widthModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	if k, ok := msg.(tea.KeyMsg); ok {
		switch k.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "down", "j":
			m.sel = (m.sel + 1) % len(teaRows)
		case "up", "k":
			m.sel = (m.sel - 1 + len(teaRows)) % len(teaRows)
		}
	}
	return m, nil
}

func (m widthModel) View() string {
	title := "고친 판 — width.Pad 로 칸을 센다"
	pad := func(s string, w int) string { return width.Pad(s, w) }
	if !m.fixed {
		title = "고장 난 판 — len 으로 바이트를 센다"
		// 바로 이 줄이 함정이다. len 은 바이트를 세므로 한글 한 글자마다 두 칸씩 모자라진다.
		pad = func(s string, w int) string {
			if d := w - len(s); d > 0 {
				return s + strings.Repeat(" ", d)
			}
			return s
		}
	}

	var b strings.Builder
	b.WriteString(title + "\n")
	b.WriteString("┌────────────┬────────────────┐\n")
	for i, r := range teaRows {
		mark := " "
		if i == m.sel {
			mark = "▸"
		}
		b.WriteString("│" + mark + pad(r.name, 11) + "│ " + pad(r.from, 15) + "│\n")
	}
	b.WriteString("└────────────┴────────────────┘\n")
	b.WriteString("\n↑/↓ 고르기   q 끝내기")
	return b.String()
}

// ── 함정 2. Tick 을 다시 걸지 않기 ──────────────────────────────────
//
// tea.Tick 은 한 번만 울린다. 받은 자리에서 다시 걸지 않으면 시계가 한 번 가고 멎는다.
// 처음 쓰는 사람이 거의 예외 없이 겪는다 — 그리고 화면이 "멈춘" 것처럼 보여서
// 원인을 렌더러에서 찾게 된다.

type tickModel struct {
	fixed bool
	n     int
}

type tickMsg struct{}

// NewTick 은 시계 재예약 함정을 보여 주는 모델을 만든다.
func NewTick(fixed bool) tea.Model { return tickModel{fixed: fixed} }

func tickCmd() tea.Cmd {
	return tea.Tick(120*time.Millisecond, func(time.Time) tea.Msg { return tickMsg{} })
}

func (m tickModel) Init() tea.Cmd { return tickCmd() }

func (m tickModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tickMsg:
		m.n++
		if m.fixed {
			return m, tickCmd() // ← 이 한 줄이 있고 없고의 차이다
		}
		return m, nil
	case tea.KeyMsg:
		if s := msg.String(); s == "q" || s == "ctrl+c" {
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m tickModel) View() string {
	state := "고장 난 판 — 재예약 없음"
	if m.fixed {
		state = "고친 판 — 울림을 받고 다시 건다"
	}
	return fmt.Sprintf("%s\n\n%s\n\n울림 %d번\n\n(고장 난 판은 여기서 멎는다)\nq 끝내기",
		state, strings.Repeat("●", m.n)+strings.Repeat("·", 20-min(m.n, 20)), m.n)
}

// ── 함정 3. 폭보다 긴 줄을 그냥 내보내기 ────────────────────────────
//
// 줄이 폭을 넘으면 터미널이 스스로 다음 줄로 감는다. 그러면 우리가 "10줄" 이라고
// 센 화면이 실제로는 14줄이 되고, 아래에 있어야 할 것이 화면 밖으로 밀려난다.
// 줄 번호로 커서를 옮기는 렌더러라면 그때부터 엉뚱한 줄을 고쳐 쓴다.
//
// **이 함정은 tea 로는 재현할 수 없다.** render.NewFrame 이 프레임을 만들 때 이미
// 폭에 맞춰 자르기 때문이다 — 구조적으로 못 일어나게 막아 둔 것이 우리 렌더러의 값이다.
// 그래서 아래 함수는 tea 를 쓰지 않고 터미널에 직접 그린다. 1부의 00_raw 와 같은 자리에서,
// 6부의 렌더러가 무엇을 대신해 주고 있는지 보이려는 것이다.

// RunRawWrap 은 프레임워크 없이 직접 그리는 판을 돌린다.
// fixed 가 참이면 폭에 맞춰 자른다.
func RunRawWrap(fixed bool) error {
	tm := term.New(os.Stdin, os.Stdout)
	if err := tm.MakeRaw(); err != nil {
		return err
	}
	defer tm.Restore()
	_ = tm.EnterAltScreen()
	_ = tm.HideCursor()
	defer tm.Cleanup()

	cols, rows, err := tm.Size()
	if err != nil {
		cols, rows = 80, 24
	}

	keys := make(chan byte, 8)
	go func() {
		buf := make([]byte, 8)
		for {
			n, err := os.Stdin.Read(buf)
			if err != nil {
				close(keys)
				return
			}
			for _, c := range buf[:n] {
				keys <- c
			}
		}
	}()

	t := time.NewTicker(150 * time.Millisecond)
	defer t.Stop()
	n := 0
	for {
		_ = tm.WriteString(rawWrapFrame(fixed, cols, rows, n))
		select {
		case c, ok := <-keys:
			if !ok || c == 'q' || c == 0x03 {
				return nil
			}
		case <-t.C:
			n++
		}
	}
}

// rawWrapFrame 은 화면 한 장을 만든다.
//
// 화면 전체를 지우고 처음부터 다시 쓴다 — 가장 단순한 방법이고, 동시에 깜빡임의 원인이다.
// 줄바꿈은 "\r\n" 이어야 한다. OPOST 를 껐으므로 "\n" 은 커서를 한 줄 내리기만 하고
// 1열로 되돌려 주지 않아 계단이 생긴다.
func rawWrapFrame(fixed bool, cols, rows, n int) string {
	head := "고장 난 판 — 폭을 넘는 줄을 그대로 내보낸다"
	if fixed {
		head = "고친 판 — width.Truncate 로 폭에 맞춰 자른다"
	}
	long := "보리차는 Bubble Tea 가 아니지만 같은 모양으로 만들 수 있다. " +
		"이 줄은 일부러 화면 폭보다 길게 만들었다. " + strings.Repeat("─", 30)

	lines := []string{head, ""}
	for i := 0; i < 6; i++ {
		l := fmt.Sprintf("%d: %s", i, long)
		if fixed {
			l = width.Truncate(l, cols)
		}
		lines = append(lines, l)
	}
	lines = append(lines, "")
	lines = append(lines, fmt.Sprintf("↑ 여섯 줄이어야 한다. 지금 이 줄은 화면의 %d번째 줄이다.", len(lines)+1))
	lines = append(lines, fmt.Sprintf("울림 %d번   q 끝내기", n))

	var b strings.Builder
	b.WriteString(term.ClearScreen)
	b.WriteString(term.CursorTo(1, 1))
	b.WriteString(strings.Join(lines, "\r\n"))
	return b.String()
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
