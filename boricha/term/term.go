package term

import (
	"errors"
	"io"
	"os"
	"sync"
)

// ErrUnsupported 는 이 운영체제에 그 기능을 위한 길이 없을 때.
// ErrNotTerminal 은 길은 있지만 상대가 터미널이 아닐 때(파이프·버퍼·파일).
//
// 둘을 나눈 이유: 앞의 것은 "여기서는 안 된다"라 프로그램이 포기해야 하고,
// 뒤의 것은 "지금 이 입출력이 터미널이 아니다"라 80×24 같은 기본값으로 물러서면 된다.
var (
	ErrUnsupported = errors.New("term: 이 플랫폼에서는 지원하지 않는다")
	ErrNotTerminal = errors.New("term: 터미널이 아니다")
)

// Term 은 터미널 장치 하나를 감싼다.
//
// 왜 io.Reader/io.Writer 를 받는가. 터미널에 시키는 일의 대부분은 "정해진 바이트를
// 내보내는 것"이라, 상대가 진짜 터미널일 필요가 없다. 버퍼를 주면 그대로 테스트가 되고,
// 나중에 testkit 이 가짜 터미널을 만들 때도 이 문이 그대로 쓰인다.
// 파일 서술자가 있어야만 되는 일(원시 모드·크기 질의)만 *os.File 을 따로 붙잡아 둔다.
type Term struct {
	in  io.Reader
	out io.Writer

	inFile  *os.File // 원시 모드는 읽는 쪽 tty 의 줄 규율(line discipline)을 바꾸는 일이다
	outFile *os.File // 크기는 쓰는 쪽에 묻는 것이 관례다

	mu    sync.Mutex
	saved *rawState // MakeRaw 직전의 termios. nil 이면 원시 모드로 들어간 적이 없다.

	// 켜 놓은 모드들. Cleanup 이 "켠 것만, 켠 순서의 역순으로" 되돌리기 위해 기억한다.
	alt, hidden, paste, focus bool
	mouse                     int // 0=꺼짐, 1=1002(버튼), 2=1003(모든 움직임)
}

// New 는 입출력 한 쌍을 감싼 Term 을 만든다. 보통은 New(os.Stdin, os.Stdout).
func New(in io.Reader, out io.Writer) *Term {
	t := &Term{in: in, out: out}
	if f, ok := in.(*os.File); ok {
		t.inFile = f
	}
	if f, ok := out.(*os.File); ok {
		t.outFile = f
	}
	return t
}

// Reader 는 감싸고 있는 입력. 입력 파서가 여기서 바이트를 읽는다.
func (t *Term) Reader() io.Reader { return t.in }

// WriteString 은 시퀀스나 화면 조각을 그대로 내보낸다.
func (t *Term) WriteString(s string) error {
	if s == "" {
		return nil
	}
	_, err := io.WriteString(t.out, s)
	return err
}

// IsTTY 는 이 입력이 진짜 터미널인지 묻는다.
// 판별법은 "termios 를 읽어 보고 되는지" 다 — 터미널만이 그 질문에 답한다.
func (t *Term) IsTTY() bool { return t.isTTY() }

// MakeRaw 는 터미널을 원시 모드로 바꾸고, 되돌릴 상태를 안에 저장한다.
// 이미 원시 모드면 아무 일도 하지 않는다.
func (t *Term) MakeRaw() error {
	t.mu.Lock()
	defer t.mu.Unlock()
	if t.saved != nil {
		return nil
	}
	return t.makeRaw()
}

// Restore 는 MakeRaw 이전 상태로 되돌린다.
//
// 이 함수는 defer 로 걸어 두라고 만든 것이다. 그래서 원시 모드로 들어간 적이 없으면
// 조용히 아무 일도 하지 않는다 — 어느 경로로 빠져나가든 defer 를 그대로 둘 수 있게.
func (t *Term) Restore() error {
	t.mu.Lock()
	defer t.mu.Unlock()
	if t.saved == nil {
		return nil
	}
	return t.restore()
}

// Size 는 화면 크기를 칸×줄로 돌려준다.
func (t *Term) Size() (int, int, error) { return t.size() }

// 아래는 전부 "시퀀스 한 줄 내보내기 + 켰다고 기억하기" 다.
func (t *Term) EnterAltScreen() error { return t.set(&t.alt, true, EnterAltScreen) }
func (t *Term) ExitAltScreen() error  { return t.set(&t.alt, false, ExitAltScreen) }
func (t *Term) HideCursor() error     { return t.set(&t.hidden, true, HideCursor) }
func (t *Term) ShowCursor() error     { return t.set(&t.hidden, false, ShowCursor) }
func (t *Term) EnablePaste() error    { return t.set(&t.paste, true, EnablePaste) }
func (t *Term) DisablePaste() error   { return t.set(&t.paste, false, DisablePaste) }
func (t *Term) EnableFocus() error    { return t.set(&t.focus, true, EnableFocus) }
func (t *Term) DisableFocus() error   { return t.set(&t.focus, false, DisableFocus) }

func (t *Term) set(flag *bool, on bool, seq string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	*flag = on
	return t.WriteString(seq)
}

// EnableMouse 는 마우스 보고를 켠다. all 이 참이면 버튼을 누르지 않은 움직임까지 받는다.
//
// 어느 쪽으로 켰는지 기억해 두는 이유는 DisableMouse 때문이다. 1003 으로 켜 놓고
// 1002 로 끄면 추적이 켜진 채 남아, 프로그램이 끝난 뒤 셸에서 마우스를 움직일 때마다
// 쓰레기 바이트가 쏟아진다.
func (t *Term) EnableMouse(all bool) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	if all {
		t.mouse = 2
		return t.WriteString(EnableMouseAll)
	}
	t.mouse = 1
	return t.WriteString(EnableMouse)
}

// DisableMouse 는 켤 때 쓴 것과 짝이 맞는 시퀀스로 끈다.
func (t *Term) DisableMouse() error {
	t.mu.Lock()
	defer t.mu.Unlock()
	seq := ""
	switch t.mouse {
	case 1:
		seq = DisableMouse
	case 2:
		seq = DisableMouseAll
	}
	t.mouse = 0
	return t.WriteString(seq)
}

// Cleanup 은 켜 둔 모드를 켠 순서의 역순으로 되돌린다.
//
// 역순이 중요하다. 대체 화면을 먼저 빠져나가면, 그 뒤의 "커서 보이기"가 원래 화면에
// 적용되고 대체 화면 쪽 커서는 숨은 채 남는다 — 다음에 그 프로그램을 켜면 커서가 없다.
// 켜지 않은 것은 끄지 않으므로 두 번 불러도 안전하다(멱등).
func (t *Term) Cleanup() error {
	t.mu.Lock()
	defer t.mu.Unlock()
	var first error
	keep := func(err error) {
		if err != nil && first == nil {
			first = err
		}
	}
	if t.focus {
		t.focus = false
		keep(t.WriteString(DisableFocus))
	}
	if t.paste {
		t.paste = false
		keep(t.WriteString(DisablePaste))
	}
	if t.mouse != 0 {
		seq := DisableMouse
		if t.mouse == 2 {
			seq = DisableMouseAll
		}
		t.mouse = 0
		keep(t.WriteString(seq))
	}
	if t.hidden {
		t.hidden = false
		keep(t.WriteString(ShowCursor))
	}
	if t.alt {
		t.alt = false
		keep(t.WriteString(ExitAltScreen))
	}
	return first
}
