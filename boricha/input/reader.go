package input

import (
	"io"
	"sync"
	"time"
)

// ESC 하나만 와 있을 때 "esc 키였다" 고 판정하기까지 기다리는 시간.
//
// 50 ms 는 타협의 산물이다. 더 짧으면 느린 연결에서 방향키가 esc+[+A 로 쪼개지고,
// 더 길면 사용자가 esc 를 누른 뒤 반응이 굼떠 보인다. 사람이 "즉시" 로 느끼는
// 경계가 대략 100 ms 이므로, 그 절반쯤에 둔다.
const DefaultEscTimeout = 50 * time.Millisecond

// ClosedMsg 는 입력이 끝났다는 사건. Program 은 이걸 받으면 정리하고 끝낸다.
// Err 이 nil 이면 정상적인 EOF 다.
type ClosedMsg struct{ Err error }

// Reader 는 바이트를 읽어 사건 채널로 흘려보낸다.
//
// 고루틴이 둘이다. 하나는 io.Reader 에서 읽기만 하고(막히는 일을 혼자 맡는다),
// 다른 하나는 그 덩어리와 시계를 함께 기다린다. 하나로 합칠 수 없는 이유는
// Read 가 막혀 있는 동안에는 시계를 볼 수 없기 때문이다.
type Reader struct {
	r   io.Reader
	dec Decoder
	esc time.Duration

	closeOnce sync.Once
	done      chan struct{}
}

func NewReader(r io.Reader) *Reader {
	return &Reader{r: r, esc: DefaultEscTimeout, done: make(chan struct{})}
}

// SetEscTimeout 은 ESC 판정 시간을 바꾼다. Start 전에 불러야 한다.
func (rd *Reader) SetEscTimeout(d time.Duration) { rd.esc = d }

// Start 는 읽기를 시작한다. 사건은 out 으로 간다.
func (rd *Reader) Start(out chan<- Msg) {
	chunks := make(chan []byte, 8)

	// (1) 읽기만 하는 고루틴.
	//
	// 여기서 Read 가 막힌다. Close 를 불러도 이 고루틴은 다음 바이트가 올 때까지
	// 깨어나지 못한다 — os.Stdin 의 Read 를 밖에서 끊을 방법이 표준 라이브러리에 없다.
	// Bubble Tea 가 muesli/cancelreader 를 쓰는 이유가 정확히 이것이다.
	// 우리는 그 대신 "프로그램이 끝나는 순간 이 고루틴은 버린다" 를 택했다.
	// 프로세스가 곧 죽으므로 새는 것이 문제가 되지 않는다 — 라이브러리라면 다른 얘기다.
	go func() {
		buf := make([]byte, 256)
		for {
			n, err := rd.r.Read(buf)
			if n > 0 {
				// 복사해서 보낸다. buf 는 다음 Read 가 덮어쓴다.
				c := make([]byte, n)
				copy(c, buf[:n])
				select {
				case chunks <- c:
				case <-rd.done:
					return
				}
			}
			if err != nil {
				select {
				case chunks <- nil: // nil 은 "끝" 이라는 표시
				case <-rd.done:
				}
				return
			}
		}
	}()

	// (2) 덩어리와 시계를 함께 기다리는 고루틴.
	go func() {
		// 멈춰 둔 타이머로 시작한다. 판단을 미룬 바이트가 생겼을 때만 돌린다.
		timer := time.NewTimer(rd.esc)
		if !timer.Stop() {
			<-timer.C
		}
		defer timer.Stop()
		armed := false

		send := func(msgs []Msg) bool {
			for _, m := range msgs {
				select {
				case out <- m:
				case <-rd.done:
					return false
				}
			}
			return true
		}

		for {
			select {
			case c := <-chunks:
				if c == nil {
					// 입력 끝. 미뤄 둔 것을 확정하고 알린다.
					if send(rd.dec.Flush()) {
						send([]Msg{ClosedMsg{}})
					}
					return
				}
				if !send(rd.dec.Feed(c)) {
					return
				}
				// 판단을 미룬 바이트가 남았으면 시계를 건다. 아니면 끈다.
				if armed && !timer.Stop() {
					select {
					case <-timer.C:
					default:
					}
				}
				armed = rd.dec.Pending()
				if armed {
					timer.Reset(rd.esc)
				}
			case <-timer.C:
				armed = false
				if !send(rd.dec.Flush()) {
					return
				}
			case <-rd.done:
				return
			}
		}
	}()
}

// Close 는 사건 보내기를 멈춘다. 여러 번 불러도 안전하다.
func (rd *Reader) Close() {
	rd.closeOnce.Do(func() { close(rd.done) })
}
