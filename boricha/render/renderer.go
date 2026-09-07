package render

import (
	"io"
	"strings"
	"sync"
	"time"

	"treasure/boricha/term"
)

// 기본 갱신 빈도. 사람 눈이 부드럽다고 느끼는 경계이고, 터미널 에뮬레이터가
// 실제로 그려 낼 수 있는 한계이기도 하다. 더 높여도 화면은 달라지지 않고
// CPU 만 더 쓴다.
const DefaultFPS = 60

// Renderer 는 프레임을 받아 달라진 줄만 터미널에 써 보낸다.
//
// Write 와 Flush 를 나눈 이유: Update 는 사건이 올 때마다 불리는데, 그 빈도가
// 화면 갱신 빈도보다 훨씬 높을 수 있다(키를 꾹 누르면 초당 수백 번). 매번 그리면
// 터미널이 따라오지 못한다. 그래서 Write 는 "최신 화면을 적어 두기" 만 하고,
// 실제 출력은 Flush 가 초당 몇 번으로 제한해 내보낸다.
type Renderer struct {
	mu   sync.Mutex
	w    io.Writer
	cols int
	rows int

	last    Frame  // 화면에 지금 그려져 있다고 믿는 것
	pending string // 아직 안 그린 최신 View
	dirty   bool   // 그릴 것이 있는가
	full    bool   // 다음번엔 전부 다시 그린다
	sync    bool   // 동기화 출력(DEC 2026)을 쓸까
	over    bool   // 마지막 프레임이 화면보다 길었나

	stop chan struct{}
	done sync.WaitGroup
}

func New(w io.Writer, cols, rows int) *Renderer {
	return &Renderer{w: w, cols: cols, rows: rows}
}

// SetSync 는 동기화 출력(DEC 사설 모드 2026)을 켠다.
//
// 켜면 한 프레임을 \e[?2026h … \e[?2026l 로 감싸서, 터미널이 프레임을 다 받을 때까지
// 화면 갱신을 미룬다. 반쯤 그려진 화면이 보이는 일(찢어짐)이 사라진다.
// 모르는 터미널은 모르는 모드를 조용히 무시하므로, 켜 두는 것이 손해는 아니다.
func (r *Renderer) SetSync(on bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.sync = on
}

// Resize 는 화면 크기가 바뀌었음을 알린다. 다음 Flush 에서 전부 다시 그린다.
//
// 크기가 바뀌면 지금 화면에 무엇이 남아 있는지 알 수 없다. 터미널이 내용을 밀어 올렸을
// 수도, 잘라 냈을 수도 있다. 그때는 diff 를 믿으면 안 된다.
func (r *Renderer) Resize(cols, rows int) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.cols, r.rows = cols, rows
	r.full = true
	r.dirty = true
}

// Repaint 는 "지금 화면을 못 믿겠다" 는 뜻이다. 다른 프로그램이 화면에 무언가 찍었거나,
// 대체 화면을 드나든 직후에 부른다.
func (r *Renderer) Repaint() {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.full = true
	r.dirty = true
}

// Write 는 그릴 화면을 적어 둔다. 실제 출력은 Flush 가 한다.
func (r *Renderer) Write(view string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.pending = view
	r.dirty = true
}

// Overflowed 는 마지막 프레임이 화면보다 길어서 잘렸는지 알려 준다.
// 프로그램이 이걸 보고 한 번만 알려 줄 수 있다 — 매 프레임 경고하면 그 경고가 화면을 뒤덮는다.
func (r *Renderer) Overflowed() bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.over
}

// Clear 는 화면을 통째로 지우고, 화면이 비었다는 것을 기억한다.
func (r *Renderer) Clear() error {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.last = Frame{}
	r.full = true
	_, err := io.WriteString(r.w, term.ClearScreen+term.CursorHome)
	return err
}

// Flush 는 지금까지 적어 둔 화면을 그린다. 달라진 것이 없으면 한 바이트도 안 내보낸다.
//
// 그 "한 바이트도 안 내보낸다" 가 중요하다. 60 fps 로 도는 프로그램에서 화면이 멈춰 있는
// 대부분의 시간 동안, 이 함수는 비교만 하고 조용히 돌아간다.
func (r *Renderer) Flush() error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if !r.dirty {
		return nil
	}
	r.dirty = false

	f := NewFrame(r.pending, r.cols, r.rows)
	r.over = r.rows > 0 && strings.Count(r.pending, "\n")+1 > r.rows

	old := r.last
	if r.full {
		old = Frame{} // 화면이 비었다고 치면 diff 가 전부를 내놓는다
		r.full = false
	}
	rows := Diff(old, f)
	r.last = f
	if len(rows) == 0 {
		return nil
	}

	// 줄 하나에 12바이트쯤 든다: 커서 이동(최대 8) + 줄 끝 지우기(3) + 내용.
	// 24줄을 다 바꿔도 300바이트 남짓이라, 60 fps 로 내보내도 초당 18 KB 다.
	var b strings.Builder
	b.Grow(len(rows) * (r.cols + 16))
	if r.sync {
		b.WriteString(term.BeginSync)
	}
	for _, i := range rows {
		b.WriteString(term.CursorTo(i+1, 1))
		// 줄 전체를 지우는 \e[2K 가 아니라 커서부터 줄 끝까지인 \e[K 를 쓴다.
		// 커서가 이미 1열에 있으니 결과는 같고, 지운 뒤 곧바로 그 자리에 쓰기 때문에
		// "지워진 줄" 이 화면에 보이는 순간이 없다.
		b.WriteString(term.ClearToEOL)
		b.WriteString(trimForClear(f.Line(i)))
	}
	// 커서를 정해진 자리에 세워 둔다. 어디에 두든 상관없어 보이지만,
	// 커서를 보이게 켜 둔 프로그램(입력창이 있는 앱)에서는 이 자리가 곧 깜빡이는 커서의 위치다.
	park := f.Height()
	if park < 1 {
		park = 1
	}
	b.WriteString(term.CursorTo(park, 1))
	if r.sync {
		b.WriteString(term.EndSync)
	}
	_, err := io.WriteString(r.w, b.String())
	return err
}

// Start 는 초당 fps 번 Flush 하는 고루틴을 띄운다.
//
// 왜 시계를 두는가. Update 는 사건마다 불린다 — 키를 꾹 누르면 초당 수백 번이다.
// 그때마다 그리면 터미널이 못 따라오고, 화면은 어차피 60번밖에 안 바뀐다.
// 시계를 두면 그 사이의 프레임은 자연히 버려지고, 마지막 것만 그려진다.
func (r *Renderer) Start(fps int) {
	if fps <= 0 {
		fps = DefaultFPS
	}
	r.stop = make(chan struct{})
	t := time.NewTicker(time.Second / time.Duration(fps))
	r.done.Add(1)
	go func() {
		defer r.done.Done()
		defer t.Stop()
		for {
			select {
			case <-t.C:
				_ = r.Flush()
			case <-r.stop:
				return
			}
		}
	}()
}

// Stop 은 시계를 멈추고, 마지막 화면을 한 번 더 그린 뒤 돌아온다.
// 마지막 Flush 를 빼먹으면 프로그램이 끝나기 직전의 화면(대개 "안녕히" 같은 인사)이
// 영영 안 보인다.
func (r *Renderer) Stop() {
	if r.stop == nil {
		return
	}
	close(r.stop)
	r.done.Wait()
	r.stop = nil
	_ = r.Flush()
}
