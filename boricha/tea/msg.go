// Package tea 는 터미널 프로그램을 Elm 아키텍처로 쓰게 해 준다.
//
// 프로그램은 세 가지로 이루어진다.
//
//	Model   지금 상태 전부. 값이다.
//	Update  사건 하나를 받아 새 상태와 "다음에 할 일" 을 돌려주는 순수 함수
//	View    상태를 화면 문자열로 그리는 순수 함수
//
// 그 바깥의 모든 지저분한 일 — 원시 모드, 바이트 파싱, 화면 diff, 크기 변경 — 은
// 이 패키지가 맡는다. 쓰는 사람은 "사건 → 상태 → 화면" 만 생각하면 된다.
//
// 이름과 모양은 Bubble Tea 를 그대로 본떴다. 이 덱을 다 읽고 진짜 Bubble Tea 로
// 옮겨 갈 때 손에 익은 것이 그대로 통하게 하려는 것이다.
package tea

import (
	"treasure/boricha/input"
	"treasure/boricha/style"
)

// Msg 는 프로그램에 일어난 일 하나다. 무엇이든 될 수 있다 —
// 키가 눌렸다, 창이 커졌다, HTTP 응답이 왔다, 1초가 지났다.
//
// input.Msg 의 별칭이다. 파서(input)가 tea 를 import 할 수 없기 때문이다(순환).
// 별칭이라 컴파일러에게는 완전히 같은 타입이고, 경계에서 변환이 필요 없다.
type Msg = input.Msg

// 입력 파서가 만드는 사건들을 이 패키지 이름으로도 쓸 수 있게 한다.
// 쓰는 사람이 input 패키지를 알 필요가 없어야 한다.
type (
	Key      = input.Key
	KeyMsg   = input.KeyMsg
	KeyMod   = input.KeyMod
	MouseMsg = input.MouseMsg
	PasteMsg = input.PasteMsg
	FocusMsg = input.FocusMsg
	BlurMsg  = input.BlurMsg

	MouseButton = input.MouseButton
	MouseAction = input.MouseAction
)

// WindowSizeMsg 는 화면 크기다. 프로그램이 시작할 때 한 번, 그 뒤로는 창이 바뀔 때마다 온다.
//
// 시작할 때 반드시 한 번 보낸다는 것이 중요하다. 그래야 모델이 첫 View 를 그릴 때
// 이미 크기를 알고 있다 — "처음 한 프레임만 크기가 0" 이라는 성가신 예외가 사라진다.
type WindowSizeMsg struct{ Width, Height int }

// ColorProfileMsg 는 이 터미널이 낼 수 있는 색 수준이다. 시작할 때 한 번 온다.
// 모델은 이걸 받아 자기 스타일들의 프로필을 정한다.
type ColorProfileMsg struct{ Profile style.Profile }

// QuitMsg 는 "끝내라" 는 사건. 직접 만들기보다 Quit 명령을 쓴다.
type QuitMsg struct{}

// batchMsg 와 sequenceMsg 는 밖으로 내보내지 않는다.
// Batch/Sequence 가 만들어 내는 내부 신호이고, 모델의 Update 에는 전달되지 않는다.
type (
	batchMsg    []Cmd
	sequenceMsg []Cmd
)
