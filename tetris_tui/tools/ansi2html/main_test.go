package main

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestPlainTextIsEscapedNotStyled(t *testing.T) {
	got := Convert("a<b>&c")
	if strings.Contains(got, "<b>") {
		t.Errorf("HTML 이 그대로 새어 나갔다: %q", got)
	}
	for _, want := range []string{"&lt;", "&gt;", "&amp;"} {
		if !strings.Contains(got, want) {
			t.Errorf("%q 로 이스케이프되지 않았다: %q", want, got)
		}
	}
	if strings.Contains(got, "<span") {
		t.Errorf("색이 없는데 span 이 생겼다: %q", got)
	}
}

func TestTrueColorForeground(t *testing.T) {
	got := Convert("\x1b[38;2;255;0;128m██\x1b[m")
	if !strings.Contains(got, "color:#ff0080") {
		t.Errorf("24비트 색이 안 나왔다: %q", got)
	}
	if !strings.Contains(got, "██") {
		t.Errorf("글자가 사라졌다: %q", got)
	}
	if strings.Count(got, "<span") != 1 {
		t.Errorf("span 이 %d개다: %q", strings.Count(got, "<span"), got)
	}
}

// 256색과 기본 16색도 같은 색으로 풀려야 한다. 캡처마다 터미널이 다른 표현을 쓴다.
func TestIndexedColors(t *testing.T) {
	if got := Convert("\x1b[38;5;196mX\x1b[m"); !strings.Contains(got, "color:#") {
		t.Errorf("256색이 안 풀렸다: %q", got)
	}
	if got := Convert("\x1b[31mX\x1b[m"); !strings.Contains(got, "color:#") {
		t.Errorf("기본 16색이 안 풀렸다: %q", got)
	}
	if got := Convert("\x1b[91mX\x1b[m"); !strings.Contains(got, "color:#") {
		t.Errorf("밝은 16색이 안 풀렸다: %q", got)
	}
}

func TestBackgroundColor(t *testing.T) {
	got := Convert("\x1b[48;2;0;32;64mX\x1b[m")
	if !strings.Contains(got, "background:#002040") {
		t.Errorf("배경색이 안 나왔다: %q", got)
	}
}

func TestBoldAndFaint(t *testing.T) {
	if got := Convert("\x1b[1mX\x1b[m"); !strings.Contains(got, "font-weight:700") {
		t.Errorf("굵게가 안 나왔다: %q", got)
	}
	if got := Convert("\x1b[2mX\x1b[m"); !strings.Contains(got, "opacity:") {
		t.Errorf("흐리게가 안 나왔다: %q", got)
	}
}

// 리셋이 실제로 스타일을 끊어야 한다. 안 끊으면 한 줄의 색이 화면 끝까지 번진다.
func TestResetEndsTheStyle(t *testing.T) {
	got := Convert("\x1b[38;2;255;0;0mA\x1b[mB")
	if !strings.HasSuffix(got, "B") {
		t.Errorf("리셋 뒤의 글자가 span 안에 갇혔다: %q", got)
	}
}

// 같은 색이 이어지면 span 하나로 합쳐야 한다.
// tmux 캡처는 칸마다 이스케이프를 넣기 때문에, 안 합치면 파일이 몇 배로 커진다.
func TestAdjacentRunsAreMerged(t *testing.T) {
	raw := strings.Repeat("\x1b[38;2;0;255;0m██\x1b[m", 10)
	got := Convert(raw)
	if n := strings.Count(got, "<span"); n != 1 {
		t.Errorf("span 이 %d개다 — 하나로 합쳐져야 한다", n)
	}
	if n := strings.Count(got, "█"); n != 20 {
		t.Errorf("블록이 %d개다 — 20개여야 한다", n)
	}
}

// 줄 끝의 공백은 지운다. 80칸 캡처는 줄마다 공백이 수십 개씩 붙어 있다.
func TestTrailingSpacesAreTrimmed(t *testing.T) {
	got := Convert("ab" + strings.Repeat(" ", 40) + "\ncd   ")
	if strings.Contains(got, "  \n") || strings.HasSuffix(got, " ") {
		t.Errorf("줄 끝 공백이 남았다: %q", got)
	}
	if !strings.Contains(got, "ab\ncd") {
		t.Errorf("내용이 망가졌다: %q", got)
	}
}

// 모르는 이스케이프(커서 이동 등)는 조용히 버린다. 화면에 글자로 새면 안 된다.
func TestUnknownEscapesAreDropped(t *testing.T) {
	got := Convert("\x1b[2J\x1b[H\x1b[?25lABC")
	if got != "ABC" {
		t.Errorf("이스케이프가 새어 나왔다: %q", got)
	}
}

func TestEmptyInput(t *testing.T) {
	if got := Convert(""); got != "" {
		t.Errorf("빈 입력이 %q 가 됐다", got)
	}
}

// 프레임 묶음을 통째로 바꾼다. 재생기가 이 JSON 을 그대로 읽는다.
//
// 프레임은 통째로 저장하지 않고 **바뀐 줄만** 저장한다. 터미널 화면은 프레임 사이에
// 대부분 그대로이기 때문이다(Bubble Tea 의 렌더러도 같은 이유로 같은 일을 한다).
func TestConvertRecording(t *testing.T) {
	in := Recording{
		Name:   "t",
		Script: "left",
		Frames: []Frame{
			{I: 0, Label: "시작", Content: "\x1b[38;2;255;0;0mA\x1b[m\n둘째 줄"},
			{I: 1, Label: "left", Content: "B\n둘째 줄"},
		},
	}
	out := ConvertRecording(in)
	if out.Name != "t" || len(out.Frames) != 2 {
		t.Fatalf("묶음이 망가졌다: %+v", out)
	}
	if out.Frames[0].Label != "시작" {
		t.Errorf("이름이 %q 다", out.Frames[0].Label)
	}
	// 첫 프레임은 모든 줄을 담는다.
	if len(out.Frames[0].D) != 2 {
		t.Errorf("첫 프레임의 줄이 %d개다 — 2개여야 한다", len(out.Frames[0].D))
	}
	// 둘째 프레임은 바뀐 첫 줄 하나만.
	if len(out.Frames[1].D) != 1 {
		t.Fatalf("둘째 프레임의 바뀐 줄이 %d개다 — 1개여야 한다: %v", len(out.Frames[1].D), out.Frames[1].D)
	}
	if out.Frames[1].D[0].Y != 0 || out.Frames[1].D[0].HTML != "B" {
		t.Errorf("바뀐 줄이 %+v 다", out.Frames[1].D[0])
	}
	if out.Frames[1].N != 2 {
		t.Errorf("둘째 프레임의 줄 수가 %d 다", out.Frames[1].N)
	}
}

// 아무것도 안 바뀐 프레임은 빈 목록이 된다 — 저장할 것이 없다.
func TestUnchangedFrameStoresNothing(t *testing.T) {
	out := ConvertRecording(Recording{Frames: []Frame{
		{Content: "same\nlines"},
		{Content: "same\nlines"},
	}})
	if len(out.Frames[1].D) != 0 {
		t.Errorf("안 바뀐 프레임에 %d줄이 저장됐다", len(out.Frames[1].D))
	}
}

// 줄 수가 줄어든 프레임도 다뤄야 한다 — N 이 잘라 내는 자리를 알려 준다.
func TestShorterFrame(t *testing.T) {
	out := ConvertRecording(Recording{Frames: []Frame{
		{Content: "a\nb\nc"},
		{Content: "a"},
	}})
	if out.Frames[1].N != 1 {
		t.Errorf("줄 수가 %d 다 — 1 이어야 한다", out.Frames[1].N)
	}
	if len(out.Frames[1].D) != 0 {
		t.Errorf("첫 줄은 그대로인데 %d줄이 저장됐다", len(out.Frames[1].D))
	}
}

// JSON 에서는 바뀐 줄이 [줄번호, HTML] 두 칸짜리 배열이다 — 키 이름을 반복하지 않으려고.
func TestLineDiffJSONShape(t *testing.T) {
	out := ConvertRecording(Recording{Frames: []Frame{{Content: "ab"}}})
	raw, err := json.Marshal(out.Frames[0])
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(raw), `[[0,"ab"]]`) {
		t.Errorf("JSON 모양이 다르다: %s", raw)
	}
}

// 화면의 폭과 높이를 재어 둔다 — 재생기가 자리를 미리 잡는 데 쓴다.
func TestRecordingSize(t *testing.T) {
	in := Recording{Frames: []Frame{{Content: "abc\nde"}, {Content: "abcdefg\nx\ny"}}}
	out := ConvertRecording(in)
	if out.Cols != 7 {
		t.Errorf("폭이 %d 다 — 가장 긴 줄은 7칸이다", out.Cols)
	}
	if out.Rows != 3 {
		t.Errorf("높이가 %d 다 — 가장 긴 프레임은 3줄이다", out.Rows)
	}
}

// 한글은 두 칸을 먹는다. 폭을 글자 수로 세면 재생기의 자리가 좁아진다.
func TestWideRunesCountAsTwoColumns(t *testing.T) {
	out := ConvertRecording(Recording{Frames: []Frame{{Content: "한글"}}})
	if out.Cols != 4 {
		t.Errorf("\"한글\"의 폭이 %d 다 — 4 여야 한다", out.Cols)
	}
}
