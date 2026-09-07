package monitor

import (
	"fmt"
	"strings"
	"time"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/widgets"
)

// 얼마나 자주 읽을까. 1초보다 짧으면 CPU 사용률이 튀어서 읽기 어렵고,
// 길면 반응이 굼떠 보인다. 이 값은 그 사이의 타협이다.
const defaultInterval = 700 * time.Millisecond

// 그래프에 남길 표본 수. 화면 폭보다 넉넉하게 두고 그릴 때 잘라 쓴다.
const history = 200

type sampleMsg Sample

// Model 은 시스템 모니터의 상태다.
type Model struct {
	prev, cur Sample
	cpuHist   []float64
	memHist   []float64

	spin widgets.Spinner
	cpu  widgets.Progress
	mem  widgets.Progress
	log  widgets.Viewport
	help widgets.Help

	w, h     int
	prof     style.Profile
	paused   bool
	reads    int
	interval time.Duration
}

func New() Model {
	sp := widgets.NewSpinner()
	sp.Set = widgets.SpinnerLine
	return Model{
		spin: sp,
		cpu:  widgets.NewProgress(40),
		mem:  widgets.NewProgress(40),
		log:  widgets.NewViewport(60, 8),
		help: widgets.NewHelp(),
		w:    80, h: 24,
		interval: defaultInterval,
	}
}

// SetInterval 은 읽는 간격을 바꾼다.
//
// 시험과 화면 기록을 위해 열어 둔 문이다. testkit 은 시계를 흉내 내지 않고 진짜로
// 기다리므로, 0.7초 간격으로 열 프레임을 뽑으면 7초가 걸린다. 시험이 느려지면
// 사람이 안 돌리게 되고, 안 돌리는 시험은 없는 것과 같다.
func (m Model) SetInterval(d time.Duration) Model { m.interval = d; return m }

// sampleCmd 는 /proc 를 한 번 읽어 오는 명령이다.
//
// 시계와 읽기를 한 명령에 묶은 이유: 둘을 따로 두면 "읽는 데 걸린 시간" 만큼
// 간격이 점점 늘어난다. 기다린 뒤에 읽고, 읽은 결과를 사건으로 돌려주면
// 다음 예약은 Update 가 한다 — 4단계에서 배운 재예약 패턴 그대로다.
func sampleCmd(interval time.Duration) tea.Cmd {
	return tea.Tick(interval, func(time.Time) tea.Msg { return sampleMsg(Read()) })
}

func (m Model) Init() tea.Cmd {
	// 첫 표본은 기다리지 않고 바로 읽는다. 안 그러면 첫 화면이 0.7초 동안 비어 있다.
	return tea.Batch(
		func() tea.Msg { return sampleMsg(Read()) },
		m.spin.Tick(),
	)
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
		return m.resize(), nil

	case tea.ColorProfileMsg:
		m.prof = msg.Profile
		m.help = m.help.Profile(msg.Profile)
		m.spin.Style = style.New().Profile(msg.Profile).Foreground("205")
		m.cpu.FullStyle = style.New().Profile(msg.Profile).Foreground("205")
		m.mem.FullStyle = style.New().Profile(msg.Profile).Foreground("39")
		return m, nil

	case sampleMsg:
		s := Sample(msg)
		m.prev, m.cur = m.cur, s
		m.reads++
		if s.Err == nil && m.reads > 1 {
			m.cpuHist = push(m.cpuHist, s.CPUPercent(m.prev))
			m.memHist = push(m.memHist, s.MemPercent())
		}
		m.log = m.log.SetContent(m.logText())
		if m.paused {
			return m, nil // 다시 예약하지 않는다 → 자연히 멎는다
		}
		return m, sampleCmd(m.interval)

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case " ", "space", "p":
			m.paused = !m.paused
			if !m.paused {
				return m, sampleCmd(m.interval) // 다시 시작할 때 여기서 건다
			}
			return m, nil
		case "?":
			m.help.ShowAll = !m.help.ShowAll
			return m.resize(), nil
		}
	}

	var cmds []tea.Cmd
	var cmd tea.Cmd
	m.spin, cmd = m.spin.Update(msg)
	cmds = append(cmds, cmd)
	m.log, cmd = m.log.Update(msg)
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

// push 는 새 값을 뒤에 붙이고 오래된 것을 버린다.
// 새 슬라이스를 만든다 — 모델은 값이므로 배열을 나눠 가지면 안 된다.
func push(h []float64, v float64) []float64 {
	next := make([]float64, 0, len(h)+1)
	next = append(next, h...)
	next = append(next, v)
	if len(next) > history {
		next = next[len(next)-history:]
	}
	return next
}

func (m Model) resize() Model {
	w := m.w - 4
	if w < 20 {
		w = 20
	}
	m.cpu.Width, m.mem.Width = w-14, w-14
	m.log.Width = w
	h := m.h - 14
	if m.help.ShowAll {
		h -= 4
	}
	if h < 3 {
		h = 3
	}
	m.log.Height = h
	m.log = m.log.SetContent(m.logText())
	return m
}

func (m Model) logText() string {
	if m.cur.Err != nil {
		return "/proc 를 읽지 못했다: " + m.cur.Err.Error() + "\n\n" +
			"이 앱은 리눅스(안드로이드 포함)의 /proc 파일 시스템을 읽는다.\n" +
			"macOS 나 윈도우에는 그런 파일이 없다 — 있는 척하지 않고 여기 적어 둔다.\n" +
			"그쪽에서는 sysctl 이나 성능 카운터 API 를 써야 하고, 그건 다른 이야기다."
	}
	var b strings.Builder
	fmt.Fprintf(&b, "읽은 횟수      %d\n", m.reads)
	fmt.Fprintf(&b, "부하           %.2f  %.2f  %.2f  (1·5·15분)\n", m.cur.Load1, m.cur.Load5, m.cur.Load15)
	fmt.Fprintf(&b, "가동 시간      %s\n", dur(m.cur.Uptime))
	fmt.Fprintf(&b, "메모리         %s / %s\n", mib(m.cur.MemTotal-m.cur.MemAvail), mib(m.cur.MemTotal))
	b.WriteString("\n")
	b.WriteString("CPU 사용률은 /proc/stat 의 **누적** 값 두 개의 차이로 구한다.\n")
	b.WriteString("한 번만 읽어서는 지금 얼마나 바쁜지 알 수 없다 — 그래서 첫 표본에는\n")
	b.WriteString("사용률이 없고, 두 번째부터 그래프가 그려진다.\n")
	b.WriteString("\n")
	b.WriteString("space 로 멈추면 다음 읽기를 예약하지 않는다. 시계를 따로 끄는 장치가\n")
	b.WriteString("필요 없는 이유다 — 재예약을 안 하면 그것이 곧 멈춤이다.\n")
	return b.String()
}

func mib(kb uint64) string { return fmt.Sprintf("%.1f GiB", float64(kb)/1024/1024) }

func dur(sec float64) string {
	d := time.Duration(sec) * time.Second
	return fmt.Sprintf("%d일 %02d:%02d:%02d",
		int(d.Hours())/24, int(d.Hours())%24, int(d.Minutes())%60, int(d.Seconds())%60)
}

// sparkline 은 값 묶음을 한 줄짜리 그래프로 그린다.
//
// 여덟 단계 블록 문자(▁▂▃▄▅▆▇█)를 쓴다. 이 글자들은 East_Asian_Width 가 N 이라
// 한 칸이다 — 한글과 달리 폭 계산이 어긋날 걱정이 없다.
func sparkline(vals []float64, w int) string {
	const blocks = "▁▂▃▄▅▆▇█"
	r := []rune(blocks)
	if w < 1 {
		return ""
	}
	if len(vals) > w {
		vals = vals[len(vals)-w:]
	}
	var b strings.Builder
	for i := 0; i < w-len(vals); i++ {
		b.WriteByte(' ')
	}
	for _, v := range vals {
		if v < 0 {
			v = 0
		}
		if v > 1 {
			v = 1
		}
		i := int(v * float64(len(r)-1))
		b.WriteRune(r[i])
	}
	return b.String()
}

func (m Model) bindings() []widgets.Binding {
	pause := "멈춤"
	if m.paused {
		pause = "다시"
	}
	return []widgets.Binding{
		widgets.NewBinding("space", pause, " ", "p"),
		widgets.NewBinding("↑/↓", "설명 넘기기", "up", "down"),
		widgets.NewBinding("?", "도움말", "?"),
		widgets.NewBinding("q", "끝내기", "q"),
	}
}

func (m Model) View() string {
	base := style.New().Profile(m.prof)
	state := "보는 중"
	if m.paused {
		state = "멈춤"
	}
	head := base.Bold(true).Render(m.spin.View()+" 보리차 모니터") + "  " +
		base.Faint(true).Render(state)

	label := base.Width(12)
	cpuNow, memNow := 0.0, 0.0
	if n := len(m.cpuHist); n > 0 {
		cpuNow, memNow = m.cpuHist[n-1], m.memHist[n-1]
	}
	m.cpu.ShowPercent, m.mem.ShowPercent = true, true

	graphW := m.cpu.Width
	rows := []string{
		style.JoinHorizontal(style.Top, label.Render("CPU"), m.cpu.View(cpuNow)),
		style.JoinHorizontal(style.Top, label.Render(""), base.Faint(true).Render(sparkline(m.cpuHist, graphW))),
		style.JoinHorizontal(style.Top, label.Render("메모리"), m.mem.View(memNow)),
		style.JoinHorizontal(style.Top, label.Render(""), base.Faint(true).Render(sparkline(m.memHist, graphW))),
	}

	return style.JoinVertical(style.Left,
		head, "",
		style.JoinVertical(style.Left, rows...), "",
		base.Border(style.NormalBorder).Padding(0, 1).Render(m.log.View()),
		"", m.help.View(m.bindings()),
	)
}
