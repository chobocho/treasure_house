package minipuppy

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sort"
	"sync"
	"time"
)

// ToolCall 은 모델이 부르려는 도구 한 건.
type ToolCall struct {
	ID   string
	Name string
	Args map[string]any
}

// Reply 는 모델의 한 번 응답.
type Reply struct {
	Text      string
	ToolCalls []ToolCall
	Usage     map[string]int
	Model     string
}

func (r Reply) WantsTools() bool { return len(r.ToolCalls) > 0 }

// ModelError 는 모델 호출 실패. Retryable 이면 다시 걸어 볼 만하다.
type ModelError struct {
	Msg       string
	Retryable bool
}

func (e *ModelError) Error() string { return e.Msg }

// Model 은 이 프로그램이 모델에 요구하는 전부다. 인터페이스가 이렇게 좁아서
// **라운드로빈이 특별 기능이 아니라 모델의 한 종류**가 될 수 있다.
type Model interface {
	Name() string
	Complete(ctx context.Context, msgs []map[string]any, tools []map[string]any) (Reply, error)
}

// ---- 대본 모델 -------------------------------------------------------

// Scripted 는 미리 정한 답을 순서대로 내놓는다.
// 시험이 진짜 모델을 부르면 느리고 비싸고 매번 다른 답이 나온다.
type Scripted struct {
	name    string
	Replies []Reply
	mu      sync.Mutex
	index   int
	Seen    [][]map[string]any // 무엇을 봤는지 (시험이 검사한다)
}

func NewScripted(name string, replies ...Reply) *Scripted {
	return &Scripted{name: name, Replies: replies}
}

func (s *Scripted) Name() string { return s.name }

func (s *Scripted) Complete(_ context.Context, msgs []map[string]any,
	_ []map[string]any) (Reply, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Seen = append(s.Seen, msgs)
	if s.index >= len(s.Replies) {
		return Reply{Text: "(대본 끝)", Model: s.name}, nil
	}
	r := s.Replies[s.index]
	s.index++
	r.Model = s.name
	return r, nil
}

// Say 와 CallTool 은 대본을 짧게 쓰기 위한 것.
func Say(text string) Reply { return Reply{Text: text} }

func CallTool(name string, kv map[string]any) Reply {
	return Reply{ToolCalls: []ToolCall{{ID: "s-" + name, Name: name, Args: kv}}}
}

// ---- HTTP 모델 -------------------------------------------------------

// HTTPModel 은 OpenAI 호환 /chat/completions.
type HTTPModel struct {
	name      string
	URL       string
	APIKey    string
	ModelID   string
	Headers   map[string]string
	MaxTokens int
	Client    *http.Client
}

func NewHTTPModel(name, url, apiKey, modelID string, timeout time.Duration) *HTTPModel {
	if timeout == 0 {
		timeout = 120 * time.Second
	}
	return &HTTPModel{name: name, URL: url, APIKey: apiKey, ModelID: modelID,
		MaxTokens: 4096, Client: &http.Client{Timeout: timeout}}
}

func (m *HTTPModel) Name() string { return m.name }

func (m *HTTPModel) Complete(ctx context.Context, msgs []map[string]any,
	tools []map[string]any) (Reply, error) {
	body := map[string]any{"model": m.ModelID, "messages": msgs,
		"max_tokens": m.MaxTokens}
	if len(tools) > 0 {
		var wrapped []map[string]any
		for _, t := range tools {
			wrapped = append(wrapped, map[string]any{"type": "function", "function": t})
		}
		body["tools"] = wrapped
	}
	raw, err := json.Marshal(body)
	if err != nil {
		return Reply{}, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		m.URL+"/chat/completions", bytes.NewReader(raw))
	if err != nil {
		return Reply{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	if m.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+m.APIKey)
	}
	for k, v := range m.Headers {
		req.Header.Set(k, v)
	}
	resp, err := m.Client.Do(req)
	if err != nil {
		return Reply{}, &ModelError{Msg: "연결 실패: " + err.Error(), Retryable: true}
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		// 429·5xx 는 다시 걸어 볼 만하다. 나머지 4xx 는 고쳐야 할 우리 잘못이다.
		retryable := resp.StatusCode == 429 || resp.StatusCode >= 500
		return Reply{}, &ModelError{
			Msg: fmt.Sprintf("HTTP %d %s", resp.StatusCode, resp.Status), Retryable: retryable}
	}
	var out map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return Reply{}, &ModelError{Msg: "응답을 읽을 수 없다: " + err.Error()}
	}
	return ParseReply(m.name, out)
}

// ParseReply 는 OpenAI 모양 응답을 Reply 로. 깨진 인자 JSON 도 삼킨다.
func ParseReply(name string, raw map[string]any) (Reply, error) {
	choices, _ := raw["choices"].([]any)
	if len(choices) == 0 {
		return Reply{}, &ModelError{Msg: "choices 가 비었다"}
	}
	first, _ := choices[0].(map[string]any)
	msg, _ := first["message"].(map[string]any)
	if msg == nil {
		return Reply{}, &ModelError{Msg: "message 가 없다"}
	}
	out := Reply{Model: name}
	if s, ok := msg["content"].(string); ok {
		out.Text = s
	}
	calls, _ := msg["tool_calls"].([]any)
	for i, c := range calls {
		cm, _ := c.(map[string]any)
		fn, _ := cm["function"].(map[string]any)
		if fn == nil {
			continue
		}
		id, _ := cm["id"].(string)
		if id == "" {
			id = fmt.Sprintf("call_%d", i)
		}
		nm, _ := fn["name"].(string)
		args := map[string]any{}
		switch a := fn["arguments"].(type) {
		case string:
			if a != "" {
				if err := json.Unmarshal([]byte(a), &args); err != nil {
					args = map[string]any{"__raw": a} // 모델이 깨진 JSON 을 보낼 때가 있다
				}
			}
		case map[string]any:
			args = a
		}
		out.ToolCalls = append(out.ToolCalls, ToolCall{ID: id, Name: nm, Args: args})
	}
	if u, ok := raw["usage"].(map[string]any); ok {
		out.Usage = map[string]int{}
		keys := make([]string, 0, len(u))
		for k := range u {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			if f, ok := u[k].(float64); ok {
				out.Usage[k] = int(f)
			}
		}
	}
	return out, nil
}

// ---- 라운드로빈 ------------------------------------------------------

// RoundRobin 은 여러 모델을 번갈아 쓴다. Model 인터페이스를 그대로 만족한다.
//
// rotate_every 가 저울질하는 것:
//
//	1 — 요청마다 바꾼다. 부하는 가장 고르지만 프롬프트 캐시가 매번 깨진다.
//	N — N 번에 한 번 바꾼다. 같은 곳으로 연달아 가서 캐시가 산다.
type RoundRobin struct {
	name        string
	Models      []Model
	RotateEvery int
	Cooldown    time.Duration
	Now         func() time.Time

	mu     sync.Mutex
	cursor int
	used   int
	down   map[string]time.Time
	Picks  []string
}

func NewRoundRobin(name string, rotateEvery int, cooldown time.Duration,
	models ...Model) (*RoundRobin, error) {
	if len(models) == 0 {
		return nil, fmt.Errorf("돌릴 모델이 없다.")
	}
	if rotateEvery < 1 {
		rotateEvery = 1
	}
	if cooldown == 0 {
		cooldown = 30 * time.Second
	}
	return &RoundRobin{name: name, Models: models, RotateEvery: rotateEvery,
		Cooldown: cooldown, Now: time.Now, down: map[string]time.Time{}}, nil
}

func (r *RoundRobin) Name() string { return r.name }

func (r *RoundRobin) healthy(m Model) bool {
	until, ok := r.down[m.Name()]
	return !ok || !r.Now().Before(until)
}

// Pick 은 지금 쓸 모델. 아픈 놈은 건너뛴다.
func (r *RoundRobin) Pick() Model {
	if r.used >= r.RotateEvery {
		r.cursor = (r.cursor + 1) % len(r.Models)
		r.used = 0
	}
	n := len(r.Models)
	for step := 0; step < n; step++ {
		c := r.Models[(r.cursor+step)%n]
		if r.healthy(c) {
			if step > 0 {
				r.cursor = (r.cursor + step) % n
				r.used = 0
			}
			return c
		}
	}
	// 전부 아프면 가장 빨리 낫는 놈으로 그냥 간다 — 멈추는 것보다는 낫다.
	best, bestAt := r.Models[0], r.down[r.Models[0].Name()]
	for _, m := range r.Models[1:] {
		if at := r.down[m.Name()]; at.Before(bestAt) {
			best, bestAt = m, at
		}
	}
	return best
}

func (r *RoundRobin) Complete(ctx context.Context, msgs []map[string]any,
	tools []map[string]any) (Reply, error) {
	r.mu.Lock()
	m := r.Pick()
	r.Picks = append(r.Picks, m.Name())
	r.mu.Unlock()

	reply, err := m.Complete(ctx, msgs, tools)

	r.mu.Lock()
	defer r.mu.Unlock()
	if err != nil {
		var me *ModelError
		if AsModelError(err, &me) && me.Retryable {
			r.down[m.Name()] = r.Now().Add(r.Cooldown)
			r.used = r.RotateEvery // 다음엔 다른 놈으로
		}
		return Reply{}, err
	}
	r.used++
	return reply, nil
}

// AsModelError 는 errors.As 의 좁은 판. 이 패키지는 의존성을 안 늘린다.
func AsModelError(err error, target **ModelError) bool {
	if me, ok := err.(*ModelError); ok {
		*target = me
		return true
	}
	return false
}
