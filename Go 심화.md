# Go Lang 고급 사용자를 위한 가이드북

## 1. Go를 고급 수준에서 본다는 것

초급 수준의 Go는 보통 아래를 다룹니다.

- 문법
- 함수
- struct
- interface
- goroutine / channel 기초
- package / module

하지만 **고급 Go**는 단순히 문법을 아는 것이 아니라 다음을 이해하는 단계입니다.

- **메모리 모델**
- **동시성 설계**
- **에러 처리 철학**
- **인터페이스 설계**
- **성능 최적화**
- **GC 및 escape analysis 이해**
- **표준 라이브러리 중심 설계**
- **프로덕션 운영성(observability, testing, profiling)**

즉, “어떻게 동작하는가”보다 **“왜 이 방식이 Go다운가”**를 설명할 수 있어야 합니다.

---

# 2. Go의 설계 철학을 다시 이해하기

Go의 고급 활용은 문법보다 철학에서 시작합니다.

## 핵심 철학

### 2.1 단순성 우선
Go는 많은 기능을 의도적으로 넣지 않았습니다.

예:
- 상속 없음
- 예외 기반 에러 처리 없음
- 제네릭도 늦게 도입
- 메타프로그래밍 제한적

이건 부족함이 아니라, **복잡성을 억제해 유지보수성을 확보하려는 선택**입니다.

### 2.2 명시성
Go는 숨겨진 동작보다 드러나는 코드를 선호합니다.

예:
- `if err != nil`
- 명시적 인터페이스 구현
- import 사용 강제
- unused variable 금지

### 2.3 composition over inheritance
Go의 struct embedding은 상속처럼 보일 수 있지만 본질적으로는 **합성(composition)** 입니다.

```go
type Logger struct{}

func (Logger) Info(msg string) {}

type Service struct {
	Logger
}
```

이 방식은 기능 재사용은 가능하지만, 복잡한 계층 구조를 피합니다.

---

# 3. 고급 타입 설계

## 3.1 값 타입 vs 포인터 타입

Go에서 가장 자주 발생하는 설계 실수 중 하나는 **무조건 포인터를 쓰는 것**입니다.

### 값을 써야 할 때
- 작고 immutable하게 다루고 싶을 때
- 복사 비용이 낮을 때
- 독립성을 보장하고 싶을 때

### 포인터를 써야 할 때
- 메서드에서 상태를 변경해야 할 때
- 복사 비용이 클 때
- nil 가능성이 의미를 가질 때
- sync primitive가 포함된 struct일 때

예:

```go
type Config struct {
	Timeout time.Duration
	Retries int
}
```

이런 타입은 보통 값으로 다뤄도 무방합니다.

반면:

```go
type Cache struct {
	mu sync.Mutex
	m  map[string]string
}
```

이런 타입은 포인터로 다뤄야 안전합니다.

### 주의
`sync.Mutex`, `sync.RWMutex`, `sync.Once`, `sync.WaitGroup` 등을 포함한 struct는 **복사하면 매우 위험**합니다.

---

## 3.2 method receiver 선택

```go
func (c Config) Validate() error
func (s *Server) Start() error
```

### 값 receiver가 적절한 경우
- receiver를 수정하지 않음
- 작은 타입
- 값 의미론이 자연스러움

### 포인터 receiver가 적절한 경우
- 상태 변경 필요
- 큰 struct
- 내부 필드에 mutex 포함
- 일관성을 위해 모든 메서드가 포인터 receiver를 써야 할 때

### 중요한 규칙
한 타입의 메서드 receiver는 **혼용하지 않는 편이 좋습니다**.  
기술적으로 가능하지만 API 사용성이 혼란스러워질 수 있습니다.

---

## 3.3 zero value를 유용하게 설계하라

Go의 좋은 타입은 **zero value가 가능한 한 유효한 상태**여야 합니다.

예:
- `bytes.Buffer`
- `sync.Mutex`
- `sync.Once`

좋은 예:

```go
type Counter struct {
	n atomic.Int64
}
```

zero value에서 바로 사용 가능합니다.

나쁜 예:

```go
type Client struct {
	conn *sql.DB
}
```

초기화 없이는 무의미하다면, 생성자와 사용 규칙이 명확해야 합니다.

---

# 4. 인터페이스 설계의 고급 원칙

## 4.1 인터페이스는 소비자 쪽에 둬라

Go의 핵심 원칙 중 하나입니다.

나쁜 예:

```go
type UserService interface {
	CreateUser(name string) error
	DeleteUser(id int) error
	UpdateUser(id int, name string) error
}
```

구현체가 하나뿐인데 큰 인터페이스를 미리 만들면 과설계가 됩니다.

좋은 예:
- 구체 타입을 먼저 만든다.
- 필요한 소비자 쪽에서 작은 인터페이스를 정의한다.

```go
type UserCreator interface {
	CreateUser(name string) error
}
```

## 4.2 작은 인터페이스를 선호하라

표준 라이브러리 예시:

- `io.Reader`
- `io.Writer`
- `io.Closer`

이처럼 인터페이스는 **행동 하나 또는 소수의 응집된 행동**을 표현하는 것이 좋습니다.

## 4.3 인터페이스를 위한 인터페이스를 만들지 말라

Java/C# 스타일 사고로 모든 계층마다 인터페이스를 만들면 Go스럽지 않습니다.

다음 경우에만 인터페이스가 특히 유용합니다.

- 테스트에서 대체 구현이 필요할 때
- 서로 다른 구현 전략이 실제로 존재할 때
- 패키지 간 결합을 낮춰야 할 때

---

# 5. 에러 처리의 고급 전략

## 5.1 에러는 값이다

Go에서 에러는 제어 흐름의 일부입니다.

```go
if err != nil {
	return fmt.Errorf("load config: %w", err)
}
```

## 5.2 wrapping을 적극 활용하라

`%w`를 사용해 원본 에러를 감싸면 추적성과 분기 처리가 좋아집니다.

```go
if err := save(); err != nil {
	return fmt.Errorf("save user profile: %w", err)
}
```

## 5.3 sentinel error는 신중히 사용하라

```go
var ErrNotFound = errors.New("not found")
```

장점:
- `errors.Is`로 비교 가능

단점:
- API 표면이 넓어짐
- 문맥이 부족할 수 있음

그래서 다음 기준이 좋습니다.

- 외부 호출자가 분기해야 하면 sentinel 고려
- 아니면 contextual wrapping만으로 충분

## 5.4 custom error type

```go
type ValidationError struct {
	Field string
	Msg   string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("%s: %s", e.Field, e.Msg)
}
```

이런 타입은 `errors.As`로 분기하기 좋습니다.

## 5.5 panic은 예외가 아니다

Go에서 `panic`은 일반 비즈니스 에러 처리가 아니라:
- 절대 발생하면 안 되는 상태
- 프로그래머 실수
- 복구 불가능한 초기화 실패
- 내부 invariant 위반

정도에 사용해야 합니다.

라이브러리 레벨에서는 panic 사용을 최대한 억제해야 합니다.

---

# 6. 동시성 고급편

## 6.1 concurrency != parallelism
Go는 동시성을 쉽게 하지만, 병렬성은 런타임/CPU 스케줄링에 의존합니다.

- **Concurrency**: 일을 구조화하는 방식
- **Parallelism**: 실제 동시에 실행되는 것

## 6.2 goroutine leak를 경계하라

아주 흔한 실수:

```go
func worker(ch <-chan int) {
	for v := range ch {
		fmt.Println(v)
	}
}
```

문제는 `ch`가 닫히지 않으면 goroutine이 영원히 살아있을 수 있다는 점입니다.

### 해결 전략
- `context.Context` 전달
- 종료 채널 설계
- producer가 close 책임을 명확히 가짐
- bounded worker pool 사용

---

## 6.3 context를 cancellation 신호로 이해하라

`context.Context`는 옵션 덩어리가 아니라 주로 다음 용도입니다.

- cancellation
- deadline/timeout
- request-scoped metadata

권장 규칙:
- 함수 첫 번째 인자로 `ctx context.Context`
- struct field에 보관하지 않기
- nil 전달하지 않기
- 취소 가능한 작업이라면 반드시 존중하기

예:

```go
func FetchUser(ctx context.Context, id string) (*User, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	return &User{ID: id}, nil
}
```

---

## 6.4 channel은 통신 수단이지 모든 동기화의 답이 아니다

Go 초중급 개발자들이 자주 하는 오해:
> “동시성 = channel”

아닙니다. 상황에 따라 더 적절한 도구가 있습니다.

- 데이터 전달: `chan`
- 상태 보호: `sync.Mutex`
- read-heavy map 보호: `sync.RWMutex`
- one-time init: `sync.Once`
- 작업 대기: `sync.WaitGroup`
- 고성능 카운터: `sync/atomic`

### 규칙
- **데이터 소유권 이전**에는 channel이 좋음
- **공유 상태 보호**에는 mutex가 더 단순한 경우가 많음

---

## 6.5 fan-out / fan-in 패턴

```go
func worker(in <-chan int, out chan<- int) {
	for x := range in {
		out <- x * 2
	}
}
```

이 패턴은 CPU 작업 분산에 유용하지만 주의할 점:
- out channel close 타이밍
- worker 개수 조절
- backpressure
- cancellation 처리

실전에서는 `errgroup`와 함께 쓰는 경우가 많습니다.

---

## 6.6 errgroup 활용

`golang.org/x/sync/errgroup`은 병렬 작업 관리에 매우 유용합니다.

```go
g, ctx := errgroup.WithContext(ctx)

for _, url := range urls {
	url := url
	g.Go(func() error {
		return fetch(ctx, url)
	})
}

if err := g.Wait(); err != nil {
	return err
}
```

장점:
- 첫 에러 발생 시 취소 전파
- goroutine lifecycle 관리가 쉬움

---

# 7. 메모리와 성능

## 7.1 escape analysis 이해

Go 컴파일러는 값이 stack에 있을지 heap으로 escape할지 결정합니다.

heap 할당이 늘어나면:
- GC 부담 증가
- latency 증가 가능

예를 들어 closure 캡처, interface boxing, 큰 객체 반환 패턴 등은 escape를 유발할 수 있습니다.

확인 예:

```bash
go build -gcflags="-m" .
```

### 중요한 점
escape를 무조건 줄이는 게 목표는 아닙니다.  
먼저 **가독성과 정확성**이 우선이고, 병목일 때만 최적화하세요.

---

## 7.2 allocation 줄이기

### 문자열 결합
```go
var b strings.Builder
b.WriteString("hello")
b.WriteString(" ")
b.WriteString("world")
```

반복적인 `+`보다 유리할 수 있습니다.

### byte buffer 재사용
```go
var pool = sync.Pool{
	New: func() any { return new(bytes.Buffer) },
}
```

단, `sync.Pool`은 성능 최적화 도구이지 일반 캐시가 아닙니다.

## 7.3 slice 다루기

### capacity 이해
```go
s := make([]int, 0, 1024)
```

예상 크기를 알면 capacity를 미리 잡아 재할당을 줄일 수 있습니다.

### 큰 backing array 유지 주의
작은 sub-slice가 큰 배열 전체를 붙잡고 있을 수 있습니다.

```go
small := big[:10]
```

필요하다면 복사해 분리하세요.

```go
small = append([]byte(nil), big[:10]...)
```

---

## 7.4 map 사용 시 주의점

- map은 concurrent write-safe 하지 않음
- iteration 순서는 랜덤
- key 타입의 comparability 필요

고성능/동시성 상황에서는:
- mutex로 보호된 일반 map
- `sync.Map` (특정 read-heavy 패턴에서만)
중 선택해야 합니다.

`sync.Map`을 무조건 쓰면 안 됩니다.

---

# 8. 제네릭스 실전 활용

Go의 generics는 강력하지만 절제해서 써야 합니다.

## 8.1 generics가 적합한 경우
- 자료구조
- 유틸리티 함수
- 타입 안정성이 중요한 반복 패턴
- `map`, `filter`, `reduce`류 도우미

예:

```go
func Map[T any, R any](in []T, fn func(T) R) []R {
	out := make([]R, 0, len(in))
	for _, v := range in {
		out = append(out, fn(v))
	}
	return out
}
```

## 8.2 generics가 과한 경우
- 도메인 로직
- 한 번만 쓰는 추상화
- interface가 더 단순한 경우
- reflection 회피를 위해 억지로 넣는 경우

### 원칙
Go에서 generics는 **가능해서 쓰는 것**이 아니라 **중복 제거와 타입 안정성이 분명할 때만** 쓰는 것이 좋습니다.

---

# 9. reflection은 최후의 수단

reflection은 다음 상황에서 가치가 있습니다.

- serialization/deserialization
- ORM/DI/framework
- 범용 라이브러리
- 태그 기반 처리

하지만 단점이 큽니다.

- 느림
- 읽기 어려움
- 타입 안정성 약화
- 런타임 에러 가능성 증가

가능하면 대안 우선순위는 보통 이렇습니다.

1. 일반 코드
2. interface
3. generics
4. reflection

---

# 10. 테스트 전략

## 10.1 table-driven test

Go의 대표적인 테스트 스타일입니다.

```go
func TestAdd(t *testing.T) {
	tests := []struct {
		a, b int
		want int
	}{
		{1, 2, 3},
		{10, 20, 30},
	}

	for _, tt := range tests {
		if got := Add(tt.a, tt.b); got != tt.want {
			t.Fatalf("got %d, want %d", got, tt.want)
		}
	}
}
```

## 10.2 subtest 활용

```go
for _, tt := range tests {
	tt := tt
	t.Run(tt.name, func(t *testing.T) {
		t.Parallel()
	})
}
```

### 주의
loop variable capture 문제를 항상 조심하세요.

## 10.3 fuzz testing
Go는 fuzzing을 지원합니다.  
파서, 디코더, 경계값 처리 함수에 특히 좋습니다.

## 10.4 integration test 분리
- 단위 테스트는 빠르게
- 통합 테스트는 분리 실행 가능하게
- 외부 시스템 의존성은 명시적으로 관리

---

# 11. 프로파일링과 관측성

## 11.1 pprof
Go 성능 분석의 핵심 도구입니다.

- CPU profile
- heap profile
- goroutine profile
- mutex/block profile

애플리케이션에 `net/http/pprof`를 붙여 실시간 분석하기도 합니다.

## 11.2 trace
병목이 goroutine scheduling, syscall wait, GC pause 등과 관련 있으면 trace가 강력합니다.

## 11.3 metrics/logging/tracing
프로덕션 Go 서비스는 보통 다음 세 축이 필요합니다.

- **metrics**: latency, throughput, error rate
- **logging**: 구조화된 로그
- **tracing**: 요청 경로 추적

---

# 12. 표준 라이브러리 중심 개발

고급 Go 개발자는 외부 프레임워크보다 먼저 표준 라이브러리를 검토합니다.

매우 중요한 패키지들:

- `context`
- `errors`
- `io`
- `net/http`
- `sync`
- `time`
- `encoding/json`
- `database/sql`
- `testing`
- `runtime`
- `pprof`
- `expvar` (경우에 따라)

Go 생태계의 강점은 프레임워크가 아니라 **표준 라이브러리의 조합성**입니다.

---

# 13. 실전 코드베이스 구조

Go 프로젝트는 과도한 계층화를 피하는 것이 좋습니다.

## 추천 원칙
- package는 역할 중심으로 나눈다
- `internal` 적극 활용
- 인터페이스는 소비자 가까이에 둔다
- `pkg` 디렉터리는 무조건 필요한 건 아니다
- `cmd/<app>` 구조로 엔트리포인트 분리

예시:

```text
myapp/
  cmd/
    api/
      main.go
  internal/
    service/
    store/
    transport/
  go.mod
```

---

# 14. 흔한 고급 실수들

## 14.1 interface 남용
모든 계층을 interface로 감싸는 것

## 14.2 channel 남용
mutex가 더 간단한데 channel로 억지 구현

## 14.3 premature optimization
벤치마크 없이 복잡한 micro-optimization 수행

## 14.4 context 오용
- struct에 저장
- optional parameter처럼 사용
- cancellation 무시

## 14.5 에러 문맥 부족
```go
return err
```

보다는:

```go
return fmt.Errorf("parse config file: %w", err)
```

## 14.6 nil interface 함정
```go
var p *MyError = nil
var err error = p
fmt.Println(err == nil) // false
```

이 문제는 인터페이스 내부의 동적 타입/값 개념을 이해해야 피할 수 있습니다.

---

# 15. 고급 Go 개발자의 체크리스트

아래 항목에 “예”라고 답할 수 있으면 꽤 높은 수준입니다.

- receiver를 값/포인터 중 의도적으로 선택하는가?
- zero value usable 타입을 설계하는가?
- 인터페이스를 작고 소비자 중심으로 정의하는가?
- goroutine leak 가능성을 항상 검토하는가?
- `context` cancellation을 전파하는가?
- `errors.Is`, `errors.As`, `%w`를 적절히 쓰는가?
- mutex와 channel 중 더 단순한 쪽을 고르는가?
- pprof와 benchmark로 실제 병목을 확인하는가?
- generics를 절제해서 사용하는가?
- 표준 라이브러리를 우선 검토하는가?

---

# 16. 추천 학습 순서

고급자로 성장하려면 다음 순서를 추천합니다.

## 1단계: 언어 내부 동작 이해
- stack vs heap
- escape analysis
- method set
- interface 내부 표현
- slice/map internals

## 2단계: 동시성 심화
- memory model
- happens-before
- mutex vs channel
- cancellation 설계
- worker pool / pipeline

## 3단계: 성능 분석
- benchmark
- pprof
- trace
- allocs/op 읽기

## 4단계: 설계 감각
- package boundary
- 작은 인터페이스
- zero-cost abstraction에 가까운 설계
- 단순한 API 만들기

---

# 17. 짧은 실전 예제: Go다운 서비스 코드의 방향

```go
type Store interface {
	GetUser(ctx context.Context, id string) (User, error)
}

type Service struct {
	store Store
}

func NewService(store Store) *Service {
	return &Service{store: store}
}

func (s *Service) GetUserName(ctx context.Context, id string) (string, error) {
	user, err := s.store.GetUser(ctx, id)
	if err != nil {
		return "", fmt.Errorf("get user %q: %w", id, err)
	}
	return user.Name, nil
}
```

이 코드가 Go다운 이유:
- 작은 인터페이스
- context 전달
- 명시적 의존성
- 에러 wrapping
- 단순한 구조

---

# 18. 결론

고급 Go는 “트릭”의 집합이 아닙니다.  
오히려 반대입니다.

**고급 Go일수록 더 단순하고, 더 명시적이며, 더 읽기 쉽습니다.**

진짜 고급 사용자는:
- 복잡한 추상화를 자제하고
- 표준 라이브러리를 최대한 활용하며
- 성능을 측정 기반으로 개선하고
- 동시성과 에러 처리를 설계 수준에서 다룹니다.

Go의 실력은 화려함보다 다음에서 드러납니다.

- 명확한 API
- 예측 가능한 동작
- 쉬운 디버깅
- 운영 가능한 코드
- 팀 전체가 읽을 수 있는 단순성
---
[[Go 패턴]]
[[Go by Example]]

---
## 🔗 관련 문서
- [[Go by Example]]
- [[Go 패턴]]
