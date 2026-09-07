package tea

import (
	"fmt"
	"strings"
	"testing"
)

// 이 파일은 "Program 없이 모델만 시험하기" 를 보이는 예다.
//
// Update 와 View 는 그냥 함수다. 터미널도, 고루틴도, 시계도 없이 그대로 부를 수 있고,
// 그래서 이런 시험은 마이크로초 안에 끝나고 어떤 기계에서도 같은 결과를 낸다.
//
// 아래 모델은 이 파일 안에서만 쓰는 가장 작은 예다 — examples/02_counter 를 줄인 것.
type demoCounter struct{ n int }

func (m demoCounter) Init() Cmd { return nil }

func (m demoCounter) Update(msg Msg) (Model, Cmd) {
	if k, ok := msg.(KeyMsg); ok {
		switch k.String() {
		case "q":
			return m, Quit
		case "up":
			m.n++
		case "down":
			m.n--
		}
	}
	return m, nil
}

func (m demoCounter) View() string { return fmt.Sprintf("셈: %d", m.n) }

// 상태 전이 하나를 확인한다. 사건 하나를 넣고 나온 모델을 본다.
func TestUpArrowIncrements(t *testing.T) {
	m := demoCounter{n: 0}

	next, cmd := m.Update(KeyMsg{Code: KeyUp})

	if got := next.(demoCounter).n; got != 1 {
		t.Errorf("n = %d, 원하는 값 1", got)
	}
	if cmd != nil {
		t.Error("할 일이 없어야 한다")
	}
	// 원본은 그대로다 — 모델이 값이라는 것이 여기서 보인다.
	if m.n != 0 {
		t.Errorf("원본이 바뀌었다: %d", m.n)
	}
}

// 화면을 시험하는 데 화면이 필요 없다. View 가 문자열을 돌려주기 때문이다.
func TestViewShowsCount(t *testing.T) {
	got := demoCounter{n: 42}.View()
	if !strings.Contains(got, "42") {
		t.Errorf("화면에 42 가 없다: %q", got)
	}
}

// 끝내는 키는 Quit 명령을 돌려준다. 명령을 직접 불러 무엇이 나오는지 볼 수 있다.
func TestQuitKeyReturnsQuitCmd(t *testing.T) {
	_, cmd := demoCounter{}.Update(KeyMsg{Code: 'q', Text: "q"})
	if cmd == nil {
		t.Fatal("q 에 아무 명령도 안 돌려줬다")
	}
	if _, ok := cmd().(QuitMsg); !ok {
		t.Errorf("= %#v, 원하는 값 QuitMsg", cmd())
	}
}
