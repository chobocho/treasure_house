// 카드만 내주는 서버 — net/http 와 encoding/json 만으로. SDK 는 아직
// 없다. 카드는 정해진 경로에 놓인 JSON 문서 한 장일 뿐이다.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
)

// region: types
// 필드 순서가 곧 JSON 키 순서다(파이썬·TS 판과 같게).
type Card struct {
	Name                string         `json:"name"`
	Description         string         `json:"description"`
	SupportedInterfaces []Interface    `json:"supportedInterfaces"`
	Version             string         `json:"version"`
	Capabilities        map[string]any `json:"capabilities"`
	DefaultInputModes   []string       `json:"defaultInputModes"`
	DefaultOutputModes  []string       `json:"defaultOutputModes"`
	Skills              []Skill        `json:"skills"`
}

type Interface struct {
	URL             string `json:"url"`
	ProtocolBinding string `json:"protocolBinding"`
	ProtocolVersion string `json:"protocolVersion"`
}

type Skill struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Tags        []string `json:"tags"`
}

// endregion

const (
	desc      = "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다."
	skillDesc = "워크숍 숙소를 고르고 견적을 냅니다."
)

func main() {
	port := flag.Int("port", 0, "붙을 포트")
	url := flag.String("url", "", "카드에 적을 바깥 주소")
	flag.Parse()
	if *url == "" {
		*url = fmt.Sprintf("http://127.0.0.1:%d/", *port)
	}
	card := Card{
		Name:                "보물상사 숙소 에이전트",
		Description:         desc,
		SupportedInterfaces: []Interface{{*url, "JSONRPC", "1.0"}},
		Version:             "1.0.0",
		Capabilities:        map[string]any{"streaming": true},
		DefaultInputModes: []string{
			"application/json", "text/plain",
		},
		DefaultOutputModes: []string{"application/json"},
		Skills: []Skill{{
			"find-lodging", "숙소 찾기", skillDesc,
			[]string{"lodging", "workshop"},
		}},
	}
	// region: handler
	// 경로 패턴에 메서드를 붙이면(GET …) 다른 메서드는 405 가 된다.
	http.HandleFunc("GET /.well-known/agent-card.json",
		func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(card)
		})
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		w.WriteHeader(http.StatusNotFound)
		fmt.Fprint(w, "없는 경로입니다\n")
	})
	// endregion
	http.ListenAndServe(fmt.Sprintf("127.0.0.1:%d", *port), nil)
}

//@ norun
