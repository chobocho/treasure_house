package minipuppy

import (
	"fmt"
	"strings"
	"unicode"
)

// Role 은 메시지의 역할.
type Role string

const (
	RoleSystem    Role = "system"
	RoleUser      Role = "user"
	RoleAssistant Role = "assistant"
	RoleTool      Role = "tool"
)

// Msg 하나. ToolCallID 가 있으면 도구 호출(assistant) 이거나 그 결과(tool).
type Msg struct {
	Role       Role   `json:"role"`
	Content    string `json:"content"`
	ToolName   string `json:"tool_name,omitempty"`
	ToolCallID string `json:"tool_call_id,omitempty"`
	ToolArgs   string `json:"tool_args,omitempty"` // JSON 문자열 그대로 보관
	Pinned     bool   `json:"pinned,omitempty"`
}

// EstimateTokens 는 토크나이저 없이 어림잡는다.
//
// 영어는 대략 4글자에 1토큰, 한글·한자는 1.5글자에 1토큰. BPE 가 한글을
// 바이트 단위로 쪼개기 때문에 훨씬 비싸다. 정확할 필요는 없다 — 컴팩션은
// '넘치기 전에' 켜지면 되고, 실제보다 조금 크게 잡는 쪽이 안전하다.
func EstimateTokens(s string) int {
	if s == "" {
		return 0
	}
	var cjk, rest int
	for _, r := range s {
		if isWide(r) {
			cjk++
		} else {
			rest++
		}
	}
	n := int(float64(cjk)/1.5+float64(rest)/4) + 1
	if n < 1 {
		return 1
	}
	return n
}

func isWide(r rune) bool {
	return unicode.Is(unicode.Hangul, r) || unicode.Is(unicode.Han, r) ||
		unicode.Is(unicode.Hiragana, r) || unicode.Is(unicode.Katakana, r)
}

// Tokens 는 이 메시지 하나가 차지하는 어림 토큰 수.
func (m Msg) Tokens() int {
	return EstimateTokens(m.Content) + EstimateTokens(m.ToolName) +
		EstimateTokens(m.ToolArgs) + 4 // 역할·구분자 오버헤드
}

// History 는 대화 기록. 파이썬판 history.py 와 같은 규칙을 지킨다.
type History struct {
	Msgs []Msg
}

func NewHistory(systemPrompt string) *History {
	h := &History{}
	if systemPrompt != "" {
		h.Msgs = append(h.Msgs, Msg{Role: RoleSystem, Content: systemPrompt, Pinned: true})
	}
	return h
}

func (h *History) Add(m Msg) { h.Msgs = append(h.Msgs, m) }

func (h *History) User(text string) { h.Add(Msg{Role: RoleUser, Content: text}) }

func (h *History) Assistant(text string) { h.Add(Msg{Role: RoleAssistant, Content: text}) }

func (h *History) ToolCall(id, name, args string) {
	h.Add(Msg{Role: RoleAssistant, ToolName: name, ToolCallID: id, ToolArgs: args})
}

func (h *History) ToolResult(id, name, content string) {
	h.Add(Msg{Role: RoleTool, ToolName: name, ToolCallID: id, Content: content})
}

func (h *History) TotalTokens() int {
	n := 0
	for _, m := range h.Msgs {
		n += m.Tokens()
	}
	return n
}

func (h *History) NeedsCompaction(window int, threshold float64) bool {
	return float64(h.TotalTokens()) > float64(window)*threshold
}

// protectedStart 는 뒤에서부터 protected 토큰을 채우는 첫 인덱스.
func (h *History) protectedStart(protected int) int {
	acc, idx := 0, len(h.Msgs)
	for i := len(h.Msgs) - 1; i >= 0; i-- {
		acc += h.Msgs[i].Tokens()
		idx = i
		if acc >= protected {
			break
		}
	}
	return idx
}

// Compact 는 시스템 프롬프트와 최근 구간 사이를 요약 한 줄로 접는다.
// 접은 게 없으면 (0, "") 를 준다.
//
// 가장 중요한 규칙: **도구 호출과 그 결과를 절대 갈라놓지 않는다.**
// 짝 없는 tool 결과가 남으면 대부분의 모델 API 가 400 을 던진다.
func (h *History) Compact(protected int) (int, string) {
	head := 0
	for head < len(h.Msgs) && h.Msgs[head].Pinned {
		head++
	}
	start := h.protectedStart(protected)
	for start > 0 && h.Msgs[start].Role == RoleTool {
		start-- // 도구 결과 한복판이면 짝(assistant 호출)까지 당긴다
	}
	if start <= head {
		return 0, ""
	}
	dropped := h.Msgs[head:start]
	if len(dropped) == 0 {
		return 0, ""
	}
	summary := Summarize(dropped)
	tail := append([]Msg{}, h.Msgs[start:]...)
	h.Msgs = append(h.Msgs[:head],
		append([]Msg{{Role: RoleUser, Content: summary, Pinned: true}}, tail...)...)
	return len(dropped), summary
}

// Summarize 는 모델을 부르지 않는 기계적 요약. 요약도 실패할 수 있어서
// 실패했을 때 돌아갈 자리가 필요하다.
func Summarize(dropped []Msg) string {
	var tools []string
	seen := map[string]bool{}
	users := 0
	for _, m := range dropped {
		switch {
		case m.Role == RoleTool && m.ToolName != "" && !seen[m.ToolName]:
			seen[m.ToolName] = true
			tools = append(tools, m.ToolName)
		case m.Role == RoleUser:
			users++
		}
	}
	parts := []string{fmt.Sprintf("[요약] 이전 대화 %d건을 접었다.", len(dropped))}
	if users > 0 {
		parts = append(parts, fmt.Sprintf("사용자 요청 %d건.", users))
	}
	if len(tools) > 0 {
		parts = append(parts, "쓴 도구: "+strings.Join(tools, ", ")+".")
	}
	return strings.Join(parts, " ")
}
