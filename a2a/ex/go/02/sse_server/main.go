// SSE 서버 — net/http 만으로. 식단을 짜며 끼니마다 이벤트 하나를
// 흘려 보내고, 마지막에 합계를 보낸 뒤 연결을 닫는다.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"time"

	"example.com/workshop/workshop"
)

type SlotEvent struct {
	Slot       string `json:"slot"`
	Regular    string `json:"regular"`
	Vegetarian string `json:"vegetarian"`
}

type TotalEvent struct {
	Total int `json:"total"`
}

// 이벤트로 보낼 값들 — 끼니마다 하나, 끝에 합계.
func events(r workshop.MealsRequest) []any {
	plan, f := workshop.PlanMeals(r)
	if f != nil {
		return []any{f}
	}
	var out []any
	for _, s := range plan.Slots {
		out = append(out, SlotEvent{s.Slot, s.Regular.Name,
			s.Vegetarian.Name})
	}
	return append(out, TotalEvent{plan.Total})
}

// region: stream
func stream(w http.ResponseWriter, r *http.Request) {
	var req workshop.MealsRequest
	json.NewDecoder(r.Body).Decode(&req)
	h := w.Header()
	h.Set("Content-Type", "text/event-stream")
	h.Set("Cache-Control", "no-cache")
	flusher := w.(http.Flusher) // 모아 두지 말고 지금 보내는 손잡이
	count := 0
	for _, ev := range events(req) {
		data, _ := json.Marshal(ev)
		// 이벤트 하나 = "data: …" 줄 + 빈 줄
		fmt.Fprintf(w, "data: %s\n\n", data)
		flusher.Flush()
		count++
		time.Sleep(50 * time.Millisecond) // 식단 짜는 시간인 셈
	}
	// 처리기가 돌아가면 응답이 끝나고, 그것이 곧 스트림의 끝
	fmt.Printf("이벤트 %d개를 보내고 닫음\n", count)
}

// endregion

func main() {
	port := flag.Int("port", 0, "들을 포트")
	flag.Parse()
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	fmt.Println("SSE 서버(go):", addr)
	http.ListenAndServe(addr, http.HandlerFunc(stream))
}

//@ norun
