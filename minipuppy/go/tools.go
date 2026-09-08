package minipuppy

import (
	"encoding/json"
	"fmt"
	"reflect"
	"sort"
	"strconv"
	"strings"
)

// ToolResult 는 도구 실행 결과. 실패도 **예외가 아니라 값**으로 돌아간다 —
// 모델이 오류 문구를 읽고 스스로 고쳐야 하기 때문.
type ToolResult struct {
	OK        bool
	Content   string
	Truncated bool
}

// Tool 은 모델이 부를 수 있는 함수 하나.
type Tool struct {
	Name        string
	Description string
	Schema      map[string]any
	call        func(*Workspace, map[string]any) (string, error)
}

// Registry 는 도구 목록과 에이전트별 허용 목록을 함께 다룬다.
type Registry struct {
	tools map[string]*Tool
}

func NewRegistry() *Registry { return &Registry{tools: map[string]*Tool{}} }

// Register 는 인자 구조체 T 에서 스키마를 뽑아 도구를 등록한다.
//
// 파이썬은 함수 서명과 타입 힌트를 읽었다. Go 는 구조체 태그를 읽는다:
//
//	type readArgs struct {
//	    Path  string `json:"path"  desc:"뿌리 기준 상대 경로" required:"true"`
//	    Start int    `json:"start" desc:"시작 행"`
//	}
//
// 대신 Go 는 컴파일 때 인자 모양이 고정된다 — 도구를 고치면서 스키마를
// 안 고치는 사고가 구조적으로 불가능하다.
func Register[T any](r *Registry, name, description string,
	fn func(*Workspace, T) (string, error)) {
	var zero T
	schema, fields := schemaOf(reflect.TypeOf(zero))
	r.tools[name] = &Tool{
		Name: name, Description: description, Schema: schema,
		call: func(ws *Workspace, raw map[string]any) (string, error) {
			var args T
			if err := decodeArgs(raw, fields, &args); err != nil {
				return "", err
			}
			return fn(ws, args)
		},
	}
}

type fieldInfo struct {
	key   string
	index int
	kind  reflect.Kind
}

func schemaOf(t reflect.Type) (map[string]any, []fieldInfo) {
	props := map[string]any{}
	var required []string
	var fields []fieldInfo
	if t == nil || t.Kind() != reflect.Struct {
		return map[string]any{"type": "object", "properties": props}, fields
	}
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		key := f.Tag.Get("json")
		if key == "" {
			key = strings.ToLower(f.Name)
		}
		key = strings.Split(key, ",")[0]
		entry := map[string]any{"type": jsonType(f.Type.Kind())}
		if d := f.Tag.Get("desc"); d != "" {
			entry["description"] = d
		}
		props[key] = entry
		if f.Tag.Get("required") == "true" {
			required = append(required, key)
		}
		fields = append(fields, fieldInfo{key: key, index: i, kind: f.Type.Kind()})
	}
	out := map[string]any{"type": "object", "properties": props}
	if len(required) > 0 {
		out["required"] = required
	} else {
		out["required"] = []string{}
	}
	return out, fields
}

func jsonType(k reflect.Kind) string {
	switch k {
	case reflect.String:
		return "string"
	case reflect.Int, reflect.Int64:
		return "integer"
	case reflect.Float64:
		return "number"
	case reflect.Bool:
		return "boolean"
	case reflect.Slice:
		return "array"
	case reflect.Map:
		return "object"
	}
	return "string"
}

// decodeArgs 는 모델이 보낸 값을 구조체 필드 타입으로 끌어당긴다.
//
// encoding/json 만으로는 안 된다. 모델은 3 을 "3" 으로, true 를 "true" 로
// 보내는 일이 잦고 json.Unmarshal 은 그걸 거부한다. 여기서 안 고치면
// 도구가 오류를 내고, 모델은 그 오류를 이해하지 못해 같은 실수를 반복한다.
func decodeArgs(raw map[string]any, fields []fieldInfo, out any) error {
	v := reflect.ValueOf(out).Elem()
	for _, f := range fields {
		got, ok := raw[f.key]
		if !ok || got == nil {
			continue
		}
		fv := v.Field(f.index)
		if err := assign(fv, got, f.key); err != nil {
			return err
		}
	}
	return nil
}

func assign(fv reflect.Value, got any, key string) error {
	switch fv.Kind() {
	case reflect.String:
		switch g := got.(type) {
		case string:
			fv.SetString(g)
		default:
			b, _ := json.Marshal(g)
			fv.SetString(string(b))
		}
	case reflect.Int, reflect.Int64:
		n, err := toInt(got)
		if err != nil {
			return fmt.Errorf("%s: 정수로 읽을 수 없는 값 %v", key, got)
		}
		fv.SetInt(n)
	case reflect.Float64:
		switch g := got.(type) {
		case float64:
			fv.SetFloat(g)
		case string:
			f, err := strconv.ParseFloat(strings.TrimSpace(g), 64)
			if err != nil {
				return fmt.Errorf("%s: 실수로 읽을 수 없는 값 %v", key, got)
			}
			fv.SetFloat(f)
		default:
			return fmt.Errorf("%s: 실수로 읽을 수 없는 값 %v", key, got)
		}
	case reflect.Bool:
		b, err := toBool(got)
		if err != nil {
			return fmt.Errorf("%s: 참/거짓으로 읽을 수 없는 값 %v", key, got)
		}
		fv.SetBool(b)
	default:
		b, err := json.Marshal(got)
		if err != nil {
			return fmt.Errorf("%s: 읽을 수 없는 값", key)
		}
		if err := json.Unmarshal(b, fv.Addr().Interface()); err != nil {
			return fmt.Errorf("%s: 읽을 수 없는 값", key)
		}
	}
	return nil
}

func toInt(got any) (int64, error) {
	switch g := got.(type) {
	case float64:
		return int64(g), nil
	case int:
		return int64(g), nil
	case bool:
		if g {
			return 1, nil
		}
		return 0, nil
	case string:
		return strconv.ParseInt(strings.TrimSpace(g), 10, 64)
	}
	return 0, fmt.Errorf("정수 아님")
}

func toBool(got any) (bool, error) {
	switch g := got.(type) {
	case bool:
		return g, nil
	case float64:
		return g != 0, nil
	case string:
		switch strings.ToLower(strings.TrimSpace(g)) {
		case "1", "true", "yes", "on", "y":
			return true, nil
		case "0", "false", "no", "off", "n":
			return false, nil
		}
	}
	return false, fmt.Errorf("참/거짓 아님")
}

func (r *Registry) Names() []string {
	out := make([]string, 0, len(r.tools))
	for n := range r.tools {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

func (r *Registry) Get(name string) *Tool { return r.tools[name] }

// Allowed 는 허용 목록으로 거른 도구들. nil 이면 전부.
func (r *Registry) Allowed(allow []string) []*Tool {
	var out []*Tool
	set := map[string]bool{}
	for _, a := range allow {
		set[a] = true
	}
	for _, n := range r.Names() {
		if allow == nil || set[n] {
			out = append(out, r.tools[n])
		}
	}
	return out
}

// Schemas 는 모델에 보낼 도구 설명. 허용 목록 밖은 **여기에 아예 안 나온다** —
// 이것이 "도구 목록이 곧 가드레일"의 기계적 근거다.
func (r *Registry) Schemas(allow []string) []map[string]any {
	var out []map[string]any
	for _, t := range r.Allowed(allow) {
		out = append(out, map[string]any{
			"name": t.Name, "description": t.Description, "parameters": t.Schema,
		})
	}
	return out
}

// Call 은 도구 하나를 부른다. 어떤 실패도 패닉으로 새지 않는다.
func (r *Registry) Call(ws *Workspace, name string, args map[string]any,
	allow []string, maxOutput int) (res ToolResult) {
	defer func() {
		if rec := recover(); rec != nil {
			res = ToolResult{OK: false, Content: fmt.Sprintf("도구가 패닉했다: %v", rec)}
		}
	}()
	if allow != nil {
		ok := false
		for _, a := range allow {
			if a == name {
				ok = true
				break
			}
		}
		if !ok {
			return ToolResult{Content: fmt.Sprintf("이 에이전트에는 '%s' 도구가 없다.", name)}
		}
	}
	t := r.tools[name]
	if t == nil {
		hint := ""
		var close []string
		for _, n := range r.Names() {
			if len(name) >= 3 && strings.HasPrefix(n, name[:3]) {
				close = append(close, n)
			}
		}
		if len(close) > 0 {
			hint = " 비슷한 것: " + strings.Join(close, ", ")
		}
		return ToolResult{Content: fmt.Sprintf("모르는 도구: '%s'.%s", name, hint)}
	}
	text, err := t.call(ws, args)
	if err != nil {
		return ToolResult{Content: err.Error()}
	}
	if maxOutput > 0 && len([]rune(text)) > maxOutput {
		runes := []rune(text)
		keep := maxOutput / 2
		cut := len(runes) - maxOutput
		text = string(runes[:keep]) +
			fmt.Sprintf("\n… [%d자 잘림] …\n", cut) + string(runes[len(runes)-keep:])
		return ToolResult{OK: true, Content: text, Truncated: true}
	}
	return ToolResult{OK: true, Content: text}
}
