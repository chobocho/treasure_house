# Go로 만드는 GW-BASIC 인터프리터

## 완전 구현 가이드 — BNF부터 가상 머신까지

> 200페이지 분량의 실전 컴파일러 / 인터프리터 구현서 — Go 1.22+ 기준

---

## 머리말

이 책은 1980년대 IBM PC를 대표하던 언어 **GW-BASIC**을 현대 Go 환경에서 처음부터 구현해 보는 실전 가이드입니다. C 버전과 TypeScript 버전을 자매서로 두고, 같은 VM 설계와 같은 예제 프로그램을 **Go 언어의 관용**(인터페이스, `error` 반환, 구조체 메서드, 동시성)으로 다시 표현합니다.

다음 네 단계를 거치는 본격적인 언어 처리 시스템을 만듭니다.

1. **BNF 문법 정의** — GW-BASIC의 모든 문법 요소를 형식 언어로 기술
2. **Lexer / Parser** — 소스 코드를 토큰으로 쪼개고 AST로 변환
3. **Bytecode Compiler** — AST를 자체 정의 바이트코드로 변환
4. **Virtual Machine** — 스택 기반 VM에서 바이트코드를 실행

결과물은 터미널과 `ebitengine`(선택) 두 가지 환경에서 동작합니다. `SCREEN`, `LINE`, `CIRCLE`, `PSET`, `COLOR` 같은 그래픽 명령과 `SOUND`, `PLAY` 같은 사운드 명령까지 동작하는 처리기를 만드는 것이 목표입니다.

### 왜 Go인가

- **단일 바이너리** — `go build` 한 번으로 의존성 없이 배포 가능
- **표준 라이브러리** — 테스트, 벤치마크, 프로파일링이 언어에 내장
- **인터페이스** — `Host` 추상화가 자연스럽고, 모킹이 쉬움
- **고루틴 / 채널** — `INPUT` 비동기 처리, 백그라운드 사운드 재생에 잘 맞음
- **포인터 + 값 의미론** — VM의 스택 셀, 환경 셀 같은 데이터 표현이 명료

### 이 책이 다루는 것

- 인터프리터 / 컴파일러의 이론적 기반
- 형식 문법(BNF)과 재귀 하강 파서
- Pratt 파서를 이용한 표현식 파싱
- 스택 기반 가상 머신 설계
- 변수 환경, 메모리 모델, 라인 번호 매핑
- GW-BASIC 고유 기능: 라인 번호, GOTO/GOSUB, FOR/NEXT, DEF FN, DATA/READ
- 그래픽 / 사운드 / 입출력 런타임
- REPL, 디버거, 테스트, 빌드 (`go test`, `go build`, `go install`)

### 이 책이 다루지 않는 것

- Go 언어 자체의 기초 (Tour of Go, *The Go Programming Language* 권장)
- DOS BIOS / 인터럽트 호환 (현대 환경에 맞춰 재해석)
- 카세트 테이프 / FAT12 입출력 (로컬 파일 + JSON 세이브 파일로 대체)

### 대상 독자

- 컴파일러와 인터프리터의 동작 원리를 코드로 이해하고 싶은 개발자
- Go로 중규모 시스템을 직접 만들어 보고 싶은 학습자
- 8비트 시절 BASIC에 대한 향수를 가진 분
- 도메인 특화 언어(DSL)를 설계하려는 엔지니어

### 사용 방법

각 장은 **이론 → BNF / 설계 → 구현 → 테스트** 의 4단 구조로 진행됩니다. 코드는 언제나 작동하는 상태로 누적됩니다. 모든 소스는 다음 디렉터리 구조를 따릅니다.

```
go_gwbasic/
├── go.mod
├── cmd/
│   └── gwbasic/
│       └── main.go
├── internal/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── compiler/
│   ├── vm/
│   ├── runtime/
│   └── host/
├── tests/
├── examples/
└── web/                # 선택: WASM 빌드 산출물
    └── index.html
```

> 📌 본 구현은 `internal/` 패키지 분리를 적극 활용합니다. 외부에서 import 할 수 없게 막아 모듈 경계를 강제합니다. 대신 `cmd/gwbasic/main.go`가 유일한 외부 진입점입니다.

### 본문 표기 약속

- **굵은 글씨**: 핵심 용어
- `monospace`: 코드 식별자, 명령어, 키워드
- > 인용 블록: GW-BASIC 원본 동작에 대한 보충
- ⚠️ 표시: 함정 / 주의 사항
- 💡 표시: 구현 팁

---

## 차례

### 제1부 · 기초 (Foundations)

- **1장** GW-BASIC, 그 시절의 언어 — 역사, 철학, 문법 특성
- **2장** 인터프리터의 해부학 — 토크나이저, 파서, 컴파일러, VM
- **3장** Go 개발 환경 구축 — `go mod`, `go test`, 도구 체인
- **4장** 프로젝트 구조와 패키지 분리

### 제2부 · 언어 명세 (Specification)

- **5장** GW-BASIC BNF 문법 전체 정의
- **6장** 어휘 단위 — 키워드, 식별자, 리터럴
- **7장** 데이터 타입 — INTEGER, SINGLE, DOUBLE, STRING
- **8장** 표현식과 연산자 우선순위

### 제3부 · 프론트엔드 (Frontend)

- **9장** Lexer 완전 구현
- **10장** Parser 기초 — 재귀 하강
- **11장** 표현식 파싱 — Pratt 알고리즘
- **12장** 문장 파싱 — 라인 번호와 명령어
- **13장** AST 노드 정의

### 제4부 · 백엔드 (Backend)

- **14장** 바이트코드 명령어 집합 (ISA) 설계
- **15장** AST → 바이트코드 컴파일러
- **16장** 스택 기반 가상 머신
- **17장** 메모리 모델과 값 표현
- **18장** 변수 환경과 스코프

### 제5부 · 런타임 (Runtime)

- **19장** PRINT와 INPUT — 입출력의 모든 것
- **20장** 제어 흐름 — GOTO, IF/THEN/ELSE, FOR/NEXT
- **21장** 서브루틴 — GOSUB / RETURN
- **22장** 배열 — DIM과 다차원 인덱싱
- **23장** 문자열 함수 — LEFT$, RIGHT$, MID$, INSTR
- **24장** 수학 함수 — SIN, COS, RND, INT
- **25장** DATA / READ / RESTORE
- **26장** 사용자 정의 함수 DEF FN

### 제6부 · 그래픽과 사운드 (Multimedia)

- **27장** SCREEN 모드와 그래픽 명령
- **28장** 사운드 — SOUND와 PLAY (MML)

### 제7부 · 도구와 통합 (Tooling)

- **29장** REPL — 즉시 실행 환경
- **30장** 디버거 — 단계 실행과 브레이크포인트
- **31장** 테스트 전략과 회귀 검증
- **32장** 빌드, 패키징, 배포

### 부록

- **A** GW-BASIC BNF 전체
- **B** 명령어 레퍼런스 카드
- **C** 에러 코드표
- **D** 예제 프로그램 모음 (10선)
- **E** 추가 학습 자료

---

## 참고 자료

- Microsoft, *GW-BASIC User's Guide*, 1987.
- Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*, 2nd ed.
- Bob Nystrom, *Crafting Interpreters*, 2021.
- Thorsten Ball, *Writing an Interpreter in Go* / *Writing a Compiler in Go*. — Go로 직접 인터프리터를 만드는 절차적 가이드. 본 책의 4부 VM 구조에 영감을 줍니다.
- Donovan & Kernighan, *The Go Programming Language*, 2015.
- IBM, *PC BASIC Reference Manual*.

---

> "BASIC is to computer programming as QWERTY is to typing."  
> — Alan Kay (paraphrased)

다음 장에서는 GW-BASIC이라는 언어가 왜 그렇게 설계되었는지, 그 시절의 환경 제약을 이해하는 데서부터 출발합니다.


---

# 제1부 · 기초

## 1장. GW-BASIC, 그 시절의 언어

### 1.1 등장 배경

1983년, IBM은 자사 PC 호환 기종이 아닌 다른 OEM(Compaq, Tandy 등)에도 BASIC을 공급할 필요가 있었습니다. 기존 IBM Cassette BASIC, Disk BASIC, Advanced BASIC(BASICA)는 IBM PC ROM에 의존했습니다. 마이크로소프트는 ROM 의존성을 제거한 100% 디스크 기반 인터프리터를 만들었고, 이를 **GW-BASIC**이라 명명했습니다.

GW가 무엇의 약자인지에 대해서는 여러 설(Gee-Whiz, Gates-William, Greg Whitten 등)이 있지만 공식 입장은 없습니다. 본질은 *"BASICA의 ROM-less 클론"* 이라는 점입니다.

### 1.2 언어 철학

GW-BASIC은 다음 세 가지 원칙 위에 서 있습니다.

1. **즉시성 (Immediate mode)** — 라인 번호 없이 입력한 명령은 즉시 실행되고, 라인 번호와 함께 입력한 명령은 프로그램에 저장됩니다.
2. **단일 전역 환경** — 변수는 모두 전역. 스코프 개념이 사실상 없습니다 (DEF FN의 매개변수 정도가 예외).
3. **인터프리터 친화적 토큰화** — 키워드는 1바이트 토큰으로 압축 저장됩니다. 메모리가 64KB 단위로 귀했던 시절의 흔적입니다.

본 구현에서도 이 세 원칙을 가능한 한 보존합니다. 단, 1바이트 토큰은 학습 목적상 텍스트로 다루겠습니다(저장 포맷은 32장에서 다시 논의).

### 1.3 데이터 타입 체계

| 접미 기호 | 타입 | 크기 | Go 매핑 | 범위 |
|----------|------|------|---------|------|
| `%` | INTEGER | 16비트 | `int16` | -32768 ~ 32767 |
| `!` (생략) | SINGLE | 32비트 부동소수 | `float32` | 약 7자리 정밀도 |
| `#` | DOUBLE | 64비트 부동소수 | `float64` | 약 16자리 정밀도 |
| `$` | STRING | 가변 | `string` | 최대 255자 |

식별자 자체에 타입 접미가 붙는 점이 GW-BASIC의 독특한 특징입니다. `A%`, `A!`, `A#`, `A$`는 **모두 다른 변수**입니다.

> 💡 Go의 `int16`/`float32`/`float64`/`string`은 BASIC의 네 타입과 거의 일대일로 대응합니다. 17장에서 이를 `Value` 인터페이스(또는 태그 유니온 구조체)로 통합합니다.

### 1.4 라인 번호의 역할

```basic
10 PRINT "HELLO"
20 GOTO 10
```

라인 번호는 단순히 정렬 키가 아니라 **분기 대상 식별자**이기도 합니다. 후속 장에서 라인 번호를 별도의 `map[int]int`(라인 → 명령어 인덱스)로 관리할 것입니다.

### 1.5 직접 모드와 프로그램 모드

GW-BASIC은 두 모드를 한 화면에서 자연스럽게 오갑니다.

```
Ok
PRINT 1+2     ← 즉시 실행
3
Ok
10 PRINT 1+2  ← 프로그램에 저장
20 END
RUN           ← 저장된 프로그램 실행
3
Ok
```

본 구현에서도 REPL이 두 모드를 모두 지원하도록 설계합니다(29장).

### 1.6 우리가 구현할 부분 집합

원본 GW-BASIC은 약 200개의 키워드를 가집니다. 우리는 그 중 핵심 80개 정도를 구현합니다.

- 제어: `GOTO`, `GOSUB`, `RETURN`, `IF/THEN/ELSE`, `FOR/NEXT/STEP`, `WHILE/WEND`, `END`, `STOP`
- 입출력: `PRINT`, `INPUT`, `PRINT USING`, `LPRINT`
- 변수: `LET`, `DIM`, `READ`, `DATA`, `RESTORE`, `DEF FN`
- 문자열: `LEN`, `LEFT$`, `RIGHT$`, `MID$`, `STR$`, `VAL`, `CHR$`, `ASC`, `INSTR`, `STRING$`, `SPACE$`
- 수학: `ABS`, `SGN`, `INT`, `FIX`, `SQR`, `SIN`, `COS`, `TAN`, `ATN`, `LOG`, `EXP`, `RND`, `RANDOMIZE`
- 그래픽: `SCREEN`, `CLS`, `COLOR`, `PSET`, `PRESET`, `LINE`, `CIRCLE`, `PAINT`, `LOCATE`
- 사운드: `SOUND`, `PLAY`, `BEEP`
- 기타: `REM`, `'`, `RUN`, `LIST`, `NEW`, `CLEAR`

---

## 2장. 인터프리터의 해부학

### 2.1 언어 처리기의 분류

| 방식 | 특징 | 예시 |
|------|------|------|
| 트리 워킹 인터프리터 | AST를 직접 순회 | 초기 Ruby, AST 학습용 구현 |
| 바이트코드 VM | 중간 코드 컴파일 후 VM 실행 | Python, Lua, Ruby YARV, JVM |
| JIT 컴파일러 | 실행 중 네이티브 코드 생성 | V8, HotSpot |
| AOT 컴파일러 | 사전에 네이티브 생성 | C, Rust, Go |

우리는 **바이트코드 VM** 방식을 택합니다. 트리 워킹은 단순하지만 GOTO/GOSUB 같은 비구조적 제어 흐름을 다루기에 부자연스럽고, JIT은 학습 곡선이 너무 가파릅니다. 바이트코드 VM은 두 마리 토끼를 잡는 균형점입니다.

> 📌 본 구현체 자체는 Go로 *AOT 컴파일*되어 단일 바이너리가 됩니다. 우리가 만드는 것은 그 바이너리 안에서 도는 *바이트코드 VM*입니다. "Go 컴파일러" + "BASIC 인터프리터"의 두 층 구조라는 점을 기억하세요.

### 2.2 처리 파이프라인

```
원본 소스
   │
   ▼
[ Lexer ]   ── 토큰 스트림 ──▶
   │
   ▼
[ Parser ]  ── AST ──▶
   │
   ▼
[ Compiler ] ── Bytecode ──▶
   │
   ▼
[   VM   ]  ── 실행 ──▶  표준 출력 / 화면 / 사운드
```

각 단계는 **순수 함수**에 가깝게 설계합니다. Lexer는 문자열을 받아 토큰 슬라이스를 반환하고, Parser는 토큰 슬라이스를 받아 AST를 반환하며, Compiler는 AST를 받아 명령어 슬라이스를 반환합니다. 부수 효과는 VM에 격리됩니다.

### 2.3 각 단계의 책임

#### Lexer (Tokenizer)

```go
tokens, err := lexer.Lex("10 PRINT 1+2")
// tokens = []Token{
//   {Kind: TNumber, Lex: "10", Line: 1, Col: 1},
//   {Kind: TKeyword, Lex: "PRINT", Line: 1, Col: 4},
//   {Kind: TNumber, Lex: "1", Line: 1, Col: 10},
//   {Kind: TOp, Lex: "+", Line: 1, Col: 11},
//   {Kind: TNumber, Lex: "2", Line: 1, Col: 12},
//   {Kind: TEOL, Line: 1, Col: 13},
// }
```

#### Parser

```go
program, err := parser.Parse(tokens)
// program = &Program{
//   Lines: []*Line{
//     {Number: 10, Statements: []Statement{
//       &PrintStmt{Args: []Expression{
//         &BinaryExpr{Op: "+", LHS: &NumLit{1}, RHS: &NumLit{2}},
//       }},
//     }},
//   },
// }
```

#### Compiler

```go
chunk := compiler.Compile(program)
// chunk.Code = []Instruction{
//   {Op: OpPushNum, Arg: 1},
//   {Op: OpPushNum, Arg: 2},
//   {Op: OpAdd},
//   {Op: OpPrint},
//   {Op: OpEnd},
// }
// chunk.LineMap = map[int]int{10: 0}
```

#### VM

```go
m := vm.New(chunk, host)
if err := m.Run(); err != nil { ... }
// → host.Print("3\n")
```

### 2.4 호스트 인터페이스 (Host)

VM은 *외부 세계*와 통신하기 위해 **`Host`** 인터페이스를 사용합니다. 이렇게 분리하면 터미널, ebitengine 그래픽, 테스트용 mock 등 어떤 환경에서도 같은 VM이 동작합니다.

```go
package host

import "context"

type Host interface {
    Print(s string)
    InputLine(ctx context.Context) (string, error)
    Cls()
    SetPixel(x, y, color int)
    DrawLine(x1, y1, x2, y2, color int)
    DrawCircle(x, y, r, color int)
    Sound(freq float64, durationMs int) error
    Now() float64        // 초 단위, TIMER 함수에 사용
    Random() float64     // [0,1)
}
```

⚠️ **주의**: `Host` 인터페이스는 가능하면 **얇게** 유지합니다. BASIC 명령 하나에 메서드 하나가 일대일로 대응될 필요는 없습니다. 예를 들어 `LINE`은 내부적으로 `SetPixel`을 반복 호출해도 충분합니다. 그러나 성능이 중요한 그래픽 명령은 Host에 직접 위임하는 편이 빠릅니다. 이 균형은 27장에서 다룹니다.

> 💡 Go의 인터페이스는 *암묵적 구현*이라 모킹이 쉽습니다. 테스트에서는 `bytes.Buffer`를 보유한 `mockHost`를 만들어 `Print` 출력을 검증합니다(31장).

---

## 3장. Go 개발 환경 구축

### 3.1 도구 선택

- **언어**: Go 1.22 이상 (range over int, builtin `min/max`, `slices`/`maps` 표준 사용)
- **빌드**: `go build` (외부 빌드 도구 없음)
- **테스트**: 표준 `testing` + `go test`
- **벤치마크**: `go test -bench=.`
- **린트**: `go vet`, `gofmt`, `staticcheck` (선택)

### 3.2 초기 프로젝트 생성

```bash
mkdir go_gwbasic && cd go_gwbasic
go mod init github.com/chobocho/go_gwbasic
```

생성된 `go.mod`:

```go
module github.com/chobocho/go_gwbasic

go 1.22
```

### 3.3 디렉터리 만들기

```bash
mkdir -p cmd/gwbasic
mkdir -p internal/{lexer,parser,ast,compiler,vm,runtime,host}
mkdir -p tests examples
```

`internal/` 패키지는 **모듈 외부에서 import 할 수 없습니다**. 우리 모듈 안에서만 쓰는 패키지를 여기에 두면, 누군가 실수로(또는 의도적으로) 우리 내부 API를 갖다 쓰는 일이 차단됩니다.

### 3.4 첫 실행 확인

`cmd/gwbasic/main.go`:

```go
package main

import "fmt"

func main() {
    fmt.Println("GW-BASIC Go bootstrap OK")
}
```

```bash
go run ./cmd/gwbasic
# → GW-BASIC Go bootstrap OK

go build -o gwbasic ./cmd/gwbasic
./gwbasic
# → GW-BASIC Go bootstrap OK
```

여기까지 동작하면 환경은 준비된 것입니다.

### 3.5 단일 파일 빌드 산출물

CLAUDE.md 규칙에 따라 `dist.js` 단일 산출물 같은 정책을 Go에서도 자연스럽게 만족합니다. `go build`는 **단일 정적 바이너리** 하나만 만들기 때문입니다.

```bash
# Linux/Mac
go build -o gwbasic ./cmd/gwbasic

# Windows에서 cross compile
GOOS=windows GOARCH=amd64 go build -o gwbasic.exe ./cmd/gwbasic

# WASM (선택)
GOOS=js GOARCH=wasm go build -o web/dist.wasm ./cmd/gwbasic-web
```

`build.sh`(Linux/Mac):

```bash
#!/usr/bin/env bash
set -euo pipefail
mkdir -p release
go build -trimpath -ldflags="-s -w" -o release/gwbasic ./cmd/gwbasic
cp -r examples release/
echo "Built: release/gwbasic"
```

`build.bat`(Windows, cp949 인코딩으로 저장):

```bat
@echo off
chcp 949 >nul
if not exist release mkdir release
go build -trimpath -ldflags="-s -w" -o release\gwbasic.exe .\cmd\gwbasic
xcopy /E /I /Y examples release\examples
echo 빌드 완료: release\gwbasic.exe
```

---

## 4장. 프로젝트 구조와 패키지 분리

### 4.1 패키지 의존 그래프

```
cmd/gwbasic/main.go
  ├── internal/repl
  │     ├── internal/lexer
  │     ├── internal/parser
  │     │     └── internal/ast
  │     ├── internal/compiler
  │     │     └── internal/ast
  │     ├── internal/vm
  │     │     └── internal/host
  │     └── internal/runtime
  └── internal/runner (배치 실행)

각 패키지는 위에서 아래로만 의존:
  lexer → parser → ast → compiler → vm → runtime
                                      ↑
                                      host
```

순환 의존은 Go 컴파일러가 강제로 막습니다. 처음에는 답답할 수 있지만, 모듈 경계를 자연스럽게 강제해 줍니다.

> ⚠️ Go에서 가장 흔한 실수: 두 패키지가 서로의 타입을 알아야 할 때 한 쪽에 모두 몰아넣거나, 양쪽이 의존할 *제3의* 패키지(`internal/types` 또는 `internal/common`)를 만들어 빼는 두 가지 패턴이 있습니다. 본 구현은 후자를 택합니다.

### 4.2 공통 타입 (`internal/common/types.go`)

```go
package common

import "fmt"

// SourcePos는 소스에서 토큰/노드 위치를 나타냅니다.
type SourcePos struct {
    Line int
    Col  int
}

// BasicError는 GW-BASIC의 표준 에러 코드를 보존합니다.
type BasicError struct {
    Code      int
    Msg       string
    Pos       SourcePos
    BasicLine int // GW-BASIC 라인 번호 (없으면 0)
}

func (e *BasicError) Error() string {
    if e.BasicLine != 0 {
        return fmt.Sprintf("?%s in %d", e.Msg, e.BasicLine)
    }
    return "?" + e.Msg
}

// 에러 코드 (GW-BASIC 표준)
const (
    ErrNextWithoutFor      = 1
    ErrSyntax              = 2
    ErrReturnWithoutGosub  = 3
    ErrOutOfData           = 4
    ErrIllegalFunctionCall = 5
    ErrOverflow            = 6
    ErrOutOfMemory         = 7
    ErrUndefinedLineNumber = 8
    ErrSubscriptOutOfRange = 9
    ErrDivisionByZero      = 11
    ErrTypeMismatch        = 13
    ErrStringTooLong       = 15
    ErrForWithoutNext      = 26
)

// 자주 쓰이는 헬퍼: BasicError를 빠르게 생성.
func NewError(code int, msg string) *BasicError {
    return &BasicError{Code: code, Msg: msg}
}
```

> 💡 Go의 관용은 에러를 `error` 인터페이스로 반환하는 것이지만, 우리는 BASIC 에러 코드를 보존해야 하므로 `*BasicError` 구체 타입을 함께 사용합니다. 호출자는 `errors.As(err, &be)`로 코드를 꺼낼 수 있습니다.

### 4.3 코딩 컨벤션 (Go 관용 + 본 프로젝트 규칙)

CLAUDE.md를 따르되, Go의 관용을 우선합니다.

| 항목 | 규칙 |
|------|------|
| 변수 / 함수 | `camelCase` (private), `PascalCase` (exported) |
| 타입 / 인터페이스 | `PascalCase` |
| 상수 | `PascalCase`(exported) 또는 `camelCase` (private). `UPPER_SNAKE` 지양 |
| 패키지 이름 | 짧은 소문자 (`lexer`, `vm`, `compiler`) |
| 파일 | `snake_case.go` |
| 에러 | 함수의 마지막 반환값으로 `error`. panic은 *복구 불가* 상황에만 |
| 인터페이스 명명 | 메서드가 하나면 `-er` 접미 (`Reader`, `Lexer`) |

> 💡 `golint`가 deprecated된 이후 표준은 `gofmt` + `go vet` + (선택) `staticcheck`입니다. 본 책은 모든 코드를 `gofmt`로 포맷하고 `go vet ./...`을 통과시킨다고 가정합니다.

### 4.4 다음 단계 미리 보기

다음 장(5장)에서는 GW-BASIC의 BNF 문법을 *전체*로 정의합니다. 이것이 책 전체의 설계도 역할을 합니다. BNF가 머릿속에 들어와야 Lexer, Parser, Compiler를 일관성 있게 만들 수 있습니다.

> 1부 끝.


---

# 제2부 · 언어 명세

## 5장. GW-BASIC BNF 문법 전체 정의

### 5.1 BNF 표기 규약

본 책에서 사용하는 표기는 EBNF 변형입니다.

- `::=` — 정의
- `|` — 선택
- `[ x ]` — 0 또는 1회
- `{ x }` — 0회 이상 반복
- `( x )` — 그룹화
- `"x"` — 종단 기호 (리터럴)
- `<x>` — 비종단 기호
- `/regex/` — 정규식 패턴 (편의용)

### 5.2 프로그램 최상위

```ebnf
<program>     ::= { <line> }
<line>        ::= <line-number> <statement-list> <eol>
                | <statement-list> <eol>          (* 직접 모드 *)

<line-number> ::= /[0-9]{1,5}/                    (* 0..65529 *)

<statement-list> ::= <statement> { ":" <statement> }

<eol>         ::= "\n" | EOF
```

GW-BASIC은 한 줄에 콜론(`:`)으로 여러 문장을 잇습니다. `10 A=1 : B=2 : PRINT A+B` 형태가 가능합니다.

### 5.3 문장(Statement)

```ebnf
<statement> ::= <assign-stmt>
              | <print-stmt>
              | <input-stmt>
              | <if-stmt>
              | <for-stmt>  | <next-stmt>
              | <while-stmt> | <wend-stmt>
              | <goto-stmt>  | <gosub-stmt> | <return-stmt>
              | <end-stmt>   | <stop-stmt>
              | <rem-stmt>
              | <dim-stmt>
              | <data-stmt>  | <read-stmt> | <restore-stmt>
              | <def-fn-stmt>
              | <on-goto-stmt> | <on-gosub-stmt>
              | <cls-stmt>   | <screen-stmt> | <color-stmt>
              | <pset-stmt>  | <line-stmt>   | <circle-stmt>
              | <paint-stmt> | <locate-stmt>
              | <sound-stmt> | <play-stmt>   | <beep-stmt>
              | <randomize-stmt>
              | <clear-stmt>
              | <swap-stmt>
              | (* empty *)
```

#### 할당

```ebnf
<assign-stmt> ::= [ "LET" ] <lvalue> "=" <expression>
<lvalue>      ::= <variable> | <array-ref>
<variable>    ::= <ident> [ <type-suffix> ]
<array-ref>   ::= <variable> "(" <expression> { "," <expression> } ")"
<type-suffix> ::= "%" | "!" | "#" | "$"
```

#### PRINT

```ebnf
<print-stmt> ::= ("PRINT" | "?") [ <print-list> ]
<print-list> ::= <print-item> { <print-sep> [ <print-item> ] }
<print-sep>  ::= "," | ";"
<print-item> ::= <expression>
               | "TAB" "(" <expression> ")"
               | "SPC" "(" <expression> ")"
               | "USING" <string-expr> ";" <expr-list>
```

콤마는 다음 탭 정지 위치(14컬럼 단위)로, 세미콜론은 즉시 이어 출력합니다. 줄 끝에 세미콜론 또는 콤마가 있으면 줄바꿈을 억제합니다.

#### INPUT

```ebnf
<input-stmt> ::= "INPUT" [ ";" ] [ <string-literal> ( ";" | "," ) ] <var-list>
<var-list>   ::= <lvalue> { "," <lvalue> }
```

#### IF / THEN / ELSE

```ebnf
<if-stmt>     ::= "IF" <expression> "THEN" <then-clause> [ "ELSE" <else-clause> ]
<then-clause> ::= <line-number> | <statement-list>
<else-clause> ::= <line-number> | <statement-list>
```

⚠️ THEN 뒤에 라인 번호가 오면 `GOTO`와 같습니다. `IF X=1 THEN 100 ELSE 200`.

#### FOR / NEXT, WHILE / WEND

```ebnf
<for-stmt>   ::= "FOR" <variable> "=" <expression> "TO" <expression>
                 [ "STEP" <expression> ]
<next-stmt>  ::= "NEXT" [ <variable> { "," <variable> } ]

<while-stmt> ::= "WHILE" <expression>
<wend-stmt>  ::= "WEND"
```

#### 분기

```ebnf
<goto-stmt>     ::= "GOTO" <line-number>
<gosub-stmt>    ::= "GOSUB" <line-number>
<return-stmt>   ::= "RETURN" [ <line-number> ]
<on-goto-stmt>  ::= "ON" <expression> "GOTO" <line-number> { "," <line-number> }
<on-gosub-stmt> ::= "ON" <expression> "GOSUB" <line-number> { "," <line-number> }
```

#### 데이터 / 정의 / 종료

```ebnf
<dim-stmt>      ::= "DIM" <dim-decl> { "," <dim-decl> }
<dim-decl>      ::= <variable> "(" <expression> { "," <expression> } ")"
<data-stmt>     ::= "DATA" <data-item> { "," <data-item> }
<data-item>     ::= <number> | <string> | <bare-string>
<read-stmt>     ::= "READ" <lvalue> { "," <lvalue> }
<restore-stmt>  ::= "RESTORE" [ <line-number> ]

<def-fn-stmt> ::= "DEF" "FN" <ident> [ "(" <param-list> ")" ] "=" <expression>
<param-list>  ::= <variable> { "," <variable> }

<end-stmt>   ::= "END"
<stop-stmt>  ::= "STOP"
<rem-stmt>   ::= "REM" /.*/ | "'" /.*/
<clear-stmt> ::= "CLEAR"
<randomize-stmt> ::= "RANDOMIZE" [ <expression> ]
<swap-stmt>  ::= "SWAP" <variable> "," <variable>
```

#### 그래픽 / 사운드 (제27, 28장에서 자세히)

```ebnf
<screen-stmt> ::= "SCREEN" <expression>
<cls-stmt>    ::= "CLS" [ <expression> ]
<color-stmt>  ::= "COLOR" [ <expression> ] [ "," <expression> ]
<pset-stmt>   ::= ("PSET" | "PRESET") <coord> [ "," <expression> ]
<line-stmt>   ::= "LINE" [ <coord> ] "-" <coord>
                  [ "," <expression> ]
                  [ "," ( "B" | "BF" ) ]
<circle-stmt> ::= "CIRCLE" <coord> "," <expression>
                  [ "," <expression> ]
                  [ "," <expression> "," <expression> ]
                  [ "," <expression> ]
<paint-stmt>  ::= "PAINT" <coord> [ "," <expression> [ "," <expression> ] ]
<locate-stmt> ::= "LOCATE" [ <expression> ] [ "," <expression> ]
<coord>       ::= [ "STEP" ] "(" <expression> "," <expression> ")"

<sound-stmt> ::= "SOUND" <expression> "," <expression>
<play-stmt>  ::= "PLAY" <string-expr>
<beep-stmt>  ::= "BEEP"
```

### 5.4 표현식 — 우선순위 단계별 BNF

```ebnf
<expression>     ::= <or-expr>
<or-expr>        ::= <xor-expr>  { "OR"  <xor-expr> }
<xor-expr>       ::= <and-expr>  { "XOR" <and-expr> }
<and-expr>       ::= <not-expr>  { "AND" <not-expr> }
<not-expr>       ::= [ "NOT" ] <rel-expr>
<rel-expr>       ::= <add-expr> [ <rel-op> <add-expr> ]
<rel-op>         ::= "=" | "<>" | "<" | "<=" | ">" | ">="
<add-expr>       ::= <mul-expr>  { ("+" | "-") <mul-expr> }
<mul-expr>       ::= <intdiv-expr> { ("*" | "/") <intdiv-expr> }
<intdiv-expr>    ::= <mod-expr>  { "\\" <mod-expr> }
<mod-expr>       ::= <pow-expr>  { "MOD" <pow-expr> }
<pow-expr>       ::= <unary-expr> { "^" <unary-expr> }     (* 우결합 *)
<unary-expr>     ::= ("+" | "-") <unary-expr> | <primary>
<primary>        ::= <number>
                   | <string>
                   | <variable>
                   | <array-ref>
                   | <func-call>
                   | "(" <expression> ")"

<func-call>      ::= <builtin-name> "(" [ <expr-list> ] ")"
                   | "FN" <ident> "(" [ <expr-list> ] ")"
<expr-list>      ::= <expression> { "," <expression> }
```

### 5.5 우선순위 표 (높음 → 낮음)

| 단계 | 연산자 | 결합성 |
|------|--------|--------|
| 1 | `()`, 함수 호출 | — |
| 2 | `^` | 우결합 |
| 3 | 단항 `+`, `-` | — |
| 4 | `*`, `/` | 좌결합 |
| 5 | `\` (정수 나눗셈) | 좌결합 |
| 6 | `MOD` | 좌결합 |
| 7 | `+`, `-` (이항) | 좌결합 |
| 8 | `=`, `<>`, `<`, `<=`, `>`, `>=` | 좌결합 |
| 9 | `NOT` | — |
| 10 | `AND` | 좌결합 |
| 11 | `XOR` | 좌결합 |
| 12 | `OR` | 좌결합 |

⚠️ GW-BASIC의 `=`은 비교 연산자이면서 동시에 할당 토큰입니다. 문맥에 따라 구분합니다(`A = 1 = 2` 는 `A = (1 = 2)`로 해석되어 A에 0(false) 또는 -1(true)이 들어갑니다).

### 5.6 어휘 단위

```ebnf
<number>      ::= <int-lit> | <float-lit> | <hex-lit> | <oct-lit>
<int-lit>     ::= /[0-9]+/
<float-lit>   ::= /[0-9]+\.[0-9]*([ED][+-]?[0-9]+)?/
                | /\.[0-9]+([ED][+-]?[0-9]+)?/
                | /[0-9]+[ED][+-]?[0-9]+/
<hex-lit>     ::= /&H[0-9A-Fa-f]+/
<oct-lit>     ::= /&O?[0-7]+/

<string>      ::= /"[^"\n]*"/
<bare-string> ::= /[^,:\n]+/      (* DATA문 안에서만 *)

<ident>       ::= /[A-Za-z][A-Za-z0-9]*/    (* 길이 40자 제한 *)
```

### 5.7 토큰 우선순위 충돌

GW-BASIC의 어휘 분석에는 미묘한 함정이 있습니다.

- `IF...THEN` 뒤의 숫자는 라인 번호이지만, 일반 위치에서는 정수 리터럴
- `REM` 뒤는 줄 끝까지 모두 주석
- `DATA` 뒤는 콤마/콜론/EOL까지 *bare string* 으로 처리될 수 있음
- 키워드 사이에 공백이 없어도 됨: `FORI=1TO10` ← 합법

이런 점들 때문에 Lexer에는 약간의 *문맥* 이 필요합니다. 9장에서 전략을 다룹니다.

---

## 6장. 어휘 단위 — 키워드, 식별자, 리터럴

### 6.1 키워드 목록

본 구현에서 인식하는 키워드는 다음과 같습니다 (대문자 정규화 후 비교).

```
AND  AS  ATN  AUTO  BEEP  BLOAD  BSAVE  CALL  CDBL  CHAIN  CHR$  CINT
CIRCLE  CLEAR  CLOSE  CLS  COLOR  COMMON  CONT  COS  CSNG  CSRLIN  CVD
CVI  CVS  DATA  DATE$  DEF  DEFDBL  DEFINT  DEFSNG  DEFSTR  DELETE  DIM
DRAW  EDIT  ELSE  END  ENVIRON  ENVIRON$  EOF  EQV  ERASE  ERL  ERR
ERROR  EXP  FIELD  FILES  FIX  FN  FOR  FRE  GET  GOSUB  GOTO  HEX$
IF  IMP  INKEY$  INP  INPUT  INPUT$  INSTR  INT  KEY  KILL  LEFT$
LEN  LET  LINE  LIST  LLIST  LOAD  LOC  LOCATE  LOF  LOG  LPOS  LPRINT
LSET  MERGE  MID$  MKD$  MKI$  MKS$  MOD  MOTOR  NAME  NEW  NEXT  NOT
OCT$  OFF  ON  OPEN  OPTION  OR  OUT  PAINT  PEEK  PEN  PLAY  POINT
POKE  POS  PRESET  PRINT  PSET  PUT  RANDOMIZE  READ  REM  RENUM
RESET  RESTORE  RESUME  RETURN  RIGHT$  RND  RSET  RUN  SAVE  SCREEN
SGN  SIN  SOUND  SPACE$  SPC  SQR  STEP  STICK  STOP  STR$  STRIG
STRING$  SWAP  SYSTEM  TAB  TAN  THEN  TIME$  TIMER  TO  TRON  TROFF
USING  USR  VAL  VARPTR  VARPTR$  VIEW  WAIT  WEND  WHILE  WIDTH
WINDOW  WRITE  XOR
```

이 중 본 구현에서 *동작*까지 지원하는 키워드는 80개 정도입니다. 나머지는 인식만 하고 `Unimplemented` 에러를 던집니다.

> 💡 Go에서는 이 목록을 `map[string]TokenKind`로 보관합니다. 9장에서 `keywordTable`이라는 변수에 한 번만 초기화되어 모든 식별자 토큰화 시 조회됩니다.

### 6.2 식별자 규칙

- 첫 글자: 영문자
- 두 번째 이후: 영문자 또는 숫자
- 길이: 40자까지 (`MaxIdentLen = 40` 상수)
- 마지막에 타입 접미(`%`, `!`, `#`, `$`) 가능
- 키워드와 같은 이름 금지

### 6.3 숫자 리터럴

```basic
123        ' INTEGER (값이 32767을 넘으면 SINGLE로 승격)
3.14       ' SINGLE (! 접미 동일)
3.14#      ' DOUBLE 강제
1.5E10     ' SINGLE 지수 표기
1.5D10     ' DOUBLE 지수 표기
&H1A       ' 16진수 → INTEGER
&O17       ' 8진수
&17        ' &O와 동일 (O 생략)
```

### 6.4 문자열 리터럴

- 큰따옴표(`"`)로 감쌈
- 줄바꿈 불가
- 이스케이프 시퀀스 없음 (GW-BASIC의 한계). 큰따옴표 자체를 넣고 싶으면 `CHR$(34)` 사용.

### 6.5 코멘트

```basic
10 PRINT "X" : REM 이건 코멘트
20 PRINT "Y" ' 이것도 코멘트
```

`REM`은 키워드, `'`는 단축 표기. 둘 다 줄 끝까지 모두 무시됩니다.

---

## 7장. 데이터 타입

### 7.1 네 가지 기본 타입

이미 1.3절에서 표를 보았습니다. 여기서는 *내부 표현*을 다룹니다.

Go에서는 다음과 같이 모델링합니다 (17장에서 다시 자세히).

```go
// internal/runtime/value.go
package runtime

type ValueTag uint8

const (
    TagInt ValueTag = iota
    TagSng
    TagDbl
    TagStr
)

// Value는 BASIC 변수에 들어갈 수 있는 모든 값을 표현하는 태그 유니온입니다.
// Go에는 sum type이 없으므로 태그 + 페이로드 구조체로 흉내냅니다.
type Value struct {
    Tag ValueTag
    I   int16    // TagInt
    F32 float32  // TagSng
    F64 float64  // TagDbl
    S   string   // TagStr
}

// 생성자 헬퍼
func IntVal(v int16) Value     { return Value{Tag: TagInt, I: v} }
func SngVal(v float32) Value   { return Value{Tag: TagSng, F32: v} }
func DblVal(v float64) Value   { return Value{Tag: TagDbl, F64: v} }
func StrVal(v string) Value    { return Value{Tag: TagStr, S: v} }
```

> 💡 `interface{}` 대신 태그 유니온을 쓰는 이유: 빈번히 생성·소비되는 VM 스택 값에서 인터페이스의 박싱 비용을 피하기 위함입니다. 벤치마크에서 약 2~3배 빠릅니다(31장).

### 7.2 타입 승격 규칙

수치 연산에서:

```
INT  + INT  → INT (오버플로 시 SNG)
INT  + SNG  → SNG
INT  + DBL  → DBL
SNG  + SNG  → SNG
SNG  + DBL  → DBL
DBL  + DBL  → DBL
```

문자열은 수치와 섞이면 `Type Mismatch` (에러 13).

### 7.3 묵시적 타입 결정

식별자에 접미가 없으면 기본은 SINGLE입니다. 단 `DEFINT A-Z` 같은 선언이 있으면 해당 알파벳 범위의 변수가 INTEGER로 기본 설정됩니다.

```basic
DEFINT I-N          ' I,J,K,L,M,N으로 시작하는 변수는 INTEGER
DEFDBL A-H, O-Z     ' 그 외는 DOUBLE
```

이런 선언은 *심볼 테이블*에 기본 타입 매핑을 등록하는 것으로 구현합니다 (18장).

### 7.4 변환 함수

```basic
CINT(x)   ' x를 INTEGER로 (반올림, -32768..32767 범위 검사)
CSNG(x)   ' SINGLE로
CDBL(x)   ' DOUBLE로
INT(x)    ' floor (음의 무한대 방향 내림)
FIX(x)    ' truncate (0 방향 내림)
STR$(x)   ' 수치 → 문자열
VAL(s$)   ' 문자열 → 수치
```

INT와 FIX의 차이는 음수에서 드러납니다.

```basic
PRINT INT(-1.5)   ' -2
PRINT FIX(-1.5)   ' -1
```

Go 구현 (24장에서 자세히):

```go
func gwInt(x float64) float64 { return math.Floor(x) }
func gwFix(x float64) float64 { return math.Trunc(x) }
```

### 7.5 STR$의 미묘함

GW-BASIC의 `STR$(x)`는 양수 앞에 공백 한 칸을 붙입니다 (부호 자리).

```basic
PRINT "[" + STR$(3) + "]"     ' [ 3]
PRINT "[" + STR$(-3) + "]"    ' [-3]
```

이 동작은 PRINT의 출력과도 일치합니다. `PRINT 3`은 ` 3 `(앞뒤 공백 포함)을 출력합니다. 19장에서 다시 다룹니다.

### 7.6 문자열의 길이 제약

- 단일 문자열: 최대 255자
- 문자열 영역: 기본 64KB
- 초과 시 `String too long` (15) 또는 `Out of string space` (14)

본 구현에서는 Go 문자열의 자연스러운 크기를 그대로 쓰되, BASIC 단일 변수에 할당될 때 255자를 넘으면 에러를 던지는 검사 함수를 둡니다.

```go
// internal/runtime/string.go
package runtime

import "github.com/chobocho/go_gwbasic/internal/common"

const MaxStringLen = 255

func CheckStringLen(s string) error {
    if len(s) > MaxStringLen {
        return common.NewError(common.ErrStringTooLong, "String too long")
    }
    return nil
}
```

---

## 8장. 표현식과 연산자 우선순위

### 8.1 우선순위가 중요한 이유

```basic
A = 1 + 2 * 3       ' A = 7  (곱셈 먼저)
B = -2 ^ 2          ' B = -4 (단항 - 가 ^ 보다 후순위)
C = NOT 3 = 2       ' C = NOT(3=2) = NOT 0 = -1
D = 1 = 1 = 1       ' D = (1=1)=1 = (-1)=1 = 0
```

GW-BASIC은 연산자 우선순위가 ANSI BASIC과 약간 다릅니다. 가장 큰 차이는 다음 두 가지입니다.

1. **단항 마이너스가 거듭제곱보다 후순위**: `-2^2 = -4`
2. **NOT이 비교보다 후순위, AND/OR보다 선순위**: 비트 연산처럼 동작하지만 부울로도 쓰임

### 8.2 단항 마이너스의 처리

```ebnf
<unary-expr> ::= ("+" | "-") <unary-expr> | <pow-expr>
<pow-expr>   ::= <primary> { "^" <unary-expr> }   (* 우결합 *)
```

이 정의를 보면 `^`의 오른쪽 피연산자에서는 다시 단항 부호가 허용됩니다(`2^-3 = 0.125`). 그러나 왼쪽에서는 `-2^2`가 `-(2^2) = -4`가 됩니다. Pratt 파서로 표현하면 단항 `-`의 결합력을 `^`보다 *낮게* 설정합니다(11장).

### 8.3 부울 동작

GW-BASIC의 부울은 **-1(true)** 와 **0(false)** 입니다. 그런데 `AND`, `OR`, `NOT`은 *비트* 연산자이기도 합니다.

- `5 AND 3 = 1` (비트 AND)
- `-1 AND 7 = 7` (true AND 7)
- `NOT 0 = -1`, `NOT 1 = -2`

따라서 `IF X = 1 AND Y = 2`는 `IF (X=1) AND (Y=2)`로 정확히 동작합니다(둘 다 -1이면 -1, 한쪽이 0이면 0).

Go에서는 `int16`의 비트 연산으로 직접 표현됩니다.

```go
func opAND(a, b int16) int16 { return a & b }
func opOR(a, b int16) int16  { return a | b }
func opXOR(a, b int16) int16 { return a ^ b }
func opNOT(a int16) int16    { return ^a }
```

### 8.4 정수 나눗셈과 MOD

```basic
PRINT 10 / 3      ' 3.333333
PRINT 10 \ 3      ' 3
PRINT 10 MOD 3    ' 1
PRINT -7 \ 2      ' -3   (0 방향)
PRINT -7 MOD 2    ' -1
```

⚠️ 정수 나눗셈은 피연산자를 먼저 INTEGER로 변환한 후 수행합니다(범위 초과면 오버플로). Go에서는 `int16`로 변환 후 `/`와 `%` 연산자가 같은 의미를 가집니다(0 방향 잘림).

### 8.5 문자열 연산

`+`만 지원합니다 (연결).

```basic
A$ = "Hello, " + "World"
```

다른 산술 연산자에 문자열을 넣으면 `Type Mismatch`.

### 8.6 비교 연산

수치-수치, 문자열-문자열만 가능. 문자열은 사전식 비교 (UTF-8 코드 포인트 순; ASCII 범위에서는 ASCII와 동일).

```basic
PRINT "ABC" < "ABD"     ' -1
PRINT "abc" < "ABC"     ' 0  (소문자가 더 큼)
```

Go는 `string < string`이 곧 lex order이므로 자연스럽게 매핑됩니다.

```go
func cmpStr(a, b string) int16 {
    switch {
    case a < b: return -1   // 사실은 비교 결과를 진리값으로 변환해야 함
    case a > b: return 0
    default:    return 0
    }
}
// 실제 BASIC 의미: a < b 가 참이면 -1, 거짓이면 0
func ltStr(a, b string) int16 {
    if a < b { return -1 }
    return 0
}
```

---

> 2부 끝. 이로써 우리가 만들 언어의 모습이 분명해졌습니다. 이제 3부에서는 이 명세를 *실행 가능한 Go 코드*로 옮깁니다.


---

# 제3부 · 프론트엔드 (1) — Lexer

## 9장. Lexer 완전 구현

### 9.1 토큰 타입 정의

가장 먼저 토큰의 형태를 Go의 타입 시스템으로 정의합니다.

```go
// internal/lexer/token.go
package lexer

type TokenKind uint8

const (
    TNumber TokenKind = iota
    TString
    TIdent
    TKeyword
    TOp
    TLParen
    TRParen
    TComma
    TSemicolon
    TColon
    TEOL
    TEOF
    TRemText
)

type NumKind uint8

const (
    NumInt NumKind = iota
    NumSng
    NumDbl
)

// Token은 Lexer의 출력 단위입니다.
// Num/NumKind 필드는 Kind == TNumber 일 때만 의미 있습니다.
type Token struct {
    Kind    TokenKind
    Lex     string  // 원시 텍스트
    Num     float64 // TNumber일 때 파싱된 값
    NumKind NumKind
    Line    int     // 1-based
    Col     int     // 1-based
}

func (k TokenKind) String() string {
    switch k {
    case TNumber:    return "NUMBER"
    case TString:    return "STRING"
    case TIdent:     return "IDENT"
    case TKeyword:   return "KEYWORD"
    case TOp:        return "OP"
    case TLParen:    return "LPAREN"
    case TRParen:    return "RPAREN"
    case TComma:     return "COMMA"
    case TSemicolon: return "SEMICOLON"
    case TColon:     return "COLON"
    case TEOL:       return "EOL"
    case TEOF:       return "EOF"
    case TRemText:   return "REM_TEXT"
    }
    return "?"
}
```

키워드 집합은 `map[string]struct{}`로 둡니다(`set` 대용).

```go
// internal/lexer/keywords.go
package lexer

var keywordSet = func() map[string]struct{} {
    list := []string{
        "AND","AS","ATN","BEEP","CHR$","CIRCLE","CINT","CLEAR","CLS","COLOR",
        "COS","CSNG","CDBL","DATA","DEF","DEFINT","DEFSNG","DEFDBL","DEFSTR",
        "DIM","ELSE","END","EQV","ERASE","ERL","ERR","EXP","FIX","FN","FOR",
        "GOSUB","GOTO","HEX$","IF","IMP","INKEY$","INPUT","INSTR","INT",
        "LEFT$","LEN","LET","LINE","LIST","LOAD","LOCATE","LOG","MID$","MOD",
        "NEW","NEXT","NOT","OCT$","OFF","ON","OR","PAINT","PLAY","PRESET",
        "PRINT","PSET","RANDOMIZE","READ","REM","RESTORE","RETURN","RIGHT$",
        "RND","RUN","SAVE","SCREEN","SGN","SIN","SOUND","SPACE$","SPC","SQR",
        "STEP","STOP","STR$","STRING$","SWAP","SYSTEM","TAB","TAN","THEN",
        "TIMER","TO","USING","VAL","WEND","WHILE","XOR",
    }
    m := make(map[string]struct{}, len(list))
    for _, w := range list {
        m[w] = struct{}{}
    }
    return m
}()

func IsKeyword(s string) bool {
    _, ok := keywordSet[s]
    return ok
}

var twoCharOps = map[string]struct{}{
    "<=": {}, ">=": {}, "<>": {},
}

var singleOps = map[byte]struct{}{
    '+': {}, '-': {}, '*': {}, '/': {}, '\\': {}, '^': {}, '=': {}, '<': {}, '>': {},
}
```

### 9.2 Lexer 구조체와 진입점

```go
// internal/lexer/lexer.go
package lexer

import (
    "strconv"
    "strings"
    "unicode"

    "github.com/chobocho/go_gwbasic/internal/common"
)

type Lexer struct {
    src    string
    pos    int
    line   int
    col    int
    tokens []Token
}

// Tokenize는 소스 문자열 전체를 토큰 슬라이스로 변환합니다.
// 마지막 토큰은 항상 TEOF.
func Tokenize(src string) ([]Token, error) {
    l := &Lexer{src: src, line: 1, col: 1}
    return l.run()
}

func (l *Lexer) run() ([]Token, error) {
    for l.pos < len(l.src) {
        if err := l.scanToken(); err != nil {
            return nil, err
        }
    }
    l.push(TEOF, "")
    return l.tokens, nil
}

// ─── 보조 메서드 ───────────────────────────────────────
func (l *Lexer) peek(off int) byte {
    if l.pos+off >= len(l.src) {
        return 0
    }
    return l.src[l.pos+off]
}

func (l *Lexer) advance() byte {
    if l.pos >= len(l.src) {
        return 0
    }
    ch := l.src[l.pos]
    l.pos++
    if ch == '\n' {
        l.line++
        l.col = 1
    } else {
        l.col++
    }
    return ch
}

func (l *Lexer) push(k TokenKind, lex string) {
    l.tokens = append(l.tokens, Token{
        Kind: k, Lex: lex,
        Line: l.line, Col: l.col - len(lex),
    })
}

func (l *Lexer) errf(format string, a ...interface{}) error {
    return &common.BasicError{
        Code: common.ErrSyntax,
        Msg:  "Syntax error: " + sprintf(format, a...),
        Pos:  common.SourcePos{Line: l.line, Col: l.col},
    }
}

func sprintf(f string, a ...interface{}) string {
    return strings.TrimRight(strings.Replace(f, "%v", "%v", -1), "")
}
```

> 💡 Go의 바이트 인덱싱은 ASCII 범위 안에서 안전합니다. 식별자에 한글을 허용하지 않을 것이므로 `byte` 단위 스캐닝이 충분합니다. UTF-8 안전이 필요한 부분(문자열 리터럴)은 그대로 바이트로 보관해도 문제 없습니다.

### 9.3 메인 스캐너

```go
func (l *Lexer) scanToken() error {
    ch := l.peek(0)

    // 공백 스킵 (개행 제외)
    if ch == ' ' || ch == '\t' || ch == '\r' {
        l.advance()
        return nil
    }
    // 개행 → EOL
    if ch == '\n' {
        l.advance()
        l.push(TEOL, "\n")
        return nil
    }
    // 작은따옴표 코멘트
    if ch == '\'' {
        return l.scanRem()
    }
    // 숫자
    if isDigit(ch) || (ch == '.' && isDigit(l.peek(1))) {
        return l.scanNumber()
    }
    // 16진수 / 8진수
    if ch == '&' {
        return l.scanRadixNumber()
    }
    // 문자열
    if ch == '"' {
        return l.scanString()
    }
    // 식별자 또는 키워드
    if isAlpha(ch) {
        return l.scanIdentOrKeyword()
    }

    // 구두점
    switch ch {
    case '(':
        l.advance()
        l.push(TLParen, "(")
        return nil
    case ')':
        l.advance()
        l.push(TRParen, ")")
        return nil
    case ',':
        l.advance()
        l.push(TComma, ",")
        return nil
    case ';':
        l.advance()
        l.push(TSemicolon, ";")
        return nil
    case ':':
        l.advance()
        l.push(TColon, ":")
        return nil
    case '?':
        l.advance()
        l.push(TKeyword, "PRINT")
        return nil
    }

    // 두 글자 연산자
    two := string([]byte{ch, l.peek(1)})
    if _, ok := twoCharOps[two]; ok {
        l.advance()
        l.advance()
        l.push(TOp, two)
        return nil
    }

    // 한 글자 연산자
    if _, ok := singleOps[ch]; ok {
        l.advance()
        l.push(TOp, string(ch))
        return nil
    }

    return l.errf("unexpected character %q", ch)
}

func isDigit(ch byte) bool { return ch >= '0' && ch <= '9' }
func isAlpha(ch byte) bool {
    return (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z')
}
func isAlnum(ch byte) bool { return isAlpha(ch) || isDigit(ch) }
```

### 9.4 숫자 스캐너

```go
func (l *Lexer) scanNumber() error {
    startLine, startCol := l.line, l.col
    var b strings.Builder
    hasDot, hasExp := false, false
    nk := NumInt

    // 정수부
    for isDigit(l.peek(0)) {
        b.WriteByte(l.advance())
    }
    // 소수점
    if l.peek(0) == '.' {
        hasDot = true
        b.WriteByte(l.advance())
        for isDigit(l.peek(0)) {
            b.WriteByte(l.advance())
        }
    }
    // 지수
    e := upper(l.peek(0))
    if e == 'E' || e == 'D' {
        hasExp = true
        if e == 'D' {
            nk = NumDbl
        } else {
            nk = NumSng
        }
        b.WriteByte(l.advance())
        if l.peek(0) == '+' || l.peek(0) == '-' {
            b.WriteByte(l.advance())
        }
        if !isDigit(l.peek(0)) {
            return l.errf("malformed exponent")
        }
        for isDigit(l.peek(0)) {
            b.WriteByte(l.advance())
        }
    }
    // 타입 접미
    switch l.peek(0) {
    case '%':
        l.advance()
        nk = NumInt
    case '!':
        l.advance()
        nk = NumSng
    case '#':
        l.advance()
        nk = NumDbl
    default:
        if !hasDot && !hasExp {
            v, _ := strconv.ParseInt(b.String(), 10, 64)
            if v > 32767 || v < -32768 {
                nk = NumSng
            } else {
                nk = NumInt
            }
        } else if nk == NumInt {
            nk = NumSng
        }
    }

    s := b.String()
    // 'D' 표기를 'E'로 정규화 후 ParseFloat
    sNorm := strings.ReplaceAll(strings.ReplaceAll(s, "D", "E"), "d", "e")
    v, err := strconv.ParseFloat(sNorm, 64)
    if err != nil {
        return l.errf("bad number: %s", s)
    }
    l.tokens = append(l.tokens, Token{
        Kind: TNumber, Lex: s, Num: v, NumKind: nk,
        Line: startLine, Col: startCol,
    })
    return nil
}

func (l *Lexer) scanRadixNumber() error {
    startLine, startCol := l.line, l.col
    l.advance() // &
    radix := 8
    prefix := "&"
    switch upper(l.peek(0)) {
    case 'H':
        radix = 16
        prefix += "H"
        l.advance()
    case 'O':
        prefix += "O"
        l.advance()
    }
    var b strings.Builder
    isOK := func(ch byte) bool {
        if radix == 16 {
            return isDigit(ch) ||
                (ch >= 'A' && ch <= 'F') || (ch >= 'a' && ch <= 'f')
        }
        return ch >= '0' && ch <= '7'
    }
    for isOK(l.peek(0)) {
        b.WriteByte(l.advance())
    }
    if b.Len() == 0 {
        return l.errf("bad &-literal")
    }
    v, err := strconv.ParseInt(b.String(), radix, 64)
    if err != nil {
        return l.errf("bad &-literal: %v", err)
    }
    l.tokens = append(l.tokens, Token{
        Kind: TNumber, Lex: prefix + b.String(),
        Num: float64(v), NumKind: NumInt,
        Line: startLine, Col: startCol,
    })
    return nil
}

func upper(b byte) byte {
    if b >= 'a' && b <= 'z' {
        return b - ('a' - 'A')
    }
    return b
}
```

### 9.5 문자열 스캐너

```go
func (l *Lexer) scanString() error {
    startLine, startCol := l.line, l.col
    l.advance() // "
    var b strings.Builder
    for {
        ch := l.peek(0)
        if ch == '"' || ch == '\n' || ch == 0 {
            break
        }
        b.WriteByte(l.advance())
    }
    if l.peek(0) != '"' {
        return l.errf("unterminated string")
    }
    l.advance() // 닫는 "
    l.tokens = append(l.tokens, Token{
        Kind: TString, Lex: b.String(),
        Line: startLine, Col: startCol,
    })
    return nil
}
```

### 9.6 식별자 / 키워드

```go
func (l *Lexer) scanIdentOrKeyword() error {
    startLine, startCol := l.line, l.col
    var b strings.Builder
    for isAlnum(l.peek(0)) {
        b.WriteByte(l.advance())
    }
    // 타입 접미 흡수
    switch l.peek(0) {
    case '$', '%', '!', '#':
        b.WriteByte(l.advance())
    }
    s := b.String()
    upperS := strings.ToUpper(s)

    if IsKeyword(upperS) {
        if upperS == "REM" {
            l.tokens = append(l.tokens, Token{
                Kind: TKeyword, Lex: "REM",
                Line: startLine, Col: startCol,
            })
            l.scanRemRest()
            return nil
        }
        l.tokens = append(l.tokens, Token{
            Kind: TKeyword, Lex: upperS,
            Line: startLine, Col: startCol,
        })
        return nil
    }
    if len(s) > 40 {
        return l.errf("identifier too long")
    }
    l.tokens = append(l.tokens, Token{
        Kind: TIdent, Lex: s,
        Line: startLine, Col: startCol,
    })
    _ = unicode.IsDigit // 미사용 import 회피용
    return nil
}

func (l *Lexer) scanRem() error {
    l.advance() // '
    l.scanRemRest()
    return nil
}

func (l *Lexer) scanRemRest() {
    var b strings.Builder
    for {
        ch := l.peek(0)
        if ch == '\n' || ch == 0 {
            break
        }
        b.WriteByte(l.advance())
    }
    l.tokens = append(l.tokens, Token{
        Kind: TRemText, Lex: b.String(),
        Line: l.line, Col: l.col,
    })
}
```

### 9.7 키워드 충돌 처리

`PRINT`, `END`, `INT` 같은 키워드를 식별자로 쓸 수 없는 것은 명확합니다. `LEFT$`, `MID$` 처럼 `$`를 포함한 *함수형 키워드*는 식별자처럼 보이지만, 우리는 두 가지 전략으로 구분합니다.

1. 토큰화 시 식별자 + 접미를 합쳐 한 단어로 만든 후, 키워드 집합에 있으면 KEYWORD로 분류.
2. `INT`, `LEN` 같은 *접미 없는* 함수명도 KEYWORD로 분류. 사용자는 같은 이름을 변수로 쓸 수 없게 됩니다.

⚠️ 이 결정으로 사용자가 `INT = 5` 라고 쓰면 파싱 에러가 납니다. 이는 GW-BASIC 동작과 동일합니다.

### 9.8 라인 번호의 처리

라인 번호 자체는 별도의 토큰 타입이 아니라 **라인 시작 위치의 NUMBER 토큰**으로 표현됩니다. Parser가 줄 시작에서 NUMBER를 만나면 라인 번호로 해석합니다(12장).

### 9.9 테스트 — Go `testing` 패키지

`internal/lexer/lexer_test.go`:

```go
package lexer

import (
    "reflect"
    "testing"
)

func kinds(toks []Token) []TokenKind {
    out := make([]TokenKind, len(toks))
    for i, t := range toks {
        out[i] = t.Kind
    }
    return out
}

func TestBasicTokens(t *testing.T) {
    toks, err := Tokenize(`10 PRINT "HELLO", A%+1`)
    if err != nil {
        t.Fatal(err)
    }
    want := []TokenKind{
        TNumber, TKeyword, TString, TComma,
        TIdent, TOp, TNumber, TEOF,
    }
    if !reflect.DeepEqual(kinds(toks), want) {
        t.Errorf("got %v, want %v", kinds(toks), want)
    }
    if toks[0].Num != 10 {
        t.Errorf("first num = %v, want 10", toks[0].Num)
    }
    if toks[2].Lex != "HELLO" {
        t.Errorf("string lex = %q", toks[2].Lex)
    }
    if toks[4].Lex != "A%" {
        t.Errorf("ident lex = %q", toks[4].Lex)
    }
}

func TestRadixNumbers(t *testing.T) {
    toks, _ := Tokenize("&H1A &O17 &7")
    cases := []struct {
        i    int
        want float64
    }{{0, 26}, {1, 15}, {2, 7}}
    for _, c := range cases {
        if toks[c.i].Num != c.want {
            t.Errorf("toks[%d].Num = %v, want %v", c.i, toks[c.i].Num, c.want)
        }
    }
}

func TestRemUntilEOL(t *testing.T) {
    toks, _ := Tokenize("10 REM hello world\n20 PRINT 1")
    var found string
    for _, tk := range toks {
        if tk.Kind == TRemText {
            found = tk.Lex
            break
        }
    }
    if found != " hello world" {
        t.Errorf("REM text = %q", found)
    }
}

func TestTickComment(t *testing.T) {
    toks, _ := Tokenize("10 PRINT 1 ' tail comment")
    var found string
    for _, tk := range toks {
        if tk.Kind == TRemText {
            found = tk.Lex
            break
        }
    }
    if found != " tail comment" {
        t.Errorf("tick text = %q", found)
    }
}

func TestTwoCharOps(t *testing.T) {
    toks, _ := Tokenize("A <= B >= C <> D")
    var ops []string
    for _, tk := range toks {
        if tk.Kind == TOp {
            ops = append(ops, tk.Lex)
        }
    }
    want := []string{"<=", ">=", "<>"}
    if !reflect.DeepEqual(ops, want) {
        t.Errorf("ops = %v, want %v", ops, want)
    }
}

func TestFloatExp(t *testing.T) {
    toks, _ := Tokenize("3.14 1.5E10 .5#")
    if toks[0].Num < 3.13 || toks[0].Num > 3.15 {
        t.Errorf("3.14 parsed as %v", toks[0].Num)
    }
    if toks[1].Num != 1.5e10 {
        t.Errorf("1.5E10 parsed as %v", toks[1].Num)
    }
    if toks[2].NumKind != NumDbl {
        t.Errorf(".5# numKind = %v", toks[2].NumKind)
    }
}

func TestQuestionToPrint(t *testing.T) {
    toks, _ := Tokenize("? 1")
    if toks[0].Lex != "PRINT" {
        t.Errorf("? not converted to PRINT, got %q", toks[0].Lex)
    }
}
```

`go test ./internal/lexer/...` 명령으로 실행합니다.

### 9.10 엣지 케이스 정리

| 입력 | 토큰 | 비고 |
|------|------|------|
| `100A=1` | NUMBER(100), IDENT(A), OP(=), NUMBER(1) | 라인 100, A=1 |
| `IFA=1THEN` | KEYWORD(IF), IDENT(A), OP(=), NUMBER(1), KEYWORD(THEN) | 키워드 사이 공백 불요 |
| `A$="x"` | IDENT(A$), OP(=), STRING("x") | $는 식별자에 흡수 |
| `1.E5` | NUMBER(100000) | `1.` 도 부동소수 |
| `.5` | NUMBER(0.5) | 정수부 생략 가능 |
| `&H10` | NUMBER(16) | 16진수 |

### 9.11 성능 노트

Go에서는 다음 점이 중요합니다.

- `[]Token`를 `make([]Token, 0, len(src)/4)`처럼 *예상 크기로 미리 할당*하면 append 시 reallocation을 줄일 수 있음
- `strings.Builder`는 `+=` 누적보다 빠르지만, 짧은 토큰에서는 차이가 미미함
- `strings.ToUpper`는 ASCII 범위에서도 알로케이션을 일으킴. 키워드 비교에서 *대문자 변환 캐시*가 가능하나 가독성을 우선해 평범하게 둠

본 구현은 가독성을 우선하지만, 1만 라인 이상의 BASIC 프로그램에서도 수십 ms 안에 토큰화가 끝납니다.

```go
// 벤치마크 예시
func BenchmarkTokenize(b *testing.B) {
    src := strings.Repeat(`10 PRINT "HI" : A%=A%+1`+"\n", 1000)
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = Tokenize(src)
    }
}
```

### 9.12 다음 장 예고

10장에서는 이 토큰 스트림을 받아 AST를 만드는 Parser의 골격을 세웁니다. *재귀 하강* 방식으로 시작해, 표현식 부분만 *Pratt* 알고리즘으로 전환하는 하이브리드 구조입니다.

---

> 9장 끝.


---

# 제3부 · 프론트엔드 (2) — Parser와 AST

## 10장. Parser 기초 — 재귀 하강

### 10.1 파서의 역할

Parser는 토큰 시퀀스를 받아 **추상 구문 트리(AST)** 를 만듭니다. 본 구현은 두 가지 기법을 결합합니다.

- **재귀 하강 (Recursive descent)** — 문장 단위 파싱
- **Pratt parsing** — 표현식 단위 파싱 (연산자 우선순위)

Go에서는 `Cursor` 구조체가 토큰 위치를 들고 다니며, 문장별 파서 함수들이 이 커서를 주고받는 방식으로 자연스럽게 구현됩니다.

### 10.2 토큰 커서

```go
// internal/parser/cursor.go
package parser

import (
    "fmt"

    "github.com/chobocho/go_gwbasic/internal/common"
    "github.com/chobocho/go_gwbasic/internal/lexer"
)

type Cursor struct {
    toks []lexer.Token
    i    int
}

func NewCursor(toks []lexer.Token) *Cursor {
    return &Cursor{toks: toks}
}

func (c *Cursor) Peek(off int) lexer.Token {
    n := c.i + off
    if n >= len(c.toks) {
        return c.toks[len(c.toks)-1]
    }
    return c.toks[n]
}

func (c *Cursor) Next() lexer.Token {
    t := c.Peek(0)
    if c.i < len(c.toks) {
        c.i++
    }
    return t
}

// Check는 다음 토큰이 주어진 종류 (선택적으로 lex)와 일치하는지만 확인 (소비 X).
func (c *Cursor) Check(k lexer.TokenKind, lex ...string) bool {
    t := c.Peek(0)
    if t.Kind != k {
        return false
    }
    if len(lex) > 0 && t.Lex != lex[0] {
        return false
    }
    return true
}

// Match는 일치하면 소비하고 true.
func (c *Cursor) Match(k lexer.TokenKind, lex ...string) bool {
    if !c.Check(k, lex...) {
        return false
    }
    c.Next()
    return true
}

// Expect는 일치하지 않으면 에러.
func (c *Cursor) Expect(k lexer.TokenKind, lex ...string) (lexer.Token, error) {
    if !c.Check(k, lex...) {
        t := c.Peek(0)
        want := k.String()
        if len(lex) > 0 {
            want = fmt.Sprintf("%s(%s)", want, lex[0])
        }
        return t, &common.BasicError{
            Code: common.ErrSyntax,
            Msg:  fmt.Sprintf("expected %s, got %s(%q)", want, t.Kind, t.Lex),
            Pos:  common.SourcePos{Line: t.Line, Col: t.Col},
        }
    }
    return c.Next(), nil
}

func (c *Cursor) IsEOF() bool { return c.Peek(0).Kind == lexer.TEOF }
func (c *Cursor) IsEOL() bool { return c.Peek(0).Kind == lexer.TEOL || c.IsEOF() }
```

### 10.3 메인 파싱 루프

```go
// internal/parser/parser.go
package parser

import (
    "github.com/chobocho/go_gwbasic/internal/ast"
    "github.com/chobocho/go_gwbasic/internal/lexer"
)

type Parser struct {
    cur *Cursor
}

func New(toks []lexer.Token) *Parser {
    return &Parser{cur: NewCursor(toks)}
}

// Parse는 전체 프로그램을 파싱해 *ast.Program을 반환합니다.
func Parse(toks []lexer.Token) (*ast.Program, error) {
    p := New(toks)
    return p.ParseProgram()
}

func (p *Parser) ParseProgram() (*ast.Program, error) {
    prog := &ast.Program{}
    for !p.cur.IsEOF() {
        if p.cur.Match(lexer.TEOL) {
            continue
        }
        line, err := p.parseLine()
        if err != nil {
            return nil, err
        }
        prog.Lines = append(prog.Lines, line)
    }
    return prog, nil
}

func (p *Parser) parseLine() (*ast.Line, error) {
    first := p.cur.Peek(0)
    var num int
    hasNum := false

    if first.Kind == lexer.TNumber {
        num = int(first.Num)
        hasNum = true
        p.cur.Next()
    }

    var stmts []ast.Stmt
    s, err := p.parseStatement()
    if err != nil {
        return nil, err
    }
    stmts = append(stmts, s)

    for p.cur.Match(lexer.TColon) {
        if p.cur.IsEOL() {
            break
        }
        s, err := p.parseStatement()
        if err != nil {
            return nil, err
        }
        stmts = append(stmts, s)
    }

    if !p.cur.IsEOF() {
        if _, err := p.cur.Expect(lexer.TEOL); err != nil {
            return nil, err
        }
    }

    line := &ast.Line{
        Statements: stmts,
        SourceLine: first.Line,
    }
    if hasNum {
        line.Number = &num
    }
    return line, nil
}
```

### 10.4 분리 전략

Go 패키지는 같은 패키지 내 파일이 자동으로 결합되므로, 표현식 파서와 문장 파서를 같은 `parser` 패키지의 별개 파일(`expr.go`, `stmt.go`)로 분리합니다.

---

## 11장. 표현식 파싱 — Pratt 알고리즘

### 11.1 왜 Pratt인가

전통적 재귀 하강은 우선순위 단계마다 함수를 만들어야 해서 12단계 함수가 필요합니다. Pratt은 *우선순위 표 한 장* + *루프 한 개*로 모든 이항 연산자를 처리합니다.

핵심 아이디어:

> 각 연산자에 **결합력(binding power)** 을 부여하고, 표현식을 파싱할 때 *현재 결합력보다 강한* 연산자가 보이는 동안만 흡수한다.

### 11.2 결합력 표 (Go 구현)

```go
// internal/parser/expr.go
package parser

type bp struct{ left, right int }

var binBP = map[string]bp{
    "OR":  {10, 11},
    "XOR": {12, 13},
    "AND": {14, 15},
    "=":   {20, 21},
    "<>":  {20, 21},
    "<":   {20, 21},
    "<=":  {20, 21},
    ">":   {20, 21},
    ">=":  {20, 21},
    "+":   {30, 31},
    "-":   {30, 31},
    "MOD": {40, 41},
    "\\":  {42, 43},
    "*":   {44, 45},
    "/":   {44, 45},
    "^":   {61, 60}, // 우결합
}

const (
    unaryRBP = 50 // 단항 + - 의 우측 결합력
    notBP    = 16 // NOT의 결합력
)
```

좌결합은 `{L, L+1}`, 우결합은 `{L, L-1}`로 표현합니다(우측 bp가 작으면 같은 우선순위에서 오른쪽으로 묶임).

### 11.3 핵심 함수

```go
import (
    "fmt"
    "github.com/chobocho/go_gwbasic/internal/ast"
    "github.com/chobocho/go_gwbasic/internal/common"
    "github.com/chobocho/go_gwbasic/internal/lexer"
)

func (p *Parser) parseExpression(minBP int) (ast.Expr, error) {
    lhs, err := p.parsePrefix()
    if err != nil {
        return nil, err
    }
    for {
        t := p.cur.Peek(0)
        var opName string

        switch t.Kind {
        case lexer.TOp:
            opName = t.Lex
        case lexer.TKeyword:
            switch t.Lex {
            case "AND", "OR", "XOR", "MOD":
                opName = t.Lex
            }
        }
        if opName == "" {
            break
        }
        b, ok := binBP[opName]
        if !ok || b.left < minBP {
            break
        }
        p.cur.Next()
        rhs, err := p.parseExpression(b.right)
        if err != nil {
            return nil, err
        }
        lhs = &ast.BinaryExpr{Op: opName, LHS: lhs, RHS: rhs}
    }
    return lhs, nil
}

func (p *Parser) parsePrefix() (ast.Expr, error) {
    t := p.cur.Peek(0)

    // 단항 +/-
    if t.Kind == lexer.TOp && (t.Lex == "+" || t.Lex == "-") {
        p.cur.Next()
        operand, err := p.parseExpression(unaryRBP)
        if err != nil {
            return nil, err
        }
        return &ast.UnaryExpr{Op: t.Lex, Operand: operand}, nil
    }

    // NOT
    if t.Kind == lexer.TKeyword && t.Lex == "NOT" {
        p.cur.Next()
        operand, err := p.parseExpression(notBP)
        if err != nil {
            return nil, err
        }
        return &ast.UnaryExpr{Op: "NOT", Operand: operand}, nil
    }

    // 괄호
    if t.Kind == lexer.TLParen {
        p.cur.Next()
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        if _, err := p.cur.Expect(lexer.TRParen); err != nil {
            return nil, err
        }
        return e, nil
    }

    // 리터럴
    if t.Kind == lexer.TNumber {
        p.cur.Next()
        nk := ast.NumInt
        switch t.NumKind {
        case lexer.NumSng:
            nk = ast.NumSng
        case lexer.NumDbl:
            nk = ast.NumDbl
        }
        return &ast.NumLit{Value: t.Num, NumType: nk}, nil
    }
    if t.Kind == lexer.TString {
        p.cur.Next()
        return &ast.StrLit{Value: t.Lex}, nil
    }

    // FN <ident>(...)
    if t.Kind == lexer.TKeyword && t.Lex == "FN" {
        p.cur.Next()
        id, err := p.cur.Expect(lexer.TIdent)
        if err != nil {
            return nil, err
        }
        var args []ast.Expr
        if p.cur.Match(lexer.TLParen) {
            args, err = p.parseExprList()
            if err != nil {
                return nil, err
            }
            if _, err := p.cur.Expect(lexer.TRParen); err != nil {
                return nil, err
            }
        }
        return &ast.FnCall{Target: "FN_" + upperASCII(id.Lex), Args: args}, nil
    }

    // 내장 함수
    if t.Kind == lexer.TKeyword && isBuiltinFunc(t.Lex) {
        p.cur.Next()
        var args []ast.Expr
        if p.cur.Match(lexer.TLParen) {
            var err error
            args, err = p.parseExprList()
            if err != nil {
                return nil, err
            }
            if _, err := p.cur.Expect(lexer.TRParen); err != nil {
                return nil, err
            }
        }
        return &ast.FnCall{Target: t.Lex, Args: args}, nil
    }

    // 식별자
    if t.Kind == lexer.TIdent {
        p.cur.Next()
        if p.cur.Match(lexer.TLParen) {
            indices, err := p.parseExprList()
            if err != nil {
                return nil, err
            }
            if _, err := p.cur.Expect(lexer.TRParen); err != nil {
                return nil, err
            }
            return &ast.ArrayRef{Name: t.Lex, Indices: indices}, nil
        }
        return &ast.VarRef{Name: t.Lex}, nil
    }

    return nil, &common.BasicError{
        Code: common.ErrSyntax,
        Msg:  fmt.Sprintf("unexpected token in expression: %s(%q)", t.Kind, t.Lex),
        Pos:  common.SourcePos{Line: t.Line, Col: t.Col},
    }
}

func (p *Parser) parseExprList() ([]ast.Expr, error) {
    var list []ast.Expr
    if p.cur.Check(lexer.TRParen) {
        return list, nil
    }
    e, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    list = append(list, e)
    for p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        list = append(list, e)
    }
    return list, nil
}

var builtinFuncs = func() map[string]struct{} {
    list := []string{
        "ABS", "ASC", "ATN", "CDBL", "CHR$", "CINT", "COS", "CSNG",
        "EXP", "FIX", "HEX$", "INKEY$", "INSTR", "INT", "LEFT$", "LEN",
        "LOG", "MID$", "OCT$", "RIGHT$", "RND", "SGN", "SIN", "SPACE$",
        "SQR", "STR$", "STRING$", "TAB", "TAN", "TIMER", "VAL",
    }
    m := make(map[string]struct{}, len(list))
    for _, w := range list {
        m[w] = struct{}{}
    }
    return m
}()

func isBuiltinFunc(s string) bool {
    _, ok := builtinFuncs[s]
    return ok
}

func upperASCII(s string) string {
    b := []byte(s)
    for i := range b {
        if b[i] >= 'a' && b[i] <= 'z' {
            b[i] -= 'a' - 'A'
        }
    }
    return string(b)
}
```

### 11.4 동작 검증

`PRINT 1 + 2 * 3 ^ 2`를 파싱한 결과:

```
BinaryExpr{Op: "+",
  LHS: NumLit{1},
  RHS: BinaryExpr{Op: "*",
    LHS: NumLit{2},
    RHS: BinaryExpr{Op: "^", LHS: NumLit{3}, RHS: NumLit{2}}}}
```

`PRINT NOT 1 = 0`:

```
UnaryExpr{Op: "NOT",
  Operand: BinaryExpr{Op: "=", LHS: NumLit{1}, RHS: NumLit{0}}}
```

NOT의 결합력(16)이 비교(20)보다 *낮기* 때문에 비교가 먼저 묶이고 NOT이 그 결과를 받습니다 — GW-BASIC 동작과 일치.

### 11.5 단항 마이너스의 함정

`-2^2`는 GW-BASIC에서 -4 입니다. 표를 보면 단항 `-`의 결합력은 50, `^`의 좌결합력은 61. `parsePrefix`에서 단항이 호출되면 `parseExpression(unaryRBP=50)`을 재귀 호출하고, 그 안에서 `^`(lbp=61)이 보이면 50≤61 이므로 흡수됩니다 → `-(2^2) = -4`. 정확.

반대로 `2^-2`는 `^`의 우측에서 단항이 다시 시작되므로 `2^(-2) = 0.25` — 이것도 일치.

### 11.6 테스트

`internal/parser/expr_test.go`:

```go
package parser

import (
    "testing"

    "github.com/chobocho/go_gwbasic/internal/ast"
    "github.com/chobocho/go_gwbasic/internal/lexer"
)

func parseExprStr(t *testing.T, src string) ast.Expr {
    t.Helper()
    toks, err := lexer.Tokenize(src)
    if err != nil {
        t.Fatal(err)
    }
    p := New(toks)
    e, err := p.parseExpression(0)
    if err != nil {
        t.Fatal(err)
    }
    return e
}

func TestPrecedence(t *testing.T) {
    e := parseExprStr(t, "1 + 2 * 3")
    b, ok := e.(*ast.BinaryExpr)
    if !ok || b.Op != "+" {
        t.Fatalf("top op = %v", e)
    }
    if rhs, ok := b.RHS.(*ast.BinaryExpr); !ok || rhs.Op != "*" {
        t.Fatalf("rhs op = %v", b.RHS)
    }
}

func TestPowRightAssoc(t *testing.T) {
    e := parseExprStr(t, "2^3^2") // 2^(3^2) = 512
    top, _ := e.(*ast.BinaryExpr)
    if top.Op != "^" {
        t.Fatal("top op")
    }
    rhs, _ := top.RHS.(*ast.BinaryExpr)
    if rhs == nil || rhs.Op != "^" {
        t.Fatal("rhs is not nested ^")
    }
}

func TestUnaryMinusPow(t *testing.T) {
    e := parseExprStr(t, "-2^2")
    u, ok := e.(*ast.UnaryExpr)
    if !ok || u.Op != "-" {
        t.Fatalf("expected unary -, got %v", e)
    }
    if _, ok := u.Operand.(*ast.BinaryExpr); !ok {
        t.Fatal("operand should be ^")
    }
}

func TestLogicalAnd(t *testing.T) {
    e := parseExprStr(t, "A=1 AND B=2")
    b, _ := e.(*ast.BinaryExpr)
    if b == nil || b.Op != "AND" {
        t.Fatal("top op should be AND")
    }
}

func TestFnCall(t *testing.T) {
    e := parseExprStr(t, `LEFT$("hello", 3)`)
    f, ok := e.(*ast.FnCall)
    if !ok || f.Target != "LEFT$" {
        t.Fatal("expected LEFT$ call")
    }
    if len(f.Args) != 2 {
        t.Fatal("expected 2 args")
    }
}
```

---

## 12장. 문장 파싱

### 12.1 디스패치 테이블

```go
// internal/parser/stmt.go
package parser

import (
    "fmt"

    "github.com/chobocho/go_gwbasic/internal/ast"
    "github.com/chobocho/go_gwbasic/internal/common"
    "github.com/chobocho/go_gwbasic/internal/lexer"
)

type stmtParser func(p *Parser) (ast.Stmt, error)

var stmtTable = map[string]stmtParser{
    "PRINT":     (*Parser).parsePrint,
    "INPUT":     (*Parser).parseInput,
    "LET":       (*Parser).parseLet,
    "IF":        (*Parser).parseIf,
    "FOR":       (*Parser).parseFor,
    "NEXT":      (*Parser).parseNext,
    "WHILE":     (*Parser).parseWhile,
    "WEND":      (*Parser).parseWend,
    "GOTO":      (*Parser).parseGoto,
    "GOSUB":     (*Parser).parseGosub,
    "RETURN":    (*Parser).parseReturn,
    "ON":        (*Parser).parseOn,
    "END":       func(*Parser) (ast.Stmt, error) { return &ast.EndStmt{}, nil },
    "STOP":      func(*Parser) (ast.Stmt, error) { return &ast.StopStmt{}, nil },
    "REM":       (*Parser).parseRemKw,
    "DIM":       (*Parser).parseDim,
    "DATA":      (*Parser).parseData,
    "READ":      (*Parser).parseRead,
    "RESTORE":   (*Parser).parseRestore,
    "DEF":       (*Parser).parseDef,
    "CLS":       (*Parser).parseCls,
    "SCREEN":    (*Parser).parseScreen,
    "COLOR":     (*Parser).parseColor,
    "PSET":      func(p *Parser) (ast.Stmt, error) { return p.parsePsetLike("PSET") },
    "PRESET":    func(p *Parser) (ast.Stmt, error) { return p.parsePsetLike("PRESET") },
    "LINE":      (*Parser).parseLineStmt,
    "CIRCLE":    (*Parser).parseCircle,
    "PAINT":     (*Parser).parsePaint,
    "LOCATE":    (*Parser).parseLocate,
    "SOUND":     (*Parser).parseSound,
    "PLAY":      (*Parser).parsePlay,
    "BEEP":      func(*Parser) (ast.Stmt, error) { return &ast.BeepStmt{}, nil },
    "RANDOMIZE": (*Parser).parseRandomize,
    "CLEAR":     func(*Parser) (ast.Stmt, error) { return &ast.ClearStmt{}, nil },
    "SWAP":      (*Parser).parseSwap,
    "RUN":       func(*Parser) (ast.Stmt, error) { return &ast.RunStmt{}, nil },
    "NEW":       func(*Parser) (ast.Stmt, error) { return &ast.NewStmt{}, nil },
    "LIST":      (*Parser).parseList,
}

func (p *Parser) parseStatement() (ast.Stmt, error) {
    t := p.cur.Peek(0)

    if t.Kind == lexer.TRemText {
        p.cur.Next()
        return &ast.RemStmt{Text: t.Lex}, nil
    }
    if t.Kind == lexer.TKeyword {
        if fn, ok := stmtTable[t.Lex]; ok {
            p.cur.Next()
            return fn(p)
        }
        // 인식되지만 미구현
        p.cur.Next()
        return &ast.UnimplementedStmt{Name: t.Lex}, nil
    }
    if t.Kind == lexer.TIdent {
        return p.parseAssign() // 묵시적 LET
    }
    if t.Kind == lexer.TEOL || t.Kind == lexer.TEOF {
        return &ast.RemStmt{}, nil
    }
    return nil, &common.BasicError{
        Code: common.ErrSyntax,
        Msg:  fmt.Sprintf("unexpected token: %s(%q)", t.Kind, t.Lex),
        Pos:  common.SourcePos{Line: t.Line, Col: t.Col},
    }
}
```

### 12.2 LET / 묵시적 할당

```go
func (p *Parser) parseLet() (ast.Stmt, error) { return p.parseAssign() }

func (p *Parser) parseAssign() (ast.Stmt, error) {
    target, err := p.parseLvalue()
    if err != nil {
        return nil, err
    }
    if _, err := p.cur.Expect(lexer.TOp, "="); err != nil {
        return nil, err
    }
    val, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    return &ast.AssignStmt{Target: target, Value: val}, nil
}

func (p *Parser) parseLvalue() (ast.Lvalue, error) {
    id, err := p.cur.Expect(lexer.TIdent)
    if err != nil {
        return nil, err
    }
    if p.cur.Match(lexer.TLParen) {
        first, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        indices := []ast.Expr{first}
        for p.cur.Match(lexer.TComma) {
            e, err := p.parseExpression(0)
            if err != nil {
                return nil, err
            }
            indices = append(indices, e)
        }
        if _, err := p.cur.Expect(lexer.TRParen); err != nil {
            return nil, err
        }
        return &ast.ArrayRef{Name: id.Lex, Indices: indices}, nil
    }
    return &ast.VarRef{Name: id.Lex}, nil
}
```

### 12.3 PRINT

```go
func (p *Parser) parsePrint() (ast.Stmt, error) {
    var items []ast.PrintItem
    var trailing string
    for !p.cur.IsEOL() && !p.cur.Check(lexer.TColon) && !p.cur.Check(lexer.TKeyword, "ELSE") {
        if p.cur.Match(lexer.TSemicolon) {
            items = append(items, ast.PrintItem{Kind: ast.PIPSep, Sep: ";"})
            trailing = ";"
            continue
        }
        if p.cur.Match(lexer.TComma) {
            items = append(items, ast.PrintItem{Kind: ast.PIPSep, Sep: ","})
            trailing = ","
            continue
        }
        if p.cur.Check(lexer.TKeyword, "TAB") || p.cur.Check(lexer.TKeyword, "SPC") {
            which := p.cur.Next().Lex
            if _, err := p.cur.Expect(lexer.TLParen); err != nil {
                return nil, err
            }
            arg, err := p.parseExpression(0)
            if err != nil {
                return nil, err
            }
            if _, err := p.cur.Expect(lexer.TRParen); err != nil {
                return nil, err
            }
            items = append(items, ast.PrintItem{Kind: ast.PIPFunc, Name: which, Arg: arg})
            trailing = ""
            continue
        }
        if p.cur.Match(lexer.TKeyword, "USING") {
            fmtExpr, err := p.parseExpression(0)
            if err != nil {
                return nil, err
            }
            if _, err := p.cur.Expect(lexer.TSemicolon); err != nil {
                return nil, err
            }
            first, err := p.parseExpression(0)
            if err != nil {
                return nil, err
            }
            args := []ast.Expr{first}
            for p.cur.Match(lexer.TSemicolon) {
                e, err := p.parseExpression(0)
                if err != nil {
                    return nil, err
                }
                args = append(args, e)
            }
            items = append(items, ast.PrintItem{Kind: ast.PIPUsing, Fmt: fmtExpr, Args: args})
            trailing = ""
            continue
        }
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        items = append(items, ast.PrintItem{Kind: ast.PIPExpr, Expr: e})
        trailing = ""
    }
    return &ast.PrintStmt{Items: items, SuppressNL: trailing != ""}, nil
}
```

### 12.4 INPUT / IF / FOR / NEXT / WHILE / WEND

```go
func (p *Parser) parseInput() (ast.Stmt, error) {
    sup := false
    if p.cur.Match(lexer.TSemicolon) {
        sup = true
    }
    prompt, sep := "", ";"
    if p.cur.Check(lexer.TString) {
        prompt = p.cur.Next().Lex
        if p.cur.Match(lexer.TSemicolon) {
            sep = ";"
        } else if p.cur.Match(lexer.TComma) {
            sep = ","
        } else {
            return nil, common.NewError(common.ErrSyntax, "expected ; or , after INPUT prompt")
        }
    }
    first, err := p.parseLvalue()
    if err != nil {
        return nil, err
    }
    targets := []ast.Lvalue{first}
    for p.cur.Match(lexer.TComma) {
        lv, err := p.parseLvalue()
        if err != nil {
            return nil, err
        }
        targets = append(targets, lv)
    }
    return &ast.InputStmt{
        Prompt: prompt, PromptSep: sep,
        Targets: targets, SuppressQuestion: sup,
    }, nil
}

func (p *Parser) parseIf() (ast.Stmt, error) {
    cond, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    if _, err := p.cur.Expect(lexer.TKeyword, "THEN"); err != nil {
        return nil, err
    }
    thenB, err := p.parseThenOrElse()
    if err != nil {
        return nil, err
    }
    var elseB *ast.Branch
    if p.cur.Match(lexer.TKeyword, "ELSE") {
        b, err := p.parseThenOrElse()
        if err != nil {
            return nil, err
        }
        elseB = b
    }
    return &ast.IfStmt{Cond: cond, Then: thenB, Else: elseB}, nil
}

func (p *Parser) parseThenOrElse() (*ast.Branch, error) {
    if p.cur.Check(lexer.TNumber) {
        n := int(p.cur.Next().Num)
        return &ast.Branch{IsGoto: true, GotoTarget: n}, nil
    }
    s, err := p.parseStatement()
    if err != nil {
        return nil, err
    }
    stmts := []ast.Stmt{s}
    for p.cur.Match(lexer.TColon) {
        if p.cur.IsEOL() || p.cur.Check(lexer.TKeyword, "ELSE") {
            break
        }
        s, err := p.parseStatement()
        if err != nil {
            return nil, err
        }
        stmts = append(stmts, s)
    }
    return &ast.Branch{Stmts: stmts}, nil
}

func (p *Parser) parseFor() (ast.Stmt, error) {
    id, err := p.cur.Expect(lexer.TIdent)
    if err != nil {
        return nil, err
    }
    if _, err := p.cur.Expect(lexer.TOp, "="); err != nil {
        return nil, err
    }
    start, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    if _, err := p.cur.Expect(lexer.TKeyword, "TO"); err != nil {
        return nil, err
    }
    end, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    var step ast.Expr
    if p.cur.Match(lexer.TKeyword, "STEP") {
        step, err = p.parseExpression(0)
        if err != nil {
            return nil, err
        }
    }
    return &ast.ForStmt{VarName: id.Lex, Start: start, End: end, Step: step}, nil
}

func (p *Parser) parseNext() (ast.Stmt, error) {
    var vars []string
    if p.cur.Check(lexer.TIdent) {
        vars = append(vars, p.cur.Next().Lex)
        for p.cur.Match(lexer.TComma) {
            id, err := p.cur.Expect(lexer.TIdent)
            if err != nil {
                return nil, err
            }
            vars = append(vars, id.Lex)
        }
    }
    return &ast.NextStmt{Vars: vars}, nil
}

func (p *Parser) parseWhile() (ast.Stmt, error) {
    cond, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    return &ast.WhileStmt{Cond: cond}, nil
}

func (p *Parser) parseWend() (ast.Stmt, error) { return &ast.WendStmt{}, nil }
```

### 12.5 GOTO / GOSUB / RETURN / ON

```go
func (p *Parser) parseGoto() (ast.Stmt, error) {
    n, err := p.cur.Expect(lexer.TNumber)
    if err != nil {
        return nil, err
    }
    return &ast.GotoStmt{Target: int(n.Num)}, nil
}
func (p *Parser) parseGosub() (ast.Stmt, error) {
    n, err := p.cur.Expect(lexer.TNumber)
    if err != nil {
        return nil, err
    }
    return &ast.GosubStmt{Target: int(n.Num)}, nil
}
func (p *Parser) parseReturn() (ast.Stmt, error) {
    s := &ast.ReturnStmt{}
    if p.cur.Check(lexer.TNumber) {
        n := int(p.cur.Next().Num)
        s.Target = &n
    }
    return s, nil
}
func (p *Parser) parseOn() (ast.Stmt, error) {
    e, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    var mode string
    if p.cur.Match(lexer.TKeyword, "GOTO") {
        mode = "GOTO"
    } else if p.cur.Match(lexer.TKeyword, "GOSUB") {
        mode = "GOSUB"
    } else {
        return nil, common.NewError(common.ErrSyntax, "expected GOTO or GOSUB after ON")
    }
    n, err := p.cur.Expect(lexer.TNumber)
    if err != nil {
        return nil, err
    }
    targets := []int{int(n.Num)}
    for p.cur.Match(lexer.TComma) {
        n, err := p.cur.Expect(lexer.TNumber)
        if err != nil {
            return nil, err
        }
        targets = append(targets, int(n.Num))
    }
    return &ast.OnGotoStmt{Expr: e, Mode: mode, Targets: targets}, nil
}
```

### 12.6 DIM / DATA / READ / RESTORE / DEF

```go
func (p *Parser) parseDim() (ast.Stmt, error) {
    d, err := p.parseDimDecl()
    if err != nil {
        return nil, err
    }
    decls := []ast.DimDecl{d}
    for p.cur.Match(lexer.TComma) {
        d, err := p.parseDimDecl()
        if err != nil {
            return nil, err
        }
        decls = append(decls, d)
    }
    return &ast.DimStmt{Decls: decls}, nil
}

func (p *Parser) parseDimDecl() (ast.DimDecl, error) {
    id, err := p.cur.Expect(lexer.TIdent)
    if err != nil {
        return ast.DimDecl{}, err
    }
    if _, err := p.cur.Expect(lexer.TLParen); err != nil {
        return ast.DimDecl{}, err
    }
    first, err := p.parseExpression(0)
    if err != nil {
        return ast.DimDecl{}, err
    }
    dims := []ast.Expr{first}
    for p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return ast.DimDecl{}, err
        }
        dims = append(dims, e)
    }
    if _, err := p.cur.Expect(lexer.TRParen); err != nil {
        return ast.DimDecl{}, err
    }
    return ast.DimDecl{Name: id.Lex, Dims: dims}, nil
}

func (p *Parser) parseData() (ast.Stmt, error) {
    first, err := p.readDataItem()
    if err != nil {
        return nil, err
    }
    items := []ast.DataItem{first}
    for p.cur.Match(lexer.TComma) {
        di, err := p.readDataItem()
        if err != nil {
            return nil, err
        }
        items = append(items, di)
    }
    return &ast.DataStmt{Items: items}, nil
}
func (p *Parser) readDataItem() (ast.DataItem, error) {
    t := p.cur.Peek(0)
    switch t.Kind {
    case lexer.TNumber:
        p.cur.Next()
        return ast.DataItem{IsStr: false, Num: t.Num}, nil
    case lexer.TString:
        p.cur.Next()
        return ast.DataItem{IsStr: true, Str: t.Lex}, nil
    }
    var s string
    for !p.cur.Check(lexer.TComma) && !p.cur.Check(lexer.TColon) && !p.cur.IsEOL() {
        s += p.cur.Next().Lex
    }
    return ast.DataItem{IsStr: true, Str: trimSpace(s)}, nil
}

func (p *Parser) parseRead() (ast.Stmt, error) {
    first, err := p.parseLvalue()
    if err != nil {
        return nil, err
    }
    targets := []ast.Lvalue{first}
    for p.cur.Match(lexer.TComma) {
        lv, err := p.parseLvalue()
        if err != nil {
            return nil, err
        }
        targets = append(targets, lv)
    }
    return &ast.ReadStmt{Targets: targets}, nil
}
func (p *Parser) parseRestore() (ast.Stmt, error) {
    s := &ast.RestoreStmt{}
    if p.cur.Check(lexer.TNumber) {
        n := int(p.cur.Next().Num)
        s.Line = &n
    }
    return s, nil
}

func (p *Parser) parseDef() (ast.Stmt, error) {
    if _, err := p.cur.Expect(lexer.TKeyword, "FN"); err != nil {
        return nil, err
    }
    id, err := p.cur.Expect(lexer.TIdent)
    if err != nil {
        return nil, err
    }
    var params []string
    if p.cur.Match(lexer.TLParen) {
        first, err := p.cur.Expect(lexer.TIdent)
        if err != nil {
            return nil, err
        }
        params = append(params, first.Lex)
        for p.cur.Match(lexer.TComma) {
            id, err := p.cur.Expect(lexer.TIdent)
            if err != nil {
                return nil, err
            }
            params = append(params, id.Lex)
        }
        if _, err := p.cur.Expect(lexer.TRParen); err != nil {
            return nil, err
        }
    }
    if _, err := p.cur.Expect(lexer.TOp, "="); err != nil {
        return nil, err
    }
    body, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    return &ast.DefFnStmt{
        Name:   "FN_" + upperASCII(id.Lex),
        Params: params,
        Body:   body,
    }, nil
}

func trimSpace(s string) string {
    i, j := 0, len(s)
    for i < j && (s[i] == ' ' || s[i] == '\t') {
        i++
    }
    for j > i && (s[j-1] == ' ' || s[j-1] == '\t') {
        j--
    }
    return s[i:j]
}
```

### 12.7 그래픽 / 사운드 — 짧은 형태

```go
func (p *Parser) parseCls() (ast.Stmt, error) {
    var mode ast.Expr
    if !p.cur.IsEOL() && !p.cur.Check(lexer.TColon) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        mode = e
    }
    return &ast.ClsStmt{Mode: mode}, nil
}
func (p *Parser) parseScreen() (ast.Stmt, error) {
    e, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    return &ast.ScreenStmt{Mode: e}, nil
}
func (p *Parser) parseColor() (ast.Stmt, error) {
    s := &ast.ColorStmt{}
    if !p.cur.IsEOL() && !p.cur.Check(lexer.TComma) && !p.cur.Check(lexer.TColon) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.FG = e
    }
    if p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.BG = e
    }
    return s, nil
}
func (p *Parser) parseLocate() (ast.Stmt, error) {
    s := &ast.LocateStmt{}
    if !p.cur.Check(lexer.TComma) && !p.cur.IsEOL() {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.Row = e
    }
    if p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.Col = e
    }
    return s, nil
}
func (p *Parser) parsePsetLike(op string) (ast.Stmt, error) {
    coord, err := p.parseCoord()
    if err != nil {
        return nil, err
    }
    var color ast.Expr
    if p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        color = e
    }
    return &ast.PsetStmt{Op: op, Coord: coord, Color: color}, nil
}
func (p *Parser) parseCoord() (ast.Coord, error) {
    isStep := p.cur.Match(lexer.TKeyword, "STEP")
    if _, err := p.cur.Expect(lexer.TLParen); err != nil {
        return ast.Coord{}, err
    }
    x, err := p.parseExpression(0)
    if err != nil {
        return ast.Coord{}, err
    }
    if _, err := p.cur.Expect(lexer.TComma); err != nil {
        return ast.Coord{}, err
    }
    y, err := p.parseExpression(0)
    if err != nil {
        return ast.Coord{}, err
    }
    if _, err := p.cur.Expect(lexer.TRParen); err != nil {
        return ast.Coord{}, err
    }
    return ast.Coord{IsStep: isStep, X: x, Y: y}, nil
}
func (p *Parser) parseLineStmt() (ast.Stmt, error) {
    var from *ast.Coord
    if !p.cur.Check(lexer.TOp, "-") {
        c, err := p.parseCoord()
        if err != nil {
            return nil, err
        }
        from = &c
    }
    if _, err := p.cur.Expect(lexer.TOp, "-"); err != nil {
        return nil, err
    }
    to, err := p.parseCoord()
    if err != nil {
        return nil, err
    }
    s := &ast.LineStmt{From: from, To: to}
    if p.cur.Match(lexer.TComma) {
        if !p.cur.Check(lexer.TComma) {
            e, err := p.parseExpression(0)
            if err != nil {
                return nil, err
            }
            s.Color = e
        }
        if p.cur.Match(lexer.TComma) {
            id, err := p.cur.Expect(lexer.TIdent)
            if err != nil {
                return nil, err
            }
            up := upperASCII(id.Lex)
            if up != "B" && up != "BF" {
                return nil, common.NewError(common.ErrSyntax, "LINE expects B or BF")
            }
            s.Mode = up
        }
    }
    return s, nil
}
func (p *Parser) parseCircle() (ast.Stmt, error) {
    center, err := p.parseCoord()
    if err != nil {
        return nil, err
    }
    if _, err := p.cur.Expect(lexer.TComma); err != nil {
        return nil, err
    }
    radius, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    s := &ast.CircleStmt{Center: center, Radius: radius}
    optional := []*ast.Expr{&s.Color, &s.Start, &s.End}
    for _, slot := range optional {
        if !p.cur.Match(lexer.TComma) {
            return s, nil
        }
        if !p.cur.Check(lexer.TComma) {
            e, err := p.parseExpression(0)
            if err != nil {
                return nil, err
            }
            *slot = e
        }
    }
    if p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.Aspect = e
    }
    return s, nil
}
func (p *Parser) parsePaint() (ast.Stmt, error) {
    pt, err := p.parseCoord()
    if err != nil {
        return nil, err
    }
    s := &ast.PaintStmt{Point: pt}
    if p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.Fill = e
    }
    if p.cur.Match(lexer.TComma) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.Border = e
    }
    return s, nil
}
func (p *Parser) parseSound() (ast.Stmt, error) {
    f, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    if _, err := p.cur.Expect(lexer.TComma); err != nil {
        return nil, err
    }
    d, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    return &ast.SoundStmt{Freq: f, Dur: d}, nil
}
func (p *Parser) parsePlay() (ast.Stmt, error) {
    e, err := p.parseExpression(0)
    if err != nil {
        return nil, err
    }
    return &ast.PlayStmt{MML: e}, nil
}
func (p *Parser) parseRandomize() (ast.Stmt, error) {
    s := &ast.RandomizeStmt{}
    if !p.cur.IsEOL() && !p.cur.Check(lexer.TColon) {
        e, err := p.parseExpression(0)
        if err != nil {
            return nil, err
        }
        s.Seed = e
    }
    return s, nil
}
func (p *Parser) parseSwap() (ast.Stmt, error) {
    a, err := p.parseLvalue()
    if err != nil {
        return nil, err
    }
    if _, err := p.cur.Expect(lexer.TComma); err != nil {
        return nil, err
    }
    b, err := p.parseLvalue()
    if err != nil {
        return nil, err
    }
    return &ast.SwapStmt{A: a, B: b}, nil
}
func (p *Parser) parseList() (ast.Stmt, error) {
    s := &ast.ListStmt{}
    if p.cur.Check(lexer.TNumber) {
        n := int(p.cur.Next().Num)
        s.From = &n
    }
    if p.cur.Match(lexer.TOp, "-") && p.cur.Check(lexer.TNumber) {
        n := int(p.cur.Next().Num)
        s.To = &n
    }
    return s, nil
}
func (p *Parser) parseRemKw() (ast.Stmt, error) {
    s := &ast.RemStmt{}
    if p.cur.Check(lexer.TRemText) {
        s.Text = p.cur.Next().Lex
    }
    return s, nil
}
```

### 12.8 파서 테스트

```go
func TestProgramShape(t *testing.T) {
    src := "10 PRINT \"Hi\"\n20 END"
    toks, _ := lexer.Tokenize(src)
    prog, err := Parse(toks)
    if err != nil {
        t.Fatal(err)
    }
    if len(prog.Lines) != 2 {
        t.Fatalf("got %d lines", len(prog.Lines))
    }
    if *prog.Lines[0].Number != 10 {
        t.Fatalf("first number = %d", *prog.Lines[0].Number)
    }
    if _, ok := prog.Lines[0].Statements[0].(*ast.PrintStmt); !ok {
        t.Fatal("first stmt should be PrintStmt")
    }
}

func TestColonStatements(t *testing.T) {
    toks, _ := lexer.Tokenize("10 A=1 : B=2 : PRINT A+B")
    prog, _ := Parse(toks)
    if len(prog.Lines[0].Statements) != 3 {
        t.Fatalf("got %d stmts", len(prog.Lines[0].Statements))
    }
}
```

---

## 13장. AST 노드 정의 (전체)

Go에서는 sealed interface 대신 **타입 어설션**으로 노드를 분기합니다. `ast.Stmt`/`ast.Expr`는 빈 인터페이스 + 마커 메서드로 정의합니다.

```go
// internal/ast/nodes.go
package ast

type NumKind uint8

const (
    NumInt NumKind = iota
    NumSng
    NumDbl
)

// 마커 인터페이스: 컴파일러가 의도치 않은 타입을 흘려 보내지 못하게 함.
type Stmt interface{ isStmt() }
type Expr interface{ isExpr() }
type Lvalue interface {
    Expr
    isLvalue()
}

// ─── 표현식 ──────────────────────────────────────────────
type NumLit struct {
    Value   float64
    NumType NumKind
}

type StrLit struct {
    Value string
}

type VarRef struct {
    Name string
}

type ArrayRef struct {
    Name    string
    Indices []Expr
}

type FnCall struct {
    Target string
    Args   []Expr
}

type UnaryExpr struct {
    Op      string
    Operand Expr
}

type BinaryExpr struct {
    Op  string
    LHS Expr
    RHS Expr
}

func (*NumLit) isExpr()     {}
func (*StrLit) isExpr()     {}
func (*VarRef) isExpr()     {}
func (*ArrayRef) isExpr()   {}
func (*FnCall) isExpr()     {}
func (*UnaryExpr) isExpr()  {}
func (*BinaryExpr) isExpr() {}

func (*VarRef) isLvalue()   {}
func (*ArrayRef) isLvalue() {}

// ─── 문장 ────────────────────────────────────────────────
type AssignStmt struct {
    Target Lvalue
    Value  Expr
}

type PrintItemKind uint8

const (
    PIPExpr PrintItemKind = iota
    PIPSep
    PIPFunc
    PIPUsing
)

type PrintItem struct {
    Kind PrintItemKind
    Expr Expr   // PIPExpr
    Sep  string // PIPSep ("," 또는 ";")
    Name string // PIPFunc ("TAB" 또는 "SPC")
    Arg  Expr   // PIPFunc
    Fmt  Expr   // PIPUsing
    Args []Expr // PIPUsing
}

type PrintStmt struct {
    Items      []PrintItem
    SuppressNL bool
}

type InputStmt struct {
    Prompt           string
    PromptSep        string // ";" or ","
    Targets          []Lvalue
    SuppressQuestion bool
}

// IF의 then/else 분기. 라인 번호로 점프하면 IsGoto=true,
// 아니면 Stmts에 문장 리스트가 들어감.
type Branch struct {
    IsGoto     bool
    GotoTarget int
    Stmts      []Stmt
}

type IfStmt struct {
    Cond Expr
    Then *Branch
    Else *Branch
}

type ForStmt struct {
    VarName    string
    Start, End Expr
    Step       Expr // nil 가능
}

type NextStmt struct {
    Vars []string
}

type WhileStmt struct{ Cond Expr }
type WendStmt struct{}

type GotoStmt struct{ Target int }
type GosubStmt struct{ Target int }
type ReturnStmt struct{ Target *int }

type OnGotoStmt struct {
    Expr    Expr
    Mode    string // "GOTO" or "GOSUB"
    Targets []int
}

type EndStmt struct{}
type StopStmt struct{}
type RemStmt struct{ Text string }
type RunStmt struct{}
type NewStmt struct{}

type ListStmt struct {
    From, To *int
}

type ClearStmt struct{}
type SwapStmt struct{ A, B Lvalue }
type RandomizeStmt struct{ Seed Expr }

type DimDecl struct {
    Name string
    Dims []Expr
}

type DimStmt struct{ Decls []DimDecl }

type DataItem struct {
    IsStr bool
    Num   float64
    Str   string
}
type DataStmt struct{ Items []DataItem }
type ReadStmt struct{ Targets []Lvalue }
type RestoreStmt struct{ Line *int }

type DefFnStmt struct {
    Name   string
    Params []string
    Body   Expr
}

type Coord struct {
    IsStep bool
    X, Y   Expr
}

type ClsStmt struct{ Mode Expr }
type ScreenStmt struct{ Mode Expr }
type ColorStmt struct{ FG, BG Expr }
type LocateStmt struct{ Row, Col Expr }
type PsetStmt struct {
    Op    string // "PSET" or "PRESET"
    Coord Coord
    Color Expr
}
type LineStmt struct {
    From  *Coord
    To    Coord
    Color Expr
    Mode  string // "" or "B" or "BF"
}
type CircleStmt struct {
    Center                      Coord
    Radius                      Expr
    Color, Start, End, Aspect   Expr
}
type PaintStmt struct {
    Point        Coord
    Fill, Border Expr
}
type SoundStmt struct{ Freq, Dur Expr }
type PlayStmt struct{ MML Expr }
type BeepStmt struct{}
type UnimplementedStmt struct{ Name string }

func (*AssignStmt) isStmt()        {}
func (*PrintStmt) isStmt()         {}
func (*InputStmt) isStmt()         {}
func (*IfStmt) isStmt()            {}
func (*ForStmt) isStmt()           {}
func (*NextStmt) isStmt()          {}
func (*WhileStmt) isStmt()         {}
func (*WendStmt) isStmt()          {}
func (*GotoStmt) isStmt()          {}
func (*GosubStmt) isStmt()         {}
func (*ReturnStmt) isStmt()        {}
func (*OnGotoStmt) isStmt()        {}
func (*EndStmt) isStmt()           {}
func (*StopStmt) isStmt()          {}
func (*RemStmt) isStmt()           {}
func (*RunStmt) isStmt()           {}
func (*NewStmt) isStmt()           {}
func (*ListStmt) isStmt()          {}
func (*ClearStmt) isStmt()         {}
func (*SwapStmt) isStmt()          {}
func (*RandomizeStmt) isStmt()     {}
func (*DimStmt) isStmt()           {}
func (*DataStmt) isStmt()          {}
func (*ReadStmt) isStmt()          {}
func (*RestoreStmt) isStmt()       {}
func (*DefFnStmt) isStmt()         {}
func (*ClsStmt) isStmt()           {}
func (*ScreenStmt) isStmt()        {}
func (*ColorStmt) isStmt()         {}
func (*LocateStmt) isStmt()        {}
func (*PsetStmt) isStmt()          {}
func (*LineStmt) isStmt()          {}
func (*CircleStmt) isStmt()        {}
func (*PaintStmt) isStmt()         {}
func (*SoundStmt) isStmt()         {}
func (*PlayStmt) isStmt()          {}
func (*BeepStmt) isStmt()          {}
func (*UnimplementedStmt) isStmt() {}

// ─── 프로그램 ─────────────────────────────────────────────
type Line struct {
    Number     *int
    Statements []Stmt
    SourceLine int
}

type Program struct {
    Lines []*Line
}
```

### 13.1 분기 처리는 type switch로

Go에는 sealed interface가 없지만, type switch가 동등한 표현력을 제공합니다.

```go
func visitStmt(s ast.Stmt) {
    switch s := s.(type) {
    case *ast.PrintStmt:
        // ...
    case *ast.AssignStmt:
        // ...
    case *ast.IfStmt:
        // ...
    default:
        panic(fmt.Sprintf("unhandled stmt: %T", s))
    }
}
```

> 💡 *exhaustive switch* 강제는 컴파일러가 자동으로 해 주지 않습니다. 새 노드를 추가할 때는 `default: panic`을 붙여 두고 정적 분석 도구(`exhaustive` 린터)로 검사하는 것이 일반적입니다.

### 13.2 AST 시각화 도구

```go
// internal/ast/print.go
package ast

import (
    "fmt"
    "strings"
)

func DumpExpr(e Expr) string {
    switch v := e.(type) {
    case *NumLit:
        return fmt.Sprintf("%g", v.Value)
    case *StrLit:
        return fmt.Sprintf("%q", v.Value)
    case *VarRef:
        return v.Name
    case *ArrayRef:
        parts := make([]string, len(v.Indices))
        for i, x := range v.Indices {
            parts[i] = DumpExpr(x)
        }
        return v.Name + "(" + strings.Join(parts, ",") + ")"
    case *FnCall:
        parts := make([]string, len(v.Args))
        for i, x := range v.Args {
            parts[i] = DumpExpr(x)
        }
        return v.Target + "(" + strings.Join(parts, ",") + ")"
    case *UnaryExpr:
        return "(" + v.Op + " " + DumpExpr(v.Operand) + ")"
    case *BinaryExpr:
        return "(" + DumpExpr(v.LHS) + " " + v.Op + " " + DumpExpr(v.RHS) + ")"
    }
    return "?"
}
```

---

> 3부 끝. 이제 GW-BASIC 소스를 받아 AST로 만드는 *완전한 프론트엔드*를 가졌습니다. 4부에서는 이 AST를 바이트코드로 컴파일하고, Go로 만든 가상 머신에서 실행시킵니다.


---

# 제4부 · 백엔드 (1) — 바이트코드와 컴파일러

## 14장. 바이트코드 명령어 집합 (ISA) 설계

### 14.1 설계 결정

Go 구현에서 옵코드는 **`uint8` 정수 + 부속 페이로드 슬라이스**로 표현합니다. JS/TS의 객체-배열 방식과 달리 Go에서는 다음 네 가지 선택지가 있습니다.

| 방식 | 장점 | 단점 |
|------|------|------|
| `interface{}` 슬라이스 | 단순 | 박싱 비용, 디스패치 느림 |
| 태그 유니온 구조체 | 빠름 | 메모리 낭비 |
| `[]byte` 인코딩 | 매우 빠름 | 디버깅 어려움 |
| **op uint8 + args 별도 슬라이스** | 균형 | — |

본 구현은 **마지막 방식**을 채택합니다. `Op uint8` + 명령별 보조 데이터 풀(상수, 라인 참조, 변수명).

### 14.2 명령어 분류표

| 분류 | 옵코드 | 설명 |
|------|--------|------|
| 스택 | `PUSH`, `POP`, `DUP`, `SWAP_TOP` | 피연산자 스택 |
| 산술 | `ADD`, `SUB`, `MUL`, `DIV`, `IDIV`, `MOD`, `POW`, `NEG` | 이항/단항 산술 |
| 비교 | `EQ`, `NE`, `LT`, `LE`, `GT`, `GE` | -1/0 결과 |
| 논리/비트 | `AND`, `OR`, `XOR`, `NOT` | int16 비트 연산 |
| 변수 | `LOAD`, `STORE`, `LOAD_ARR`, `STORE_ARR`, `DIM` | 환경 접근 |
| 분기 | `JMP`, `JMPF`, `JMPT`, `CALL`, `RET`, `RET_TO` | 제어 흐름 |
| 루프 | `FOR_INIT`, `FOR_NEXT`, `WHILE_TEST`, `WEND` | FOR/WHILE |
| 입출력 | `PRINT_VAL`, `PRINT_SEP`, `PRINT_TAB`, `PRINT_SPC`, `PRINT_USING`, `PRINT_NL`, `INPUT` | 콘솔 |
| 그래픽 | `CLS`, `SCREEN`, `COLOR`, `LOCATE`, `PSET`, `PRESET`, `LINE`, `CIRCLE`, `PAINT` | Host 위임 |
| 사운드 | `SOUND`, `PLAY`, `BEEP` | Host 위임 |
| 함수 | `CALL_BUILTIN`, `CALL_FN`, `DEF_FN` | 내장/사용자 함수 |
| 데이터 | `READ`, `RESTORE` | DATA 풀 |
| 기타 | `RANDOMIZE`, `CLEAR`, `SWAP`, `END`, `STOP`, `HALT` | — |

### 14.3 Go 타입 정의

```go
// internal/vm/op.go
package vm

type Op uint8

const (
    OpHalt Op = iota
    OpEnd
    OpStop

    OpPush
    OpPop
    OpDup
    OpSwapTop

    OpAdd
    OpSub
    OpMul
    OpDiv
    OpIDiv
    OpMod
    OpPow
    OpNeg

    OpEq
    OpNe
    OpLt
    OpLe
    OpGt
    OpGe

    OpAnd
    OpOr
    OpXor
    OpNot

    OpLoad
    OpStore
    OpLoadArr
    OpStoreArr
    OpDim

    OpJmp
    OpJmpF
    OpJmpT
    OpCall
    OpRet
    OpRetTo

    OpForInit
    OpForNext
    OpWhileTest
    OpWend

    OpPrintVal
    OpPrintSep
    OpPrintTab
    OpPrintSpc
    OpPrintUsing
    OpPrintNL
    OpInput

    OpCls
    OpScreen
    OpColor
    OpLocate
    OpPset
    OpPreset
    OpLineDraw
    OpCircle
    OpPaint
    OpSound
    OpPlay
    OpBeep

    OpCallBuiltin
    OpCallFn
    OpRead
    OpRestore

    OpRandomize
    OpClear
    OpSwap
)

// String은 디스어셈블러용.
func (o Op) String() string {
    return opNames[o]
}

var opNames = [...]string{
    OpHalt: "HALT", OpEnd: "END", OpStop: "STOP",
    OpPush: "PUSH", OpPop: "POP", OpDup: "DUP", OpSwapTop: "SWAP_TOP",
    OpAdd: "ADD", OpSub: "SUB", OpMul: "MUL", OpDiv: "DIV",
    OpIDiv: "IDIV", OpMod: "MOD", OpPow: "POW", OpNeg: "NEG",
    OpEq: "EQ", OpNe: "NE", OpLt: "LT", OpLe: "LE",
    OpGt: "GT", OpGe: "GE",
    OpAnd: "AND", OpOr: "OR", OpXor: "XOR", OpNot: "NOT",
    OpLoad: "LOAD", OpStore: "STORE",
    OpLoadArr: "LOAD_ARR", OpStoreArr: "STORE_ARR", OpDim: "DIM",
    OpJmp: "JMP", OpJmpF: "JMPF", OpJmpT: "JMPT",
    OpCall: "CALL", OpRet: "RET", OpRetTo: "RET_TO",
    OpForInit: "FOR_INIT", OpForNext: "FOR_NEXT",
    OpWhileTest: "WHILE_TEST", OpWend: "WEND",
    OpPrintVal: "PRINT_VAL", OpPrintSep: "PRINT_SEP",
    OpPrintTab: "PRINT_TAB", OpPrintSpc: "PRINT_SPC",
    OpPrintUsing: "PRINT_USING", OpPrintNL: "PRINT_NL",
    OpInput: "INPUT",
    OpCls: "CLS", OpScreen: "SCREEN", OpColor: "COLOR", OpLocate: "LOCATE",
    OpPset: "PSET", OpPreset: "PRESET", OpLineDraw: "LINE",
    OpCircle: "CIRCLE", OpPaint: "PAINT",
    OpSound: "SOUND", OpPlay: "PLAY", OpBeep: "BEEP",
    OpCallBuiltin: "CALL_BUILTIN", OpCallFn: "CALL_FN",
    OpRead: "READ", OpRestore: "RESTORE",
    OpRandomize: "RANDOMIZE", OpClear: "CLEAR", OpSwap: "SWAP",
}
```

### 14.4 명령 구조와 보조 풀

```go
// internal/vm/chunk.go
package vm

import "github.com/chobocho/go_gwbasic/internal/runtime"

// Instr은 한 명령. 페이로드는 옵코드별로 의미가 다릅니다.
//   - 즉치 정수 (점프 대상, 인자 개수, 배열 차원 수)
//   - 상수 풀 인덱스 (PUSH의 BasicValue, LOAD의 변수명)
type Instr struct {
    Op   Op
    A    int32 // 첫 번째 인자
    B    int32 // 두 번째 인자
    Mode uint8 // 비트 플래그 (LINE: B/BF, INPUT: suppressQ 등)
}

// Chunk는 컴파일된 프로그램. 코드 + 상수 풀 + 메타데이터.
type Chunk struct {
    Code        []Instr
    Consts      []runtime.Value // PUSH의 즉치값 풀
    Names       []string        // LOAD/STORE/CALL 변수·함수명 풀
    LineMap     map[int]int     // BASIC 라인 번호 → code 인덱스
    DataPool    []runtime.Value // 모든 DATA 항목 평탄화
    DataLineMap map[int]int     // RESTORE n 용
    DefFns      map[string]*FnEntry
    InputDescs  []InputDesc     // INPUT 문 보조
    SwapDescs   []SwapDesc
    LineModes   []LineMode      // LINE/CIRCLE 옵션 비트
}

type FnEntry struct {
    Params []string
    Body   []Instr
}

type InputDesc struct {
    Prompt           string
    PromptSep        string
    Vars             []InputVar
    SuppressQuestion bool
}

type InputVar struct {
    Name    string
    IsArray bool
    NIdx    int
}

type SwapDesc struct {
    A, B InputVar
}

type LineMode struct {
    HasFrom, FromStep, ToStep, HasColor bool
    BMode                               uint8 // 0:none 1:B 2:BF
}
```

> 💡 변수명을 `Names []string` 풀에 한 번만 저장하고, 명령은 인덱스만 들고 있게 하면 캐시 친화적입니다. `runtime.Value`도 마찬가지로 `Consts` 풀에 모읍니다.

### 14.5 디코딩 비용

Go의 `switch op` 디스패치는 컴파일 시 *jump table*로 최적화됩니다(`go tool compile -S`로 확인 가능). 표준 ISA 80여 개 정도의 디스패치는 한 자릿수 ns 수준입니다. 8086 4.77MHz 시절 GW-BASIC 대비 **약 1000배** 빠른 실행 속도를 가능케 합니다.

---

## 15장. AST → 바이트코드 컴파일러

### 15.1 컴파일러 골격

```go
// internal/compiler/compiler.go
package compiler

import (
    "fmt"
    "strings"

    "github.com/chobocho/go_gwbasic/internal/ast"
    "github.com/chobocho/go_gwbasic/internal/common"
    "github.com/chobocho/go_gwbasic/internal/runtime"
    "github.com/chobocho/go_gwbasic/internal/vm"
)

type forFrame struct {
    varIdx       int32 // Names 인덱스
    initOpIdx    int   // FOR_INIT 명령의 위치 (loopEnd patch 대상)
    loopStart    int
}

type whileFrame struct {
    testStart  int
    exitPatch  int
}

type Compiler struct {
    chunk        *vm.Chunk
    constsIndex  map[runtime.Value]int32
    namesIndex   map[string]int32
    unresolved   []unresolvedRef
    forStack     []forFrame
    whileStack   []whileFrame
}

type unresolvedRef struct {
    line   int
    opIdx  int
    field  uint8 // 0: A field
}

func New() *Compiler {
    return &Compiler{
        chunk:       newChunk(),
        constsIndex: map[runtime.Value]int32{},
        namesIndex:  map[string]int32{},
    }
}

func newChunk() *vm.Chunk {
    return &vm.Chunk{
        LineMap:     map[int]int{},
        DataLineMap: map[int]int{},
        DefFns:      map[string]*vm.FnEntry{},
    }
}

func Compile(prog *ast.Program) (*vm.Chunk, error) {
    c := New()
    return c.Compile(prog)
}

func (c *Compiler) Compile(prog *ast.Program) (*vm.Chunk, error) {
    c.collectData(prog)

    for _, line := range prog.Lines {
        if line.Number != nil {
            c.chunk.LineMap[*line.Number] = len(c.chunk.Code)
        }
        for _, s := range line.Statements {
            if err := c.emitStmt(s); err != nil {
                return nil, err
            }
        }
    }
    c.emit(vm.Instr{Op: vm.OpEnd})

    if len(c.forStack) > 0 {
        return nil, common.NewError(common.ErrForWithoutNext, "FOR without NEXT")
    }
    if err := c.resolve(); err != nil {
        return nil, err
    }
    return c.chunk, nil
}

func (c *Compiler) emit(ins vm.Instr) int {
    c.chunk.Code = append(c.chunk.Code, ins)
    return len(c.chunk.Code) - 1
}

func (c *Compiler) constIdx(v runtime.Value) int32 {
    if i, ok := c.constsIndex[v]; ok {
        return i
    }
    i := int32(len(c.chunk.Consts))
    c.chunk.Consts = append(c.chunk.Consts, v)
    c.constsIndex[v] = i
    return i
}

func (c *Compiler) nameIdx(s string) int32 {
    if i, ok := c.namesIndex[s]; ok {
        return i
    }
    i := int32(len(c.chunk.Names))
    c.chunk.Names = append(c.chunk.Names, s)
    c.namesIndex[s] = i
    return i
}

func normName(s string) string { return strings.ToUpper(s) }

func (c *Compiler) collectData(prog *ast.Program) {
    for _, line := range prog.Lines {
        for _, s := range line.Statements {
            d, ok := s.(*ast.DataStmt)
            if !ok {
                continue
            }
            if line.Number != nil {
                if _, exists := c.chunk.DataLineMap[*line.Number]; !exists {
                    c.chunk.DataLineMap[*line.Number] = len(c.chunk.DataPool)
                }
            }
            for _, item := range d.Items {
                if item.IsStr {
                    c.chunk.DataPool = append(c.chunk.DataPool, runtime.StrVal(item.Str))
                } else {
                    c.chunk.DataPool = append(c.chunk.DataPool, runtime.DblVal(item.Num))
                }
            }
        }
    }
}

func (c *Compiler) lineRef(n int, opIdx int) int32 {
    if i, ok := c.chunk.LineMap[n]; ok {
        return int32(i)
    }
    c.unresolved = append(c.unresolved, unresolvedRef{line: n, opIdx: opIdx})
    return -1
}

func (c *Compiler) resolve() error {
    for _, u := range c.unresolved {
        i, ok := c.chunk.LineMap[u.line]
        if !ok {
            return &common.BasicError{
                Code: common.ErrUndefinedLineNumber,
                Msg:  fmt.Sprintf("Undefined line: %d", u.line),
            }
        }
        c.chunk.Code[u.opIdx].A = int32(i)
    }
    return nil
}
```

### 15.2 표현식 컴파일

```go
var binOpMap = map[string]vm.Op{
    "+":   vm.OpAdd,
    "-":   vm.OpSub,
    "*":   vm.OpMul,
    "/":   vm.OpDiv,
    "\\":  vm.OpIDiv,
    "MOD": vm.OpMod,
    "^":   vm.OpPow,
    "=":   vm.OpEq,
    "<>":  vm.OpNe,
    "<":   vm.OpLt,
    "<=":  vm.OpLe,
    ">":   vm.OpGt,
    ">=":  vm.OpGe,
    "AND": vm.OpAnd,
    "OR":  vm.OpOr,
    "XOR": vm.OpXor,
}

func (c *Compiler) emitExpr(e ast.Expr) error {
    switch v := e.(type) {
    case *ast.NumLit:
        var val runtime.Value
        switch v.NumType {
        case ast.NumInt:
            val = runtime.IntVal(int16(v.Value))
        case ast.NumDbl:
            val = runtime.DblVal(v.Value)
        default:
            val = runtime.SngVal(float32(v.Value))
        }
        c.emit(vm.Instr{Op: vm.OpPush, A: c.constIdx(val)})
    case *ast.StrLit:
        c.emit(vm.Instr{Op: vm.OpPush, A: c.constIdx(runtime.StrVal(v.Value))})
    case *ast.VarRef:
        c.emit(vm.Instr{Op: vm.OpLoad, A: c.nameIdx(normName(v.Name))})
    case *ast.ArrayRef:
        for _, idx := range v.Indices {
            if err := c.emitExpr(idx); err != nil {
                return err
            }
        }
        c.emit(vm.Instr{
            Op: vm.OpLoadArr,
            A:  c.nameIdx(normName(v.Name)),
            B:  int32(len(v.Indices)),
        })
    case *ast.UnaryExpr:
        if err := c.emitExpr(v.Operand); err != nil {
            return err
        }
        switch v.Op {
        case "-":
            c.emit(vm.Instr{Op: vm.OpNeg})
        case "+":
            // no-op
        case "NOT":
            c.emit(vm.Instr{Op: vm.OpNot})
        }
    case *ast.BinaryExpr:
        if err := c.emitExpr(v.LHS); err != nil {
            return err
        }
        if err := c.emitExpr(v.RHS); err != nil {
            return err
        }
        op, ok := binOpMap[v.Op]
        if !ok {
            return common.NewError(common.ErrSyntax, "unknown binary op: "+v.Op)
        }
        c.emit(vm.Instr{Op: op})
    case *ast.FnCall:
        for _, a := range v.Args {
            if err := c.emitExpr(a); err != nil {
                return err
            }
        }
        if strings.HasPrefix(v.Target, "FN_") {
            c.emit(vm.Instr{
                Op: vm.OpCallFn,
                A:  c.nameIdx(v.Target),
                B:  int32(len(v.Args)),
            })
        } else {
            c.emit(vm.Instr{
                Op: vm.OpCallBuiltin,
                A:  c.nameIdx(v.Target),
                B:  int32(len(v.Args)),
            })
        }
    default:
        return fmt.Errorf("emitExpr: unhandled %T", e)
    }
    return nil
}
```

### 15.3 문장 컴파일

문장은 종류가 많아 길지만 패턴은 일정합니다. 핵심만 발췌합니다.

```go
func (c *Compiler) emitStmt(s ast.Stmt) error {
    switch v := s.(type) {
    case *ast.RemStmt, *ast.DataStmt:
        return nil // 코드 생성 없음

    case *ast.AssignStmt:
        if err := c.emitExpr(v.Value); err != nil {
            return err
        }
        switch t := v.Target.(type) {
        case *ast.VarRef:
            c.emit(vm.Instr{Op: vm.OpStore, A: c.nameIdx(normName(t.Name))})
        case *ast.ArrayRef:
            for _, idx := range t.Indices {
                if err := c.emitExpr(idx); err != nil {
                    return err
                }
            }
            c.emit(vm.Instr{
                Op: vm.OpStoreArr,
                A:  c.nameIdx(normName(t.Name)),
                B:  int32(len(t.Indices)),
            })
        }
        return nil

    case *ast.PrintStmt:
        return c.emitPrint(v)

    case *ast.IfStmt:
        return c.emitIf(v)

    case *ast.GotoStmt:
        idx := c.emit(vm.Instr{Op: vm.OpJmp})
        c.chunk.Code[idx].A = c.lineRef(v.Target, idx)
        return nil

    case *ast.GosubStmt:
        idx := c.emit(vm.Instr{Op: vm.OpCall})
        c.chunk.Code[idx].A = c.lineRef(v.Target, idx)
        return nil

    case *ast.ReturnStmt:
        if v.Target != nil {
            idx := c.emit(vm.Instr{Op: vm.OpRetTo})
            c.chunk.Code[idx].A = c.lineRef(*v.Target, idx)
        } else {
            c.emit(vm.Instr{Op: vm.OpRet})
        }
        return nil

    case *ast.OnGotoStmt:
        return c.emitOnGoto(v)

    case *ast.ForStmt:
        return c.emitFor(v)

    case *ast.NextStmt:
        return c.emitNext(v)

    case *ast.WhileStmt:
        return c.emitWhile(v)
    case *ast.WendStmt:
        return c.emitWend()

    case *ast.DimStmt:
        for _, d := range v.Decls {
            for _, dim := range d.Dims {
                if err := c.emitExpr(dim); err != nil {
                    return err
                }
            }
            c.emit(vm.Instr{
                Op: vm.OpDim,
                A:  c.nameIdx(normName(d.Name)),
                B:  int32(len(d.Dims)),
            })
        }
        return nil

    case *ast.ReadStmt:
        for _, t := range v.Targets {
            switch lv := t.(type) {
            case *ast.ArrayRef:
                for _, idx := range lv.Indices {
                    if err := c.emitExpr(idx); err != nil {
                        return err
                    }
                }
                c.emit(vm.Instr{
                    Op: vm.OpRead, Mode: 1,
                    A: c.nameIdx(normName(lv.Name)),
                    B: int32(len(lv.Indices)),
                })
            case *ast.VarRef:
                c.emit(vm.Instr{
                    Op: vm.OpRead,
                    A:  c.nameIdx(normName(lv.Name)),
                })
            }
        }
        return nil

    case *ast.RestoreStmt:
        ins := vm.Instr{Op: vm.OpRestore, A: -1}
        if v.Line != nil {
            ins.A = int32(*v.Line)
            ins.Mode = 1
        }
        c.emit(ins)
        return nil

    case *ast.DefFnStmt:
        sub := New()
        if err := sub.emitExpr(v.Body); err != nil {
            return err
        }
        sub.emit(vm.Instr{Op: vm.OpRet})
        // 부 컴파일러의 chunk.Names가 다르면 재매핑이 필요. 단순화를 위해
        // 본문에서 사용하는 이름은 자식 chunk를 그대로 보존.
        c.chunk.DefFns[v.Name] = &vm.FnEntry{
            Params: upperAll(v.Params),
            Body:   sub.chunk.Code,
        }
        // 자식 상수/이름 풀을 부모로 합치는 작업은 16장에서 자세히 다룸.
        return nil

    case *ast.EndStmt:
        c.emit(vm.Instr{Op: vm.OpEnd})
    case *ast.StopStmt:
        c.emit(vm.Instr{Op: vm.OpStop})
    case *ast.RunStmt:
        c.emit(vm.Instr{Op: vm.OpJmp, A: 0})
    case *ast.ClearStmt:
        c.emit(vm.Instr{Op: vm.OpClear})
    case *ast.RandomizeStmt:
        if v.Seed != nil {
            if err := c.emitExpr(v.Seed); err != nil {
                return err
            }
            c.emit(vm.Instr{Op: vm.OpRandomize, Mode: 1})
        } else {
            c.emit(vm.Instr{Op: vm.OpRandomize})
        }

    case *ast.ListStmt, *ast.NewStmt:
        return nil // REPL 명령. 컴파일 단계에서 NOOP

    case *ast.ClsStmt:
        if v.Mode != nil {
            if err := c.emitExpr(v.Mode); err != nil {
                return err
            }
            c.emit(vm.Instr{Op: vm.OpCls, Mode: 1})
        } else {
            c.emit(vm.Instr{Op: vm.OpCls})
        }
    case *ast.ScreenStmt:
        if err := c.emitExpr(v.Mode); err != nil {
            return err
        }
        c.emit(vm.Instr{Op: vm.OpScreen})
    case *ast.ColorStmt:
        return c.emitColor(v)
    case *ast.LocateStmt:
        return c.emitLocate(v)
    case *ast.PsetStmt:
        return c.emitPsetLike(v)
    case *ast.LineStmt:
        return c.emitLine(v)
    case *ast.CircleStmt:
        return c.emitCircle(v)
    case *ast.PaintStmt:
        return c.emitPaint(v)
    case *ast.SoundStmt:
        if err := c.emitExpr(v.Freq); err != nil {
            return err
        }
        if err := c.emitExpr(v.Dur); err != nil {
            return err
        }
        c.emit(vm.Instr{Op: vm.OpSound})
    case *ast.PlayStmt:
        if err := c.emitExpr(v.MML); err != nil {
            return err
        }
        c.emit(vm.Instr{Op: vm.OpPlay})
    case *ast.BeepStmt:
        c.emit(vm.Instr{Op: vm.OpBeep})

    case *ast.UnimplementedStmt:
        return common.NewError(common.ErrSyntax, "Unimplemented: "+v.Name)
    default:
        return fmt.Errorf("compile: unhandled stmt %T", s)
    }
    return nil
}

func upperAll(xs []string) []string {
    out := make([]string, len(xs))
    for i, s := range xs {
        out[i] = normName(s)
    }
    return out
}
```

### 15.4 PRINT, IF, FOR, WHILE 발췌

```go
func (c *Compiler) emitPrint(s *ast.PrintStmt) error {
    for _, item := range s.Items {
        switch item.Kind {
        case ast.PIPExpr:
            if err := c.emitExpr(item.Expr); err != nil {
                return err
            }
            c.emit(vm.Instr{Op: vm.OpPrintVal})
        case ast.PIPSep:
            mode := uint8(0)
            if item.Sep == "," {
                mode = 1
            }
            c.emit(vm.Instr{Op: vm.OpPrintSep, Mode: mode})
        case ast.PIPFunc:
            if err := c.emitExpr(item.Arg); err != nil {
                return err
            }
            if item.Name == "TAB" {
                c.emit(vm.Instr{Op: vm.OpPrintTab})
            } else {
                c.emit(vm.Instr{Op: vm.OpPrintSpc})
            }
        case ast.PIPUsing:
            if err := c.emitExpr(item.Fmt); err != nil {
                return err
            }
            for _, a := range item.Args {
                if err := c.emitExpr(a); err != nil {
                    return err
                }
            }
            c.emit(vm.Instr{Op: vm.OpPrintUsing, A: int32(len(item.Args))})
        }
    }
    if !s.SuppressNL {
        c.emit(vm.Instr{Op: vm.OpPrintNL})
    }
    return nil
}

func (c *Compiler) emitIf(s *ast.IfStmt) error {
    if err := c.emitExpr(s.Cond); err != nil {
        return err
    }
    jToElse := c.emit(vm.Instr{Op: vm.OpJmpF, A: -1})
    if err := c.emitBranch(s.Then); err != nil {
        return err
    }
    jToEnd := c.emit(vm.Instr{Op: vm.OpJmp, A: -1})
    c.chunk.Code[jToElse].A = int32(len(c.chunk.Code))
    if s.Else != nil {
        if err := c.emitBranch(s.Else); err != nil {
            return err
        }
    }
    c.chunk.Code[jToEnd].A = int32(len(c.chunk.Code))
    return nil
}

func (c *Compiler) emitBranch(b *ast.Branch) error {
    if b.IsGoto {
        idx := c.emit(vm.Instr{Op: vm.OpJmp})
        c.chunk.Code[idx].A = c.lineRef(b.GotoTarget, idx)
        return nil
    }
    for _, s := range b.Stmts {
        if err := c.emitStmt(s); err != nil {
            return err
        }
    }
    return nil
}

func (c *Compiler) emitFor(s *ast.ForStmt) error {
    if err := c.emitExpr(s.Start); err != nil {
        return err
    }
    if err := c.emitExpr(s.End); err != nil {
        return err
    }
    if s.Step != nil {
        if err := c.emitExpr(s.Step); err != nil {
            return err
        }
    } else {
        c.emit(vm.Instr{Op: vm.OpPush, A: c.constIdx(runtime.IntVal(1))})
    }
    nameIdx := c.nameIdx(normName(s.VarName))
    initIdx := c.emit(vm.Instr{Op: vm.OpForInit, A: nameIdx, B: -1})
    c.forStack = append(c.forStack, forFrame{
        varIdx:    nameIdx,
        initOpIdx: initIdx,
        loopStart: len(c.chunk.Code),
    })
    return nil
}

func (c *Compiler) emitNext(s *ast.NextStmt) error {
    names := s.Vars
    if len(names) == 0 {
        names = []string{""}
    }
    for _, n := range names {
        if len(c.forStack) == 0 {
            return common.NewError(common.ErrNextWithoutFor, "NEXT without FOR")
        }
        top := c.forStack[len(c.forStack)-1]
        c.forStack = c.forStack[:len(c.forStack)-1]
        if n != "" {
            want := normName(n)
            got := c.chunk.Names[top.varIdx]
            if want != got {
                return common.NewError(common.ErrNextWithoutFor,
                    "NEXT "+want+" doesn't match FOR "+got)
            }
        }
        c.emit(vm.Instr{Op: vm.OpForNext, A: top.varIdx, B: int32(top.loopStart)})
        c.chunk.Code[top.initOpIdx].B = int32(len(c.chunk.Code))
    }
    return nil
}

func (c *Compiler) emitWhile(s *ast.WhileStmt) error {
    testStart := len(c.chunk.Code)
    if err := c.emitExpr(s.Cond); err != nil {
        return err
    }
    exitPatch := c.emit(vm.Instr{Op: vm.OpWhileTest, A: -1})
    c.whileStack = append(c.whileStack, whileFrame{testStart: testStart, exitPatch: exitPatch})
    return nil
}

func (c *Compiler) emitWend() error {
    if len(c.whileStack) == 0 {
        return common.NewError(common.ErrSyntax, "WEND without WHILE")
    }
    top := c.whileStack[len(c.whileStack)-1]
    c.whileStack = c.whileStack[:len(c.whileStack)-1]
    c.emit(vm.Instr{Op: vm.OpWend, A: int32(top.testStart)})
    c.chunk.Code[top.exitPatch].A = int32(len(c.chunk.Code))
    return nil
}
```

### 15.5 그래픽 보조

```go
func (c *Compiler) emitColor(s *ast.ColorStmt) error {
    var mode uint8
    if s.FG != nil {
        if err := c.emitExpr(s.FG); err != nil {
            return err
        }
        mode |= 1
    }
    if s.BG != nil {
        if err := c.emitExpr(s.BG); err != nil {
            return err
        }
        mode |= 2
    }
    c.emit(vm.Instr{Op: vm.OpColor, Mode: mode})
    return nil
}

func (c *Compiler) emitLocate(s *ast.LocateStmt) error {
    var mode uint8
    if s.Row != nil {
        if err := c.emitExpr(s.Row); err != nil {
            return err
        }
        mode |= 1
    }
    if s.Col != nil {
        if err := c.emitExpr(s.Col); err != nil {
            return err
        }
        mode |= 2
    }
    c.emit(vm.Instr{Op: vm.OpLocate, Mode: mode})
    return nil
}

func (c *Compiler) emitPsetLike(s *ast.PsetStmt) error {
    if err := c.emitExpr(s.Coord.X); err != nil {
        return err
    }
    if err := c.emitExpr(s.Coord.Y); err != nil {
        return err
    }
    var mode uint8
    if s.Coord.IsStep {
        mode |= 1
    }
    if s.Color != nil {
        if err := c.emitExpr(s.Color); err != nil {
            return err
        }
        mode |= 2
    }
    op := vm.OpPset
    if s.Op == "PRESET" {
        op = vm.OpPreset
    }
    c.emit(vm.Instr{Op: op, Mode: mode})
    return nil
}

func (c *Compiler) emitLine(s *ast.LineStmt) error {
    var mode uint8
    if s.From != nil {
        if err := c.emitExpr(s.From.X); err != nil {
            return err
        }
        if err := c.emitExpr(s.From.Y); err != nil {
            return err
        }
        mode |= 1
        if s.From.IsStep {
            mode |= 2
        }
    }
    if err := c.emitExpr(s.To.X); err != nil {
        return err
    }
    if err := c.emitExpr(s.To.Y); err != nil {
        return err
    }
    if s.To.IsStep {
        mode |= 4
    }
    if s.Color != nil {
        if err := c.emitExpr(s.Color); err != nil {
            return err
        }
        mode |= 8
    }
    switch s.Mode {
    case "B":
        mode |= 16
    case "BF":
        mode |= 32
    }
    c.emit(vm.Instr{Op: vm.OpLineDraw, Mode: mode})
    return nil
}

func (c *Compiler) emitCircle(s *ast.CircleStmt) error {
    if err := c.emitExpr(s.Center.X); err != nil {
        return err
    }
    if err := c.emitExpr(s.Center.Y); err != nil {
        return err
    }
    if err := c.emitExpr(s.Radius); err != nil {
        return err
    }
    var mode uint8
    if s.Center.IsStep {
        mode |= 1
    }
    optional := []ast.Expr{s.Color, s.Start, s.End, s.Aspect}
    bits := []uint8{2, 4, 8, 16}
    for i, e := range optional {
        if e != nil {
            if err := c.emitExpr(e); err != nil {
                return err
            }
            mode |= bits[i]
        }
    }
    c.emit(vm.Instr{Op: vm.OpCircle, Mode: mode})
    return nil
}

func (c *Compiler) emitPaint(s *ast.PaintStmt) error {
    if err := c.emitExpr(s.Point.X); err != nil {
        return err
    }
    if err := c.emitExpr(s.Point.Y); err != nil {
        return err
    }
    var mode uint8
    if s.Point.IsStep {
        mode |= 1
    }
    if s.Fill != nil {
        if err := c.emitExpr(s.Fill); err != nil {
            return err
        }
        mode |= 2
    }
    if s.Border != nil {
        if err := c.emitExpr(s.Border); err != nil {
            return err
        }
        mode |= 4
    }
    c.emit(vm.Instr{Op: vm.OpPaint, Mode: mode})
    return nil
}
```

### 15.6 ON … GOTO/GOSUB

```go
func (c *Compiler) emitOnGoto(s *ast.OnGotoStmt) error {
    if err := c.emitExpr(s.Expr); err != nil {
        return err
    }
    for i, target := range s.Targets {
        c.emit(vm.Instr{Op: vm.OpDup})
        c.emit(vm.Instr{
            Op: vm.OpPush,
            A:  c.constIdx(runtime.IntVal(int16(i + 1))),
        })
        c.emit(vm.Instr{Op: vm.OpEq})
        jt := c.emit(vm.Instr{Op: vm.OpJmpT, A: -1})
        c.chunk.Code[jt].A = int32(len(c.chunk.Code))
        c.emit(vm.Instr{Op: vm.OpPop})
        idx := c.emit(vm.Instr{Op: vm.OpJmp})
        c.chunk.Code[idx].A = c.lineRef(target, idx)
        if s.Mode == "GOSUB" {
            c.chunk.Code[idx].Op = vm.OpCall
        }
    }
    c.emit(vm.Instr{Op: vm.OpPop})
    return nil
}
```

### 15.7 디스어셈블러

```go
// internal/compiler/disasm.go
package compiler

import (
    "fmt"
    "strings"

    "github.com/chobocho/go_gwbasic/internal/vm"
)

func Disassemble(ch *vm.Chunk) string {
    var b strings.Builder
    rev := map[int]int{}
    for ln, idx := range ch.LineMap {
        rev[idx] = ln
    }
    for i, ins := range ch.Code {
        if ln, ok := rev[i]; ok {
            fmt.Fprintf(&b, "; line %d\n", ln)
        }
        switch ins.Op {
        case vm.OpPush:
            fmt.Fprintf(&b, "%4d: %s %v\n", i, ins.Op, ch.Consts[ins.A])
        case vm.OpLoad, vm.OpStore, vm.OpCallBuiltin, vm.OpCallFn:
            fmt.Fprintf(&b, "%4d: %s %s (%d)\n", i, ins.Op, ch.Names[ins.A], ins.B)
        case vm.OpJmp, vm.OpJmpF, vm.OpJmpT, vm.OpCall, vm.OpRetTo:
            fmt.Fprintf(&b, "%4d: %s →%d\n", i, ins.Op, ins.A)
        default:
            fmt.Fprintf(&b, "%4d: %s a=%d b=%d m=%d\n", i, ins.Op, ins.A, ins.B, ins.Mode)
        }
    }
    return b.String()
}
```

`10 FOR I=1 TO 3 / 20 PRINT I / 30 NEXT I / 40 END` 디스어셈블 결과(개략):

```
; line 10
   0: PUSH 1(int16)
   1: PUSH 3(int16)
   2: PUSH 1(int16)
   3: FOR_INIT a=0 b=8 m=0    ; "I", loopEnd=8
; line 20
   4: LOAD I (0)
   5: PRINT_VAL ...
   6: PRINT_NL ...
; line 30
   7: FOR_NEXT a=0 b=4 m=0    ; "I", loopStart=4
; line 40
   8: END ...
   9: END ...
```

### 15.8 컴파일러 테스트

```go
package compiler

import (
    "testing"

    "github.com/chobocho/go_gwbasic/internal/lexer"
    "github.com/chobocho/go_gwbasic/internal/parser"
    "github.com/chobocho/go_gwbasic/internal/vm"
)

func compileStr(t *testing.T, src string) *vm.Chunk {
    t.Helper()
    toks, err := lexer.Tokenize(src)
    if err != nil {
        t.Fatal(err)
    }
    prog, err := parser.Parse(toks)
    if err != nil {
        t.Fatal(err)
    }
    ch, err := Compile(prog)
    if err != nil {
        t.Fatal(err)
    }
    return ch
}

func TestPrint12(t *testing.T) {
    ch := compileStr(t, "10 PRINT 1+2")
    ops := []vm.Op{}
    for _, ins := range ch.Code {
        ops = append(ops, ins.Op)
    }
    want := []vm.Op{
        vm.OpPush, vm.OpPush, vm.OpAdd,
        vm.OpPrintVal, vm.OpPrintNL,
        vm.OpEnd,
    }
    if len(ops) != len(want) {
        t.Fatalf("op count %d != %d", len(ops), len(want))
    }
    for i := range want {
        if ops[i] != want[i] {
            t.Errorf("op[%d] = %s, want %s", i, ops[i], want[i])
        }
    }
}

func TestForLoopPatch(t *testing.T) {
    ch := compileStr(t, "10 FOR I=1 TO 3\n20 PRINT I\n30 NEXT I")
    var initIdx, nextIdx int = -1, -1
    for i, ins := range ch.Code {
        if ins.Op == vm.OpForInit {
            initIdx = i
        }
        if ins.Op == vm.OpForNext {
            nextIdx = i
        }
    }
    if initIdx < 0 || nextIdx < 0 {
        t.Fatal("missing FOR_INIT/FOR_NEXT")
    }
    if int(ch.Code[initIdx].B) <= initIdx {
        t.Error("FOR_INIT.loopEnd not patched")
    }
    if int(ch.Code[nextIdx].B) >= nextIdx {
        t.Error("FOR_NEXT.loopStart not before NEXT")
    }
}

func TestGotoResolution(t *testing.T) {
    ch := compileStr(t, "10 GOTO 30\n20 PRINT 1\n30 PRINT 2")
    if ch.Code[0].Op != vm.OpJmp {
        t.Fatal("first op should be JMP")
    }
    target := int(ch.Code[0].A)
    if target <= 0 || target >= len(ch.Code) {
        t.Fatalf("JMP target out of range: %d", target)
    }
    if ch.Code[target].Op != vm.OpPush {
        t.Errorf("JMP should land on PUSH (start of PRINT), got %s",
            ch.Code[target].Op)
    }
}
```

`go test ./internal/compiler/...` 로 실행합니다.

---

> 14-15장 끝. 다음 장에서 이 바이트코드를 실행할 VM을 만듭니다.


---

# 제4부 · 백엔드 (2) — 가상 머신과 메모리 모델

## 16장. 스택 기반 가상 머신

### 16.1 VM 자료구조

```go
// internal/vm/vm.go
package vm

import (
    "context"
    "fmt"
    "math"
    "math/rand"
    "strings"

    "github.com/chobocho/go_gwbasic/internal/common"
    "github.com/chobocho/go_gwbasic/internal/host"
    "github.com/chobocho/go_gwbasic/internal/runtime"
)

type VM struct {
    ch      *Chunk
    pc      int
    stack   []runtime.Value
    callStk []int           // GOSUB 복귀 PC
    forStk  []forState
    whileStk []int          // WHILE 시작 PC
    env     *runtime.Env
    rng     *rand.Rand
    host    host.Host
    dataIdx int
    halted  bool
}

type forState struct {
    nameIdx int32
    end     float64
    step    float64
    loopEnd int   // FOR_NEXT가 갈 위치 (NEXT 다음 명령)
    loopBody int  // 루프 본문 시작 PC
}

func New(ch *Chunk, h host.Host) *VM {
    return &VM{
        ch:    ch,
        env:   runtime.NewEnv(),
        rng:   rand.New(rand.NewSource(1)),
        host:  h,
        stack: make([]runtime.Value, 0, 256),
    }
}

func (m *VM) Run(ctx context.Context) error {
    for !m.halted {
        if err := ctx.Err(); err != nil {
            return err
        }
        if m.pc < 0 || m.pc >= len(m.ch.Code) {
            return common.NewError(common.ErrSyntax, "PC out of range")
        }
        ins := m.ch.Code[m.pc]
        m.pc++
        if err := m.step(ctx, ins); err != nil {
            return err
        }
    }
    return nil
}
```

### 16.2 스택 헬퍼

```go
func (m *VM) push(v runtime.Value) { m.stack = append(m.stack, v) }
func (m *VM) pop() runtime.Value {
    n := len(m.stack) - 1
    v := m.stack[n]
    m.stack = m.stack[:n]
    return v
}
func (m *VM) peek(off int) runtime.Value {
    return m.stack[len(m.stack)-1-off]
}
```

### 16.3 디스패치 루프

```go
func (m *VM) step(ctx context.Context, ins Instr) error {
    switch ins.Op {
    case OpPush:
        m.push(m.ch.Consts[ins.A])
    case OpPop:
        m.pop()
    case OpDup:
        m.push(m.peek(0))
    case OpSwapTop:
        n := len(m.stack)
        m.stack[n-1], m.stack[n-2] = m.stack[n-2], m.stack[n-1]

    case OpAdd, OpSub, OpMul, OpDiv, OpIDiv, OpMod, OpPow:
        return m.binArith(ins.Op)

    case OpEq, OpNe, OpLt, OpLe, OpGt, OpGe:
        return m.binCmp(ins.Op)

    case OpAnd, OpOr, OpXor:
        return m.binLogic(ins.Op)

    case OpNeg:
        v := m.pop()
        return m.pushNeg(v)
    case OpNot:
        v := m.pop()
        i, err := runtime.ToInt16(v)
        if err != nil {
            return err
        }
        m.push(runtime.IntVal(^i))

    case OpLoad:
        name := m.ch.Names[ins.A]
        m.push(m.env.Get(name))
    case OpStore:
        name := m.ch.Names[ins.A]
        m.env.Set(name, m.pop())

    case OpLoadArr:
        return m.loadArr(ins)
    case OpStoreArr:
        return m.storeArr(ins)
    case OpDim:
        return m.dim(ins)

    case OpJmp:
        m.pc = int(ins.A)
    case OpJmpF:
        v := m.pop()
        if isFalse(v) {
            m.pc = int(ins.A)
        }
    case OpJmpT:
        v := m.pop()
        if !isFalse(v) {
            m.pc = int(ins.A)
        }
    case OpCall:
        m.callStk = append(m.callStk, m.pc)
        m.pc = int(ins.A)
    case OpRet:
        if len(m.callStk) == 0 {
            return common.NewError(common.ErrReturnWithoutGosub, "RETURN without GOSUB")
        }
        m.pc = m.callStk[len(m.callStk)-1]
        m.callStk = m.callStk[:len(m.callStk)-1]
    case OpRetTo:
        if len(m.callStk) == 0 {
            return common.NewError(common.ErrReturnWithoutGosub, "RETURN without GOSUB")
        }
        m.callStk = m.callStk[:len(m.callStk)-1]
        m.pc = int(ins.A)

    case OpForInit:
        return m.forInit(ins)
    case OpForNext:
        return m.forNext(ins)
    case OpWhileTest:
        v := m.pop()
        if isFalse(v) {
            m.pc = int(ins.A)
        } else {
            m.whileStk = append(m.whileStk, m.pc-1) // WHILE_TEST 자체 위치
        }
    case OpWend:
        m.pc = int(ins.A)

    case OpPrintVal:
        v := m.pop()
        m.host.Print(runtime.PrintFmt(v))
    case OpPrintSep:
        if ins.Mode == 1 { // ","
            m.host.Print(runtime.TabTo(14))
        }
    case OpPrintTab:
        n, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        m.host.Print(runtime.TabTo(int(n)))
    case OpPrintSpc:
        n, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        m.host.Print(strings.Repeat(" ", int(n)))
    case OpPrintNL:
        m.host.Print("\n")
    case OpPrintUsing:
        // 단순화: 17장 PRINT USING 항목에서 자세히
        return m.printUsing(int(ins.A))

    case OpInput:
        return m.execInput(ctx, ins)

    case OpCls:
        m.host.Cls()
        if ins.Mode == 1 {
            m.pop() // 모드값 폐기 (현재 구현은 모드 무시)
        }
    case OpScreen:
        _ = m.pop() // 모드 (host에 위임 가능)
    case OpColor:
        return m.execColor(ins)
    case OpLocate:
        return m.execLocate(ins)
    case OpPset, OpPreset:
        return m.execPset(ins)
    case OpLineDraw:
        return m.execLine(ins)
    case OpCircle:
        return m.execCircle(ins)
    case OpPaint:
        return m.execPaint(ins)
    case OpSound:
        return m.execSound(ins)
    case OpPlay:
        return m.execPlay(ins)
    case OpBeep:
        return m.host.Sound(800, 200)

    case OpCallBuiltin:
        return m.callBuiltin(ins)
    case OpCallFn:
        return m.callUserFn(ins)

    case OpRead:
        return m.execRead(ins)
    case OpRestore:
        return m.execRestore(ins)
    case OpRandomize:
        return m.execRandomize(ins)
    case OpClear:
        m.env.Reset()
        m.stack = m.stack[:0]
    case OpSwap:
        return m.execSwap(ins)

    case OpEnd, OpStop, OpHalt:
        m.halted = true

    default:
        return fmt.Errorf("unknown opcode: %s", ins.Op)
    }
    return nil
}

func isFalse(v runtime.Value) bool {
    switch v.Tag {
    case runtime.TagInt:
        return v.I == 0
    case runtime.TagSng:
        return v.F32 == 0
    case runtime.TagDbl:
        return v.F64 == 0
    case runtime.TagStr:
        return v.S == ""
    }
    return false
}
```

### 16.4 산술 연산

```go
func (m *VM) binArith(op Op) error {
    b := m.pop()
    a := m.pop()
    // 문자열 + 문자열 → 연결
    if a.Tag == runtime.TagStr && b.Tag == runtime.TagStr {
        if op != OpAdd {
            return common.NewError(common.ErrTypeMismatch, "Type mismatch")
        }
        s := a.S + b.S
        if err := runtime.CheckStringLen(s); err != nil {
            return err
        }
        m.push(runtime.StrVal(s))
        return nil
    }
    if a.Tag == runtime.TagStr || b.Tag == runtime.TagStr {
        return common.NewError(common.ErrTypeMismatch, "Type mismatch")
    }

    af := runtime.ToFloat64(a)
    bf := runtime.ToFloat64(b)
    var r float64
    switch op {
    case OpAdd:
        r = af + bf
    case OpSub:
        r = af - bf
    case OpMul:
        r = af * bf
    case OpDiv:
        if bf == 0 {
            return common.NewError(common.ErrDivisionByZero, "Division by zero")
        }
        r = af / bf
    case OpIDiv:
        ai := int64(af)
        bi := int64(bf)
        if bi == 0 {
            return common.NewError(common.ErrDivisionByZero, "Division by zero")
        }
        r = float64(ai / bi)
    case OpMod:
        ai := int64(af)
        bi := int64(bf)
        if bi == 0 {
            return common.NewError(common.ErrDivisionByZero, "Division by zero")
        }
        r = float64(ai % bi)
    case OpPow:
        r = math.Pow(af, bf)
    }
    m.push(promoteNumeric(a, b, r))
    return nil
}

func promoteNumeric(a, b runtime.Value, r float64) runtime.Value {
    // 둘 다 INT면 INT(범위 검사 후), 한쪽 DBL이면 DBL, 아니면 SNG
    if a.Tag == runtime.TagInt && b.Tag == runtime.TagInt {
        if r >= -32768 && r <= 32767 && r == math.Trunc(r) {
            return runtime.IntVal(int16(r))
        }
        return runtime.SngVal(float32(r))
    }
    if a.Tag == runtime.TagDbl || b.Tag == runtime.TagDbl {
        return runtime.DblVal(r)
    }
    return runtime.SngVal(float32(r))
}

func (m *VM) pushNeg(v runtime.Value) error {
    switch v.Tag {
    case runtime.TagInt:
        m.push(runtime.IntVal(-v.I))
    case runtime.TagSng:
        m.push(runtime.SngVal(-v.F32))
    case runtime.TagDbl:
        m.push(runtime.DblVal(-v.F64))
    default:
        return common.NewError(common.ErrTypeMismatch, "Type mismatch")
    }
    return nil
}
```

### 16.5 비교와 논리

```go
func (m *VM) binCmp(op Op) error {
    b := m.pop()
    a := m.pop()
    var lt, eq bool
    if a.Tag == runtime.TagStr && b.Tag == runtime.TagStr {
        lt = a.S < b.S
        eq = a.S == b.S
    } else if a.Tag == runtime.TagStr || b.Tag == runtime.TagStr {
        return common.NewError(common.ErrTypeMismatch, "Type mismatch")
    } else {
        af := runtime.ToFloat64(a)
        bf := runtime.ToFloat64(b)
        lt = af < bf
        eq = af == bf
    }
    var r bool
    switch op {
    case OpEq:
        r = eq
    case OpNe:
        r = !eq
    case OpLt:
        r = lt
    case OpLe:
        r = lt || eq
    case OpGt:
        r = !lt && !eq
    case OpGe:
        r = !lt
    }
    if r {
        m.push(runtime.IntVal(-1))
    } else {
        m.push(runtime.IntVal(0))
    }
    return nil
}

func (m *VM) binLogic(op Op) error {
    b := m.pop()
    a := m.pop()
    ai, err := runtime.ToInt16(a)
    if err != nil {
        return err
    }
    bi, err := runtime.ToInt16(b)
    if err != nil {
        return err
    }
    var r int16
    switch op {
    case OpAnd:
        r = ai & bi
    case OpOr:
        r = ai | bi
    case OpXor:
        r = ai ^ bi
    }
    m.push(runtime.IntVal(r))
    return nil
}
```

### 16.6 배열 명령

```go
func (m *VM) loadArr(ins Instr) error {
    name := m.ch.Names[ins.A]
    n := int(ins.B)
    idx := make([]int, n)
    for i := n - 1; i >= 0; i-- {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        idx[i] = int(v)
    }
    v, err := m.env.GetArray(name, idx)
    if err != nil {
        return err
    }
    m.push(v)
    return nil
}

func (m *VM) storeArr(ins Instr) error {
    name := m.ch.Names[ins.A]
    n := int(ins.B)
    idx := make([]int, n)
    for i := n - 1; i >= 0; i-- {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        idx[i] = int(v)
    }
    val := m.pop()
    return m.env.SetArray(name, idx, val)
}

func (m *VM) dim(ins Instr) error {
    name := m.ch.Names[ins.A]
    n := int(ins.B)
    dims := make([]int, n)
    for i := n - 1; i >= 0; i-- {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        dims[i] = int(v)
    }
    return m.env.Dim(name, dims)
}
```

### 16.7 FOR / NEXT 의미론

GW-BASIC의 FOR는 **미리 종료 검사**를 수행합니다(`step>0 && start>end`이면 본문 한 번도 실행 안 함). step이 음수면 반대.

```go
func (m *VM) forInit(ins Instr) error {
    step := runtime.ToFloat64(m.pop())
    end := runtime.ToFloat64(m.pop())
    start := runtime.ToFloat64(m.pop())
    name := m.ch.Names[ins.A]
    m.env.SetByName(name, runtime.SngVal(float32(start)))

    state := forState{
        nameIdx:  ins.A,
        end:      end,
        step:     step,
        loopEnd:  int(ins.B),
        loopBody: m.pc, // 다음 명령
    }
    // 즉시 종료 검사
    if (step > 0 && start > end) || (step < 0 && start < end) {
        m.pc = state.loopEnd
        return nil
    }
    m.forStk = append(m.forStk, state)
    return nil
}

func (m *VM) forNext(ins Instr) error {
    if len(m.forStk) == 0 {
        return common.NewError(common.ErrNextWithoutFor, "NEXT without FOR")
    }
    top := m.forStk[len(m.forStk)-1]
    name := m.ch.Names[ins.A]
    cur := runtime.ToFloat64(m.env.Get(name))
    cur += top.step
    m.env.SetByName(name, runtime.SngVal(float32(cur)))
    if (top.step > 0 && cur > top.end) || (top.step < 0 && cur < top.end) {
        m.forStk = m.forStk[:len(m.forStk)-1]
        // 그냥 진행 (다음 명령이 NEXT 다음 명령)
        return nil
    }
    m.pc = int(ins.B) // loopStart
    return nil
}
```

> 💡 GW-BASIC은 `var = end + step` 후 종료를 검사합니다. 즉, 루프 종료 후 변수 값은 `end + step`이 되어 있습니다 (테스트 케이스 작성 시 기억해 두세요).

### 16.8 GOSUB / RETURN

`OpCall`은 PC를 콜 스택에 푸시 후 점프, `OpRet`은 콜 스택 톱으로 복귀. `OpRetTo`는 `RETURN n` 형태로, 스택을 한 번 pop하되 PC는 *지정한 라인*으로 점프합니다(현실적으로 거의 쓰이지 않지만 호환을 위해 구현).

### 16.9 INPUT의 비동기성

INPUT은 호스트로부터 줄 입력을 받아야 하므로 *블로킹*이 일어납니다. Go에서는 `context.Context`를 통해 취소 신호를 받을 수 있게 설계합니다.

```go
func (m *VM) execInput(ctx context.Context, ins Instr) error {
    desc := m.ch.InputDescs[ins.A]
    if desc.Prompt != "" {
        m.host.Print(desc.Prompt)
        if desc.PromptSep == ";" && !desc.SuppressQuestion {
            m.host.Print("? ")
        }
    } else if !desc.SuppressQuestion {
        m.host.Print("? ")
    }
    line, err := m.host.InputLine(ctx)
    if err != nil {
        return err
    }
    parts := splitInput(line)
    if len(parts) < len(desc.Vars) {
        return common.NewError(common.ErrIllegalFunctionCall, "Redo from start")
    }
    for i, vd := range desc.Vars {
        v, err := parseInputValue(vd.Name, parts[i])
        if err != nil {
            return err
        }
        m.env.Set(vd.Name, v)
    }
    return nil
}

func splitInput(line string) []string {
    var out []string
    var cur strings.Builder
    inStr := false
    for i := 0; i < len(line); i++ {
        c := line[i]
        switch {
        case c == '"':
            inStr = !inStr
        case c == ',' && !inStr:
            out = append(out, strings.TrimSpace(cur.String()))
            cur.Reset()
        default:
            cur.WriteByte(c)
        }
    }
    out = append(out, strings.TrimSpace(cur.String()))
    return out
}

func parseInputValue(varName, raw string) (runtime.Value, error) {
    if strings.HasSuffix(varName, "$") {
        // 큰따옴표 제거
        s := strings.Trim(raw, `"`)
        return runtime.StrVal(s), nil
    }
    return runtime.ParseNumber(raw)
}
```

### 16.10 그래픽/사운드 디스패치 (요지)

```go
func (m *VM) execColor(ins Instr) error {
    var fg, bg int
    has := func(bit uint8) bool { return ins.Mode&bit != 0 }
    if has(2) {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        bg = int(v)
    }
    if has(1) {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        fg = int(v)
    }
    return m.host.SetColor(fg, bg, ins.Mode)
}

func (m *VM) execLocate(ins Instr) error {
    var row, col int = -1, -1
    if ins.Mode&2 != 0 {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        col = int(v)
    }
    if ins.Mode&1 != 0 {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        row = int(v)
    }
    return m.host.Locate(row, col)
}

func (m *VM) execPset(ins Instr) error {
    color := -1
    if ins.Mode&2 != 0 {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        color = int(v)
    }
    y, err := runtime.ToInt16(m.pop())
    if err != nil {
        return err
    }
    x, err := runtime.ToInt16(m.pop())
    if err != nil {
        return err
    }
    if ins.Op == OpPreset {
        m.host.SetPixel(int(x), int(y), 0)
        return nil
    }
    m.host.SetPixel(int(x), int(y), color)
    return nil
}

func (m *VM) execLine(ins Instr) error {
    color := -1
    if ins.Mode&8 != 0 {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        color = int(v)
    }
    y2, err := runtime.ToInt16(m.pop())
    if err != nil {
        return err
    }
    x2, err := runtime.ToInt16(m.pop())
    if err != nil {
        return err
    }
    var x1, y1 int16
    if ins.Mode&1 != 0 {
        y1, err = runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        x1, err = runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
    }
    box := ins.Mode&16 != 0
    fill := ins.Mode&32 != 0
    if box {
        m.host.DrawBox(int(x1), int(y1), int(x2), int(y2), color, fill)
    } else {
        m.host.DrawLine(int(x1), int(y1), int(x2), int(y2), color)
    }
    return nil
}

func (m *VM) execCircle(ins Instr) error {
    // 인자 순서 (스택 top→bot): aspect, end, start, color, r, y, x
    pop := func() (int16, error) { return runtime.ToInt16(m.pop()) }
    var aspect float64 = 1
    var startA, endA float64 = 0, 2 * math.Pi
    color := -1
    if ins.Mode&16 != 0 {
        v, err := pop()
        if err != nil {
            return err
        }
        aspect = float64(v)
    }
    if ins.Mode&8 != 0 {
        v, err := pop()
        if err != nil {
            return err
        }
        endA = float64(v)
    }
    if ins.Mode&4 != 0 {
        v, err := pop()
        if err != nil {
            return err
        }
        startA = float64(v)
    }
    if ins.Mode&2 != 0 {
        v, err := pop()
        if err != nil {
            return err
        }
        color = int(v)
    }
    r, err := pop()
    if err != nil {
        return err
    }
    y, err := pop()
    if err != nil {
        return err
    }
    x, err := pop()
    if err != nil {
        return err
    }
    m.host.DrawCircle(int(x), int(y), int(r), color, startA, endA, aspect)
    return nil
}

func (m *VM) execPaint(ins Instr) error {
    border := -1
    if ins.Mode&4 != 0 {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        border = int(v)
    }
    fill := -1
    if ins.Mode&2 != 0 {
        v, err := runtime.ToInt16(m.pop())
        if err != nil {
            return err
        }
        fill = int(v)
    }
    y, err := runtime.ToInt16(m.pop())
    if err != nil {
        return err
    }
    x, err := runtime.ToInt16(m.pop())
    if err != nil {
        return err
    }
    m.host.Paint(int(x), int(y), fill, border)
    return nil
}

func (m *VM) execSound(ins Instr) error {
    durTicks, err := runtime.ToInt16(m.pop())
    if err != nil {
        return err
    }
    freq := runtime.ToFloat64(m.pop())
    // GW-BASIC tick = 1/18.2초
    ms := int(float64(durTicks) * 1000 / 18.2)
    return m.host.Sound(freq, ms)
}

func (m *VM) execPlay(ins Instr) error {
    v := m.pop()
    if v.Tag != runtime.TagStr {
        return common.NewError(common.ErrTypeMismatch, "PLAY needs string")
    }
    return m.host.PlayMML(v.S)
}
```

### 16.11 RANDOMIZE / SWAP / READ / RESTORE

```go
func (m *VM) execRandomize(ins Instr) error {
    if ins.Mode == 1 {
        v := m.pop()
        seed := int64(runtime.ToFloat64(v))
        m.rng = rand.New(rand.NewSource(seed))
    } else {
        seed, err := m.host.InputLine(context.Background())
        if err != nil {
            return err
        }
        x, _ := runtime.ParseNumber(seed)
        m.rng = rand.New(rand.NewSource(int64(runtime.ToFloat64(x))))
    }
    return nil
}

func (m *VM) execRead(ins Instr) error {
    if m.dataIdx >= len(m.ch.DataPool) {
        return common.NewError(common.ErrOutOfData, "Out of DATA")
    }
    v := m.ch.DataPool[m.dataIdx]
    m.dataIdx++
    name := m.ch.Names[ins.A]
    if ins.Mode == 1 {
        n := int(ins.B)
        idx := make([]int, n)
        for i := n - 1; i >= 0; i-- {
            x, err := runtime.ToInt16(m.pop())
            if err != nil {
                return err
            }
            idx[i] = int(x)
        }
        return m.env.SetArray(name, idx, runtime.Coerce(v, name))
    }
    m.env.Set(name, runtime.Coerce(v, name))
    return nil
}

func (m *VM) execRestore(ins Instr) error {
    if ins.Mode == 1 {
        line := int(ins.A)
        idx, ok := m.ch.DataLineMap[line]
        if !ok {
            return common.NewError(common.ErrUndefinedLineNumber, "RESTORE: undefined line")
        }
        m.dataIdx = idx
    } else {
        m.dataIdx = 0
    }
    return nil
}

func (m *VM) execSwap(ins Instr) error {
    desc := m.ch.SwapDescs[ins.A]
    a, err := m.env.GetLvalue(desc.A.Name, m.popN(desc.A.NIdx))
    if err != nil {
        return err
    }
    b, err := m.env.GetLvalue(desc.B.Name, m.popN(desc.B.NIdx))
    if err != nil {
        return err
    }
    if !runtime.SameType(a, b) {
        return common.NewError(common.ErrTypeMismatch, "SWAP types differ")
    }
    if err := m.env.SetLvalue(desc.A.Name, nil, b); err != nil {
        return err
    }
    return m.env.SetLvalue(desc.B.Name, nil, a)
}

func (m *VM) popN(n int) []int {
    if n == 0 {
        return nil
    }
    out := make([]int, n)
    for i := n - 1; i >= 0; i-- {
        v, _ := runtime.ToInt16(m.pop())
        out[i] = int(v)
    }
    return out
}
```

### 16.12 사용자 정의 함수 호출

```go
func (m *VM) callUserFn(ins Instr) error {
    name := m.ch.Names[ins.A]
    nargs := int(ins.B)
    fn, ok := m.ch.DefFns[name]
    if !ok {
        return common.NewError(common.ErrSyntax, "undefined FN: "+name)
    }
    if len(fn.Params) != nargs {
        return common.NewError(common.ErrIllegalFunctionCall, "FN arg count mismatch")
    }
    args := make([]runtime.Value, nargs)
    for i := nargs - 1; i >= 0; i-- {
        args[i] = m.pop()
    }
    // 매개변수는 *섀도잉*. 현재 환경의 동명 변수를 잠시 가리고 함수 본문 실행.
    saved := m.env.Snapshot(fn.Params)
    for i, p := range fn.Params {
        m.env.Set(p, args[i])
    }
    sub := &VM{
        ch:    &Chunk{Code: fn.Body, Consts: m.ch.Consts, Names: m.ch.Names},
        env:   m.env,
        rng:   m.rng,
        host:  m.host,
        stack: make([]runtime.Value, 0, 8),
    }
    if err := sub.Run(context.Background()); err != nil {
        return err
    }
    m.env.Restore(saved)
    if len(sub.stack) != 1 {
        return common.NewError(common.ErrIllegalFunctionCall, "FN body did not produce one value")
    }
    m.push(sub.stack[0])
    return nil
}
```

### 16.13 디스패치 성능

`switch ins.Op`는 Go 컴파일러가 *간접 점프 테이블*로 컴파일합니다. 1 GHz CPU 기준 평균 3~5 ns/명령 수준이며, 8086 GW-BASIC 대비 약 1000배 이상 빠른 throughput입니다. 추가 최적화는 31장(테스트/벤치)에서 다룹니다.

### 16.14 VM 통합 테스트

```go
package vm

import (
    "context"
    "strings"
    "testing"

    "github.com/chobocho/go_gwbasic/internal/compiler"
    "github.com/chobocho/go_gwbasic/internal/host"
    "github.com/chobocho/go_gwbasic/internal/lexer"
    "github.com/chobocho/go_gwbasic/internal/parser"
)

type bufHost struct {
    out strings.Builder
    in  []string
    host.NullHost
}

func (b *bufHost) Print(s string) { b.out.WriteString(s) }
func (b *bufHost) InputLine(ctx context.Context) (string, error) {
    if len(b.in) == 0 {
        return "", nil
    }
    s := b.in[0]
    b.in = b.in[1:]
    return s, nil
}

func runSrc(t *testing.T, src string, in ...string) string {
    t.Helper()
    toks, err := lexer.Tokenize(src)
    if err != nil {
        t.Fatal(err)
    }
    prog, err := parser.Parse(toks)
    if err != nil {
        t.Fatal(err)
    }
    ch, err := compiler.Compile(prog)
    if err != nil {
        t.Fatal(err)
    }
    h := &bufHost{in: in}
    m := New(ch, h)
    if err := m.Run(context.Background()); err != nil {
        t.Fatal(err)
    }
    return h.out.String()
}

func TestPrintArith(t *testing.T) {
    got := runSrc(t, "10 PRINT 1+2*3")
    if !strings.Contains(got, "7") {
        t.Errorf("output = %q", got)
    }
}

func TestForLoop(t *testing.T) {
    got := runSrc(t, "10 FOR I=1 TO 3\n20 PRINT I\n30 NEXT I")
    if !strings.Contains(got, "1") || !strings.Contains(got, "2") ||
        !strings.Contains(got, "3") {
        t.Errorf("got %q", got)
    }
}

func TestGosubReturn(t *testing.T) {
    src := strings.Join([]string{
        `10 GOSUB 100`,
        `20 PRINT "AFTER"`,
        `30 END`,
        `100 PRINT "SUB"`,
        `110 RETURN`,
    }, "\n")
    got := runSrc(t, src)
    if !strings.Contains(got, "SUB") || !strings.Contains(got, "AFTER") {
        t.Errorf("got %q", got)
    }
}
```

---

## 17장. 메모리 모델과 값 표현

### 17.1 Value 타입 (재방문)

7장에서 정의한 태그 유니온을 다시 봅니다:

```go
// internal/runtime/value.go
package runtime

import (
    "math"
    "strconv"

    "github.com/chobocho/go_gwbasic/internal/common"
)

type ValueTag uint8

const (
    TagInt ValueTag = iota
    TagSng
    TagDbl
    TagStr
)

type Value struct {
    Tag ValueTag
    I   int16
    F32 float32
    F64 float64
    S   string
}

func IntVal(v int16) Value   { return Value{Tag: TagInt, I: v} }
func SngVal(v float32) Value { return Value{Tag: TagSng, F32: v} }
func DblVal(v float64) Value { return Value{Tag: TagDbl, F64: v} }
func StrVal(v string) Value  { return Value{Tag: TagStr, S: v} }
```

### 17.2 변환 함수

```go
func ToInt16(v Value) (int16, error) {
    switch v.Tag {
    case TagInt:
        return v.I, nil
    case TagSng:
        f := math.Round(float64(v.F32))
        if f < -32768 || f > 32767 {
            return 0, common.NewError(common.ErrOverflow, "Overflow")
        }
        return int16(f), nil
    case TagDbl:
        f := math.Round(v.F64)
        if f < -32768 || f > 32767 {
            return 0, common.NewError(common.ErrOverflow, "Overflow")
        }
        return int16(f), nil
    }
    return 0, common.NewError(common.ErrTypeMismatch, "Type mismatch")
}

func ToFloat64(v Value) float64 {
    switch v.Tag {
    case TagInt:
        return float64(v.I)
    case TagSng:
        return float64(v.F32)
    case TagDbl:
        return v.F64
    }
    return 0
}

func SameType(a, b Value) bool {
    if a.Tag == TagStr || b.Tag == TagStr {
        return a.Tag == b.Tag
    }
    return true // 수치 타입끼리는 SWAP 가능
}

func Coerce(v Value, varName string) Value {
    // 변수명에 접미가 붙어 있으면 그 타입으로 강제 변환
    if len(varName) == 0 {
        return v
    }
    suf := varName[len(varName)-1]
    switch suf {
    case '%':
        if i, err := ToInt16(v); err == nil {
            return IntVal(i)
        }
    case '!':
        return SngVal(float32(ToFloat64(v)))
    case '#':
        return DblVal(ToFloat64(v))
    case '$':
        if v.Tag == TagStr {
            return v
        }
    }
    return v
}

func ParseNumber(s string) (Value, error) {
    f, err := strconv.ParseFloat(s, 64)
    if err != nil {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "bad number: "+s)
    }
    if f == math.Trunc(f) && f >= -32768 && f <= 32767 {
        return IntVal(int16(f)), nil
    }
    return DblVal(f), nil
}
```

### 17.3 PRINT 포맷

```go
import (
    "fmt"
    "strings"
)

// PrintFmt는 `PRINT`가 한 값을 출력할 때의 형식.
// 양수에는 선행 공백, 모든 수치에는 후행 공백 한 칸을 붙입니다.
func PrintFmt(v Value) string {
    switch v.Tag {
    case TagStr:
        return v.S
    case TagInt:
        return numLead(float64(v.I)) + " "
    case TagSng:
        return numLead(float64(v.F32)) + " "
    case TagDbl:
        return numLead(v.F64) + " "
    }
    return ""
}

func numLead(f float64) string {
    s := formatBasicNumber(f)
    if f >= 0 {
        return " " + s
    }
    return s
}

// formatBasicNumber는 GW-BASIC 풍의 수치 표기로 변환.
// 32비트 정밀도 한도 안의 수는 정수처럼, 그 외는 6자리 유효숫자 부동소수.
func formatBasicNumber(f float64) string {
    if f == math.Trunc(f) && f >= -1e15 && f <= 1e15 {
        return strconv.FormatFloat(f, 'f', 0, 64)
    }
    s := strconv.FormatFloat(f, 'g', 7, 32)
    return s
}

// TabTo는 14컬럼 단위 PRINT 콤마 구분자가 만드는 공백.
func TabTo(col int) string {
    // 단순화: 14 단위 패딩만. 실제 호스트는 cursor를 알아서 추적.
    if col <= 0 {
        return ""
    }
    return strings.Repeat(" ", 14)
}
```

---

## 18장. 변수 환경과 스코프

### 18.1 Env 구조

```go
// internal/runtime/env.go
package runtime

import (
    "fmt"
    "strings"

    "github.com/chobocho/go_gwbasic/internal/common"
)

type Env struct {
    scalars map[string]Value
    arrays  map[string]*Array

    // DEFINT/DEFSTR 등의 알파벳 기본 타입
    defType [26]ValueTag
}

type Array struct {
    Name string
    Dims []int
    Data []Value // 평탄화 저장
    Tag  ValueTag
}

func NewEnv() *Env {
    e := &Env{
        scalars: map[string]Value{},
        arrays:  map[string]*Array{},
    }
    for i := range e.defType {
        e.defType[i] = TagSng
    }
    return e
}

func (e *Env) Reset() {
    e.scalars = map[string]Value{}
    e.arrays = map[string]*Array{}
}

func (e *Env) Get(name string) Value {
    if v, ok := e.scalars[name]; ok {
        return v
    }
    return e.zeroFor(name)
}

func (e *Env) Set(name string, v Value) {
    e.scalars[name] = Coerce(v, name)
}

func (e *Env) SetByName(name string, v Value) { e.Set(name, v) }

func (e *Env) zeroFor(name string) Value {
    suf := suffixOf(name)
    switch suf {
    case '%':
        return IntVal(0)
    case '!':
        return SngVal(0)
    case '#':
        return DblVal(0)
    case '$':
        return StrVal("")
    }
    // 첫 글자에 따른 기본 타입
    if len(name) == 0 {
        return SngVal(0)
    }
    c := strings.ToUpper(name)[0]
    if c < 'A' || c > 'Z' {
        return SngVal(0)
    }
    switch e.defType[c-'A'] {
    case TagInt:
        return IntVal(0)
    case TagDbl:
        return DblVal(0)
    case TagStr:
        return StrVal("")
    }
    return SngVal(0)
}

func suffixOf(name string) byte {
    if name == "" {
        return 0
    }
    last := name[len(name)-1]
    switch last {
    case '%', '!', '#', '$':
        return last
    }
    return 0
}
```

### 18.2 배열 관리

```go
func (e *Env) Dim(name string, dims []int) error {
    if _, exists := e.arrays[name]; exists {
        return common.NewError(common.ErrSyntax, "Duplicate definition: "+name)
    }
    total := 1
    for _, d := range dims {
        total *= d + 1 // GW-BASIC: DIM A(10) → 0~10, 11개
    }
    if total <= 0 || total > 1<<24 {
        return common.NewError(common.ErrSubscriptOutOfRange, "Bad DIM size")
    }
    a := &Array{Name: name, Dims: dims, Data: make([]Value, total)}
    a.Tag = e.zeroFor(name).Tag
    zero := e.zeroFor(name)
    for i := range a.Data {
        a.Data[i] = zero
    }
    e.arrays[name] = a
    return nil
}

func (e *Env) GetArray(name string, idx []int) (Value, error) {
    a, ok := e.arrays[name]
    if !ok {
        // 묵시적 DIM (10)을 차원만큼 적용
        d := make([]int, len(idx))
        for i := range d {
            d[i] = 10
        }
        if err := e.Dim(name, d); err != nil {
            return Value{}, err
        }
        a = e.arrays[name]
    }
    flat, err := flatIndex(a, idx)
    if err != nil {
        return Value{}, err
    }
    return a.Data[flat], nil
}

func (e *Env) SetArray(name string, idx []int, v Value) error {
    a, ok := e.arrays[name]
    if !ok {
        d := make([]int, len(idx))
        for i := range d {
            d[i] = 10
        }
        if err := e.Dim(name, d); err != nil {
            return err
        }
        a = e.arrays[name]
    }
    flat, err := flatIndex(a, idx)
    if err != nil {
        return err
    }
    a.Data[flat] = Coerce(v, name)
    return nil
}

func flatIndex(a *Array, idx []int) (int, error) {
    if len(idx) != len(a.Dims) {
        return 0, common.NewError(common.ErrSubscriptOutOfRange,
            fmt.Sprintf("dim mismatch: have %d, got %d", len(a.Dims), len(idx)))
    }
    flat := 0
    stride := 1
    for i := len(a.Dims) - 1; i >= 0; i-- {
        if idx[i] < 0 || idx[i] > a.Dims[i] {
            return 0, common.NewError(common.ErrSubscriptOutOfRange, "Subscript out of range")
        }
        flat += idx[i] * stride
        stride *= a.Dims[i] + 1
    }
    return flat, nil
}
```

### 18.3 LValue / Snapshot (DEF FN 매개변수 섀도잉)

```go
func (e *Env) GetLvalue(name string, idx []int) (Value, error) {
    if len(idx) > 0 {
        return e.GetArray(name, idx)
    }
    return e.Get(name), nil
}

func (e *Env) SetLvalue(name string, idx []int, v Value) error {
    if len(idx) > 0 {
        return e.SetArray(name, idx, v)
    }
    e.Set(name, v)
    return nil
}

// Snapshot/Restore: DEF FN 매개변수의 일시적 섀도잉.
type EnvSnapshot struct {
    saved map[string]Value
}

func (e *Env) Snapshot(names []string) EnvSnapshot {
    s := EnvSnapshot{saved: map[string]Value{}}
    for _, n := range names {
        if v, ok := e.scalars[n]; ok {
            s.saved[n] = v
        } else {
            s.saved[n] = Value{Tag: 255} // sentinel: not previously defined
        }
    }
    return s
}

func (e *Env) Restore(s EnvSnapshot) {
    for n, v := range s.saved {
        if v.Tag == 255 {
            delete(e.scalars, n)
        } else {
            e.scalars[n] = v
        }
    }
}
```

### 18.4 DEFINT / DEFSNG / DEFDBL / DEFSTR

```go
// 컴파일러에서 호출 (또는 VM 진입 직후): 알파벳 범위에 기본 타입을 등록.
func (e *Env) DefRange(tag ValueTag, from, to byte) {
    f := from - 'A'
    t := to - 'A'
    for i := f; i <= t; i++ {
        e.defType[i] = tag
    }
}
```

### 18.5 다음 장 예고

5부에서 PRINT/INPUT, 제어 흐름, 배열, 문자열·수학 함수, DATA/READ, DEF FN의 *런타임* 동작을 자세히 다룹니다. 4부에서 만든 VM이 이들 명령을 호스트와 환경 위에서 어떻게 *실제로* 동작시키는지 코드와 예제로 확인합니다.

---

> 4부 끝.


---

# 제5부 · 런타임 (1) — 입출력과 제어 흐름

## 19장. PRINT와 INPUT — 입출력의 모든 것

### 19.1 PRINT의 의미론

GW-BASIC `PRINT`는 작은 문법 그 자체입니다.

- 인자 사이의 `;` — 공백 없이 이어 붙임
- 인자 사이의 `,` — 다음 14컬럼 탭 정지로 이동
- 마지막에 `;` 또는 `,` — 줄바꿈 억제
- 수치는 양수 앞 한 칸, 모든 수치 뒤 한 칸 공백

### 19.2 Host 인터페이스 (Go)

```go
// internal/host/host.go
package host

import "context"

type Host interface {
    Print(s string)
    InputLine(ctx context.Context) (string, error)

    Cls()
    SetColor(fg, bg int, mode uint8) error
    Locate(row, col int) error
    SetPixel(x, y, color int)
    DrawLine(x1, y1, x2, y2, color int)
    DrawBox(x1, y1, x2, y2, color int, fill bool)
    DrawCircle(x, y, r, color int, startA, endA, aspect float64)
    Paint(x, y, fill, border int)

    Sound(freqHz float64, durationMs int) error
    PlayMML(s string) error

    Now() float64
}

// NullHost는 호스트 인터페이스의 기본 무동작 구현. 그래픽이 없는 환경에서도
// 컴파일 가능하도록 모든 메서드를 빈 동작으로 채워 둡니다.
type NullHost struct{}

func (NullHost) Print(string)                                {}
func (NullHost) InputLine(context.Context) (string, error)   { return "", nil }
func (NullHost) Cls()                                         {}
func (NullHost) SetColor(int, int, uint8) error              { return nil }
func (NullHost) Locate(int, int) error                        { return nil }
func (NullHost) SetPixel(int, int, int)                      {}
func (NullHost) DrawLine(int, int, int, int, int)            {}
func (NullHost) DrawBox(int, int, int, int, int, bool)       {}
func (NullHost) DrawCircle(int, int, int, int, float64, float64, float64) {}
func (NullHost) Paint(int, int, int, int)                    {}
func (NullHost) Sound(float64, int) error                    { return nil }
func (NullHost) PlayMML(string) error                        { return nil }
func (NullHost) Now() float64                                 { return 0 }
```

### 19.3 터미널 호스트 구현

```go
// internal/host/term.go
package host

import (
    "bufio"
    "context"
    "fmt"
    "io"
    "os"
    "time"
)

type TermHost struct {
    NullHost
    out  io.Writer
    in   *bufio.Reader
    col  int // 현재 출력 컬럼 (0-based)
}

func NewTermHost() *TermHost {
    return &TermHost{
        out: os.Stdout,
        in:  bufio.NewReader(os.Stdin),
    }
}

func (h *TermHost) Print(s string) {
    fmt.Fprint(h.out, s)
    for i := 0; i < len(s); i++ {
        if s[i] == '\n' {
            h.col = 0
        } else {
            h.col++
        }
    }
}

func (h *TermHost) InputLine(ctx context.Context) (string, error) {
    type result struct {
        s   string
        err error
    }
    ch := make(chan result, 1)
    go func() {
        s, err := h.in.ReadString('\n')
        ch <- result{s, err}
    }()
    select {
    case <-ctx.Done():
        return "", ctx.Err()
    case r := <-ch:
        return trimNewline(r.s), r.err
    }
}

func (h *TermHost) Cls() {
    fmt.Fprint(h.out, "\x1b[2J\x1b[H")
    h.col = 0
}

func (h *TermHost) Locate(row, col int) error {
    if row < 0 {
        row = 0
    }
    if col < 0 {
        col = 0
    }
    fmt.Fprintf(h.out, "\x1b[%d;%dH", row+1, col+1)
    h.col = col
    return nil
}

func (h *TermHost) SetColor(fg, bg int, mode uint8) error {
    // VT100 16색 매핑
    if mode&1 != 0 && fg >= 0 && fg <= 15 {
        if fg < 8 {
            fmt.Fprintf(h.out, "\x1b[3%dm", fg)
        } else {
            fmt.Fprintf(h.out, "\x1b[9%dm", fg-8)
        }
    }
    if mode&2 != 0 && bg >= 0 && bg <= 15 {
        if bg < 8 {
            fmt.Fprintf(h.out, "\x1b[4%dm", bg)
        } else {
            fmt.Fprintf(h.out, "\x1b[10%dm", bg-8)
        }
    }
    return nil
}

func (h *TermHost) Sound(freqHz float64, durMs int) error {
    // 터미널 환경에서는 BEL만 출력하고 시간 동기 sleep
    fmt.Fprint(h.out, "\a")
    time.Sleep(time.Duration(durMs) * time.Millisecond)
    return nil
}

func (h *TermHost) Now() float64 {
    return float64(time.Now().UnixNano()) / 1e9
}

func trimNewline(s string) string {
    n := len(s)
    if n > 0 && s[n-1] == '\n' {
        n--
    }
    if n > 0 && s[n-1] == '\r' {
        n--
    }
    return s[:n]
}
```

### 19.4 PRINT 콤마의 정확한 의미

콤마는 다음 14컬럼 경계로 점프합니다. 이를 정확히 구현하려면 호스트가 *현재 컬럼*을 알아야 합니다(`TermHost.col`). VM 측에서는 `OpPrintSep`만 호스트에 위임하되, 호스트는 자기 컬럼 카운터를 보고 필요한 만큼 공백을 출력합니다.

```go
func (h *TermHost) PrintComma() {
    // 14의 배수로 다음 정지점 계산
    target := ((h.col / 14) + 1) * 14
    h.Print(strings.Repeat(" ", target-h.col))
}
```

VM 쪽 코드에서 `OpPrintSep, Mode=1`일 때 `h.PrintComma()`를 호출하도록 인터페이스를 확장합니다(또는 `Print(strings.Repeat(" ", n))`로 우회).

### 19.5 PRINT USING

`PRINT USING "###.##"; X` 와 같이 `USING` 형식 문자열을 따라 출력합니다.

| 패턴 | 의미 |
|------|------|
| `#` | 자릿수 (앞 공백 패딩) |
| `.` | 소수점 위치 |
| `+` | 부호 강제 표기 |
| `-` | 음수에만 부호 |
| `^^^^` | 지수 표기 |
| `\ \` | 문자열 N자 (공백 채움) |
| `!` | 첫 글자 한 자 |
| `&` | 전체 문자열 |

```go
// internal/runtime/printusing.go
package runtime

import (
    "fmt"
    "math"
    "strconv"
    "strings"
)

func FormatUsing(fmtStr string, args []Value) (string, error) {
    var out strings.Builder
    i := 0
    argIdx := 0
    for i < len(fmtStr) {
        c := fmtStr[i]
        switch {
        case c == '#' || c == '+' || c == '-' || c == '.':
            // 숫자 형식 슬롯 추출
            slot, n := scanNumericSlot(fmtStr[i:])
            i += n
            if argIdx >= len(args) {
                return "", fmt.Errorf("PRINT USING: not enough args")
            }
            out.WriteString(formatNumericSlot(slot, ToFloat64(args[argIdx])))
            argIdx++
        case c == '\\':
            // 문자열 N자 슬롯
            j := i + 1
            for j < len(fmtStr) && fmtStr[j] == ' ' {
                j++
            }
            if j < len(fmtStr) && fmtStr[j] == '\\' {
                width := j - i + 1
                i = j + 1
                if argIdx >= len(args) {
                    return "", fmt.Errorf("PRINT USING: not enough args")
                }
                s := args[argIdx].S
                if len(s) > width {
                    s = s[:width]
                }
                out.WriteString(s + strings.Repeat(" ", width-len(s)))
                argIdx++
                continue
            }
            out.WriteByte(c)
            i++
        case c == '!':
            i++
            if argIdx >= len(args) {
                return "", fmt.Errorf("PRINT USING: not enough args")
            }
            s := args[argIdx].S
            if s == "" {
                out.WriteByte(' ')
            } else {
                out.WriteByte(s[0])
            }
            argIdx++
        case c == '&':
            i++
            if argIdx >= len(args) {
                return "", fmt.Errorf("PRINT USING: not enough args")
            }
            out.WriteString(args[argIdx].S)
            argIdx++
        default:
            out.WriteByte(c)
            i++
        }
    }
    return out.String(), nil
}

type numericSlot struct {
    intDigits int
    fracDigits int
    forceSign bool
    trailSign bool
}

func scanNumericSlot(s string) (numericSlot, int) {
    var slot numericSlot
    i := 0
    if i < len(s) && s[i] == '+' {
        slot.forceSign = true
        i++
    }
    for i < len(s) && s[i] == '#' {
        slot.intDigits++
        i++
    }
    if i < len(s) && s[i] == '.' {
        i++
        for i < len(s) && s[i] == '#' {
            slot.fracDigits++
            i++
        }
    }
    if i < len(s) && s[i] == '-' {
        slot.trailSign = true
        i++
    }
    return slot, i
}

func formatNumericSlot(s numericSlot, x float64) string {
    width := s.intDigits + s.fracDigits
    if s.fracDigits > 0 {
        width++
    }
    out := strconv.FormatFloat(x, 'f', s.fracDigits, 64)
    if x >= 0 {
        if s.forceSign {
            out = "+" + out
        } else {
            out = " " + out
        }
    }
    if math.Abs(x) >= math.Pow10(s.intDigits) {
        out = "%" + out // overflow 표기
    }
    if len(out) < width {
        out = strings.Repeat(" ", width-len(out)) + out
    }
    return out
}
```

VM의 `OpPrintUsing`은 위 `FormatUsing`을 호출하고 결과를 호스트에 출력합니다.

```go
// VM 쪽 (vm.go)
func (m *VM) printUsing(nargs int) error {
    args := make([]runtime.Value, nargs)
    for i := nargs - 1; i >= 0; i-- {
        args[i] = m.pop()
    }
    fmt := m.pop()
    if fmt.Tag != runtime.TagStr {
        return common.NewError(common.ErrTypeMismatch, "PRINT USING needs string fmt")
    }
    s, err := runtime.FormatUsing(fmt.S, args)
    if err != nil {
        return err
    }
    m.host.Print(s)
    return nil
}
```

### 19.6 INPUT의 동작

`INPUT [;] ["prompt"; or ,] var-list` 의 형태입니다. 줄을 하나 받아 콤마로 자르고 각 변수에 대입. 타입이 안 맞으면 `Redo from start`와 함께 다시 입력 받습니다(본 구현은 단순화하여 한 번만 시도).

`INPUT$(n)` 함수로 *n 글자만* 받는 형태도 있는데(에코 없이), 이는 22장에서 다룹니다.

```go
// 위 16.9 execInput 참고. 추가로 재시도 루프를 두려면:
func (m *VM) execInputLoop(ctx context.Context, ins Instr) error {
    for {
        err := m.execInput(ctx, ins)
        if err == nil {
            return nil
        }
        // Redo from start
        if be, ok := err.(*common.BasicError); ok &&
            be.Code == common.ErrIllegalFunctionCall {
            m.host.Print("?Redo from start\n")
            continue
        }
        return err
    }
}
```

### 19.7 INKEY$ 와 비차단 입력

`INKEY$`는 키 하나를 비차단으로 읽고, 없으면 빈 문자열을 반환합니다. 터미널에서는 raw mode 전환이 필요합니다(stdlib만 쓰면 까다로움).

```go
// internal/host/inkey.go
package host

import (
    "os"

    "golang.org/x/term"
)

// 본 책 전체는 외부 라이브러리를 피한다는 CLAUDE.md 규칙을 따르므로,
// 외부 의존이 필요한 INKEY$는 *옵션 빌드 태그*로 분리합니다.
//   //go:build inkey
// 위 태그가 없으면 빈 문자열을 반환하는 기본 구현을 씁니다.

func (h *TermHost) Inkey() string { return "" }
```

> 💡 외부 의존 없는 순수 Go 구현은 `cmd/gwbasic-tty`에서 raw mode 시스템 콜(`syscall.SetTermios`)을 직접 호출하는 방법이 있지만, 이식성을 위해 본 책에서는 단순한 기본 구현만 둡니다.

---

## 20장. 제어 흐름 — GOTO, IF/THEN/ELSE, FOR/NEXT

### 20.1 GOTO와 라인 맵

15장 컴파일러에서 모든 GOTO/GOSUB는 **이미 코드 오프셋**으로 패치되었습니다. 따라서 VM의 `OpJmp`는 그저 `pc = ins.A` 한 줄입니다.

```go
case OpJmp:
    m.pc = int(ins.A)
```

미해결 라인 번호는 *컴파일 단계*에서 `Undefined line: N` 에러로 잡힙니다. 런타임에는 라인 번호가 존재하지 않습니다(역방향으로 디버거가 라인을 찾을 때만 `LineMap`을 역참조).

### 20.2 IF/THEN/ELSE

15.4의 `emitIf`가 만든 코드는 이렇게 생겼습니다.

```
   eval cond
   JMPF →ELSE
   <then-branch code>
   JMP →END
ELSE:
   <else-branch code>
END:
```

THEN 절이 라인 번호인 경우(`IF X THEN 100`)는 `<then-branch>`가 그저 `JMP 100`이고, 마지막의 `JMP →END`는 *도달 불가*가 됩니다. 컴파일러는 단순화를 위해 그냥 만들어 두지만, 데드 코드 제거 패스를 추가하면 코드 크기가 줄어듭니다.

### 20.3 FOR/NEXT의 구체

```
PUSH start
PUSH end
PUSH step    ; (생략 시 컴파일러가 1을 push)
FOR_INIT name, loopEnd

 ; loop body
LOAD name
... do work
FOR_NEXT name, loopBody
loopEnd:
```

- `FOR_INIT`: 변수에 `start` 대입 + 즉시 종료 검사. 종료 조건이면 `pc = loopEnd`
- `FOR_NEXT`: 변수 += step + 종료 검사. 안 끝나면 `pc = loopBody`

### 20.4 WHILE/WEND

GW-BASIC의 WHILE은 *조건 선검사 루프*입니다.

```
loopStart:
  eval cond
  WHILE_TEST →loopEnd   ; cond false면 점프
  ; body
  WEND →loopStart
loopEnd:
```

### 20.5 ON … GOTO/GOSUB

15.6의 `emitOnGoto`는 풀어 표현했습니다. 1-based 인덱스가 0이거나 범위 초과면 *그냥 통과*하는 동작이 GW-BASIC 공식 동작입니다(에러 X).

### 20.6 무한 루프 보호

악의적이거나 실수로 인한 무한 루프를 다루기 위해 VM은 `context.Context`를 통해 취소를 받습니다. 메인 진입점에서:

```go
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()
m.Run(ctx)
```

또는 사용자 Ctrl-C 시그널을 `signal.Notify`로 받아 `cancel()` 호출.

### 20.7 통합 예제 — `examples/sieve.bas`

소수 체 (에라토스테네스):

```basic
10 N=200
20 DIM A(N)
30 FOR I=2 TO N : A(I)=1 : NEXT I
40 FOR I=2 TO INT(SQR(N))
50  IF A(I)=0 THEN 80
60  FOR J=I*I TO N STEP I : A(J)=0 : NEXT J
80 NEXT I
90 FOR I=2 TO N
100 IF A(I)=1 THEN PRINT I;
110 NEXT I
120 PRINT
130 END
```

이 프로그램이 정상 종료하면 200 이하 모든 소수가 출력됩니다. VM 통합 테스트로 다음을 추가합니다.

```go
func TestSieve200(t *testing.T) {
    src, err := os.ReadFile("../../examples/sieve.bas")
    if err != nil {
        t.Skip(err)
    }
    out := runSrc(t, string(src))
    // 200 이하 소수 검사 — 작은 수 일부만 확인
    for _, p := range []string{"2", "3", "5", "7", "11", "199"} {
        if !strings.Contains(out, p) {
            t.Errorf("missing prime %s in output: %q", p, out)
        }
    }
}
```

---

## 21장. 서브루틴 — GOSUB / RETURN

### 21.1 호출 스택

GW-BASIC은 **서브루틴이 곧 라인 번호**입니다. 매개변수도, 반환값도, 지역 변수도 없습니다. 모든 변수는 전역.

```go
case OpCall:
    m.callStk = append(m.callStk, m.pc)
    m.pc = int(ins.A)
case OpRet:
    if len(m.callStk) == 0 {
        return common.NewError(common.ErrReturnWithoutGosub, "RETURN without GOSUB")
    }
    m.pc = m.callStk[len(m.callStk)-1]
    m.callStk = m.callStk[:len(m.callStk)-1]
```

### 21.2 RETURN n 의 동작

`RETURN 100`은 콜 스택에서 항목 하나를 *버리고* 라인 100으로 점프합니다. 일반적인 함수 호출 의미와 다르므로 주의.

```go
case OpRetTo:
    if len(m.callStk) == 0 {
        return common.NewError(common.ErrReturnWithoutGosub, "RETURN without GOSUB")
    }
    m.callStk = m.callStk[:len(m.callStk)-1]
    m.pc = int(ins.A)
```

### 21.3 ON ... GOSUB와 그 함정

`ON N GOSUB 100, 200, 300`은 N에 따라 분기 후 GOSUB 의미로 호출합니다. 모든 분기에서 `RETURN`이 콜 스택을 정리해야 합니다. 컴파일러는 이미 분기마다 별도의 `OpCall`을 발행하므로 이 부분은 자연스럽게 동작합니다.

### 21.4 재귀 GOSUB

GW-BASIC은 콜 스택 깊이가 일반적으로 *수십 레벨*에 불과합니다(메모리 한계). 본 구현은 Go 슬라이스이므로 사실상 무한 깊이가 가능합니다. 그러나 호환성을 위해 옵션으로 한도를 둡니다.

```go
const MaxCallDepth = 1024

case OpCall:
    if len(m.callStk) >= MaxCallDepth {
        return common.NewError(common.ErrOutOfMemory, "Out of stack space")
    }
    m.callStk = append(m.callStk, m.pc)
    m.pc = int(ins.A)
```

### 21.5 통합 예제 — `examples/gosub_demo.bas`

```basic
10 N=5
20 GOSUB 100
30 PRINT "FACT="; F
40 END
100 F=1
110 FOR I=1 TO N
120 F=F*I
130 NEXT I
140 RETURN
```

테스트:

```go
func TestGosubFactorial(t *testing.T) {
    src, _ := os.ReadFile("../../examples/gosub_demo.bas")
    out := runSrc(t, string(src))
    if !strings.Contains(out, "FACT= 120") {
        t.Errorf("expected FACT= 120, got %q", out)
    }
}
```

---

> 5부 (1) 끝. 다음 장(8부 파일)에서 배열·문자열·수학 함수, DATA/READ/RESTORE, DEF FN을 다룹니다.


---

# 제5부 · 런타임 (2) — 표준 라이브러리

## 22장. 배열 — DIM과 다차원 인덱싱

### 22.1 묵시적 DIM 규칙

GW-BASIC은 첫 사용 시 자동으로 `DIM A(10)`을 적용합니다. 따라서 `A(5) = 1`이 처음 등장해도 동작합니다. 본 구현은 18.2 `Env.GetArray`/`SetArray`에서 이 규칙을 구현했습니다.

차원이 1인 배열은 인덱스 0~10, 총 11개의 칸을 가집니다. 차원 N개 배열은 `(d1+1) × (d2+1) × ... × (dN+1)` 칸.

### 22.2 OPTION BASE

GW-BASIC의 `OPTION BASE 1`은 배열의 시작 인덱스를 0이 아닌 1로 만듭니다. 본 구현에서는 다음과 같이 처리합니다.

```go
// internal/runtime/env.go (확장)
func (e *Env) SetOptionBase(b int) error {
    if b != 0 && b != 1 {
        return common.NewError(common.ErrSyntax, "OPTION BASE must be 0 or 1")
    }
    if len(e.arrays) > 0 {
        return common.NewError(common.ErrSyntax, "OPTION BASE after DIM")
    }
    e.optBase = b
    return nil
}
```

배열 크기 계산을 `dims[i]+1` 대신 `dims[i] - e.optBase + 1`로 수정합니다.

### 22.3 ERASE — 배열 해제

```go
func (e *Env) Erase(name string) error {
    if _, ok := e.arrays[name]; !ok {
        return common.NewError(common.ErrSubscriptOutOfRange, "ERASE: not found")
    }
    delete(e.arrays, name)
    return nil
}
```

### 22.4 다차원 평탄화 검증

```go
func TestArrayFlatten(t *testing.T) {
    e := NewEnv()
    if err := e.Dim("A", []int{3, 4}); err != nil {
        t.Fatal(err)
    }
    if err := e.SetArray("A", []int{2, 3}, IntVal(42)); err != nil {
        t.Fatal(err)
    }
    v, _ := e.GetArray("A", []int{2, 3})
    if v.I != 42 {
        t.Errorf("got %d", v.I)
    }
}
```

---

## 23장. 문자열 함수

### 23.1 LEN, LEFT$, RIGHT$, MID$, INSTR, STR$, VAL, CHR$, ASC, SPACE$, STRING$, HEX$, OCT$

```go
// internal/runtime/strfunc.go
package runtime

import (
    "fmt"
    "math"
    "strconv"
    "strings"

    "github.com/chobocho/go_gwbasic/internal/common"
)

func FnLEN(args []Value) (Value, error) {
    if len(args) != 1 || args[0].Tag != TagStr {
        return Value{}, common.NewError(common.ErrTypeMismatch, "LEN needs string")
    }
    return IntVal(int16(len(args[0].S))), nil
}

func FnLEFT(args []Value) (Value, error) {
    if len(args) != 2 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "LEFT$ needs 2 args")
    }
    if args[0].Tag != TagStr {
        return Value{}, common.NewError(common.ErrTypeMismatch, "")
    }
    n, err := ToInt16(args[1])
    if err != nil {
        return Value{}, err
    }
    s := args[0].S
    if int(n) > len(s) {
        n = int16(len(s))
    }
    if n < 0 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "negative LEFT$")
    }
    return StrVal(s[:n]), nil
}

func FnRIGHT(args []Value) (Value, error) {
    if len(args) != 2 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "RIGHT$ needs 2 args")
    }
    if args[0].Tag != TagStr {
        return Value{}, common.NewError(common.ErrTypeMismatch, "")
    }
    n, err := ToInt16(args[1])
    if err != nil {
        return Value{}, err
    }
    s := args[0].S
    if int(n) > len(s) {
        n = int16(len(s))
    }
    return StrVal(s[len(s)-int(n):]), nil
}

func FnMID(args []Value) (Value, error) {
    if len(args) < 2 || len(args) > 3 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "MID$ needs 2~3 args")
    }
    if args[0].Tag != TagStr {
        return Value{}, common.NewError(common.ErrTypeMismatch, "")
    }
    s := args[0].S
    start, err := ToInt16(args[1])
    if err != nil {
        return Value{}, err
    }
    if start < 1 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "MID$ start<1")
    }
    if int(start) > len(s) {
        return StrVal(""), nil
    }
    n := len(s) - int(start) + 1
    if len(args) == 3 {
        m, err := ToInt16(args[2])
        if err != nil {
            return Value{}, err
        }
        if int(m) < n {
            n = int(m)
        }
    }
    return StrVal(s[start-1 : int(start-1)+n]), nil
}

func FnINSTR(args []Value) (Value, error) {
    var startPos int = 1
    var hay, needle string
    switch len(args) {
    case 2:
        if args[0].Tag != TagStr || args[1].Tag != TagStr {
            return Value{}, common.NewError(common.ErrTypeMismatch, "")
        }
        hay, needle = args[0].S, args[1].S
    case 3:
        sp, err := ToInt16(args[0])
        if err != nil {
            return Value{}, err
        }
        startPos = int(sp)
        if args[1].Tag != TagStr || args[2].Tag != TagStr {
            return Value{}, common.NewError(common.ErrTypeMismatch, "")
        }
        hay, needle = args[1].S, args[2].S
    default:
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "INSTR args")
    }
    if startPos < 1 || startPos > len(hay) {
        return IntVal(0), nil
    }
    idx := strings.Index(hay[startPos-1:], needle)
    if idx < 0 {
        return IntVal(0), nil
    }
    return IntVal(int16(idx + startPos)), nil
}

func FnSTR(args []Value) (Value, error) {
    if len(args) != 1 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "STR$")
    }
    f := ToFloat64(args[0])
    body := formatBasicNumber(f)
    if f >= 0 {
        body = " " + body
    }
    return StrVal(body), nil
}

func FnVAL(args []Value) (Value, error) {
    if len(args) != 1 || args[0].Tag != TagStr {
        return Value{}, common.NewError(common.ErrTypeMismatch, "VAL needs string")
    }
    s := strings.TrimSpace(args[0].S)
    // GW-BASIC: 숫자가 아닌 글자가 나올 때까지 파싱, 못 읽으면 0
    end := 0
    for end < len(s) {
        c := s[end]
        if (c >= '0' && c <= '9') || c == '.' || c == '+' || c == '-' || c == 'E' || c == 'e' {
            end++
            continue
        }
        break
    }
    if end == 0 {
        return SngVal(0), nil
    }
    f, err := strconv.ParseFloat(s[:end], 64)
    if err != nil {
        return SngVal(0), nil
    }
    return SngVal(float32(f)), nil
}

func FnCHR(args []Value) (Value, error) {
    if len(args) != 1 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "CHR$")
    }
    n, err := ToInt16(args[0])
    if err != nil {
        return Value{}, err
    }
    if n < 0 || n > 255 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "CHR$ range")
    }
    return StrVal(string([]byte{byte(n)})), nil
}

func FnASC(args []Value) (Value, error) {
    if len(args) != 1 || args[0].Tag != TagStr {
        return Value{}, common.NewError(common.ErrTypeMismatch, "ASC needs string")
    }
    s := args[0].S
    if s == "" {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "ASC of empty")
    }
    return IntVal(int16(s[0])), nil
}

func FnSPACE(args []Value) (Value, error) {
    n, err := ToInt16(args[0])
    if err != nil {
        return Value{}, err
    }
    if n < 0 || n > 255 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "SPACE$ range")
    }
    return StrVal(strings.Repeat(" ", int(n))), nil
}

func FnSTRING(args []Value) (Value, error) {
    if len(args) != 2 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "STRING$")
    }
    n, err := ToInt16(args[0])
    if err != nil {
        return Value{}, err
    }
    var ch byte
    switch args[1].Tag {
    case TagStr:
        if args[1].S == "" {
            return Value{}, common.NewError(common.ErrIllegalFunctionCall, "STRING$ empty")
        }
        ch = args[1].S[0]
    default:
        v, err := ToInt16(args[1])
        if err != nil {
            return Value{}, err
        }
        ch = byte(v)
    }
    return StrVal(strings.Repeat(string([]byte{ch}), int(n))), nil
}

func FnHEX(args []Value) (Value, error) {
    n, err := ToInt16(args[0])
    if err != nil {
        return Value{}, err
    }
    return StrVal(fmt.Sprintf("%X", uint16(n))), nil
}

func FnOCT(args []Value) (Value, error) {
    n, err := ToInt16(args[0])
    if err != nil {
        return Value{}, err
    }
    return StrVal(strconv.FormatUint(uint64(uint16(n)), 8)), nil
}

// 보조: STR$/PRINT가 공유하는 수치 표기
var _ = math.Floor
```

### 23.2 통합 예제 — `examples/string_demo.bas`

```basic
10 A$ = "Hello, World"
20 PRINT LEN(A$); LEFT$(A$,5); RIGHT$(A$,5); MID$(A$,8,5)
30 PRINT INSTR(A$, "World")
40 PRINT STRING$(5, "*"); SPACE$(3); CHR$(65)
50 END
```

기대 출력 (대략):

```
 12 Hello World World
 8
*****   A
```

---

## 24장. 수학 함수

```go
// internal/runtime/mathfunc.go
package runtime

import (
    "math"
    "math/rand"

    "github.com/chobocho/go_gwbasic/internal/common"
)

func FnABS(args []Value) (Value, error) { return SngVal(float32(math.Abs(ToFloat64(args[0])))), nil }
func FnSGN(args []Value) (Value, error) {
    f := ToFloat64(args[0])
    switch {
    case f > 0:
        return IntVal(1), nil
    case f < 0:
        return IntVal(-1), nil
    }
    return IntVal(0), nil
}
func FnINT(args []Value) (Value, error) {
    return DblVal(math.Floor(ToFloat64(args[0]))), nil
}
func FnFIX(args []Value) (Value, error) {
    return DblVal(math.Trunc(ToFloat64(args[0]))), nil
}
func FnSQR(args []Value) (Value, error) {
    f := ToFloat64(args[0])
    if f < 0 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "SQR negative")
    }
    return DblVal(math.Sqrt(f)), nil
}
func FnSIN(args []Value) (Value, error) { return DblVal(math.Sin(ToFloat64(args[0]))), nil }
func FnCOS(args []Value) (Value, error) { return DblVal(math.Cos(ToFloat64(args[0]))), nil }
func FnTAN(args []Value) (Value, error) { return DblVal(math.Tan(ToFloat64(args[0]))), nil }
func FnATN(args []Value) (Value, error) { return DblVal(math.Atan(ToFloat64(args[0]))), nil }
func FnLOG(args []Value) (Value, error) {
    f := ToFloat64(args[0])
    if f <= 0 {
        return Value{}, common.NewError(common.ErrIllegalFunctionCall, "LOG of non-positive")
    }
    return DblVal(math.Log(f)), nil
}
func FnEXP(args []Value) (Value, error) { return DblVal(math.Exp(ToFloat64(args[0]))), nil }

func FnCINT(args []Value) (Value, error) {
    n, err := ToInt16(args[0])
    if err != nil {
        return Value{}, err
    }
    return IntVal(n), nil
}
func FnCSNG(args []Value) (Value, error) { return SngVal(float32(ToFloat64(args[0]))), nil }
func FnCDBL(args []Value) (Value, error) { return DblVal(ToFloat64(args[0])), nil }

// RND 동작 (GW-BASIC):
//   RND, RND(0) → 마지막에 생성된 난수 반환
//   RND(양수)   → 새 난수
//   RND(음수)   → 시드 재설정
func FnRND(rng *rand.Rand, last *float64, args []Value) (Value, error) {
    if len(args) == 0 {
        v := rng.Float64()
        *last = v
        return SngVal(float32(v)), nil
    }
    f := ToFloat64(args[0])
    if f == 0 {
        return SngVal(float32(*last)), nil
    }
    if f < 0 {
        rng.Seed(int64(f))
    }
    v := rng.Float64()
    *last = v
    return SngVal(float32(v)), nil
}
```

### 24.1 builtin 디스패치

VM의 `OpCallBuiltin`은 함수명으로 위 함수 중 하나를 찾아 호출합니다.

```go
// internal/vm/builtins.go
package vm

import (
    "github.com/chobocho/go_gwbasic/internal/common"
    "github.com/chobocho/go_gwbasic/internal/runtime"
)

type builtinFn func(*VM, []runtime.Value) (runtime.Value, error)

var builtinTable = map[string]builtinFn{
    "ABS":     wrap1(runtime.FnABS),
    "SGN":     wrap1(runtime.FnSGN),
    "INT":     wrap1(runtime.FnINT),
    "FIX":     wrap1(runtime.FnFIX),
    "SQR":     wrap1(runtime.FnSQR),
    "SIN":     wrap1(runtime.FnSIN),
    "COS":     wrap1(runtime.FnCOS),
    "TAN":     wrap1(runtime.FnTAN),
    "ATN":     wrap1(runtime.FnATN),
    "LOG":     wrap1(runtime.FnLOG),
    "EXP":     wrap1(runtime.FnEXP),
    "CINT":    wrap1(runtime.FnCINT),
    "CSNG":    wrap1(runtime.FnCSNG),
    "CDBL":    wrap1(runtime.FnCDBL),
    "LEN":     wrapN(runtime.FnLEN),
    "LEFT$":   wrapN(runtime.FnLEFT),
    "RIGHT$":  wrapN(runtime.FnRIGHT),
    "MID$":    wrapN(runtime.FnMID),
    "INSTR":   wrapN(runtime.FnINSTR),
    "STR$":    wrapN(runtime.FnSTR),
    "VAL":     wrapN(runtime.FnVAL),
    "CHR$":    wrapN(runtime.FnCHR),
    "ASC":     wrapN(runtime.FnASC),
    "SPACE$":  wrapN(runtime.FnSPACE),
    "STRING$": wrapN(runtime.FnSTRING),
    "HEX$":    wrapN(runtime.FnHEX),
    "OCT$":    wrapN(runtime.FnOCT),
    "RND": func(m *VM, a []runtime.Value) (runtime.Value, error) {
        return runtime.FnRND(m.rng, &m.lastRand, a)
    },
    "TIMER": func(m *VM, _ []runtime.Value) (runtime.Value, error) {
        return runtime.SngVal(float32(m.host.Now())), nil
    },
}

func wrap1(f func([]runtime.Value) (runtime.Value, error)) builtinFn {
    return func(m *VM, a []runtime.Value) (runtime.Value, error) {
        if len(a) != 1 {
            return runtime.Value{}, common.NewError(common.ErrIllegalFunctionCall, "1-arg fn")
        }
        return f(a)
    }
}
func wrapN(f func([]runtime.Value) (runtime.Value, error)) builtinFn {
    return func(_ *VM, a []runtime.Value) (runtime.Value, error) {
        return f(a)
    }
}

func (m *VM) callBuiltin(ins Instr) error {
    name := m.ch.Names[ins.A]
    nargs := int(ins.B)
    args := make([]runtime.Value, nargs)
    for i := nargs - 1; i >= 0; i-- {
        args[i] = m.pop()
    }
    fn, ok := builtinTable[name]
    if !ok {
        return common.NewError(common.ErrSyntax, "Undefined builtin: "+name)
    }
    v, err := fn(m, args)
    if err != nil {
        return err
    }
    m.push(v)
    return nil
}
```

VM 구조체에 `lastRand float64` 필드를 추가합니다 (RND 마지막 값 보존용).

### 24.2 통합 예제 — `examples/fib.bas`

```basic
10 N=20
20 A=0 : B=1
30 FOR I=1 TO N
40 PRINT B;
50 T=A+B : A=B : B=T
60 NEXT I
70 PRINT
```

테스트:

```go
func TestFibonacci(t *testing.T) {
    src, _ := os.ReadFile("../../examples/fib.bas")
    out := runSrc(t, string(src))
    // 1, 1, 2, 3, 5, 8, 13, 21, ... 34
    for _, x := range []string{" 1 ", " 2 ", " 3 ", " 5 ", " 8 ", " 13 ", " 21 ", " 34 "} {
        if !strings.Contains(out, x) {
            t.Errorf("missing %q in %q", x, out)
        }
    }
}
```

---

## 25장. DATA / READ / RESTORE

### 25.1 데이터 풀

15.1의 `collectData`는 모든 `DATA` 문을 평탄화하여 `Chunk.DataPool`에 저장하고, 라인 번호별로 시작 인덱스를 `DataLineMap`에 기록합니다.

`READ`는 풀에서 다음 항목을 꺼내 변수에 대입. 변수 타입에 맞춰 강제 변환(`runtime.Coerce`).

`RESTORE` (인자 없음) → 인덱스 = 0.
`RESTORE n` → 인덱스 = `DataLineMap[n]`.

### 25.2 통합 예제 — `examples/data_demo.bas`

```basic
10 FOR I=1 TO 5
20 READ X
30 PRINT X;
40 NEXT I
50 PRINT
60 RESTORE
70 READ A : PRINT "FIRST="; A
80 DATA 10, 20, 30, 40, 50
```

기대 출력:

```
 10  20  30  40  50
FIRST= 10
```

### 25.3 타입 불일치 처리

`READ` 대상이 `A$`인데 풀의 다음 값이 수치면? 본 구현은 `runtime.Coerce`로 가능한 한 변환을 시도하고, 변환 불가면 `Type Mismatch` 에러를 발생시킵니다.

```go
func Coerce(v Value, varName string) Value {
    suf := suffixOf(varName)
    if suf == '$' {
        if v.Tag == TagStr {
            return v
        }
        return StrVal(formatBasicNumber(ToFloat64(v))) // 수치를 문자열로 강제
    }
    if v.Tag == TagStr {
        // 문자열을 수치로 (실패하면 0)
        if x, err := ParseNumber(v.S); err == nil {
            return Coerce(x, varName)
        }
        return SngVal(0)
    }
    switch suf {
    case '%':
        if i, err := ToInt16(v); err == nil {
            return IntVal(i)
        }
    case '!':
        return SngVal(float32(ToFloat64(v)))
    case '#':
        return DblVal(ToFloat64(v))
    }
    return v
}
```

---

## 26장. 사용자 정의 함수 DEF FN

### 26.1 의미

`DEF FN <name>(<params>) = <expression>` 형태. 매개변수는 *값* 으로 전달되며, 본문은 단일 표현식. 호출은 `FN<name>(<args>)`.

### 26.2 컴파일 (요약)

15.3의 `*ast.DefFnStmt` 케이스에서 본문을 별도 컴파일러로 컴파일하여 `Chunk.DefFns[name]`에 저장합니다. 호출 명령은 `OpCallFn`.

⚠️ **중요한 단순화**: 자식 컴파일러는 부모와 다른 `Names`/`Consts` 풀을 갖습니다. 본 책은 다음 두 옵션 중 하나를 권장합니다.

1. 자식 코드의 `OpLoad/OpStore/OpPush`를 부모 풀로 *재매핑*
2. 자식 본문을 컴파일할 때 부모 컴파일러의 `c`를 그대로 재사용해 *동일 풀*에 발행

본 구현은 옵션 2를 택합니다.

```go
func (c *Compiler) compileDefFn(s *ast.DefFnStmt) error {
    // 본문을 부모 코드 영역에 임시로 발행한 뒤 잘라내기
    start := len(c.chunk.Code)
    if err := c.emitExpr(s.Body); err != nil {
        return err
    }
    c.emit(vm.Instr{Op: vm.OpRet})
    body := append([]vm.Instr(nil), c.chunk.Code[start:]...)
    c.chunk.Code = c.chunk.Code[:start]
    c.chunk.DefFns[s.Name] = &vm.FnEntry{
        Params: upperAll(s.Params),
        Body:   body,
    }
    return nil
}
```

이렇게 하면 본문은 부모와 같은 `Consts/Names` 풀을 공유하므로, 16.12의 `callUserFn`이 `Body`만 따로 실행해도 인덱스가 그대로 유효합니다.

### 26.3 매개변수 섀도잉

`callUserFn`은 호출 직전에 동명의 전역 변수를 `env.Snapshot`으로 저장하고, 함수 본문 종료 후 `env.Restore`로 복원합니다 (18.3 참고).

### 26.4 예제

```basic
10 DEF FN SQUARE(X) = X * X
20 DEF FN HYPOT(A,B) = SQR(FN SQUARE(A) + FN SQUARE(B))
30 PRINT FN HYPOT(3, 4)
```

기대 출력: ` 5 `.

```go
func TestDefFnHypot(t *testing.T) {
    src := `10 DEF FN SQUARE(X) = X * X
20 DEF FN HYPOT(A,B) = SQR(FN SQUARE(A) + FN SQUARE(B))
30 PRINT FN HYPOT(3, 4)`
    out := runSrc(t, src)
    if !strings.Contains(out, "5") {
        t.Errorf("got %q", out)
    }
}
```

---

> 5부 끝.


---

# 제6부 · 그래픽과 사운드

## 27장. SCREEN 모드와 그래픽 명령

### 27.1 GW-BASIC 화면 모드 요약

| SCREEN | 해상도 | 색상 | 비고 |
|--------|--------|------|------|
| 0 | 80×25 텍스트 | 16 | 기본 텍스트 |
| 1 | 320×200 | 4 | CGA |
| 2 | 640×200 | 2 | CGA 흑백 |
| 7 | 320×200 | 16 | EGA |
| 8 | 640×200 | 16 | EGA |
| 9 | 640×350 | 16 | EGA |
| 13 | 320×200 | 256 | VGA |

본 구현은 SCREEN 1, 2, 9, 13만 의미 있게 다루고 나머지는 9에 매핑합니다.

### 27.2 추상 그래픽 호스트

19.2의 `Host`에 그래픽 메서드들이 이미 들어 있습니다. 호스트별 구현은 두 가지를 제공합니다.

1. **터미널** — 텍스트 SCREEN 0만 지원, 그래픽 명령은 무시 또는 ASCII 아트로 근사
2. **이미지 출력 호스트** — `image.RGBA`에 그려서 PNG로 저장 (테스트·기록용)
3. **ebiten 호스트** — 게임 윈도우에 실시간 출력 (선택, 빌드 태그 분리)

### 27.3 image.RGBA 호스트 (외부 의존 없음)

```go
// internal/host/imghost.go
package host

import (
    "context"
    "image"
    "image/color"
    "image/png"
    "io"
    "math"
    "os"
)

type ImgHost struct {
    NullHost
    Img    *image.RGBA
    pal    [256]color.RGBA
    fg, bg int
    cursorX, cursorY int
    Path   string
    nowFn  func() float64
}

func NewImgHost(w, h int, path string) *ImgHost {
    img := image.NewRGBA(image.Rect(0, 0, w, h))
    h0 := &ImgHost{
        Img:  img,
        Path: path,
        fg:   15,
        bg:   0,
    }
    h0.setupPalette()
    return h0
}

func (h *ImgHost) setupPalette() {
    // 기본 16색 CGA 팔레트
    base := []color.RGBA{
        {0, 0, 0, 255}, {0, 0, 170, 255}, {0, 170, 0, 255}, {0, 170, 170, 255},
        {170, 0, 0, 255}, {170, 0, 170, 255}, {170, 85, 0, 255}, {170, 170, 170, 255},
        {85, 85, 85, 255}, {85, 85, 255, 255}, {85, 255, 85, 255}, {85, 255, 255, 255},
        {255, 85, 85, 255}, {255, 85, 255, 255}, {255, 255, 85, 255}, {255, 255, 255, 255},
    }
    for i, c := range base {
        h.pal[i] = c
    }
    // 16~255는 검은색
}

func (h *ImgHost) Cls() {
    bg := h.pal[h.bg&0xff]
    for y := 0; y < h.Img.Bounds().Dy(); y++ {
        for x := 0; x < h.Img.Bounds().Dx(); x++ {
            h.Img.SetRGBA(x, y, bg)
        }
    }
}

func (h *ImgHost) SetColor(fg, bg int, mode uint8) error {
    if mode&1 != 0 {
        h.fg = fg
    }
    if mode&2 != 0 {
        h.bg = bg
    }
    return nil
}

func (h *ImgHost) SetPixel(x, y, color int) {
    c := h.fg
    if color >= 0 {
        c = color
    }
    if x < 0 || y < 0 || x >= h.Img.Bounds().Dx() || y >= h.Img.Bounds().Dy() {
        return
    }
    h.Img.SetRGBA(x, y, h.pal[c&0xff])
}

func (h *ImgHost) DrawLine(x1, y1, x2, y2, color int) {
    bresenham(x1, y1, x2, y2, func(x, y int) { h.SetPixel(x, y, color) })
}

func (h *ImgHost) DrawBox(x1, y1, x2, y2, color int, fill bool) {
    if x1 > x2 {
        x1, x2 = x2, x1
    }
    if y1 > y2 {
        y1, y2 = y2, y1
    }
    if fill {
        for y := y1; y <= y2; y++ {
            for x := x1; x <= x2; x++ {
                h.SetPixel(x, y, color)
            }
        }
        return
    }
    h.DrawLine(x1, y1, x2, y1, color)
    h.DrawLine(x2, y1, x2, y2, color)
    h.DrawLine(x2, y2, x1, y2, color)
    h.DrawLine(x1, y2, x1, y1, color)
}

func (h *ImgHost) DrawCircle(cx, cy, r, color int, startA, endA, aspect float64) {
    // 단순화: 원호는 1° 단위로 점을 찍어 표현. aspect는 y 방향 스케일.
    if aspect == 0 {
        aspect = 1
    }
    if endA == 0 {
        endA = 2 * math.Pi
    }
    steps := int(math.Abs(endA-startA) * float64(r) * 2)
    if steps < 32 {
        steps = 32
    }
    for i := 0; i <= steps; i++ {
        a := startA + (endA-startA)*float64(i)/float64(steps)
        x := cx + int(math.Round(float64(r)*math.Cos(a)))
        y := cy + int(math.Round(float64(r)*aspect*math.Sin(a)))
        h.SetPixel(x, y, color)
    }
}

func (h *ImgHost) Paint(x, y, fillColor, borderColor int) {
    // 4-방향 flood fill (스택 기반)
    if x < 0 || y < 0 || x >= h.Img.Bounds().Dx() || y >= h.Img.Bounds().Dy() {
        return
    }
    target := h.Img.RGBAAt(x, y)
    fill := h.pal[fillColor&0xff]
    border := h.pal[borderColor&0xff]
    if target == fill || target == border {
        return
    }
    type pt struct{ x, y int }
    stack := []pt{{x, y}}
    for len(stack) > 0 {
        n := len(stack) - 1
        p := stack[n]
        stack = stack[:n]
        c := h.Img.RGBAAt(p.x, p.y)
        if c != target {
            continue
        }
        h.Img.SetRGBA(p.x, p.y, fill)
        if p.x > 0 {
            stack = append(stack, pt{p.x - 1, p.y})
        }
        if p.y > 0 {
            stack = append(stack, pt{p.x, p.y - 1})
        }
        if p.x < h.Img.Bounds().Dx()-1 {
            stack = append(stack, pt{p.x + 1, p.y})
        }
        if p.y < h.Img.Bounds().Dy()-1 {
            stack = append(stack, pt{p.x, p.y + 1})
        }
    }
}

// Save는 그래픽 출력 결과를 PNG로 저장합니다 (테스트용).
func (h *ImgHost) Save() error {
    f, err := os.Create(h.Path)
    if err != nil {
        return err
    }
    defer f.Close()
    return png.Encode(f, h.Img)
}

// Bresenham line algorithm
func bresenham(x0, y0, x1, y1 int, set func(x, y int)) {
    dx := abs(x1 - x0)
    dy := -abs(y1 - y0)
    sx := -1
    if x0 < x1 {
        sx = 1
    }
    sy := -1
    if y0 < y1 {
        sy = 1
    }
    err := dx + dy
    for {
        set(x0, y0)
        if x0 == x1 && y0 == y1 {
            return
        }
        e2 := 2 * err
        if e2 >= dy {
            err += dy
            x0 += sx
        }
        if e2 <= dx {
            err += dx
            y0 += sy
        }
    }
}

func abs(x int) int {
    if x < 0 {
        return -x
    }
    return x
}

// 인터페이스 부합 확인
var _ Host = (*ImgHost)(nil)

func (h *ImgHost) InputLine(ctx context.Context) (string, error) { return "", nil }
func (h *ImgHost) Print(s string)                                {}
func (h *ImgHost) Sound(float64, int) error                      { return nil }
func (h *ImgHost) PlayMML(string) error                          { return nil }
func (h *ImgHost) Now() float64                                   { return 0 }

var _ io.Closer = (*os.File)(nil) // 사용하지 않는 import 예방
```

### 27.4 그래픽 통합 예제 — `examples/circle_demo.bas`

```basic
10 SCREEN 1
20 CLS
30 FOR I=10 TO 100 STEP 10
40 CIRCLE (160, 100), I, I MOD 4
50 NEXT I
60 LINE (0,0)-(319,199), 3, B
70 END
```

테스트:

```go
func TestImgHostCircles(t *testing.T) {
    h := host.NewImgHost(320, 200, "out.png")
    src, _ := os.ReadFile("../../examples/circle_demo.bas")
    runWithHost(t, string(src), h)
    if err := h.Save(); err != nil {
        t.Fatal(err)
    }
}
```

`out.png`를 열어 직접 눈으로 확인할 수 있습니다.

### 27.5 좌표 시스템과 STEP

`STEP (dx, dy)`는 마지막 그래픽 위치를 기준으로 한 상대 좌표입니다. 본 구현은 `ImgHost`에 `lastX, lastY` 필드를 두고 PSET/LINE/CIRCLE 호출 후 갱신합니다(생략은 독자 과제).

### 27.6 LOCATE와 텍스트 출력

`LOCATE row, col`은 텍스트 커서를 이동시키는 명령입니다. SCREEN 0에서는 흔하지만, 그래픽 모드에서는 8x8 비트맵 폰트를 사용해 `Print`가 픽셀에 글자를 그립니다.

```go
// 8x8 ASCII 폰트는 코드 포인트 0x20~0x7E만 정의 (생략)
var font8x8 [128][8]byte = ...

func (h *ImgHost) PrintAt(x, y int, s string) {
    for i, c := range s {
        glyph := font8x8[c]
        for row := 0; row < 8; row++ {
            for col := 0; col < 8; col++ {
                if glyph[row]&(1<<(7-col)) != 0 {
                    h.SetPixel(x+i*8+col, y+row, h.fg)
                }
            }
        }
    }
}
```

폰트 데이터는 부록 D에 임베드합니다 (`go:embed` 디렉티브 사용 가능).

---

## 28장. 사운드 — SOUND와 PLAY (MML)

### 28.1 SOUND freq, dur

GW-BASIC `SOUND 440, 18`은 440Hz를 약 1초간 재생합니다(18 ticks ≈ 1초). 우리 호스트는 다음과 같이 처리합니다.

- 터미널: BEL + sleep
- ebiten 호스트: PCM 사인 톤을 즉시 합성 후 재생

### 28.2 PCM 합성 (외부 의존 없음)

`go-audio` 등 외부 라이브러리 없이도 표준 라이브러리만으로 WAV 파일을 만들 수 있습니다.

```go
// internal/host/wavhost.go
package host

import (
    "encoding/binary"
    "fmt"
    "math"
    "os"
)

type WavHost struct {
    NullHost
    sampleRate int
    samples    []int16
    Path       string
}

func NewWavHost(path string) *WavHost {
    return &WavHost{
        sampleRate: 44100,
        Path:       path,
    }
}

func (h *WavHost) Sound(freqHz float64, durMs int) error {
    n := h.sampleRate * durMs / 1000
    twoPi := 2.0 * math.Pi
    for i := 0; i < n; i++ {
        s := math.Sin(twoPi * freqHz * float64(i) / float64(h.sampleRate))
        h.samples = append(h.samples, int16(s*16000))
    }
    return nil
}

func (h *WavHost) PlayMML(s string) error {
    notes, err := ParseMML(s)
    if err != nil {
        return err
    }
    for _, n := range notes {
        if err := h.Sound(n.Freq, n.DurMs); err != nil {
            return err
        }
    }
    return nil
}

func (h *WavHost) Save() error {
    f, err := os.Create(h.Path)
    if err != nil {
        return err
    }
    defer f.Close()
    dataLen := len(h.samples) * 2
    write := func(v interface{}) { binary.Write(f, binary.LittleEndian, v) }
    f.Write([]byte("RIFF"))
    write(uint32(36 + dataLen))
    f.Write([]byte("WAVE"))
    f.Write([]byte("fmt "))
    write(uint32(16))           // fmt chunk size
    write(uint16(1))            // PCM
    write(uint16(1))            // mono
    write(uint32(h.sampleRate)) // sample rate
    write(uint32(h.sampleRate * 2))
    write(uint16(2))            // block align
    write(uint16(16))           // bits per sample
    f.Write([]byte("data"))
    write(uint32(dataLen))
    for _, s := range h.samples {
        write(s)
    }
    fmt.Fprintln(os.Stderr, "WAV saved:", h.Path)
    return nil
}
```

### 28.3 MML 파서 (PLAY)

`PLAY "CDEFGAB"`은 도-레-미-파-솔-라-시 한 옥타브를 연주합니다. `O3`은 옥타브 3, `L4`는 4분음표, `T120`은 BPM 120.

```go
// internal/host/mml.go
package host

import (
    "strconv"
    "strings"
    "unicode"
)

type Note struct {
    Freq  float64
    DurMs int
}

func ParseMML(src string) ([]Note, error) {
    src = strings.ToUpper(src)
    var out []Note
    octave := 4
    length := 4
    tempo := 120
    i := 0
    for i < len(src) {
        c := src[i]
        i++
        switch {
        case unicode.IsSpace(rune(c)):
            continue
        case c == 'O':
            n, k := readInt(src[i:])
            octave = n
            i += k
        case c == 'L':
            n, k := readInt(src[i:])
            length = n
            i += k
        case c == 'T':
            n, k := readInt(src[i:])
            tempo = n
            i += k
        case c == '<':
            octave--
        case c == '>':
            octave++
        case c == 'P', c == 'R':
            n, k := readInt(src[i:])
            i += k
            if n == 0 {
                n = length
            }
            out = append(out, Note{Freq: 0, DurMs: noteDurMs(n, tempo)})
        case c >= 'A' && c <= 'G':
            // 음정. 다음에 #, +, - 가 올 수 있고, 길이가 올 수 있음.
            shift := 0
            if i < len(src) && (src[i] == '#' || src[i] == '+') {
                shift = 1
                i++
            } else if i < len(src) && src[i] == '-' {
                shift = -1
                i++
            }
            ln := length
            if i < len(src) && src[i] >= '0' && src[i] <= '9' {
                n, k := readInt(src[i:])
                ln = n
                i += k
            }
            // 점음표
            for i < len(src) && src[i] == '.' {
                ln = ln * 2 / 3
                i++
            }
            freq := noteFreq(c, shift, octave)
            out = append(out, Note{Freq: freq, DurMs: noteDurMs(ln, tempo)})
        }
    }
    return out, nil
}

func readInt(s string) (int, int) {
    i := 0
    for i < len(s) && s[i] >= '0' && s[i] <= '9' {
        i++
    }
    if i == 0 {
        return 0, 0
    }
    n, _ := strconv.Atoi(s[:i])
    return n, i
}

// 노트 → 주파수 (A4 = 440Hz)
var noteSemitone = map[byte]int{
    'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
}

func noteFreq(name byte, shift, octave int) float64 {
    semi := noteSemitone[name] + shift + (octave-4)*12
    // A4 (octave 4, A) → semi = 9 → freq = 440
    return 440.0 * pow2((float64(semi)-9)/12.0)
}

func pow2(x float64) float64 {
    // math.Pow(2, x) 와 동등하지만 명시적 표현
    return mathPow(2, x)
}
```

`mathPow`은 `math.Pow`이며, 별도 정의 대신 `math.Pow`을 직접 호출해도 좋습니다.

### 28.4 통합 예제

```basic
10 PLAY "T120 O4 CDEFGAB > C"
20 SOUND 440, 18
30 SOUND 880, 18
40 BEEP
```

테스트:

```go
func TestPlayScale(t *testing.T) {
    h := host.NewWavHost("scale.wav")
    runWithHost(t, `10 PLAY "T120 O4 CDEFGAB"`, h)
    if err := h.Save(); err != nil {
        t.Fatal(err)
    }
}
```

`scale.wav`을 재생해 음계가 들리는지 확인합니다.

---

> 6부 끝.


---

# 제7부 · 도구와 통합

## 29장. REPL — 즉시 실행 환경

### 29.1 REPL 골격

GW-BASIC의 가장 매력적인 부분 — 라인 번호가 없는 입력은 *즉시 실행*되고, 라인 번호가 있으면 *프로그램에 저장*됩니다.

```go
// internal/repl/repl.go
package repl

import (
    "bufio"
    "context"
    "fmt"
    "io"
    "os"
    "sort"
    "strconv"
    "strings"

    "github.com/chobocho/go_gwbasic/internal/compiler"
    "github.com/chobocho/go_gwbasic/internal/host"
    "github.com/chobocho/go_gwbasic/internal/lexer"
    "github.com/chobocho/go_gwbasic/internal/parser"
    "github.com/chobocho/go_gwbasic/internal/vm"
)

type REPL struct {
    program map[int]string // 라인번호 → 원본 텍스트
    host    host.Host
    in      *bufio.Reader
    out     io.Writer
}

func New(h host.Host) *REPL {
    return &REPL{
        program: map[int]string{},
        host:    h,
        in:      bufio.NewReader(os.Stdin),
        out:     os.Stdout,
    }
}

func (r *REPL) Loop(ctx context.Context) error {
    fmt.Fprintln(r.out, "GW-BASIC (Go port). Type HELP for help, BYE to quit.")
    for {
        fmt.Fprint(r.out, "Ok\n")
        line, err := r.in.ReadString('\n')
        if err == io.EOF {
            return nil
        }
        if err != nil {
            return err
        }
        line = strings.TrimRight(line, "\r\n")
        if line == "" {
            continue
        }
        switch strings.ToUpper(strings.TrimSpace(line)) {
        case "BYE", "SYSTEM", "QUIT":
            return nil
        case "LIST":
            r.list()
            continue
        case "NEW":
            r.program = map[int]string{}
            continue
        case "RUN":
            if err := r.run(ctx); err != nil {
                fmt.Fprintf(r.out, "%v\n", err)
            }
            continue
        case "HELP":
            fmt.Fprintln(r.out, "Commands: LIST, NEW, RUN, BYE")
            continue
        }
        // 라인 번호로 시작하면 프로그램에 저장, 아니면 즉시 실행
        if n, body, ok := splitLineNumber(line); ok {
            if body == "" {
                delete(r.program, n)
            } else {
                r.program[n] = body
            }
            continue
        }
        if err := r.runImmediate(ctx, line); err != nil {
            fmt.Fprintf(r.out, "%v\n", err)
        }
    }
}

func splitLineNumber(s string) (int, string, bool) {
    s = strings.TrimLeft(s, " \t")
    i := 0
    for i < len(s) && s[i] >= '0' && s[i] <= '9' {
        i++
    }
    if i == 0 {
        return 0, "", false
    }
    n, _ := strconv.Atoi(s[:i])
    rest := strings.TrimLeft(s[i:], " \t")
    return n, rest, true
}

func (r *REPL) list() {
    keys := make([]int, 0, len(r.program))
    for k := range r.program {
        keys = append(keys, k)
    }
    sort.Ints(keys)
    for _, k := range keys {
        fmt.Fprintf(r.out, "%d %s\n", k, r.program[k])
    }
}

func (r *REPL) run(ctx context.Context) error {
    src := r.assemble()
    return r.execute(ctx, src)
}

func (r *REPL) runImmediate(ctx context.Context, line string) error {
    return r.execute(ctx, line)
}

func (r *REPL) assemble() string {
    keys := make([]int, 0, len(r.program))
    for k := range r.program {
        keys = append(keys, k)
    }
    sort.Ints(keys)
    var b strings.Builder
    for _, k := range keys {
        fmt.Fprintf(&b, "%d %s\n", k, r.program[k])
    }
    return b.String()
}

func (r *REPL) execute(ctx context.Context, src string) error {
    toks, err := lexer.Tokenize(src)
    if err != nil {
        return err
    }
    prog, err := parser.Parse(toks)
    if err != nil {
        return err
    }
    ch, err := compiler.Compile(prog)
    if err != nil {
        return err
    }
    m := vm.New(ch, r.host)
    return m.Run(ctx)
}
```

### 29.2 진입점

```go
// cmd/gwbasic/main.go
package main

import (
    "context"
    "flag"
    "fmt"
    "os"
    "os/signal"

    "github.com/chobocho/go_gwbasic/internal/host"
    "github.com/chobocho/go_gwbasic/internal/repl"
    "github.com/chobocho/go_gwbasic/internal/runner"
)

func main() {
    runFile := flag.String("run", "", "run a .bas file and exit")
    flag.Parse()

    ctx, cancel := context.WithCancel(context.Background())
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, os.Interrupt)
    go func() {
        <-sigCh
        cancel()
    }()
    defer cancel()

    h := host.NewTermHost()

    if *runFile != "" {
        if err := runner.RunFile(ctx, *runFile, h); err != nil {
            fmt.Fprintln(os.Stderr, err)
            os.Exit(1)
        }
        return
    }
    if err := repl.New(h).Loop(ctx); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}
```

```go
// internal/runner/runner.go
package runner

import (
    "context"
    "os"

    "github.com/chobocho/go_gwbasic/internal/compiler"
    "github.com/chobocho/go_gwbasic/internal/host"
    "github.com/chobocho/go_gwbasic/internal/lexer"
    "github.com/chobocho/go_gwbasic/internal/parser"
    "github.com/chobocho/go_gwbasic/internal/vm"
)

func RunFile(ctx context.Context, path string, h host.Host) error {
    src, err := os.ReadFile(path)
    if err != nil {
        return err
    }
    toks, err := lexer.Tokenize(string(src))
    if err != nil {
        return err
    }
    prog, err := parser.Parse(toks)
    if err != nil {
        return err
    }
    ch, err := compiler.Compile(prog)
    if err != nil {
        return err
    }
    return vm.New(ch, h).Run(ctx)
}
```

빌드:

```bash
go build -o gwbasic ./cmd/gwbasic
./gwbasic -run examples/sieve.bas
```

---

## 30장. 디버거 — 단계 실행과 브레이크포인트

### 30.1 VM 훅 인터페이스

```go
// internal/vm/debug.go
package vm

type Debugger interface {
    BeforeStep(m *VM, ins Instr) bool // false 반환 시 정지
    OnError(m *VM, err error)
}

// VM 구조체에 필드 추가
//   Debugger Debugger
//   stepMode bool
//   breakOn  map[int]bool

// step 함수 진입부:
//   if m.Debugger != nil {
//       if !m.Debugger.BeforeStep(m, ins) {
//           return errPaused
//       }
//   }
```

### 30.2 단순 CLI 디버거

```go
type CLIDebugger struct {
    breakLines map[int]bool
    stepLeft   int
    chunk      *Chunk
}

func (d *CLIDebugger) BeforeStep(m *VM, ins Instr) bool {
    line := d.lineAt(m.pc - 1)
    if d.breakLines[line] {
        fmt.Printf("[BREAK at line %d]\n", line)
        return d.prompt(m)
    }
    if d.stepLeft > 0 {
        d.stepLeft--
        return true
    }
    return d.prompt(m)
}

func (d *CLIDebugger) prompt(m *VM) bool {
    for {
        fmt.Print("(dbg) ")
        var cmd string
        fmt.Scanln(&cmd)
        switch cmd {
        case "s", "step":
            d.stepLeft = 0
            return true
        case "n", "next":
            d.stepLeft = 1
            return true
        case "c", "cont":
            d.stepLeft = -1 // 무한
            return true
        case "p", "print":
            fmt.Println("stack:", m.stack)
        case "q":
            return false
        }
    }
}

func (d *CLIDebugger) lineAt(opIdx int) int {
    // 옵 인덱스 → BASIC 라인 역방향 조회 (LineMap을 역으로)
    best := 0
    for ln, idx := range d.chunk.LineMap {
        if idx <= opIdx && ln > best {
            best = ln
        }
    }
    return best
}
```

### 30.3 TRON / TROFF

GW-BASIC의 `TRON`은 라인 추적을 켭니다. 디버거 인터페이스를 통해 `BeforeStep`에서 라인 번호 출력:

```go
type TraceDebugger struct {
    chunk *Chunk
    last  int
}

func (d *TraceDebugger) BeforeStep(m *VM, ins Instr) bool {
    line := lineAt(d.chunk, m.pc-1)
    if line != d.last && line > 0 {
        fmt.Printf("[%d]", line)
        d.last = line
    }
    return true
}
```

---

## 31장. 테스트 전략과 회귀 검증

### 31.1 테스트 계층

| 계층 | 위치 | 도구 |
|------|------|------|
| Lexer 단위 | `internal/lexer/*_test.go` | `go test` |
| Parser 단위 | `internal/parser/*_test.go` | 동일 |
| Compiler 단위 | `internal/compiler/*_test.go` | 동일 |
| VM 단위 | `internal/vm/*_test.go` | 동일 |
| 통합 (run .bas) | `tests/integration_test.go` | 동일 |
| 골든 출력 | `tests/golden_test.go` | `go test -update` 플래그로 갱신 |

### 31.2 골든 테스트 패턴

`examples/*.bas`를 실행한 출력을 `examples/expected/*.txt`에 저장하고, CI에서 자동 비교합니다.

```go
// tests/golden_test.go
package tests

import (
    "bytes"
    "context"
    "flag"
    "os"
    "path/filepath"
    "strings"
    "testing"

    "github.com/chobocho/go_gwbasic/internal/compiler"
    "github.com/chobocho/go_gwbasic/internal/host"
    "github.com/chobocho/go_gwbasic/internal/lexer"
    "github.com/chobocho/go_gwbasic/internal/parser"
    "github.com/chobocho/go_gwbasic/internal/vm"
)

var update = flag.Bool("update", false, "update golden files")

type captureHost struct {
    host.NullHost
    buf bytes.Buffer
}

func (h *captureHost) Print(s string) { h.buf.WriteString(s) }

func TestExamples(t *testing.T) {
    files, _ := filepath.Glob("../examples/*.bas")
    for _, f := range files {
        name := strings.TrimSuffix(filepath.Base(f), ".bas")
        t.Run(name, func(t *testing.T) {
            src, _ := os.ReadFile(f)
            toks, err := lexer.Tokenize(string(src))
            if err != nil {
                t.Fatal(err)
            }
            prog, err := parser.Parse(toks)
            if err != nil {
                t.Fatal(err)
            }
            ch, err := compiler.Compile(prog)
            if err != nil {
                t.Fatal(err)
            }
            h := &captureHost{}
            if err := vm.New(ch, h).Run(context.Background()); err != nil {
                t.Fatal(err)
            }
            golden := "../examples/expected/" + name + ".txt"
            if *update {
                _ = os.MkdirAll("../examples/expected", 0o755)
                _ = os.WriteFile(golden, h.buf.Bytes(), 0o644)
                return
            }
            want, err := os.ReadFile(golden)
            if err != nil {
                t.Skipf("golden missing (run with -update): %v", err)
                return
            }
            if !bytes.Equal(h.buf.Bytes(), want) {
                t.Errorf("output mismatch\n--- want ---\n%s\n--- got ---\n%s",
                    want, h.buf.String())
            }
        })
    }
}
```

`go test ./tests/ -update` 로 골든을 갱신, `go test ./tests/` 로 검증.

### 31.3 벤치마크

```go
// internal/vm/bench_test.go
func BenchmarkSieve(b *testing.B) {
    src, _ := os.ReadFile("../../examples/sieve.bas")
    toks, _ := lexer.Tokenize(string(src))
    prog, _ := parser.Parse(toks)
    ch, _ := compiler.Compile(prog)
    h := &nullHost{}
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = vm.New(ch, h).Run(context.Background())
    }
}
```

`go test -bench=. ./internal/vm/`. 일반적인 노트북에서 `examples/sieve.bas`(소수 200까지)는 수백 µs 안에 실행됩니다.

### 31.4 퍼지 테스트

Go 1.18+의 fuzzing으로 Lexer/Parser의 강건성을 검사합니다.

```go
// internal/lexer/fuzz_test.go
func FuzzTokenize(f *testing.F) {
    seeds := []string{
        `10 PRINT "HI"`,
        "20 GOTO 10",
        "REM hello",
    }
    for _, s := range seeds {
        f.Add(s)
    }
    f.Fuzz(func(t *testing.T, s string) {
        defer func() {
            if r := recover(); r != nil {
                t.Errorf("panic on %q: %v", s, r)
            }
        }()
        _, _ = lexer.Tokenize(s)
    })
}
```

`go test -fuzz=FuzzTokenize ./internal/lexer/`로 임의 입력을 폭격해 패닉이 일어나지 않는지 확인합니다.

---

## 32장. 빌드, 패키징, 배포

### 32.1 단일 바이너리 빌드

```bash
go build -trimpath -ldflags="-s -w" -o gwbasic ./cmd/gwbasic
```

`-trimpath`: 빌드 경로 정보 제거 (재현 가능 빌드)
`-s -w`: 디버그 심볼 제거 → 바이너리 크기 약 30% 감소

### 32.2 크로스 컴파일

```bash
# Windows
GOOS=windows GOARCH=amd64 go build -o gwbasic.exe ./cmd/gwbasic
# macOS Apple Silicon
GOOS=darwin GOARCH=arm64 go build -o gwbasic-mac-arm64 ./cmd/gwbasic
# Linux
GOOS=linux GOARCH=amd64 go build -o gwbasic-linux ./cmd/gwbasic
```

### 32.3 WASM 빌드 (브라우저 실행)

```bash
GOOS=js GOARCH=wasm go build -o web/dist.wasm ./cmd/gwbasic-web
cp "$(go env GOROOT)/misc/wasm/wasm_exec.js" web/
```

`web/index.html`은 `wasm_exec.js`를 로드하고 `dist.wasm`을 인스턴스화합니다.

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>GW-BASIC (Go WASM)</title></head>
<body>
<pre id="out"></pre>
<script src="wasm_exec.js"></script>
<script>
  const go = new Go();
  WebAssembly.instantiateStreaming(fetch("dist.wasm"), go.importObject)
    .then(r => go.run(r.instance));
</script>
</body>
</html>
```

`python -m http.server 8001`로 띄워 브라우저에서 동작 확인. CLAUDE.md의 빌드 규칙(외부 라이브러리 불사용, 단일 산출물, http.server 동작)을 모두 만족합니다.

### 32.4 build.sh / build.bat

`build.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
mkdir -p release
go build -trimpath -ldflags="-s -w" -o release/gwbasic ./cmd/gwbasic
cp -r examples release/
echo "Built: release/gwbasic"
```

`build.bat` (cp949 인코딩):

```bat
@echo off
chcp 949 >nul
if not exist release mkdir release
go build -trimpath -ldflags="-s -w" -o release\gwbasic.exe .\cmd\gwbasic
xcopy /E /I /Y examples release\examples >nul
echo 빌드 완료: release\gwbasic.exe
```

### 32.5 GitHub Actions 워크플로

`.github/workflows/test.yml`:

```yaml
name: test
on: [push, pull_request]
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go vet ./...
      - run: go test -race ./...
      - run: go build ./cmd/gwbasic
```

`-race`는 데이터 경합 검사. 본 구현은 VM 자체가 단일 고루틴 실행이므로 큰 의미 없지만, REPL 입력이 별도 고루틴이므로 안전망이 됩니다.

### 32.6 릴리스 절차

1. 버전 태그: `git tag v0.1.0 && git push --tags`
2. GoReleaser 또는 수동: 4종 OS/아키텍처 바이너리 빌드
3. GitHub Release에 첨부
4. README 갱신 — 다운로드 링크, 사용법

```bash
# Goreleaser 예시 (.goreleaser.yml)
project_name: gwbasic
builds:
  - id: gwbasic
    main: ./cmd/gwbasic
    goos: [linux, darwin, windows]
    goarch: [amd64, arm64]
    ldflags: ["-s -w -X main.version={{.Version}}"]
archives:
  - format: tar.gz
    format_overrides:
      - goos: windows
        format: zip
```

---

> 7부 끝. 다음 부록에서 BNF 전체, 명령어 카드, 에러 코드, 예제 모음을 정리합니다.


---

# 부록

## 부록 A. GW-BASIC BNF 전체

```ebnf
(* ─── 프로그램 구조 ───────────────────────────── *)
<program>     ::= { <line> }
<line>        ::= <line-number> <statement-list> <eol>
                | <statement-list> <eol>
<line-number> ::= /[0-9]{1,5}/
<statement-list> ::= <statement> { ":" <statement> }
<eol>         ::= "\n" | EOF

(* ─── 어휘 단위 ───────────────────────────────── *)
<number>      ::= <int-lit> | <float-lit> | <hex-lit> | <oct-lit>
<int-lit>     ::= /[0-9]+/
<float-lit>   ::= /[0-9]+\.[0-9]*([ED][+-]?[0-9]+)?/
                | /\.[0-9]+([ED][+-]?[0-9]+)?/
                | /[0-9]+[ED][+-]?[0-9]+/
<hex-lit>     ::= /&H[0-9A-Fa-f]+/
<oct-lit>     ::= /&O?[0-7]+/
<string>      ::= /"[^"\n]*"/
<ident>       ::= /[A-Za-z][A-Za-z0-9]*/
<type-suffix> ::= "%" | "!" | "#" | "$"

(* ─── 문장 ────────────────────────────────────── *)
<statement> ::= <assign-stmt>
              | <print-stmt>     | <input-stmt>
              | <if-stmt>
              | <for-stmt>       | <next-stmt>
              | <while-stmt>     | <wend-stmt>
              | <goto-stmt>      | <gosub-stmt> | <return-stmt>
              | <on-goto-stmt>
              | <end-stmt>       | <stop-stmt>
              | <rem-stmt>
              | <dim-stmt>
              | <data-stmt>      | <read-stmt>  | <restore-stmt>
              | <def-fn-stmt>
              | <cls-stmt>       | <screen-stmt>| <color-stmt>
              | <pset-stmt>      | <line-stmt>  | <circle-stmt>
              | <paint-stmt>     | <locate-stmt>
              | <sound-stmt>     | <play-stmt>  | <beep-stmt>
              | <randomize-stmt>
              | <clear-stmt>     | <swap-stmt>
              | (* empty *)

<assign-stmt> ::= [ "LET" ] <lvalue> "=" <expression>
<lvalue>      ::= <variable> | <array-ref>
<variable>    ::= <ident> [ <type-suffix> ]
<array-ref>   ::= <variable> "(" <expression> { "," <expression> } ")"

<print-stmt>  ::= ("PRINT" | "?") [ <print-list> ]
<print-list>  ::= <print-item> { <print-sep> [ <print-item> ] }
<print-sep>   ::= "," | ";"
<print-item>  ::= <expression>
                | "TAB" "(" <expression> ")"
                | "SPC" "(" <expression> ")"
                | "USING" <string-expr> ";" <expr-list>

<input-stmt>  ::= "INPUT" [ ";" ] [ <string> ( ";" | "," ) ] <var-list>
<var-list>    ::= <lvalue> { "," <lvalue> }

<if-stmt>     ::= "IF" <expression> "THEN" <then-clause>
                  [ "ELSE" <else-clause> ]
<then-clause> ::= <line-number> | <statement-list>
<else-clause> ::= <line-number> | <statement-list>

<for-stmt>    ::= "FOR" <variable> "=" <expression> "TO" <expression>
                  [ "STEP" <expression> ]
<next-stmt>   ::= "NEXT" [ <variable> { "," <variable> } ]
<while-stmt>  ::= "WHILE" <expression>
<wend-stmt>   ::= "WEND"

<goto-stmt>   ::= "GOTO"  <line-number>
<gosub-stmt>  ::= "GOSUB" <line-number>
<return-stmt> ::= "RETURN" [ <line-number> ]
<on-goto-stmt>::= "ON" <expression> ("GOTO" | "GOSUB")
                  <line-number> { "," <line-number> }

<dim-stmt>      ::= "DIM" <dim-decl> { "," <dim-decl> }
<dim-decl>      ::= <variable> "(" <expression> { "," <expression> } ")"
<data-stmt>     ::= "DATA" <data-item> { "," <data-item> }
<data-item>     ::= <number> | <string> | <bare-string>
<read-stmt>     ::= "READ" <lvalue> { "," <lvalue> }
<restore-stmt>  ::= "RESTORE" [ <line-number> ]

<def-fn-stmt>   ::= "DEF" "FN" <ident> [ "(" <param-list> ")" ] "=" <expression>
<param-list>    ::= <variable> { "," <variable> }

<end-stmt>       ::= "END"
<stop-stmt>      ::= "STOP"
<rem-stmt>       ::= ("REM" | "'") /.*/
<clear-stmt>     ::= "CLEAR"
<randomize-stmt> ::= "RANDOMIZE" [ <expression> ]
<swap-stmt>      ::= "SWAP" <variable> "," <variable>

<screen-stmt>    ::= "SCREEN" <expression>
<cls-stmt>       ::= "CLS" [ <expression> ]
<color-stmt>     ::= "COLOR" [ <expression> ] [ "," <expression> ]
<pset-stmt>      ::= ("PSET" | "PRESET") <coord> [ "," <expression> ]
<line-stmt>      ::= "LINE" [ <coord> ] "-" <coord>
                     [ "," <expression> ] [ "," ( "B" | "BF" ) ]
<circle-stmt>    ::= "CIRCLE" <coord> "," <expression>
                     [ "," <expression> ]
                     [ "," <expression> "," <expression> ]
                     [ "," <expression> ]
<paint-stmt>     ::= "PAINT" <coord> [ "," <expression> [ "," <expression> ] ]
<locate-stmt>    ::= "LOCATE" [ <expression> ] [ "," <expression> ]
<coord>          ::= [ "STEP" ] "(" <expression> "," <expression> ")"

<sound-stmt> ::= "SOUND" <expression> "," <expression>
<play-stmt>  ::= "PLAY" <string-expr>
<beep-stmt>  ::= "BEEP"

(* ─── 표현식 ─────────────────────────────────── *)
<expression>     ::= <or-expr>
<or-expr>        ::= <xor-expr>  { "OR"  <xor-expr> }
<xor-expr>       ::= <and-expr>  { "XOR" <and-expr> }
<and-expr>       ::= <not-expr>  { "AND" <not-expr> }
<not-expr>       ::= [ "NOT" ] <rel-expr>
<rel-expr>       ::= <add-expr> [ <rel-op> <add-expr> ]
<rel-op>         ::= "=" | "<>" | "<" | "<=" | ">" | ">="
<add-expr>       ::= <mul-expr>  { ("+" | "-") <mul-expr> }
<mul-expr>       ::= <intdiv-expr> { ("*" | "/") <intdiv-expr> }
<intdiv-expr>    ::= <mod-expr>  { "\\" <mod-expr> }
<mod-expr>       ::= <pow-expr>  { "MOD" <pow-expr> }
<pow-expr>       ::= <unary-expr> { "^" <unary-expr> }
<unary-expr>     ::= ("+" | "-") <unary-expr> | <primary>
<primary>        ::= <number> | <string>
                   | <variable> | <array-ref>
                   | <func-call>
                   | "(" <expression> ")"

<func-call>      ::= <builtin-name> "(" [ <expr-list> ] ")"
                   | "FN" <ident> "(" [ <expr-list> ] ")"
<expr-list>      ::= <expression> { "," <expression> }
```

## 부록 B. 명령어 레퍼런스 카드

| 명령 | 설명 | 본 구현 |
|------|------|---------|
| `PRINT`, `?` | 표준출력 | ✓ |
| `INPUT` | 한 줄 입력 | ✓ |
| `LET`, `=` | 할당 | ✓ |
| `IF / THEN / ELSE` | 조건 분기 | ✓ |
| `FOR / NEXT [STEP]` | 카운터 루프 | ✓ |
| `WHILE / WEND` | 선검사 루프 | ✓ |
| `GOTO`, `GOSUB`, `RETURN` | 분기/서브루틴 | ✓ |
| `ON x GOTO/GOSUB` | 분기 표 | ✓ |
| `END`, `STOP` | 종료 | ✓ |
| `REM`, `'` | 주석 | ✓ |
| `DIM`, `ERASE` | 배열 선언/해제 | ✓ |
| `DATA / READ / RESTORE` | 데이터 풀 | ✓ |
| `DEF FN` | 사용자 함수 | ✓ |
| `RANDOMIZE`, `RND` | 난수 | ✓ |
| `CLS`, `SCREEN`, `COLOR` | 화면 모드 | ✓ |
| `PSET`, `PRESET`, `LINE`, `CIRCLE`, `PAINT` | 그래픽 | ✓ |
| `LOCATE` | 커서 이동 | ✓ |
| `SOUND`, `PLAY`, `BEEP` | 사운드 | ✓ |
| `LEN`, `LEFT$`, `RIGHT$`, `MID$`, `INSTR`, `STR$`, `VAL`, `CHR$`, `ASC` | 문자열 | ✓ |
| `SPACE$`, `STRING$`, `HEX$`, `OCT$` | 문자열 | ✓ |
| `ABS`, `SGN`, `INT`, `FIX`, `SQR` | 수학 | ✓ |
| `SIN`, `COS`, `TAN`, `ATN`, `LOG`, `EXP` | 수학 | ✓ |
| `CINT`, `CSNG`, `CDBL` | 형변환 | ✓ |
| `TIMER` | 시간 | ✓ |
| `DEFINT/SNG/DBL/STR` | 기본 타입 | ✓ |
| `OPTION BASE` | 인덱스 시작 | △ |
| `INKEY$` | 비차단 키 | △ |
| `OPEN/CLOSE/PRINT#/INPUT#` | 파일 입출력 | ✗ |
| `FIELD/GET/PUT/LSET/RSET` | 랜덤 파일 | ✗ |
| `PEEK/POKE/USR/CALL` | 메모리/네이티브 | ✗ |
| `BLOAD/BSAVE` | 바이너리 입출력 | ✗ |
| `KEY ON/OFF` | 함수키 | ✗ |
| `DRAW` | 매크로 그래픽 | ✗ |

## 부록 C. 에러 코드표

```go
// internal/common/errcodes.go
const (
    ErrNextWithoutFor      = 1   // NEXT without FOR
    ErrSyntax              = 2   // Syntax error
    ErrReturnWithoutGosub  = 3   // RETURN without GOSUB
    ErrOutOfData           = 4   // Out of DATA
    ErrIllegalFunctionCall = 5   // Illegal function call
    ErrOverflow            = 6   // Overflow
    ErrOutOfMemory         = 7   // Out of memory
    ErrUndefinedLineNumber = 8   // Undefined line number
    ErrSubscriptOutOfRange = 9   // Subscript out of range
    ErrDuplicateDefinition = 10  // Duplicate Definition
    ErrDivisionByZero      = 11  // Division by zero
    ErrIllegalDirect       = 12  // Illegal direct
    ErrTypeMismatch        = 13  // Type mismatch
    ErrOutOfStringSpace    = 14  // Out of string space
    ErrStringTooLong       = 15  // String too long
    ErrStringFormulaTooComplex = 16
    ErrCantContinue        = 17
    ErrUndefinedUserFunction = 18
    ErrNoResume            = 19
    ErrResumeWithoutError  = 20
    ErrUnprintableError    = 21
    ErrMissingOperand      = 22
    ErrLineBufferOverflow  = 23
    ErrDeviceTimeout       = 24
    ErrDeviceFault         = 25
    ErrForWithoutNext      = 26
)
```

## 부록 D. 예제 프로그램 모음 (10선)

본 책에 동봉된 `examples/` 디렉터리에는 다음 예제가 들어 있습니다.

1. **hello.bas** — `10 PRINT "HELLO, WORLD"`
2. **fib.bas** — 피보나치 수열 (24장)
3. **sieve.bas** — 에라토스테네스 체 (20장)
4. **string_demo.bas** — 문자열 함수 데모 (23장)
5. **data_demo.bas** — DATA/READ 데모 (25장)
6. **gosub_demo.bas** — GOSUB 팩토리얼 (21장)
7. **ctrl_demo.bas** — IF/FOR/WHILE 종합 제어 흐름
8. **circle_demo.bas** — 그래픽 동심원
9. **mml_demo.bas** — `PLAY "T120 O4 CDEFGAB > C"`
10. **game_demo.bas** — 텍스트 어드벤처 시작점 (독자 과제)

각 예제는 다음 명령으로 실행 가능합니다.

```bash
./gwbasic -run examples/sieve.bas
```

## 부록 E. 추가 학습 자료

| 분류 | 자료 |
|------|------|
| 인터프리터 일반 | Bob Nystrom, *Crafting Interpreters* (https://craftinginterpreters.com) |
| Go로 인터프리터 | Thorsten Ball, *Writing an Interpreter in Go* / *Writing a Compiler in Go* |
| Go 표준 학습 | Donovan & Kernighan, *The Go Programming Language* (2015) |
| Go 공식 | https://go.dev/tour, https://go.dev/doc/effective_go |
| 컴파일러 이론 | Aho et al., *Compilers: Principles, Techniques, and Tools* (Dragon Book) |
| BASIC 역사 | Microsoft, *GW-BASIC User's Guide* (1987), `IBM PC BASIC Reference` |
| Pratt parser | Bob Nystrom, "Pratt Parsers: Expression Parsing Made Easy" |

## 부록 F. 자매서

본 책은 다음 자매서와 *동일한 VM 설계와 예제* 를 공유합니다. 언어별 구현 차이를 비교하며 학습하시면 좋습니다.

- **C로 만드는 GW-BASIC 인터프리터** — `chobocho_box/c_gwbasic_book/`
- **TypeScript로 만드는 GW-BASIC 인터프리터** — `chobocho_box/ts_gwbasic_book/`
- **Lua로 만드는 GW-BASIC 인터프리터** — `chobocho_box/lua_gwbasic_book/`

## 부록 G. 프로젝트 디렉터리 최종 구조

```
go_gwbasic_book/
├── 00_preface.md            ← 머리말
├── 01_part1_foundations.md  ← 1부 기초
├── 02_part2_specification.md
├── 03_part3_lexer.md
├── 04_part3_parser.md
├── 05_part4_bytecode.md
├── 06_part4_vm.md
├── 07_part5_runtime_io.md
├── 08_part5_runtime_lib.md
├── 09_part6_graphics_sound.md
├── 10_part7_tools.md
├── 11_appendix.md           ← 부록 (본 파일)
├── examples/
│   ├── ctrl_demo.bas
│   ├── data_demo.bas
│   ├── fib.bas
│   ├── gosub_demo.bas
│   ├── hello.bas
│   ├── sieve.bas
│   └── string_demo.bas
├── src/                     ← Go 소스 (cmd, internal 미러)
└── tests/                   ← 통합 / 골든 테스트
```

`go_gwbasic/` 실제 구현 트리:

```
go_gwbasic/
├── go.mod
├── cmd/
│   └── gwbasic/main.go
├── internal/
│   ├── common/    types.go errcodes.go
│   ├── lexer/     token.go keywords.go lexer.go *_test.go
│   ├── parser/    cursor.go parser.go expr.go stmt.go *_test.go
│   ├── ast/       nodes.go print.go
│   ├── compiler/  compiler.go disasm.go *_test.go
│   ├── vm/        op.go chunk.go vm.go builtins.go debug.go *_test.go
│   ├── runtime/   value.go env.go strfunc.go mathfunc.go printusing.go
│   ├── host/      host.go term.go imghost.go wavhost.go mml.go
│   ├── repl/      repl.go
│   └── runner/    runner.go
├── examples/      *.bas
├── tests/         golden_test.go integration_test.go
├── build.sh
└── build.bat
```

## 부록 H. 개발 체크리스트

- [ ] `go vet ./...` 통과
- [ ] `go test ./...` 모든 테스트 통과
- [ ] `go test -race ./...` 데이터 경합 없음
- [ ] `go test -bench=. ./internal/vm/` 회귀 없는 성능
- [ ] `examples/*.bas` 전체가 골든 테스트 통과
- [ ] `python -m http.server 8001` 후 WASM 빌드 동작
- [ ] `build.sh`, `build.bat` 산출물 확인
- [ ] 한글 빌드 메시지가 cp949에서 깨지지 않음
- [ ] README.md 한글, history.md 갱신

## 부록 I. 짧은 후기

GW-BASIC은 1980년대의 언어이지만, *언어 처리기*를 처음부터 만들어 보기에 매우 좋은 교재입니다. 다음의 모든 핵심 주제가 작은 분량 안에 들어 있기 때문입니다.

- 어휘 분석, 문맥에 의존하는 토큰화 (REM, DATA, IF/THEN)
- 재귀 하강 + Pratt의 하이브리드 파싱
- 라인 번호와 GOTO — 비구조적 제어 흐름의 컴파일
- 스택 기반 VM의 디스패치 루프
- 동적 타입과 묵시적 변환
- 호스트 추상화 (그래픽, 사운드, 입출력)
- 골든 테스트와 벤치마크

이 책의 Go 구현이 독자께 처음 컴파일러를 만들어 보는 즐거움의 출발점이 되기를 바랍니다.

> "도구는 자기보다 큰 것을 만들 수 있다."  
> — Doug Engelbart (paraphrased)

```basic
9999 PRINT "다 만든 BASIC으로 다음 BASIC을 만드세요." : END
```

---

> 부록 끝. 책 전체 끝.
