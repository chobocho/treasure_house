// Package mygit 은 만들면서 배우는 Git 의 Go 구현이다(git/SPEC.md).
//
// Python 구현(py/mygit)과 같은 규격서·같은 golden 으로 시험받는다.
// 표준 라이브러리만 쓰고, SHA-1 은 손으로 짠다(SPEC.md §2).
package mygit

// Step 은 지금까지 만든 부록 A 의 단계다. 장면 시험은 자기 단계가
// 오기 전에는 "N단계에서 켜진다" 는 이유로 건너뛴다.
const Step = 7

// GitError 는 SPEC.md §15 의 오류 한 가지 — 메시지와 종료 코드.
// 출력은 cli 만 한다. 다른 코드는 이것을 돌려줄 뿐이다.
type GitError struct {
	Msg  string
	Code int
}

func (e *GitError) Error() string { return e.Msg }

// Fail 은 코드 128 의 오류를 만든다(git 의 fatal 과 같은 코드).
func Fail(msg string) *GitError { return &GitError{msg, 128} }

// NotImplemented 는 아직 짜지 않은 함수의 껍데기가 던진다(코드 99).
func NotImplemented() *GitError {
	return &GitError{"not implemented", 99}
}
