//go:build windows

package term

// 윈도우의 콘솔은 termios 도 ioctl 도 쓰지 않는다.
// SetConsoleMode 로 ENABLE_VIRTUAL_TERMINAL_PROCESSING 과 ENABLE_VIRTUAL_TERMINAL_INPUT 을
// 켜고, 크기는 GetConsoleScreenBufferInfo 로 얻고, 크기 변경은 신호가 아니라
// 입력 큐의 WINDOW_BUFFER_SIZE_EVENT 로 온다. 즉 이 패키지를 통째로 한 벌 더 써야 한다.
//
// 이 저장소에서는 거기까지 가지 않는다. 대신 "된다고 거짓말하지 않는" 스텁을 둔다 —
// 컴파일은 되고, 터미널을 만지려는 순간 ErrUnsupported 로 정직하게 거절한다.
type rawState struct{}

func (t *Term) isTTY() bool { return false }

func (t *Term) makeRaw() error { return ErrUnsupported }

func (t *Term) restore() error { return ErrUnsupported }

func (t *Term) size() (int, int, error) { return 0, 0, ErrUnsupported }

// NotifyResize 는 아무 일도 하지 않는다. 창 크기는 처음 한 번만 알 수 있다.
func (t *Term) NotifyResize(ch chan<- struct{}) (stop func()) { return func() {} }
