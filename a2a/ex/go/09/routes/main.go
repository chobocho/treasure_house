// SDK 의 HTTP 처리기 셋은 http.Handler — 무엇에 어떻게 답하나.
//
//	go run ./09/routes
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/09/steps"
)

const send = `{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":
  {"message":{"messageId":"m-1","role":"ROLE_USER",
  "parts":[{"text":"안녕"}]}}}`

// region: probe
// probe 는 요청 하나를 처리기에 넣고 상태·형식·본문 앞부분을 찍는다
func probe(name string, h http.Handler, method, path, body string) {
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	out, _ := io.ReadAll(rec.Body)
	text := []rune(strings.TrimSpace(string(out)))
	if len(text) > 50 {
		text = append(text[:50], '…')
	}
	row := fmt.Sprintf("%-4s %-4s %-10s %d %-16s %s", name, method,
		path, rec.Code, rec.Header().Get("Content-Type"), string(text))
	fmt.Println(strings.TrimRight(row, " "))
}

func main() {
	h := a2asrv.NewHandler(steps.Echo{})
	rpc := a2asrv.NewJSONRPCHandler(h)
	card := a2asrv.NewStaticAgentCardHandler(
		steps.EchoCard("http://127.0.0.1:10900/"))
	rest := a2asrv.NewRESTHandler(h)
	probe("rpc", rpc, "POST", "/any/where", send)
	probe("rpc", rpc, "GET", "/", "")
	probe("card", card, "GET", "/any/where", "")
	probe("card", card, "POST", "/", "")
	probe("rest", rest, "GET", "/tasks/t-1", "")
	probe("rest", rest, "GET", "/nowhere", "")
}

// endregion
