// SDK 클라이언트로 HTTP+JSON 문을 쓴다 — 서버 셋에 같은 세 가지를.
//
//	go run ./13/rest_client 이름=URL …
//
// 1) 막는 SendMessage  2) 없는 작업 GetTask  3) 없는 작업에 잇는 스트림
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

func msg(taskID a2a.TaskID) *a2a.SendMessageRequest {
	m := a2a.NewMessage(a2a.MessageRoleUser,
		a2a.NewTextPart("2026-10-30 1박 30명"))
	m.ID, m.TaskID = "c-1", taskID
	return &a2a.SendMessageRequest{Message: m}
}

// kindOf: 표지 오류(sentinel) 가운데 어느 것에 걸리나
func kindOf(err error) string {
	if err == nil {
		return "성공"
	}
	for _, s := range []error{a2a.ErrTaskNotFound,
		a2a.ErrServerError, a2a.ErrInternalError} {
		if errors.Is(err, s) {
			return fmt.Sprintf("%q", s.Error())
		}
	}
	return fmt.Sprintf("%T", err)
}

// region: client
func one(ctx context.Context, label, url string) error {
	card, err := agentcard.DefaultResolver.Resolve(ctx, url)
	if err != nil {
		return err
	}
	// Go 공장도 기본으로 JSON-RPC 와 HTTP+JSON 을 둘 다 안다
	client, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		return err
	}
	defer client.Destroy()
	res, err := client.SendMessage(ctx, msg(""))
	if err != nil {
		return err
	}
	state := strings.TrimPrefix(
		string(res.(*a2a.Task).Status.State), "TASK_STATE_")
	_, err = client.GetTask(ctx, &a2a.GetTaskRequest{ID: "t-nope"})
	got := kindOf(err)
	var sub error
	stream := client.SendStreamingMessage(ctx, msg("t-nope"))
	for _, err := range stream {
		sub = err
	}
	fmt.Printf("%s: 보내기 %s | 없는 작업 %s | 잇기 %s\n",
		label, state, got, kindOf(sub))
	return nil
}

// endregion

func main() {
	for _, arg := range os.Args[1:] {
		label, url, _ := strings.Cut(arg, "=")
		if err := one(context.Background(), label, url); err != nil {
			fmt.Println(label+":", err)
		}
	}
}

//@ norun
