// Go SDK 의 push.HTTPPushSender — 기본값이 루프백 웹훅을 막는 것과,
// 막지 않게 했을 때 무슨 머리글을 붙이는지를 본다. 웹훅 둘: 기록만 하는
// 중계기(탭 뒤)와, 토큰 tok-ok 를 X-A2A-Notification-Token 에서 찾는
// 수신기(hook_check). 교통 에이전트가 이 보내기를 쓰지 않는 까닭(4장)의
// 증거다.
//
//	go run ./11/guard 중계기 수신기
package main

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv/push"
)

// region: guard
func main() {
	ctx := context.Background()
	relay, check := os.Args[1], os.Args[2]
	ev := &a2a.Task{ID: "t-guard", ContextID: "c-guard",
		Status: a2a.TaskStatus{State: a2a.TaskStateWorking}}
	cfg := &a2a.PushConfig{TaskID: "t-guard", URL: relay,
		Token: "tok-ok", Auth: &a2a.PushAuthInfo{
			Scheme: "Bearer", Credentials: "hook-secret"}}
	// ① 기본값 — 사설·루프백 주소를 막는다
	// (FailOnError 로 오류를 돌려받는다)
	strict := push.NewHTTPPushSender(
		&push.HTTPSenderConfig{FailOnError: true})
	fmt.Println("① 기본값 →", short(strict.SendPush(ctx, cfg, ev)))
	// ② 사설망 허용 — 닿는다
	open := push.NewHTTPPushSender(&push.HTTPSenderConfig{
		FailOnError: true, AllowPrivateNetworks: true})
	fmt.Println("② 허용, Bearer →", open.SendPush(ctx, cfg, ev))
	// ③ 스킴이 bearer·basic 이 아니면 Authorization 을 붙이지 않는다
	cfg.Auth.Scheme = "Digest"
	fmt.Println("③ 허용, Digest →", open.SendPush(ctx, cfg, ev))
	// ④ 맞는 토큰인데 — X- 머리글을 찾는 수신기에 곧장
	cfg.URL, cfg.Auth.Scheme = check, "Bearer"
	fmt.Println("④ 수신기에 →", open.SendPush(ctx, cfg, ev))
}

// endregion

// short 는 오류를 "dial tcp …" 부터만 — 앞의 "Post URL:" 는 길기만 하다
func short(err error) string {
	s := fmt.Sprint(err)
	if i := strings.Index(s, "dial tcp"); i >= 0 {
		return "…" + s[i:]
	}
	return s
}

//@ norun
