//go:build linux || darwin

package term

import "syscall"

// winsize 는 커널이 TIOCGWINSZ 로 채워 주는 구조체다.
//
// syscall 패키지에 Winsize 가 있을 것 같지만 리눅스에는 없다. 그래서 직접 적는다 —
// 커널이 기대하는 배치(16비트 넷)를 그대로 맞추기만 하면 된다.
// Xpixel/Ypixel 은 픽셀 크기인데, 요즘 터미널 에뮬레이터는 대개 0 을 준다.
type winsize struct{ Row, Col, Xpixel, Ypixel uint16 }

// dims 는 winsize 를 (칸, 줄) 로 바꾼다.
//
// 0 을 거르는 이유: 터미널에 붙어 있지 않은 pty(예: 파이프에 물린 tmux 창)는
// ioctl 이 성공하면서 0×0 을 채워 준다. 그걸 그대로 믿으면 렌더러가 0줄짜리 화면에
// 그리려다 아무것도 못 그린다. 크기를 모른다는 것은 오류로 알리고,
// 부르는 쪽이 80×24 로 물러서게 하는 편이 정직하다.
func (w winsize) dims() (int, int, error) {
	if w.Col == 0 || w.Row == 0 {
		return 0, 0, ErrNotTerminal
	}
	return int(w.Col), int(w.Row), nil
}

// makeRawTermios 는 termios 구조체를 원시 모드 값으로 바꾼다.
//
// "원시 모드" 는 새 모드로 갈아 끼우는 것이 아니라, 커널이 대신 해 주던 친절을
// 하나씩 끄는 일이다. 우리가 끄는 친절이 정확히 무엇인지가 이 함수의 전부다.
// 사용자가 설정해 둔 나머지(전송 속도, 다른 특수문자)는 손대지 않는다.
func makeRawTermios(t *syscall.Termios) {
	// 들어오는 바이트 가공 끄기.
	//   IXON   Ctrl+S/Ctrl+Q 를 출력 흐름 제어로 가로챈다 → 우리에겐 그냥 키다
	//   ICRNL  엔터(0x0D)를 줄바꿈(0x0A)으로 바꿔 준다 → 캐리지 리턴 그대로 받고 싶다
	//   BRKINT 브레이크 신호를 SIGINT 로 바꾼다
	//   INPCK  패리티 검사, ISTRIP 8번째 비트 지우기 → UTF-8 이 통째로 망가진다
	t.Iflag &^= syscall.IXON | syscall.ICRNL | syscall.BRKINT | syscall.INPCK | syscall.ISTRIP

	// 나가는 바이트 가공 끄기.
	//   OPOST  "\n" 을 "\r\n" 으로 바꿔 준다. 커서를 우리가 직접 옮기는 이상
	//          이 친절은 한 칸 어긋남으로만 돌아온다.
	t.Oflag &^= syscall.OPOST

	// 줄 편집 끄기 — 원시 모드라는 이름이 붙은 진짜 이유.
	//   ICANON 엔터를 칠 때까지 모아 두는 "줄 단위" 를 끈다 → 한 글자씩 즉시 온다
	//   ECHO   친 글자를 커널이 되비추는 것을 끈다 → 무엇을 보일지는 우리가 정한다
	//   ISIG   Ctrl+C/Ctrl+Z 를 신호로 바꾸는 것을 끈다 → 0x03 바이트로 받는다
	//   IEXTEN Ctrl+V(다음 글자를 그대로) 같은 확장 처리를 끈다
	t.Lflag &^= syscall.ECHO | syscall.ICANON | syscall.ISIG | syscall.IEXTEN

	// 글자 크기를 8비트로 못박는다. 7비트로 남아 있으면 한글의 한 바이트가 잘린다.
	t.Cflag &^= syscall.CSIZE | syscall.PARENB
	t.Cflag |= syscall.CS8

	// 읽기 조건. VMIN=1 은 "1바이트라도 오면 즉시 돌려줘라",
	// VTIME=0 은 "시간 제한 없이 기다려라". VMIN=0 으로 두면 read 가 0바이트로
	// 곧장 돌아와 바쁜 대기가 되고, CPU 하나를 통째로 태운다.
	t.Cc[syscall.VMIN] = 1
	t.Cc[syscall.VTIME] = 0
}
