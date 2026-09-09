package minipuppy

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

var nameRe = regexp.MustCompile(`^[a-z0-9][a-z0-9_-]{0,39}$`)

// ReadOnlyTools 와 FullTools 는 자주 쓰는 허용 목록.
var (
	ReadOnlyTools = []string{"grep", "list_files", "read_file"}
	FullTools     = []string{"edit_file", "grep", "list_files", "read_file",
		"run_command", "write_file"}
)

// AgentSpec 은 인격 하나의 정의. 이게 전부라서 JSON 파일 하나로 만들 수 있다.
type AgentSpec struct {
	Name        string   `json:"name"`
	DisplayName string   `json:"display_name"`
	Description string   `json:"description"`
	System      string   `json:"-"`
	SystemRaw   any      `json:"system_prompt"`
	Tools       []string `json:"tools"`
	ModelName   string   `json:"model"`
	Source      string   `json:"-"`
}

// normalize 는 system_prompt 가 문자열이든 문자열 배열이든 받아 준다.
func (s *AgentSpec) normalize() error {
	switch v := s.SystemRaw.(type) {
	case string:
		s.System = v
	case []any:
		var lines []string
		for _, l := range v {
			lines = append(lines, fmt.Sprint(l))
		}
		s.System = strings.Join(lines, "\n")
	case nil:
	default:
		return fmt.Errorf("system_prompt 는 문자열이거나 문자열 배열이어야 한다")
	}
	if s.DisplayName == "" {
		s.DisplayName = s.Name
	}
	if !nameRe.MatchString(s.Name) {
		return fmt.Errorf("에이전트 이름은 소문자·숫자·-·_ 로 40자까지: %q", s.Name)
	}
	return nil
}

// Builtin 은 코드에 들어 있는 인격들.
func Builtin() []AgentSpec {
	return []AgentSpec{
		{Name: "minipuppy", DisplayName: "Mini Puppy 🐶",
			Description: "코드를 읽고 고치는 기본 에이전트",
			System: "너는 minipuppy, 명령줄에서 도는 코딩 에이전트다.\n" +
				"- 먼저 읽고 나서 고친다. 파일을 안 보고 추측하지 마라.\n" +
				"- 한 번에 한 가지만 바꾼다.\n" +
				"- 고친 뒤에는 시험을 돌려 확인한다.",
			Tools: FullTools, Source: "builtin"},
		{Name: "reader", DisplayName: "Reader 📖",
			Description: "읽기만 한다. 아무것도 못 고친다",
			System:      "너는 코드를 읽고 설명하는 에이전트다. 직접 고치지는 않는다.",
			Tools:       ReadOnlyTools, Source: "builtin"},
		{Name: "tester", DisplayName: "Tester 🧪",
			Description: "시험을 돌리고 실패를 보고한다",
			System:      "너는 시험을 돌려 결과를 정리하는 에이전트다.",
			Tools:       append(append([]string{}, ReadOnlyTools...), "run_command"),
			Source:      "builtin"},
	}
}

// AgentRegistry 는 내장 인격 위에 JSON 파일을 얹는다.
type AgentRegistry struct {
	Dir    string
	Specs  map[string]AgentSpec
	Errors []string
}

func NewAgentRegistry(dir string) *AgentRegistry {
	r := &AgentRegistry{Dir: dir}
	r.Reload()
	return r
}

func (r *AgentRegistry) Reload() {
	r.Specs = map[string]AgentSpec{}
	r.Errors = nil
	for _, s := range Builtin() {
		r.Specs[s.Name] = s
	}
	if r.Dir == "" {
		return
	}
	entries, err := os.ReadDir(r.Dir)
	if err != nil {
		return
	}
	names := make([]string, 0, len(entries))
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	for _, n := range names {
		raw, err := os.ReadFile(filepath.Join(r.Dir, n))
		if err != nil {
			continue
		}
		var spec AgentSpec
		if err := json.Unmarshal(raw, &spec); err != nil {
			r.Errors = append(r.Errors, n+": JSON 이 깨졌다")
			continue
		}
		if spec.Name == "" {
			spec.Name = strings.TrimSuffix(n, ".json")
		}
		spec.Source = filepath.Join(r.Dir, n)
		if err := spec.normalize(); err != nil {
			r.Errors = append(r.Errors, n+": "+err.Error())
			continue
		}
		r.Specs[spec.Name] = spec // 파일이 내장을 덮는다
	}
}

func (r *AgentRegistry) Names() []string {
	out := make([]string, 0, len(r.Specs))
	for n := range r.Specs {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

func (r *AgentRegistry) Get(name string) (AgentSpec, bool) {
	s, ok := r.Specs[name]
	return s, ok
}

func (r *AgentRegistry) Describe() string {
	var b strings.Builder
	for _, n := range r.Names() {
		s := r.Specs[n]
		mark := "파일"
		if s.Source == "builtin" {
			mark = "내장"
		}
		tools := "전부"
		if s.Tools != nil {
			tools = fmt.Sprintf("%d개", len(s.Tools))
		}
		fmt.Fprintf(&b, "%-12s %-4s 도구 %-4s %s\n", n, mark, tools, s.Description)
	}
	return strings.TrimRight(b.String(), "\n")
}

// Build 는 인격 하나를 실행 가능한 Agent 로 만든다.
// 없는 도구를 요구하면 여기서 막는다 — 실행 중에 알면 늦다.
func (r *AgentRegistry) Build(name string, model Model, tools *Registry,
	bus *Bus, lim Limits) (*Agent, error) {
	spec, ok := r.Get(name)
	if !ok {
		return nil, fmt.Errorf("모르는 에이전트: %s (있는 것: %s)",
			name, strings.Join(r.Names(), ", "))
	}
	var unknown []string
	for _, t := range spec.Tools {
		if tools.Get(t) == nil {
			unknown = append(unknown, t)
		}
	}
	if len(unknown) > 0 {
		return nil, fmt.Errorf("'%s' 가 없는 도구를 요구한다: %s",
			name, strings.Join(unknown, ", "))
	}
	return &Agent{Name: spec.Name, DisplayName: spec.DisplayName,
		System: spec.System, Model: model, Tools: spec.Tools,
		Registry: tools, Bus: bus, Limits: lim}, nil
}

type invokeArgs struct {
	Agent string `json:"agent" desc:"에이전트 이름" required:"true"`
	Task  string `json:"task" desc:"맡길 일을 한 문단으로" required:"true"`
}

// RegisterSubagentTool 은 에이전트를 도구로 노출한다.
// 깊이 제한이 유일한 안전장치다 — 없으면 자기가 자기를 불러 토큰을 태운다.
func RegisterSubagentTool(tools *Registry, agents *AgentRegistry,
	modelFor func(AgentSpec) (Model, error), bus *Bus, lim Limits, maxDepth int) {
	Register(tools, "invoke_agent", "다른 에이전트에게 일을 맡기고 결과만 받는다.",
		func(w *Workspace, a invokeArgs) (string, error) {
			depth := w.Depth + 1
			if depth > maxDepth {
				return "", fmt.Errorf("서브에이전트 깊이 한계(%d)를 넘었다.", maxDepth)
			}
			spec, ok := agents.Get(a.Agent)
			if !ok {
				return "", fmt.Errorf("모르는 에이전트: %s (있는 것: %s)",
					a.Agent, strings.Join(agents.Names(), ", "))
			}
			model, err := modelFor(spec)
			if err != nil {
				return "", err
			}
			sub, err := agents.Build(a.Agent, model, tools, bus, lim)
			if err != nil {
				return "", err
			}
			child := *w
			child.Depth = depth
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
			defer cancel()
			res, _ := sub.Run(ctx, a.Task, nil, &child)
			// 자식의 대화 기록은 넘기지 않는다. **결과만** 부모 컨텍스트에 들어간다 —
			// 이것이 서브에이전트가 컨텍스트를 아끼는 원리다.
			return fmt.Sprintf("[%s] %s\n(걸음 %d, 도구 %d회)",
				a.Agent, res.Text, res.Steps, res.ToolCalls), nil
		})
}
