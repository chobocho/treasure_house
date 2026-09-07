package testkit

import (
	"strings"

	"treasure/boricha/input"
	"treasure/boricha/render"
	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/width"
)

// Options 는 각본을 돌릴 조건이다. 각본 안의 크기 지정이 여기 값을 덮어쓴다.
type Options struct {
	Cols, Rows int
	Profile    style.Profile
}

// Result 는 각본을 돌린 결과다.
type Result struct {
	// Frames 는 걸음마다 남긴 화면이다. 각 프레임은 Rows 줄 × Cols 칸이다.
	Frames []string
	// Labels 는 그 프레임을 만든 걸음의 이름이다. 재생기의 설명줄에 그대로 쓴다.
	// Frames 와 길이가 같다는 것이 계약이다.
	Labels []string
	// Final 은 각본이 끝났을 때의 모델.
	Final      tea.Model
	Cols, Rows int
}

// RunScript 는 80×24, 256색으로 각본을 돌린다.
func RunScript(m tea.Model, script string) (Result, error) {
	return Run(m, script, Options{Cols: 80, Rows: 24, Profile: style.ANSI256})
}

// Run 은 각본대로 모델을 돌리고 걸음마다 화면을 남긴다.
//
// Program 과 다른 점은 딱 둘이다.
//
//	① 명령을 고루틴이 아니라 **그 자리에서 차례로** 돌린다.
//	   그래서 Batch 도 적힌 순서대로 돈다 — 진짜 Program 은 동시에 돌린다.
//	   이것이 결정론의 대가다. 대신 두 번 돌리면 바이트까지 같다.
//	② 시계가 없다. 명령이 돌 틈은 각본의 기다리기(.N)가 준다.
//	   그래서 스스로를 재예약하는 시계를 넣어도 각본은 반드시 끝난다.
//
// 입력은 진짜 바이트로 만들어 진짜 파서(input.Decoder)에 넣는다.
// 파서를 건너뛰고 KeyMsg 를 바로 만들면, 파서에 있는 버그를 이 도구로는 영영 못 찾는다.
func Run(m tea.Model, script string, o Options) (Result, error) {
	steps, err := Parse(script)
	if err != nil {
		return Result{}, err
	}
	cols, rows := o.Cols, o.Rows
	for _, s := range steps {
		if s.Kind == "size" {
			cols, rows = s.W, s.H
		}
	}
	if cols < 1 {
		cols = 80
	}
	if rows < 1 {
		rows = 24
	}

	r := &runner{model: m, cols: cols, rows: rows}

	// 시작 사건은 Program 이 보내는 것과 같은 것, 같은 순서로.
	r.handle(tea.WindowSizeMsg{Width: cols, Height: rows})
	r.handle(tea.ColorProfileMsg{Profile: o.Profile})
	r.push(m.Init())
	r.round()
	r.snap("시작")

	var dec input.Decoder
	for _, s := range steps {
		if r.quit {
			break
		}
		switch s.Kind {
		case "size":
			continue // 걸음이 아니라 설정이다 — 프레임을 남기지 않는다
		case "wait":
			for i := 0; i < s.N; i++ {
				r.round()
				r.snap(".")
			}
			continue
		}
		for _, msg := range dec.Feed(s.Bytes()) {
			r.handle(msg)
		}
		// 각 걸음의 끝은 "더 안 온다" 와 같다. 미뤄 둔 ESC 를 여기서 확정한다.
		for _, msg := range dec.Flush() {
			r.handle(msg)
		}
		r.round()
		r.snap(label(s))
	}

	return Result{Frames: r.frames, Labels: r.labels, Final: r.model, Cols: cols, Rows: rows}, nil
}

// runner 는 Program 의 루프를 시계 없이 다시 쓴 것이다.
type runner struct {
	model      tea.Model
	cols, rows int
	pending    []tea.Cmd
	frames     []string
	labels     []string
	quit       bool
}

func (r *runner) push(c tea.Cmd) {
	if c != nil {
		r.pending = append(r.pending, c)
	}
}

func (r *runner) handle(msg tea.Msg) {
	if r.quit || msg == nil {
		return
	}
	if _, ok := msg.(tea.QuitMsg); ok {
		r.quit = true
		return
	}
	if cmds, ok := tea.Expand(msg); ok {
		// Batch/Sequence 의 내부 신호. 모델에게 주지 않고 명령 줄에 붙인다.
		for _, c := range cmds {
			r.push(c)
		}
		return
	}
	var cmd tea.Cmd
	r.model, cmd = r.model.Update(msg)
	r.push(cmd)
}

// round 는 지금 밀려 있는 명령을 한 차례 돌린다.
//
// 도는 도중에 새로 생긴 명령은 다음 차례로 미룬다. 그러지 않으면 스스로를 재예약하는
// 시계 하나가 이 함수를 영영 못 끝나게 한다.
func (r *runner) round() {
	cmds := r.pending
	r.pending = nil
	for i := 0; i < len(cmds); i++ {
		if r.quit {
			return
		}
		msg := cmds[i]()
		if sub, ok := tea.Expand(msg); ok {
			// Batch/Sequence 는 이번 차례에 이어서 푼다 — 안 그러면 한 겹마다
			// 기다리기가 한 번씩 더 필요해져서 각본이 읽기 어려워진다.
			cmds = append(cmds, sub...)
			continue
		}
		r.handle(msg)
	}
}

// snap 은 지금 화면을 프레임으로 남긴다.
// 자르기와 채우기를 여기서 해 두면, 재생기는 "모든 프레임이 같은 모양" 만 믿으면 된다.
// label 은 걸음을 재생기의 설명줄에 적을 짧은 이름으로 바꾼다.
func label(s Step) string {
	switch s.Kind {
	case "special":
		return "<" + s.Text + ">"
	case "text":
		return "\"" + s.Text + "\""
	}
	return s.Text
}

func (r *runner) snap(label string) {
	f := render.NewFrame(r.model.View(), r.cols, r.rows)
	out := make([]string, r.rows)
	for i := range out {
		out[i] = width.Pad(f.Line(i), r.cols)
	}
	r.frames = append(r.frames, strings.Join(out, "\n"))
	r.labels = append(r.labels, label)
}
