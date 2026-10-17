// a2a 의 표지 오류(Err…)마다 JSON-RPC 코드와 HTTP+JSON 상태 — SDK 의
// 전송 처리기에 오류만 돌려주는 가짜 처리기를 물려 물어본다.
//
//	go run ./09/error_codes
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"slices"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

// region: fake
// RequestHandler 를 품고 GetTask 하나만 덮어쓴다(나머지는 안 부른다)
type fails struct {
	a2asrv.RequestHandler
	err error
}

func (f fails) GetTask(context.Context, *a2a.GetTaskRequest,
) (*a2a.Task, error) {
	return nil, f.err
}

// codes 는 같은 오류를 JSON-RPC 와 HTTP+JSON 으로 보낸 답이다.
func codes(err error) (int, int) {
	rpc := a2asrv.NewJSONRPCHandler(fails{err: err})
	rec := httptest.NewRecorder()
	rpc.ServeHTTP(rec, httptest.NewRequest("POST", "/",
		strings.NewReader(`{"jsonrpc":"2.0","id":1,
		  "method":"GetTask","params":{"id":"t-1"}}`)))
	var r struct{ Error struct{ Code int } }
	_ = json.Unmarshal(rec.Body.Bytes(), &r)
	rest := a2asrv.NewRESTHandler(fails{err: err})
	rec = httptest.NewRecorder()
	rest.ServeHTTP(rec, httptest.NewRequest("GET", "/tasks/t-1", nil))
	return r.Error.Code, rec.Code
}

// endregion

func main() {
	// region: codes
	for _, e := range []struct {
		name string
		err  error
	}{
		{"ErrParseError", a2a.ErrParseError},
		{"ErrInvalidRequest", a2a.ErrInvalidRequest},
		{"ErrMethodNotFound", a2a.ErrMethodNotFound},
		{"ErrInvalidParams", a2a.ErrInvalidParams},
		{"ErrInternalError", a2a.ErrInternalError},
		{"ErrServerError", a2a.ErrServerError},
		{"ErrTaskNotFound", a2a.ErrTaskNotFound},
		{"ErrTaskNotCancelable", a2a.ErrTaskNotCancelable},
		{"ErrPushNotificationNotSupported",
			a2a.ErrPushNotificationNotSupported},
		{"ErrUnsupportedOperation", a2a.ErrUnsupportedOperation},
		{"ErrUnsupportedContentType", a2a.ErrUnsupportedContentType},
		{"ErrInvalidAgentResponse", a2a.ErrInvalidAgentResponse},
		{"ErrExtendedCardNotConfigured",
			a2a.ErrExtendedCardNotConfigured},
		{"ErrExtensionSupportRequired",
			a2a.ErrExtensionSupportRequired},
		{"ErrVersionNotSupported", a2a.ErrVersionNotSupported},
		{"ErrUnauthenticated", a2a.ErrUnauthenticated},
		{"ErrUnauthorized", a2a.ErrUnauthorized},
		{"fmt.Errorf(\"…: %w\", …)",
			fmt.Errorf("작업 t-1: %w", a2a.ErrTaskNotFound)},
		{"errors.New(\"…\")", fmt.Errorf("아무 오류")},
	} {
		rpc, http := codes(e.err)
		fmt.Printf("%-33s %7d  %d\n", e.name, rpc, http)
	}
	// endregion

	// region: two
	// 표지 둘을 함께 감싼 오류 — 코드는 어느 쪽인가(200번 물어본다)
	both := fmt.Errorf("%w: %w", a2a.ErrTaskNotFound,
		a2a.ErrInvalidParams)
	var seen []int
	var rest int
	for range 200 {
		rpc, http := codes(both)
		if !slices.Contains(seen, rpc) {
			seen = append(seen, rpc)
		}
		rest = http
	}
	slices.Sort(seen)
	fmt.Println("두 표지를 감싼 오류: JSON-RPC", seen, " HTTP", rest)
	// endregion
}
