// 떠 있는 숙소 에이전트를 골든 벡터로 검사한다 — 업무 규칙
// 시험(workshop/domain_test.go)과 같은 기대값을, 이번에는 A2A 를
// 거쳐서. 사례마다 새 작업 하나(막는 호출).
//
//	go run ./09/golden_lodging URL
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

type goldenCase struct {
	Name     string
	Input    any
	Expected any
}

func cases() []goldenCase {
	raw, err := os.ReadFile(workshop.FixturePath("golden/domain.json"))
	if err != nil {
		panic(err)
	}
	var all map[string][]goldenCase
	if err := json.Unmarshal(raw, &all); err != nil {
		panic(err)
	}
	return all["chooseLodging"]
}

// region: check
// 완료면 아티팩트의 DataPart, 거절이면 상태 메시지의 까닭
func answerOf(t *a2a.Task) any {
	if t.Status.State == a2a.TaskStateCompleted {
		return t.Artifacts[0].Parts[0].Data()
	}
	return map[string]any{"ok": false,
		"reason": common.TextOf(t.Status.Message)}
}

func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	if err != nil {
		panic(err)
	}
	client, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		panic(err)
	}
	defer client.Destroy()
	all, passed := cases(), 0
	for i, c := range all {
		m := a2a.NewMessage(a2a.MessageRoleUser,
			a2a.NewDataPart(c.Input))
		m.ID = fmt.Sprintf("g-%d", i+1)
		res, err := client.SendMessage(ctx,
			&a2a.SendMessageRequest{Message: m})
		if err != nil {
			panic(err)
		}
		t := res.(*a2a.Task)
		// 양쪽 다 JSON 에서 풀린 값(수는 float64)이라 바로 견준다
		ok := reflect.DeepEqual(answerOf(t), c.Expected)
		passed += map[bool]int{true: 1}[ok]
		mark := map[bool]string{true: "O", false: "X"}[ok]
		state := strings.TrimPrefix(string(t.Status.State),
			"TASK_STATE_")
		fmt.Printf("%s %-28s %s\n", mark, c.Name, state)
	}
	fmt.Printf("%d/%d 골든과 같음\n", passed, len(all))
}

// endregion

//@ norun
