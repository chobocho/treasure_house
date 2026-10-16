// 비동기 두 가지 — (1) 차례로 생기는 이벤트를 하나씩 받기,
// (2) 세 견적을 한꺼번에 기다리기. iter.Seq2 와 goroutine·channel.
package main

import (
	"fmt"
	"iter"
	"strings"
	"sync"
	"time"

	"example.com/workshop/workshop"
)

// region: steps
// 함수 이터레이터: yield 를 부를 때마다 받는 쪽 for 가 한 바퀴 돈다.
// 둘째 값 error 는 도중에 실패를 알리는 자리다.
func steps() iter.Seq2[string, error] {
	return func(yield func(string, error) bool) {
		names := []string{"배차 요청 접수", "기사 배정", "차량 확정"}
		for _, s := range names {
			time.Sleep(50 * time.Millisecond)
			if !yield(s, nil) { // 받는 쪽이 멈추면 그만둔다
				return
			}
		}
	}
}

// endregion

// region: fanout
type job struct {
	name  string
	delay time.Duration
	total func() int
}

func main() {
	for s, err := range steps() { // 이벤트가 생기는 대로 받는다
		if err != nil {
			panic(err)
		}
		fmt.Println("상태:", s)
	}
	jobs := []job{
		{"숙소", 300 * time.Millisecond, lodging},
		{"식사", 100 * time.Millisecond, meals},
		{"교통", 200 * time.Millisecond, buses},
	}
	totals := make([]int, len(jobs)) // 자리를 정해 두면 순서가 지켜진다
	done := make(chan string)
	var wg sync.WaitGroup
	for i, j := range jobs {
		wg.Go(func() { // goroutine 셋을 동시에 띄운다
			time.Sleep(j.delay) // 다른 에이전트에 묻는 시간인 셈
			totals[i] = j.total()
			done <- j.name
		})
	}
	go func() { wg.Wait(); close(done) }() // 다 끝나면 채널을 닫는다
	for name := range done {
		fmt.Println("끝남:", name)
	}
	parts, sum := []string{}, 0
	for i, j := range jobs {
		parts = append(parts, fmt.Sprintf("%s %d", j.name, totals[i]))
		sum += totals[i]
	}
	fmt.Println("모은 순서:", strings.Join(parts, " · "))
	fmt.Println("합계:", sum)
}

// endregion

func lodging() int {
	q, _ := workshop.ChooseLodging(workshop.LodgingRequest{
		Date: "2026-10-30", Nights: 1, Headcount: 30})
	return q.Total
}

func meals() int {
	p, _ := workshop.PlanMeals(workshop.MealsRequest{
		Nights: 1, Headcount: 30, Vegetarians: 2})
	return p.Total
}

func buses() int {
	b, _ := workshop.ChooseBuses(workshop.BusRequest{
		Headcount: 30, Nights: 1})
	return b.Total
}
