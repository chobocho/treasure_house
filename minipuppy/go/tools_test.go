package minipuppy

import (
	"strings"
	"testing"
)

type addArgs struct {
	A int  `json:"a" desc:"첫 수" required:"true"`
	B int  `json:"b" desc:"둘째 수"`
	L bool `json:"loud" desc:"크게 말할까"`
}

func addRegistry(t *testing.T) *Registry {
	t.Helper()
	r := NewRegistry()
	Register(r, "add", "두 수를 더한다.", func(_ *Workspace, a addArgs) (string, error) {
		out := itoa(a.A + a.B)
		if a.L {
			out = strings.ToUpper(out) + "!"
		}
		return out, nil
	})
	Register(r, "boom", "일부러 터진다.", func(_ *Workspace, _ struct{}) (string, error) {
		panic("안에서 터졌다")
	})
	Register(r, "chatter", "길게 떠든다.", func(_ *Workspace, _ struct{}) (string, error) {
		return repeat("가", 5000), nil
	})
	return r
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var b []byte
	for n > 0 {
		b = append([]byte{byte('0' + n%10)}, b...)
		n /= 10
	}
	if neg {
		return "-" + string(b)
	}
	return string(b)
}

// 구조체 태그에서 스키마를 뽑는다 — 파이썬은 타입 힌트, Go 는 태그.
func TestSchemaFromStructTags(t *testing.T) {
	r := addRegistry(t)
	var got map[string]any
	for _, s := range r.Schemas(nil) {
		if s["name"] == "add" {
			got = s
		}
	}
	if got == nil {
		t.Fatal("add 스키마가 없다")
	}
	params := got["parameters"].(map[string]any)
	props := params["properties"].(map[string]any)
	a := props["a"].(map[string]any)
	if a["type"] != "integer" || a["description"] != "첫 수" {
		t.Fatalf("a 스키마가 틀렸다: %v", a)
	}
	if props["loud"].(map[string]any)["type"] != "boolean" {
		t.Fatal("bool 이 boolean 으로 안 갔다")
	}
	req := params["required"].([]string)
	if len(req) != 1 || req[0] != "a" {
		t.Fatalf("required 가 틀렸다: %v", req)
	}
}

// 모델은 3 을 "3" 으로, true 를 "true" 로 보낸다. encoding/json 만으로는 못 받는다.
func TestArgCoercion(t *testing.T) {
	r := addRegistry(t)
	got := r.Call(nil, "add", map[string]any{"a": "3", "b": "4"}, nil, 0)
	if !got.OK || got.Content != "7" {
		t.Fatalf("문자열 숫자를 못 받았다: %+v", got)
	}
	got = r.Call(nil, "add", map[string]any{"a": 1, "loud": "yes"}, nil, 0)
	if !got.OK || !strings.HasSuffix(got.Content, "!") {
		t.Fatalf("문자열 참거짓을 못 받았다: %+v", got)
	}
	got = r.Call(nil, "add", map[string]any{"a": "사과"}, nil, 0)
	if got.OK || !strings.Contains(got.Content, "정수로 읽을 수 없는") {
		t.Fatalf("못 읽는 값은 거절해야 한다: %+v", got)
	}
}

func TestAllowlistBlocksSchemaAndCall(t *testing.T) {
	r := addRegistry(t)
	allow := []string{"boom"}
	schemas := r.Schemas(allow)
	if len(schemas) != 1 || schemas[0]["name"] != "boom" {
		t.Fatalf("허용 목록 밖이 스키마에 남았다: %v", schemas)
	}
	got := r.Call(nil, "add", map[string]any{"a": 1}, allow, 0)
	if got.OK || !strings.Contains(got.Content, "도구가 없다") {
		t.Fatalf("허용 목록 밖을 불렀는데 통과했다: %+v", got)
	}
}

// 도구가 패닉해도 프로그램은 안 죽고, 모델은 오류 문구를 받는다.
func TestPanicBecomesResult(t *testing.T) {
	r := addRegistry(t)
	got := r.Call(nil, "boom", nil, nil, 0)
	if got.OK || !strings.Contains(got.Content, "패닉") {
		t.Fatalf("패닉이 결과로 안 돌아왔다: %+v", got)
	}
}

func TestUnknownToolGivesHint(t *testing.T) {
	r := addRegistry(t)
	got := r.Call(nil, "cha", nil, nil, 0)
	if got.OK || !strings.Contains(got.Content, "chatter") {
		t.Fatalf("비슷한 이름을 안 알려 줬다: %+v", got)
	}
}

func TestLongOutputIsTruncatedInMiddle(t *testing.T) {
	r := addRegistry(t)
	got := r.Call(nil, "chatter", nil, nil, 1000)
	if !got.OK || !got.Truncated {
		t.Fatalf("잘렸어야 한다: %+v", got)
	}
	if n := len([]rune(got.Content)); n > 1200 {
		t.Fatalf("너무 길다: %d", n)
	}
	if !strings.Contains(got.Content, "자 잘림") {
		t.Fatal("잘렸다는 표시가 없다")
	}
}
