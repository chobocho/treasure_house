// 맨손 숙소 에이전트 — SDK 없이, 표준 라이브러리만으로 A2A v1.0.
//
// JSON-RPC 바인딩 하나: 카드, SendMessage, GetTask, CancelTask,
// SendStreamingMessage(SSE). 업무 규칙은 workshop 패키지가 정하고,
// 말과 기록은 완성 에이전트(agents/lodging)와 같다.
//
//	go run ./06/bare_lodging --port P [--url 카드에_적을_주소]
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"

	bs "example.com/workshop/06/barestore"
	"example.com/workshop/workshop"
)

// region: card
// newCard 는 완성 에이전트의 카드와 같은 필드·같은 값(3부).
// 맵이라 와이어의 키는 알파벳 차례가 된다(2부 — Go 는 맵 키를 정렬).
func newCard(url string) map[string]any {
	return map[string]any{
		"name":        "보물상사 숙소 에이전트",
		"description": "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
		"supportedInterfaces": []any{map[string]any{"url": url,
			"protocolBinding": "JSONRPC", "protocolVersion": "1.0"}},
		"provider": map[string]any{"organization": "보물상사",
			"url": "https://treasure-house.example"},
		"version":      "1.0.0",
		"capabilities": map[string]any{"streaming": true},
		"defaultInputModes": []string{
			"application/json", "text/plain"},
		"defaultOutputModes": []string{"application/json"},
		"skills": []any{map[string]any{
			"id":          "find-lodging",
			"name":        "숙소 찾기",
			"description": "워크숍 숙소를 고르고 견적을 냅니다.",
			"tags":        []string{"lodging", "workshop"},
			"examples": []string{
				`{"date":"2026-10-30","nights":1,"headcount":30}`},
		}},
	}
}

// endregion

// region: rpc-error
// rpcError 는 JSON-RPC 의 error 객체 하나 — code·message·data.
// Go 의 error 이기도 해서 처리 함수가 그대로 돌려줄 수 있다.
type rpcError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    []any  `json:"data,omitempty"`
}

func (e *rpcError) Error() string { return e.Message }

// endregion

// region: a2a-errors
const google = "type.googleapis.com/google.rpc."

// §5.4 의 A2A 오류 가운데 이 서버가 내는 넷 — 코드·문구·reason
var a2aErrors = map[string]struct {
	code            int
	message, reason string
}{
	"TaskNotFound": {-32001, "Task not found", "TASK_NOT_FOUND"},
	"TaskNotCancelable": {-32002, "Task cannot be canceled",
		"TASK_NOT_CANCELABLE"},
	"UnsupportedOperation": {-32004, "Unsupported operation",
		"UNSUPPORTED_OPERATION"},
	"VersionNotSupported": {-32009, "Version not supported",
		"VERSION_NOT_SUPPORTED"},
}

// a2aError — data 에 google.rpc.ErrorInfo 하나(§9.5).
func a2aError(name, key, value string) *rpcError {
	e := a2aErrors[name]
	info := map[string]any{"@type": google + "ErrorInfo",
		"reason": e.reason, "domain": "a2a-protocol.org",
		"metadata": map[string]string{key: value}}
	return &rpcError{e.code, e.message, []any{info}}
}

// badParams — -32602, 어느 필드가 왜 틀렸는지 BadRequest 로(§9.5).
func badParams(field, why string) *rpcError {
	v := map[string]string{"field": field, "description": why}
	data := map[string]any{"@type": google + "BadRequest",
		"fieldViolations": []any{v}}
	return &rpcError{-32602, "Invalid parameters", []any{data}}
}

// endregion

// region: version
// checkVersion: §3.6.2 — 요청의 판으로 처리하고, 모르는 판이면 -32009.
// 빈 값은 0.3 으로 읽는다. 패치 번호(1.0.1 의 .1)는 보지 않는다.
func checkVersion(h http.Header) *rpcError {
	asked := h.Get("A2A-Version")
	if asked == "" {
		asked = "0.3"
	}
	f := strings.Split(asked, ".")
	if len(f) < 2 || f[0] != "1" || f[1] != "0" {
		return a2aError("VersionNotSupported", "version", asked)
	}
	return nil
}

// endregion

// region: lodging
var store = bs.New()

// 빠진 항목을 하나씩 되묻는다. 순서가 곧 묻는 순서다.
var order = []string{"date", "nights", "headcount"}
var questions = map[string]string{
	"date":      "날짜는 언제입니까? (예: 2026-10-30)",
	"nights":    "며칠 묵습니까? (예: 1박)",
	"headcount": "인원은 몇 명입니까?",
}
var rules = map[string]*regexp.Regexp{"date": workshop.ReDate,
	"nights": workshop.ReNights, "headcount": workshop.ReHeadcount}

// heard: 사용자가 지금까지 한 말 → 요청. DataPart 먼저, 글이 덮는다.
// 에이전트의 물음은 건너뛴다 — 물음 속 '예: 1박' 은 답이 아니다.
func heard(t *bs.Task) map[string]any {
	var parts []bs.Part
	for _, m := range t.History {
		if m.Role == "ROLE_USER" {
			parts = append(parts, m.Parts...)
		}
	}
	req := map[string]any{}
	for _, p := range parts {
		if d, ok := p["data"].(map[string]any); ok {
			for k, v := range d {
				req[k] = v
			}
		}
	}
	for _, p := range parts {
		text, _ := p["text"].(string)
		for key, rx := range rules {
			if m := rx.FindStringSubmatch(text); m != nil {
				req[key] = m[1]
			}
		}
	}
	return req
}

// endregion

// region: work
// lodging 은 완성 에이전트의 실행기가 하는 일. 이벤트 목록을 돌려준다.
func lodging(t *bs.Task) ([]bs.Event, error) {
	req := heard(t)
	var missing []string
	for _, k := range order {
		if _, ok := req[k]; !ok {
			missing = append(missing, k)
		}
	}
	if len(missing) > 0 {
		fmt.Printf("[숙소] 되묻기: %s\n", pyList(missing))
		ev, err := bs.Move(t, bs.InputRequired,
			bs.Part{"text": questions[missing[0]]},
			bs.Part{"data": map[string]any{"missing": missing}})
		return []bs.Event{ev}, err
	}
	date, _ := req["date"].(string)
	quote, fail := workshop.ChooseLodging(workshop.LodgingRequest{
		Date: date, Nights: toInt(req["nights"]),
		Headcount: toInt(req["headcount"])})
	if fail != nil {
		fmt.Printf("[숙소] 거절: %s\n", fail.Reason)
		ev, err := bs.Move(t, bs.Rejected, bs.Part{"text": fail.Reason})
		return []bs.Event{ev}, err
	}
	summary := fmt.Sprintf("%s %d실, %s원",
		quote.VenueName, quote.Rooms, comma(quote.Total))
	fmt.Printf("[숙소] 견적: %s\n", summary)
	art := bs.AddArtifact(t, "숙소 견적",
		bs.Part{"data": quote}, bs.Part{"text": summary})
	done, err := bs.Move(t, bs.Completed)
	return []bs.Event{art, done}, err
}

// endregion

// region: helpers
// toInt: DataPart 의 수는 float64(30), 글에서 읽은 것은 문자열("30").
func toInt(v any) int {
	switch n := v.(type) {
	case float64:
		return int(n)
	case string:
		i, _ := strconv.Atoi(n)
		return i
	}
	return 0
}

// pyList: ['headcount'] — 파이썬이 리스트를 찍는 모양(서버 기록용).
func pyList(xs []string) string {
	q := make([]string, len(xs))
	for i, x := range xs {
		q[i] = "'" + x + "'"
	}
	return "[" + strings.Join(q, ", ") + "]"
}

func comma(n int) string {
	s := strconv.Itoa(n)
	for i := len(s) - 3; i > 0; i -= 3 {
		s = s[:i] + "," + s[i:]
	}
	return s
}

// endregion

// region: check
// sendParams 는 SendMessageRequest 에서 이 서버가 읽는 것만.
type sendParams struct {
	Message       *bs.Message `json:"message"`
	Configuration struct {
		HistoryLength *int `json:"historyLength"`
	} `json:"configuration"`
}

// readSend: 인자를 읽고 message 의 필수 필드(§5.7)를 본다 — -32602.
func readSend(raw json.RawMessage) (sendParams, error) {
	var p sendParams
	if err := json.Unmarshal(raw, &p); err != nil {
		return p, badParams("params", err.Error())
	}
	return p, checkMessage(p.Message)
}

func checkMessage(m *bs.Message) error {
	switch {
	case m == nil:
		return badParams("message", "메시지가 없습니다")
	case m.MessageID == "":
		return badParams("message.messageId", "비어 있습니다")
	case m.Role != "ROLE_USER":
		return badParams("message.role", "ROLE_USER 여야 합니다")
	case len(m.Parts) == 0:
		return badParams("message.parts", "파트가 하나도 없습니다")
	}
	for _, p := range m.Parts {
		n := 0
		for _, k := range []string{"text", "raw", "url", "data"} {
			if _, ok := p[k]; ok {
				n++
			}
		}
		if n != 1 { // Part 의 oneof(4부)
			why := "text·raw·url·data 중 하나만 있어야 합니다"
			return badParams("message.parts", why)
		}
	}
	return nil
}

// endregion

// region: find
// find: id 로 작업을 찾는다 — 없으면 -32001(§3.4.2).
func find(id string) (*bs.Task, error) {
	if t := store.Get(id); t != nil {
		return t, nil
	}
	return nil, a2aError("TaskNotFound", "taskId", id)
}

// endregion

// region: begin
// begin 은 두 Send 메서드의 앞부분 — 새 작업이거나 이어 말하기다.
func begin(msg bs.Message) (*bs.Task, error) {
	if msg.TaskID == "" {
		return store.Create(msg), nil
	}
	t, err := find(msg.TaskID)
	if err != nil {
		return nil, err
	}
	if msg.ContextID != "" && msg.ContextID != t.ContextID { // §3.4.3
		why := "작업의 contextId 와 다릅니다"
		return nil, badParams("message.contextId", why)
	}
	if !bs.CanMove(t.Status.State, bs.Working) {
		// 종료 상태 — 표에 나갈 곳이 없다(§3.1.1)
		return nil, a2aError("UnsupportedOperation", "taskId", t.ID)
	}
	bs.Move(t, bs.Working) // 지난 물음은 이 때 이력으로 내려간다
	store.Append(t, msg)
	return t, nil
}

// endregion

// region: send
// sendMessage: 막는 호출 — 끝나거나 멈출 때까지 다 하고 Task 를 준다.
func sendMessage(raw json.RawMessage) (any, error) {
	p, err := readSend(raw)
	if err != nil {
		return nil, err
	}
	n, err := length(p.Configuration.HistoryLength)
	if err != nil {
		return nil, err
	}
	t, err := begin(*p.Message)
	if err != nil {
		return nil, err
	}
	// 이벤트는 버린다 — 결과는 저장소의 Task 에
	if _, err := lodging(t); err != nil {
		return nil, err
	}
	return map[string]any{"task": bs.View(t, n)}, nil
}

// endregion

// region: get
// length: historyLength — 없으면 -1(전부), 음수는 -32602.
func length(n *int) (int, error) {
	if n == nil {
		return -1, nil
	}
	if *n < 0 {
		return 0, badParams("historyLength", "0 이상의 정수여야 합니다")
	}
	return *n, nil
}

func getTask(raw json.RawMessage) (any, error) {
	p, err := readTask(raw) // 틀린 모양이면 -32602
	if err != nil {
		return nil, err
	}
	n, err := length(p.HistoryLength)
	if err != nil {
		return nil, err
	}
	t, err := findRaw(p.ID)
	if err != nil {
		return nil, err
	}
	return bs.View(t, n), nil
}

// endregion

// region: params
// GetTask·CancelTask 의 인자. id 는 바이트로 들고 있다가 손으로 본다.
type taskParams struct {
	ID            json.RawMessage `json:"id"`
	HistoryLength *int            `json:"historyLength"`
}

// readTask: Unmarshal 은 맞지 않는 필드를 만나도 끝까지 채운 뒤에야
// 오류를 준다. 오류를 버리면 반쯤 읽은 값으로 일하게 된다(8장).
// id 는 RawMessage 라 여기서 걸리는 것은 historyLength 뿐이다.
func readTask(raw json.RawMessage) (taskParams, error) {
	var p taskParams
	if err := json.Unmarshal(raw, &p); err != nil {
		why := "0 이상의 정수여야 합니다"
		return p, badParams("historyLength", why)
	}
	return p, nil
}

// findRaw: 문자열 id 만 작업을 찾는다. 수 5 는 받은 글자("5") 그대로
// 없는 작업으로 알린다 — 파이썬 str(5)·TS String(5) 와 같은 답.
func findRaw(id json.RawMessage) (*bs.Task, error) {
	var s string
	if json.Unmarshal(id, &s) != nil {
		return nil, a2aError("TaskNotFound", "taskId", string(id))
	}
	return find(s)
}

// endregion

// region: cancel
// cancelTask: 취소 — 이미 CANCELED 면 그대로 돌려준다(§3.3.1 멱등).
func cancelTask(raw json.RawMessage) (any, error) {
	var p struct {
		ID json.RawMessage `json:"id"`
	}
	// 어떤 값이든 바이트로 담기니 실패하지 않는다
	json.Unmarshal(raw, &p)
	t, err := findRaw(p.ID)
	if err != nil {
		return nil, err
	}
	if t.Status.State != bs.Canceled {
		if !bs.CanMove(t.Status.State, bs.Canceled) {
			return nil, a2aError("TaskNotCancelable", "taskId", t.ID)
		}
		bs.Move(t, bs.Canceled)
	}
	return bs.View(t, -1), nil
}

// endregion

// region: stream
// sendStreamingMessage: 첫 이벤트는 늘 Task 다(§3.1.2). 이어 말할 때도.
// 돌려주는 것은 StreamResponse 의 목록. 숙소 일은 기다릴 것이
// 없어 한 번에 다 나오고, 내보내기(SSE)는 http 쪽이 한다.
func sendStreamingMessage(raw json.RawMessage) (any, error) {
	p, err := readSend(raw)
	if err != nil {
		return nil, err
	}
	t, err := begin(*p.Message)
	if err != nil {
		return nil, err
	}
	first := bs.Event{Task: bs.View(t, -1)} // 지금 모습을 먼저 떠 둔다
	rest, err := lodging(t)
	return append([]bs.Event{first}, rest...), err
}

// endregion

// region: methods
// 메서드 이름(§9.4, PascalCase) → 처리 함수, 답이 SSE 스트림인가
type method struct {
	fn      func(json.RawMessage) (any, error)
	streams bool
}

var methods = map[string]method{
	"SendMessage":          {sendMessage, false},
	"SendStreamingMessage": {sendStreamingMessage, true},
	"GetTask":              {getTask, false},
	"CancelTask":           {cancelTask, false},
}

// endregion

// region: dispatch
type request struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"` // 받은 글자 그대로 돌려준다
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

// dispatch: 본문 → (JSON-RPC 응답, nil) 또는 (nil, 스트림 응답들).
func dispatch(body []byte, h http.Header) (any, []any) {
	var req request
	if !json.Valid(body) {
		return failure(nil, &rpcError{Code: -32700,
			Message: "Invalid JSON payload"}), nil
	}
	// 배치(배열)와 알림(id 없음)은 받지 않는다 — A2A 는 늘 답을 준다
	if json.Unmarshal(body, &req) != nil || req.JSONRPC != "2.0" ||
		req.Method == "" || !plainID(req.ID) {
		return failure(nil, &rpcError{Code: -32600,
			Message: "Request payload validation error"}), nil
	}
	result, streams, err := call(req, h)
	if err != nil {
		return failure(req.ID, err), nil
	}
	if !streams {
		return ok(req.ID, result), nil
	}
	var out []any
	for _, ev := range result.([]bs.Event) {
		out = append(out, ok(req.ID, ev))
	}
	return nil, out
}

// endregion

// region: call
// call 은 판·메서드·인자를 보고 처리 함수를 부른다. 저장소는 함수가
// 도는 동안만 잠근다 — 응답을 쓰는(느린) 동안에는 놓아 둔다.
func call(req request, h http.Header) (any, bool, *rpcError) {
	if err := checkVersion(h); err != nil { // 판이 메서드의 뜻을 정한다
		return nil, false, err
	}
	m, found := methods[req.Method]
	if !found {
		return nil, false, &rpcError{Code: -32601,
			Message: "Method not found"}
	}
	if len(req.Params) == 0 || req.Params[0] != '{' {
		return nil, false, badParams("params", "객체여야 합니다")
	}
	store.Mu.Lock()
	result, err := m.fn(req.Params)
	store.Mu.Unlock()
	if e, isRPC := err.(*rpcError); isRPC {
		return nil, false, e
	} else if err != nil { // 우리 코드가 깨졌다 — 전이 표 위반(버그)
		fmt.Fprintf(os.Stderr, "[숙소] 내부 오류: %v\n", err)
		return nil, false, &rpcError{Code: -32603,
			Message: "Internal error"}
	}
	return result, m.streams, nil
}

// endregion

// region: envelope
// plainID: 문자열이나 수만 — 없음(알림)·null·객체는 받지 않는다.
func plainID(id json.RawMessage) bool {
	return len(id) > 0 && (id[0] == '"' || id[0] == '-' ||
		(id[0] >= '0' && id[0] <= '9'))
}

func ok(id json.RawMessage, result any) any {
	return map[string]any{"jsonrpc": "2.0", "id": id, "result": result}
}

func failure(id json.RawMessage, err *rpcError) any {
	if id == nil {
		id = json.RawMessage("null")
	}
	return map[string]any{"jsonrpc": "2.0", "id": id, "error": err}
}

// endregion

// region: http
// 경로 둘 — GET 카드, POST / (JSON-RPC). 나머지는 404.
func handler(c map[string]any) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /.well-known/agent-card.json",
		func(w http.ResponseWriter, r *http.Request) { reply(w, c) })
	mux.HandleFunc("POST /{$}", func(w http.ResponseWriter,
		r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		resp, events := dispatch(body, r.Header)
		if resp != nil {
			reply(w, resp)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for _, ev := range events {
			data, _ := json.Marshal(ev) // data 줄 + 빈 줄(2부)
			fmt.Fprintf(w, "data: %s\n\n", data)
			w.(http.Flusher).Flush()
		}
	}) // 처리 함수가 돌아가면 응답이, 곧 스트림이 끝난다
	return mux
}

func reply(w http.ResponseWriter, v any) {
	data, _ := json.Marshal(v)
	w.Header().Set("Content-Type", "application/json")
	w.Write(data)
}

// endregion

func main() {
	port := flag.Int("port", 0, "들을 포트")
	url := flag.String("url", "", "카드에 적을 주소(기본: 붙는 주소)")
	flag.Parse()
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	if *url == "" {
		*url = "http://" + addr + "/"
	}
	http.ListenAndServe(addr, handler(newCard(*url)))
}

//@ norun
