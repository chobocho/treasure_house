//go:build darwin

package term

import "syscall"

// macOS 쪽 이름. 리눅스의 TCGETS/TCSETS 와 같은 일을 한다.
//
// 이 파일은 이 저장소를 만든 기계(android/arm64)에서 **돌려 본 적이 없다**.
// GOOS=darwin 으로 컴파일이 되는 것까지만 확인했다. 덱에서도 그렇게 적어 둔다.
const (
	ioctlGetTermios = syscall.TIOCGETA
	ioctlSetTermios = syscall.TIOCSETA
)
