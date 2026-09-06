package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
)

// 레코더를 시험할 아주 작은 모델. 진짜 게임 모델 대신 이걸 쓰는 이유는
// "레코더가 제 일을 하는가"와 "게임이 옳은가"를 섞지 않기 위해서다.
type counter struct {
	n    int
	size string
}

func (c counter) Init() tea.Cmd { return nil }

func (c counter) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "right":
			c.n++
		case "left":
			c.n--
		case "space":
			c.n += 10
		}
	case tea.WindowSizeMsg:
		c.size = strconv.Itoa(msg.Width) + "x" + strconv.Itoa(msg.Height)
	case TickMsg:
		c.n += 100
	}
	return c, nil
}

func (c counter) View() tea.View {
	return tea.NewView("n=" + strconv.Itoa(c.n) + " size=" + c.size)
}

func TestParseStepKinds(t *testing.T) {
	steps, err := ParseScript("right right left space wait wait 100x40")
	if err != nil {
		t.Fatalf("파싱 실패: %v", err)
	}
	if len(steps) != 7 {
		t.Fatalf("스텝이 %d개다", len(steps))
	}
}

func TestUnknownStepIsAnError(t *testing.T) {
	if _, err := ParseScript("right 이런키는없다"); err == nil {
		t.Error("모르는 스텝인데 오류가 안 났다")
	}
}

func TestRunCapturesOneFrameForTheInitialStateAndEachStep(t *testing.T) {
	steps, err := ParseScript("right right wait")
	if err != nil {
		t.Fatal(err)
	}
	rec := Run("t", counter{}, steps)
	// 첫 프레임은 아무것도 누르기 전의 화면이다 — 이게 없으면 "무엇이 어떻게 바뀌었나"를 못 본다.
	if len(rec.Frames) != len(steps)+1 {
		t.Fatalf("프레임이 %d개다 — %d개여야 한다", len(rec.Frames), len(steps)+1)
	}
	want := []string{"n=0 size=", "n=1 size=", "n=2 size=", "n=102 size="}
	for i, w := range want {
		if got := rec.Frames[i].Content; got != w {
			t.Errorf("프레임 %d: %q — %q 를 기대했다", i, got, w)
		}
	}
}

func TestFrameLabelsSayWhatHappened(t *testing.T) {
	steps, _ := ParseScript("right wait 80x24")
	rec := Run("t", counter{}, steps)
	want := []string{"시작", "right", "wait", "80x24"}
	for i, w := range want {
		if rec.Frames[i].Label != w {
			t.Errorf("프레임 %d 이름이 %q — %q 를 기대했다", i, rec.Frames[i].Label, w)
		}
	}
}

func TestResizeStepSendsWindowSize(t *testing.T) {
	steps, _ := ParseScript("100x40")
	rec := Run("t", counter{}, steps)
	if !strings.Contains(rec.Frames[1].Content, "size=100x40") {
		t.Errorf("크기가 안 들어갔다: %q", rec.Frames[1].Content)
	}
}

// 빈 스크립트도 유효하다 — 첫 화면 한 장만 남는다.
func TestEmptyScript(t *testing.T) {
	steps, err := ParseScript("")
	if err != nil {
		t.Fatal(err)
	}
	rec := Run("t", counter{}, steps)
	if len(rec.Frames) != 1 {
		t.Fatalf("프레임이 %d개다", len(rec.Frames))
	}
}

// 레코더는 결정론적이어야 한다. 같은 스크립트를 두 번 돌리면 바이트까지 같아야
// `make record` 뒤의 git diff 가 비어 있고, 덱의 그림이 소스와 어긋나지 않는다.
func TestRunIsDeterministic(t *testing.T) {
	steps, _ := ParseScript("right space left wait 80x24")
	a, _ := json.Marshal(Run("t", counter{}, steps))
	b, _ := json.Marshal(Run("t", counter{}, steps))
	if string(a) != string(b) {
		t.Error("같은 스크립트를 두 번 돌렸는데 결과가 다르다")
	}
}

func TestWriteRecordingIsIndentedJSON(t *testing.T) {
	dir := t.TempDir()
	steps, _ := ParseScript("right")
	path := filepath.Join(dir, "frames_t.json")
	if err := WriteRecording(path, Run("t", counter{}, steps)); err != nil {
		t.Fatalf("쓰기 실패: %v", err)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	// 들여쓴 JSON 이어야 git diff 가 읽힌다 — 한 줄짜리는 리뷰가 불가능하다.
	if !strings.Contains(string(raw), "\n  \"name\"") {
		t.Errorf("들여쓰기가 안 됐다:\n%s", raw[:min(120, len(raw))])
	}
	var back Recording
	if err := json.Unmarshal(raw, &back); err != nil {
		t.Fatalf("다시 읽기 실패: %v", err)
	}
	if back.Name != "t" || len(back.Frames) != 2 {
		t.Errorf("되읽은 내용이 다르다: %+v", back)
	}
}

// 등록부는 6단계까지 채워진다. 지금은 비어 있어도 조회가 안전해야 한다.
func TestLookupUnknownMode(t *testing.T) {
	if _, ok := Lookup("없는모드"); ok {
		t.Error("없는 모드가 조회됐다")
	}
}
