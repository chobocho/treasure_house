// SDK 클라이언트로 식사 에이전트의 스트림을 받아 이벤트를 Task 하나로
// 접는다(4장). -cut 이면 첫 조각 뒤에 끊고 SubscribeToTask 로 다시
// 붙어 이어 접는다(5장). 끝으로 GetTask 의 아티팩트와 견준다.
//
//	go run ./10/fold [-cut] URL
package main

import (
	"context"
	"encoding/gob"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	"github.com/a2aproject/a2a-go/v2/a2aevent"
)

func name(s a2a.TaskState) string {
	return strings.TrimPrefix(string(s), "TASK_STATE_")
}

func arts(t *a2a.Task) string {
	var out []string
	for _, a := range t.Artifacts {
		out = append(out, fmt.Sprintf("%s×%d", a.ID, len(a.Parts)))
	}
	return strings.Join(out, " ")
}

// region: fold
// fold 는 이벤트 하나를 view 에 접는다. Task 는 통째로 바꾸고,
// 나머지는 SDK 의 공개 함수 a2aevent.ApplyUpdate 에 맡긴다.
func fold(view *a2a.Task, ev a2a.Event) (*a2a.Task, error) {
	if t, ok := ev.(*a2a.Task); ok {
		return t, nil // 첫 이벤트(다시 붙은 뒤에도)
	}
	if view == nil {
		return nil, fmt.Errorf("첫 이벤트가 Task 가 아니다")
	}
	// 새 Task 를 돌려준다 — 넘긴 view 는 고치지 않는다
	return a2aevent.ApplyUpdate(view, ev)
}

// endregion

// region: resub
// resubscribe 는 같은 taskId 로 다시 붙어 이어 접는다
func resubscribe(
	ctx context.Context, c *a2aclient.Client, view *a2a.Task,
) (*a2a.Task, error) {
	m := 0
	req := &a2a.SubscribeToTaskRequest{ID: view.ID}
	for ev, err := range c.SubscribeToTask(ctx, req) {
		if err != nil {
			return nil, err
		}
		if m++; m == 1 {
			if t, ok := ev.(*a2a.Task); ok {
				fmt.Printf("다시 붙음 — task %s %s\n",
					name(t.Status.State), arts(t))
			}
		}
		if view, err = fold(view, ev); err != nil {
			return nil, err
		}
	}
	fmt.Printf("구독으로 이벤트 %d개\n", m)
	return view, nil
}

// endregion

// region: send
func run(ctx context.Context, url string, cut bool) error {
	card, err := agentcard.DefaultResolver.Resolve(ctx, url)
	if err != nil {
		return err
	}
	c, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		return err
	}
	defer c.Destroy()
	ask := map[string]any{
		"nights": 1, "headcount": 30, "vegetarians": 2}
	m := a2a.NewMessage(a2a.MessageRoleUser,
		a2a.NewTextPart("식단 부탁합니다"), a2a.NewDataPart(ask))
	m.ID = "f-1"
	var view *a2a.Task
	n := 0
	req := &a2a.SendMessageRequest{Message: m}
	for ev, err := range c.SendStreamingMessage(ctx, req) {
		if err != nil {
			return err
		}
		if view, err = fold(view, ev); err != nil {
			return fmt.Errorf("이벤트 %d 접기: %w", n+1, err)
		}
		n++
		if _, ok := ev.(*a2a.TaskArtifactUpdateEvent); ok && cut {
			fmt.Printf("이벤트 %d개 뒤에 끊음 — %s\n", n, arts(view))
			break // SDK 가 응답 본문을 닫는다
		}
	}
	if cut {
		if view, err = resubscribe(ctx, c, view); err != nil {
			return err
		}
	} else {
		fmt.Printf("이벤트 %d개\n", n)
	}
	return report(ctx, c, view)
}

// endregion

// region: files
// files 는 파일 파트와 데이터 파트를 꺼낸다 — 마지막 두 아티팩트
func files(view *a2a.Task) {
	for _, a := range view.Artifacts[1:] {
		p := a.Parts[0]
		switch c := p.Content.(type) {
		case a2a.Raw: // []byte
			head, _, _ := strings.Cut(string(c), "\n")
			fmt.Printf("  %s %s %d바이트 — %q\n",
				p.Filename, p.MediaType, len(c), head)
		case a2a.Data: // encoding/json 이 푼 any
			total := c.Value.(map[string]any)["total"]
			fmt.Printf("  %s total %v (%T)\n", a.Name, total, total)
		}
	}
}

// endregion

func report(
	ctx context.Context, c *a2aclient.Client, view *a2a.Task,
) error {
	fmt.Printf("접은 Task — %s %s\n",
		name(view.Status.State), arts(view))
	for _, p := range view.Artifacts[0].Parts {
		fmt.Print("  " + p.Text())
	}
	files(view)
	got, err := c.GetTask(ctx, &a2a.GetTaskRequest{ID: view.ID})
	if err != nil {
		return err
	}
	a, _ := json.Marshal(got.Artifacts) // 맵 키는 정렬되어 나온다
	b, _ := json.Marshal(view.Artifacts)
	fmt.Println("GetTask 와 아티팩트가 같다:", string(a) == string(b))
	return nil
}

func main() {
	cut := flag.Bool("cut", false, "첫 조각 뒤에 끊고 다시 붙기")
	bare := flag.Bool("bare", false, "gob 등록 없이(실패를 보려고)")
	flag.Parse()
	// region: gob
	// ApplyUpdate 는 Task 를 gob 으로 복사한다. DataPart 의 JSON 객체·
	// 배열을 gob 에 알리는 것은 SDK 의 저장소 패키지뿐이라
	// (taskstore/inmemory.go), 저장소가 없는 클라이언트는 직접 한다.
	if !*bare {
		gob.Register(map[string]any{})
		gob.Register([]any{})
	}
	// endregion
	err := run(context.Background(), flag.Arg(0), *cut)
	if err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}

//@ norun
