// 토큰을 확인하는 웹훅 수신기 — 설정에 적어 준 토큰이 아니면 401.
// agents/webhook 은 받은 것을 찍기만 한다. 이것은 문을 지킨다.
//
//	go run ./11/hook_check --port P --token T
package main

import (
	"crypto/subtle"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
)

var want []byte

// region: check
func hook(w http.ResponseWriter, r *http.Request) {
	got := r.Header.Get("X-A2A-Notification-Token")
	// == 대신 ConstantTimeCompare — 걸린 시간으로 토큰을 짐작 못 하게
	if subtle.ConstantTimeCompare([]byte(got), want) != 1 {
		if got == "" {
			got = "-"
		}
		fmt.Printf("거절 401: token=%s\n", got)
		w.WriteHeader(http.StatusUnauthorized)
		return
	}
	var body map[string]json.RawMessage
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	for kind := range body { // 몸통의 키는 하나뿐이다
		fmt.Printf("통과 204: %s\n", kind)
	}
	w.WriteHeader(http.StatusNoContent)
}

// endregion

func main() {
	port := flag.Int("port", 0, "붙을 포트(필수)")
	token := flag.String("token", "", "약속한 토큰(필수)")
	flag.Parse()
	if *port == 0 || *token == "" {
		fmt.Fprintln(os.Stderr, "--port 와 --token 이 필요합니다")
		os.Exit(2)
	}
	want = []byte(*token)
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	http.HandleFunc("POST /", hook)
	if err := http.ListenAndServe(addr, nil); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

//@ norun
