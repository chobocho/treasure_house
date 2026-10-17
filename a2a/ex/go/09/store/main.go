// taskstore.InMemory — 누구의 작업인가, 꺼내면 사본인가, 판 번호.
//
//	go run ./09/store
package main

import (
	"context"
	"fmt"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"

	"example.com/workshop/workshop"
)

// as 는 이름 name 으로 로그인한 호출의 맥락이다(빈 이름 = 익명).
func as(name string) context.Context {
	ctx, cc := a2asrv.NewCallContext(context.Background(), nil)
	if name != "" {
		cc.User = a2asrv.NewAuthenticatedUser(name, nil)
	}
	return ctx
}

func found(err error) string {
	if err == nil {
		return "ok" // 찾았다
	}
	return err.Error()
}

func newTask(id a2a.TaskID, parts ...*a2a.Part) *a2a.Task {
	info := a2a.TaskInfo{TaskID: id, ContextID: "c-1"}
	msg := a2a.NewMessage(a2a.MessageRoleUser, parts...)
	return a2a.NewSubmittedTask(info, msg)
}

func main() {
	// region: owner
	// SDK 기본 처리기와 같은 설정 — 주인은 CallContext 의 사용자 이름
	store := taskstore.NewInMemory(&taskstore.InMemoryStoreConfig{
		Authenticator: a2asrv.NewTaskStoreAuthenticator(),
	})
	_, _ = store.Create(as("kim"), newTask("t-kim",
		a2a.NewTextPart("30명")))
	_, _ = store.Create(as(""), newTask("t-anon",
		a2a.NewTextPart("20명")))
	for _, who := range []string{"kim", "lee", ""} {
		_, kim := store.Get(as(who), "t-kim")
		_, anon := store.Get(as(who), "t-anon")
		list := "0개"
		page, err := store.List(as(who), &a2a.ListTasksRequest{})
		if err != nil {
			list = err.Error()
		} else if len(page.Tasks) > 0 {
			list = fmt.Sprint(len(page.Tasks), "개")
		}
		fmt.Printf("%-5q t-kim %-14s t-anon %-14s List %s\n",
			who, found(kim), found(anon), list)
	}
	// endregion

	// region: tenant
	// 테넌트를 달아도 같은 작업이 나온다 — 칸은 taskId 와 주인뿐
	h := a2asrv.NewHandler(nil, a2asrv.WithTaskStore(store))
	t, err := h.GetTask(as("kim"),
		&a2a.GetTaskRequest{Tenant: "b", ID: "t-kim"})
	fmt.Println("테넌트 b 의 kim → GetTask t-kim:", t.ID, err)
	// endregion

	// region: copy
	got, _ := store.Get(as("kim"), "t-kim")
	got.Task.Status.State = a2a.TaskStateCompleted // 저장 없이 고친다
	again, _ := store.Get(as("kim"), "t-kim")
	fmt.Println("다시 꺼낸 상태:", again.Task.Status.State,
		" 판:", again.Version)
	// DataPart 에 구조체를 넣은 Task — 사본(gob)을 못 뜬다
	req := workshop.LodgingRequest{Date: "2026-10-30", Nights: 1}
	_, err = store.Create(as("kim"),
		newTask("t-struct", a2a.NewDataPart(req)))
	fmt.Println("구조체 DataPart:", err)
	_, err = store.Create(as("kim"), newTask("t-map",
		a2a.NewDataPart(map[string]any{"nights": 1}),
		a2a.NewRawPart([]byte("안녕"))))
	m, _ := store.Get(as("kim"), "t-map")
	parts := m.Task.History[0].Parts
	fmt.Printf("map DataPart: %v → %T %v, raw %q\n", err,
		parts[0].Data().(map[string]any)["nights"],
		parts[0].Data(), parts[1].Raw())
	// endregion

	// region: version
	// 고친 Task 를 넣을 때 앞 판을 적는다 — 낡은 판이면 거절
	next := *again.Task
	next.Status = a2a.TaskStatus{State: a2a.TaskStateWorking}
	up := &taskstore.UpdateRequest{Task: &next,
		PrevVersion: again.Version}
	v, err := store.Update(as("kim"), up)
	fmt.Println("판", again.Version, "→ Update:", v, err)
	v, err = store.Update(as("kim"), up) // 같은 앞 판으로 또
	fmt.Println("판", again.Version, "→ Update:", v, err)
	// endregion
}
