package minipuppy

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func agentsDir(t *testing.T, files map[string]string) string {
	t.Helper()
	dir := filepath.Join(t.TempDir(), "agents")
	must(t, os.MkdirAll(dir, 0o755))
	for name, body := range files {
		must(t, os.WriteFile(filepath.Join(dir, name), []byte(body), 0o644))
	}
	return dir
}

func TestBuiltinAgentsExist(t *testing.T) {
	r := NewAgentRegistry("")
	names := strings.Join(r.Names(), ",")
	if !strings.Contains(names, "minipuppy") || !strings.Contains(names, "reader") {
		t.Fatalf("내장 인격이 없다: %s", names)
	}
	if _, ok := r.Get("없는놈"); ok {
		t.Fatal("없는 놈이 있다")
	}
}

// reader 에는 쓰기 도구가 없다 — 프롬프트를 구슬려도 못 고친다.
func TestReaderHasNoWriteTools(t *testing.T) {
	r := NewAgentRegistry("")
	spec, _ := r.Get("reader")
	for _, banned := range []string{"write_file", "edit_file", "run_command"} {
		for _, got := range spec.Tools {
			if got == banned {
				t.Fatalf("reader 가 %s 를 들고 있다", banned)
			}
		}
	}
}

// JSON 파일 하나로 새 인격이 생긴다. 이게 이 층의 전부다.
func TestJSONAgentCreatesPersona(t *testing.T) {
	dir := agentsDir(t, map[string]string{
		"python-tutor.json": `{
			"name": "python-tutor",
			"display_name": "Python Tutor 🐍",
			"system_prompt": ["너는 파이썬 튜터다.", "답을 바로 주지 마라."],
			"tools": ["read_file", "grep"]}`,
	})
	r := NewAgentRegistry(dir)
	spec, ok := r.Get("python-tutor")
	if !ok {
		t.Fatalf("못 읽었다: %v", r.Errors)
	}
	if spec.DisplayName != "Python Tutor 🐍" {
		t.Fatalf("이름이 틀렸다: %s", spec.DisplayName)
	}
	if !strings.Contains(spec.System, "답을 바로 주지 마라") {
		t.Fatalf("배열 프롬프트를 안 이었다: %q", spec.System)
	}
	if len(spec.Tools) != 2 {
		t.Fatalf("도구 목록이 틀렸다: %v", spec.Tools)
	}
}

func TestJSONAgentOverridesBuiltin(t *testing.T) {
	dir := agentsDir(t, map[string]string{
		"reader.json": `{"name":"reader","system_prompt":"바꿔치기","tools":["grep"]}`,
	})
	r := NewAgentRegistry(dir)
	spec, _ := r.Get("reader")
	if len(spec.Tools) != 1 || spec.Tools[0] != "grep" {
		t.Fatalf("파일이 내장을 못 덮었다: %v", spec.Tools)
	}
}

// 나쁜 파일 하나가 나머지를 죽이면 안 된다.
func TestBadFilesAreRecordedNotFatal(t *testing.T) {
	dir := agentsDir(t, map[string]string{
		"broken.json":   "{{{",
		"badname.json":  `{"name":"한글 이름!!"}`,
		"good-one.json": `{"name":"good-one","tools":["grep"]}`,
	})
	r := NewAgentRegistry(dir)
	if len(r.Errors) != 2 {
		t.Fatalf("오류를 %d건 기록했다: %v", len(r.Errors), r.Errors)
	}
	if _, ok := r.Get("good-one"); !ok {
		t.Fatal("멀쩡한 것까지 죽었다")
	}
	if _, ok := r.Get("minipuppy"); !ok {
		t.Fatal("내장까지 죽었다")
	}
}

// 없는 도구를 요구하면 실행 중이 아니라 만들 때 막는다.
func TestUnknownToolBlocksBuild(t *testing.T) {
	dir := agentsDir(t, map[string]string{
		"ghost.json": `{"name":"ghost","tools":["존재하지_않는_도구"]}`,
	})
	r := NewAgentRegistry(dir)
	tools := NewRegistry()
	RegisterFileTools(tools)
	if _, err := r.Build("ghost", NewScripted("s"), tools, nil, DefaultLimits()); err == nil {
		t.Fatal("없는 도구를 요구하는데 만들어졌다")
	}
}

func TestBuiltAgentCarriesAllowlist(t *testing.T) {
	r := NewAgentRegistry("")
	tools := NewRegistry()
	RegisterFileTools(tools)
	RegisterShellTools(tools, 0)
	a, err := r.Build("reader", NewScripted("s"), tools, nil, DefaultLimits())
	must(t, err)
	for _, s := range tools.Schemas(a.Tools) {
		if s["name"] == "write_file" {
			t.Fatal("막힌 도구가 스키마에 나갔다")
		}
	}
}

// ---- 서브에이전트 ------------------------------------------------------

func subagentSetup(t *testing.T, maxDepth int) (*Registry, *Workspace) {
	t.Helper()
	tools, ws := tempWorkspace(t)
	RegisterShellTools(tools, 0)
	agents := NewAgentRegistry("")
	RegisterSubagentTool(tools, agents,
		func(AgentSpec) (Model, error) { return NewScripted("s", Say("읽어 봤다")), nil },
		nil, DefaultLimits(), maxDepth)
	return tools, ws
}

// 자식의 대화 기록은 안 넘어온다. 결과만 넘어온다 — 컨텍스트를 아끼는 원리.
func TestSubagentReturnsOnlyResult(t *testing.T) {
	tools, ws := subagentSetup(t, 2)
	got := tools.Call(ws, "invoke_agent",
		map[string]any{"agent": "reader", "task": "a.go 를 읽어라"}, nil, 0)
	if !got.OK || !strings.Contains(got.Content, "[reader]") ||
		!strings.Contains(got.Content, "읽어 봤다") {
		t.Fatalf("결과가 안 돌아왔다: %+v", got)
	}
	if !strings.Contains(got.Content, "걸음") {
		t.Fatalf("비용 요약이 없다: %q", got.Content)
	}
}

// 깊이 제한이 없으면 자기가 자기를 불러 토큰을 태운다.
func TestSubagentDepthLimit(t *testing.T) {
	tools, ws := subagentSetup(t, 1)
	ws.Depth = 1
	got := tools.Call(ws, "invoke_agent",
		map[string]any{"agent": "reader", "task": "또"}, nil, 0)
	if got.OK || !strings.Contains(got.Content, "깊이 한계") {
		t.Fatalf("깊이 제한이 안 걸렸다: %+v", got)
	}
}

func TestSubagentUnknownNameLists(t *testing.T) {
	tools, ws := subagentSetup(t, 2)
	got := tools.Call(ws, "invoke_agent",
		map[string]any{"agent": "없음", "task": "x"}, nil, 0)
	if got.OK || !strings.Contains(got.Content, "reader") {
		t.Fatalf("있는 것을 안 알려 줬다: %+v", got)
	}
}

func TestSubagentRunsUnderContext(t *testing.T) {
	tools, ws := subagentSetup(t, 2)
	got := tools.Call(ws, "invoke_agent",
		map[string]any{"agent": "tester", "task": "시험 돌려"}, nil, 0)
	if !got.OK {
		t.Fatalf("서브에이전트가 못 돌았다: %+v", got)
	}
}
