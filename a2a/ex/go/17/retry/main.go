// 다시 해도 되는 실패만, 간격을 두 배씩 늘려 다시 한다.
//
//	go run ./17/retry 카드주소 죽은주소
package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: retry
// retry: safe — 두 번 해도 결과가 같은 호출(Get·List·Cancel)인가
func retry(call func() error, safe bool) error {
	wait := 100 * time.Millisecond
	for n := 1; ; n++ {
		err := call()
		if err == nil {
			return nil
		}
		// 요청이 떠나지도 못한 실패(dial)는 늘 다시 해도 된다.
		// 그 밖의 전송 실패(시간 초과 등)는 safe 일 때만.
		var op *net.OpError
		refused := errors.As(err, &op) && op.Op == "dial"
		late := errors.Is(err, context.DeadlineExceeded)
		kind := err.Error()
		if refused {
			kind = op.Err.Error()
		}
		if !(refused || safe && late) || n == 4 {
			fmt.Printf("  시도 %d: %s → 그만\n", n, kind)
			return err
		}
		fmt.Printf("  시도 %d: %s → %v 뒤 다시\n", n, kind, wait)
		time.Sleep(wait)
		wait *= 2 // 지수 백오프(실제로는 지터를 더한다)
	}
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// region: main
func main() {
	ctx := context.Background()
	card, err := agentcard.NewResolver(http.DefaultClient).
		Resolve(ctx, os.Args[1])
	check(err)
	live, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	get := &a2a.GetTaskRequest{ID: "no-such-task"}
	fmt.Println("① 없는 작업")
	retry(func() error { _, err := live.GetTask(ctx, get); return err },
		true)
	bus := map[string]any{
		"headcount": 30, "nights": 1, "depart": "강남역"}
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = "m-retry"
	fmt.Println("② 1.5초에 끊긴 SendMessage")
	retry(func() error {
		short, cancel := context.WithTimeout(ctx, 1500*time.Millisecond)
		defer cancel() // 시도마다 새 제한
		_, err := live.SendMessage(short,
			&a2a.SendMessageRequest{Message: msg})
		return err
	}, false)
	// 실험용 — 카드의 주소만 아무도 듣지 않는 포트로 바꿔 끼운다
	card.SupportedInterfaces[0].URL = os.Args[2]
	gone, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	fmt.Println("③ 죽은 주소에 GetTask")
	retry(func() error { _, err := gone.GetTask(ctx, get); return err },
		true)
}

// endregion

//@ norun
