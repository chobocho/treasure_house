//go:build linux || darwin

package term

import (
	"os"
	"os/signal"
	"syscall"
	"unsafe"
)

// rawState 는 원시 모드로 들어가기 직전의 termios 를 통째로 담아 둔 것이다.
// 되돌릴 때 이걸 그대로 다시 써 넣는다 — 어느 비트를 우리가 껐는지 기억할 필요가 없다.
type rawState struct{ termios syscall.Termios }

// ioctl 은 커널에게 "이 장치에 대해 이 요청을 처리해 달라"고 부탁하는 유일한 창구다.
//
// Go 표준 라이브러리에는 터미널 전용 함수가 없다. 그래서 시스템 호출을 직접 부른다.
// arg 는 커널이 읽거나 채워 줄 구조체의 주소다 — 요청 번호마다 무엇을 가리켜야 하는지가
// 정해져 있고, 틀리면 메모리가 조용히 망가진다. 그래서 이 함수는 패키지 밖으로 내보내지 않는다.
func ioctl(fd, req uintptr, arg unsafe.Pointer) error {
	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, fd, req, uintptr(arg)); errno != 0 {
		return errno
	}
	return nil
}

func getTermios(fd uintptr) (syscall.Termios, error) {
	var t syscall.Termios
	err := ioctl(fd, ioctlGetTermios, unsafe.Pointer(&t))
	return t, err
}

func setTermios(fd uintptr, t *syscall.Termios) error {
	return ioctl(fd, ioctlSetTermios, unsafe.Pointer(t))
}

// isTTY 는 termios 를 읽어 보고 되는지로 판별한다.
// 터미널만이 이 질문에 답한다 — 파일도 파이프도 ENOTTY 로 거절한다.
func (t *Term) isTTY() bool {
	if t.inFile == nil {
		return false
	}
	_, err := getTermios(t.inFile.Fd())
	return err == nil
}

func (t *Term) makeRaw() error {
	if t.inFile == nil {
		return ErrNotTerminal
	}
	fd := t.inFile.Fd()
	old, err := getTermios(fd)
	if err != nil {
		return ErrNotTerminal
	}
	raw := old // 값 복사 — old 는 되돌릴 원본으로 그대로 둬야 한다
	makeRawTermios(&raw)
	if err := setTermios(fd, &raw); err != nil {
		return err
	}
	t.saved = &rawState{termios: old}
	return nil
}

func (t *Term) restore() error {
	fd := t.inFile.Fd()
	err := setTermios(fd, &t.saved.termios)
	// 되돌리기에 실패해도 저장본은 버린다. 실패한 상태를 계속 붙들고 있으면
	// 두 번째 Restore 가 같은 실패를 되풀이할 뿐이다.
	t.saved = nil
	return err
}

// size 는 크기를 쓰는 쪽에 묻는다. 출력이 파일이 아니면(리다이렉트) 읽는 쪽으로 물러선다.
func (t *Term) size() (int, int, error) {
	f := t.outFile
	if f == nil {
		f = t.inFile
	}
	if f == nil {
		return 0, 0, ErrNotTerminal
	}
	var ws winsize
	if err := ioctl(f.Fd(), syscall.TIOCGWINSZ, unsafe.Pointer(&ws)); err != nil {
		return 0, 0, ErrNotTerminal
	}
	return ws.dims()
}

// NotifyResize 는 창 크기가 바뀔 때마다 ch 에 신호를 넣는다.
// 돌려주는 함수를 부르면 구독을 끊는다.
//
// 터미널은 크기가 바뀌었다고 바이트를 보내 주지 않는다. 대신 커널이 SIGWINCH 신호를
// 보낸다 — 입력 흐름 밖에서 오는 유일한 사건이라, 파서가 아니라 여기서 받는다.
// ch 가 꽉 차 있으면 그냥 버린다: 크기 변경은 "마지막 값만 맞으면 되는" 사건이고,
// 창을 드래그하는 동안 수십 번 오는 신호를 다 큐에 쌓을 이유가 없다.
func (t *Term) NotifyResize(ch chan<- struct{}) (stop func()) {
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGWINCH)
	done := make(chan struct{})
	go func() {
		for {
			select {
			case <-sig:
				select {
				case ch <- struct{}{}:
				default:
				}
			case <-done:
				return
			}
		}
	}()
	return func() {
		signal.Stop(sig)
		close(done)
	}
}
