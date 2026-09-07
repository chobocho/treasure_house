//go:build linux

package term

import "syscall"

// termios 를 읽고 쓰는 ioctl 요청 번호. 이름과 값이 운영체제마다 다르다.
// 리눅스는 TCGETS/TCSETS, macOS 는 TIOCGETA/TIOCSETA 다 — 하는 일은 같다.
const (
	ioctlGetTermios = syscall.TCGETS
	ioctlSetTermios = syscall.TCSETS
)
