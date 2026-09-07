package tea

import (
	"os"
	"sync"
	"time"

	"treasure/boricha/input"
	"treasure/boricha/render"
	"treasure/boricha/style"
	"treasure/boricha/term"
)

// Program 은 모델 하나를 터미널에서 돌린다.
//
// 안에서 도는 것은 고루틴 셋과 채널 하나다.
//
//	① 입력 고루틴   바이트를 읽어 사건으로 바꿔 msgs 로 보낸다 (input.Reader)
//	② 명령 고루틴들 Cmd 하나가 곧 고루틴 하나. 끝나면 사건을 msgs 로 보낸다
//	③ 주 고루틴     msgs 에서 사건을 하나씩 꺼내 Update 를 부르고 화면을 적어 둔다
//
// 모델을 만지는 것은 ③뿐이다. 그래서 모델에 잠금장치가 필요 없고,
// "Update 가 도는 동안 상태가 바뀌어 있었다" 는 종류의 버그가 아예 생기지 않는다.
// 이것이 Elm 아키텍처를 고른 실질적인 이유다.
type Program struct {
	init Model
	opts options

	msgs     chan Msg
	killed   chan struct{} // Kill 이 닫는다 — 즉시 멈춤
	done     chan struct{} // 정리가 끝나면 닫힌다 — Send 가 매달리지 않게
	finished chan struct{} // Run 이 완전히 돌아오면 닫힌다 — Wait 가 기다린다

	tm   *term.Term
	rend *render.Renderer
	rdr  *input.Reader

	shutOnce sync.Once
	killOnce sync.Once
}

// NewProgram 은 프로그램을 만든다. 아직 아무것도 시작하지 않는다.
func NewProgram(m Model, opts ...Option) *Program {
	o := options{
		in:          os.Stdin,
		out:         os.Stdout,
		fps:         render.DefaultFPS,
		catchPanics: true,
	}
	for _, f := range opts {
		f(&o)
	}
	return &Program{
		init: m,
		opts: o,
		// 넉넉히 버퍼를 둔다. 명령 고루틴이 사건을 보내려는데 주 고루틴이 Update 중이면
		// 버퍼가 없으면 그 자리에서 막힌다 — 잠깐 막히는 것은 괜찮지만,
		// 사건이 몰릴 때(키 반복, 마우스 움직임) 매번 막히면 눈에 띄게 굼떠진다.
		msgs:     make(chan Msg, 128),
		killed:   make(chan struct{}),
		done:     make(chan struct{}),
		finished: make(chan struct{}),
	}
}

// Run 은 프로그램을 돌리고, 끝났을 때의 모델을 돌려준다.
//
// 돌아올 때는 터미널이 반드시 원래대로 되어 있다 — 정상 종료든, 입력이 끊겼든,
// Update 에서 패닉이 났든.
func (p *Program) Run() (Model, error) {
	defer close(p.finished)
	defer p.shutdown()

	// 패닉을 가로채는 defer 는 **마지막에** 건다. defer 는 나중에 건 것이 먼저 돌므로,
	// 이 순서라야 패닉이 났을 때 터미널을 먼저 되돌리고 다시 던질 수 있다.
	if p.opts.catchPanics {
		defer func() {
			if r := recover(); r != nil {
				p.shutdown() // 여러 번 불러도 안전하다
				panic(r)     // 삼키지 않는다. 삼키면 버그가 조용히 숨는다.
			}
		}()
	}

	p.tm = term.New(p.opts.in, p.opts.out)

	if p.tm.IsTTY() {
		if err := p.tm.MakeRaw(); err != nil {
			return p.init, err
		}
	}
	if p.opts.altScreen {
		_ = p.tm.EnterAltScreen()
	}
	if !p.opts.noRenderer {
		// 커서는 우리가 그리는 동안 화면을 돌아다닌다. 보이면 그 자체가 깜빡임이다.
		_ = p.tm.HideCursor()
	}
	switch p.opts.mouse {
	case 1:
		_ = p.tm.EnableMouse(false)
	case 2:
		_ = p.tm.EnableMouse(true)
	}
	if p.opts.paste {
		_ = p.tm.EnablePaste()
	}
	if p.opts.focus {
		_ = p.tm.EnableFocus()
	}

	w, h := p.size()

	prof := style.NoColor
	if p.opts.profile != nil {
		prof = *p.opts.profile
	} else {
		prof = style.DetectProfile(os.Getenv, p.tm.IsTTY())
	}

	if !p.opts.noRenderer {
		p.rend = render.New(p.opts.out, w, h)
		p.rend.SetSync(p.opts.sync)
		p.rend.Start(p.opts.fps)
	}

	if p.opts.in != nil {
		p.rdr = input.NewReader(p.opts.in)
		if p.opts.escTimeout > 0 {
			p.rdr.SetEscTimeout(p.opts.escTimeout)
		}
		p.rdr.Start(p.msgs)
	}

	p.watchResize()

	if p.opts.quitAfter > 0 {
		t := time.AfterFunc(p.opts.quitAfter, func() { p.Send(QuitMsg{}) })
		defer t.Stop()
	}

	// 시작 사건. 버퍼가 있으므로 막히지 않는다.
	// 크기를 먼저 알려 주는 것이 중요하다 — 모델이 첫 View 를 그릴 때 이미 알고 있어야 한다.
	p.msgs <- WindowSizeMsg{Width: w, Height: h}
	p.msgs <- ColorProfileMsg{Profile: prof}

	model := p.init
	if p.rend != nil {
		p.rend.Write(model.View())
	}
	go p.exec(model.Init())

	return p.loop(model)
}

// loop 이 이 패키지의 심장이다. 열 줄이 안 된다 —
// 나머지 코드 전부가 이 열 줄을 단순하게 유지하기 위해 존재한다.
func (p *Program) loop(model Model) (Model, error) {
	for {
		select {
		case msg := <-p.msgs:
			switch m := msg.(type) {
			case QuitMsg:
				return model, nil
			case input.ClosedMsg:
				// 읽을 것이 더 없다. 파이프로 돌릴 때 여기서 끝난다.
				return model, m.Err
			case batchMsg:
				// 내부 신호다. 모델에게 주지 않고 각자 고루틴으로 흩뿌린다.
				for _, c := range m {
					go p.exec(c)
				}
				continue
			case sequenceMsg:
				go p.execSeq(m)
				continue
			case WindowSizeMsg:
				if p.rend != nil {
					p.rend.Resize(m.Width, m.Height)
				}
			}

			var cmd Cmd
			model, cmd = model.Update(msg)
			if p.rend != nil {
				p.rend.Write(model.View())
			}
			if cmd != nil {
				go p.exec(cmd)
			}

		case <-p.killed:
			return model, nil
		}
	}
}

// Send 는 밖에서 사건을 밀어 넣는다. 웹소켓, 다른 고루틴, 신호 처리기에서 쓴다.
//
// Update 안에서 부르면 안 된다. 주 고루틴이 자기 자신을 기다리게 되어,
// 버퍼가 차는 순간 굳는다.
func (p *Program) Send(msg Msg) {
	select {
	case p.msgs <- msg:
	case <-p.done:
	case <-p.killed:
	}
}

// Quit 은 프로그램에게 끝내라고 한다. 남은 정리는 정상적으로 이루어진다.
func (p *Program) Quit() { p.Send(QuitMsg{}) }

// Kill 은 즉시 멈춘다. 처리 중이던 사건은 버려진다. 정리는 그래도 한다.
func (p *Program) Kill() { p.killOnce.Do(func() { close(p.killed) }) }

// Wait 은 Run 이 완전히 끝날 때까지 기다린다.
func (p *Program) Wait() { <-p.finished }

// exec 는 명령 하나를 자기 고루틴에서 돌린다.
func (p *Program) exec(c Cmd) {
	if c == nil {
		return
	}
	if msg := c(); msg != nil {
		p.Send(msg)
	}
}

// execSeq 는 명령들을 차례로 돌린다. 앞의 것이 끝나야 다음이 시작한다.
func (p *Program) execSeq(cmds []Cmd) {
	for _, c := range cmds {
		if c == nil {
			continue
		}
		if msg := c(); msg != nil {
			p.Send(msg)
		}
		select {
		case <-p.done:
			return
		default:
		}
	}
}

func (p *Program) size() (int, int) {
	if p.opts.w > 0 && p.opts.h > 0 {
		return p.opts.w, p.opts.h
	}
	if w, h, err := p.tm.Size(); err == nil {
		return w, h
	}
	// 터미널이 아니거나 크기를 모른다. 80×24 는 VT100 이래의 기본값이고,
	// 지금도 대부분의 터미널이 그 크기로 열린다. 거짓말을 하는 것이 아니라
	// "모를 때의 약속" 을 지키는 것이다.
	return 80, 24
}

// watchResize 는 창 크기가 바뀔 때마다 WindowSizeMsg 를 보낸다.
//
// 크기 변경은 입력 흐름 밖에서 온다 — 터미널이 바이트를 보내는 것이 아니라
// 커널이 SIGWINCH 신호를 보낸다. 그래서 파서가 아니라 여기서 받는다.
func (p *Program) watchResize() {
	if !p.tm.IsTTY() {
		return
	}
	ch := make(chan struct{}, 1)
	stop := p.tm.NotifyResize(ch)
	go func() {
		defer stop()
		for {
			select {
			case <-ch:
				if w, h, err := p.tm.Size(); err == nil {
					p.Send(WindowSizeMsg{Width: w, Height: h})
				}
			case <-p.done:
				return
			case <-p.killed:
				return
			}
		}
	}()
}

// shutdown 은 켜 둔 것을 전부 되돌린다. 몇 번 불러도 한 번만 돈다.
//
// 순서가 중요하다.
//  1. 렌더러를 멈춘다 — 마지막 화면을 한 번 더 그린다("안녕히" 같은 마지막 프레임)
//  2. 켜 둔 모드를 켠 순서의 역순으로 끈다
//  3. 원시 모드를 되돌린다 ← 이것이 마지막이어야 한다
//
// 3번을 먼저 하면 그 뒤에 내보내는 정리 시퀀스가 줄 편집을 거쳐 나가면서
// 화면에 쓰레기를 남긴다.
func (p *Program) shutdown() {
	p.shutOnce.Do(func() {
		close(p.done)
		if p.rdr != nil {
			p.rdr.Close()
		}
		if p.rend != nil {
			p.rend.Stop()
		}
		if p.tm != nil {
			_ = p.tm.Cleanup()
			_ = p.tm.Restore()
		}
	})
}
