package testkit

import (
	"bytes"
	"fmt"
	"strings"
	"testing"
	"time"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/width"
)

// 시험용 모델. 진짜 앱이 하는 일을 작게 줄여 놓았다 — 키를 세고, 글자를 모으고,
// 명령을 걸고, 크기를 기억한다.
type app struct {
	n     int
	typed string
	ticks int
	w, h  int
	prof  style.Profile
}

type tickMsg struct{}

func (m app) Init() tea.Cmd { return nil }

func (m app) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
	case tea.ColorProfileMsg:
		m.prof = msg.Profile
	case tickMsg:
		m.ticks++
		return m, tea.Tick(time.Millisecond, func(time.Time) tea.Msg { return tickMsg{} })
	case tea.PasteMsg:
		m.typed += string(msg)
	case tea.KeyMsg:
		switch msg.String() {
		case "q":
			return m, tea.Quit
		case "up":
			m.n++
		case "down":
			m.n--
		case "t":
			return m, tea.Tick(time.Millisecond, func(time.Time) tea.Msg { return tickMsg{} })
		default:
			if msg.Text != "" {
				m.typed += msg.Text
			}
		}
	}
	return m, nil
}

func (m app) View() string {
	return fmt.Sprintf("n=%d\n글=%s\n틱=%d\n%d×%d", m.n, m.typed, m.ticks, m.w, m.h)
}

func TestRunScript(t *testing.T) {
	r, err := RunScript(app{}, `20x6 <up> <up> <down> "보리차" q`)
	if err != nil {
		t.Fatal(err)
	}
	got := r.Final.(app)
	if got.n != 1 {
		t.Errorf("n = %d, 원하는 값 1", got.n)
	}
	if got.typed != "보리차" {
		t.Errorf("글 = %q", got.typed)
	}
	if got.w != 20 || got.h != 6 {
		t.Errorf("크기 = %d×%d", got.w, got.h)
	}
	if r.Cols != 20 || r.Rows != 6 {
		t.Errorf("Result 크기 = %d×%d", r.Cols, r.Rows)
	}
}

// 프레임은 언제나 Rows 줄, Cols 칸이다. 재생기가 그것을 전제로 그린다.
func TestFrameShape(t *testing.T) {
	r, err := RunScript(app{}, `12x5 <up> "한글이 길게 들어간 줄" .2`)
	if err != nil {
		t.Fatal(err)
	}
	if len(r.Frames) == 0 {
		t.Fatal("프레임이 없다")
	}
	for i, f := range r.Frames {
		lines := strings.Split(f, "\n")
		if len(lines) != 5 {
			t.Errorf("프레임 %d 이 %d줄", i, len(lines))
			continue
		}
		for j, l := range lines {
			if w := width.StringWidth(l); w != 12 {
				t.Errorf("프레임 %d 줄 %d 이 %d칸: %q", i, j, w, l)
			}
		}
	}
}

// 걸음마다 프레임이 하나씩. 크기 지정은 걸음이 아니라 설정이므로 프레임을 안 남긴다.
// 첫 프레임은 아무 입력도 없는 시작 화면이다.
func TestFrameCount(t *testing.T) {
	r, _ := RunScript(app{}, `20x6 <up> <up> .3`)
	// 시작 1 + 키 2 + 기다리기 3 = 6.
	// 기다리기가 프레임을 남기는 것이 중요하다 — 애니메이션은 그 프레임들로 만들어진다.
	if len(r.Frames) != 6 {
		t.Errorf("프레임 %d개, 원하는 값 6개", len(r.Frames))
	}
}

// **결정론이 이 도구의 존재 이유다.** 두 번 돌리면 글자 하나까지 같아야 한다.
// 그래야 make record 를 다시 돌린 뒤 git diff 가 비어 있다.
func TestDeterministic(t *testing.T) {
	script := `30x8 <up> "차" t .3 <down> q`
	a, err := RunScript(app{}, script)
	if err != nil {
		t.Fatal(err)
	}
	b, err := RunScript(app{}, script)
	if err != nil {
		t.Fatal(err)
	}
	if len(a.Frames) != len(b.Frames) {
		t.Fatalf("프레임 수가 %d 대 %d", len(a.Frames), len(b.Frames))
	}
	for i := range a.Frames {
		if a.Frames[i] != b.Frames[i] {
			t.Fatalf("프레임 %d 이 다르다\n%q\n%q", i, a.Frames[i], b.Frames[i])
		}
	}
}

// 명령은 기다리는 걸음에서 돈다. 재예약하는 시계는 걸음 수만큼만 돈다 —
// 그래서 무한히 도는 시계를 넣어도 각본은 반드시 끝난다.
func TestWaitRunsCommands(t *testing.T) {
	r, _ := RunScript(app{}, `20x6 t .4`)
	// t 를 친 걸음의 끝에서 한 번, 기다린 네 번에 네 번 = 5.
	// 스스로를 재예약하는 시계인데도 여기서 멈춘다 — 각본이 준 틈만큼만 돌기 때문이다.
	if got := r.Final.(app).ticks; got != 5 {
		t.Errorf("틱 = %d, 원하는 값 5", got)
	}
}

// q 를 만나면 그 뒤의 걸음은 무시한다.
func TestQuitStopsEarly(t *testing.T) {
	r, _ := RunScript(app{}, `20x6 <up> q <up> <up>`)
	if got := r.Final.(app).n; got != 1 {
		t.Errorf("n = %d, 원하는 값 1", got)
	}
}

// 색 수준을 정해 줄 수 있다. 기록에는 색이 필요하다.
func TestProfile(t *testing.T) {
	r, _ := Run(app{}, `20x6 q`, Options{Cols: 20, Rows: 6, Profile: style.TrueColor})
	if got := r.Final.(app).prof; got != style.TrueColor {
		t.Errorf("색 수준 = %v", got)
	}
}

func TestBadScript(t *testing.T) {
	if _, err := RunScript(app{}, `<없는키>`); err == nil {
		t.Error("이상한 각본에 오류를 안 냈다")
	}
}

// ── 진짜 Program 과 대조 ────────────────────────────────────────────
//
// testkit 은 Program 을 쓰지 않고 같은 규칙을 다시 쓴 것이다.
// 그러면 "그 규칙이 정말 같은가" 를 누군가 지켜봐야 한다. 이 시험이 그것이다.
// 같은 바이트를 두 길로 흘려 넣고 끝난 모델이 같은지 본다.
func TestMatchesRealProgram(t *testing.T) {
	script := `20x6 <up> <up> <down> "보리차" q`
	kit, err := RunScript(app{}, script)
	if err != nil {
		t.Fatal(err)
	}

	steps, _ := Parse(script)
	var raw bytes.Buffer
	for _, s := range steps {
		raw.Write(s.Bytes())
	}
	var out bytes.Buffer
	p := tea.NewProgram(app{},
		tea.WithInput(&raw), tea.WithOutput(&out),
		tea.WithWindowSize(20, 6), tea.WithColorProfile(style.ANSI256))
	final, err := p.Run()
	if err != nil {
		t.Fatal(err)
	}

	a, b := kit.Final.(app), final.(app)
	if a.n != b.n || a.typed != b.typed || a.w != b.w || a.h != b.h {
		t.Errorf("testkit %+v\nProgram %+v", a, b)
	}
}

// 프레임과 이름표는 늘 짝이 맞아야 한다. 재생기가 둘을 나란히 읽는다.
func TestLabels(t *testing.T) {
	r, err := RunScript(app{}, `20x6 <up> "차" .2 q`)
	if err != nil {
		t.Fatal(err)
	}
	if len(r.Labels) != len(r.Frames) {
		t.Fatalf("프레임 %d개, 이름표 %d개", len(r.Frames), len(r.Labels))
	}
	want := []string{"시작", "<up>", `"차"`, ".", ".", "q"}
	for i, w := range want {
		if r.Labels[i] != w {
			t.Errorf("이름표 %d = %q, 원하는 값 %q", i, r.Labels[i], w)
		}
	}
}
