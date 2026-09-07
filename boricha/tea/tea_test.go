package tea

import (
	"bytes"
	"fmt"
	"strings"
	"sync"
	"testing"
	"time"

	"treasure/boricha/style"
	"treasure/boricha/term"
)

// ── 시험용 모델 ─────────────────────────────────────────────────────
// 세는 모델 하나로 대부분의 시험을 치른다. 진짜 앱이 하는 일과 똑같이
// 사건을 받아 자기를 고친 복사본과 다음에 할 일(Cmd)을 돌려준다.

type counter struct {
	n      int
	keys   []string
	size   [2]int
	prof   style.Profile
	custom []string
}

type customMsg string

func (m counter) Init() Cmd { return nil }

func (m counter) Update(msg Msg) (Model, Cmd) {
	switch msg := msg.(type) {
	case KeyMsg:
		m.keys = append(append([]string{}, m.keys...), msg.String())
		switch msg.String() {
		case "q":
			return m, Quit
		case "up":
			m.n++
		case "down":
			m.n--
		}
	case WindowSizeMsg:
		m.size = [2]int{msg.Width, msg.Height}
	case ColorProfileMsg:
		m.prof = msg.Profile
	case customMsg:
		m.custom = append(append([]string{}, m.custom...), string(msg))
	}
	return m, nil
}

func (m counter) View() string { return fmt.Sprintf("n=%d", m.n) }

// 머리에서 손으로 돌려 보는 대신, 짧은 시간 안에 끝나는지 확인하며 돌린다.
func run(t *testing.T, m Model, in string, opts ...Option) (Model, string) {
	t.Helper()
	var out bytes.Buffer
	all := append([]Option{
		WithInput(strings.NewReader(in)),
		WithOutput(&out),
		WithWindowSize(80, 24),
	}, opts...)
	p := NewProgram(m, all...)

	type res struct {
		m   Model
		err error
	}
	ch := make(chan res, 1)
	go func() {
		fm, err := p.Run()
		ch <- res{fm, err}
	}()
	select {
	case r := <-ch:
		if r.err != nil {
			t.Fatalf("Run: %v", r.err)
		}
		return r.m, out.String()
	case <-time.After(3 * time.Second):
		p.Kill()
		t.Fatal("3초 안에 안 끝났다")
		return nil, ""
	}
}

// ── 루프의 기본 ─────────────────────────────────────────────────────

// 사건이 오면 Update 가 불리고, 돌려받은 모델이 다음 사건의 입력이 된다.
func TestLoopUpdatesModel(t *testing.T) {
	m, _ := run(t, counter{}, "\x1b[A\x1b[A\x1b[Bq")
	c := m.(counter)
	if c.n != 1 {
		t.Errorf("n = %d, 원하는 값 1 (위 두 번, 아래 한 번)", c.n)
	}
	want := []string{"up", "up", "down", "q"}
	if strings.Join(c.keys, ",") != strings.Join(want, ",") {
		t.Errorf("키 = %v, 원하는 값 %v", c.keys, want)
	}
}

// 입력이 끝나면(EOF) 프로그램도 끝난다. q 를 안 눌러도 멈춰야 한다 —
// 안 그러면 파이프로 돌리는 모든 시험이 영원히 매달린다.
func TestEOFEndsProgram(t *testing.T) {
	m, _ := run(t, counter{}, "\x1b[A")
	if m.(counter).n != 1 {
		t.Errorf("n = %d, 원하는 값 1", m.(counter).n)
	}
}

// 시작하자마자 화면 크기와 색 수준을 알려 준다.
// 모델이 첫 View 를 그릴 때 이미 크기를 알고 있어야 하기 때문이다.
func TestInitialMessages(t *testing.T) {
	m, _ := run(t, counter{}, "q", WithColorProfile(style.ANSI256))
	c := m.(counter)
	if c.size != [2]int{80, 24} {
		t.Errorf("크기 = %v, 원하는 값 [80 24]", c.size)
	}
	if c.prof != style.ANSI256 {
		t.Errorf("색 수준 = %v, 원하는 값 %v", c.prof, style.ANSI256)
	}
}

// ── Cmd ─────────────────────────────────────────────────────────────

type initModel struct{ counter }

func (m initModel) Init() Cmd { return func() Msg { return customMsg("init") } }
func (m initModel) Update(msg Msg) (Model, Cmd) {
	inner, cmd := m.counter.Update(msg)
	m.counter = inner.(counter)
	return m, cmd
}

func TestInitCmdRuns(t *testing.T) {
	m, _ := run(t, initModel{}, "q")
	if got := m.(initModel).custom; len(got) != 1 || got[0] != "init" {
		t.Errorf("custom = %v, 원하는 값 [init]", got)
	}
}

type batchModel struct {
	counter
	cmd Cmd
}

func (m batchModel) Init() Cmd { return m.cmd }
func (m batchModel) Update(msg Msg) (Model, Cmd) {
	inner, cmd := m.counter.Update(msg)
	m.counter = inner.(counter)
	return m, cmd
}

func msgCmd(s string) Cmd { return func() Msg { return customMsg(s) } }

// 지연을 넣은 Cmd. Batch 가 정말 동시에 도는지, Sequence 가 정말 차례로 도는지
// 구별하려면 "느린 것을 먼저" 놓아야 한다.
func slowMsgCmd(s string, d time.Duration) Cmd {
	return func() Msg { time.Sleep(d); return customMsg(s) }
}

// Batch 는 한꺼번에 돌린다. 순서는 보장하지 않는다 — 그게 계약이다.
// 그래서 느린 것을 먼저 넣고, 늦게 넣은 빠른 것이 먼저 도착하는지 본다.
func TestBatchIsConcurrentAndUnordered(t *testing.T) {
	cmd := Batch(slowMsgCmd("slow", 80*time.Millisecond), msgCmd("fast"))
	m, _ := run(t, batchModel{cmd: cmd}, "", WithInput(nil), WithQuitAfter(400*time.Millisecond))
	got := m.(batchModel).custom
	if len(got) != 2 {
		t.Fatalf("custom = %v, 원하는 값 두 개", got)
	}
	if got[0] != "fast" || got[1] != "slow" {
		t.Errorf("custom = %v — 동시에 돌았다면 빠른 것이 먼저 온다", got)
	}
}

// Sequence 는 앞의 것이 끝나야 다음 것을 시작한다. 느린 것을 먼저 넣어도 순서가 지켜진다.
func TestSequenceIsOrdered(t *testing.T) {
	cmd := Sequence(slowMsgCmd("first", 60*time.Millisecond), msgCmd("second"), msgCmd("third"))
	m, _ := run(t, batchModel{cmd: cmd}, "", WithInput(nil), WithQuitAfter(400*time.Millisecond))
	got := m.(batchModel).custom
	want := []string{"first", "second", "third"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Errorf("custom = %v, 원하는 값 %v", got, want)
	}
}

// nil Cmd 는 "할 일 없음" 이다. 걸러 내지 않으면 nil 을 부르다 죽는다.
func TestNilCmdsAreIgnored(t *testing.T) {
	cmd := Batch(nil, msgCmd("a"), nil)
	m, _ := run(t, batchModel{cmd: cmd}, "", WithInput(nil), WithQuitAfter(200*time.Millisecond))
	if got := m.(batchModel).custom; len(got) != 1 || got[0] != "a" {
		t.Errorf("custom = %v, 원하는 값 [a]", got)
	}
	if Batch() != nil {
		t.Error("Batch() 가 nil 이 아니다")
	}
	if Sequence() != nil {
		t.Error("Sequence() 가 nil 이 아니다")
	}
}

// Tick 은 **한 번만** 울린다. 되풀이하려면 받은 자리에서 다시 걸어야 한다.
// 이것이 처음 쓰는 사람이 가장 많이 걸려 넘어지는 자리다.
func TestTickFiresOnce(t *testing.T) {
	cmd := Tick(20*time.Millisecond, func(time.Time) Msg { return customMsg("tick") })
	m, _ := run(t, batchModel{cmd: cmd}, "",
		WithInput(nil), WithQuitAfter(200*time.Millisecond))
	if got := m.(batchModel).custom; len(got) != 1 {
		t.Errorf("200 ms 동안 tick 이 %d번 — 한 번이어야 한다: %v", len(got), got)
	}
}

// Every 도 한 번만 울린다. 다만 시각을 시계에 맞춘다.
func TestEveryFiresOnce(t *testing.T) {
	cmd := Every(20*time.Millisecond, func(time.Time) Msg { return customMsg("every") })
	m, _ := run(t, batchModel{cmd: cmd}, "",
		WithInput(nil), WithQuitAfter(200*time.Millisecond))
	if got := m.(batchModel).custom; len(got) != 1 {
		t.Errorf("every 가 %d번: %v", len(got), got)
	}
}

// 되풀이하려면 tick 을 받은 자리에서 다시 건다. 이것이 "재예약" 패턴이다.
type repeatModel struct {
	counter
	d time.Duration
}

func (m repeatModel) Init() Cmd { return m.tick() }
func (m repeatModel) tick() Cmd {
	return Tick(m.d, func(time.Time) Msg { return customMsg("t") })
}
func (m repeatModel) Update(msg Msg) (Model, Cmd) {
	if _, ok := msg.(customMsg); ok {
		inner, _ := m.counter.Update(msg)
		m.counter = inner.(counter)
		return m, m.tick() // ← 다시 건다
	}
	inner, cmd := m.counter.Update(msg)
	m.counter = inner.(counter)
	return m, cmd
}

func TestTickRearmPattern(t *testing.T) {
	m, _ := run(t, repeatModel{d: 15 * time.Millisecond}, "",
		WithInput(nil), WithQuitAfter(200*time.Millisecond))
	if got := len(m.(repeatModel).custom); got < 3 {
		t.Errorf("재예약했는데 %d번만 울렸다", got)
	}
}

// ── 밖에서 밀어 넣기 ────────────────────────────────────────────────

// 프로그램 바깥(웹소켓, 시계, 다른 고루틴)에서 사건을 넣을 수 있어야 한다.
func TestSendFromOutside(t *testing.T) {
	var out bytes.Buffer
	p := NewProgram(counter{},
		WithInput(nil), WithOutput(&out), WithWindowSize(80, 24))

	var wg sync.WaitGroup
	wg.Add(1)
	var final Model
	go func() {
		defer wg.Done()
		final, _ = p.Run()
	}()

	time.Sleep(50 * time.Millisecond)
	p.Send(customMsg("hello"))
	p.Send(customMsg("world"))
	time.Sleep(50 * time.Millisecond)
	p.Quit()
	wg.Wait()

	got := final.(counter).custom
	if len(got) != 2 || got[0] != "hello" || got[1] != "world" {
		t.Errorf("custom = %v, 원하는 값 [hello world]", got)
	}
}

// ── 화면 ────────────────────────────────────────────────────────────

// 렌더러를 달면 View 의 결과가 실제로 바이트로 나간다.
func TestRendererWritesView(t *testing.T) {
	_, out := run(t, counter{}, "\x1b[Aq", WithFPS(200))
	if !strings.Contains(out, "n=1") {
		t.Errorf("화면에 n=1 이 없다: %q", out)
	}
}

// WithoutRenderer 면 화면에 아무것도 안 쓴다. 시험과 기록에 쓰는 모드다.
func TestWithoutRenderer(t *testing.T) {
	_, out := run(t, counter{}, "\x1b[Aq", WithoutRenderer())
	if out != "" {
		t.Errorf("아무것도 안 써야 하는데 %q", out)
	}
}

// ── 정리 ────────────────────────────────────────────────────────────

// 끝날 때 켜 둔 것을 전부 되돌린다. 안 그러면 셸이 망가진 채로 돌아온다.
func TestCleanupOnExit(t *testing.T) {
	_, out := run(t, counter{}, "q", WithAltScreen())
	if !strings.HasSuffix(out, term.ExitAltScreen) {
		t.Errorf("대체 화면을 안 빠져나왔다: %q", out[max(0, len(out)-40):])
	}
}

// Update 에서 패닉이 나도 터미널은 되돌려야 한다.
// 안 그러면 사용자는 원시 모드에 갇힌 셸에서 stty sane 을 쳐야 한다.
type panicModel struct{ counter }

func (m panicModel) Update(msg Msg) (Model, Cmd) {
	if _, ok := msg.(KeyMsg); ok {
		panic("일부러 터뜨린다")
	}
	return m, nil
}

func TestPanicRestoresTerminal(t *testing.T) {
	var out bytes.Buffer
	p := NewProgram(panicModel{},
		WithInput(strings.NewReader("a")), WithOutput(&out),
		WithWindowSize(80, 24), WithAltScreen())

	done := make(chan any, 1)
	go func() {
		defer func() { done <- recover() }()
		p.Run()
	}()

	select {
	case r := <-done:
		if r == nil {
			t.Fatal("패닉이 다시 던져지지 않았다 — 삼켜 버리면 버그가 숨는다")
		}
	case <-time.After(3 * time.Second):
		t.Fatal("3초 안에 안 끝났다")
	}
	if !strings.Contains(out.String(), term.ExitAltScreen) {
		t.Error("패닉 뒤에 대체 화면을 안 빠져나왔다")
	}
}

// ── 값 의미론의 함정 ────────────────────────────────────────────────

// Update 는 고친 **복사본** 을 돌려줘야 한다. 값 수신자에 대고 필드를 고친 뒤
// 원래 모델을 돌려주면 그 변경은 사라진다. 처음 쓰는 사람이 반드시 한 번은 겪는 버그다.
type forgetful struct{ n int }

func (m forgetful) Init() Cmd { return nil }
func (m forgetful) Update(msg Msg) (Model, Cmd) {
	if k, ok := msg.(KeyMsg); ok {
		if k.String() == "q" {
			return m, Quit
		}
		m.n++                   // 복사본을 고쳤는데
		return forgetful{}, nil // 엉뚱한 것을 돌려준다
	}
	return m, nil
}
func (m forgetful) View() string { return fmt.Sprintf("%d", m.n) }

func TestForgettingToReturnTheCopyLosesChanges(t *testing.T) {
	m, _ := run(t, forgetful{}, "aaaq")
	if got := m.(forgetful).n; got != 0 {
		t.Errorf("n = %d — 이 시험은 '변경이 사라진다' 는 것을 못박는다", got)
	}
}
