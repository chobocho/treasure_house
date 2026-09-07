package input

import (
	"io"
	"reflect"
	"testing"
	"time"
)

// 채널에서 사건 하나를 받되, 오지 않으면 시험을 실패시킨다.
func recv(t *testing.T, ch <-chan Msg, within time.Duration) Msg {
	t.Helper()
	select {
	case m := <-ch:
		return m
	case <-time.After(within):
		t.Fatalf("%v 안에 사건이 오지 않았다", within)
		return nil
	}
}

func mustNothing(t *testing.T, ch <-chan Msg, within time.Duration) {
	t.Helper()
	select {
	case m := <-ch:
		t.Fatalf("아무것도 오지 말아야 하는데 %#v 가 왔다", m)
	case <-time.After(within):
	}
}

func TestReaderDeliversKeys(t *testing.T) {
	pr, pw := io.Pipe()
	rd := NewReader(pr)
	ch := make(chan Msg, 16)
	rd.Start(ch)
	defer rd.Close()

	go pw.Write([]byte("a한\x1b[A"))

	want := []Msg{
		KeyMsg{Code: 'a', Text: "a"},
		KeyMsg{Code: '한', Text: "한"},
		KeyMsg{Code: KeyUp},
	}
	for _, w := range want {
		if got := recv(t, ch, time.Second); !reflect.DeepEqual(got, w) {
			t.Fatalf("= %#v, 원하는 값 %#v", got, w)
		}
	}
}

// ESC 하나만 오고 조용해지면, 그것은 esc 키였다.
// 이 판정을 하는 시계가 Reader 에 있다는 것이 Decoder 와 나눈 이유다.
func TestReaderLoneEscapeAfterTimeout(t *testing.T) {
	pr, pw := io.Pipe()
	rd := NewReader(pr)
	rd.SetEscTimeout(30 * time.Millisecond)
	ch := make(chan Msg, 4)
	rd.Start(ch)
	defer rd.Close()

	go pw.Write([]byte{0x1b})

	got := recv(t, ch, time.Second)
	if want := (KeyMsg{Code: KeyEscape}); !reflect.DeepEqual(got, want) {
		t.Fatalf("= %#v, 원하는 값 %#v", got, want)
	}
}

// 방향키는 세 바이트가 붙어서 온다. 시계가 그 사이에 끼어들면 안 된다.
func TestReaderDoesNotSplitFastSequence(t *testing.T) {
	pr, pw := io.Pipe()
	rd := NewReader(pr)
	rd.SetEscTimeout(30 * time.Millisecond)
	ch := make(chan Msg, 4)
	rd.Start(ch)
	defer rd.Close()

	go pw.Write([]byte("\x1b[D"))

	got := recv(t, ch, time.Second)
	if want := (KeyMsg{Code: KeyLeft}); !reflect.DeepEqual(got, want) {
		t.Fatalf("= %#v, 원하는 값 %#v", got, want)
	}
	mustNothing(t, ch, 100*time.Millisecond)
}

// 시계가 지난 뒤에 '[' 가 오면 방향키가 아니라 esc 다음에 '[' 를 친 것이 된다.
// 이것이 이 방식의 대가다 — 느린 SSH 에서 방향키가 esc+[+A 로 쪼개지는 유명한 증상.
func TestReaderSlowSequenceBecomesSeparateKeys(t *testing.T) {
	pr, pw := io.Pipe()
	rd := NewReader(pr)
	rd.SetEscTimeout(20 * time.Millisecond)
	ch := make(chan Msg, 8)
	rd.Start(ch)
	defer rd.Close()

	go func() {
		pw.Write([]byte{0x1b})
		time.Sleep(200 * time.Millisecond)
		pw.Write([]byte("[A"))
	}()

	want := []Msg{
		KeyMsg{Code: KeyEscape},
		KeyMsg{Code: '[', Text: "["},
		KeyMsg{Code: 'A', Text: "A"},
	}
	for _, w := range want {
		if got := recv(t, ch, 2*time.Second); !reflect.DeepEqual(got, w) {
			t.Fatalf("= %#v, 원하는 값 %#v", got, w)
		}
	}
}

// 입력이 끝나면(EOF) 그 사실을 알려 줘야 한다. Program 은 이걸 받고 끝낸다.
func TestReaderReportsEOF(t *testing.T) {
	rd := NewReader(io.NopCloser(nopReader{}))
	ch := make(chan Msg, 4)
	rd.Start(ch)
	defer rd.Close()

	got := recv(t, ch, time.Second)
	m, ok := got.(ClosedMsg)
	if !ok {
		t.Fatalf("= %#v, 원하는 값 ClosedMsg", got)
	}
	if m.Err != nil {
		t.Errorf("EOF 는 오류가 아니다: %v", m.Err)
	}
}

type nopReader struct{}

func (nopReader) Read(p []byte) (int, error) { return 0, io.EOF }

// Close 한 뒤에는 채널에 아무것도 넣지 않는다.
func TestReaderCloseStops(t *testing.T) {
	pr, pw := io.Pipe()
	rd := NewReader(pr)
	ch := make(chan Msg, 8)
	rd.Start(ch)

	go pw.Write([]byte("a"))
	recv(t, ch, time.Second)

	rd.Close()
	rd.Close() // 두 번 불러도 안전해야 한다
	go pw.Write([]byte("bcd"))
	mustNothing(t, ch, 150*time.Millisecond)
}
