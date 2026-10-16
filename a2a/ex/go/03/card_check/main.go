// 에이전트 카드 검증기 — 필수 필드(proto REQUIRED)와 흔한 실수.
// 표준 라이브러리만. 오류가 하나라도 있으면 종료 코드 1.
//
//	go run ./03/card_check 카드주소...
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
	"time"
)

type obj = map[string]any

// finding 은 검사 결과 한 줄: 수준(오류·경고)과 내용.
type finding struct{ level, text string }

// region: rules
var (
	card = []string{"name", "description", "version",
		"supportedInterfaces", "capabilities", "defaultInputModes",
		"defaultOutputModes", "skills"}
	iface = []string{"url", "protocolBinding", "protocolVersion"}
	skill = []string{"id", "name", "description", "tags"}
	patch = regexp.MustCompile(`^\d+\.\d+\.\d+`) // 1.0.1 처럼
)

// absent: ProtoJSON 은 빈 문자열·빈 목록을 안 적는다 — 비면 없는 것.
// 객체는 비어도 "있음" — capabilities 가 {} 면 켠 기능이 없을 뿐.
func absent(o obj, key string) bool {
	v, ok := o[key]
	switch x := v.(type) {
	case string:
		return x == ""
	case []any:
		return len(x) == 0
	}
	return !ok || v == nil
}

// endregion

// region: required
func list(o obj, name string) []obj {
	var out []obj
	items, _ := o[name].([]any)
	for _, it := range items {
		m, _ := it.(obj)
		out = append(out, m)
	}
	return out
}

func required(c obj) []finding {
	var out []finding
	miss := func(path string) {
		msg := path + ": 필수인데 없거나 비었다"
		out = append(out, finding{"오류", msg})
	}
	for _, k := range card {
		if absent(c, k) {
			miss(k)
		}
	}
	for _, g := range []struct {
		name string
		keys []string
	}{{"supportedInterfaces", iface}, {"skills", skill}} {
		for i, it := range list(c, g.name) {
			for _, k := range g.keys {
				if absent(it, k) {
					miss(fmt.Sprintf("%s[%d].%s", g.name, i, k))
				}
			}
		}
	}
	return out
}

// endregion

// region: iface
var client = &http.Client{Timeout: 2 * time.Second}

// reachable: 어떤 상태 코드든 답이 오면 닿은 것이다.
func reachable(u string) bool {
	res, err := client.Get(u)
	if err != nil {
		return false
	}
	res.Body.Close()
	return true
}

func interfaces(c obj, cardURL string) []finding {
	var out []finding
	home := host(cardURL)
	for i, f := range list(c, "supportedInterfaces") {
		at := fmt.Sprintf("supportedInterfaces[%d]", i)
		u, _ := f["url"].(string)
		if v, _ := f["protocolVersion"].(string); patch.MatchString(v) {
			out = append(out, finding{"경고",
				fmt.Sprintf("%s.protocolVersion: %s (§3.6)", at, v)})
		}
		if u != "" && !reachable(u) {
			out = append(out, finding{"오류",
				fmt.Sprintf("%s.url: 닿지 않는다 %s", at, u)})
		}
		if u != "" && host(u) != home {
			out = append(out, finding{"경고",
				fmt.Sprintf("%s.url: 카드를 받은 곳(%s)과 다르다",
					at, home)})
		}
	}
	return out
}

func host(u string) string {
	p, err := url.Parse(u)
	if err != nil {
		return ""
	}
	return p.Host
}

// endregion

// region: main
// cardURL: .json 으로 끝나면 그 파일, 아니면 well-known 경로.
func cardURL(addr string) string {
	if strings.HasSuffix(addr, ".json") {
		return addr
	}
	const well = "/.well-known/agent-card.json"
	return strings.TrimSuffix(addr, "/") + well
}

func main() {
	bad := false
	for _, addr := range os.Args[1:] {
		u := cardURL(addr)
		var c obj
		res, err := http.Get(u)
		if err == nil {
			err = json.NewDecoder(res.Body).Decode(&c)
			res.Body.Close()
		}
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		found := append(required(c), interfaces(c, u)...)
		fmt.Println(addr)
		if len(found) == 0 {
			fmt.Println("  문제 없음")
		}
		for _, f := range found {
			fmt.Printf("  %s %s\n", f.level, f.text)
			bad = bad || f.level == "오류"
		}
	}
	if bad {
		os.Exit(1)
	}
}

// endregion
//@ norun
