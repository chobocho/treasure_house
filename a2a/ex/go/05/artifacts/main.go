// 식사 에이전트에 식단을 맡기고(막는 호출), 끝난 Task 의 아티팩트를
// 하나씩 읽는다 — id·이름·설명, 파트의 종류, metadata·extensions.
//
//	go run ./05/artifacts 카드주소
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"slices"
	"unicode/utf8"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

var meals = map[string]any{
	"nights": 1, "headcount": 30, "vegetarians": 2,
}

// region: read
func part(p *a2a.Part) string {
	switch c := p.Content.(type) {
	case a2a.Text: // 글자 수는 룬으로 센다(len 은 바이트)
		n := utf8.RuneCountInString(string(c))
		return fmt.Sprintf("text %d자", n)
	case a2a.Raw:
		return fmt.Sprintf("raw %s %s %d바이트",
			p.Filename, p.MediaType, len(c))
	case a2a.Data:
		m, _ := c.Value.(map[string]any)
		keys := slices.Sorted(func(yield func(string) bool) {
			for k := range m {
				if !yield(k) {
					return
				}
			}
		})
		return fmt.Sprintf("data %q…", keys[:3])
	}
	return fmt.Sprintf("%T", p.Content)
}

func read(t *a2a.Task) {
	fmt.Println("아티팩트", len(t.Artifacts), "개")
	for _, a := range t.Artifacts {
		fmt.Printf("- %s '%s' 설명:%q\n", a.ID, a.Name, a.Description)
		for _, p := range a.Parts {
			fmt.Println("    ", part(p))
		}
		meta := map[bool]string{true: "없음", false: "있음"}
		fmt.Printf("    metadata %s, extensions %q\n",
			meta[a.Metadata == nil], a.Extensions)
	}
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func main() {
	ctx := context.Background()
	r := agentcard.NewResolver(http.DefaultClient)
	card, err := r.Resolve(ctx, os.Args[1])
	check(err)
	c, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(meals))
	msg.ID = "meals-1"
	req := &a2a.SendMessageRequest{Message: msg}
	res, err := c.SendMessage(ctx, req)
	check(err)
	read(res.(*a2a.Task)) // 식사 에이전트는 Task 로 답한다
}

//@ norun
