package render

import (
	"bytes"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestTrimForClear(t *testing.T) {
	cases := []struct{ in, want string }{
		{"abc   ", "abc"},
		{"abc", "abc"},
		{"   ", ""},
		{"", ""},
		{"a b  ", "a b"},
		// 꾸밈이 걸린 줄은 손대지 않는다. 줄 끝의 공백이 "색칠된 칸" 일 수 있기 때문이다.
		{"\x1b[44mab  \x1b[0m", "\x1b[44mab  \x1b[0m"},
		{"\x1b[31mabc\x1b[0m   ", "\x1b[31mabc\x1b[0m   "},
	}
	for _, c := range cases {
		if got := trimForClear(c.in); got != c.want {
			t.Errorf("trimForClear(%q) = %q, 원하는 값 %q", c.in, got, c.want)
		}
	}
}

// 렌더러는 줄 끝 공백을 떼고 내보낸다. \e[K 가 이미 그 자리를 지웠기 때문이다.
func TestFlushTrimsTrailingSpaces(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("ab        ")
	r.Flush()
	want := "\x1b[1;1H\x1b[Kab" + "\x1b[1;1H"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 잘라 낸 공백 때문에 다음 프레임의 비교가 틀리면 안 된다.
// 비교는 자르기 전의 줄로 해야 한다 — "ab" 와 "ab  " 는 화면에서는 같아 보여도
// 배경색이 붙는 순간 달라지기 때문이다.
func TestTrimDoesNotConfuseDiff(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("ab   ")
	r.Flush()
	buf.Reset()
	r.Write("ab   ")
	r.Flush()
	if got := buf.String(); got != "" {
		t.Errorf("같은 화면인데 %q 를 다시 썼다", got)
	}
}

// 시계로 도는 렌더러. Write 를 아무리 자주 불러도 그리기는 초당 fps 번이다.
type syncBuf struct {
	mu sync.Mutex
	b  strings.Builder
}

func (s *syncBuf) Write(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.b.Write(p)
}

func (s *syncBuf) String() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.b.String()
}

func TestStartStop(t *testing.T) {
	var buf syncBuf
	r := New(&buf, 10, 5)
	r.Start(200)
	for i := 0; i < 50; i++ {
		r.Write("frame")
	}
	time.Sleep(60 * time.Millisecond)
	r.Stop()

	got := buf.String()
	if !strings.Contains(got, "frame") {
		t.Errorf("시계가 도는데 아무것도 안 그렸다: %q", got)
	}
	// 50번 썼지만 화면은 한 번만 바뀌었으므로 "frame" 은 한 번만 나가야 한다.
	if n := strings.Count(got, "frame"); n != 1 {
		t.Errorf("\"frame\" 을 %d번 그렸다 — 화면이 안 바뀌었는데도", n)
	}
	// Stop 뒤에는 더 그리지 않는다.
	before := buf.String()
	r.Write("after")
	time.Sleep(30 * time.Millisecond)
	if buf.String() != before {
		t.Error("Stop 뒤에도 그렸다")
	}
}
