// 예산 확장을 켜고 숙소 견적을 묻는 Go SDK 클라이언트.
//
//	go run ./14/budget_client URL
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	"github.com/a2aproject/a2a-go/v2/a2aext"

	"example.com/workshop/agents/common"
)

const URI = "https://treasure-house.example/a2a/ext/budget/v1"

// region: send
func run(ctx context.Context, url string) error {
	card, err := agentcard.DefaultResolver.Resolve(ctx, url)
	if err != nil {
		return err
	}
	kind := "선택"
	for _, e := range card.Capabilities.Extensions {
		if e.URI == URI && e.Required {
			kind = "필수"
		}
	}
	fmt.Println("카드:", kind)
	// 활성기: 카드가 적은 확장일 때만 A2A-Extensions 에 싣는다
	client, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithCallInterceptors(a2aext.NewActivator(URI)))
	if err != nil {
		return err
	}
	defer client.Destroy()
	m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(
		map[string]any{"date": "2026-10-30", "nights": 1,
			"headcount": 30}))
	m.ID = "b-1"
	m.Extensions = []string{URI} // 이 메시지에 확장의 데이터가 있다
	m.Metadata = map[string]any{URI: map[string]any{"limit": 2000000}}
	req := &a2a.SendMessageRequest{Message: m}
	res, err := client.SendMessage(ctx, req)
	if err != nil {
		return err
	}
	if t, ok := res.(*a2a.Task); ok {
		show(t.Artifacts[0])
	}
	return nil
}

// endregion

// region: show
func show(art *a2a.Artifact) {
	data, _ := art.Parts[0].Data().(map[string]any)
	total := common.Int(data["total"])
	got, ok := art.Metadata[URI].(map[string]any)
	if !ok {
		fmt.Printf("견적 %s원 · 판정 없음\n", common.Comma(total))
		return
	}
	verdict := "넘음"
	if got["within"] == true {
		verdict = "안"
	}
	fmt.Printf("견적 %s원 · 상한 %s원 %s\n", common.Comma(total),
		common.Comma(common.Int(got["limit"])), verdict)
}

// endregion

func main() {
	if err := run(context.Background(), os.Args[1]); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}

//@ norun
