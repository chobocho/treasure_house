// 고치기 전의 교통 에이전트 hookSender — agents/bus/main.go 의 그
// 자리를 2026-10-18 에 고치기 전 모습 그대로 옮겨 두었다(8장의 "전").
// 설정에 authentication 과 틀린 토큰을 함께 실어 한 번 보낸다.
//
//	go run ./11/hookold 웹훅
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

// region: push
// hookSender 는 푸시 알림을 웹훅에 POST 한다. SDK 의 HTTPPushSender
// 를 쓰지 않는 까닭 둘: 토큰 머리글 이름이 A2A-Notification-Token 으로
// 파이썬·TS 의 X-A2A-Notification-Token 과 다르고(명세는 이름을 정하지
// 않는다), 기본값이 루프백(127.0.0.1) 주소를 막는다.
type hookSender struct{ client *http.Client }

func (s hookSender) SendPush(
	ctx context.Context, cfg *a2a.PushConfig, ev a2a.Event,
) error {
	body, err := json.Marshal(a2a.StreamResponse{Event: ev})
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		cfg.URL, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if cfg.Token != "" {
		req.Header.Set("X-A2A-Notification-Token", cfg.Token)
	}
	resp, err := s.client.Do(req)
	if err != nil {
		// 웹훅이 죽어도 작업은 계속한다(오류를 돌려주면 SDK 가
		// 작업을 FAILED 로 바꾼다). 파이썬 SDK 도 기록만 남긴다.
		slog.Warn("push failed", "url", cfg.URL, "error", err)
		return nil
	}
	return resp.Body.Close()
}

// endregion

func main() {
	s := hookSender{&http.Client{Timeout: 10 * time.Second}}
	ev := &a2a.Task{ID: "t-old", ContextID: "c-old",
		Status: a2a.TaskStatus{State: a2a.TaskStateWorking}}
	cfg := &a2a.PushConfig{TaskID: "t-old", URL: os.Args[1],
		Token: "tok-bad", Auth: &a2a.PushAuthInfo{
			Scheme: "Bearer", Credentials: "hook-secret"}}
	fmt.Println("SendPush →", s.SendPush(context.Background(), cfg, ev))
}

//@ norun
