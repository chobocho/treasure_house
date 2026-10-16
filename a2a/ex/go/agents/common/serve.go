package common

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"
)

// Options 는 에이전트마다 다른 서버 부품이다.
type Options struct {
	// 토큰 발급·JWKS 처럼 더 다는 경로
	Routes func(mux *http.ServeMux)
	// JSON-RPC 경로 앞에 세우는 HTTP 검사(정산의 Bearer 401)
	Guard func(http.Handler) http.Handler
	// 카드 경로 처리기. 비면 SDK 의 정적 카드 처리기
	Card http.Handler
	// SDK 요청 처리기 옵션(확장 카드, 푸시, 호출 가로채기 등)
	Handler []a2asrv.RequestHandlerOption
}

// region: serve
// Serve 는 JSON-RPC 와 카드 경로를 단 HTTP 서버를 띄운다.
func Serve(
	card *a2a.AgentCard, exec a2asrv.AgentExecutor, port int,
	o Options,
) {
	store := taskstore.NewInMemory(&taskstore.InMemoryStoreConfig{
		Authenticator: owner,
	})
	opts := append([]a2asrv.RequestHandlerOption{
		a2asrv.WithCapabilityChecks(&card.Capabilities),
		a2asrv.WithTaskStore(store),
	}, o.Handler...)
	h := a2asrv.NewHandler(exec, opts...)
	// SDK 의 처리기는 호출 맥락(사용자)을 붙인 뒤 안쪽 처리기를
	// 부른다. 그 안쪽을 waiter 로 감싸 결재 대기를 이어 준다(park.go).
	if ih, ok := h.(*a2asrv.InterceptedHandler); ok {
		ih.Handler = waiter{ih.Handler}
	}
	var rpc http.Handler = a2asrv.NewJSONRPCHandler(h)
	if o.Guard != nil {
		rpc = o.Guard(rpc)
	}
	cardHandler := o.Card
	if cardHandler == nil {
		cardHandler = a2asrv.NewStaticAgentCardHandler(card)
	}
	mux := http.NewServeMux()
	mux.Handle(a2asrv.WellKnownAgentCardPath, cardHandler)
	mux.Handle("/{$}", rpc) // 정확히 "/" 만
	if o.Routes != nil {
		o.Routes(mux)
	}
	addr := fmt.Sprintf("127.0.0.1:%d", port)
	if err := http.ListenAndServe(addr, mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// endregion

// owner 는 작업의 주인 이름이다. SDK 의 작업 저장소는 이름이 빈 익명
// 호출자에게 ListTasks 를 거절한다(-31401 UNAUTHENTICATED). 파이썬·TS
// 는 익명에게도 목록을 주므로, 익명은 'anonymous' 한 사람으로 본다.
// 토큰을 낸 사용자(정산의 planner)의 작업은 그대로 그 사람 것이다.
func owner(ctx context.Context) (string, error) {
	cc, ok := a2asrv.CallContextFrom(ctx)
	if !ok {
		return "", a2a.ErrUnauthenticated
	}
	if cc.User == nil || cc.User.Name == "" {
		return "anonymous", nil
	}
	return cc.User.Name, nil
}

// Say 는 서버 로그 한 줄. 표준 출력은 캡처되므로 이 줄만 찍는다
// (SDK 의 slog 기록은 표준 오류로 간다).
func Say(format string, a ...any) {
	fmt.Printf(format+"\n", a...)
}

// ProtoJSON 은 카드를 프로토 JSON 모양 바이트로 만든다: false·빈
// 문자열·빈 목록처럼 기본값인 필드를 뺀다. Go SDK 는 이런 값도
// 적어 내지만(예: "pushNotifications":false) 파이썬·TS 는 빼고 낸다.
// 서명은 세 SDK 가 같은 바이트를 정규화해야 맞으므로, 서명하는
// 카드는 이 모양으로 서명하고 이 모양 그대로 내보낸다.
func ProtoJSON(card *a2a.AgentCard) []byte {
	var v any
	raw, err := json.Marshal(card)
	if err == nil {
		err = json.Unmarshal(raw, &v)
	}
	if err != nil {
		panic(err)
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(dropDefaults(v)); err != nil {
		panic(err)
	}
	return bytes.TrimRight(buf.Bytes(), "\n")
}

func dropDefaults(v any) any {
	switch x := v.(type) {
	case map[string]any:
		out := map[string]any{}
		for k, e := range x {
			if e = dropDefaults(e); e != nil {
				out[k] = e
			}
		}
		if len(out) == 0 {
			return nil
		}
		return out
	case []any:
		var out []any
		for _, e := range x {
			if e = dropDefaults(e); e != nil {
				out = append(out, e)
			}
		}
		if len(out) == 0 {
			return nil
		}
		return out
	case string:
		if x == "" {
			return nil
		}
	case bool:
		if !x {
			return nil
		}
	}
	return v
}

// CardBytes 는 미리 만든 카드 바이트를 그대로 내보내는 카드 생산자다
// (SDK 의 AgentCardJSONProducer). Card 는 쓰이지 않지만 인터페이스
// 몫으로 둔다.
type CardBytes []byte

func (b CardBytes) CardJSON(context.Context) ([]byte, error) {
	return b, nil
}

func (b CardBytes) Card(context.Context) (*a2a.AgentCard, error) {
	var c a2a.AgentCard
	return &c, json.Unmarshal(b, &c)
}
