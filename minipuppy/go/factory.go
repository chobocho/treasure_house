package minipuppy

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
	"time"
)

// ModelSpec 은 models.json 의 한 항목.
//
//	{
//	  "gpt-4.1": {"type":"openai", "url":"...", "model_id":"gpt-4.1",
//	              "api_key":"$OPENAI_API_KEY"},
//	  "교대":    {"type":"round_robin", "models":["gpt-4.1","느린것"],
//	              "rotate_every": 4}
//	}
//
// round_robin 이 type 값 하나로 들어간다는 것이 요점이다. 특별 취급이 없다.
type ModelSpec struct {
	Type        string            `json:"type"`
	URL         string            `json:"url"`
	APIKey      string            `json:"api_key"`
	ModelID     string            `json:"model_id"`
	Timeout     int               `json:"timeout"`
	MaxTokens   int               `json:"max_tokens"`
	Headers     map[string]string `json:"headers"`
	Models      []string          `json:"models"`
	RotateEvery int               `json:"rotate_every"`
	Cooldown    int               `json:"cooldown"`
	Replies     []ScriptedReply   `json:"replies"`
}

// ScriptedReply 는 대본 한 줄. 문자열이면 말, 객체면 도구 호출.
type ScriptedReply struct {
	Text  string         `json:"text"`
	Tool  string         `json:"tool"`
	Args  map[string]any `json:"args"`
	Tools []struct {
		Tool string         `json:"tool"`
		Args map[string]any `json:"args"`
	} `json:"tools"`
}

func (s *ScriptedReply) UnmarshalJSON(b []byte) error {
	var text string
	if err := json.Unmarshal(b, &text); err == nil {
		s.Text = text
		return nil
	}
	type raw ScriptedReply
	var r raw
	if err := json.Unmarshal(b, &r); err != nil {
		return err
	}
	*s = ScriptedReply(r)
	return nil
}

func (s ScriptedReply) toReply(i int) Reply {
	out := Reply{Text: s.Text}
	if s.Tool != "" {
		out.ToolCalls = append(out.ToolCalls,
			ToolCall{ID: fmt.Sprintf("s%d", i), Name: s.Tool, Args: s.Args})
	}
	for j, t := range s.Tools {
		out.ToolCalls = append(out.ToolCalls,
			ToolCall{ID: fmt.Sprintf("s%d-%d", i, j), Name: t.Tool, Args: t.Args})
	}
	return out
}

// LoadModels 는 models.json 을 읽어 내장 정의 위에 얹는다.
func LoadModels(path string) map[string]ModelSpec {
	defs := map[string]ModelSpec{
		"scripted": {Type: "scripted",
			Replies: []ScriptedReply{{Text: "대본이 비었다."}}},
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return defs
	}
	var got map[string]ModelSpec
	if err := json.Unmarshal(raw, &got); err != nil {
		return defs
	}
	for k, v := range got {
		defs[k] = v
	}
	return defs
}

// BuildModel 은 이름 하나로 모델 객체를 만든다. 자기 자신을 가리키면 막는다.
func BuildModel(name string, defs map[string]ModelSpec, env map[string]string,
	building ...string) (Model, error) {
	for _, b := range building {
		if b == name {
			return nil, fmt.Errorf("모델 정의가 자기 자신을 가리킨다: %s",
				strings.Join(append(building, name), " -> "))
		}
	}
	spec, ok := defs[name]
	if !ok {
		keys := make([]string, 0, len(defs))
		for k := range defs {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		return nil, fmt.Errorf("models.json 에 '%s' 가 없다. 있는 것: %s",
			name, strings.Join(keys, ", "))
	}
	switch spec.Type {
	case "scripted":
		replies := make([]Reply, 0, len(spec.Replies))
		for i, r := range spec.Replies {
			replies = append(replies, r.toReply(i))
		}
		return NewScripted(name, replies...), nil
	case "round_robin":
		if len(spec.Models) == 0 {
			return nil, fmt.Errorf("round_robin '%s' 에 models 가 비었다.", name)
		}
		var members []Model
		for _, m := range spec.Models {
			built, err := BuildModel(m, defs, env, append(building, name)...)
			if err != nil {
				return nil, err
			}
			members = append(members, built)
		}
		cd := time.Duration(spec.Cooldown) * time.Second
		return NewRoundRobin(name, spec.RotateEvery, cd, members...)
	case "", "openai", "anthropic", "custom", "openai_compatible":
		if spec.URL == "" {
			return nil, fmt.Errorf("'%s' 에 url 이 없다.", name)
		}
		id := spec.ModelID
		if id == "" {
			id = name
		}
		m := NewHTTPModel(name, spec.URL, expandEnv(spec.APIKey, env), id,
			time.Duration(spec.Timeout)*time.Second)
		if spec.MaxTokens > 0 {
			m.MaxTokens = spec.MaxTokens
		}
		if len(spec.Headers) > 0 {
			m.Headers = map[string]string{}
			for k, v := range spec.Headers {
				m.Headers[k] = expandEnv(v, env)
			}
		}
		return m, nil
	}
	return nil, fmt.Errorf("모르는 모델 종류: %q", spec.Type)
}

// expandEnv 는 "$OPENAI_API_KEY" 처럼 적힌 값을 환경변수로 푼다.
// 설정 파일에 키를 직접 적는 것을 막기 위한 것이다 — 파일은 백업·git·
// 화면 공유로 새기 쉽지만 환경변수는 덜하다.
func expandEnv(v string, env map[string]string) string {
	if strings.HasPrefix(v, "$") {
		return env[v[1:]]
	}
	return v
}
