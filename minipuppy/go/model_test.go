package minipuppy

import (
	"context"
	"strings"
	"testing"
	"time"
)

// 가짜 모델. 부른 횟수를 세고, 원하면 실패한다.
type fakeModel struct {
	name      string
	fail      bool
	retryable bool
	count     int
}

func (f *fakeModel) Name() string { return f.name }

func (f *fakeModel) Complete(_ context.Context, _ []map[string]any,
	_ []map[string]any) (Reply, error) {
	f.count++
	if f.fail {
		return Reply{}, &ModelError{Msg: f.name + " 실패", Retryable: f.retryable}
	}
	return Reply{Text: f.name, Model: f.name}, nil
}

// 가짜 시계. 쿨다운을 실제로 기다리지 않는다.
type fakeClock struct{ at time.Time }

func (c *fakeClock) now() time.Time       { return c.at }
func (c *fakeClock) pass(d time.Duration) { c.at = c.at.Add(d) }

func TestRotateEveryHoldsSameModel(t *testing.T) {
	rr, err := NewRoundRobin("rr", 2, 0,
		&fakeModel{name: "a"}, &fakeModel{name: "b"}, &fakeModel{name: "c"})
	must(t, err)
	for i := 0; i < 6; i++ {
		if _, err := rr.Complete(context.Background(), nil, nil); err != nil {
			t.Fatal(err)
		}
	}
	want := []string{"a", "a", "b", "b", "c", "c"}
	if strings.Join(rr.Picks, ",") != strings.Join(want, ",") {
		t.Fatalf("교대 순서가 틀렸다: %v", rr.Picks)
	}
}

func TestRotateEveryOneSwitchesEachCall(t *testing.T) {
	rr, err := NewRoundRobin("rr", 1, 0, &fakeModel{name: "a"}, &fakeModel{name: "b"})
	must(t, err)
	for i := 0; i < 4; i++ {
		rr.Complete(context.Background(), nil, nil)
	}
	if strings.Join(rr.Picks, ",") != "a,b,a,b" {
		t.Fatalf("매번 안 바꿨다: %v", rr.Picks)
	}
}

func TestFailedModelIsSkippedDuringCooldown(t *testing.T) {
	clock := &fakeClock{at: time.Unix(0, 0)}
	a := &fakeModel{name: "a", fail: true, retryable: true}
	b := &fakeModel{name: "b"}
	rr, err := NewRoundRobin("rr", 1, 30*time.Second, a, b)
	must(t, err)
	rr.Now = clock.now

	if _, err := rr.Complete(context.Background(), nil, nil); err == nil {
		t.Fatal("a 는 실패했어야 한다")
	}
	for i := 0; i < 2; i++ {
		got, err := rr.Complete(context.Background(), nil, nil)
		if err != nil || got.Text != "b" {
			t.Fatalf("쉬는 모델을 다시 불렀다: %v %v", got, err)
		}
	}
	if a.count != 1 {
		t.Fatalf("a 를 %d번 불렀다", a.count)
	}
	clock.pass(31 * time.Second)
	for i := 0; i < 2; i++ {
		rr.Complete(context.Background(), nil, nil)
	}
	if a.count != 2 {
		t.Fatalf("쿨다운이 끝났는데 a 가 안 돌아왔다 (count=%d)", a.count)
	}
}

// 우리 잘못(4xx)은 다른 모델로 돌려도 똑같이 실패한다. 쿨다운을 걸지 않는다.
func TestNonRetryableDoesNotCooldown(t *testing.T) {
	a := &fakeModel{name: "a", fail: true, retryable: false}
	rr, err := NewRoundRobin("rr", 1, 30*time.Second, a, &fakeModel{name: "b"})
	must(t, err)
	rr.Complete(context.Background(), nil, nil)
	if len(rr.down) != 0 {
		t.Fatalf("쿨다운이 걸렸다: %v", rr.down)
	}
}

func TestRoundRobinNeedsMembers(t *testing.T) {
	if _, err := NewRoundRobin("rr", 1, 0); err == nil {
		t.Fatal("빈 라운드로빈이 만들어졌다")
	}
}

func TestParseToolCalls(t *testing.T) {
	got, err := ParseReply("t", map[string]any{
		"choices": []any{map[string]any{"message": map[string]any{
			"content": nil,
			"tool_calls": []any{map[string]any{"id": "c1",
				"function": map[string]any{"name": "read_file",
					"arguments": `{"path":"a.go"}`}}}}}},
		"usage": map[string]any{"total_tokens": float64(12)}})
	must(t, err)
	if !got.WantsTools() || got.ToolCalls[0].Name != "read_file" {
		t.Fatalf("도구 호출을 못 읽었다: %+v", got)
	}
	if got.ToolCalls[0].Args["path"] != "a.go" {
		t.Fatalf("인자를 못 읽었다: %+v", got.ToolCalls[0].Args)
	}
	if got.Usage["total_tokens"] != 12 {
		t.Fatalf("usage 를 못 읽었다: %v", got.Usage)
	}
}

// 모델이 깨진 JSON 을 인자로 보낼 때가 있다. 삼키고 원문을 넘긴다.
func TestParseBrokenArguments(t *testing.T) {
	got, err := ParseReply("t", map[string]any{
		"choices": []any{map[string]any{"message": map[string]any{
			"tool_calls": []any{map[string]any{"id": "c1",
				"function": map[string]any{"name": "grep",
					"arguments": `{"needle": `}}}}}}})
	must(t, err)
	if _, ok := got.ToolCalls[0].Args["__raw"]; !ok {
		t.Fatalf("원문을 안 남겼다: %+v", got.ToolCalls[0].Args)
	}
}

func TestBuildModelRoundRobinIsJustAModel(t *testing.T) {
	defs := map[string]ModelSpec{
		"빠름": {Type: "openai", URL: "https://api.x/v1", ModelID: "gpt-4.1",
			APIKey: "$MY_KEY"},
		"느림":   {Type: "openai", URL: "https://api.y/v1"},
		"교대":   {Type: "round_robin", Models: []string{"빠름", "느림"}, RotateEvery: 4},
		"자기참조": {Type: "round_robin", Models: []string{"자기참조"}},
	}
	env := map[string]string{"MY_KEY": "sk-비밀"}

	m, err := BuildModel("교대", defs, env)
	must(t, err)
	rr, ok := m.(*RoundRobin)
	if !ok || rr.RotateEvery != 4 {
		t.Fatalf("round_robin 이 안 만들어졌다: %T", m)
	}
	var _ Model = rr // 규약이 같다는 것이 요점이다

	h, err := BuildModel("빠름", defs, env)
	must(t, err)
	if h.(*HTTPModel).APIKey != "sk-비밀" {
		t.Fatal("$환경변수를 안 풀었다")
	}
	if _, err := BuildModel("자기참조", defs, env); err == nil ||
		!strings.Contains(err.Error(), "자기 자신") {
		t.Fatalf("자기참조를 안 막았다: %v", err)
	}
	if _, err := BuildModel("없음", defs, env); err == nil ||
		!strings.Contains(err.Error(), "빠름") {
		t.Fatalf("있는 것을 안 알려 줬다: %v", err)
	}
}
