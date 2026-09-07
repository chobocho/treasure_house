//go:build linux || darwin

package term

import (
	"syscall"
	"testing"
)

// 원시 모드는 "termios 구조체에서 비트 몇 개를 끄는 일" 이 전부다.
// 진짜 터미널을 열지 않고, 모든 비트가 켜진 가짜 구조체에 함수를 적용해
// 정확히 무엇이 꺼지고 무엇이 켜졌는지 센다.
func TestMakeRawTermios(t *testing.T) {
	// 플래그 필드의 폭은 플랫폼마다 다르다(리눅스 uint32, macOS uint64).
	// 0 을 뒤집어 "전부 1" 을 만들면 어느 쪽에서도 그대로 컴파일된다.
	var raw syscall.Termios
	raw.Iflag = ^raw.Iflag
	raw.Oflag = ^raw.Oflag
	raw.Cflag = ^raw.Cflag
	raw.Lflag = ^raw.Lflag
	makeRawTermios(&raw)

	// 입력 가공 끄기 — Ctrl+S/Ctrl+Q 흐름 제어(IXON), 엔터를 줄바꿈으로 바꾸기(ICRNL),
	// Ctrl+C 를 신호로 만들기 전 단계의 브레이크 처리(BRKINT), 패리티(INPCK/ISTRIP)
	for _, c := range []struct {
		name string
		bit  uint64
	}{
		{"IXON", syscall.IXON}, {"ICRNL", syscall.ICRNL}, {"BRKINT", syscall.BRKINT},
		{"INPCK", syscall.INPCK}, {"ISTRIP", syscall.ISTRIP},
	} {
		if uint64(raw.Iflag)&c.bit != 0 {
			t.Errorf("Iflag 의 %s 가 아직 켜져 있다", c.name)
		}
	}
	// 출력 가공 끄기 — "\n" 을 "\r\n" 으로 바꿔 주는 친절(OPOST)을 끈다.
	// 커서를 직접 옮기는 우리에겐 그 친절이 한 칸 어긋남으로 돌아온다.
	if uint64(raw.Oflag)&syscall.OPOST != 0 {
		t.Error("Oflag 의 OPOST 가 아직 켜져 있다")
	}
	// 줄 편집 끄기 — 엔터를 기다리지 않고(ICANON), 친 글자를 되비추지 않고(ECHO),
	// Ctrl+C 를 신호가 아니라 바이트 0x03 으로 받고(ISIG), Ctrl+V 같은 확장도 끈다(IEXTEN).
	for _, c := range []struct {
		name string
		bit  uint64
	}{
		{"ICANON", syscall.ICANON}, {"ECHO", syscall.ECHO},
		{"ISIG", syscall.ISIG}, {"IEXTEN", syscall.IEXTEN},
	} {
		if uint64(raw.Lflag)&c.bit != 0 {
			t.Errorf("Lflag 의 %s 가 아직 켜져 있다", c.name)
		}
	}
	// 한 글자는 8비트. CSIZE 를 지우고 CS8 만 남긴다.
	if uint64(raw.Cflag)&uint64(syscall.CSIZE) != uint64(syscall.CS8) {
		t.Errorf("Cflag 의 글자 크기가 CS8 이 아니다: %#x", uint64(raw.Cflag)&uint64(syscall.CSIZE))
	}
	if uint64(raw.Cflag)&syscall.PARENB != 0 {
		t.Error("Cflag 의 PARENB 가 아직 켜져 있다")
	}
	// 읽기 조건: 1바이트라도 오면 바로 돌려주고(VMIN=1), 시간 제한은 두지 않는다(VTIME=0).
	// VMIN=0 으로 두면 read 가 0바이트로 계속 돌아와 CPU 를 태운다.
	if raw.Cc[syscall.VMIN] != 1 {
		t.Errorf("VMIN = %d, 원하는 값 1", raw.Cc[syscall.VMIN])
	}
	if raw.Cc[syscall.VTIME] != 0 {
		t.Errorf("VTIME = %d, 원하는 값 0", raw.Cc[syscall.VTIME])
	}
}

// 우리가 건드리지 않기로 한 비트는 그대로 남아야 한다.
// termios 를 통째로 새로 만들어 넣으면 사용자의 터미널 설정(속도 등)이 날아간다.
func TestMakeRawKeepsUnrelatedFields(t *testing.T) {
	var raw syscall.Termios
	raw.Ispeed = 38400
	raw.Ospeed = 38400
	raw.Cc[0] = 0x7f
	makeRawTermios(&raw)
	if raw.Ispeed != 38400 || raw.Ospeed != 38400 {
		t.Errorf("전송 속도가 바뀌었다: %d/%d", raw.Ispeed, raw.Ospeed)
	}
	if raw.Cc[0] != 0x7f {
		t.Errorf("Cc[0] 이 바뀌었다: %#x", raw.Cc[0])
	}
}

// 크기 질의는 ioctl 이 채워 준 winsize 를 읽는 것뿐이다.
// 커널이 0 을 채워 주는 경우(파이프에 붙은 pty 등)를 오류로 걸러 낸다.
func TestWinsizeToCols(t *testing.T) {
	cases := []struct {
		ws      winsize
		w, h    int
		wantErr bool
	}{
		{winsize{Row: 24, Col: 80}, 80, 24, false},
		{winsize{Row: 50, Col: 132}, 132, 50, false},
		{winsize{Row: 0, Col: 0}, 0, 0, true},
		{winsize{Row: 24, Col: 0}, 0, 0, true},
	}
	for _, c := range cases {
		w, h, err := c.ws.dims()
		if (err != nil) != c.wantErr {
			t.Errorf("%+v: err = %v", c.ws, err)
			continue
		}
		if err == nil && (w != c.w || h != c.h) {
			t.Errorf("%+v = %d×%d, 원하는 값 %d×%d", c.ws, w, h, c.w, c.h)
		}
	}
}
