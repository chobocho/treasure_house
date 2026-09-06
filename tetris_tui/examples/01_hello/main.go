// 01_hello — Bubble Tea 프로그램의 최소 형태.
//
// 이 예제의 목적은 단 하나다: "모델 하나 + 메서드 셋"이 전부라는 것을 보이는 것.
// 상태를 바꾸는 코드도, 그리는 코드도 없다. 그런데도 이건 완전한 TUI 프로그램이다.
//
//	go run ./examples/01_hello
package main

import (
	"fmt"
	"os"

	tea "charm.land/bubbletea/v2"
)

// model 은 프로그램의 상태 전부다.
// 필드가 없어도 된다 — Bubble Tea 가 요구하는 건 "타입"이지 "내용"이 아니다.
type model struct {
	// 종료 직전에 한 번 더 그려지는 화면을 위해 남긴다.
	// (Quit 을 돌려주면 마지막 View 가 렌더된 뒤에 프로그램이 내려간다)
	quitting bool
}

// Init 은 프로그램이 시작될 때 딱 한 번 불린다.
// 처음부터 시킬 일(타이머 걸기·파일 읽기 등)이 있으면 여기서 Cmd 로 돌려준다.
// 할 일이 없으면 nil. 이 예제는 할 일이 없다.
func (m model) Init() tea.Cmd { return nil }

// Update 는 메시지가 올 때마다 불린다. 키 입력도, 창 크기 변화도, 타이머도
// 전부 "메시지"라는 한 종류의 사건으로 들어온다 — 이게 Elm 아키텍처의 핵심이다.
//
// 반환값이 (Model, Cmd) 인 것에 주의. 모델을 *바꿔서 돌려준다*. 필드를 제자리에서
// 고치는 게 아니다 — m 은 값 복사본이라 여기서 고쳐 봐야 호출자에게 안 돌아간다.
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		// msg.String() 은 "q", "ctrl+c", "left" 같은 사람이 읽는 이름을 준다.
		switch msg.String() {
		case "q", "ctrl+c", "esc":
			m.quitting = true
			// tea.Quit 은 Cmd 다 — 지금 당장 끝내는 게 아니라
			// "끝내라는 메시지를 만들어 달라"는 주문서를 돌려주는 것이다.
			return m, tea.Quit
		}
	}
	return m, nil
}

// View 는 Update 가 끝날 때마다 불려서 화면 전체를 문자열로 만들어 낸다.
// 커서를 옮기거나 지우는 코드는 한 줄도 없다. 우리는 "지금 화면은 이렇게 생겼다"만
// 말하고, 실제로 무엇을 다시 그릴지는 Bubble Tea 가 이전 화면과 비교해서 정한다.
func (m model) View() tea.View {
	if m.quitting {
		return tea.NewView("안녕히 가세요.\n")
	}
	return tea.NewView("Bubble Tea 에 오신 것을 환영합니다!\n\nq 를 누르면 끝납니다.\n")
}

func main() {
	if _, err := tea.NewProgram(model{}).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
