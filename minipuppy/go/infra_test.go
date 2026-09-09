package minipuppy

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// ---- 버스 ------------------------------------------------------------

func TestBusDeliversInOrder(t *testing.T) {
	col := NewCollector()
	b := NewBus(col.Sink)
	b.Infof("하나")
	b.Warnf("둘")
	b.Errorf("셋")
	got := col.Kinds()
	if len(got) != 3 || got[0] != KindInfo || got[2] != KindError {
		t.Fatalf("순서가 틀렸다: %v", got)
	}
}

// 렌더러 하나가 죽었다고 에이전트를 멈추면 안 된다.
func TestBusSurvivesPanickingSink(t *testing.T) {
	col := NewCollector()
	b := NewBus(func(Message) { panic("렌더러 사고") }, col.Sink)
	b.Infof("살아남아라")
	if len(col.Msgs) != 1 {
		t.Fatal("뒤 싱크가 못 받았다")
	}
	if len(b.SinkPanics()) != 1 {
		t.Fatalf("패닉을 안 기록했다: %v", b.SinkPanics())
	}
}

func TestCollectorFiltersKinds(t *testing.T) {
	col := NewCollector(KindTool, KindToolOut)
	b := NewBus(col.Sink)
	b.Emit(KindTool, "read_file")
	b.Emit(KindAgent, "다 됐다")
	b.Emit(KindToolOut, "내용")
	if len(col.Msgs) != 2 {
		t.Fatalf("걸러지지 않았다: %d", len(col.Msgs))
	}
}

// ---- 원자적 쓰기와 세션 -------------------------------------------------

func TestAtomicWriteLeavesNoTemp(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "out", "a.txt")
	must(t, AtomicWriteFile(path, []byte("내용")))
	raw, err := os.ReadFile(path)
	must(t, err)
	if string(raw) != "내용" {
		t.Fatalf("내용이 다르다: %q", raw)
	}
	entries, err := os.ReadDir(filepath.Dir(path))
	must(t, err)
	for _, e := range entries {
		if strings.HasSuffix(e.Name(), ".tmp") {
			t.Fatalf("임시 파일이 남았다: %s", e.Name())
		}
	}
}

func TestAtomicOverwriteReplacesFully(t *testing.T) {
	path := filepath.Join(t.TempDir(), "a.txt")
	must(t, AtomicWriteFile(path, []byte("아주 긴 옛 내용이 여기 있었다")))
	must(t, AtomicWriteFile(path, []byte("새것")))
	raw, _ := os.ReadFile(path)
	if string(raw) != "새것" {
		t.Fatalf("옛 내용이 남았다: %q", raw)
	}
}

func TestSessionRoundTrip(t *testing.T) {
	st := Store{Dir: filepath.Join(t.TempDir(), "sessions")}
	s := NewSession("reader")
	s.Title = "첫 세션"
	s.Messages = []Msg{{Role: RoleUser, Content: "안녕"}}
	must(t, st.Save(s))
	got, err := st.Load(s.ID)
	must(t, err)
	if got.Agent != "reader" || got.Messages[0].Content != "안녕" ||
		got.Version != SchemaVersion {
		t.Fatalf("왕복이 깨졌다: %+v", got)
	}
	if !st.Delete(s.ID) || st.Delete(s.ID) {
		t.Fatal("지우기가 이상하다")
	}
}

// 형식을 바꾸면 지난 세션이 안 열린다. 버전을 보고 한 단계씩 올린다.
func TestMigrateV1ToV2(t *testing.T) {
	var raw map[string]any
	must(t, json.Unmarshal([]byte(`{"version":1,"id":"old1",
		"messages":["옛날 메시지"]}`), &raw))
	got, err := Migrate(raw)
	must(t, err)
	if got.Version != 2 || len(got.Messages) != 1 ||
		got.Messages[0].Role != RoleUser || got.Messages[0].Content != "옛날 메시지" {
		t.Fatalf("이주가 틀렸다: %+v", got)
	}
	if got.Agent != "minipuppy" {
		t.Fatalf("기본 에이전트가 안 채워졌다: %q", got.Agent)
	}
}

func TestListSkipsBrokenFiles(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "sessions")
	st := Store{Dir: dir}
	must(t, os.MkdirAll(dir, 0o755))
	must(t, os.WriteFile(filepath.Join(dir, "쓰레기.json"), []byte("아님"), 0o644))
	a := NewSession("x")
	a.Title = "먼저"
	must(t, st.Save(a))
	b := NewSession("x")
	b.Title = "나중"
	must(t, st.Save(b))
	b.Updated = a.Updated + 100
	must(t, AtomicWriteJSON(filepath.Join(dir, b.ID+".json"), b))
	got := st.List()
	if len(got) != 2 || got[0].Title != "나중" {
		t.Fatalf("목록이 틀렸다: %d건 %v", len(got), got)
	}
}

// ---- 설정 세 겹 --------------------------------------------------------

func TestConfigLayers(t *testing.T) {
	dir := t.TempDir()
	c := NewConfig(dir, map[string]string{})
	if c.Get("model") != Defaults["model"] || c.Source("model") != "default" {
		t.Fatal("기본값 층이 안 잡힌다")
	}
	must(t, c.Set("model", "gpt-4.1"))
	if c.Get("model") != "gpt-4.1" || c.Source("model") != "file" {
		t.Fatalf("파일 층이 기본값을 못 덮었다: %s", c.Get("model"))
	}

	env := NewConfig(dir, map[string]string{"MINIPUPPY_MODEL": "sonnet"})
	if env.Get("model") != "sonnet" || env.Source("model") != "env" {
		t.Fatalf("환경변수 층이 파일을 못 덮었다: %s", env.Get("model"))
	}
	// 환경변수가 덮는 키를 Set 해도 Get 은 안 바뀐다 — 진짜 우선순위를 보여 준다
	must(t, env.Set("model", "haiku"))
	if env.Get("model") != "sonnet" {
		t.Fatal("Set 이 환경변수를 이겼다")
	}
	raw, _ := os.ReadFile(env.Path())
	if !strings.Contains(string(raw), "haiku") {
		t.Fatalf("파일에는 써졌어야 한다: %q", raw)
	}
}

func TestConfigCacheInvalidatesOnEdit(t *testing.T) {
	dir := t.TempDir()
	c := NewConfig(dir, map[string]string{})
	must(t, c.Set("agent", "reader"))
	if c.Get("agent") != "reader" {
		t.Fatal("못 읽었다")
	}
	must(t, os.WriteFile(c.Path(), []byte("[puppy]\nagent = tester\n"), 0o644))
	if c.Get("agent") != "tester" {
		t.Fatal("파일이 바뀌었는데 캐시가 안 풀렸다")
	}
}

func TestLimitsFromConfig(t *testing.T) {
	c := NewConfig(t.TempDir(), map[string]string{})
	must(t, c.Set("context_window", "32000"))
	must(t, c.Set("compaction_threshold", "0.6"))
	lim := LimitsFrom(c)
	if lim.ContextWindow != 32000 || lim.CompactionThreshold != 0.6 {
		t.Fatalf("설정이 안 넘어왔다: %+v", lim)
	}
	if c.Bool("yolo_mode") {
		t.Fatal("기본 yolo 는 거짓이어야 한다")
	}
}

// ---- 셸 --------------------------------------------------------------

func TestDangerousCommandsBlocked(t *testing.T) {
	if LooksDangerous("sudo rm -rf / --no-preserve-root") == "" {
		t.Fatal("위험한 명령을 못 알아봤다")
	}
	if LooksDangerous("git status") != "" {
		t.Fatal("멀쩡한 명령을 막았다")
	}
	r := NewRegistry()
	RegisterShellTools(r, 0)
	ws, _ := NewWorkspace(t.TempDir())
	got := r.Call(ws, "run_command", map[string]any{"command": "rm -rf /"}, nil, 0)
	if got.OK || !strings.Contains(got.Content, "막힌 명령") {
		t.Fatalf("실행 전에 막았어야 한다: %+v", got)
	}
}

// 대화형 명령에 걸리면 영원히 멈춘다. 제한 시간이 지나면 죽인다.
func TestShellTimeoutKills(t *testing.T) {
	cmd := "ping -n 30 127.0.0.1 >nul"
	if os.PathSeparator == '/' {
		cmd = "sleep 30"
	}
	res, err := RunShell(context.Background(), cmd, t.TempDir(), 2*time.Second)
	must(t, err)
	if !res.TimedOut {
		t.Fatal("제한 시간을 안 지켰다")
	}
	if res.Seconds > 15 {
		t.Fatalf("너무 오래 걸렸다: %.1f초", res.Seconds)
	}
}
