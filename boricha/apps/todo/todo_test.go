package todo

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"treasure/boricha/tea"
	"treasure/boricha/testkit"
)

// 각본으로 앱을 돌리고 끝난 모델을 돌려준다.
// 진짜 파서와 진짜 Update 를 지나므로, 키 하나가 잘못 해석되면 여기서 걸린다.
func run(t *testing.T, m Model, script string) Model {
	t.Helper()
	r, err := testkit.RunScript(m, script)
	if err != nil {
		t.Fatal(err)
	}
	return r.Final.(Model)
}

func texts(m Model) string {
	var b strings.Builder
	for _, t := range m.tasks {
		if t.Done {
			b.WriteString("[x]")
		} else {
			b.WriteString("[ ]")
		}
		b.WriteString(t.Text + " ")
	}
	return strings.TrimSpace(b.String())
}

func TestAddTask(t *testing.T) {
	m := run(t, New(""), `60x20 a "보리차 사기" <enter> a "찻잔 씻기" <enter>`)
	if got := texts(m); got != "[ ]보리차 사기 [ ]찻잔 씻기" {
		t.Errorf("= %q", got)
	}
}

// 빈 글은 안 넣는다. 실수로 enter 를 두 번 쳤을 때 빈 줄이 쌓이는 것을 막는다.
func TestAddEmptyIsRejected(t *testing.T) {
	m := run(t, New(""), `60x20 a <enter> a "   " <enter>`)
	if len(m.tasks) != 0 {
		t.Errorf("빈 할 일이 %d개 들어갔다: %q", len(m.tasks), texts(m))
	}
}

// esc 로 취소하면 아무것도 안 남는다.
func TestAddCancel(t *testing.T) {
	m := run(t, New(""), `60x20 a "취소할 것" <esc>`)
	if len(m.tasks) != 0 {
		t.Errorf("취소했는데 %q", texts(m))
	}
	if m.mode != modeList {
		t.Error("esc 뒤에도 입력 상태다")
	}
}

func TestToggleDone(t *testing.T) {
	m := run(t, New(""), `60x20 a "가" <enter> a "나" <enter> <down> <space>`)
	if got := texts(m); got != "[ ]가 [x]나" {
		t.Errorf("= %q", got)
	}
	m = run(t, New(""), `60x20 a "가" <enter> <space> <space>`)
	if got := texts(m); got != "[ ]가" {
		t.Errorf("두 번 눌렀는데 %q", got)
	}
}

func TestDelete(t *testing.T) {
	m := run(t, New(""), `60x20 a "가" <enter> a "나" <enter> a "다" <enter> <down> d`)
	if got := texts(m); got != "[ ]가 [ ]다" {
		t.Errorf("= %q", got)
	}
}

// 글이 똑같은 할 일이 둘일 때, 지운 것이 정말 고른 것이어야 한다.
// 값으로 뒤지면 언제나 앞의 것을 찾아 엉뚱한 것이 사라진다.
func TestDeleteWithDuplicateTexts(t *testing.T) {
	m := run(t, New(""), `60x20 a "우유" <enter> a "우유" <enter> <down> <space> <up> d`)
	// 첫 번째를 지웠으니 남은 것은 끝난 표시가 붙은 두 번째다.
	if got := texts(m); got != "[x]우유" {
		t.Errorf("= %q, 원하는 값 %q", got, "[x]우유")
	}
}

// 걸러 놓은 상태에서 지우면 걸러진 목록이 아니라 진짜 목록에서 그것이 지워져야 한다.
func TestDeleteWhileFiltered(t *testing.T) {
	m := run(t, New(""),
		`60x20 a "보리차" <enter> a "녹차" <enter> a "커피" <enter> / "녹" <enter> d`)
	if got := texts(m); got != "[ ]보리차 [ ]커피" {
		t.Errorf("= %q", got)
	}
}

// 거르는 중에는 a·d·space 가 글자로 들어가야 한다.
func TestFilterTypingIsNotACommand(t *testing.T) {
	m := run(t, New(""), `60x20 a "abc" <enter> / a`)
	if !m.list.Filtering() {
		t.Fatal("거르기가 안 켜졌다")
	}
	if m.mode == modeAdd {
		t.Error("거르는 중에 a 가 '추가' 로 먹혔다")
	}
	if len(m.tasks) != 1 {
		t.Errorf("할 일이 %d개", len(m.tasks))
	}
}

// 저장은 명령으로 밀어냈다. 파일이 실제로 만들어지고 다시 읽히는지 본다.
func TestSaveAndLoad(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "todo.json")

	m := run(t, New(path), `60x20 a "보리차 사기" <enter> <space> .2`)
	if len(m.tasks) != 1 {
		t.Fatalf("할 일이 %d개", len(m.tasks))
	}

	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("저장된 파일이 없다: %v", err)
	}
	var got []Task
	if err := json.Unmarshal(b, &got); err != nil {
		t.Fatalf("JSON 이 깨졌다: %v", err)
	}
	if len(got) != 1 || got[0].Text != "보리차 사기" || !got[0].Done {
		t.Errorf("저장된 것 = %+v", got)
	}

	// 다시 띄우면 그대로 돌아온다.
	back := run(t, New(path), `60x20 .2`)
	if len(back.tasks) != 1 || back.tasks[0].Text != "보리차 사기" {
		t.Errorf("불러온 것 = %+v", back.tasks)
	}
}

// 파일이 없는 것은 오류가 아니다 — 첫 실행이다.
func TestLoadMissingFileIsNotAnError(t *testing.T) {
	m := run(t, New(filepath.Join(t.TempDir(), "없는파일.json")), `60x20 .2`)
	if strings.Contains(m.status, "실패") {
		t.Errorf("첫 실행을 오류로 알렸다: %q", m.status)
	}
}

// 할 일이 없으면 완료·지우기 배치를 꺼 둔다. 도움말에도 안 나오고 눌러도 안 먹는다.
func TestBindingsDisabledWhenEmpty(t *testing.T) {
	m := New("")
	for _, b := range m.bindings() {
		if b.Help[1] == "지우기" && b.Enabled() {
			t.Error("빈 목록인데 지우기가 켜져 있다")
		}
	}
	m2 := run(t, New(""), `60x20 a "가" <enter>`)
	for _, b := range m2.bindings() {
		if b.Help[1] == "지우기" && !b.Enabled() {
			t.Error("할 일이 있는데 지우기가 꺼져 있다")
		}
	}
}

// 화면이 크기를 넘지 않는다.
func TestViewFitsScreen(t *testing.T) {
	r, err := testkit.RunScript(New(""), `50x18 a "보리차 사기" <enter> a "찻잔 씻기" <enter>`)
	if err != nil {
		t.Fatal(err)
	}
	for i, f := range r.Frames {
		if n := strings.Count(f, "\n") + 1; n != 18 {
			t.Errorf("프레임 %d 이 %d줄", i, n)
		}
	}
}

var _ tea.Model = Model{}
