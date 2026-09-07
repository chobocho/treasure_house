package tea

import (
	"io"
	"time"

	"treasure/boricha/style"
)

// Option 은 Program 을 만들 때 켜고 끄는 것들이다.
//
// 왜 함수인가. 설정 구조체를 받으면 필드가 늘 때마다 부르는 쪽이 다 깨지거나,
// 안 쓰는 필드를 0으로 채워 넣어야 한다. 함수로 두면 필요한 것만 적으면 되고,
// 기본값이 "아무것도 안 적었을 때" 로 자연스럽게 정해진다.
type Option func(*options)

type options struct {
	in  io.Reader
	out io.Writer

	altScreen bool
	mouse     int // 0 안 씀, 1 버튼만, 2 움직임까지
	paste     bool
	focus     bool

	noRenderer bool
	fps        int
	sync       bool

	w, h        int
	profile     *style.Profile
	escTimeout  time.Duration
	catchPanics bool
	quitAfter   time.Duration
}

// WithInput 은 읽을 곳을 바꾼다. nil 을 주면 입력을 아예 받지 않는다
// (밖에서 Send 로만 움직이는 프로그램, 또는 기록용).
func WithInput(r io.Reader) Option { return func(o *options) { o.in = r } }

// WithOutput 은 그릴 곳을 바꾼다. 버퍼를 주면 화면 없이 시험할 수 있다.
func WithOutput(w io.Writer) Option { return func(o *options) { o.out = w } }

// WithAltScreen 은 대체 화면 버퍼를 쓴다. 프로그램이 끝나면 셸 화면이 그대로 돌아온다.
func WithAltScreen() Option { return func(o *options) { o.altScreen = true } }

// WithMouse 는 버튼 사건과 끌기를 받는다.
func WithMouse() Option { return func(o *options) { o.mouse = 1 } }

// WithMouseAllMotion 은 버튼을 안 눌러도 움직임을 전부 받는다.
// 사건이 훨씬 많아지므로 정말 필요할 때만 켠다.
func WithMouseAllMotion() Option { return func(o *options) { o.mouse = 2 } }

// WithBracketedPaste 는 붙여넣기를 한 덩어리로 받는다.
// 켜지 않으면 붙여넣은 여러 줄이 "엔터를 여러 번 친 것" 과 구별되지 않는다.
func WithBracketedPaste() Option { return func(o *options) { o.paste = true } }

// WithFocusReporting 은 창이 앞뒤로 오갈 때 FocusMsg/BlurMsg 를 받는다.
func WithFocusReporting() Option { return func(o *options) { o.focus = true } }

// WithoutRenderer 는 화면에 아무것도 안 쓴다. 시험과 기록에 쓴다.
func WithoutRenderer() Option { return func(o *options) { o.noRenderer = true } }

// WithFPS 는 초당 몇 번까지 그릴지 정한다. 기본은 60이다.
func WithFPS(n int) Option { return func(o *options) { o.fps = n } }

// WithSyncOutput 은 한 프레임을 동기화 출력(DEC 2026)으로 감싼다.
func WithSyncOutput() Option { return func(o *options) { o.sync = true } }

// WithWindowSize 는 크기를 못박는다. 터미널이 아닌 곳(시험·기록)에서 쓴다.
func WithWindowSize(w, h int) Option { return func(o *options) { o.w, o.h = w, h } }

// WithColorProfile 은 색 수준을 못박는다. 안 주면 환경 변수를 보고 정한다.
func WithColorProfile(p style.Profile) Option { return func(o *options) { o.profile = &p } }

// WithEscTimeout 은 ESC 하나를 esc 키로 확정하기까지 기다릴 시간을 바꾼다.
func WithEscTimeout(d time.Duration) Option { return func(o *options) { o.escTimeout = d } }

// WithoutCatchPanics 는 패닉을 가로채지 않는다.
//
// 기본은 가로채는 쪽이다. 가로채지 않으면 원시 모드인 채로 프로세스가 죽고,
// 사용자는 글자가 안 보이고 엔터도 안 먹는 셸 앞에서 stty sane 을 쳐야 한다.
// 다만 디버거를 붙여 쓸 때는 가로채지 않는 편이 낫다.
func WithoutCatchPanics() Option { return func(o *options) { o.catchPanics = false } }

// WithQuitAfter 는 정해진 시간이 지나면 스스로 끝낸다.
// 사람 없이 화면을 기록할 때(tools/record, 시험) 쓰려고 둔 것이다.
func WithQuitAfter(d time.Duration) Option { return func(o *options) { o.quitAfter = d } }
