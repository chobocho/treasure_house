// 푸시 알림을 받아 찍기만 하는 웹훅 수신기(표준 라이브러리만).
//
// 에이전트가 POST 로 보내는 몸통(StreamResponse 모양의 JSON)과 토큰
// 헤더를 한 줄 요약으로 찍는다. 받은 순서대로 번호를 붙인다.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
)

var (
	count int
	mu    sync.Mutex
)

type status struct {
	State   string `json:"state"`
	Message struct {
		Parts []map[string]any `json:"parts"`
	} `json:"message"`
}

type event struct {
	Status   status `json:"status"`
	Artifact struct {
		Name string `json:"name"`
	} `json:"artifact"`
}

// region: summary
// summary: {"statusUpdate": {...}}
// → "statusUpdate TASK_STATE_WORKING …"
func summary(body map[string]event) string {
	for kind, ev := range body { // 몸통의 키는 하나뿐이다
		switch kind {
		case "statusUpdate":
			var texts []string
			for _, p := range ev.Status.Message.Parts {
				if t, ok := p["text"].(string); ok {
					texts = append(texts, t)
				}
			}
			line := kind + " " + ev.Status.State + " " +
				strings.Join(texts, " ")
			return strings.TrimRight(line, " \t\n")
		case "artifactUpdate":
			return kind + " " + ev.Artifact.Name
		case "task":
			return kind + " " + ev.Status.State
		}
		return kind
	}
	return ""
}

// endregion

// region: hook
func hook(w http.ResponseWriter, r *http.Request) {
	var body map[string]event
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	token := r.Header.Get("X-A2A-Notification-Token")
	if token == "" {
		token = "-"
	}
	mu.Lock()
	count++
	fmt.Printf("#%d token=%s %s\n", count, token, summary(body))
	mu.Unlock()
	w.WriteHeader(http.StatusNoContent)
}

// endregion

func main() {
	port := flag.Int("port", 0, "붙을 포트(필수)")
	flag.Parse()
	if *port == 0 {
		fmt.Fprintln(os.Stderr, "--port 가 필요합니다")
		os.Exit(2)
	}
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	http.HandleFunc("POST /", hook)
	if err := http.ListenAndServe(addr, nil); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
