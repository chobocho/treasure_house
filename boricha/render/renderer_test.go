package render

import (
	"bytes"
	"testing"
)

// 렌더러가 내보내는 바이트를 그대로 못박는다.
//
// 화면에 무엇이 그려지는지는 눈으로만 확인할 수 있지만, "무엇을 써 보냈는지" 는
// 바이트로 확인할 수 있다. 그리고 터미널은 우리가 써 보낸 것만 그린다.
// 그래서 이 시험이 곧 렌더러의 명세다.
func TestFirstPaint(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("ab\ncd")
	if err := r.Flush(); err != nil {
		t.Fatal(err)
	}
	// 줄마다: 그 줄로 커서 이동 → 줄 끝까지 지우기 → 새 내용.
	// 마지막에 커서를 정해진 자리(마지막 줄 1열)에 세워 둔다.
	want := "\x1b[1;1H\x1b[Kab" + "\x1b[2;1H\x1b[Kcd" + "\x1b[2;1H"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 달라진 것이 없으면 한 바이트도 내보내지 않는다.
// 60 fps 로 도는 프로그램에서 이 한 줄이 CPU 와 배터리를 지킨다.
func TestNoChangeWritesNothing(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("ab\ncd")
	r.Flush()
	buf.Reset()
	r.Write("ab\ncd")
	if err := r.Flush(); err != nil {
		t.Fatal(err)
	}
	if got := buf.String(); got != "" {
		t.Errorf("= %q, 원하는 값 \"\"", got)
	}
}

func TestOnlyChangedLines(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("a\nb\nc")
	r.Flush()
	buf.Reset()
	r.Write("a\nX\nc")
	r.Flush()
	want := "\x1b[2;1H\x1b[KX" + "\x1b[3;1H"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 화면이 줄어들면 남은 자리를 지워야 한다.
// 안 지우면 지난 프레임의 글이 아래에 그대로 남아 유령처럼 보인다.
func TestShrinkClearsLeftovers(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("a\nb\nc")
	r.Flush()
	buf.Reset()
	r.Write("a")
	r.Flush()
	want := "\x1b[2;1H\x1b[K" + "\x1b[3;1H\x1b[K" + "\x1b[1;1H"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 폭을 넘는 줄은 자른다. 자르지 않으면 터미널이 스스로 다음 줄로 감아 버려
// 우리가 세어 둔 줄 번호와 실제 화면이 어긋난다 — 그때부터 화면이 무너진다.
func TestClipsToWidth(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 3, 5)
	r.Write("abcdef")
	r.Flush()
	want := "\x1b[1;1H\x1b[Kabc" + "\x1b[1;1H"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// Repaint 는 "지금 화면을 못 믿겠다" 는 뜻이다. 크기가 바뀌었거나,
// 다른 프로그램이 화면에 무언가 찍었을 때 부른다. 전부 다시 그린다.
func TestRepaint(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("a\nb")
	r.Flush()
	buf.Reset()
	r.Repaint()
	r.Write("a\nb")
	r.Flush()
	want := "\x1b[1;1H\x1b[Ka" + "\x1b[2;1H\x1b[Kb" + "\x1b[2;1H"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 크기가 바뀌면 다시 자르고 전부 다시 그려야 한다.
func TestResizeForcesFullRedraw(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 3, 5)
	r.Write("abcdef")
	r.Flush()
	buf.Reset()
	r.Resize(6, 5)
	r.Write("abcdef")
	r.Flush()
	want := "\x1b[1;1H\x1b[Kabcdef" + "\x1b[1;1H"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

func TestClear(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.Write("a")
	r.Flush()
	buf.Reset()
	if err := r.Clear(); err != nil {
		t.Fatal(err)
	}
	if got, want := buf.String(), "\x1b[2J\x1b[H"; got != want {
		t.Errorf("= %q, 원하는 값 %q", got, want)
	}
	// 지운 뒤에는 화면이 비었다고 알고 있어야 한다 — 같은 내용을 다시 그려도 전부 써야 한다.
	buf.Reset()
	r.Write("a")
	r.Flush()
	if got, want := buf.String(), "\x1b[1;1H\x1b[Ka\x1b[1;1H"; got != want {
		t.Errorf("지운 뒤 = %q, 원하는 값 %q", got, want)
	}
}

// 동기화 출력(DEC 2026)을 켜면 한 프레임을 통째로 감싼다.
// 터미널이 프레임을 다 받을 때까지 화면 갱신을 미뤄, 반쯤 그려진 화면이 보이지 않는다.
// 모르는 터미널은 이 모드를 조용히 무시하므로 켜 두어도 해롭지 않다.
func TestSyncOutput(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 5)
	r.SetSync(true)
	r.Write("a")
	r.Flush()
	want := "\x1b[?2026h" + "\x1b[1;1H\x1b[Ka" + "\x1b[1;1H" + "\x1b[?2026l"
	if got := buf.String(); got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
	// 바뀐 것이 없으면 감싸는 시퀀스도 안 보낸다.
	buf.Reset()
	r.Write("a")
	r.Flush()
	if got := buf.String(); got != "" {
		t.Errorf("= %q, 원하는 값 \"\"", got)
	}
}

// 화면보다 긴 View 는 잘린다. 잘랐다는 사실은 한 번만 알린다 —
// 매 프레임 경고하면 그 경고가 곧 화면을 뒤덮는다.
func TestOverflowWarnsOnce(t *testing.T) {
	var buf bytes.Buffer
	r := New(&buf, 10, 2)
	r.Write("a\nb\nc\nd")
	r.Flush()
	if !r.Overflowed() {
		t.Error("화면보다 긴 View 인데 Overflowed() 가 거짓")
	}
	r.Write("a\nb")
	r.Flush()
	if r.Overflowed() {
		t.Error("들어가는 View 인데 Overflowed() 가 참")
	}
}
