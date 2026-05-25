# 실무형 Go 동시성 패턴북 심화편  
## 실전 예제 24선으로 배우는 고급 Go Concurrency

---

# 서문

Go의 동시성은 흔히 “goroutine과 channel”로 요약된다.  
하지만 실무에서는 그것만으로 충분하지 않다.

현실의 서비스는 다음과 같은 문제를 마주한다.

- 요청 취소가 전파되지 않는다
- goroutine leak가 쌓인다
- channel close 책임이 불분명하다
- worker pool이 backpressure를 만들지 못한다
- timeout과 retry가 섞이며 시스템이 더 불안정해진다
- mutex와 channel을 잘못 선택해 코드가 복잡해진다
- fan-out은 쉬운데 fan-in과 종료 시점이 어렵다
- shared state를 보호하다가 성능 병목이 생긴다

이 책은 단순한 문법 설명서가 아니다.  
이 책의 목표는 다음과 같다.

1. **실무에서 자주 쓰는 동시성 패턴을 이해한다**
2. **각 패턴의 의도와 한계를 구분한다**
3. **안전한 종료, 취소, 에러 전파를 기본 설계로 삼는다**
4. **Go다운 단순함을 유지하면서도 운영 가능한 코드를 만든다**

---

# 이 책의 독자

이 책은 다음 독자를 대상으로 한다.

- Go 기본 문법과 goroutine/channel 기초를 이미 아는 개발자
- 실무에서 API 서버, 배치, 워커, 스트리밍 처리를 개발하는 개발자
- 단순 예제가 아니라 실제 운영 코드를 더 잘 설계하고 싶은 개발자
- 동시성 버그, 데드락, leak, race condition을 줄이고 싶은 개발자

---

# 이 책에서 반복해서 강조하는 원칙

동시성은 기능이 아니라 **수명 관리(lifecycle management)** 이다.  
다음 원칙은 모든 장에서 반복된다.

- goroutine을 만들면 **어떻게 끝나는지** 먼저 생각한다
- channel을 만들면 **누가 닫는지** 먼저 정한다
- timeout이 있으면 **취소가 실제로 전파되는지** 확인한다
- 공유 상태라면 channel보다 mutex가 더 단순한지 먼저 검토한다
- 빠른 코드보다 먼저 **예측 가능한 코드**를 쓴다
- 최적화는 benchmark와 pprof 이후에 한다

---

# 목차

## Part 1. 동시성 설계의 기초 재정의
1. goroutine lifecycle
2. channel ownership
3. cancellation first design

## Part 2. 실무 패턴
4. fire-and-forget의 함정
5. worker pool
6. pipeline
7. fan-out / fan-in
8. errgroup
9. semaphore
10. bounded concurrency
11. shared state 보호
12. pub/sub 스타일 내부 이벤트 처리

## Part 3. 운영 가능한 동시성
13. timeout, retry, backpressure
14. shutdown
15. leak 방지
16. race 방지
17. profiling과 디버깅

## Part 4. 안티패턴과 체크리스트
18. 흔한 실수
19. 설계 점검표

---

# Part 1. 동시성 설계의 기초 재정의

---

## 1장. goroutine은 공짜가 아니다

goroutine은 매우 가볍지만, **무료가 아니다**.  
문제는 생성 비용보다 **회수하지 못했을 때의 비용**이다.

goroutine 설계에서 가장 먼저 답해야 할 질문은 이것이다.

1. 언제 시작하는가?
2. 언제 끝나는가?
3. 누가 취소하는가?
4. 실패는 어디로 전파되는가?

---

## 예제 1. 가장 단순한 goroutine 시작

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	go func() {
		fmt.Println("background work")
	}()
	time.Sleep(100 * time.Millisecond)
}
```

### 해설
이 코드는 교육용으로는 괜찮지만 실무 코드로는 부족하다.

- 종료 보장 없음
- 실패 전파 없음
- lifecycle 추적 어려움

---

## 예제 2. `WaitGroup`으로 종료를 기다리기

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup

	wg.Add(1)
	go func() {
		defer wg.Done()
		fmt.Println("background work")
	}()

	wg.Wait()
}
```

### 핵심
goroutine을 시작했다면, 최소한 **끝났는지 기다릴 수 있어야** 한다.

---

## 예제 3. goroutine leak가 생기는 단순한 사례

```go
package main

func main() {
	ch := make(chan int)

	go func() {
		ch <- 1
	}()

	// 받는 쪽이 없음
}
```

### 문제
전송자는 영원히 block될 수 있다.  
프로그램이 바로 끝나면 티가 안 날 뿐, 서버 코드에서는 leak가 된다.

---

## 예제 4. 수신자가 없을 수 있는 경우 `select`로 빠져나오기

```go
package main

import (
	"context"
	"fmt"
	"time"
)

func send(ctx context.Context, ch chan<- int, v int) error {
	select {
	case ch <- v:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func main() {
	ch := make(chan int)
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	err := send(ctx, ch, 1)
	fmt.Println("send result:", err)
}
```

### 핵심
block 가능성이 있는 channel 연산은 실무에서 종종 `ctx.Done()`과 함께 고려해야 한다.

---

# 2장. channel ownership를 명확히 하라

channel 관련 버그의 상당수는 문법보다 **소유권이 모호해서** 생긴다.

핵심 규칙:

- **보내는 쪽이 닫는다**
- 수신자는 대체로 닫지 않는다
- 여러 sender가 있으면 close 책임을 더 신중히 설계해야 한다

---

## 예제 5. producer가 close하는 올바른 패턴

```go
package main

import "fmt"

func producer() <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for i := 1; i <= 3; i++ {
			out <- i
		}
	}()
	return out
}

func main() {
	for v := range producer() {
		fmt.Println(v)
	}
}
```

---

## 예제 6. 수신자가 close하면 위험해지는 예

```go
package main

func main() {
	ch := make(chan int)

	go func() {
		ch <- 1
	}()

	close(ch) // sender와 경쟁 가능
}
```

### 문제
sender가 아직 보내는 중이면 panic이 날 수 있다.

---

## 예제 7. 여러 producer가 있을 때 close를 안전하게 처리하기

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	out := make(chan int)
	var wg sync.WaitGroup

	producer := func(start int) {
		defer wg.Done()
		for i := start; i < start+3; i++ {
			out <- i
		}
	}

	wg.Add(2)
	go producer(0)
	go producer(100)

	go func() {
		wg.Wait()
		close(out)
	}()

	for v := range out {
		fmt.Println(v)
	}
}
```

### 핵심
여러 sender가 있다면 **모든 sender 종료 후 close**가 안전하다.

---

# 3장. cancellation first 설계

좋은 동시성 설계는 “어떻게 실행할까?”보다 **“어떻게 멈출까?”**를 먼저 고민한다.

---

## 예제 8. 취소 불가능한 generator

```go
package main

func generator() <-chan int {
	ch := make(chan int)
	go func() {
		for i := 0; ; i++ {
			ch <- i
		}
	}()
	return ch
}
```

### 문제
호출자가 더 이상 읽지 않으면 goroutine이 남는다.

---

## 예제 9. `context.Context`를 받는 generator

```go
package main

import (
	"context"
	"fmt"
)

func generator(ctx context.Context) <-chan int {
	ch := make(chan int)
	go func() {
		defer close(ch)
		for i := 0; ; i++ {
			select {
			case ch <- i:
			case <-ctx.Done():
				return
			}
		}
	}()
	return ch
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	ch := generator(ctx)

	for i := 0; i < 5; i++ {
		fmt.Println(<-ch)
	}
	cancel()
}
```

### 핵심
goroutine을 반환하는 API는 취소 경로를 함께 노출하는 것이 좋다.

---

# Part 2. 실무 패턴

---

# 4장. Fire-and-forget의 함정

실무에서 “백그라운드로 던져두자”는 유혹은 매우 크다.  
하지만 추적되지 않는 goroutine은 쉽게 장애의 원인이 된다.

---

## 예제 10. 단순 fire-and-forget

```go
package main

import "log"

func sendEmail(to string) {
	log.Println("sending email to", to)
}

func handler(user string) {
	go sendEmail(user)
}
```

### 문제
- 실패 추적 불가
- 종료 시 유실 가능
- 동시 요청이 몰리면 goroutine 폭증 가능

---

## 예제 11. bounded queue로 백그라운드 작업 처리

```go
package main

import (
	"log"
)

type EmailJob struct {
	To string
}

type EmailSender struct {
	queue chan EmailJob
}

func NewEmailSender(size int) *EmailSender {
	s := &EmailSender{
		queue: make(chan EmailJob, size),
	}
	go s.loop()
	return s
}

func (s *EmailSender) loop() {
	for job := range s.queue {
		log.Println("sending email to", job.To)
	}
}

func (s *EmailSender) Submit(job EmailJob) bool {
	select {
	case s.queue <- job:
		return true
	default:
		return false
	}
}

func main() {
	sender := NewEmailSender(2)
	ok := sender.Submit(EmailJob{To: "a@example.com"})
	log.Println("submitted:", ok)
}
```

### 핵심
fire-and-forget 대신 **큐의 크기로 부하를 제한**할 수 있다.

---

# 5장. Worker Pool 패턴

worker pool은 가장 흔한 실무 패턴 중 하나다.  
핵심은 “병렬 처리”보다 **bounded concurrency**다.

---

## 예제 12. 기본 worker pool

```go
package main

import (
	"fmt"
	"sync"
)

func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs {
		results <- job * 2
		fmt.Printf("worker %d processed %d\n", id, job)
	}
}

func main() {
	jobs := make(chan int)
	results := make(chan int)
	var wg sync.WaitGroup

	for i := 0; i < 3; i++ {
		wg.Add(1)
		go worker(i, jobs, results, &wg)
	}

	go func() {
		for i := 1; i <= 5; i++ {
			jobs <- i
		}
		close(jobs)
	}()

	go func() {
		wg.Wait()
		close(results)
	}()

	for r := range results {
		fmt.Println("result:", r)
	}
}
```

---

## 예제 13. `context`를 지원하는 worker pool

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

func worker(ctx context.Context, id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for {
		select {
		case <-ctx.Done():
			return
		case job, ok := <-jobs:
			if !ok {
				return
			}
			time.Sleep(50 * time.Millisecond)
			select {
			case results <- job * 2:
			case <-ctx.Done():
				return
			}
			fmt.Printf("worker %d processed %d\n", id, job)
		}
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	jobs := make(chan int)
	results := make(chan int)
	var wg sync.WaitGroup

	for i := 0; i < 3; i++ {
		wg.Add(1)
		go worker(ctx, i, jobs, results, &wg)
	}

	go func() {
		defer close(jobs)
		for i := 1; i <= 10; i++ {
			select {
			case jobs <- i:
			case <-ctx.Done():
				return
			}
		}
	}()

	go func() {
		wg.Wait()
		close(results)
	}()

	for r := range results {
		fmt.Println("result:", r)
	}
}
```

### 핵심
- 생산자도 `ctx.Done()`을 봐야 한다
- worker도 `ctx.Done()`을 봐야 한다
- 결과 channel 송신도 취소 가능해야 한다

---

## 예제 14. 작업 실패를 수집하는 worker pool

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

type Result struct {
	Value int
	Err   error
}

func worker(jobs <-chan int, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs {
		if job == 3 {
			results <- Result{Err: errors.New("job 3 failed")}
			continue
		}
		results <- Result{Value: job * 10}
	}
}

func main() {
	jobs := make(chan int)
	results := make(chan Result)

	var wg sync.WaitGroup
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go worker(jobs, results, &wg)
	}

	go func() {
		defer close(jobs)
		for i := 1; i <= 5; i++ {
			jobs <- i
		}
	}()

	go func() {
		wg.Wait()
		close(results)
	}()

	for r := range results {
		if r.Err != nil {
			fmt.Println("error:", r.Err)
			continue
		}
		fmt.Println("value:", r.Value)
	}
}
```

### 포인트
실패를 개별 결과로 다룰지, 전체 작업을 취소할지는 요구사항에 따라 다르다.

---

# 6장. Pipeline 패턴

pipeline은 여러 단계를 거쳐 데이터를 처리할 때 강력하다.  
하지만 각 단계의 **종료와 backpressure**를 잘 설계해야 한다.

---

## 예제 15. 2단계 pipeline

```go
package main

import "fmt"

func gen(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, n := range nums {
			out <- n
		}
	}()
	return out
}

func square(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			out <- n * n
		}
	}()
	return out
}

func main() {
	for n := range square(gen(1, 2, 3, 4)) {
		fmt.Println(n)
	}
}
```

---

## 예제 16. 취소 가능한 pipeline

```go
package main

import (
	"context"
	"fmt"
)

func gen(ctx context.Context, nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, n := range nums {
			select {
			case out <- n:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

func square(ctx context.Context, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			select {
			case out <- n * n:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	ch := square(ctx, gen(ctx, 1, 2, 3, 4, 5))

	fmt.Println(<-ch)
	fmt.Println(<-ch)
	cancel()
}
```

### 핵심
중간 단계도 취소를 이해해야 끝까지 leak 없이 종료된다.

---

## 예제 17. 필터 + 변환 + 집계 pipeline

```go
package main

import "fmt"

func gen(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, n := range nums {
			out <- n
		}
	}()
	return out
}

func filterEven(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			if n%2 == 0 {
				out <- n
			}
		}
	}()
	return out
}

func multiplyBy10(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			out <- n * 10
		}
	}()
	return out
}

func sum(in <-chan int) int {
	total := 0
	for n := range in {
		total += n
	}
	return total
}

func main() {
	total := sum(multiplyBy10(filterEven(gen(1, 2, 3, 4, 5, 6))))
	fmt.Println(total)
}
```

---

# 7장. Fan-out / Fan-in 패턴

---

## 예제 18. fan-out으로 작업 병렬화

```go
package main

import (
	"fmt"
	"sync"
)

func worker(id int, in <-chan int, out chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for n := range in {
		out <- n * 2
		fmt.Printf("worker %d handled %d\n", id, n)
	}
}

func main() {
	in := make(chan int)
	out := make(chan int)
	var wg sync.WaitGroup

	for i := 0; i < 3; i++ {
		wg.Add(1)
		go worker(i, in, out, &wg)
	}

	go func() {
		for i := 1; i <= 6; i++ {
			in <- i
		}
		close(in)
	}()

	go func() {
		wg.Wait()
		close(out)
	}()

	for v := range out {
		fmt.Println(v)
	}
}
```

---

## 예제 19. 여러 입력 channel을 하나로 합치기

```go
package main

import (
	"fmt"
	"sync"
)

func merge(cs ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	out := make(chan int)

	output := func(c <-chan int) {
		defer wg.Done()
		for n := range c {
			out <- n
		}
	}

	wg.Add(len(cs))
	for _, c := range cs {
		go output(c)
	}

	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

func main() {
	a := make(chan int, 2)
	b := make(chan int, 2)

	a <- 1
	a <- 2
	close(a)

	b <- 10
	b <- 20
	close(b)

	for n := range merge(a, b) {
		fmt.Println(n)
	}
}
```

### 핵심
fan-in에서 close는 **모든 입력 소모 후** 수행되어야 한다.

---

# 8장. `errgroup` 패턴

여러 작업을 병렬 실행하고, 하나가 실패하면 나머지를 취소해야 할 때 가장 좋은 선택 중 하나다.

---

## 예제 20. `errgroup` 기본 사용

```go
package main

import (
	"context"
	"fmt"
	"time"

	"golang.org/x/sync/errgroup"
)

func task(ctx context.Context, name string, d time.Duration) error {
	select {
	case <-time.After(d):
		fmt.Println("done:", name)
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func main() {
	g, ctx := errgroup.WithContext(context.Background())

	g.Go(func() error { return task(ctx, "A", 100*time.Millisecond) })
	g.Go(func() error { return task(ctx, "B", 200*time.Millisecond) })
	g.Go(func() error { return task(ctx, "C", 150*time.Millisecond) })

	if err := g.Wait(); err != nil {
		fmt.Println("error:", err)
	}
}
```

---

## 예제 21. 하나가 실패하면 전체 취소

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"golang.org/x/sync/errgroup"
)

func task(ctx context.Context, name string, fail bool) error {
	select {
	case <-time.After(100 * time.Millisecond):
		if fail {
			return errors.New(name + " failed")
		}
		fmt.Println(name, "ok")
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func main() {
	g, ctx := errgroup.WithContext(context.Background())

	g.Go(func() error { return task(ctx, "task1", false) })
	g.Go(func() error { return task(ctx, "task2", true) })
	g.Go(func() error { return task(ctx, "task3", false) })

	if err := g.Wait(); err != nil {
		fmt.Println("group error:", err)
	}
}
```

### 핵심
실패 전파와 취소 전파를 함께 다룰 때 `errgroup`은 매우 유용하다.

---

# 9장. Semaphore와 bounded concurrency

“동시에 몇 개까지 허용할 것인가?”는 실무에서 가장 중요한 질문 중 하나다.

---

## 예제 22. buffered channel로 semaphore 구현

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	sem := make(chan struct{}, 2)

	for i := 1; i <= 5; i++ {
		i := i
		go func() {
			sem <- struct{}{}
			defer func() { <-sem }()

			fmt.Println("start", i)
			time.Sleep(200 * time.Millisecond)
			fmt.Println("done", i)
		}()
	}

	time.Sleep(2 * time.Second)
}
```

### 의미
동시에 최대 2개 작업만 실행된다.

---

## 예제 23. 요청 수 제한이 있는 외부 API 호출

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

func callAPI(id int) {
	fmt.Println("calling api", id)
	time.Sleep(100 * time.Millisecond)
	fmt.Println("done api", id)
}

func main() {
	sem := make(chan struct{}, 3)
	var wg sync.WaitGroup

	for i := 1; i <= 10; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			callAPI(i)
		}(i)
	}

	wg.Wait()
}
```

### 실전 포인트
rate limit와는 다르다.  
이건 **동시 실행 개수 제한**이다.

---

# 10장. Shared State 보호 패턴

동시성 문제를 모두 channel로 푸는 것은 좋은 전략이 아니다.

---

## 예제 24. mutex로 안전한 counter 만들기

```go
package main

import (
	"fmt"
	"sync"
)

type Counter struct {
	mu sync.Mutex
	n  int
}

func (c *Counter) Inc() {
	c.mu.Lock()
	c.n++
	c.mu.Unlock()
}

func (c *Counter) Value() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.n
}

func main() {
	var c Counter
	var wg sync.WaitGroup

	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			c.Inc()
		}()
	}

	wg.Wait()
	fmt.Println(c.Value())
}
```

---

## 예제 25. `RWMutex`로 read-heavy workload 다루기

```go
package main

import (
	"fmt"
	"sync"
)

type Cache struct {
	mu sync.RWMutex
	m  map[string]string
}

func NewCache() *Cache {
	return &Cache{m: make(map[string]string)}
}

func (c *Cache) Get(k string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.m[k]
	return v, ok
}

func (c *Cache) Set(k, v string) {
	c.mu.Lock()
	c.m[k] = v
	c.mu.Unlock()
}

func main() {
	cache := NewCache()
	cache.Set("name", "gopher")
	v, ok := cache.Get("name")
	fmt.Println(v, ok)
}
```

### 주의
`RWMutex`는 항상 `Mutex`보다 빠른 것이 아니다.  
실제 read-heavy workload에서만 유리할 수 있다.

---

## 예제 26. `atomic`으로 단순 카운터 최적화

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	var n atomic.Int64
	var wg sync.WaitGroup

	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			n.Add(1)
		}()
	}

	wg.Wait()
	fmt.Println(n.Load())
}
```

### 원칙
단순 수치 갱신에는 atomic이 적합할 수 있지만,  
여러 필드의 일관성을 함께 보장해야 하면 mutex가 더 낫다.

---

# 11장. 내부 이벤트 처리 패턴

서비스 내부에서 간단한 이벤트 전달이 필요할 때가 있다.

---

## 예제 27. 단순 내부 pub/sub

```go
package main

import "fmt"

type EventBus struct {
	subs []chan string
}

func (b *EventBus) Subscribe() <-chan string {
	ch := make(chan string, 1)
	b.subs = append(b.subs, ch)
	return ch
}

func (b *EventBus) Publish(msg string) {
	for _, ch := range b.subs {
		select {
		case ch <- msg:
		default:
		}
	}
}

func main() {
	var bus EventBus
	sub := bus.Subscribe()

	bus.Publish("user.created")
	fmt.Println(<-sub)
}
```

### 주의
이 패턴은 단순 내부 이벤트 전달에만 적합하다.  
정교한 메시징 시스템을 대체하진 못한다.

---

# Part 3. 운영 가능한 동시성

---

# 12장. Timeout, Retry, Backpressure

timeout과 retry는 시스템을 보호할 수도 있지만, 잘못 쓰면 오히려 장애를 증폭시킨다.

---

## 예제 28. timeout이 있는 작업

```go
package main

import (
	"context"
	"fmt"
	"time"
)

func work(ctx context.Context) error {
	select {
	case <-time.After(500 * time.Millisecond):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	fmt.Println(work(ctx))
}
```

---

## 예제 29. 단순 retry with context

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

func unstable(attempt int) error {
	if attempt < 3 {
		return errors.New("temporary error")
	}
	return nil
}

func retry(ctx context.Context, max int) error {
	for i := 1; i <= max; i++ {
		err := unstable(i)
		if err == nil {
			return nil
		}
		select {
		case <-time.After(100 * time.Millisecond):
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return errors.New("all retries failed")
}

func main() {
	ctx := context.Background()
	fmt.Println(retry(ctx, 5))
}
```

### 포인트
retry는 반드시
- 횟수 제한
- timeout
- 대상 작업의 idempotency
를 고려해야 한다.

---

## 예제 30. backpressure를 만드는 bounded queue

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	queue := make(chan int, 2)

	go func() {
		for job := range queue {
			fmt.Println("processing", job)
			time.Sleep(300 * time.Millisecond)
		}
	}()

	for i := 1; i <= 5; i++ {
		select {
		case queue <- i:
			fmt.Println("enqueued", i)
		default:
			fmt.Println("queue full, dropped", i)
		}
	}

	time.Sleep(2 * time.Second)
}
```

### 핵심
큐가 가득 찼을 때
- block할지
- drop할지
- 에러를 반환할지
는 비즈니스 정책이다.

---

# 13장. Graceful Shutdown

서비스는 시작보다 종료가 더 어렵다.

---

## 예제 31. 종료 신호를 받아 worker 중지하기

```go
package main

import (
	"context"
	"fmt"
	"time"
)

func worker(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			fmt.Println("worker stopped")
			return
		default:
			fmt.Println("working...")
			time.Sleep(100 * time.Millisecond)
		}
	}
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	go worker(ctx)

	time.Sleep(350 * time.Millisecond)
	cancel()
	time.Sleep(100 * time.Millisecond)
}
```

---

## 예제 32. HTTP 서버 graceful shutdown 개념 예시

```go
package main

import (
	"context"
	"net/http"
	"time"
)

func main() {
	srv := &http.Server{
		Addr: ":8080",
	}

	go srv.ListenAndServe()

	time.Sleep(1 * time.Second)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
}
```

### 실전 포인트
- 새 요청 중단
- 기존 요청 마무리 대기
- background worker도 함께 종료
- DB, queue consumer도 shutdown 순서를 가져야 함

---

# 14장. Leak 방지 패턴

---

## 예제 33. ticker를 멈추지 않으면 생기는 문제

```go
package main

import "time"

func main() {
	ticker := time.NewTicker(time.Second)
	_ = ticker
}
```

### 문제
사용 후 `Stop()`하지 않으면 자원 누수가 될 수 있다.

---

## 예제 34. ticker를 올바르게 종료하기

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()

	timeout := time.After(700 * time.Millisecond)

	for {
		select {
		case t := <-ticker.C:
			fmt.Println("tick at", t)
		case <-timeout:
			return
		}
	}
}
```

---

## 예제 35. `time.After`를 루프에서 남용하지 않기

```go
package main

import (
	"context"
	"fmt"
	"time"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			fmt.Println("poll")
		case <-ctx.Done():
			return
		}
	}
}
```

### 해설
루프 안에서 반복적으로 `time.After`를 만드는 것보다 `ticker`가 더 적절한 경우가 많다.

---

# 15장. Race Condition과 디버깅

---

## 예제 36. race condition이 있는 코드

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	n := 0

	for i := 0; i < 100; i++ {
		go func() {
			n++
		}()
	}

	time.Sleep(100 * time.Millisecond)
	fmt.Println(n)
}
```

### 문제
동시 수정에 대한 보호가 없다.

---

## 예제 37. race detector로 확인하기

```bash
go test -race ./...
```

또는

```bash
go run -race main.go
```

### 핵심
동시성 코드는 반드시 race detector를 습관처럼 사용해야 한다.

---

# 16장. 실전 복합 예제

이제 여러 패턴을 합쳐보자.

---

## 예제 38. bounded worker + cancellation + graceful close

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type Job struct {
	ID int
}

type Result struct {
	ID  int
	Err error
}

func worker(ctx context.Context, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	for {
		select {
		case <-ctx.Done():
			return
		case job, ok := <-jobs:
			if !ok {
				return
			}
			time.Sleep(100 * time.Millisecond)
			select {
			case results <- Result{ID: job.ID}:
			case <-ctx.Done():
				return
			}
		}
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	jobs := make(chan Job)
	results := make(chan Result)

	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go worker(ctx, jobs, results, &wg)
	}

	go func() {
		defer close(jobs)
		for i := 1; i <= 10; i++ {
			select {
			case jobs <- Job{ID: i}:
			case <-ctx.Done():
				return
			}
		}
	}()

	go func() {
		wg.Wait()
		close(results)
	}()

	for r := range results {
		fmt.Println("done job:", r.ID)
	}
}
```

### 들어간 패턴
- bounded concurrency
- context cancellation
- producer close
- worker drain
- result close synchronization

---

# Part 4. 안티패턴과 체크리스트

---

# 17장. 흔한 안티패턴

---

## 안티패턴 1. channel이면 무조건 Go답다고 생각하기
단순 shared counter는 mutex가 더 쉽다.

## 안티패턴 2. close를 아무 데서나 하기
close는 ownership 문제다.

## 안티패턴 3. goroutine을 만들고 잊어버리기
항상 종료 경로를 생각해야 한다.

## 안티패턴 4. timeout만 걸고 실제 작업이 ctx를 안 보기
취소가 선언만 되고 실제 전파가 안 되는 경우가 많다.

## 안티패턴 5. 무제한 fan-out
외부 API, DB, 파일 IO는 반드시 동시성 제한을 검토해야 한다.

## 안티패턴 6. retry로 장애를 증폭시키기
느린 의존성을 향해 무한 재시도하면 더 망가진다.

## 안티패턴 7. 결과 channel을 닫지 않거나 너무 일찍 닫기
fan-in/fan-out에서 자주 생기는 버그다.

---

# 18장. 동시성 설계 체크리스트

실무에서 코드를 리뷰할 때 아래 항목을 확인하자.

### lifecycle
- goroutine은 언제 종료되는가?
- 종료 신호는 무엇인가?
- shutdown 시 join 가능한가?

### channel
- 누가 close하는가?
- 여러 sender가 있는가?
- close 시점이 안전한가?

### cancellation
- `context.Context`가 실제로 전파되는가?
- 송신/수신 block에서 `ctx.Done()`을 보는가?

### backpressure
- queue가 가득 차면 어떻게 되는가?
- block / drop / fail-fast 중 정책이 있는가?

### error handling
- 병렬 작업 실패가 어디로 모이는가?
- 하나 실패하면 전체 취소가 필요한가?

### shared state
- channel보다 mutex가 더 단순하지 않은가?
- race detector로 검증했는가?

### ops
- timeout은 적절한가?
- retry는 제한되어 있는가?
- ticker, timer가 해제되는가?

---

# 부록 A. 예제 분류표

이 책의 예제를 목적별로 다시 분류하면 다음과 같다.

## lifecycle / 종료
- 예제 2
- 예제 4
- 예제 9
- 예제 31
- 예제 32
- 예제 38

## channel ownership
- 예제 5
- 예제 6
- 예제 7
- 예제 19

## worker pool / fan-out
- 예제 12
- 예제 13
- 예제 14
- 예제 18
- 예제 22
- 예제 23

## pipeline
- 예제 15
- 예제 16
- 예제 17

## shared state
- 예제 24
- 예제 25
- 예제 26
- 예제 36

## 운영성
- 예제 28
- 예제 29
- 예제 30
- 예제 34
- 예제 35
- 예제 37

---

# 부록 B. 독자를 위한 실습 과제

1. 예제 12의 worker pool에 우선순위 job queue를 추가하라.  
2. 예제 19의 merge 함수에 `context.Context` 지원을 넣어라.  
3. 예제 23의 semaphore 예제에 timeout 실패 처리를 추가하라.  
4. 예제 27의 EventBus를 unsubscribe 가능하게 바꿔라.  
5. 예제 29의 retry에 exponential backoff를 넣어라.  
6. 예제 38에 첫 번째 에러 발생 시 전체 취소 로직을 넣어라.  
7. 예제 24, 26을 benchmark로 비교하라.  
8. race detector와 pprof를 함께 사용해 병목과 경쟁 상태를 분석하라.

---

# 맺음말

Go 동시성의 진짜 어려움은 goroutine을 만드는 것이 아니다.  
**멈추는 방법, 실패를 전파하는 방법, 안전하게 회수하는 방법**을 설계하는 데 있다.

좋은 동시성 코드는 화려하지 않다.  
오히려 다음 특징을 가진다.

- 종료가 명확하다
- 소유권이 명확하다
- 취소가 전파된다
- 부하가 제한된다
- 장애 시 행동이 예측 가능하다

실무에서 중요한 것은 “더 많은 goroutine”이 아니라  
**더 적은 놀라움과 더 많은 통제**다.

원하시면 다음 답변에서  
**“출판용 완성 원고 스타일”**로 바로 재편집해드리겠습니다.

---
## 🔗 관련 문서
- [[Go by Example]]
- [[Go 심화]]
