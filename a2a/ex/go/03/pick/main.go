// 스킬의 태그로 일을 맡길 에이전트를 고른다. 기획 에이전트가
// 15부에서 동료를 찾는 방법의 핵심만 떼어 낸 것이다.
//
//	go run ./03/pick [--out 미디어타입] 태그 카드주소...
package main

import (
	"context"
	"flag"
	"fmt"
	"net/http"
	"os"
	"slices"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: pick
func outModes(card *a2a.AgentCard, s a2a.AgentSkill) []string {
	// 스킬에 적힌 출력 모드가 있으면 그것, 없으면 카드의 기본값
	if len(s.OutputModes) > 0 {
		return s.OutputModes
	}
	return card.DefaultOutputModes
}

func matches(card *a2a.AgentCard, tag, mode string) []a2a.AgentSkill {
	var hit []a2a.AgentSkill
	for _, s := range card.Skills {
		if !slices.Contains(s.Tags, tag) {
			continue
		}
		if mode == "" || slices.Contains(outModes(card, s), mode) {
			hit = append(hit, s)
		}
	}
	return hit
}

// endregion

// region: main
func main() {
	out := flag.String("out", "", "이 출력 모드를 내는 스킬만")
	flag.Parse()
	tag, urls := flag.Arg(0), flag.Args()[1:]
	show := *out
	if show == "" {
		show = "아무거나"
	}
	fmt.Printf("태그 %s · 출력 %s\n", tag, show)
	found := 0
	r := agentcard.NewResolver(http.DefaultClient)
	for _, url := range urls {
		card, err := r.Resolve(context.Background(), url)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		for _, s := range matches(card, tag, *out) {
			found++
			tags := strings.Join(s.Tags, ",")
			modes := strings.Join(outModes(card, s), ",")
			fmt.Printf("  %s · %s [%s] → %s\n",
				card.Name, s.ID, tags, modes)
		}
	}
	fmt.Printf("  고른 곳 %d\n", found)
}

// endregion
//@ norun
