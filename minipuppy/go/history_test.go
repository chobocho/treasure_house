package minipuppy

import "testing"

// 도구 호출/결과 짝을 섞어 놓은 기록을 만든다.
func buildHistory(turns int) *History {
	h := NewHistory("너는 코딩 에이전트다.")
	long := ""
	for i := 0; i < 12; i++ {
		long += "긴 문장을 채운다 "
	}
	for i := 0; i < turns; i++ {
		h.User("요청 " + string(rune('0'+i%10)) + " — " + long)
		id := "c" + string(rune('0'+i%10))
		h.ToolCall(id, "read_file", `{"path":"a.py"}`)
		h.ToolResult(id, "read_file", long+long+long)
	}
	return h
}

func TestEstimateTokens(t *testing.T) {
	if EstimateTokens("") != 0 {
		t.Fatal("빈 문자열은 0 이어야 한다")
	}
	영어, 한글 := EstimateTokens(repeat("a", 60)), EstimateTokens(repeat("가", 60))
	if 한글 <= 영어 {
		t.Fatalf("한글이 더 비싸야 한다: 한글=%d 영어=%d", 한글, 영어)
	}
}

func repeat(s string, n int) string {
	out := ""
	for i := 0; i < n; i++ {
		out += s
	}
	return out
}

func TestNeedsCompaction(t *testing.T) {
	h := buildHistory(12)
	if !h.NeedsCompaction(2000, 0.75) {
		t.Fatalf("넘쳤어야 한다: %d토큰", h.TotalTokens())
	}
	if h.NeedsCompaction(1_000_000, 0.75) {
		t.Fatal("창이 크면 안 넘쳐야 한다")
	}
}

func TestCompactKeepsSystemAndTail(t *testing.T) {
	h := buildHistory(12)
	last := h.Msgs[len(h.Msgs)-1].Content
	before := h.TotalTokens()
	n, summary := h.Compact(400)
	if n == 0 {
		t.Fatal("접었어야 한다")
	}
	if h.Msgs[0].Role != RoleSystem {
		t.Fatal("시스템 프롬프트가 사라졌다")
	}
	if h.Msgs[len(h.Msgs)-1].Content != last {
		t.Fatal("최근 메시지가 사라졌다")
	}
	if h.TotalTokens() >= before {
		t.Fatal("토큰이 줄지 않았다")
	}
	if !contains(summary, "read_file") {
		t.Fatalf("요약에 쓴 도구가 없다: %s", summary)
	}
}

// 컴팩션의 진짜 함정 — 짝 없는 도구 결과가 남으면 모델 API 가 400 을 던진다.
func TestCompactNeverOrphansToolResult(t *testing.T) {
	for _, protected := range []int{50, 120, 300, 700, 1500, 4000} {
		h := buildHistory(12)
		h.Compact(protected)
		open := map[string]bool{}
		for _, m := range h.Msgs {
			switch {
			case m.Role == RoleAssistant && m.ToolCallID != "":
				open[m.ToolCallID] = true
			case m.Role == RoleTool:
				if !open[m.ToolCallID] {
					t.Fatalf("짝 없는 도구 결과가 남았다 (protected=%d)", protected)
				}
			}
		}
	}
}

func TestCompactNothingToFold(t *testing.T) {
	h := NewHistory("시스템")
	h.User("한 마디")
	if n, _ := h.Compact(10000); n != 0 {
		t.Fatal("접을 중간이 없으면 0 이어야 한다")
	}
}

func TestCompactTwiceIsSafe(t *testing.T) {
	h := buildHistory(12)
	h.Compact(300)
	h.Compact(300)
	if h.Msgs[0].Role != RoleSystem || len(h.Msgs) < 2 {
		t.Fatal("두 번 접었더니 망가졌다")
	}
}

func contains(s, sub string) bool {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}
