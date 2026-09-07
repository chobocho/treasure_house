package tea

import (
	"io"
	"log"
	"os"
	"time"
)

// Cmd 는 "다음에 할 일" 이다. 다른 고루틴에서 실행되고, 끝나면 사건 하나를 돌려준다.
//
// 왜 이런 것이 필요한가. Update 는 순수해야 한다 — 같은 사건에 늘 같은 결과를 내야
// 시험할 수 있다. 그런데 파일을 읽거나 시계를 보거나 HTTP 를 부르는 일은 순수하지 않다.
// 그래서 Update 는 그 일을 **직접 하지 않고**, "이 일을 해 달라" 는 함수를 돌려준다.
// 실제로 하는 것은 Program 이고, 결과는 다시 사건이 되어 Update 로 돌아온다.
//
// nil 은 "할 일 없음" 이다. 그래서 Update 의 두 번째 반환값을 nil 로 두는 것이 정상이다.
type Cmd func() Msg

// Quit 은 프로그램을 끝낸다. Cmd 로 그대로 쓴다:
//
//	return m, tea.Quit
func Quit() Msg { return QuitMsg{} }

// Batch 는 여러 일을 **한꺼번에** 시킨다. 순서는 보장하지 않는다 —
// 각자 자기 고루틴에서 돌고, 먼저 끝난 것의 사건이 먼저 온다.
//
// nil 은 걸러 낸다. 조건에 따라 명령을 넣거나 빼는 코드를 쓸 때
// tea.Batch(cmdA, maybeNil, cmdC) 를 그냥 쓸 수 있게 하려는 것이다.
func Batch(cmds ...Cmd) Cmd {
	valid := make([]Cmd, 0, len(cmds))
	for _, c := range cmds {
		if c != nil {
			valid = append(valid, c)
		}
	}
	switch len(valid) {
	case 0:
		return nil
	case 1:
		return valid[0] // 하나면 감쌀 이유가 없다
	}
	return func() Msg { return batchMsg(valid) }
}

// Sequence 는 여러 일을 **차례로** 시킨다. 앞의 것이 끝나야 다음이 시작한다.
//
// Batch 와 갈라 쓰는 기준: 결과가 서로를 기다려야 하면 Sequence,
// 아니면 Batch 다. 애니메이션처럼 "이것 끝나고 저것" 이 필요할 때가 Sequence 다.
func Sequence(cmds ...Cmd) Cmd {
	valid := make([]Cmd, 0, len(cmds))
	for _, c := range cmds {
		if c != nil {
			valid = append(valid, c)
		}
	}
	switch len(valid) {
	case 0:
		return nil
	case 1:
		return valid[0]
	}
	return func() Msg { return sequenceMsg(valid) }
}

// Tick 은 d 만큼 기다렸다가 사건 하나를 보낸다. 시각은 fn 에 넘어간다.
//
// **한 번만 울린다.** 되풀이하려면 그 사건을 받은 자리에서 Tick 을 다시 걸어야 한다:
//
//	case tickMsg:
//	    return m, m.tick()   // ← 다시 건다
//
// 처음 쓰는 사람이 가장 많이 걸려 넘어지는 자리다. "왜 시계가 한 번만 가지?"
// 되풀이를 기본으로 두지 않은 이유는, 그러면 멈추는 방법을 따로 만들어야 하고
// 모델이 죽은 뒤에도 도는 시계가 남기 때문이다. 다시 거는 쪽이 통제하기 쉽다.
func Tick(d time.Duration, fn func(time.Time) Msg) Cmd {
	return func() Msg {
		t := time.NewTimer(d)
		defer t.Stop()
		return fn(<-t.C)
	}
}

// Every 도 한 번만 울린다. 다만 시각을 **벽시계에 맞춘다.**
//
// Every(time.Second, …) 를 12:34:20.4 에 걸면 0.6초 뒤인 12:34:21.0 에 울린다.
// 여러 곳에서 재는 시계를 서로 맞추고 싶을 때(초 단위 시계 표시 같은 것) 쓴다.
func Every(d time.Duration, fn func(time.Time) Msg) Cmd {
	return func() Msg {
		now := time.Now()
		t := time.NewTimer(now.Truncate(d).Add(d).Sub(now))
		defer t.Stop()
		return fn(<-t.C)
	}
}

// LogToFile 은 디버그 로그를 파일로 돌린다.
//
// 화면을 통째로 쓰는 프로그램은 fmt.Println 으로 디버그할 수 없다 — 그 글이
// 화면 한복판에 찍혀 우리가 그린 것을 망가뜨린다. 그래서 로그는 파일로 뺀다.
// 다른 터미널에서 tail -f 로 보면 된다.
//
//	f, _ := tea.LogToFile("debug.log", "보리차")
//	defer f.Close()
//	log.Println("여기까지 왔다")
func LogToFile(path, prefix string) (io.Closer, error) {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0o644)
	if err != nil {
		return nil, err
	}
	log.SetOutput(f)
	if prefix != "" {
		log.SetPrefix(prefix + " ")
	}
	log.SetFlags(log.Ltime | log.Lshortfile)
	return f, nil
}
