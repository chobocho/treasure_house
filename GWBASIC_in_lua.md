# Lua로 만드는 GW-BASIC 인터프리터

**바이트코드 가상 머신을 직접 설계하고 1980년대의 명작 언어를 되살리는 200페이지 가이드**

저자: chobocho
판: 1.0 (2026)
대상 독자: 컴파일러/인터프리터의 내부 동작을 손으로 만들어보고 싶은 개발자
선수 지식: 기본적인 Lua 또는 다른 동적 언어 경험, 자료구조에 대한 일반적인 지식

---

## 머리말

이 책은 한 권의 노트와 키보드만 있으면 1980년대의 GW-BASIC 인터프리터를 처음부터 끝까지 직접 만들 수 있도록 설계되었다. 단순히 코드 조각을 모아 놓은 것이 아니라, 다음의 흐름을 따라 한 줄 한 줄 빌드해 나간다.

1. **언어 명세를 BNF로 정의한다.** 무엇을 만드는지가 분명해야 무엇을 짤지가 분명해진다.
2. **어휘 분석기(lexer)를 작성한다.** 문자의 흐름을 토큰의 흐름으로 바꾼다.
3. **재귀 하강 파서를 작성한다.** 토큰을 추상 구문 트리(AST)로 바꾼다.
4. **바이트코드를 설계한다.** 트리워킹이 아닌, 컴팩트하고 빠른 명령어 집합을 정의한다.
5. **컴파일러를 작성한다.** AST를 바이트코드로 낮춘다(lower).
6. **스택 기반 가상 머신을 작성한다.** 바이트코드를 실행한다.
7. **표준 라이브러리를 채운다.** GW-BASIC이 제공하는 수학·문자열 함수들을 구현한다.
8. **REPL과 파일 로더로 마무리한다.** 실제 .BAS 프로그램이 돌아간다.

GW-BASIC은 흔히 향수의 대상으로만 거론되지만, 인터프리터를 처음 만들어 보기에 이만한 언어가 없다. 라인 번호 기반의 단순한 제어 흐름, 정수/실수/문자열의 직관적인 타입 시스템, 그리고 BASIC 특유의 명령형 단어들(LET, PRINT, GOSUB, DATA, READ, DEF FN…)이 학습자의 부담을 적당한 선에서 머무르게 해 준다. 동시에 표현식 평가, 우선순위, 짧은-회로 평가, GOTO/GOSUB의 호출 스택 관리, 배열의 차원 처리, DEF FN의 클로저, ON GOTO의 분기표 컴파일 등 컴파일러 학습에서 반드시 만나는 주제를 모두 자연스럽게 다루게 된다.

이 책에서 만든 인터프리터는 실제로 동작한다. 부록 C에 첨부된 약 1,500줄의 Lua 코드를 그대로 입력해도 좋고, 깃 저장소에서 받아도 좋다. 어느 쪽이든 다음 명령으로 즉시 실행된다.

```sh
$ lua src/main.lua examples/sieve.bas
```

이 책의 모든 코드는 Lua 5.1과 LuaJIT, 그리고 Lua 5.3/5.4에서 호환된다. 외부 라이브러리는 필요 없다.

---

## 차례 (Table of Contents)

**제1부 도입과 배경**
- 1장 GW-BASIC을 다시 만드는 이유
- 2장 인터프리터의 5단계 파이프라인
- 3장 Lua를 빠르게 복습하기
- 4장 프로젝트 구조와 빌드

**제2부 어휘 분석**
- 5장 토큰의 정의
- 6장 정규 표현식 없이 만드는 어휘 분석기
- 7장 문자열, 숫자 리터럴과 타입 접미어
- 8장 키워드와 식별자

**제3부 문법과 파서**
- 9장 BNF로 표현하는 GW-BASIC 문법
- 10장 재귀 하강 파서의 뼈대
- 11장 표현식 파서 — 우선순위 등반(Pratt) 기법
- 12장 문장 파서와 라인 번호

**제4부 AST와 컴파일러**
- 13장 AST 노드 설계
- 14장 바이트코드 명령어 집합 정의
- 15장 표현식 컴파일
- 16장 제어 흐름 컴파일과 백패치

**제5부 가상 머신**
- 17장 스택 기반 VM의 구조
- 18장 변수와 환경
- 19장 GOSUB / RETURN 호출 스택
- 20장 배열, DIM, 그리고 다차원 인덱스

**제6부 런타임과 내장 함수**
- 21장 PRINT의 의외로 깊은 세계
- 22장 INPUT, DATA, READ
- 23장 수학·문자열 내장 함수
- 24장 DEF FN과 사용자 정의 함수

**제7부 통합과 확장**
- 25장 REPL 만들기
- 26장 파일 로더와 LIST/RUN/NEW
- 27장 에러 처리와 ON ERROR GOTO
- 28장 성능, 디버그, 다음 단계

**부록**
- 부록 A 전체 BNF
- 부록 B 바이트코드 명령어 사전
- 부록 C 전체 Lua 소스 코드
- 부록 D 예제 .BAS 프로그램 모음
- 부록 E 참고 문헌과 더 읽을거리

---

# 제1부 — 도입과 배경

## 1장. GW-BASIC을 다시 만드는 이유

### 1.1 BASIC은 죽지 않았다

BASIC은 1964년 다트머스에서 태어났고, 1981년 IBM PC와 함께 BASICA·GW-BASIC이라는 형태로 거실의 PC에 들어왔다. 한 줄에 한 명령씩, 라인 번호로 흐름을 통제하는 이 단순한 언어는 한 세대의 프로그래머를 길러냈다. 21세기에 BASIC을 직접 구현해 보는 것이 무슨 의미가 있을까?

대답은 명확하다. **언어 처리기의 모든 핵심 주제를 가장 짧은 거리로 통과할 수 있기 때문이다.** Python이나 JavaScript의 문법은 너무 풍부해서 학습자가 인터프리터의 본질에 다가가기 전에 길을 잃기 쉽다. 반대로 Lisp 같은 언어는 너무 균질해서 “파서가 거의 없다”는 함정이 있다. GW-BASIC은 그 사이의 황금 지대에 있다.

- 표현식의 우선순위는 풍부하지만 정형적이다.
- 명령문은 약 20여 개이고 각각 동작이 뚜렷하다.
- 동적 타이핑이지만 변수 이름의 접미어(`A`, `A%`, `A!`, `A#`, `A$`)로 타입을 명시한다.
- GOTO/GOSUB라는 비구조적 제어 흐름이 있어 “주소 계산”의 감각을 익히기에 좋다.
- 배열, 사용자 함수(DEF FN), DATA/READ 등 “작고 완비된” 기능 셋이 있다.

이런 특성 때문에 BASIC은 “인터프리터 학습용 언어”로 거듭 추천되어 왔다. 이 책은 그 추천을 진지하게 받아들여, 단순한 트리 워커가 아니라 **바이트코드를 설계하고 가상 머신에서 실행**하는 완전한 구현을 목표로 한다.

### 1.2 우리가 만들 것의 모양

이 책에서 만드는 인터프리터의 최종 형태는 다음과 같다.

```
[ 소스(.bas) ]
      │  Lexer
      ▼
[ 토큰 스트림 ]
      │  Parser
      ▼
[ AST ]
      │  Compiler
      ▼
[ Bytecode ]
      │  VM
      ▼
[ 표준 출력 / 변수 / 메모리 ]
```

각 단계는 독립적인 모듈이며, 단계 사이의 인터페이스는 단순한 Lua 테이블이다. 단계가 분리되어 있다는 것이 단순히 코드 정리 차원의 문제가 아님을 7장과 11장에서 보게 될 것이다. 단계 분리는 곧 디버깅 가능성, 테스트 가능성, 그리고 무엇보다 **사고의 명료함**과 직결된다.

### 1.3 왜 트리 워킹이 아니고 바이트코드 VM인가

가장 단순한 인터프리터는 AST를 받아 재귀적으로 평가하는 트리 워커(tree walker)다. AST 노드의 종류만큼 `eval(node)` 함수의 분기가 있고, 그게 전부다. 이 책의 1장에서 그것을 만들고 끝낼 수도 있었지만, 우리는 그렇게 하지 않는다. 이유는 세 가지다.

1. **GOTO와 GOSUB.** GW-BASIC의 핵심 제어 흐름은 “라인 N으로 점프”다. 트리 워커에서 점프를 흉내내려면 “예외를 던져서 위로 도망치고 다시 찾아간다”는 식의 트릭이 필요하다. 바이트코드 VM에서는 그저 명령 포인터(`ip`)를 갈아끼우면 끝이다.
2. **속도.** 바이트코드는 디스패치 비용이 압도적으로 작다. 트리 워킹은 노드를 다시 해석하기 위해 매번 함수 호출을 해야 하지만, 바이트코드는 한 줄짜리 `op` 디스패치로 끝난다.
3. **언어 처리의 정체성.** 이 책의 학습 가치 절반이 “바이트코드 설계”라는 사고 훈련에 있다. 어떤 명령을 가질 것인가? 스택은 어떻게 다룰 것인가? 라인 번호는 언제 해소(resolve)할 것인가? 이러한 결정을 직접 내려 보는 것이 핵심이다.

### 1.4 학습 경로

이 책은 처음부터 끝까지 순서대로 읽도록 설계되었다. 각 장은 직전 장의 코드 위에 새 코드를 얹는다. 중간에 빠지면 컴파일이 되지 않는다. 그러나 이미 어떤 단계를 만들어 본 적이 있는 독자는 다음의 “지름길 표”를 참고할 수 있다.

| 이미 알고 있는 것 | 가도 좋은 장 |
|---|---|
| 토큰화/파싱은 익숙하다 | 13장(AST 설계)부터 |
| 트리 워커를 짜 본 적 있다 | 14장(바이트코드 명령어)부터 |
| LLVM IR/스택 머신을 안다 | 17장(VM 본체)과 21장(PRINT)을 먼저 |
| 그저 GW-BASIC만 좀 더 정확히 만들고 싶다 | 21~24장을 집중적으로 |

### 1.5 실행 환경

이 책의 코드는 다음 환경에서 검증되었다.

- Lua 5.1.5 (PUC-Rio)
- LuaJIT 2.1
- Lua 5.3.6, 5.4.6

운영체제로는 Linux, macOS, Windows(WSL), Termux(Android)에서 동작을 확인했다. 외부 라이브러리는 사용하지 않는다.

설치는 보통 다음으로 충분하다.

```sh
# Debian/Ubuntu
sudo apt install lua5.3

# macOS (Homebrew)
brew install lua

# Termux
pkg install lua54

# Windows
# https://luabinaries.sourceforge.net 에서 받을 것
```

---

## 2장. 인터프리터의 5단계 파이프라인

### 2.1 다섯 단계의 본질

인터프리터를 본격적으로 살펴보면 어디서나 같은 다섯 단계가 등장한다.

1. **Lexing** — 문자 → 토큰
2. **Parsing** — 토큰 → AST
3. **Lowering / Compiling** — AST → 바이트코드(혹은 IR)
4. **Execution** — 바이트코드 실행
5. **Runtime services** — 입출력, 메모리 관리, 표준 라이브러리

각 단계의 출력은 다음 단계의 입력이다. 단계 경계가 명확할수록 디버깅이 쉽다. 우리 인터프리터에서는 다음 명령으로 각 단계의 출력을 들여다볼 수 있다(28장 참고).

```sh
$ lua src/main.lua --dump-tokens examples/fib.bas
$ lua src/main.lua --dump-ast    examples/fib.bas
$ lua src/main.lua --dump-bc     examples/fib.bas
```

이 디버그 플래그는 7부에서 추가하므로 지금은 머릿속에 “단계 출력은 모두 관찰 가능해야 한다”는 원칙만 새겨 두자.

### 2.2 한 줄 예시로 따라가는 파이프라인

다음 한 줄짜리 BASIC을 우리 파이프라인이 어떻게 처리하는지 미리 보자.

```basic
10 LET A = 1 + 2 * 3
```

**Lexing 결과(토큰):**

```
NUMBER(10)  KEYWORD(LET)  IDENT(A)  EQ  NUMBER(1)  PLUS  NUMBER(2)  STAR  NUMBER(3)  EOL  EOF
```

**Parsing 결과(AST):**

```
Program
└─ Line(10)
   └─ Let
      ├─ target: Var(A)
      └─ expr  : BinOp(+,
                       NumLit(1),
                       BinOp(*, NumLit(2), NumLit(3)))
```

**Compiling 결과(바이트코드):**

```
1: PUSHN 1
2: PUSHN 2
3: PUSHN 3
4: MUL
5: ADD
6: STORE A
7: HALT
```

**Execution(VM의 스택 변화):**

```
PUSHN 1 :  [1]
PUSHN 2 :  [1, 2]
PUSHN 3 :  [1, 2, 3]
MUL     :  [1, 6]
ADD     :  [7]
STORE A :  []        # 변수 A = 7
HALT    :  종료
```

이 책의 모든 챕터는 이 다섯 단계 어딘가에 자리한다. 우리는 1장에서 25장까지 이 다이어그램의 화살표를 한 칸씩 채워 나간다.

### 2.3 단계의 분리가 가져다주는 이득

가장 큰 이득은 “테스트 가능성”이다. 어휘 분석기는 단지 함수 하나에 문자열을 넣고 토큰 배열을 받는다. 그러므로 단위 테스트가 자명하다.

```lua
local toks = require("lexer").new('10 PRINT "HI"\n'):tokenize()
assert(toks[1].type == "NUMBER" and toks[1].value == 10)
assert(toks[2].type == "KEYWORD" and toks[2].value == "PRINT")
assert(toks[3].type == "STRING" and toks[3].value == "HI")
```

각 단계가 순수 함수에 가까울수록(즉 부수효과가 적을수록) 이런 단위 테스트가 자연스러워진다. 우리는 매 단계를 `tests/` 디렉터리에 짧은 어서션으로 묶어 둔다.

### 2.4 “언제 컴파일할 것인가”라는 질문

전통적인 BASIC 인터프리터는 사실상 “라인 단위 즉시 실행”에 가깝다. 그러나 이 책은 BASIC 프로그램 전체를 한 번에 컴파일하여 바이트코드로 만든 뒤 실행한다. 이는 다음과 같은 trade-off를 만든다.

| | 즉시 실행(per-line) | 사전 컴파일(우리 방식) |
|---|---|---|
| 시작 지연 | 거의 0 | 작지만 존재 |
| 실행 속도 | 느림 | 빠름 |
| 라인 수정의 즉각성 | 좋음 | 컴파일 다시 |
| GOTO 점프 비용 | 라인 번호 → 라인 텍스트 → 다시 파싱 | 라인 번호 → 주소 한 번 |

REPL(25장)에서는 사용자가 라인을 수정할 때마다 전체를 재컴파일하지만, 라인 수가 작은 BASIC 프로그램에서 이는 거의 즉각적이다.

---

## 3장. Lua를 빠르게 복습하기

이 책은 Lua를 처음 배우는 책이 아니지만, 우리가 사용할 패턴 몇 가지는 미리 정리해 두어야 한다. 이미 익숙한 독자는 이 장을 건너뛰어도 좋다.

### 3.1 테이블이 전부다

Lua의 모든 자료구조는 테이블 하나로 표현된다.

```lua
local arr  = {1, 2, 3}
local rec  = {name="A", age=10}
local dual = {1, 2, 3, name="A", age=10}
print(#arr, rec.name, dual[2])  -- 3  A  2
```

`#`은 연속된 정수 인덱스(1..n)의 길이만 알려준다. 비어 있는 칸이 있으면 결과가 모호하니, 우리 코드는 “순수 배열” 또는 “순수 레코드”로 분리해 사용한다.

### 3.2 `:`와 `.`의 차이

객체지향 흉내는 `setmetatable`로 만든다. 메서드 호출 시 `:`을 쓰면 `self`가 자동으로 전달된다.

```lua
local Lexer = {}
Lexer.__index = Lexer

function Lexer.new(src)
  return setmetatable({src=src, pos=1}, Lexer)
end

function Lexer:peek()  -- self 자동 전달
  return self.src:sub(self.pos, self.pos)
end

local lx = Lexer.new("ABC")
print(lx:peek())  -- "A"
```

이 패턴이 책 내내 반복된다.

### 3.3 패턴 매칭

Lua의 `string` 라이브러리는 정규표현식 대신 “패턴”이라는 자체 언어를 쓴다. 우리는 다음 정도면 충분하다.

| 패턴 | 의미 |
|---|---|
| `%d` | 숫자 |
| `%a` | 알파벳 |
| `%w` | 영숫자 |
| `%s` | 공백 |
| `[…]` | 문자 집합 |
| `^…$` | 앵커 |

### 3.4 스코프와 클로저

`local`을 빠뜨리면 글로벌이 된다. 우리 인터프리터에서는 글로벌을 절대 만들지 않는다(CLAUDE.md의 금지 사항이기도 하다). 모든 함수는 `local` 또는 모듈 테이블의 필드다.

```lua
local M = {}
function M.foo() ... end
return M
```

### 3.5 모듈 시스템

`require("name")`은 `package.path`에서 `name.lua`를 찾아 한 번만 실행하고, 반환값을 캐싱한다. 우리는 모든 모듈에서 단일 테이블을 반환하고 그 안에 함수와 상수를 모은다.

### 3.6 Lua 5.1과 5.3의 호환성

이 책의 코드는 5.1을 최저선으로 잡는다. 5.3 이후에 들어온 다음 기능은 사용하지 않는다.

- `goto label` (5.2+)
- 정수/부동소수 분리(5.3+)
- 비트연산자 `<<`, `>>`, `~` (5.3+)
- `//` (정수 나눗셈, 5.3+)

대신 다음으로 대체한다.

- `math.floor(a/b)`로 정수 나눗셈
- 직접 구현한 `band`, `bor`, `bxor`, `bnot` 함수(`vm.lua` 참고)

---

## 4장. 프로젝트 구조와 빌드

### 4.1 디렉터리 레이아웃

```
lua_gwbasic_book/
├── book.md              ← 지금 읽고 있는 이 책
├── README.md            ← 한국어 안내
├── src/
│   ├── lexer.lua        ← 어휘 분석기
│   ├── parser.lua       ← 파서
│   ├── ast.lua          ← AST 노드 헬퍼
│   ├── compiler.lua     ← AST → 바이트코드
│   ├── runtime.lua      ← 내장 함수 테이블
│   ├── vm.lua           ← 가상 머신
│   └── main.lua         ← REPL/파일 로더
├── examples/
│   ├── hello.bas
│   ├── fib.bas
│   ├── sieve.bas
│   ├── string_demo.bas
│   ├── data_demo.bas
│   ├── gosub_demo.bas
│   └── ctrl_demo.bas
└── tests/
    └── (단위 테스트)
```

### 4.2 빌드 / 실행

별도 빌드 단계는 없다. 다음으로 즉시 실행된다.

```sh
$ cd src
$ lua main.lua ../examples/hello.bas
$ lua main.lua                       # REPL
```

### 4.3 모듈 의존도

```
main.lua
  ├── lexer.lua
  ├── parser.lua  ── ast.lua
  ├── compiler.lua ── ast.lua
  │                ── runtime.lua
  └── vm.lua      ── runtime.lua
```

순환 의존이 없도록 신경 썼다. `runtime.lua`는 다른 모듈에 의존하지 않는다.

### 4.4 테스트 실행

```sh
$ lua tests/run_all.lua
```

### 4.5 어떤 BASIC 프로그램이 돌아가는가

`examples/` 안의 모든 프로그램이 검증되어 있다. 직접 짜 보고 싶다면 `examples/template.bas`를 복사해서 시작하면 된다. 이 책의 코드는 다음을 제공한다.

- 정수/실수/문자열 변수, 4종 접미어
- 다차원 배열(자동 DIM 또는 명시적 DIM)
- 산술 연산, 비교 연산, 논리 비트연산
- IF/THEN/ELSE, FOR/NEXT, WHILE/WEND
- GOTO, GOSUB/RETURN, ON GOTO/GOSUB
- DATA/READ/RESTORE
- DEF FN
- PRINT의 `,` 영역 분리, `;` 무공백 분리, TAB(), SPC()
- INPUT
- 약 30종의 내장 함수

지원하지 않는 것은 다음이다.

- 그래픽 명령 (LINE, CIRCLE, SCREEN…)
- 파일 I/O (OPEN, CLOSE, GET#, PUT#)
- 문자열의 특수 PRINT USING 포맷팅(부분 지원)
- ON ERROR GOTO (27장에서 약식 구현)

---

# 제2부 — 어휘 분석

## 5장. 토큰의 정의

### 5.1 토큰이란 무엇인가

토큰(token)은 “언어가 의미를 부여하는 가장 작은 단위”다. 더 작게 쪼개면 의미가 사라진다. `LET A = 1`이라는 다섯 글자 사이의 다섯 토큰을 보면 다음과 같다.

| 입력 | 토큰 |
|---|---|
| `LET` | KEYWORD(LET) |
| ` ` | (무시) |
| `A` | IDENT(A) |
| ` ` | (무시) |
| `=` | EQ |
| ` ` | (무시) |
| `1` | NUMBER(1) |

공백은 토큰 사이의 구분자일 뿐, 그 자체는 토큰이 아니다(예외: 줄바꿈은 의미가 있어서 EOL 토큰을 만든다).

### 5.2 토큰의 종류

우리 GW-BASIC의 토큰은 다음과 같이 분류한다.

```
NUMBER     - 숫자 리터럴 (정수, 실수, 지수 표기)
STRING     - 문자열 리터럴
IDENT      - 식별자 (변수/배열/함수 이름)
KEYWORD    - 예약어 (LET, PRINT, IF, ...)
REM        - 주석 (줄 끝까지)
EOL        - 줄바꿈
EOF        - 파일 끝
COLON      - :
SEMI       - ;
COMMA      - ,
LPAREN     - (
RPAREN     - )
PLUS, MINUS, STAR, SLASH, BACKSLASH, CARET
EQ, NE, LT, GT, LE, GE
```

### 5.3 토큰 데이터의 모양

각 토큰은 다음과 같은 Lua 테이블이다.

```lua
{ type = "NUMBER", value = 10, line = 1 }
{ type = "KEYWORD", value = "PRINT", line = 1 }
{ type = "STRING", value = "HI", line = 1 }
```

`type`은 토큰의 종류, `value`는 의미값(숫자라면 숫자, 식별자라면 이름), `line`은 디버깅용이다. 굳이 컬럼은 저장하지 않았는데, BASIC은 라인 단위로 동작하므로 라인 번호만 있어도 충분하기 때문이다.

### 5.4 GW-BASIC만의 특이성

GW-BASIC의 어휘 분석에서 다른 언어와 가장 다른 점은 **변수 이름의 마지막 한 글자가 타입을 나타낸다**는 것이다.

| 접미어 | 타입 | 예 |
|---|---|---|
| `$` | 문자열 | `NAME$` |
| `%` | 정수(16비트) | `COUNT%` |
| `!` | 단정도 실수 | `X!` |
| `#` | 배정도 실수 | `Y#` |
| (없음) | 단정도 실수 (기본) | `A` |

이 접미어는 어휘 분석기가 식별자의 끝에 따라 함께 토큰에 묻혀 들어가야 한다. 예컨대 `NAME$`는 IDENT 토큰의 `value`가 `"NAME$"`이 되어야 한다. 이렇게 해 두면 컴파일러/VM은 변수 이름의 마지막 글자만 보고 타입 강제(coercion)를 결정할 수 있다.

### 5.5 키워드와 식별자의 충돌

`PRINT`는 키워드이지만 `PRINTER`는 식별자다. 가장 흔한 처리 방식은 **항상 식별자처럼 읽고, 다 읽고 나서 키워드 표를 조회**하는 것이다. 이렇게 하면 “접두사 일치”의 함정에 걸리지 않는다.

```lua
function Lexer:lex_ident()
  -- 알파벳/숫자를 모두 읽음
  -- ...
  -- 끝났으면 KEYWORDS 테이블 조회
  if KEYWORDS[upper] then emit("KEYWORD", upper)
  else emit("IDENT", upper) end
end
```

### 5.6 대소문자

GW-BASIC은 식별자와 키워드 모두 대소문자를 구분하지 않는다. 우리 어휘 분석기는 IDENT/KEYWORD를 모두 대문자로 정규화한다. 문자열 리터럴은 물론 그대로 둔다.

### 5.7 REM과 ' (apostrophe)

REM은 줄 끝까지 주석이다. 진짜 GW-BASIC은 `'`도 같은 의미로 쓸 수 있지만, 이 책의 구현은 REM만 받아들인다(연습 문제로 추가해 보라).

---

## 6장. 정규 표현식 없이 만드는 어휘 분석기

### 6.1 왜 손으로 짜는가

대부분의 책은 lex/flex/PEG 같은 도구로 어휘 분석기를 생성한다. 이 책은 그러지 않는다. 이유는 단순하다. **손으로 짜야 동작이 머리에 남는다.** 그리고 BASIC의 어휘 규칙은 정규 도구를 쓸 만큼 복잡하지 않다.

### 6.2 인터페이스

```lua
local Lexer = require("lexer")
local toks  = Lexer.new(source_string):tokenize()
```

생성자는 소스 문자열을 받고, `tokenize()`는 토큰 배열을 반환한다. 그 사이에 lexer 객체는 다음의 상태를 가진다.

- `src`  : 입력 문자열
- `pos`  : 현재 위치(1-base)
- `line` : 현재 라인 번호
- `tokens` : 누적 결과

### 6.3 핵심 헬퍼: peek와 advance

```lua
function Lexer:peek(off)
  off = off or 0
  return self.src:sub(self.pos + off, self.pos + off)
end

function Lexer:advance()
  local c = self:peek()
  self.pos = self.pos + 1
  if c == "\n" then self.line = self.line + 1 end
  return c
end
```

`peek(off)`은 위치를 옮기지 않고 현재 위치 + off 의 문자를 본다. `advance()`는 위치를 한 칸 앞으로 옮기며 라인을 갱신한다. 이 두 함수만 있으면 거의 모든 어휘 분석기를 짤 수 있다.

### 6.4 핵심 루프

```lua
function Lexer:tokenize()
  while self.pos <= #self.src do
    self:skip_inline_ws()
    local c = self:peek()
    if c == "" then break
    elseif c == "\n" then self:emit("EOL","\n"); self:advance()
    elseif c == ":"   then self:emit("COLON",":"); self:advance()
    -- ... 그 외 한 글자 토큰들
    elseif c:match("%d") then self:lex_number()
    elseif c == '"'    then self:lex_string()
    elseif c:match("[%a_]") then self:lex_ident()
    else error("알 수 없는 문자: "..c)
    end
  end
  self:emit("EOF","")
  return self.tokens
end
```

이 한 함수가 어휘 분석기의 80%다. 나머지 20%는 숫자/문자열/식별자의 보조 함수들이다.

### 6.5 두 글자 연산자: `<>`, `<=`, `>=`

`<` 하나만 보고 결정해서는 안 된다. 그 다음 글자가 `=`이면 `<=`, `>`이면 `<>`다. 이 처리는 다음과 같이 해결한다.

```lua
elseif c == "<" then
  self:advance()
  if self:peek() == "=" then self:advance(); self:emit("LE","<=")
  elseif self:peek() == ">" then self:advance(); self:emit("NE","<>")
  else self:emit("LT","<")
  end
```

`>` 도 동일한 패턴이다. `>=`, `><`(GW-BASIC은 `<>`와 동치)를 처리한다.

### 6.6 공백 처리

BASIC은 들여쓰기와 무관하지만, 빠르게 “공백/탭/캐리지 리턴”을 건너뛰는 헬퍼가 필요하다.

```lua
function Lexer:skip_inline_ws()
  while true do
    local c = self:peek()
    if c == " " or c == "\t" or c == "\r" then self:advance()
    else break end
  end
end
```

라인 종료 문자 `\n`은 의미가 있으므로 스킵하지 않는다.

### 6.7 ?를 PRINT로 받기

`PRINT`를 `?`로 줄여 쓰는 BASIC 방언이 많다. 우리도 받아들인다.

```lua
elseif c == "?" then self:emit("KEYWORD","PRINT"); self:advance()
```

### 6.8 흔한 실수들

- **무한 루프.** `peek()`만 보고 `advance()`를 빠뜨리면 영원히 같은 자리다. 케이스 추가 시 항상 “이 케이스는 pos를 진행시키는가?”를 확인하자.
- **문자열 종결 누락.** `"hello`만 입력되면 어휘 분석기는 EOF에 닿을 때까지 읽는다. 명시적인 에러를 띄워야 한다.
- **숫자의 부호.** `-1`은 두 토큰(MINUS, NUMBER)이지 한 토큰이 아니다. 부호 처리는 파서의 단항 연산자에서 한다(11장 참고).
- **REM 처리.** REM 다음의 모든 글자는 그 자체로 토큰이 아니라 “무시”다. 줄바꿈이 나올 때까지 advance만 한다.

---

## 7장. 문자열, 숫자 리터럴과 타입 접미어

### 7.1 숫자 리터럴의 형식

GW-BASIC의 숫자 리터럴은 다음 셋을 모두 지원한다.

- 정수: `123`, `0`, `-0`은 `0`과 같다.
- 실수: `3.14`, `.5`(소수점으로 시작), `5.`(소수점으로 끝남)
- 지수: `1.2E3`, `1D-3`(`D`는 배정도 표기)
- 16진수: `&H1F`, 8진수: `&O17`

이 책의 구현은 처음 셋을 모두 받지만, &H/&O는 연습 문제로 남긴다. 또한 타입 접미어 `%`, `!`, `#`을 리터럴 끝에 붙일 수 있다.

```basic
A% = 100
B! = 1.5
C# = 1.234567890123#
```

### 7.2 lex_number 구현

```lua
function Lexer:lex_number()
  local start = self.pos
  while is_digit(self:peek()) do self:advance() end
  if self:peek() == "." then
    self:advance()
    while is_digit(self:peek()) do self:advance() end
  end
  local p = self:peek()
  if p == "e" or p == "E" or p == "d" or p == "D" then
    self:advance()
    if self:peek() == "+" or self:peek() == "-" then self:advance() end
    while is_digit(self:peek()) do self:advance() end
  end
  local p2 = self:peek()
  if p2 == "%" or p2 == "!" or p2 == "#" then self:advance() end
  local text = self.src:sub(start, self.pos - 1)
  text = text:gsub("[dD]", "e"):gsub("[%%!#]$", "")
  self:emit("NUMBER", tonumber(text))
end
```

요점은 **상태 기계처럼 한 부분씩 읽고**, 마지막에 `tonumber`로 한 번에 파싱하는 것이다. 직접 자릿수마다 곱하면 부동소수 오차의 원인이 되므로 표준 변환에 맡기는 편이 안전하다.

### 7.3 문자열 리터럴

```lua
function Lexer:lex_string()
  self:advance() -- 여는 "
  local buf = {}
  while true do
    local c = self:peek()
    if c == "" or c == "\n" then
      error("문자열이 닫히지 않았습니다 (line "..self.line..")")
    elseif c == '"' then
      self:advance(); break
    else
      buf[#buf+1] = c; self:advance()
    end
  end
  self:emit("STRING", table.concat(buf))
end
```

GW-BASIC은 이스케이프 문자를 지원하지 않는다. `"`는 곧 종료다. 이중 따옴표(`""`)를 한 글자로 취급하는 방언도 있지만 표준은 아니다.

### 7.4 타입 접미어 처리의 위치

접미어는 어휘 분석기가 “식별자 토큰의 일부”로 흡수한다. `NAME$`는 한 토큰이며 그 `value`가 `"NAME$"`이다. 이로써 후속 단계는 마지막 글자만 보고 타입을 알 수 있다.

```lua
local kind = name:sub(-1)
-- kind ∈ {"$", "%", "!", "#"} 또는 그 외(단정도 기본)
```

---

## 8장. 키워드와 식별자

### 8.1 키워드 목록

이 책의 인터프리터가 키워드로 인식하는 단어는 다음과 같다.

```
LET, PRINT, INPUT, IF, THEN, ELSE,
GOTO, GOSUB, RETURN,
FOR, TO, STEP, NEXT,
WHILE, WEND,
END, STOP, REM,
DIM, DATA, READ, RESTORE,
DEF, FN, ON,
AND, OR, NOT, MOD, XOR, EQV, IMP,
CLS, RUN, NEW, LIST,
TAB, SPC, USING
```

이 목록은 `lexer.lua`의 `KEYWORDS` 테이블에서 한곳에서 관리한다.

### 8.2 키워드 vs 식별자의 결정

“긴 토큰 우선(longest match)” 원칙이 작동한다. 우리 어휘 분석기는 알파벳/숫자가 이어지는 한 끝까지 읽고, 그 결과 문자열을 키워드 표에서 찾아본다. 그래서 `IFX`는 `IF` + `X`가 아니라 식별자 `IFX`이다. 이는 BASIC의 표준 동작이며, 어떤 BASIC 방언도 “키워드의 접두 일치”를 시도하지 않는다.

### 8.3 REM의 특수성

REM은 어휘 단계에서 줄 끝까지 모든 문자를 삼킨다. 이는 다른 키워드와 다른 점이다.

```lua
if upper == "REM" then
  while self:peek() ~= "\n" and self:peek() ~= "" do self:advance() end
  self:emit("REM","")
  return
end
```

이렇게 하면 REM 뒤에 무엇이 와도 파서를 거치지 않으므로 안전하다. (`100 REM IF THEN GOTO`도 문제없다.)

### 8.4 FN의 특수성

`DEF FN<NAME>(...)`에서 `FN`은 키워드일까, 함수 이름의 일부일까? GW-BASIC은 보통 `FN`을 함수 이름의 접두사로 보고 그 전체를 식별자로 취급한다. 즉 `FNSQR`은 한 식별자다. 그래서 우리 어휘 분석기는 `FN`을 키워드로 등록하지만, **실제 함수 이름과 붙어 있는 경우엔 IDENT가 우선**한다(긴 토큰 우선 원칙). 이 처리에 대해서는 12장 파서에서 다시 다룬다.

### 8.5 어휘 분석기 단위 테스트

`tests/test_lexer.lua` 가 다음과 같다.

```lua
local Lexer = require("lexer")

local function tok(src)
  return Lexer.new(src):tokenize()
end

local t = tok('10 PRINT "HELLO": A% = 1\n')
assert(t[1].type == "NUMBER" and t[1].value == 10)
assert(t[2].type == "KEYWORD" and t[2].value == "PRINT")
assert(t[3].type == "STRING" and t[3].value == "HELLO")
assert(t[4].type == "COLON")
assert(t[5].type == "IDENT" and t[5].value == "A%")
assert(t[6].type == "EQ")
assert(t[7].type == "NUMBER" and t[7].value == 1)
print("lexer ok")
```

이 정도로 골격이 잡혀 있는지 빠르게 검증할 수 있다.

---

# 제3부 — 문법과 파서

## 9장. BNF로 표현하는 GW-BASIC 문법

### 9.1 왜 BNF인가

문법을 자연어로 설명하면 누락이 생긴다. BNF는 “이 언어가 받아들이는 모든 문자열의 모양”을 빠짐없이 정의하는 가장 단순한 도구다. 우리가 만들 BNF는 LL(1)에 가깝고, 재귀 하강 파서로 곧장 코드 변환할 수 있다.

### 9.2 표기 약속

이 책에서 사용하는 BNF 변형은 다음을 따른다.

- `<x>`   : 비단말(non-terminal)
- `"x"`   : 문자/리터럴
- `x | y` : 둘 중 하나
- `x*`    : 0회 이상
- `x+`    : 1회 이상
- `x?`    : 0 또는 1회
- `(x y)` : 묶음

### 9.3 프로그램과 라인

```
<program>     ::= (<line> <eol>)*
<line>        ::= <line-number>? <statement-list>
<line-number> ::= <integer>
<statement-list> ::= <statement> ( ":" <statement> )*
```

GW-BASIC은 한 줄에 콜론(`:`)으로 여러 문장을 이을 수 있다. 라인 번호는 보통 있지만, 이 책의 REPL은 “직접 모드”도 받아들이므로 옵션으로 했다.

### 9.4 문장(Statements)

```
<statement> ::= <let>
              | <print>
              | <input>
              | <if>
              | <for>     | <next>
              | <while>   | <wend>
              | <goto>    | <gosub> | <return>
              | <end>     | <stop>  | <rem>
              | <dim>
              | <data>    | <read>  | <restore>
              | <def-fn>
              | <on-goto>
              | <cls>
```

각 문장의 BNF는 다음 절들에서 정의한다.

### 9.5 단순 문장들

```
<let>     ::= ("LET")? <lvalue> "=" <expr>
<lvalue>  ::= <ident> ( "(" <expr> ( "," <expr> )* ")" )?
<print>   ::= "PRINT" <print-list>?
<print-list> ::= <print-item> ( <print-sep> <print-item>? )*
<print-item> ::= <expr>
              | "TAB" "(" <expr> ")"
              | "SPC" "(" <expr> ")"
<print-sep> ::= "," | ";"
<input>   ::= "INPUT" ( <string> ( ";" | "," ) )? <lvalue> ( "," <lvalue> )*
<goto>    ::= "GOTO" <line-number>
<gosub>   ::= "GOSUB" <line-number>
<return>  ::= "RETURN"
<end>     ::= "END"
<stop>    ::= "STOP"
<rem>     ::= "REM" <any-text>
<cls>     ::= "CLS"
```

“암시적 LET”도 합법적이다. `A = 1`은 `LET A = 1`과 같다.

### 9.6 제어 흐름

```
<if>    ::= "IF" <expr> ( "THEN" | "GOTO" ) <then-branch>
            ( "ELSE" <then-branch> )?
<then-branch> ::= <line-number>          # 단축 GOTO
              |  <statement-list>

<for>   ::= "FOR" <ident> "=" <expr> "TO" <expr> ( "STEP" <expr> )?
<next>  ::= "NEXT" ( <ident> ( "," <ident> )* )?

<while> ::= "WHILE" <expr>
<wend>  ::= "WEND"

<on-goto> ::= "ON" <expr> ( "GOTO" | "GOSUB" )
              <line-number> ( "," <line-number> )*
```

### 9.7 데이터 / 함수

```
<dim>     ::= "DIM" <ident> "(" <expr> ( "," <expr> )* ")"
              ( "," <ident> "(" <expr> ( "," <expr> )* ")" )*
<data>    ::= "DATA" <data-item> ( "," <data-item> )*
<data-item> ::= <number> | <string> | <unquoted-string>
<read>    ::= "READ" <lvalue> ( "," <lvalue> )*
<restore> ::= "RESTORE" <line-number>?
<def-fn>  ::= "DEF" "FN" <ident> ( "(" <ident> ( "," <ident> )* ")" )?
              "=" <expr>
```

### 9.8 표현식 (가장 어려운 부분)

표현식 BNF는 우선순위를 “계층 구조”로 표현한다. 우선순위가 가장 낮은 것이 맨 위에, 가장 높은 것이 맨 아래에 있다.

```
<expr>     ::= <imp-expr>
<imp-expr> ::= <eqv-expr>  ( "IMP" <eqv-expr> )*
<eqv-expr> ::= <xor-expr>  ( "EQV" <xor-expr> )*
<xor-expr> ::= <or-expr>   ( "XOR" <or-expr>  )*
<or-expr>  ::= <and-expr>  ( "OR"  <and-expr> )*
<and-expr> ::= <not-expr>  ( "AND" <not-expr> )*
<not-expr> ::= "NOT"? <rel-expr>
<rel-expr> ::= <add-expr>  ( ( "=" | "<>" | "<" | ">" | "<=" | ">=" ) <add-expr> )?
<add-expr> ::= <mod-expr>  ( ( "+" | "-" ) <mod-expr> )*
<mod-expr> ::= <idiv-expr> ( "MOD" <idiv-expr> )*
<idiv-expr>::= <mul-expr>  ( "\"  <mul-expr>  )*
<mul-expr> ::= <unary>     ( ( "*" | "/" ) <unary> )*
<unary>    ::= ( "-" | "+" )? <power>
<power>    ::= <atom> ( "^" <unary> )?           # 우결합
<atom>     ::= <number>
            | <string>
            | <ident> ( "(" <args>? ")" )?
            | "FN" <ident> ( "(" <args>? ")" )?
            | "(" <expr> ")"
<args>     ::= <expr> ( "," <expr> )*
```

이 트리만 그대로 함수로 옮기면 곧 파서가 된다. 실제 코드(`parser.lua`)에서는 이 계층 대신 “precedence climbing”이라는 한 함수로 단축했다. 동등한 결과지만 코드량이 절반이다(11장 참고).

### 9.9 모호성과 해소

전형적인 모호성이 두 군데 있다.

1. **`-` 의 양면성.** 단항 부호인지 이항 뺄셈인지. 해결: “직전 토큰이 atom의 끝이면 이항, 아니면 단항.”
2. **`(` 의 양면성.** 함수 호출인지 그룹 표현인지. 해결: 직전 토큰이 IDENT이면 호출, 아니면 그룹.

이 두 규칙은 우리 파서에 자연스럽게 녹아 있다.

### 9.10 BNF에서 코드로 가는 다리

BNF의 각 규칙은 같은 이름의 함수가 된다.

- `<expr>`     → `parse_expr()`
- `<add-expr>` → `parse_binop(min_prec=8)`
- `<atom>`     → `parse_atom()`

원본 BNF가 left-recursive(좌재귀)일 때만 형태 변환이 필요하다. 우리는 위에서 이미 left-recursion을 “루프(`*`)”로 표현해 두었으므로 그대로 짤 수 있다.

---

## 10장. 재귀 하강 파서의 뼈대

### 10.1 재귀 하강이란

각 비단말(non-terminal)에 대해 함수를 하나씩 만든다. 그 함수는 직전까지 진행된 위치를 보고, 자신이 책임지는 부분을 소비하며, 결과 AST 노드를 반환한다.

```
parse_X()  # <X> 규칙을 처리하는 함수
```

함수가 AST를 만든다는 점이 핵심이다. 토큰을 단지 통과시키기만 하는 “인식기”가 아니라, 동시에 트리를 짓는 “생성기”다.

### 10.2 파서의 상태

```lua
local Parser = {}
Parser.__index = Parser

function M.new(tokens)
  return setmetatable({ toks = tokens, pos = 1 }, Parser)
end

function Parser:cur()     return self.toks[self.pos] end
function Parser:advance() self.pos = self.pos + 1; return self.toks[self.pos-1] end
function Parser:check(t,v)
  local tk = self:cur()
  if not tk or tk.type ~= t then return false end
  if v ~= nil and tk.value ~= v then return false end
  return true
end
function Parser:accept(t,v) if self:check(t,v) then return self:advance() end end
function Parser:expect(t,v,msg)
  if self:check(t,v) then return self:advance() end
  error(...)
end
```

이 다섯 함수가 파서의 “알파벳”이다.

### 10.3 BNF → 코드의 변환표

| BNF | 코드 |
|---|---|
| `<X> ::= a b c` | `parse_a(); parse_b(); parse_c()` 순차 호출 |
| `<X> ::= a | b` | 첫 토큰을 보고 분기 |
| `<X> ::= a*`   | `while parse_a() do end` |
| `<X> ::= a?`   | `if check then parse_a() end` |

### 10.4 에러 메시지의 품질

파서의 에러 메시지가 좋아야 사용자 경험이 결정된다. 우리 `expect`는 다음과 같은 메시지를 만든다.

```
파서 오류: ) 가 필요한데 EOL(\n)를 만났습니다 (line 30)
```

“무엇을 기대했는지”와 “무엇을 만났는지”를 모두 알리는 것이 비결이다.

### 10.5 Look-ahead 깊이

우리 파서는 LL(1)이지만, 가끔 한 토큰 앞을 더 본다(`peek(1)`). 예: `.5`처럼 점으로 시작하는 숫자.

```lua
elseif c == "." and is_digit(self:peek(1)) then
  self:lex_number()
```

이는 어휘 분석기 차원의 lookahead로, 파서까지 영향을 주지는 않는다.

---

## 11장. 표현식 파서 — Pratt(precedence climbing) 기법

### 11.1 단순 재귀 하강의 한계

표현식의 각 우선순위마다 함수를 하나씩 두면 깔끔하지만, 우선순위가 9~10단이나 되는 GW-BASIC에서는 함수 9~10개를 일일이 짜야 한다. 게다가 우선순위를 하나 추가하려면 코드가 곳곳에서 바뀐다.

### 11.2 Precedence climbing

“현재 최소 우선순위 `min_prec`을 인자로 받아서 한 함수가 모든 이항 연산자를 처리한다”는 발상이다.

```lua
function Parser:parse_binop(min_prec)
  local left = self:parse_unary()
  while true do
    local op, prec = self:peek_binop()
    if not op or prec < min_prec then break end
    self:advance()
    local next_min = is_left(op) and (prec + 1) or prec
    local right = self:parse_binop(next_min)
    left = AST.BinOp(op, left, right)
  end
  return left
end
```

핵심 두 줄:

- `prec < min_prec` → 더 약한 연산자가 나오면 멈추고 위로 반환.
- `next_min = prec + 1` (좌결합) 또는 `prec` (우결합).

이 알고리즘을 처음 보면 신기할 수 있는데, 직접 손으로 한두 표현식을 추적해 보면 명확해진다. 11.5절의 예제로 확인하자.

### 11.3 우선순위 표

```lua
function Parser:peek_binop()
  local t = self:cur()
  if not t then return nil end
  if t.type == "PLUS"      then return "+", 8 end
  if t.type == "MINUS"     then return "-", 8 end
  if t.type == "STAR"      then return "*", 11 end
  if t.type == "SLASH"     then return "/", 11 end
  if t.type == "BACKSLASH" then return "\\", 10 end
  if t.type == "CARET"     then return "^", 13 end
  if t.type == "EQ"        then return "=", 7 end
  if t.type == "NE"        then return "<>", 7 end
  if t.type == "LT"        then return "<", 7 end
  if t.type == "GT"        then return ">", 7 end
  if t.type == "LE"        then return "<=", 7 end
  if t.type == "GE"        then return ">=", 7 end
  if t.type == "KEYWORD" then
    if t.value == "AND" or t.value == "OR" or t.value == "MOD"
       or t.value == "XOR" or t.value == "EQV" or t.value == "IMP" then
      return t.value, PREC[t.value]
    end
  end
end
```

### 11.4 단항과 거듭제곱

```lua
function Parser:parse_unary()
  if self:accept("MINUS") then return AST.UnOp("-", self:parse_unary()) end
  if self:accept("PLUS") then return self:parse_unary() end
  if self:eat_kw("NOT") then return AST.UnOp("NOT", self:parse_unary()) end
  return self:parse_power()
end

function Parser:parse_power()
  local base = self:parse_atom()
  if self:check("CARET") then
    self:advance()
    local exp = self:parse_unary()       -- 우결합!
    return AST.BinOp("^", base, exp)
  end
  return base
end
```

`-2^2`는 `-(2^2) = -4`인가, `(-2)^2 = 4`인가? GW-BASIC은 단항 부호가 거듭제곱보다 약하므로 `-(2^2) = -4`다. 위 코드는 그 의미를 지킨다.

### 11.5 추적 예: `1 + 2 * 3 ^ 2`

목표 트리: `1 + (2 * (3 ^ 2))`.

1. `parse_binop(0)` → `parse_unary()` → atom = `1`
2. peek = `+` (prec 8) ≥ 0 → 소비, `parse_binop(9)` 호출
   1. atom = `2`
   2. peek = `*` (prec 11) ≥ 9 → 소비, `parse_binop(12)` 호출
      1. atom = `3`, parse_power 안에서 `^ 2`까지 처리되어 `3^2`
      2. peek = (다음) → 11 < 12 이므로 정지, 반환 `3^2`
   3. 결과: `2 * (3^2)`. 다음 peek는 끝 → 반환
3. 결과: `1 + (2 * (3^2))`. ✓

### 11.6 단항과 이항의 구분

`A - B`는 이항. `-A`는 단항. 파서가 항상 “표현식을 시작할 때 atom 또는 단항이 와야 한다”는 위치라면 `-`는 단항이고, “이미 atom을 끝냈고 다음 연산자를 본다”라면 `-`는 이항이다. 이 규칙은 코드의 구조(어디서 호출하는가)에 자연스럽게 배어 있다.

---

## 12장. 문장 파서와 라인 번호

### 12.1 라인 단위 처리

```lua
function Parser:parse_program()
  local lines = {}
  while not self:check("EOF") do
    if self:check("EOL") then self:advance()
    else lines[#lines+1] = self:parse_line() end
  end
  return AST.Program(lines)
end

function Parser:parse_line()
  local num
  if self:check("NUMBER") then num = self:advance().value end
  local stmts = self:parse_stmt_list()
  if self:check("EOL") then self:advance() end
  return AST.Line(num, stmts)
end
```

라인 번호는 옵션이지만, 실제 BASIC 프로그램에서는 거의 항상 있다. 라인 번호는 파서 단계에서는 그저 메타데이터지만, 컴파일러에서는 “주소 매핑 테이블”의 키가 된다(16장).

### 12.2 콜론으로 묶인 문장 목록

```lua
function Parser:parse_stmt_list()
  local out = {}
  while not self:check("EOL") and not self:check("EOF") do
    local s = self:parse_stmt()
    if s then out[#out+1] = s end
    if self:accept("COLON") then -- 다음 문장
    else break end
  end
  return out
end
```

이렇게 하면 `10 A=1 : B=2 : PRINT A+B`처럼 콜론으로 이어붙인 BASIC을 자연스럽게 받는다.

### 12.3 문장 디스패처

```lua
function Parser:parse_stmt()
  if self:check("REM") then self:advance(); return AST.Rem() end
  if self:eat_kw("LET")    then return self:parse_let_body() end
  if self:eat_kw("PRINT")  then return self:parse_print() end
  if self:eat_kw("INPUT")  then return self:parse_input() end
  if self:eat_kw("IF")     then return self:parse_if() end
  if self:eat_kw("FOR")    then return self:parse_for() end
  if self:eat_kw("NEXT")   then return self:parse_next() end
  if self:eat_kw("WHILE")  then return AST.While(self:parse_expr()) end
  if self:eat_kw("WEND")   then return AST.Wend() end
  if self:eat_kw("GOTO")   then return AST.Goto(self:expect("NUMBER",nil,"라인 번호").value) end
  if self:eat_kw("GOSUB")  then return AST.Gosub(self:expect("NUMBER",nil,"라인 번호").value) end
  if self:eat_kw("RETURN") then return AST.Return() end
  if self:eat_kw("END")    then return AST.End() end
  if self:eat_kw("STOP")   then return AST.Stop() end
  if self:eat_kw("DIM")    then return self:parse_dim() end
  if self:eat_kw("DATA")   then return self:parse_data() end
  if self:eat_kw("READ")   then return self:parse_read() end
  if self:eat_kw("RESTORE")then return self:parse_restore() end
  if self:eat_kw("DEF")    then return self:parse_def() end
  if self:eat_kw("ON")     then return self:parse_on() end
  if self:eat_kw("CLS")    then return AST.Cls() end
  if self:check("IDENT")   then return self:parse_let_body() end -- 암시적 LET
  return nil
end
```

### 12.4 IF / THEN / ELSE의 세 형태

GW-BASIC의 IF는 다음 세 형태를 모두 받아야 한다.

```basic
IF X > 0 THEN 100              ' 라인 번호 한 개
IF X > 0 GOTO 100              ' GOTO 단축
IF X > 0 THEN PRINT X : Y = 1 ELSE PRINT 0
```

우리 파서는 다음과 같이 처리한다.

```lua
function Parser:parse_if()
  local cond = self:parse_expr()
  if not self:eat_kw("THEN") then
    if not self:eat_kw("GOTO") then error("THEN 또는 GOTO") end
  end
  local then_branch = self:parse_then_branch()
  local else_branch
  if self:eat_kw("ELSE") then else_branch = self:parse_then_branch() end
  return AST.If(cond, then_branch, else_branch)
end

function Parser:parse_then_branch()
  if self:check("NUMBER") then
    return { AST.Goto(self:advance().value) }
  end
  local out = {}
  while true do
    local s = self:parse_stmt()
    if s then out[#out+1] = s end
    if not self:accept("COLON") then break end
    if self:check("EOL") or self:is_kw("ELSE") then break end
  end
  return out
end
```

결과적으로 `IF X>0 THEN 100`은 `then = [Goto(100)]`로 통일된다. 컴파일러가 신경 쓸 게 줄어든다.

### 12.5 FOR / NEXT

```lua
function Parser:parse_for()
  local v = self:expect("IDENT", nil, "변수").value
  self:expect("EQ", nil, "=")
  local s = self:parse_expr()
  if not self:eat_kw("TO") then error("TO") end
  local e = self:parse_expr()
  local step
  if self:eat_kw("STEP") then step = self:parse_expr() end
  return AST.For(v, s, e, step)
end
```

`NEXT`는 변수 이름이 와도 되고 안 와도 된다. 여러 변수를 콤마로 나열할 수 있다(`NEXT I, J`).

### 12.6 DEF FN의 까다로움

가장 짜증나는 케이스는 다음 두 형태가 동시에 합법이라는 점이다.

```basic
DEF FNSQR(X) = X*X
DEF FN SQR(X) = X*X      ' (방언)
```

또한 사용 시점에는 `FNSQR(2)`가 한 식별자로 토큰화된다. 우리는 다음 방식을 채택했다.

- 어휘 분석: `FNSQR`은 IDENT 한 토큰.
- 파서 `parse_def`: DEF 다음의 IDENT가 FN으로 시작하지 않으면 오류. FN 접두를 그대로 둔 채 함수 이름으로 등록한다(즉 “FNSQR”이 키).
- 파서 `parse_atom`: IDENT(args) 형태에서 IDENT가 FN으로 시작하면 `FnCall(name, args)`로 해석한다.

이 설계는 구현이 단순하면서도 BASIC 사용자의 직관에 맞는다.

### 12.7 ON GOTO / ON GOSUB

```lua
function Parser:parse_on()
  local expr = self:parse_expr()
  local kind
  if self:eat_kw("GOTO") then kind = "GOTO"
  elseif self:eat_kw("GOSUB") then kind = "GOSUB"
  else error("ON 다음에 GOTO 또는 GOSUB") end
  local targets = { self:expect("NUMBER",nil,"라인 번호").value }
  while self:accept("COMMA") do
    targets[#targets+1] = self:expect("NUMBER",nil,"라인 번호").value
  end
  return (kind == "GOTO") and AST.OnGoto(expr, targets) or AST.OnGosub(expr, targets)
end
```

식의 값 `n`이 1, 2, 3...일 때 각각 첫 번째, 두 번째, 세 번째 라인 번호로 점프한다. 0이거나 범위를 벗어나면 다음 문장으로 넘어간다(GW-BASIC 동작 규약).

---

# 제4부 — AST와 컴파일러

## 13장. AST 노드 설계

### 13.1 AST는 무엇이고 무엇이 아닌가

추상 구문 트리는 **소스 코드의 의미를 잃지 않은 가장 작은 표현**이다. 공백이나 줄바꿈, 괄호 같은 “전시(display)” 정보는 잃어도 좋고, 의미 보존만이 목표다.

### 13.2 노드의 일관된 모양

이 책의 모든 AST 노드는 다음 두 가지를 만족한다.

- 평범한 Lua 테이블이다.
- `tag` 필드에 노드 종류 문자열이 들어 있다.

```lua
function M.NumLit(v)            return { tag="NumLit",  value=v }     end
function M.BinOp(op, l, r)      return { tag="BinOp",   op=op, left=l, right=r } end
```

이 설계의 장점은 직렬화/덤프가 그냥 동작한다는 것이다(테이블 출력 함수 한 번이면 끝).

### 13.3 노드 카탈로그

#### 프로그램 구조

| 노드 | 필드 |
|---|---|
| Program | lines: Line[] |
| Line | number: int?, stmts: Stmt[] |

#### 문장

| 노드 | 필드 |
|---|---|
| Let | target: Var, expr: Expr |
| Print | items: PrintItem[] |
| Input | prompt: string?, vars: Var[] |
| If | cond: Expr, then_: Stmt[], else_: Stmt[]? |
| For | var: string, start: Expr, stop: Expr, step: Expr? |
| Next | vars: string[] |
| While | cond: Expr |
| Wend | (없음) |
| Goto | target: int |
| Gosub | target: int |
| Return | (없음) |
| End | (없음) |
| Stop | (없음) |
| Rem | (없음) |
| Cls | (없음) |
| Dim | decls: {name,dims:Expr[]}[] |
| Data | values: {kind,value}[] |
| Read | vars: Var[] |
| Restore | target: int? |
| DefFn | name: string, params: string[], body: Expr |
| OnGoto | expr: Expr, targets: int[] |
| OnGosub | expr: Expr, targets: int[] |

#### 표현식

| 노드 | 필드 |
|---|---|
| NumLit | value: number |
| StrLit | value: string |
| Var | name: string, indices: Expr[]? |
| BinOp | op: string, left: Expr, right: Expr |
| UnOp | op: string, operand: Expr |
| Call | name: string, args: Expr[]   (내장 함수 또는 배열) |
| FnCall | name: string, args: Expr[]   (DEF FN) |

#### PRINT 항목

| 노드 | 필드 |
|---|---|
| PrintExpr | expr: Expr |
| PrintSep | kind: "," 또는 ";" |
| PrintTab | expr: Expr |
| PrintSpc | expr: Expr |

### 13.4 “일반 함수 호출”과 “DEF FN 호출”의 분리

언어 차원에서 둘은 완전히 다른 의미가 있다.

- 일반 호출: 컴파일러가 `runtime.is_builtin(name)`을 보고 내장이면 CALLF로, 아니면 배열 ALOAD로 컴파일.
- DEF FN 호출: 항상 CALLU(사용자 함수)로 컴파일.

이를 AST 단계에서 노드 종류로 분리해 두면, 컴파일러가 단순해진다.

### 13.5 AST 덤프 헬퍼

디버깅을 위해 단순한 트리 덤프 함수를 두면 좋다.

```lua
local function dump(node, indent)
  indent = indent or 0
  local pad = string.rep("  ", indent)
  if type(node) ~= "table" then print(pad..tostring(node)); return end
  io.write(pad..(node.tag or "?").."\n")
  for k,v in pairs(node) do
    if k ~= "tag" then
      io.write(pad.."  "..k..":\n")
      dump(v, indent+2)
    end
  end
end
```

(공식 코드에는 들어 있지 않지만, 7부에서 디버그 모드에 추가한다.)

---

## 14장. 바이트코드 명령어 집합 정의

### 14.1 우리 VM의 정체성

이 책의 VM은 **스택 기반**이다. 레지스터 머신(예: Lua 5.0의 새 VM, JVM의 한 변형)이 아니라, 자바 가상 머신·CPython·웹 어셈블리와 같이 임시 결과를 스택에 쌓는다. 학습용으로는 압도적으로 단순하다.

### 14.2 명령어 카테고리

```
[ 상수/변수 ]   PUSHN, PUSHS, LOAD, STORE, POP
[ 배열 ]       DIM, ALOAD, ASTORE
[ 산술 ]       ADD, SUB, MUL, DIV, IDIV, MOD, POW, NEG
[ 비교 ]       EQ, NE, LT, GT, LE, GE
[ 논리/비트 ]  AND, OR, XOR, EQV, IMP, NOT
[ 점프 ]       JMP, JZ, JNZ, GOSUB, RETURN, ONJMP
[ 입출력 ]     PRINT_ITEM, PRINT_NL, PRINT_TAB, PRINT_TAB_TO, PRINT_SPC, INPUT, CLS
[ 데이터 ]     READ, READ_A, RESTORE
[ 함수 ]       CALLF (내장), CALLU (사용자)
[ 종료 ]       HALT
```

### 14.3 표현 형식

명령어는 다음과 같은 Lua 테이블이다.

```lua
{ op = "ADD" }
{ op = "PUSHN", arg = 42 }
{ op = "STORE", arg = "A" }
{ op = "JMP",   arg = 17 }   -- ops 인덱스
{ op = "ALOAD", arg = "M",  arg2 = 2 }   -- 2차원
{ op = "CALLF", arg = "SQR", arg2 = 1 }  -- 인자 1개
{ op = "ONJMP", arg = "GOTO", arg2 = {100,200,300} }
```

대안은 “바이트 배열”이지만, 학습용으로는 테이블이 압도적으로 편하다.

### 14.4 스택 효과 (stack effect)

각 명령은 스택을 어떻게 변형하는가? 이 “스택 효과”를 정의해 두면 컴파일러가 잘 동작하는지 검증할 수 있다.

| 명령 | 입력 → 출력 |
|---|---|
| PUSHN/PUSHS | () → (v) |
| LOAD | () → (v) |
| STORE | (v) → () |
| ADD/SUB/MUL/DIV/...| (a,b) → (a⋆b) |
| NEG/NOT | (a) → (¬a) |
| EQ/NE/... | (a,b) → (bool) |
| ALOAD n | (i1..in) → (v) |
| ASTORE n | (i1..in, v) → () |
| JMP/JZ/JNZ | JZ/JNZ는 (cond) → () |
| GOSUB | () → () (호출 스택만 변경) |
| RETURN | () → () |
| PRINT_ITEM | (v) → () |
| CALLF n / CALLU n | (a1..an) → (v) |

이 표를 등에 새겨 두자. 디버깅의 절반은 “이 명령 후에 스택이 균형 잡혔는가?”를 묻는 것이다.

### 14.5 실행 후의 검증

VM이 종료할 때 스택이 비어 있어야 한다(또는 마지막 결과 하나만 남거나). 그렇지 않다면 컴파일러 또는 명령 정의에 버그가 있다. 테스트에 다음 한 줄을 넣어 두면 좋다.

```lua
assert(#vm.stack == 0, "stack leak: "..#vm.stack)
```

### 14.6 디스어셈블

```
1: PUSHN 1
2: PUSHN 2
3: PUSHN 3
4: MUL
5: ADD
6: STORE A
7: HALT
```

이런 디스어셈블을 출력하는 함수를 한 번만 짜 두면 디버깅이 비약적으로 편해진다(28장에서 추가).

---

## 15장. 표현식 컴파일

### 15.1 핵심 아이디어

표현식 컴파일은 “포스트오더(post-order) 순회”다. 자식 먼저, 자기 자신 나중. 이렇게 하면 자식의 결과가 스택에 쌓인 뒤 자기 연산이 그것을 소비한다.

### 15.2 코드

```lua
function Compiler:compile_expr(e)
  local tag = e.tag
  if tag == "NumLit" then self:emit("PUSHN", e.value); return end
  if tag == "StrLit" then self:emit("PUSHS", e.value); return end
  if tag == "Var" then
    if e.indices then
      for _, idx in ipairs(e.indices) do self:compile_expr(idx) end
      self:emit("ALOAD", e.name, #e.indices)
    else
      self:emit("LOAD", e.name)
    end
    return
  end
  if tag == "BinOp" then
    self:compile_expr(e.left)
    self:compile_expr(e.right)
    -- 연산자 → 명령 매핑
    local m = {
      ["+"]="ADD", ["-"]="SUB", ["*"]="MUL", ["/"]="DIV",
      ["\\"]="IDIV", ["MOD"]="MOD", ["^"]="POW",
      ["="]="EQ", ["<>"]="NE", ["<"]="LT", [">"]="GT",
      ["<="]="LE", [">="]="GE",
      ["AND"]="AND", ["OR"]="OR", ["XOR"]="XOR",
      ["EQV"]="EQV", ["IMP"]="IMP",
    }
    self:emit(m[e.op]); return
  end
  if tag == "UnOp" then
    self:compile_expr(e.operand)
    if e.op == "-" then self:emit("NEG")
    elseif e.op == "NOT" then self:emit("NOT") end
    return
  end
  ...
end
```

### 15.3 함수 호출 컴파일

```lua
if tag == "Call" then
  if runtime.is_builtin(e.name) then
    for _, a in ipairs(e.args) do self:compile_expr(a) end
    self:emit("CALLF", e.name, #e.args)
  else
    -- 배열 인덱싱
    for _, a in ipairs(e.args) do self:compile_expr(a) end
    self:emit("ALOAD", e.name, #e.args)
  end
end
if tag == "FnCall" then
  for _, a in ipairs(e.args) do self:compile_expr(a) end
  self:emit("CALLU", e.name, #e.args)
end
```

이 작은 분기가 “BASIC의 `A(I)`는 함수일 수도, 배열일 수도 있다”는 모호성을 컴파일 시점에 해소한다.

### 15.4 단축 평가

GW-BASIC의 `AND`/`OR`은 비트 연산이지 단축 평가가 아니다. 즉 `A AND B`는 양쪽 모두를 평가한다. 그래서 우리 컴파일러는 양 자식을 모두 컴파일하고 AND/OR 명령을 emit하면 끝이다. 다른 언어의 단축 평가(C, Lua, Python)와 다르므로 주의하자.

### 15.5 표현식 트리 → 명령어 시퀀스

`(1 + 2) * 3`:

```
PUSHN 1
PUSHN 2
ADD
PUSHN 3
MUL
```

`A * (B - C)`:

```
LOAD A
LOAD B
LOAD C
SUB
MUL
```

“스택의 마지막 두 값을 항상 같은 방향으로 소비한다”는 점이 핵심이다. 즉 `SUB`는 `(top-1) - top`이고, `DIV`는 `(top-1) / top`이다. 이 약속은 vm.lua에 있다.

---

## 16장. 제어 흐름 컴파일과 백패치

### 16.1 두 종류의 점프

- **선행 점프(forward jump):** IF/WHILE의 “조건 거짓이면 끝으로” 같은 것. 끝 주소를 아직 모른다.
- **후방 점프(backward jump):** FOR/WHILE의 “루프 처음으로” 같은 것. 시작 주소를 이미 안다.

전자는 “백패치(backpatch)”가 필요하다. 일단 0(또는 더미)으로 emit해 두고, 나중에 주소가 결정되면 채워 넣는다.

### 16.2 IF의 컴파일

```lua
function Compiler:compile_if(s)
  self:compile_expr(s.cond)
  local jz = self:emit("JZ", 0)              -- 미지의 끝 주소
  for _, st in ipairs(s.then_) do self:compile_stmt(st) end
  if s.else_ then
    local jmp_end = self:emit("JMP", 0)
    self:patch(jz, "arg", self:current_addr())
    for _, st in ipairs(s.else_) do self:compile_stmt(st) end
    self:patch(jmp_end, "arg", self:current_addr())
  else
    self:patch(jz, "arg", self:current_addr())
  end
end
```

핵심은 `emit`이 인덱스를 반환한다는 점, 그리고 그 인덱스를 잡고 있다가 `patch`로 채워 넣는다는 점이다.

### 16.3 FOR/NEXT의 컴파일

FOR/NEXT는 두 점에서 까다롭다. (1) STEP의 부호에 따라 종료 조건이 다르고, (2) 중첩이 흔해서 “FOR/NEXT 짝”을 컴파일러가 추적해야 한다.

```lua
function Compiler:compile_for(s)
  local v = s.var
  self:compile_expr(s.start); self:emit("STORE", v)
  self:compile_expr(s.stop);  self:emit("STORE", "__LIMIT_"..v)
  if s.step then self:compile_expr(s.step) else self:emit("PUSHN", 1) end
  self:emit("STORE", "__STEP_"..v)
  local top = self:current_addr()
  -- step * (i - limit) <= 0 이면 계속
  self:emit("LOAD", "__STEP_"..v)
  self:emit("LOAD", v)
  self:emit("LOAD", "__LIMIT_"..v)
  self:emit("SUB"); self:emit("MUL"); self:emit("PUSHN", 0); self:emit("LE")
  local jz = self:emit("JZ", 0)
  self.for_stack[#self.for_stack+1] = { var=v, top=top, exit_jz=jz }
end
```

종료 검사식 `step * (i - limit) <= 0`은 부호와 무관하게 동작한다.

- step > 0: i ≤ limit ↔ i - limit ≤ 0 ↔ step*(i-limit) ≤ 0
- step < 0: i ≥ limit ↔ i - limit ≥ 0 ↔ step*(i-limit) ≤ 0

```lua
function Compiler:compile_next(s)
  local vars = #s.vars > 0 and s.vars or { nil }
  for _, vname in ipairs(vars) do
    local frame = table.remove(self.for_stack)
    if not frame then error("NEXT 짝이 없음") end
    if vname and vname ~= frame.var then error("NEXT "..vname.." vs FOR "..frame.var) end
    self:emit("LOAD", frame.var)
    self:emit("LOAD", "__STEP_"..frame.var)
    self:emit("ADD")
    self:emit("STORE", frame.var)
    self:emit("JMP", frame.top)
    self:patch(frame.exit_jz, "arg", self:current_addr())
  end
end
```

`for_stack`은 컴파일 시점의 스택일 뿐, 런타임 스택과는 다르다. NEXT가 이 스택에서 가장 최근 FOR 프레임을 꺼내 짝을 맺는다.

### 16.4 라인 번호 → 주소

GOTO/GOSUB는 “라인 번호로” 점프하지만, VM은 “명령 주소로” 점프한다. 이 변환을 컴파일러가 한다.

```lua
function Compiler:compile_program(prog)
  for _, line in ipairs(prog.lines) do
    if line.number then self.line_addr[line.number] = self:current_addr() end
    for _, st in ipairs(line.stmts) do self:compile_stmt(st) end
  end
  self:emit("HALT")
  -- pending GOTO/GOSUB 백패치
  for _, p in ipairs(self.pending_gotos) do
    local target = self.line_addr[p.line]
    if not target then error("Undefined line "..p.line) end
    self.ops[p.addr].arg = target
  end
  ...
end
```

라인 번호가 “미래의 라인”이라면 컴파일 시점에 그 라인 주소를 모른다. 그래서 일단 GOTO/GOSUB을 0으로 emit하고 “보류 목록”에 적어 둔다. 모든 라인이 컴파일된 뒤 보류 목록을 순회하면서 채운다. 이것이 “선형 스캔 백패치”다.

### 16.5 ON GOTO의 컴파일

ON GOTO는 “식의 값에 따라 N개 라인 중 하나로”다. 우리는 ONJMP라는 단일 명령으로 처리한다.

```lua
function Compiler:compile_on(s, op)
  self:compile_expr(s.expr)
  self:emit("ONJMP", op, s.targets) -- targets는 라인 번호 배열
end
```

VM에서는 식의 값을 받아 해당 라인의 주소를 line_addr에서 찾아 점프한다(20장 참고). 이 변환이 “런타임에 매번 일어나는 비용”이지만 ON GOTO는 자주 쓰지 않으므로 무방하다.

### 16.6 컴파일러 상태와 청소

컴파일러는 다음 상태를 누적한다.

- `ops`: 명령 배열
- `line_addr`: 라인번호 → ops 주소
- `data`: 평탄화된 DATA 항목들
- `data_line_addr`: 라인번호 → 데이터 인덱스(RESTORE의 라인 번호 인자용)
- `fns`: DEF FN 정의 테이블
- `pending_gotos`: 보류 점프
- `for_stack`, `while_stack`: 컴파일 시점 스택

컴파일이 끝나면 `bytecode = { ops, line_addr, data, data_line_addr, fns }`만 VM에 넘긴다. 컴파일 시 임시 상태(`pending_gotos`, `for_stack`)는 외부에 새지 않는다.

---

# 제5부 — 가상 머신

## 17장. 스택 기반 VM의 구조

### 17.1 VM이 가진 것들

```lua
{
  bc          = bytecode,
  ip          = 1,             -- 명령 포인터
  stack       = {},            -- 데이터 스택
  call_stack  = {},            -- GOSUB 복귀 주소
  vars        = {},            -- 스칼라 변수
  arrays      = {},            -- 배열
  data_ptr    = 1,             -- 다음 READ 위치
  print_col   = 0,             -- 현재 컬럼
  halted      = false,
  zone_width  = 14,
  line_width  = 80,
}
```

이 구조 하나면 GW-BASIC 프로그램을 돌리기에 충분하다. 추가 디버그 정보(call stack snapshots, breakpoints)는 28장에서 확장한다.

### 17.2 메인 루프

```lua
function VM:run()
  local ops = self.bc.ops
  while not self.halted and self.ip <= #ops do
    local op = ops[self.ip]
    self.ip = self.ip + 1
    self:exec(op)
  end
end

function VM:exec(op)
  local h = self.handlers[op.op]
  if not h then error("Unknown opcode: "..op.op) end
  h(self, op)
end
```

핸들러는 큰 테이블 `VM.handlers`에 op 이름으로 등록되어 있다. 디스패치 한 줄로 끝난다.

### 17.3 점프와 ip의 약속

핸들러 호출 *전에* `ip`를 1 증가시켰다는 점이 중요하다. 즉 `JMP` 핸들러는 `op.arg`를 그대로 ip에 대입하면 된다(+1할 필요 없음).

```lua
H.JMP = function(vm, op) vm.ip = op.arg end
H.JZ  = function(vm, op)
  local v = vm:pop()
  if not runtime.truthy(v) then vm.ip = op.arg end
end
```

GOSUB는 “복귀 주소”로 현재 ip를 그대로 저장하면 된다(이미 +1이 된 상태이므로 다음 명령부터 재개).

```lua
H.GOSUB = function(vm, op)
  vm.call_stack[#vm.call_stack+1] = vm.ip
  vm.ip = op.arg
end
```

### 17.4 산술 명령들

```lua
local function num2(vm)
  local b = tonum(vm:pop())
  local a = tonum(vm:pop())
  return a, b
end

H.ADD = function(vm)
  local b = vm:pop(); local a = vm:pop()
  if type(a) == "string" or type(b) == "string" then
    vm:push(tostring(a)..tostring(b))
  else
    vm:push(a + b)
  end
end
H.SUB  = function(vm) local a,b=num2(vm); vm:push(a-b) end
H.MUL  = function(vm) local a,b=num2(vm); vm:push(a*b) end
H.DIV  = function(vm) local a,b=num2(vm); if b==0 then error("Division by zero") end; vm:push(a/b) end
H.IDIV = function(vm) local a,b=num2(vm); vm:push(math.floor(a/b)) end
H.MOD  = function(vm) local a,b=num2(vm); vm:push(a - math.floor(a/b)*b) end
H.POW  = function(vm) local a,b=num2(vm); vm:push(a^b) end
H.NEG  = function(vm) vm:push(-tonum(vm:pop())) end
```

ADD가 문자열을 받으면 자동으로 연결로 빠진다. 이는 GW-BASIC의 동작과 일치한다(`"AB"+"CD" = "ABCD"`).

### 17.5 비교 결과의 표현

GW-BASIC은 “참=−1, 거짓=0”이라는 약속을 따른다. C와 Lua의 “참=1”과 다르다. 그래서 우리 비교 핸들러는 다음 헬퍼를 쓴다.

```lua
function M.bool(b) if b then return -1 else return 0 end end
```

JZ는 “스택 값이 거짓(0/공문자열)일 때 점프”다. GW-BASIC식 −1은 거짓이 아니므로 IF에서 −1은 ‘참’으로 작동한다. 이는 다음 truthy 정의와 맞물린다.

```lua
function M.truthy(v)
  if type(v) == "number" then return v ~= 0 end
  if type(v) == "string" then return v ~= "" end
  return false
end
```

### 17.6 문자열의 경우

문자열은 `EQ`/`NE`/`LT`/`GT`에서 Lua의 비교 연산자가 그대로 동작한다(사전식). `ADD`만 자동 연결로 변환된다. 다른 산술은 Lua에서 에러를 내는데, 우리는 명시적인 BASIC식 “Type mismatch” 메시지로 잡지 않고 Lua 에러를 통과시킨다(필요하다면 `tonum`이 0을 반환하므로 sane한 결과가 나온다).

---

## 18장. 변수와 환경

### 18.1 단순한 환경

GW-BASIC은 일반적으로 “전역 변수만” 가진다. DEF FN의 매개변수만 함수 호출 동안 임시로 그림자(shadow)할 뿐이다. 그래서 우리 환경은 단순 평면 테이블이다.

```lua
self.vars  = {}   -- 스칼라
self.arrays= {}   -- 배열 (자기만의 데이터/차원 정보를 갖는다)
```

### 18.2 미정의 변수의 기본값

GW-BASIC은 정의되지 않은 변수에 접근해도 에러가 아니다. 기본값이 자동으로 들어 있다.

- 숫자 변수: 0
- 문자열 변수: ""

```lua
function VM:default_var(name)
  if name:sub(-1) == "$" then return "" else return 0 end
end

function VM:get_var(name)
  if self.vars[name] ~= nil then return self.vars[name] end
  return self:default_var(name)
end
```

### 18.3 타입 강제

대입 시점에 변수의 접미어와 값의 타입이 맞지 않으면 강제 변환한다. `runtime.coerce_for_var`가 이 일을 한다.

```lua
function M.coerce_for_var(name, value)
  local k = M.var_kind(name)
  if k == "string" then
    if type(value) == "number" then error("Type mismatch") end
    return value
  else
    if type(value) == "string" then error("Type mismatch") end
    if k == "int" then return math.floor(value + 0.5) end
    return value
  end
end
```

### 18.4 변수 이름과 표시

내부적으로 변수 이름은 “접미어 포함, 대문자”로 통일되어 있다. 즉 `a$`도 `A$`로 저장된다. 사용자가 `Print A$` 또는 `print a$`로 써도 같은 변수다.

### 18.5 “기본 단정도”의 함의

`A`, `B`처럼 접미어 없는 변수는 단정도 실수다. Lua에서는 이를 그저 `number`로 표현한다. 단/배 정도의 구분은 BASIC 차원에서만 의미가 있으므로, 우리는 통합 처리한다(정밀도 차이는 무시).

---

## 19장. GOSUB / RETURN 호출 스택

### 19.1 GOSUB의 의미

GOSUB은 “지금 위치를 기억하고 라인 N으로 점프”다. RETURN은 “마지막 GOSUB이 기억해 둔 위치로 돌아가기”다. 함수 호출과 의미가 비슷하지만, 인자나 반환값이 없다는 점에서 더 단순하다.

### 19.2 호출 스택의 구현

```lua
self.call_stack = {}

H.GOSUB = function(vm, op)
  vm.call_stack[#vm.call_stack+1] = vm.ip   -- 현재 ip(다음 명령)
  vm.ip = op.arg
end

H.RETURN = function(vm)
  local ret = table.remove(vm.call_stack)
  if not ret then error("RETURN without GOSUB") end
  vm.ip = ret
end
```

이게 전부다. 스택이라는 자료구조가 “중첩 호출”을 자연스럽게 허용해 준다.

### 19.3 GOSUB 없는 RETURN

```basic
10 RETURN
```

이런 프로그램은 곧장 에러다. 우리 핸들러는 빈 스택에서 `table.remove`가 nil을 반환하므로 명시적으로 검사한다.

### 19.4 ON GOSUB

ON GOSUB은 GOSUB과 같이 호출 스택을 사용하면서, 식의 값으로 분기한다.

```lua
H.ONJMP = function(vm, op)
  local n = math.floor(tonum(vm:pop()) + 0.5)
  if n < 1 or n > #op.arg2 then return end
  local target = vm.bc.line_addr[op.arg2[n]]
  if op.arg == "GOSUB" then
    vm.call_stack[#vm.call_stack+1] = vm.ip
  end
  vm.ip = target
end
```

### 19.5 RETURN N 변형

GW-BASIC은 `RETURN <line>`을 통해 “복귀를 무시하고 새 라인으로 가기”도 지원한다. 우리 구현은 받지 않는다(연습 문제).

### 19.6 “주의해야 할 패턴”

GOSUB 안에서 GOSUB 없이 GOTO로 바깥으로 빠져나가면, 호출 스택에 “고스트 프레임”이 남는다. GW-BASIC은 이 동작을 방치하며, 결국 RETURN에서 잘못된 위치로 돌아가게 된다. BASIC 프로그래머는 이 함정을 알고 피한다. 우리 VM도 따로 보호하지 않는다.

---

## 20장. 배열, DIM, 그리고 다차원 인덱스

### 20.1 BASIC 배열의 약속

- 인덱스는 0-base. `DIM A(10)`은 인덱스 0~10, 총 11칸.
- 다차원 가능. `DIM M(3, 4)`는 4×5 = 20칸.
- DIM 없이 사용하면 자동으로 `DIM 10`이 된다(각 차원 10).

### 20.2 데이터 표현

```lua
self.arrays[name] = {
  dims = {n1, n2, ...},   -- 각 차원의 최댓값
  data = {...},           -- 평탄화된 1차원 Lua 테이블
  base = 0,               -- (옵션) OPTION BASE는 미구현
}
```

평탄화된 인덱스는 row-major 순서로 계산한다.

```lua
function VM:linear_index(arr, idxs)
  local idx = 0
  for i = 1, #idxs do
    local d = arr.dims[i]
    local k = math.floor(idxs[i] + 0.5)
    if k < 0 or k > d then error("Subscript out of range") end
    idx = idx * (d + 1) + k
  end
  return idx + 1                       -- Lua의 1-base
end
```

### 20.3 DIM 명령

```lua
H.DIM = function(vm, op)
  local n = op.arg2
  local dims = {}
  for i = n, 1, -1 do dims[i] = math.floor(vm:pop() + 0.5) end
  vm:dim_array(op.arg, dims)
end

function VM:dim_array(name, dims)
  local total = 1
  for _,d in ipairs(dims) do total = total * (d + 1) end
  local data = {}
  local fill = self:default_var(name)
  for i=1,total do data[i] = fill end
  self.arrays[name] = { dims = dims, data = data, base = 0 }
end
```

### 20.4 자동 DIM

DIM 없이 `A(5)`로 처음 접근하면 어떻게 할까? GW-BASIC은 자동으로 DIM 10을 한다.

```lua
function VM:ensure_array(name, ndims)
  if self.arrays[name] then return self.arrays[name] end
  local dims = {}
  for i=1,ndims do dims[i] = 10 end
  self:dim_array(name, dims)
  return self.arrays[name]
end
```

이 함수가 ALOAD/ASTORE/READ_A에서 모두 호출된다.

### 20.5 ALOAD / ASTORE

```lua
H.ALOAD = function(vm, op)
  local n = op.arg2
  local idxs = {}
  for i = n, 1, -1 do idxs[i] = vm:pop() end
  local arr = vm:ensure_array(op.arg, n)
  vm:push(arr.data[vm:linear_index(arr, idxs)])
end
H.ASTORE = function(vm, op)
  local n = op.arg2
  local val = vm:pop()
  local idxs = {}
  for i = n, 1, -1 do idxs[i] = vm:pop() end
  local arr = vm:ensure_array(op.arg, n)
  val = runtime.coerce_for_var(op.arg, val)
  arr.data[vm:linear_index(arr, idxs)] = val
end
```

여기서 “인덱스 먼저, 값 나중”의 스택 순서 약속이 보인다. 컴파일러도 이 순서로 emit한다(15장).

### 20.6 ReDIM

GW-BASIC은 한 배열을 한 번만 DIM할 수 있다. 두 번째 DIM은 “Duplicate definition” 에러다. 우리 구현은 단순히 덮어쓴다(연습 문제로 검사를 추가하라).

---

# 제6부 — 런타임과 내장 함수

## 21장. PRINT의 의외로 깊은 세계

### 21.1 PRINT의 두 분리자

GW-BASIC의 PRINT는 두 가지 분리자(`,`와 `;`)와 두 가지 항목 함수(`TAB`, `SPC`)를 갖는다. 그리고 마지막에 분리자가 *없으면* 줄바꿈, *있으면* 줄바꿈 안 함이다.

| 식 | 결과 (• = 공백) |
|---|---|
| `PRINT "A"; "B"` | `AB` 줄바꿈 |
| `PRINT "A", "B"` | `A•••••••••••••B` 줄바꿈 (다음 영역으로) |
| `PRINT "A";` | `A` 줄바꿈 *없음* |
| `PRINT 3` | `•3•` 줄바꿈 (양수 앞 공백, 뒤 공백) |

### 21.2 숫자 출력의 BASIC 규칙

숫자는 양수일 때 앞에 한 칸 공백, 그리고 항상 뒤에 한 칸 공백이 붙는다. 음수일 때는 앞 공백 자리에 `-`가 들어가고, 뒤 공백은 그대로다.

```lua
function M.basic_tostring(v)
  if type(v) == "string" then return v end
  if v ~= v then return "NaN" end
  if v == math.huge then return "INF" end
  if v == -math.huge then return "-INF" end
  if v == math.floor(v) and math.abs(v) < 1e15 then
    local s = tostring(math.floor(v))
    if v >= 0 then return " "..s.." " else return s.." " end
  end
  local s = string.format("%.7g", v)
  if v >= 0 then return " "..s.." " else return s.." " end
end
```

이 함수가 `PRINT_ITEM` 핸들러의 핵심이다.

### 21.3 컬럼 추적

`,`로 다음 “zone”으로 이동하려면 현재 컬럼을 알아야 한다. 우리 VM은 `print_col`을 갱신한다.

```lua
function VM:print_str(s)
  if self.output then self.output(s)
  else io.write(s) end
  for i=1,#s do
    local c = s:sub(i,i)
    if c == "\n" then self.print_col = 0
    else self.print_col = self.print_col + 1 end
  end
end
```

### 21.4 PRINT_TAB / PRINT_TAB_TO

- `,`(콤마): `PRINT_TAB` — 다음 14의 배수 컬럼으로 이동.
- `TAB(n)`: `PRINT_TAB_TO` — 컬럼 n으로 이동(이미 지나갔으면 다음 줄).

```lua
H.PRINT_TAB = function(vm)
  local col = vm.print_col
  local next_zone = math.floor(col / vm.zone_width) * vm.zone_width + vm.zone_width
  if next_zone >= vm.line_width then vm:newline()
  else vm:print_str(string.rep(" ", next_zone - col)) end
end

H.PRINT_TAB_TO = function(vm)
  local target = math.floor(tonum(vm:pop()))
  if target < 1 then target = 1 end
  if vm.print_col >= target then vm:newline() end
  vm:print_str(string.rep(" ", target - 1 - vm.print_col))
end
```

### 21.5 SPC(n)

단순히 n칸의 공백을 찍는다. 컬럼은 그만큼 증가.

```lua
H.PRINT_SPC = function(vm)
  local n = math.floor(tonum(vm:pop()))
  if n > 0 then vm:print_str(string.rep(" ", n)) end
end
```

### 21.6 “마지막에 분리자가 있으면 줄바꿈 없음” 구현

이 의미는 컴파일러가 처리한다. 마지막 항목이 분리자이면 PRINT_NL을 emit하지 않는다.

```lua
function Compiler:compile_print(s)
  local last_was_sep = false
  for _, item in ipairs(s.items) do
    if item.tag == "PrintExpr" then
      self:compile_expr(item.expr); self:emit("PRINT_ITEM")
      last_was_sep = false
    elseif item.tag == "PrintSep" then
      if item.kind == "," then self:emit("PRINT_TAB") end
      last_was_sep = true
    elseif item.tag == "PrintTab" then
      self:compile_expr(item.expr); self:emit("PRINT_TAB_TO")
      last_was_sep = true
    elseif item.tag == "PrintSpc" then
      self:compile_expr(item.expr); self:emit("PRINT_SPC")
      last_was_sep = true
    end
  end
  if not last_was_sep then self:emit("PRINT_NL") end
end
```

---

## 22장. INPUT, DATA, READ

### 22.1 INPUT 한 줄 받기

```lua
H.INPUT = function(vm, op)
  local prompt = op.arg or ""
  if prompt == "" or not prompt then prompt = "? " else prompt = prompt .. "? " end
  local line
  if vm.input then line = vm.input(prompt)
  else
    io.write(prompt); io.flush()
    line = io.read("*l") or ""
  end
  local name = op.arg2
  if name:sub(-1) == "$" then vm:set_var(name, line)
  else vm:set_var(name, tonumber(line) or 0) end
end
```

테스트 가능성을 위해 `vm.input`이 주입되어 있으면 그것을 쓰고, 아니면 표준 입력으로 폴백한다.

### 22.2 INPUT 다중 변수

`INPUT A, B, C`는 “쉼표로 구분된 한 줄에서 세 값을 채운다”는 의미가 정석이지만, 우리 구현은 “각 변수마다 별도 prompt”의 단순 버전이다. 진짜 GW-BASIC 호환을 원하면 한 줄을 읽고 쉼표 분리로 채우는 코드를 추가하면 된다.

### 22.3 DATA / READ / RESTORE

DATA는 컴파일 시 평탄화되어 `bytecode.data` 배열에 들어간다. READ는 `data_ptr`을 진행시키며 변수에 채운다.

```lua
H.READ = function(vm, op)
  local item = vm.bc.data[vm.data_ptr]
  if not item then error("Out of DATA") end
  vm.data_ptr = vm.data_ptr + 1
  local name = op.arg
  if name:sub(-1) == "$" then vm:set_var(name, tostring(item.value))
  else
    if item.kind == "number" then vm:set_var(name, item.value)
    else vm:set_var(name, tonumber(item.value) or 0) end
  end
end
H.RESTORE = function(vm, op)
  if op.arg then vm.data_ptr = vm.bc.data_line_addr[op.arg] or 1
  else vm.data_ptr = 1 end
end
```

### 22.4 RESTORE의 라인 번호

`RESTORE 200`은 “라인 200의 DATA부터 다시 시작”이다. 이를 위해 컴파일러는 “이 라인의 첫 DATA 항목이 평탄화 배열에서 몇 번째인지”를 따로 기록한다(`data_line_addr`).

---

## 23장. 수학·문자열 내장 함수

### 23.1 함수 등록

`runtime.lua`의 `M.builtins` 테이블에 모든 내장 함수가 들어 있다.

```lua
B.SQR  = function(_, a) return math.sqrt(tonum(a[1])) end
B.LEN  = function(_, a) return #tostr(a[1]) end
B["LEFT$"] = function(_, a) return tostr(a[1]):sub(1, tonum(a[2])) end
...
```

이름은 대문자로 정규화한다(`runtime.is_builtin`이 `:upper()`로 비교).

### 23.2 수학 함수 카탈로그

| 함수 | 의미 |
|---|---|
| ABS(x) | 절댓값 |
| SGN(x) | 부호 (-1, 0, 1) |
| INT(x) | 내림 |
| FIX(x) | 0 방향 자르기 |
| SQR(x) | 제곱근 |
| EXP(x) | e^x |
| LOG(x) | 자연로그 |
| SIN, COS, TAN, ATN | 삼각/역탄젠트 |
| RND | 0~1 난수 |

### 23.3 문자열 함수 카탈로그

| 함수 | 의미 |
|---|---|
| LEN(s$) | 길이 |
| LEFT$(s$, n) | 왼쪽 n자 |
| RIGHT$(s$, n) | 오른쪽 n자 |
| MID$(s$, i [,n]) | i번째부터 n자 (i는 1-base) |
| CHR$(n) | 코드 → 1자 문자열 |
| ASC(s$) | 1자 → 코드 |
| STR$(n) | 숫자 → 문자열 |
| VAL(s$) | 문자열 → 숫자 |
| SPACE$(n) | n칸 공백 |
| STRING$(n, ch) | ch를 n번 반복 |
| INSTR([start,] s$, t$) | t$의 위치 (없으면 0) |
| UCASE$, LCASE$ | 대/소문자 |

### 23.4 시간/시스템 함수

| 함수 | 의미 |
|---|---|
| TIMER | 시스템 시간 (초) |
| DATE$ | 현재 날짜 |
| TIME$ | 현재 시각 |

### 23.5 호출 컨벤션

내장 함수 시그니처는 `function(vm, args_table)`이다. `args_table`은 위치 인자 배열. 반환값 하나(또는 없음). VM의 CALLF 핸들러가 다음과 같이 호출한다.

```lua
H.CALLF = function(vm, op)
  local argc = op.arg2
  local args = {}
  for i = argc, 1, -1 do args[i] = vm:pop() end
  vm:push(runtime.call(op.arg, vm, args))
end
```

인자를 “뒤에서 앞으로” 꺼내서 `args[i]`에 넣는 패턴은 스택 머신 컴파일러의 표준이다(컴파일러가 인자를 왼→오 순서로 push했으므로 pop하면 오→왼이고, 이를 다시 뒤집어 올바른 순서로 만든다).

### 23.6 새 함수 추가하기

함수 추가는 다음 두 곳만 건드리면 된다.

1. `runtime.lua`의 `B` 테이블에 함수 등록.
2. (선택) 키워드/예약어로 막히지 않는지 확인.

예: `B.HEX$ = function(_,a) return string.format("%X", tonum(a[1])) end`

---

## 24장. DEF FN과 사용자 정의 함수

### 24.1 DEF FN의 의미

`DEF FN<name>(p1, p2, ...) = expr`은 한 줄짜리 함수다. 본문은 항상 표현식 하나다. 호출 시 매개변수에 인자를 바인드하고 식을 평가한다.

### 24.2 등록과 호출

```lua
-- 컴파일러:
if tag == "DefFn" then
  self.fns[s.name:upper()] = { params = s.params, expr = s.body }
  return
end
```

DEF FN은 바이트코드에 “명령”을 emit하지 않고, 컴파일 시점에 등록만 한다. 호출 시점에 본문 식을 즉석으로 평가한다.

```lua
H.CALLU = function(vm, op)
  local fn = vm.bc.fns[op.arg:upper()]
  if not fn then error("Undefined FN") end
  local argc = op.arg2
  local args = {}
  for i = argc, 1, -1 do args[i] = vm:pop() end
  -- 매개변수 그림자
  local saved = {}
  for i, p in ipairs(fn.params) do saved[p] = vm.vars[p]; vm.vars[p] = args[i] end
  local result = vm:eval_expr_ast(fn.expr)
  for p, v in pairs(saved) do vm.vars[p] = v end
  vm:push(result)
end
```

### 24.3 본문이 AST인 이유

DEF FN의 본문을 컴파일하지 않고 AST 그대로 두는 이유는 “호출 시 매개변수 환경을 따로 잡아야” 하기 때문이다. 본문을 별도의 함수로 컴파일해 두고 호출 규약(calling convention)을 만드는 것도 가능하지만, 한 줄짜리 식이라는 본질을 살리면 즉석 평가가 충분하다.

### 24.4 재귀

매개변수의 그림자가 “지역화”되어 있으므로 재귀도 동작한다.

```basic
10 DEF FNFACT(N) = (N <= 1) * 1 + (N > 1) * N * FNFACT(N-1)
20 PRINT FNFACT(5)
```

(이 표현식은 “비교의 결과가 −1/0”인 BASIC식 트릭이다. `(N>1) = -1`이므로 부호를 다시 뒤집는 등의 보정이 필요할 수 있다. GW-BASIC식 IF 없는 한 줄 함수 정의의 묘미.)

### 24.5 한계

- 본문은 한 식이어야 한다. 여러 줄 함수는 GOSUB을 써야 한다.
- 매개변수가 빠지면 컴파일 시 등록만 되고 사용 시점에 GW-BASIC은 “오른쪽의 모든 변수가 매개변수”인 것처럼 동작한다(우리 구현은 빈 매개변수 리스트를 그대로 유지). 

---

# 제7부 — 통합과 확장

## 25장. REPL 만들기

### 25.1 REPL의 책임

- 사용자가 한 줄을 친다.
- 라인 번호로 시작하면 “저장”, 아니면 “즉시 실행”.
- `RUN`이면 누적된 라인을 컴파일하고 실행.
- `LIST`면 저장된 라인을 출력.
- `NEW`면 모두 비움.

### 25.2 단순 구현

```lua
local function repl()
  print("LuaGW-BASIC 1.0")
  local lines = {}
  while true do
    io.write("Ok\n> "); io.flush()
    local line = io.read("*l")
    if not line then break end
    if line:upper() == "BYE" or line:upper() == "QUIT" then break end
    if line:upper() == "RUN" then
      local src = table.concat(lines, "\n")
      local ok, err = pcall(function()
        local bc = compile_source(src); VM.new(bc):run()
      end)
      if not ok then print("Error: "..tostring(err)) end
    elseif line:upper() == "LIST" then
      for _, l in ipairs(lines) do print(l) end
    elseif line:upper() == "NEW" then
      lines = {}
    elseif line:match("^%s*%d") then
      lines[#lines+1] = line
    else
      local ok, err = pcall(function()
        local bc = compile_source(line); VM.new(bc):run()
      end)
      if not ok then print("Error: "..tostring(err)) end
    end
  end
end
```

### 25.3 라인 번호 정렬

진짜 GW-BASIC은 라인이 추가될 때 번호 순서로 정렬한다. 우리 단순 REPL은 입력 순서대로 보관하지만, RUN 시점에 라인 번호 순으로 정렬해서 컴파일하면 더 충실해진다.

### 25.4 라인 수정

같은 라인 번호로 다시 입력하면 기존 라인을 대체한다. 우리는 이 기능을 의도적으로 단순화했다(연습 문제).

---

## 26장. 파일 로더와 LIST/RUN/NEW

### 26.1 파일 형식

GW-BASIC은 두 형식의 .BAS를 가진다.

- **ASCII 형식**: 평범한 텍스트.
- **토큰화 형식**: 0xFF로 시작하는 바이너리.

우리는 ASCII만 지원한다. 토큰화 디코더 작성은 좋은 연습 문제다.

### 26.2 파일 로딩

```lua
local function run_file(path)
  local f = io.open(path, "r")
  local src = f:read("*a")
  f:close()
  local bc = compile_source(src)
  VM.new(bc):run()
end
```

### 26.3 SAVE/LOAD를 REPL에 추가하기

라인을 파일로 저장하고 다시 읽는 명령은 다음과 같다.

```lua
elseif cmd:upper():match("^SAVE ") then
  local name = cmd:match('^SAVE%s+"(.+)"')
  local f = io.open(name, "w")
  for _, l in ipairs(lines) do f:write(l, "\n") end
  f:close()
elseif cmd:upper():match("^LOAD ") then
  ...
```

이 책의 베이스라인 코드에는 들어 있지 않다(연습 문제).

---

## 27장. 에러 처리와 ON ERROR GOTO

### 27.1 에러의 양상

GW-BASIC의 에러는 “Error N at line M”로 표시되며, ON ERROR GOTO로 핸들러를 등록할 수 있다.

### 27.2 우리 인터프리터의 에러

우리는 Lua의 `pcall`을 활용해 에러를 잡는다.

```lua
local ok, err = pcall(function() vm:run() end)
if not ok then
  io.stderr:write("실행 오류: "..tostring(err).."\n")
end
```

라인 번호를 함께 표시하려면 VM에 “현재 실행 중인 라인” 추적이 필요하다. 컴파일러가 “라인 시작 명령”에 라인 번호를 메타데이터로 붙이거나, 별도의 `addr_to_line` 역방향 테이블을 만들면 된다.

### 27.3 ON ERROR GOTO 구현 스케치

VM에 `error_handler_addr` 필드를 추가하고, `pcall`로 잡은 에러를 그 주소로 점프시킨다. RESUME은 GOSUB의 RETURN처럼 이전 ip로 복귀한다. 이 책의 베이스라인 코드에는 포함되지 않았다.

---

## 28장. 성능, 디버그, 다음 단계

### 28.1 성능의 큰 그림

작은 BASIC 프로그램은 우리 VM에서도 충분히 빠르다. 그러나 백만 단위 반복을 도는 프로그램은 다음 최적화를 고려해 볼 만하다.

1. **변수 인덱스화.** 변수 이름 문자열을 숫자 슬롯으로 바꾼다. 컴파일러가 “이름 → 슬롯” 매핑을 만들고, LOAD/STORE는 슬롯 번호로 바뀐다.
2. **상수 풀.** 자주 쓰는 숫자/문자열을 상수 풀에 모아 인덱스로 참조. 명령어가 더 작아진다.
3. **상수 폴딩.** `1 + 2 * 3`처럼 정적으로 평가 가능한 식은 컴파일 시에 결과로 치환.
4. **분기 평탄화.** FOR/NEXT의 검사식을 단일 명령(`FOR_TEST`)로 융합.

### 28.2 디버그 모드

다음 옵션을 main에 추가하면 디버깅이 훨씬 쉬워진다.

```sh
lua main.lua --dump-tokens prog.bas
lua main.lua --dump-ast    prog.bas
lua main.lua --dump-bc     prog.bas
lua main.lua --trace       prog.bas
```

`--trace`는 매 명령 실행 전에 ip와 스택 상태를 한 줄로 출력한다.

### 28.3 다음 단계

이 책을 마친 독자가 도전해 볼 만한 주제 목록:

- ON ERROR GOTO / RESUME의 완전한 구현
- PRINT USING 포맷팅
- OPEN/CLOSE/INPUT#/PRINT# (시퀀셜 파일 I/O)
- LINE INPUT
- 그래픽 명령 (LINE, CIRCLE, PSET) — 별도의 캔버스 백엔드 필요
- &H/&O 진수 리터럴
- OPTION BASE 0/1
- 토큰화된 .BAS 파일 디코더

이상의 모든 기능은 이 책의 골격에 “명령 한 둘 추가, 핸들러 한 둘 추가” 정도로 붙는다.

---

# 제8부 — 한 줄씩 따라가기

## 29장. fib.bas의 전 생애 추적

이 장에서는 8줄짜리 BASIC 프로그램이 우리 인터프리터의 다섯 단계를 통과해 결과까지 도달하는 모든 과정을 한 명령씩 따라간다. 짧은 시간 동안 “단계가 분리되어 있다”는 것이 무슨 의미인지 체감하게 될 것이다.

### 29.1 입력 프로그램

```basic
10 N = 7
20 A = 0 : B = 1
30 FOR I = 2 TO N
40   C = A + B : A = B : B = C
50 NEXT I
60 PRINT B
70 END
```

기대 출력: `13` (피보나치 7번째).

### 29.2 토큰 (lexer 출력 일부)

```
NUMBER(10) IDENT(N) EQ NUMBER(7) EOL
NUMBER(20) IDENT(A) EQ NUMBER(0) COLON IDENT(B) EQ NUMBER(1) EOL
NUMBER(30) KEYWORD(FOR) IDENT(I) EQ NUMBER(2) KEYWORD(TO) IDENT(N) EOL
NUMBER(40) IDENT(C) EQ IDENT(A) PLUS IDENT(B) COLON
           IDENT(A) EQ IDENT(B) COLON IDENT(B) EQ IDENT(C) EOL
NUMBER(50) KEYWORD(NEXT) IDENT(I) EOL
NUMBER(60) KEYWORD(PRINT) IDENT(B) EOL
NUMBER(70) KEYWORD(END) EOL
EOF
```

### 29.3 AST (parser 출력 요약)

```
Program
└─ Line(10) Let(N, 7)
└─ Line(20) Let(A, 0); Let(B, 1)
└─ Line(30) For(I, 2, Var(N), nil)
└─ Line(40) Let(C, A+B); Let(A, B); Let(B, C)
└─ Line(50) Next(I)
└─ Line(60) Print(Var(B))
└─ Line(70) End
```

### 29.4 바이트코드 (compiler 출력 핵심)

라인 번호 → 주소 매핑은 다음과 같다.

```
line 10 → addr 1
line 20 → addr 3
line 30 → addr 7
line 40 → addr 17
line 50 → addr 25
line 60 → addr 33
line 70 → addr 36
```

코드 (압축된 형태):

```
 1 PUSHN 7         ; 10: N=7
 2 STORE N

 3 PUSHN 0         ; 20: A=0
 4 STORE A
 5 PUSHN 1         ;     B=1
 6 STORE B

 7 PUSHN 2         ; 30: FOR I = 2 TO N
 8 STORE I
 9 LOAD  N
10 STORE __LIMIT_I
11 PUSHN 1
12 STORE __STEP_I
13 LOAD __STEP_I   ; 루프 검사
14 LOAD I
15 LOAD __LIMIT_I
16 SUB; MUL; PUSHN 0; LE; JZ 32

17 LOAD A          ; 40: C = A + B
18 LOAD B
19 ADD
20 STORE C
21 LOAD B          ;     A = B
22 STORE A
23 LOAD C          ;     B = C
24 STORE B

25 LOAD I          ; 50: NEXT (= I += STEP; jmp top)
26 LOAD __STEP_I
27 ADD
28 STORE I
29 JMP 13

32 LOAD B          ; 60: PRINT B
33 PRINT_ITEM
34 PRINT_NL

35 HALT             ; 70: END
36 HALT
```

(주: 위 주소들은 설명을 위해 간소화한 것이다. 실제 emit 결과는 `--dump-bc` 옵션으로 정확히 확인할 수 있다.)

### 29.5 VM 트레이스 (요약)

| ip | op | stack 변화 후 | vars |
|---:|---|---|---|
| 1 | PUSHN 7 | (7) | |
| 2 | STORE N | () | N=7 |
| 3 | PUSHN 0 | (0) | |
| 4 | STORE A | () | A=0 |
| 5 | PUSHN 1 | (1) | |
| 6 | STORE B | () | B=1 |
| 7 | PUSHN 2 | (2) | |
| 8 | STORE I | () | I=2 |
| 9 | LOAD N | (7) | |
| 10 | STORE __LIMIT_I | () | __LIMIT_I=7 |
| 11 | PUSHN 1 | (1) | |
| 12 | STORE __STEP_I | () | __STEP_I=1 |
| 13 | LOAD __STEP_I | (1) | |
| 14 | LOAD I | (1, 2) | |
| 15 | LOAD __LIMIT_I | (1, 2, 7) | |
| 16 | SUB | (1, -5) | |
| 17 | MUL | (-5) | |
| 18 | PUSHN 0; LE | (-1) | (참=-1) |
| 19 | JZ 32 | () | (참 → 점프 안 함) |
| ... | (루프 본문 6회) | ... | A=8, B=13 |
| 32+ | LOAD B; PRINT_ITEM; PRINT_NL | | 화면에 ` 13 ` |
| | HALT | | 종료 |

이런 표를 직접 만들어 보는 것이 “인터프리터를 이해했다”의 가장 분명한 시험이다.

### 29.6 실험: 추적을 켜고 직접 보자

`vm.lua`의 `run` 함수에 다음 한 줄을 임시로 넣으면 위 표가 자동으로 만들어진다.

```lua
function VM:run()
  local ops = self.bc.ops
  while not self.halted and self.ip <= #ops do
    local op = ops[self.ip]
    -- DEBUG:
    io.stderr:write(("[%d] %s %s\n"):format(self.ip, op.op, tostring(op.arg or "")))
    self.ip = self.ip + 1
    self:exec(op)
  end
end
```

실험이 끝나면 한 줄을 지우면 된다. 이 정도 즉흥 디버깅이 부담 없는 것이 “수제 인터프리터”의 매력이다.

---

## 30장. 흔한 함정과 디버깅 패턴

### 30.1 “스택이 비어 있는데 왜 RETURN이 뜨나?”

증상: `Error: RETURN without GOSUB`.

원인 후보:

1. GOSUB으로 들어가지 않은 코드가 RETURN에 도달.
2. GOSUB 안에서 GOTO로 “함수 밖”으로 빠져나갔는데 그 라인 어딘가에 RETURN이 있음.
3. ON GOSUB의 식의 값이 범위 밖이라 점프하지 않았는데, 라인이 그대로 흘러내려가다 RETURN을 만남.

대응: 컴파일 시 “GOSUB 진입 깊이”를 정적으로 추적하지는 않는다. 런타임 에러로 잡고, 라인 번호와 함께 표시한다.

### 30.2 “Subscript out of range”

배열 인덱스가 차원 범위를 벗어났다. 가장 흔한 원인은 자동 DIM의 기본값 10에 익숙해진 코드가 11번째 칸을 쓰려 한 경우. 명시적인 `DIM A(N)`로 의도를 분명히 하자.

### 30.3 무한 FOR 루프

`FOR I = 1 TO 10 STEP 0` 같은 코드는 무한 루프다. 우리 종료식 `step*(i-limit) <= 0`도 0을 곱하므로 `<= 0`이 항상 참, 즉 영원히 돈다. 정확히 BASIC의 정의된 동작이지만, 사용자가 의도하지 않았을 가능성이 크다.

### 30.4 “타입 미스매치” 잡기

`A$ = 1`이나 `A = "X"`는 명시적 에러를 띄운다(`runtime.coerce_for_var`). 이 에러가 의외로 도움이 된다 — 변수 이름의 접미어를 잘못 쓴 경우를 대부분 잡는다.

### 30.5 코드 모듈별 디버깅 진입점

| 증상 | 들여다 볼 모듈 |
|---|---|
| 입력 자체가 안 읽힘 | `lexer.lua` |
| 토큰은 맞는데 “파서 오류” | `parser.lua` |
| 실행은 되는데 결과가 이상 | `vm.lua` 핸들러 |
| 라인 번호 점프가 잘못됨 | `compiler.lua`의 `pending_gotos` / `line_addr` |
| PRINT 포맷이 어긋남 | `runtime.basic_tostring`, `vm.lua`의 PRINT_TAB |

### 30.6 “바이트코드를 의심하라”

대부분의 실수는 컴파일러에서 발생한다. 의심스러우면 `--dump-bc`로 코드를 출력한 뒤 한 줄씩 손으로 추적하자. 표현식이 여러 항인데 오퍼레이터가 하나만 emit되었다거나, 백패치를 잊었다거나 하는 “시각적으로 명백한” 버그가 대부분이다.

### 30.7 단위 테스트로 회귀 막기

이 책의 `tests/run_all.lua`는 24개의 미니 어서션을 실행한다. 새 기능을 추가할 때마다 한두 줄짜리 테스트를 더하라. “느린 회귀”는 100줄짜리 큰 테스트가 아니라 1줄짜리 작은 테스트가 잡는다. 테스트 추가의 마찰을 0에 가깝게 유지하는 것이 인터프리터 품질의 비밀이다.

```lua
run_expect("10 PRINT 7 MOD 3\n", " 1 \n")
```

이 한 줄이 MOD 연산자의 회귀를 영원히 잡아 준다.

---

## 31장. 연습 문제

각 문제는 독립적으로 풀 수 있게 설계되었다. 별표(★)는 난이도다.

### 31.1 입문

1. ★ `'`(작은따옴표)도 REM처럼 줄 끝까지 주석으로 동작하게 어휘 분석기를 고쳐라.
2. ★ `&H1F`(16진수)와 `&O17`(8진수) 리터럴을 인식하라. 결과는 NUMBER 토큰.
3. ★ PRINT의 마지막 항목이 `,`이면 “다음 영역으로 이동”하지만 줄바꿈은 하지 않는다. 이 동작을 검증하는 테스트를 추가하라.
4. ★ `?`만으로 한 줄 PRINT를 받는 동작이 이미 있다. `?A`, `?A,B` 등에서도 잘 동작하는지 확인하라.

### 31.2 중급

5. ★★ `DEF FN`의 본문을 컴파일러가 “전용 라인”으로 컴파일하도록 바꾸어 보라(즉 일반 호출처럼 CALL 명령으로 해소). 이때의 함수 호출 규약을 정의하라.
6. ★★ `RESUME`(ON ERROR GOTO와 함께 쓰는 명령)을 구현하라.
7. ★★ `LINE INPUT A$`(콤마 포함, 한 줄 통째로 읽기)를 구현하라.
8. ★★ `WHILE`/`WEND`만 있고 “WHILE 0이면 들어가지도 않는다”는 동작이 있다. WHILE이 0인 케이스 테스트를 추가하라.

### 31.3 고급

9. ★★★ 컴파일러가 “상수 폴딩”을 수행하도록 만들라. 즉 `1 + 2 * 3` 같은 식은 컴파일 시 `7`로 치환된다.
10. ★★★ 변수 이름을 “슬롯 인덱스”로 컴파일하라. 즉 LOAD/STORE의 인자가 문자열이 아니라 정수 슬롯 번호가 된다. 이로써 hash 룩업을 배열 인덱싱으로 줄인다.
11. ★★★ `ON ERROR GOTO`의 완전한 구현. VM에 “현재 ip를 라인으로 매핑”하는 역방향 테이블을 둔다.
12. ★★★ 토큰화된 .BAS 파일(첫 바이트 0xFF) 디코더를 작성하여 평문으로 변환한 뒤 우리 컴파일러로 보낸다.

### 31.4 도전

13. ★★★★ 그래픽 명령(`SCREEN`, `LINE`, `CIRCLE`, `PSET`, `COLOR`)을 별도의 캔버스 백엔드(예: SDL2 바인딩이나 LÖVE2D)와 연결하라.
14. ★★★★ 우리 VM을 LuaJIT의 FFI로 바꿔서 “레지스터 머신”으로 재작성하고 벤치마크를 비교하라.
15. ★★★★ 우리 BASIC을 Lua 함수로 “트랜스파일”하여 LuaJIT가 JIT할 수 있도록 만들라.

### 31.5 작은 실용 과제

- “끝맺음 사인”(End-of-program)에서 `Ok`를 한 줄 출력해 진짜 GW-BASIC 분위기를 흉내내라.
- REPL에서 라인 번호를 입력해 같은 번호의 라인을 대체/삭제할 수 있도록 만들라.
- `SAVE "name.bas"`, `LOAD "name.bas"`를 REPL에 추가하라.
- `RUN`을 입력했을 때 변수와 호출 스택을 비우는지 확인하라(이는 기본 동작이어야 한다).

연습 문제의 모든 정답을 한 권에 담을 수는 없지만, 책의 깃 저장소에는 일부 풀이가 `solutions/` 디렉터리로 추가될 예정이다.

---

# 부록

## 부록 A — 전체 BNF

```ebnf
<program>     ::= ( <line> <eol> )*
<line>        ::= <line-number>? <statement-list>
<line-number> ::= <integer>
<statement-list> ::= <statement> ( ":" <statement> )*

<statement> ::= <let> | <print> | <input> | <if>
              | <for> | <next> | <while> | <wend>
              | <goto> | <gosub> | <return>
              | <end> | <stop> | <rem>
              | <dim> | <data> | <read> | <restore>
              | <def-fn> | <on-goto> | <cls>

<let>     ::= ( "LET" )? <lvalue> "=" <expr>
<lvalue>  ::= <ident> ( "(" <expr> ( "," <expr> )* ")" )?

<print>   ::= "PRINT" <print-list>?
<print-list> ::= <print-item> ( <print-sep> <print-item>? )*
<print-item> ::= <expr>
              | "TAB" "(" <expr> ")"
              | "SPC" "(" <expr> ")"
<print-sep>  ::= "," | ";"

<input>   ::= "INPUT" ( <string> ( ";" | "," ) )?
              <lvalue> ( "," <lvalue> )*

<if>      ::= "IF" <expr> ( "THEN" | "GOTO" ) <then-branch>
              ( "ELSE" <then-branch> )?
<then-branch> ::= <line-number> | <statement-list>

<for>     ::= "FOR" <ident> "=" <expr> "TO" <expr> ( "STEP" <expr> )?
<next>    ::= "NEXT" ( <ident> ( "," <ident> )* )?

<while>   ::= "WHILE" <expr>
<wend>    ::= "WEND"

<goto>    ::= "GOTO" <line-number>
<gosub>   ::= "GOSUB" <line-number>
<return>  ::= "RETURN"
<end>     ::= "END"
<stop>    ::= "STOP"
<rem>     ::= "REM" <any-text>
<cls>     ::= "CLS"

<dim>     ::= "DIM" <ident> "(" <expr> ( "," <expr> )* ")"
              ( "," <ident> "(" <expr> ( "," <expr> )* ")" )*

<data>      ::= "DATA" <data-item> ( "," <data-item> )*
<data-item> ::= <number> | <string> | <unquoted-string>

<read>    ::= "READ" <lvalue> ( "," <lvalue> )*
<restore> ::= "RESTORE" <line-number>?

<def-fn>  ::= "DEF" "FN" <ident>
              ( "(" <ident> ( "," <ident> )* ")" )? "=" <expr>

<on-goto> ::= "ON" <expr> ( "GOTO" | "GOSUB" )
              <line-number> ( "," <line-number> )*

<expr>     ::= <imp-expr>
<imp-expr> ::= <eqv-expr>  ( "IMP" <eqv-expr> )*
<eqv-expr> ::= <xor-expr>  ( "EQV" <xor-expr> )*
<xor-expr> ::= <or-expr>   ( "XOR" <or-expr>  )*
<or-expr>  ::= <and-expr>  ( "OR"  <and-expr> )*
<and-expr> ::= <not-expr>  ( "AND" <not-expr> )*
<not-expr> ::= "NOT"? <rel-expr>
<rel-expr> ::= <add-expr>  ( ( "=" | "<>" | "<" | ">" | "<=" | ">=" )
                              <add-expr> )?
<add-expr> ::= <mod-expr>  ( ( "+" | "-" ) <mod-expr> )*
<mod-expr> ::= <idiv-expr> ( "MOD" <idiv-expr> )*
<idiv-expr>::= <mul-expr>  ( "\"  <mul-expr>  )*
<mul-expr> ::= <unary>     ( ( "*" | "/" ) <unary> )*
<unary>    ::= ( "-" | "+" )? <power>
<power>    ::= <atom> ( "^" <unary> )?
<atom>     ::= <number> | <string>
            | <ident> ( "(" <args>? ")" )?
            | "FN" <ident> ( "(" <args>? ")" )?
            | "(" <expr> ")"
<args>     ::= <expr> ( "," <expr> )*

<ident>   ::= <letter> ( <letter> | <digit> )* ( "$" | "%" | "!" | "#" )?
<number>  ::= <digit>+ ( "." <digit>* )? ( ( "E" | "D" ) ( "+" | "-" )? <digit>+ )?
<string>  ::= '"' <any-char-except-quote-or-newline>* '"'
<eol>     ::= "\n"
```

---

## 부록 B — 바이트코드 명령어 사전

| 명령 | arg | arg2 | 스택 효과 | 설명 |
|---|---|---|---|---|
| HALT | — | — | — | VM 종료 |
| PUSHN | 숫자 | — | () → (n) | 숫자 푸시 |
| PUSHS | 문자열 | — | () → (s) | 문자열 푸시 |
| LOAD | 변수명 | — | () → (v) | 변수 읽기 |
| STORE | 변수명 | — | (v) → () | 변수 쓰기 |
| POP | — | — | (v) → () | 한 칸 버리기 |
| ALOAD | 배열명 | ndims | (i1..in) → (v) | 배열 읽기 |
| ASTORE | 배열명 | ndims | (i1..in,v) → () | 배열 쓰기 |
| DIM | 배열명 | ndims | (d1..dn) → () | 배열 차원 선언 |
| ADD | — | — | (a,b) → (a+b 또는 연결) | |
| SUB / MUL / DIV / IDIV / MOD / POW / NEG | — | — | 산술 | |
| EQ / NE / LT / GT / LE / GE | — | — | (a,b) → (-1/0) | 비교 |
| AND / OR / XOR / EQV / IMP / NOT | — | — | 비트 논리 | |
| JMP | 주소 | — | () → () | 무조건 점프 |
| JZ | 주소 | — | (v) → () | v가 거짓이면 점프 |
| JNZ | 주소 | — | (v) → () | v가 참이면 점프 |
| GOSUB | 주소 | — | () → () | 호출 스택 push 후 점프 |
| RETURN | — | — | () → () | 호출 스택 pop |
| ONJMP | "JMP"\|"GOSUB" | 라인배열 | (n) → () | n번째 라인으로 |
| PRINT_ITEM | — | — | (v) → () | 값 출력 |
| PRINT_NL | — | — | () → () | 줄바꿈 |
| PRINT_TAB | — | — | () → () | 다음 영역으로 |
| PRINT_TAB_TO | — | — | (n) → () | 컬럼 n으로 |
| PRINT_SPC | — | — | (n) → () | n칸 공백 |
| INPUT | prompt | 변수명 | () → () | 입력 받기 |
| READ | 변수명 | — | () → () | DATA에서 읽기 |
| READ_A | 배열명 | ndims | (i1..in) → () | 배열에 READ |
| RESTORE | 라인번호? | — | () → () | data 포인터 리셋 |
| CALLF | 함수명 | argc | (a1..an) → (v) | 내장 호출 |
| CALLU | 함수명 | argc | (a1..an) → (v) | DEF FN 호출 |
| CLS | — | — | () → () | 화면 지우기 |

---

## 부록 C — 전체 Lua 소스 코드

이 절은 6개 모듈의 전체 소스를 그대로 싣는다. 책에서 단편적으로 인용된 코드의 출처이며, 그대로 복사해도 동작한다.

### C.1 lexer.lua

```lua
-- lexer.lua : GW-BASIC 어휘 분석기 (Lua 5.1 호환)
-- 입력: 소스 문자열
-- 출력: 토큰 배열 { {type=..., value=..., line=...}, ... }

local M = {}

local KEYWORDS = {
  LET=true, PRINT=true, INPUT=true,
  IF=true, THEN=true, ELSE=true,
  GOTO=true, GOSUB=true, RETURN=true,
  FOR=true, TO=true, STEP=true, NEXT=true,
  WHILE=true, WEND=true,
  END=true, STOP=true, REM=true,
  DIM=true, DATA=true, READ=true, RESTORE=true,
  DEF=true, FN=true, ON=true,
  AND=true, OR=true, NOT=true, MOD=true, XOR=true,
  CLS=true, RUN=true, NEW=true, LIST=true,
  TAB=true, SPC=true, USING=true,
  PRINT_HASH=false, -- placeholder
}

local function is_digit(c) return c and c:match("%d") ~= nil end
local function is_alpha(c) return c and c:match("[%a_]") ~= nil end
local function is_alnum(c) return c and c:match("[%w_]") ~= nil end

local Lexer = {}
Lexer.__index = Lexer

function M.new(source)
  return setmetatable({
    src = source,
    pos = 1,
    line = 1,
    col = 1,
    tokens = {},
    at_line_start = true,
  }, Lexer)
end

function Lexer:peek(off)
  off = off or 0
  return self.src:sub(self.pos + off, self.pos + off)
end

function Lexer:advance()
  local c = self:peek()
  self.pos = self.pos + 1
  if c == "\n" then
    self.line = self.line + 1
    self.col = 1
  else
    self.col = self.col + 1
  end
  return c
end

function Lexer:emit(t, v)
  self.tokens[#self.tokens+1] = { type = t, value = v, line = self.line }
end

function Lexer:skip_inline_ws()
  while true do
    local c = self:peek()
    if c == " " or c == "\t" or c == "\r" then
      self:advance()
    else
      break
    end
  end
end

function Lexer:lex_number()
  local start = self.pos
  while is_digit(self:peek()) do self:advance() end
  local is_float = false
  if self:peek() == "." then
    is_float = true
    self:advance()
    while is_digit(self:peek()) do self:advance() end
  end
  local p = self:peek()
  if p == "e" or p == "E" or p == "d" or p == "D" then
    is_float = true
    self:advance()
    if self:peek() == "+" or self:peek() == "-" then self:advance() end
    while is_digit(self:peek()) do self:advance() end
  end
  -- 타입 접미어 (선택)
  local p2 = self:peek()
  if p2 == "%" or p2 == "!" or p2 == "#" then self:advance() end
  local text = self.src:sub(start, self.pos - 1)
  -- 'D'를 'E'로 치환 (배정도 → 단일 표기로)
  text = text:gsub("[dD]", "e")
  -- 접미어 제거
  text = text:gsub("[%%!#]$", "")
  self:emit("NUMBER", tonumber(text))
end

function Lexer:lex_string()
  self:advance() -- 여는 따옴표
  local buf = {}
  while true do
    local c = self:peek()
    if c == "" or c == "\n" then
      error("문자열이 닫히지 않았습니다 (line "..self.line..")")
    elseif c == '"' then
      self:advance()
      break
    else
      buf[#buf+1] = c
      self:advance()
    end
  end
  self:emit("STRING", table.concat(buf))
end

function Lexer:lex_ident()
  local start = self.pos
  while is_alnum(self:peek()) do self:advance() end
  -- 변수 타입 접미어
  local p = self:peek()
  local suffix = ""
  if p == "$" or p == "%" or p == "!" or p == "#" then
    suffix = self:advance()
  end
  local raw = self.src:sub(start, self.pos - 1)
  local upper = raw:upper()
  -- 키워드 처리
  if KEYWORDS[upper:gsub("[%$%%!#]$", "")] then
    local kw = upper:gsub("[%$%%!#]$", "")
    if kw == "REM" then
      -- REM 은 줄 끝까지 무시
      while self:peek() ~= "\n" and self:peek() ~= "" do self:advance() end
      self:emit("REM", "")
      return
    end
    self:emit("KEYWORD", kw)
    return
  end
  self:emit("IDENT", upper) -- GW-BASIC 식별자는 대소문자 무시
end

function Lexer:tokenize()
  while self.pos <= #self.src do
    self:skip_inline_ws()
    local c = self:peek()
    if c == "" then break
    elseif c == "\n" then
      self:emit("EOL", "\n")
      self:advance()
    elseif c == ":" then self:emit("COLON",":"); self:advance()
    elseif c == ";" then self:emit("SEMI",";"); self:advance()
    elseif c == "," then self:emit("COMMA",","); self:advance()
    elseif c == "(" then self:emit("LPAREN","("); self:advance()
    elseif c == ")" then self:emit("RPAREN",")"); self:advance()
    elseif c == "+" then self:emit("PLUS","+"); self:advance()
    elseif c == "-" then self:emit("MINUS","-"); self:advance()
    elseif c == "*" then self:emit("STAR","*"); self:advance()
    elseif c == "/" then self:emit("SLASH","/"); self:advance()
    elseif c == "\\" then self:emit("BACKSLASH","\\"); self:advance()
    elseif c == "^" then self:emit("CARET","^"); self:advance()
    elseif c == "?" then self:emit("KEYWORD","PRINT"); self:advance() -- ? 는 PRINT 약식
    elseif c == "=" then self:emit("EQ","="); self:advance()
    elseif c == "<" then
      self:advance()
      if self:peek() == "=" then self:advance(); self:emit("LE","<=")
      elseif self:peek() == ">" then self:advance(); self:emit("NE","<>")
      else self:emit("LT","<") end
    elseif c == ">" then
      self:advance()
      if self:peek() == "=" then self:advance(); self:emit("GE",">=")
      elseif self:peek() == "<" then self:advance(); self:emit("NE","<>")
      else self:emit("GT",">") end
    elseif is_digit(c) then
      self:lex_number()
    elseif c == "." and is_digit(self:peek(1)) then
      self:lex_number()
    elseif c == '"' then
      self:lex_string()
    elseif is_alpha(c) then
      self:lex_ident()
    else
      error("알 수 없는 문자 '"..c.."' (line "..self.line..")")
    end
  end
  self:emit("EOF","")
  return self.tokens
end

return M

```

### C.2 ast.lua

```lua
-- ast.lua : AST 노드 생성 헬퍼
-- 모든 노드는 단순 테이블이며, 'tag' 필드로 종류를 구분한다.

local M = {}

local function node(tag, t)
  t = t or {}
  t.tag = tag
  return t
end

function M.Program(lines)            return node("Program",   {lines=lines}) end
function M.Line(num, stmts)          return node("Line",      {number=num, stmts=stmts}) end

-- 문장 (Statements)
function M.Let(target, expr)         return node("Let",       {target=target, expr=expr}) end
function M.Print(items)              return node("Print",     {items=items}) end
function M.Input(prompt, vars)       return node("Input",     {prompt=prompt, vars=vars}) end
function M.If(cond, t, e)            return node("If",        {cond=cond, then_=t, else_=e}) end
function M.For(var, s, e, st)        return node("For",       {var=var, start=s, stop=e, step=st}) end
function M.Next(vars)                return node("Next",      {vars=vars}) end
function M.While(cond)               return node("While",     {cond=cond}) end
function M.Wend()                    return node("Wend",      {}) end
function M.Goto(target)              return node("Goto",      {target=target}) end
function M.Gosub(target)             return node("Gosub",     {target=target}) end
function M.Return()                  return node("Return",    {}) end
function M.End()                     return node("End",       {}) end
function M.Stop()                    return node("Stop",      {}) end
function M.Rem()                     return node("Rem",       {}) end
function M.Dim(decls)                return node("Dim",       {decls=decls}) end
function M.Data(values)              return node("Data",      {values=values}) end
function M.Read(vars)                return node("Read",      {vars=vars}) end
function M.Restore(target)           return node("Restore",   {target=target}) end
function M.DefFn(name, params, body) return node("DefFn",     {name=name, params=params, body=body}) end
function M.OnGoto(expr, targets)     return node("OnGoto",    {expr=expr, targets=targets}) end
function M.OnGosub(expr, targets)    return node("OnGosub",   {expr=expr, targets=targets}) end
function M.Cls()                     return node("Cls",       {}) end

-- 표현식 (Expressions)
function M.NumLit(v)                 return node("NumLit",    {value=v}) end
function M.StrLit(v)                 return node("StrLit",    {value=v}) end
function M.Var(name, indices)        return node("Var",       {name=name, indices=indices}) end
function M.BinOp(op, l, r)           return node("BinOp",     {op=op, left=l, right=r}) end
function M.UnOp(op, e)               return node("UnOp",      {op=op, operand=e}) end
function M.Call(name, args)          return node("Call",      {name=name, args=args}) end
function M.FnCall(name, args)        return node("FnCall",    {name=name, args=args}) end -- 사용자 DEF FN

-- PRINT 항목 표현
function M.PrintExpr(expr)           return node("PrintExpr", {expr=expr}) end
function M.PrintSep(kind)            return node("PrintSep",  {kind=kind}) end -- "," 또는 ";"
function M.PrintTab(expr)            return node("PrintTab",  {expr=expr}) end
function M.PrintSpc(expr)            return node("PrintSpc",  {expr=expr}) end

return M

```

### C.3 parser.lua

```lua
-- parser.lua : GW-BASIC 재귀 하강 파서
-- 토큰 → AST

local AST = require("ast")
local M = {}

local Parser = {}
Parser.__index = Parser

function M.new(tokens)
  return setmetatable({ toks = tokens, pos = 1 }, Parser)
end

function Parser:peek(off) return self.toks[self.pos + (off or 0)] end
function Parser:cur()     return self.toks[self.pos] end
function Parser:advance() self.pos = self.pos + 1; return self.toks[self.pos-1] end

function Parser:check(t, v)
  local tk = self:cur()
  if not tk then return false end
  if tk.type ~= t then return false end
  if v ~= nil and tk.value ~= v then return false end
  return true
end

function Parser:accept(t, v)
  if self:check(t, v) then return self:advance() end
end

function Parser:expect(t, v, msg)
  if self:check(t, v) then return self:advance() end
  local cur = self:cur() or {type="?",value="?",line=-1}
  error(("파서 오류: %s 가 필요한데 %s(%s)를 만났습니다 (line %d)"):format(
    msg or (v or t), cur.type, tostring(cur.value), cur.line or -1))
end

-- 키워드 검사 헬퍼
function Parser:is_kw(name) return self:check("KEYWORD", name) end
function Parser:eat_kw(name) return self:accept("KEYWORD", name) end

-- 프로그램 파싱: 라인의 연속
function Parser:parse_program()
  local lines = {}
  while not self:check("EOF") do
    if self:check("EOL") then self:advance()
    else
      local line = self:parse_line()
      if line then lines[#lines+1] = line end
    end
  end
  return AST.Program(lines)
end

function Parser:parse_line()
  local num
  if self:check("NUMBER") then
    num = self:advance().value
  else
    -- 라인 번호 없는 직접 모드 입력도 허용
    num = nil
  end
  local stmts = self:parse_stmt_list()
  if self:check("EOL") then self:advance() end
  return AST.Line(num, stmts)
end

function Parser:parse_stmt_list()
  local out = {}
  while not self:check("EOL") and not self:check("EOF") do
    local s = self:parse_stmt()
    if s then out[#out+1] = s end
    if self:accept("COLON") then
      -- 다음 문장
    else
      break
    end
  end
  return out
end

function Parser:parse_stmt()
  if self:check("REM") then self:advance(); return AST.Rem() end
  if self:eat_kw("LET")     then return self:parse_let_body() end
  if self:eat_kw("PRINT")   then return self:parse_print() end
  if self:eat_kw("INPUT")   then return self:parse_input() end
  if self:eat_kw("IF")      then return self:parse_if() end
  if self:eat_kw("FOR")     then return self:parse_for() end
  if self:eat_kw("NEXT")    then return self:parse_next() end
  if self:eat_kw("WHILE")   then return AST.While(self:parse_expr()) end
  if self:eat_kw("WEND")    then return AST.Wend() end
  if self:eat_kw("GOTO")    then return AST.Goto(self:expect("NUMBER",nil,"라인 번호").value) end
  if self:eat_kw("GOSUB")   then return AST.Gosub(self:expect("NUMBER",nil,"라인 번호").value) end
  if self:eat_kw("RETURN")  then return AST.Return() end
  if self:eat_kw("END")     then return AST.End() end
  if self:eat_kw("STOP")    then return AST.Stop() end
  if self:eat_kw("DIM")     then return self:parse_dim() end
  if self:eat_kw("DATA")    then return self:parse_data() end
  if self:eat_kw("READ")    then return self:parse_read() end
  if self:eat_kw("RESTORE") then return self:parse_restore() end
  if self:eat_kw("DEF")     then return self:parse_def() end
  if self:eat_kw("ON")      then return self:parse_on() end
  if self:eat_kw("CLS")     then return AST.Cls() end
  -- 암시적 LET (LET 키워드 생략)
  if self:check("IDENT") then return self:parse_let_body() end
  -- 빈 문장
  return nil
end

-- LET <var> = <expr>  또는  <var> = <expr>
function Parser:parse_let_body()
  local target = self:parse_lvalue()
  self:expect("EQ", nil, "=")
  local expr = self:parse_expr()
  return AST.Let(target, expr)
end

function Parser:parse_lvalue()
  local id = self:expect("IDENT", nil, "변수 이름").value
  local indices
  if self:accept("LPAREN") then
    indices = { self:parse_expr() }
    while self:accept("COMMA") do
      indices[#indices+1] = self:parse_expr()
    end
    self:expect("RPAREN", nil, ")")
  end
  return AST.Var(id, indices)
end

-- PRINT 문 파싱
function Parser:parse_print()
  local items = {}
  while true do
    if self:check("EOL") or self:check("EOF") or self:check("COLON")
       or self:is_kw("ELSE") then break end
    if self:accept("COMMA") then
      items[#items+1] = AST.PrintSep(",")
    elseif self:accept("SEMI") then
      items[#items+1] = AST.PrintSep(";")
    elseif self:eat_kw("TAB") then
      self:expect("LPAREN", nil, "(")
      local e = self:parse_expr()
      self:expect("RPAREN", nil, ")")
      items[#items+1] = AST.PrintTab(e)
    elseif self:eat_kw("SPC") then
      self:expect("LPAREN", nil, "(")
      local e = self:parse_expr()
      self:expect("RPAREN", nil, ")")
      items[#items+1] = AST.PrintSpc(e)
    else
      items[#items+1] = AST.PrintExpr(self:parse_expr())
    end
  end
  return AST.Print(items)
end

-- INPUT [prompt;] var [, var ...]
function Parser:parse_input()
  local prompt
  if self:check("STRING") then
    prompt = self:advance().value
    if self:accept("SEMI") or self:accept("COMMA") then end
  end
  local vars = { self:parse_lvalue() }
  while self:accept("COMMA") do
    vars[#vars+1] = self:parse_lvalue()
  end
  return AST.Input(prompt, vars)
end

-- IF cond THEN ... [ELSE ...]
-- THEN/ELSE 뒤에 라인 번호가 오면 GOTO 로 처리
function Parser:parse_if()
  local cond = self:parse_expr()
  if not self:eat_kw("THEN") then
    -- IF .. GOTO n  도 허용
    if not self:eat_kw("GOTO") then
      error("THEN 또는 GOTO 가 필요합니다")
    end
  end
  local then_branch = self:parse_then_branch()
  local else_branch
  if self:eat_kw("ELSE") then
    else_branch = self:parse_then_branch()
  end
  return AST.If(cond, then_branch, else_branch)
end

function Parser:parse_then_branch()
  -- 라인 번호 단독 → GOTO
  if self:check("NUMBER") then
    local n = self:advance().value
    return { AST.Goto(n) }
  end
  -- 일반 문장 목록
  local out = {}
  while true do
    local s = self:parse_stmt()
    if s then out[#out+1] = s end
    if not self:accept("COLON") then break end
    if self:check("EOL") or self:check("EOF") or self:is_kw("ELSE") then break end
  end
  return out
end

-- FOR v = e1 TO e2 [STEP e3]
function Parser:parse_for()
  local v = self:expect("IDENT", nil, "변수").value
  self:expect("EQ", nil, "=")
  local s = self:parse_expr()
  if not self:eat_kw("TO") then error("TO 가 필요합니다") end
  local e = self:parse_expr()
  local step
  if self:eat_kw("STEP") then step = self:parse_expr() end
  return AST.For(v, s, e, step)
end

function Parser:parse_next()
  local vars = {}
  if self:check("IDENT") then
    vars[#vars+1] = self:advance().value
    while self:accept("COMMA") do
      vars[#vars+1] = self:expect("IDENT", nil, "변수").value
    end
  end
  return AST.Next(vars)
end

function Parser:parse_dim()
  local decls = {}
  while true do
    local name = self:expect("IDENT", nil, "배열 이름").value
    self:expect("LPAREN", nil, "(")
    local dims = { self:parse_expr() }
    while self:accept("COMMA") do dims[#dims+1] = self:parse_expr() end
    self:expect("RPAREN", nil, ")")
    decls[#decls+1] = { name = name, dims = dims }
    if not self:accept("COMMA") then break end
  end
  return AST.Dim(decls)
end

function Parser:parse_data()
  local values = {}
  while true do
    if self:check("STRING") then
      values[#values+1] = { kind="string", value=self:advance().value }
    elseif self:check("NUMBER") then
      values[#values+1] = { kind="number", value=self:advance().value }
    elseif self:check("MINUS") then
      self:advance()
      values[#values+1] = { kind="number", value=-self:expect("NUMBER",nil,"숫자").value }
    elseif self:check("IDENT") then
      values[#values+1] = { kind="string", value=self:advance().value } -- 따옴표 없는 문자열
    else
      error("DATA 항목이 잘못되었습니다")
    end
    if not self:accept("COMMA") then break end
  end
  return AST.Data(values)
end

function Parser:parse_read()
  local vars = { self:parse_lvalue() }
  while self:accept("COMMA") do vars[#vars+1] = self:parse_lvalue() end
  return AST.Read(vars)
end

function Parser:parse_restore()
  local target
  if self:check("NUMBER") then target = self:advance().value end
  return AST.Restore(target)
end

-- DEF FN<name>(params) = expr  또는  DEF FNNAME(params) = expr
function Parser:parse_def()
  local name
  if self:eat_kw("FN") then
    name = "FN" .. self:expect("IDENT", nil, "함수 이름").value
  elseif self:check("IDENT") then
    local id = self:advance().value
    if id:sub(1,2) ~= "FN" then
      error("DEF 다음에 FN 으로 시작하는 이름이 필요합니다 (got "..id..")")
    end
    name = id
  else
    error("DEF 다음에 FN 또는 함수 이름이 필요합니다")
  end
  local params = {}
  if self:accept("LPAREN") then
    if not self:check("RPAREN") then
      params[#params+1] = self:expect("IDENT",nil,"매개변수").value
      while self:accept("COMMA") do
        params[#params+1] = self:expect("IDENT",nil,"매개변수").value
      end
    end
    self:expect("RPAREN", nil, ")")
  end
  self:expect("EQ", nil, "=")
  local body = self:parse_expr()
  return AST.DefFn(name, params, body)
end

function Parser:parse_on()
  local expr = self:parse_expr()
  local kind
  if self:eat_kw("GOTO") then kind = "GOTO"
  elseif self:eat_kw("GOSUB") then kind = "GOSUB"
  else error("ON 다음에 GOTO 또는 GOSUB 가 필요합니다") end
  local targets = { self:expect("NUMBER",nil,"라인 번호").value }
  while self:accept("COMMA") do
    targets[#targets+1] = self:expect("NUMBER",nil,"라인 번호").value
  end
  if kind == "GOTO" then return AST.OnGoto(expr, targets)
  else return AST.OnGosub(expr, targets) end
end

-- 표현식 파싱 (precedence climbing)
-- 우선순위 (낮음 → 높음): IMP, EQV, XOR, OR, AND, NOT, 비교, +-, MOD, \, */, ^, 단항-
local PREC = {
  ["IMP"]=1, ["EQV"]=2, ["XOR"]=3, ["OR"]=4, ["AND"]=5,
  -- NOT 은 단항
  ["="]=7, ["<>"]=7, ["<"]=7, [">"]=7, ["<="]=7, [">="]=7,
  ["+"]=8, ["-"]=8,
  ["MOD"]=9,
  ["\\"]=10,
  ["*"]=11, ["/"]=11,
  ["^"]=13,
}
local LEFT_ASSOC = { ["^"]=false } -- ^ 는 우결합
local function is_left(op) if LEFT_ASSOC[op] == false then return false end return true end

function Parser:peek_binop()
  local t = self:cur()
  if not t then return nil end
  if t.type == "PLUS"      then return "+", 8 end
  if t.type == "MINUS"     then return "-", 8 end
  if t.type == "STAR"      then return "*", 11 end
  if t.type == "SLASH"     then return "/", 11 end
  if t.type == "BACKSLASH" then return "\\", 10 end
  if t.type == "CARET"     then return "^", 13 end
  if t.type == "EQ"        then return "=", 7 end
  if t.type == "NE"        then return "<>", 7 end
  if t.type == "LT"        then return "<", 7 end
  if t.type == "GT"        then return ">", 7 end
  if t.type == "LE"        then return "<=", 7 end
  if t.type == "GE"        then return ">=", 7 end
  if t.type == "KEYWORD" then
    if t.value == "AND" or t.value == "OR" or t.value == "MOD"
       or t.value == "XOR" or t.value == "EQV" or t.value == "IMP" then
      return t.value, PREC[t.value]
    end
  end
  return nil
end

function Parser:parse_expr()
  return self:parse_binop(0)
end

function Parser:parse_binop(min_prec)
  local left = self:parse_unary()
  while true do
    local op, prec = self:peek_binop()
    if not op or prec < min_prec then break end
    self:advance()
    local next_min = is_left(op) and (prec + 1) or prec
    local right = self:parse_binop(next_min)
    left = AST.BinOp(op, left, right)
  end
  return left
end

function Parser:parse_unary()
  if self:accept("MINUS") then return AST.UnOp("-", self:parse_unary()) end
  if self:accept("PLUS") then return self:parse_unary() end
  if self:eat_kw("NOT") then return AST.UnOp("NOT", self:parse_unary()) end
  return self:parse_power()
end

function Parser:parse_power()
  local base = self:parse_atom()
  if self:check("CARET") then
    self:advance()
    local exp = self:parse_unary()
    return AST.BinOp("^", base, exp)
  end
  return base
end

function Parser:parse_atom()
  local t = self:cur()
  if not t then error("표현식이 비었습니다") end
  if t.type == "NUMBER" then self:advance(); return AST.NumLit(t.value) end
  if t.type == "STRING" then self:advance(); return AST.StrLit(t.value) end
  if t.type == "LPAREN" then
    self:advance()
    local e = self:parse_expr()
    self:expect("RPAREN", nil, ")")
    return e
  end
  if t.type == "KEYWORD" and t.value == "FN" then
    self:advance()
    local name = self:expect("IDENT",nil,"FN 이름").value
    local args = {}
    if self:accept("LPAREN") then
      if not self:check("RPAREN") then
        args[#args+1] = self:parse_expr()
        while self:accept("COMMA") do args[#args+1] = self:parse_expr() end
      end
      self:expect("RPAREN", nil, ")")
    end
    return AST.FnCall(name, args)
  end
  if t.type == "IDENT" then
    self:advance()
    -- 함수 호출 또는 배열 참조: foo(args)
    if self:check("LPAREN") then
      self:advance()
      local args = {}
      if not self:check("RPAREN") then
        args[#args+1] = self:parse_expr()
        while self:accept("COMMA") do args[#args+1] = self:parse_expr() end
      end
      self:expect("RPAREN", nil, ")")
      -- FN 접두 → 사용자 정의 함수
      if t.value:sub(1,2) == "FN" then
        return AST.FnCall(t.value, args)
      end
      -- 내장 함수인지 변수의 배열 인덱싱인지는 컴파일러가 판별
      return AST.Call(t.value, args)
    end
    return AST.Var(t.value, nil)
  end
  error("예상치 못한 토큰: "..t.type.."("..tostring(t.value)..")")
end

return M

```

### C.4 runtime.lua

```lua
-- runtime.lua : GW-BASIC 내장 함수
-- VM 에서 CALLF 명령으로 호출된다.
-- 각 함수는 (vm, args) 를 받고 반환값을 돌려준다.

local M = {}

local function tonum(v)
  if type(v) == "number" then return v end
  if type(v) == "string" then return tonumber(v) or 0 end
  return 0
end
local function tostr(v)
  if type(v) == "string" then return v end
  if type(v) == "number" then
    if v == math.floor(v) and math.abs(v) < 1e15 then
      return tostring(math.floor(v))
    end
    return tostring(v)
  end
  return tostring(v)
end

M.builtins = {}

local B = M.builtins

-- 수학 함수
B.ABS  = function(_, a) return math.abs(tonum(a[1])) end
B.SGN  = function(_, a) local v=tonum(a[1]); if v>0 then return 1 elseif v<0 then return -1 else return 0 end end
B.INT  = function(_, a) return math.floor(tonum(a[1])) end
B.FIX  = function(_, a) local v=tonum(a[1]); if v>=0 then return math.floor(v) else return math.ceil(v) end end
B.SQR  = function(_, a) return math.sqrt(tonum(a[1])) end
B.EXP  = function(_, a) return math.exp(tonum(a[1])) end
B.LOG  = function(_, a) return math.log(tonum(a[1])) end
B.SIN  = function(_, a) return math.sin(tonum(a[1])) end
B.COS  = function(_, a) return math.cos(tonum(a[1])) end
B.TAN  = function(_, a) return math.tan(tonum(a[1])) end
B.ATN  = function(_, a) return math.atan(tonum(a[1])) end
B.RND  = function(_, a)
  local n = a[1] and tonum(a[1]) or 1
  if n == 0 then return math.random() end -- 마지막 값 (단순화)
  return math.random()
end

-- 문자열 함수
B.LEN     = function(_, a) return #tostr(a[1]) end
B.LEFT    = function(_, a) return tostr(a[1]):sub(1, tonum(a[2])) end
B["LEFT$"]= B.LEFT
B.RIGHT   = function(_, a) local s=tostr(a[1]); local n=tonum(a[2]); return s:sub(#s-n+1) end
B["RIGHT$"]= B.RIGHT
B.MID     = function(_, a)
  local s=tostr(a[1]); local i=tonum(a[2]); local n=a[3] and tonum(a[3]) or (#s - i + 1)
  return s:sub(i, i+n-1)
end
B["MID$"] = B.MID
B.CHR     = function(_, a) return string.char(tonum(a[1]) % 256) end
B["CHR$"] = B.CHR
B.ASC     = function(_, a) local s=tostr(a[1]); return s:byte(1) or 0 end
B.STR     = function(_, a)
  local v=tonum(a[1])
  if v >= 0 then return " "..tostr(v) end
  return tostr(v)
end
B["STR$"] = B.STR
B.VAL     = function(_, a) return tonumber(tostr(a[1])) or 0 end
B.SPACE   = function(_, a) return string.rep(" ", tonum(a[1])) end
B["SPACE$"]= B.SPACE
B.STRING  = function(_, a)
  local n = tonum(a[1])
  local c = a[2]
  if type(c) == "number" then c = string.char(c % 256) else c = tostr(c):sub(1,1) end
  return string.rep(c, n)
end
B["STRING$"]= B.STRING
B.INSTR   = function(_, a)
  -- INSTR([start,] target, search)
  if #a == 2 then
    local s,t = tostr(a[1]), tostr(a[2])
    local i = s:find(t, 1, true)
    return i or 0
  else
    local start, s, t = tonum(a[1]), tostr(a[2]), tostr(a[3])
    local i = s:find(t, start, true)
    return i or 0
  end
end
B.UCASE   = function(_, a) return tostr(a[1]):upper() end
B["UCASE$"]= B.UCASE
B.LCASE   = function(_, a) return tostr(a[1]):lower() end
B["LCASE$"]= B.LCASE

-- 시간/시스템
B.TIMER = function() return os.time() end
B.DATE  = function() return os.date("%m-%d-%Y") end
B["DATE$"]= B.DATE
B.TIME  = function() return os.date("%H:%M:%S") end
B["TIME$"]= B.TIME

-- 모든 함수 키를 대문자로 통일
local upper = {}
for k,v in pairs(B) do upper[k:upper()] = v end
M.builtins = upper

-- 함수 이름이 내장 함수인지 확인
function M.is_builtin(name)
  return M.builtins[name:upper()] ~= nil
end

function M.call(name, vm, args)
  local fn = M.builtins[name:upper()]
  if not fn then error("정의되지 않은 함수: "..name) end
  return fn(vm, args)
end

-- 변수 이름의 타입 ($, %, !, # 또는 없음)
function M.var_kind(name)
  local last = name:sub(-1)
  if last == "$" then return "string"
  elseif last == "%" then return "int"
  elseif last == "!" then return "single"
  elseif last == "#" then return "double"
  else return "single" end
end

function M.coerce_for_var(name, value)
  local k = M.var_kind(name)
  if k == "string" then
    if type(value) == "number" then
      error("Type mismatch: 문자열 변수 "..name.." 에 숫자 대입")
    end
    return value
  else
    if type(value) == "string" then
      error("Type mismatch: 숫자 변수 "..name.." 에 문자열 대입")
    end
    if k == "int" then return math.floor(value + 0.5) end
    return value
  end
end

-- BASIC 형식의 숫자 출력
function M.basic_tostring(v)
  if type(v) == "string" then return v end
  if type(v) == "number" then
    if v ~= v then return "NaN" end
    if v == math.huge then return "INF" end
    if v == -math.huge then return "-INF" end
    if v == math.floor(v) and math.abs(v) < 1e15 then
      local s = tostring(math.floor(v))
      if v >= 0 then return " "..s.." " else return s.." " end
    end
    local s = string.format("%.7g", v)
    if v >= 0 then return " "..s.." " else return s.." " end
  end
  return tostring(v)
end

-- 비교 결과 (BASIC 은 -1=참, 0=거짓)
function M.bool(b) if b then return -1 else return 0 end end
function M.truthy(v)
  if type(v) == "number" then return v ~= 0 end
  if type(v) == "string" then return v ~= "" end
  return false
end

return M

```

### C.5 compiler.lua

```lua
-- compiler.lua : AST → 바이트코드
-- 출력 형식:
--   bytecode = { ops = {...}, line_addr = {ln=addr,...}, data = {...},
--                fns = {name = {params, body_addr_index_to_expr_program}},
--                strings = {...} }
-- 각 op 는 { op="ADD" } 또는 { op="JMP", arg=N } 등으로 표현.

local M = {}

local Compiler = {}
Compiler.__index = Compiler

function M.new()
  return setmetatable({
    ops = {},
    line_addr = {},   -- BASIC 라인번호 → ops 인덱스 (1-base)
    data = {},        -- DATA 항목 (순서대로 평탄화)
    data_line_addr = {}, -- 라인번호 → data 인덱스
    fns = {},         -- DEF FN 정의 {name → {params={}, expr=AST}}
    strings = {},     -- 문자열 풀 (실제로는 op 안에 직접 박음)
    pending_gotos = {}, -- {addr_in_ops, line_no, kind}
  }, Compiler)
end

function Compiler:emit(op, arg, arg2)
  self.ops[#self.ops+1] = { op = op, arg = arg, arg2 = arg2 }
  return #self.ops
end

function Compiler:current_addr() return #self.ops + 1 end

function Compiler:patch(addr, key, value)
  self.ops[addr][key] = value
end

function Compiler:compile_program(prog)
  for _, line in ipairs(prog.lines) do
    if line.number then
      self.line_addr[line.number] = self:current_addr()
      self.data_line_addr[line.number] = self.data_line_addr[line.number] or (#self.data + 1)
    end
    for _, stmt in ipairs(line.stmts) do
      self:compile_stmt(stmt, line.number)
    end
  end
  self:emit("HALT")
  -- pending GOTO/GOSUB 백패치
  for _, p in ipairs(self.pending_gotos) do
    local target = self.line_addr[p.line]
    if not target then error("Undefined line "..tostring(p.line)) end
    self.ops[p.addr].arg = target
  end
  return {
    ops = self.ops,
    line_addr = self.line_addr,
    data = self.data,
    data_line_addr = self.data_line_addr,
    fns = self.fns,
  }
end

function Compiler:compile_stmt(s, line_no)
  local tag = s.tag
  if tag == "Rem" or tag == "Wend" then
    -- nothing here for Rem; Wend handled below
  end
  if tag == "Rem" then return end
  if tag == "Let"     then self:compile_let(s); return end
  if tag == "Print"   then self:compile_print(s); return end
  if tag == "Input"   then self:compile_input(s); return end
  if tag == "If"      then self:compile_if(s, line_no); return end
  if tag == "For"     then self:compile_for(s); return end
  if tag == "Next"    then self:compile_next(s); return end
  if tag == "While"   then self:compile_while(s); return end
  if tag == "Wend"    then self:compile_wend(s); return end
  if tag == "Goto"    then self:compile_goto(s, "JMP"); return end
  if tag == "Gosub"   then self:compile_goto(s, "GOSUB"); return end
  if tag == "Return"  then self:emit("RETURN"); return end
  if tag == "End"     then self:emit("HALT"); return end
  if tag == "Stop"    then self:emit("HALT"); return end
  if tag == "Cls"     then self:emit("CLS"); return end
  if tag == "Dim"     then self:compile_dim(s); return end
  if tag == "Data"    then self:compile_data(s); return end
  if tag == "Read"    then self:compile_read(s); return end
  if tag == "Restore" then self:emit("RESTORE", s.target); return end
  if tag == "DefFn"   then self.fns[s.name:upper()] = { params = s.params, expr = s.body }; return end
  if tag == "OnGoto"  then self:compile_on(s, "JMP"); return end
  if tag == "OnGosub" then self:compile_on(s, "GOSUB"); return end
  error("Unsupported statement: "..tostring(tag))
end

function Compiler:compile_let(s)
  local v = s.target
  if v.indices then
    -- 배열 대입: 인덱스 push, 그 다음 값 push, ASTORE
    for _, idx in ipairs(v.indices) do self:compile_expr(idx) end
    self:compile_expr(s.expr)
    self:emit("ASTORE", v.name, #v.indices)
  else
    self:compile_expr(s.expr)
    self:emit("STORE", v.name)
  end
end

function Compiler:compile_print(s)
  local last_was_sep = false
  for _, item in ipairs(s.items) do
    if item.tag == "PrintExpr" then
      self:compile_expr(item.expr)
      self:emit("PRINT_ITEM")
      last_was_sep = false
    elseif item.tag == "PrintSep" then
      if item.kind == "," then self:emit("PRINT_TAB") end
      last_was_sep = true
    elseif item.tag == "PrintTab" then
      self:compile_expr(item.expr)
      self:emit("PRINT_TAB_TO")
      last_was_sep = true
    elseif item.tag == "PrintSpc" then
      self:compile_expr(item.expr)
      self:emit("PRINT_SPC")
      last_was_sep = true
    end
  end
  if not last_was_sep then self:emit("PRINT_NL") end
end

function Compiler:compile_input(s)
  for _, v in ipairs(s.vars) do
    self:emit("INPUT", s.prompt, v.name)
  end
end

function Compiler:compile_if(s, line_no)
  self:compile_expr(s.cond)
  local jz = self:emit("JZ", 0)
  for _, stmt in ipairs(s.then_) do self:compile_stmt(stmt, line_no) end
  if s.else_ then
    local jmp_end = self:emit("JMP", 0)
    self:patch(jz, "arg", self:current_addr())
    for _, stmt in ipairs(s.else_) do self:compile_stmt(stmt, line_no) end
    self:patch(jmp_end, "arg", self:current_addr())
  else
    self:patch(jz, "arg", self:current_addr())
  end
end

-- FOR/NEXT 컴파일
-- FOR I = a TO b STEP s
-- => STORE I, STORE __limit_I, STORE __step_I; loop_top: 검사; ... NEXT => 증가, JMP loop_top
function Compiler:compile_for(s)
  local v = s.var
  self:compile_expr(s.start); self:emit("STORE", v)
  self:compile_expr(s.stop);  self:emit("STORE", "__LIMIT_"..v)
  if s.step then self:compile_expr(s.step) else self:emit("PUSHN", 1) end
  self:emit("STORE", "__STEP_"..v)
  local top = self:current_addr()
  -- 검사 코드: ((step >= 0 and i <= limit) or (step < 0 and i >= limit))
  -- 단순화: step*(i - limit) <= 0 이면 계속
  self:emit("LOAD", "__STEP_"..v)
  self:emit("LOAD", v)
  self:emit("LOAD", "__LIMIT_"..v)
  self:emit("SUB")
  self:emit("MUL")
  self:emit("PUSHN", 0)
  self:emit("LE")
  local jz = self:emit("JZ", 0)
  self.for_stack = self.for_stack or {}
  self.for_stack[#self.for_stack+1] = { var = v, top = top, exit_jz = jz }
end

function Compiler:compile_next(s)
  local vars = s.vars
  if #vars == 0 then vars = { nil } end
  for _, vname in ipairs(vars) do
    local frame = table.remove(self.for_stack)
    if not frame then error("NEXT 에 대응하는 FOR 가 없습니다") end
    if vname and vname ~= frame.var then
      error("NEXT "..vname.." 인데 FOR "..frame.var.." 입니다")
    end
    -- i = i + step
    self:emit("LOAD", frame.var)
    self:emit("LOAD", "__STEP_"..frame.var)
    self:emit("ADD")
    self:emit("STORE", frame.var)
    self:emit("JMP", frame.top)
    self:patch(frame.exit_jz, "arg", self:current_addr())
  end
end

function Compiler:compile_while(s)
  self.while_stack = self.while_stack or {}
  local top = self:current_addr()
  self:compile_expr(s.cond)
  local jz = self:emit("JZ", 0)
  self.while_stack[#self.while_stack+1] = { top = top, exit_jz = jz }
end

function Compiler:compile_wend(s)
  local frame = table.remove(self.while_stack)
  if not frame then error("WEND 에 대응하는 WHILE 가 없습니다") end
  self:emit("JMP", frame.top)
  self:patch(frame.exit_jz, "arg", self:current_addr())
end

function Compiler:compile_goto(s, op)
  local addr = self:emit(op, 0)
  self.pending_gotos[#self.pending_gotos+1] = { addr = addr, line = s.target }
end

function Compiler:compile_dim(s)
  for _, d in ipairs(s.decls) do
    for _, dim in ipairs(d.dims) do self:compile_expr(dim) end
    self:emit("DIM", d.name, #d.dims)
  end
end

function Compiler:compile_data(s)
  for _, v in ipairs(s.values) do
    self.data[#self.data+1] = v
  end
end

function Compiler:compile_read(s)
  for _, v in ipairs(s.vars) do
    if v.indices then
      for _, idx in ipairs(v.indices) do self:compile_expr(idx) end
      self:emit("READ_A", v.name, #v.indices)
    else
      self:emit("READ", v.name)
    end
  end
end

function Compiler:compile_on(s, op)
  self:compile_expr(s.expr)
  -- ON 식의 값 N → N번째 라인으로
  -- 명령: ONJMP { targets = {l1,l2,...}, kind = "JMP"|"GOSUB" }
  -- 각 라인은 라인주소로 즉시 변환할 수 없으니 백패치
  local addr = self:emit("ONJMP", op, s.targets)
  self.pending_on = self.pending_on or {}
  self.pending_on[#self.pending_on+1] = addr
end

-- 표현식 컴파일
local runtime = require("runtime")

function Compiler:compile_expr(e)
  local tag = e.tag
  if tag == "NumLit" then self:emit("PUSHN", e.value); return end
  if tag == "StrLit" then self:emit("PUSHS", e.value); return end
  if tag == "Var" then
    if e.indices then
      for _, idx in ipairs(e.indices) do self:compile_expr(idx) end
      self:emit("ALOAD", e.name, #e.indices)
    else
      self:emit("LOAD", e.name)
    end
    return
  end
  if tag == "BinOp" then
    self:compile_expr(e.left)
    self:compile_expr(e.right)
    local m = {
      ["+"]="ADD", ["-"]="SUB", ["*"]="MUL", ["/"]="DIV",
      ["\\"]="IDIV", ["MOD"]="MOD", ["^"]="POW",
      ["="]="EQ", ["<>"]="NE", ["<"]="LT", [">"]="GT",
      ["<="]="LE", [">="]="GE",
      ["AND"]="AND", ["OR"]="OR", ["XOR"]="XOR",
      ["EQV"]="EQV", ["IMP"]="IMP",
    }
    local op = m[e.op]
    if not op then error("Unknown op: "..tostring(e.op)) end
    self:emit(op)
    return
  end
  if tag == "UnOp" then
    self:compile_expr(e.operand)
    if e.op == "-" then self:emit("NEG")
    elseif e.op == "NOT" then self:emit("NOT")
    else error("Unknown unary: "..e.op) end
    return
  end
  if tag == "Call" then
    -- 내장 함수 또는 배열 인덱싱
    if runtime.is_builtin(e.name) then
      for _, a in ipairs(e.args) do self:compile_expr(a) end
      self:emit("CALLF", e.name, #e.args)
    else
      -- 배열로 간주
      for _, a in ipairs(e.args) do self:compile_expr(a) end
      self:emit("ALOAD", e.name, #e.args)
    end
    return
  end
  if tag == "FnCall" then
    for _, a in ipairs(e.args) do self:compile_expr(a) end
    self:emit("CALLU", e.name, #e.args)
    return
  end
  error("Unsupported expr: "..tostring(tag))
end

return M

```

### C.6 vm.lua

```lua
-- vm.lua : 스택 기반 가상 머신
-- 입력: compiler 가 생성한 bytecode 객체
-- 동작: ops 를 순차 실행, GOTO/GOSUB 시 ip 를 line_addr 로 점프

local runtime = require("runtime")
local M = {}

local VM = {}
VM.__index = VM

function M.new(bc, opts)
  opts = opts or {}
  return setmetatable({
    bc = bc,
    ip = 1,
    stack = {},
    call_stack = {},   -- GOSUB 복귀 주소
    vars = {},         -- 스칼라 변수
    arrays = {},       -- 배열 {data={}, dims={n1,n2,...}, base=0}
    data_ptr = 1,      -- READ 포인터
    print_col = 0,
    output = opts.output,   -- 함수: print 한 줄 받음 (테스트용)
    input  = opts.input,    -- 함수: 프롬프트 받고 입력 한 줄 반환
    halted = false,
    zone_width = 14,        -- PRINT , 영역 폭 (GW-BASIC 기본 14)
    line_width = 80,
  }, VM)
end

function VM:push(v) self.stack[#self.stack+1] = v end
function VM:pop()
  local n = #self.stack
  local v = self.stack[n]
  self.stack[n] = nil
  return v
end
function VM:top() return self.stack[#self.stack] end

local function tonum(v)
  if type(v) == "number" then return v end
  return tonumber(v) or 0
end
local function tostr(v) return runtime.basic_tostring(v):gsub("^%s","") end

function VM:default_var(name)
  if name:sub(-1) == "$" then return "" else return 0 end
end

function VM:get_var(name)
  if self.vars[name] ~= nil then return self.vars[name] end
  return self:default_var(name)
end

function VM:set_var(name, v)
  v = runtime.coerce_for_var(name, v)
  self.vars[name] = v
end

function VM:dim_array(name, dims)
  local total = 1
  for _,d in ipairs(dims) do total = total * (d + 1) end -- 0..d
  local data = {}
  local fill = self:default_var(name)
  for i=1,total do data[i] = fill end
  self.arrays[name] = { dims = dims, data = data, base = 0 }
end

function VM:ensure_array(name, ndims)
  if self.arrays[name] then return self.arrays[name] end
  -- 자동 DIM: 각 차원 10
  local dims = {}
  for i=1,ndims do dims[i] = 10 end
  self:dim_array(name, dims)
  return self.arrays[name]
end

function VM:linear_index(arr, idxs)
  -- 0-base 인덱스, dims = 차원별 최대값(0..d), 크기 = d+1
  local idx = 0
  for i = 1, #idxs do
    local d = arr.dims[i]
    if not d then error("배열 "..tostring(idxs).." 차원 초과") end
    local k = math.floor(idxs[i] + 0.5)
    if k < 0 or k > d then error("배열 인덱스 범위 벗어남: "..k) end
    idx = idx * (d + 1) + k
  end
  return idx + 1 -- Lua 1-base
end

function VM:print_str(s)
  if self.output then self.output(s)
  else io.write(s) end
  -- 컬럼 위치 갱신
  for i=1,#s do
    local c = s:sub(i,i)
    if c == "\n" then self.print_col = 0
    else self.print_col = self.print_col + 1 end
  end
end

function VM:newline() self:print_str("\n") end

function VM:run()
  local ops = self.bc.ops
  while not self.halted and self.ip <= #ops do
    local op = ops[self.ip]
    self.ip = self.ip + 1
    self:exec(op)
  end
end

function VM:exec(op)
  local name = op.op
  local h = self.handlers[name]
  if not h then error("Unknown opcode: "..tostring(name)) end
  h(self, op)
end

-- 핸들러 테이블
VM.handlers = {}
local H = VM.handlers

H.HALT = function(vm) vm.halted = true end
H.PUSHN = function(vm, op) vm:push(op.arg) end
H.PUSHS = function(vm, op) vm:push(op.arg) end
H.POP = function(vm) vm:pop() end

H.LOAD = function(vm, op)
  vm:push(vm:get_var(op.arg))
end
H.STORE = function(vm, op)
  vm:set_var(op.arg, vm:pop())
end

H.ALOAD = function(vm, op)
  local n = op.arg2
  local idxs = {}
  for i = n, 1, -1 do idxs[i] = vm:pop() end
  local arr = vm:ensure_array(op.arg, n)
  vm:push(arr.data[vm:linear_index(arr, idxs)])
end
H.ASTORE = function(vm, op)
  local n = op.arg2
  local val = vm:pop()
  local idxs = {}
  for i = n, 1, -1 do idxs[i] = vm:pop() end
  local arr = vm:ensure_array(op.arg, n)
  val = runtime.coerce_for_var(op.arg, val)
  arr.data[vm:linear_index(arr, idxs)] = val
end

H.DIM = function(vm, op)
  local n = op.arg2
  local dims = {}
  for i = n, 1, -1 do dims[i] = math.floor(vm:pop() + 0.5) end
  vm:dim_array(op.arg, dims)
end

local function num2(vm)
  local b = tonum(vm:pop())
  local a = tonum(vm:pop())
  return a, b
end

H.ADD = function(vm)
  local b = vm:pop(); local a = vm:pop()
  if type(a) == "string" or type(b) == "string" then
    vm:push(tostring(a)..tostring(b))
  else
    vm:push(a + b)
  end
end
H.SUB  = function(vm) local a,b=num2(vm); vm:push(a-b) end
H.MUL  = function(vm) local a,b=num2(vm); vm:push(a*b) end
H.DIV  = function(vm) local a,b=num2(vm); if b==0 then error("Division by zero") end; vm:push(a/b) end
H.IDIV = function(vm) local a,b=num2(vm); if b==0 then error("Division by zero") end
                       vm:push(math.floor(a/b)) end
H.MOD  = function(vm) local a,b=num2(vm); vm:push(a - math.floor(a/b)*b) end
H.POW  = function(vm) local a,b=num2(vm); vm:push(a^b) end
H.NEG  = function(vm) vm:push(-tonum(vm:pop())) end

H.EQ = function(vm) local b=vm:pop(); local a=vm:pop(); vm:push(runtime.bool(a==b)) end
H.NE = function(vm) local b=vm:pop(); local a=vm:pop(); vm:push(runtime.bool(a~=b)) end
H.LT = function(vm) local b=vm:pop(); local a=vm:pop(); vm:push(runtime.bool(a<b)) end
H.GT = function(vm) local b=vm:pop(); local a=vm:pop(); vm:push(runtime.bool(a>b)) end
H.LE = function(vm) local b=vm:pop(); local a=vm:pop(); vm:push(runtime.bool(a<=b)) end
H.GE = function(vm) local b=vm:pop(); local a=vm:pop(); vm:push(runtime.bool(a>=b)) end

-- 비트 논리 연산자 (GW-BASIC 은 정수 비트연산)
local function band(a,b)
  a = math.floor(a); b = math.floor(b)
  local r,p = 0,1
  for i=0,31 do
    if (a%2 == 1) and (b%2 == 1) then r = r + p end
    a = math.floor(a/2); b = math.floor(b/2); p = p*2
  end
  return r
end
local function bor(a,b)
  a = math.floor(a); b = math.floor(b)
  local r,p = 0,1
  for i=0,31 do
    if (a%2 == 1) or (b%2 == 1) then r = r + p end
    a = math.floor(a/2); b = math.floor(b/2); p = p*2
  end
  return r
end
local function bxor(a,b)
  a = math.floor(a); b = math.floor(b)
  local r,p = 0,1
  for i=0,31 do
    if (a%2) ~= (b%2) then r = r + p end
    a = math.floor(a/2); b = math.floor(b/2); p = p*2
  end
  return r
end
local function bnot(a)
  return -math.floor(a) - 1
end

H.AND = function(vm) local a,b=num2(vm); vm:push(band(a,b)) end
H.OR  = function(vm) local a,b=num2(vm); vm:push(bor(a,b)) end
H.XOR = function(vm) local a,b=num2(vm); vm:push(bxor(a,b)) end
H.EQV = function(vm) local a,b=num2(vm); vm:push(bnot(bxor(a,b))) end
H.IMP = function(vm) local a,b=num2(vm); vm:push(bor(bnot(a), b)) end
H.NOT = function(vm) vm:push(bnot(tonum(vm:pop()))) end

H.JMP = function(vm, op) vm.ip = op.arg end
H.JZ  = function(vm, op) local v = vm:pop(); if not runtime.truthy(v) then vm.ip = op.arg end end
H.JNZ = function(vm, op) local v = vm:pop(); if runtime.truthy(v) then vm.ip = op.arg end end

H.GOSUB = function(vm, op)
  vm.call_stack[#vm.call_stack+1] = vm.ip
  vm.ip = op.arg
end
H.RETURN = function(vm)
  local ret = table.remove(vm.call_stack)
  if not ret then error("RETURN without GOSUB") end
  vm.ip = ret
end

H.ONJMP = function(vm, op)
  -- op.arg = "JMP"|"GOSUB", op.arg2 = {라인번호 리스트}
  local n = math.floor(tonum(vm:pop()) + 0.5)
  if n < 1 or n > #op.arg2 then return end -- 범위 밖이면 무시
  local target_line = op.arg2[n]
  local target_addr = vm.bc.line_addr[target_line]
  if not target_addr then error("Undefined line "..target_line) end
  if op.arg == "GOSUB" then
    vm.call_stack[#vm.call_stack+1] = vm.ip
  end
  vm.ip = target_addr
end

H.PRINT_ITEM = function(vm)
  local v = vm:pop()
  vm:print_str(runtime.basic_tostring(v))
end
H.PRINT_NL = function(vm) vm:newline() end
H.PRINT_TAB = function(vm)
  -- , 분리자: 다음 zone 으로
  local col = vm.print_col
  local next_zone = math.floor(col / vm.zone_width) * vm.zone_width + vm.zone_width
  if next_zone >= vm.line_width then vm:newline()
  else vm:print_str(string.rep(" ", next_zone - col)) end
end
H.PRINT_TAB_TO = function(vm)
  local target = math.floor(tonum(vm:pop()))
  if target < 1 then target = 1 end
  if vm.print_col >= target then vm:newline() end
  vm:print_str(string.rep(" ", target - 1 - vm.print_col))
end
H.PRINT_SPC = function(vm)
  local n = math.floor(tonum(vm:pop()))
  if n > 0 then vm:print_str(string.rep(" ", n)) end
end

H.CLS = function(vm)
  if vm.output then vm.output("\27[2J\27[H")
  else io.write("\27[2J\27[H") end
  vm.print_col = 0
end

H.INPUT = function(vm, op)
  local prompt = op.arg or ""
  if prompt == "" or not prompt then prompt = "? " else prompt = prompt .. "? " end
  local line
  if vm.input then line = vm.input(prompt)
  else
    io.write(prompt); io.flush()
    line = io.read("*l") or ""
  end
  -- 변수 타입에 따라 변환
  local name = op.arg2
  if name:sub(-1) == "$" then
    vm:set_var(name, line)
  else
    vm:set_var(name, tonumber(line) or 0)
  end
end

H.READ = function(vm, op)
  local item = vm.bc.data[vm.data_ptr]
  if not item then error("Out of DATA") end
  vm.data_ptr = vm.data_ptr + 1
  local name = op.arg
  if name:sub(-1) == "$" then
    vm:set_var(name, tostring(item.value))
  else
    if item.kind == "number" then vm:set_var(name, item.value)
    else vm:set_var(name, tonumber(item.value) or 0) end
  end
end
H.READ_A = function(vm, op)
  local item = vm.bc.data[vm.data_ptr]
  if not item then error("Out of DATA") end
  vm.data_ptr = vm.data_ptr + 1
  local n = op.arg2
  local idxs = {}
  for i = n, 1, -1 do idxs[i] = vm:pop() end
  local arr = vm:ensure_array(op.arg, n)
  local val
  if op.arg:sub(-1) == "$" then val = tostring(item.value)
  else val = (item.kind=="number") and item.value or (tonumber(item.value) or 0) end
  arr.data[vm:linear_index(arr, idxs)] = val
end

H.RESTORE = function(vm, op)
  if op.arg then
    vm.data_ptr = vm.bc.data_line_addr[op.arg] or 1
  else
    vm.data_ptr = 1
  end
end

H.CALLF = function(vm, op)
  local argc = op.arg2
  local args = {}
  for i = argc, 1, -1 do args[i] = vm:pop() end
  vm:push(runtime.call(op.arg, vm, args))
end

H.CALLU = function(vm, op)
  local fn = vm.bc.fns[op.arg:upper()]
  if not fn then error("Undefined FN "..op.arg) end
  local argc = op.arg2
  local args = {}
  for i = argc, 1, -1 do args[i] = vm:pop() end
  -- 매개변수를 임시로 설정 → 식 평가 → 복원
  local saved = {}
  for i, p in ipairs(fn.params) do saved[p] = vm.vars[p]; vm.vars[p] = args[i] end
  local result = vm:eval_expr_ast(fn.expr)
  for p, v in pairs(saved) do vm.vars[p] = v end
  vm:push(result)
end

-- 부분적 AST 평가 (DEF FN 본문은 컴파일 없이 즉석 평가)
function VM:eval_expr_ast(e)
  local tag = e.tag
  if tag == "NumLit" then return e.value end
  if tag == "StrLit" then return e.value end
  if tag == "Var" then
    if e.indices then
      local idxs = {}
      for i, ie in ipairs(e.indices) do idxs[i] = self:eval_expr_ast(ie) end
      local arr = self:ensure_array(e.name, #idxs)
      return arr.data[self:linear_index(arr, idxs)]
    end
    return self:get_var(e.name)
  end
  if tag == "BinOp" then
    local a = self:eval_expr_ast(e.left)
    local b = self:eval_expr_ast(e.right)
    if e.op == "+" then
      if type(a)=="string" or type(b)=="string" then return tostring(a)..tostring(b) end
      return a + b
    end
    if e.op == "-" then return tonum(a) - tonum(b) end
    if e.op == "*" then return tonum(a) * tonum(b) end
    if e.op == "/" then return tonum(a) / tonum(b) end
    if e.op == "\\" then return math.floor(tonum(a)/tonum(b)) end
    if e.op == "MOD" then local x,y=tonum(a),tonum(b); return x - math.floor(x/y)*y end
    if e.op == "^" then return tonum(a) ^ tonum(b) end
    if e.op == "=" then return runtime.bool(a==b) end
    if e.op == "<>" then return runtime.bool(a~=b) end
    if e.op == "<" then return runtime.bool(a<b) end
    if e.op == ">" then return runtime.bool(a>b) end
    if e.op == "<=" then return runtime.bool(a<=b) end
    if e.op == ">=" then return runtime.bool(a>=b) end
    if e.op == "AND" then return band(tonum(a), tonum(b)) end
    if e.op == "OR" then return bor(tonum(a), tonum(b)) end
    if e.op == "XOR" then return bxor(tonum(a), tonum(b)) end
    error("Unknown op "..e.op)
  end
  if tag == "UnOp" then
    local v = self:eval_expr_ast(e.operand)
    if e.op == "-" then return -tonum(v) end
    if e.op == "NOT" then return bnot(tonum(v)) end
  end
  if tag == "Call" then
    local args = {}
    for i, a in ipairs(e.args) do args[i] = self:eval_expr_ast(a) end
    if runtime.is_builtin(e.name) then
      return runtime.call(e.name, self, args)
    end
    local arr = self:ensure_array(e.name, #args)
    return arr.data[self:linear_index(arr, args)]
  end
  if tag == "FnCall" then
    local fn = self.bc.fns[e.name:upper()]
    if not fn then error("Undefined FN "..e.name) end
    local args = {}
    for i, a in ipairs(e.args) do args[i] = self:eval_expr_ast(a) end
    local saved = {}
    for i, p in ipairs(fn.params) do saved[p] = self.vars[p]; self.vars[p] = args[i] end
    local result = self:eval_expr_ast(fn.expr)
    for p, v in pairs(saved) do self.vars[p] = v end
    return result
  end
  error("Cannot eval "..tostring(tag))
end

return M

```

### C.7 main.lua

```lua
-- main.lua : GW-BASIC 인터프리터 진입점
-- 사용법:
--   lua main.lua <파일.bas>
--   lua main.lua          (REPL 모드)

-- 같은 디렉터리의 모듈을 찾도록 패키지 경로 설정
local script_dir = arg[0]:match("(.*/)") or "./"
package.path = script_dir.."?.lua;"..package.path

local Lexer    = require("lexer")
local Parser   = require("parser")
local Compiler = require("compiler")
local VM       = require("vm")

local function compile_source(src)
  local tokens = Lexer.new(src):tokenize()
  local ast = Parser.new(tokens):parse_program()
  local bc = Compiler.new():compile_program(ast)
  return bc
end

local function run_file(path)
  local f, err = io.open(path, "r")
  if not f then print("파일을 열 수 없습니다: "..tostring(err)); os.exit(1) end
  local src = f:read("*a")
  f:close()
  local ok, err2 = pcall(function()
    local bc = compile_source(src)
    local vm = VM.new(bc)
    vm:run()
  end)
  if not ok then
    io.stderr:write("실행 오류: "..tostring(err2).."\n")
    os.exit(2)
  end
end

local function repl()
  print("LuaGW-BASIC 1.0  --  종료: BYE 또는 Ctrl-D")
  local lines = {}
  while true do
    io.write("Ok\n> "); io.flush()
    local line = io.read("*l")
    if not line then break end
    if line:upper() == "BYE" or line:upper() == "QUIT" then break end
    if line:upper() == "RUN" then
      local src = table.concat(lines, "\n")
      local ok, err = pcall(function()
        local bc = compile_source(src)
        VM.new(bc):run()
      end)
      if not ok then print("Error: "..tostring(err)) end
    elseif line:upper() == "LIST" then
      for _, l in ipairs(lines) do print(l) end
    elseif line:upper() == "NEW" then
      lines = {}
    else
      -- 라인 번호로 시작하면 프로그램 라인, 아니면 즉시 실행
      if line:match("^%s*%d") then
        lines[#lines+1] = line
      else
        local ok, err = pcall(function()
          local bc = compile_source(line)
          VM.new(bc):run()
        end)
        if not ok then print("Error: "..tostring(err)) end
      end
    end
  end
  print("Bye!")
end

if arg[1] then
  run_file(arg[1])
else
  repl()
end

```

> 본 책의 깃 저장소(`/storage/self/primary/Documents/chobocho_box/lua_gwbasic_book/src/`)에서 같은 파일을 직접 받을 수 있다.

---

## 부록 D — 예제 .BAS 프로그램 모음

### D.1 hello.bas

```basic
10 REM HELLO WORLD
20 PRINT "HELLO, GW-BASIC!"
30 FOR I = 1 TO 5
40   PRINT "  ", I, I*I, I*I*I
50 NEXT I
60 PRINT "DONE."
70 END
```

### D.2 fib.bas — 피보나치

```basic
10 REM FIBONACCI
20 N = 15
30 A = 0 : B = 1
40 PRINT "FIB(0) = "; A
50 PRINT "FIB(1) = "; B
60 FOR I = 2 TO N
70   C = A + B
80   PRINT "FIB("; I; ") = "; C
90   A = B : B = C
100 NEXT I
110 END
```

### D.3 sieve.bas — 에라토스테네스의 체

```basic
10 REM SIEVE OF ERATOSTHENES
20 N = 50
30 DIM S(N)
40 FOR I = 2 TO N : S(I) = 1 : NEXT I
50 FOR I = 2 TO N
60   IF S(I) = 0 THEN GOTO 100
70   FOR J = I*2 TO N STEP I
80     S(J) = 0
90   NEXT J
100 NEXT I
110 PRINT "PRIMES UP TO "; N; ":"
120 FOR I = 2 TO N
130   IF S(I) = 1 THEN PRINT I;
140 NEXT I
150 PRINT
160 END
```

### D.4 string_demo.bas — 문자열 함수

```basic
10 REM STRING FUNCTIONS DEMO
20 A$ = "GW-BASIC INTERPRETER"
30 PRINT "ORIG : "; A$
40 PRINT "LEN  : "; LEN(A$)
50 PRINT "LEFT : "; LEFT$(A$, 7)
60 PRINT "RIGHT: "; RIGHT$(A$, 11)
70 PRINT "MID  : "; MID$(A$, 4, 5)
80 PRINT "UPPER: "; UCASE$(A$)
90 PRINT "LOWER: "; LCASE$(A$)
100 PRINT "REV  : ";
110 FOR I = LEN(A$) TO 1 STEP -1
120   PRINT MID$(A$, I, 1);
130 NEXT I
140 PRINT
150 END
```

### D.5 data_demo.bas — DATA / READ / RESTORE

```basic
10 REM DATA / READ DEMO
20 DIM N$(4)
30 FOR I = 0 TO 4
40   READ N$(I)
50 NEXT I
60 FOR I = 0 TO 4
70   PRINT I; " : "; N$(I)
80 NEXT I
90 RESTORE
100 READ A$
110 PRINT "FIRST AGAIN: "; A$
120 END
200 DATA "MERCURY", "VENUS", "EARTH", "MARS", "JUPITER"
```

### D.6 gosub_demo.bas — GOSUB / DEF FN

```basic
10 REM GOSUB / DEF FN
20 DEF FNSQR(X) = X*X
30 FOR I = 1 TO 5
40   N = I
50   GOSUB 200
60 NEXT I
70 END
200 PRINT "N = "; N; "  N^2 = "; FNSQR(N)
210 RETURN
```

### D.7 ctrl_demo.bas — IF / ELSE / ON GOTO

```basic
10 REM IF/THEN/ELSE & ON GOTO
20 FOR I = 1 TO 6
30   IF I MOD 2 = 0 THEN PRINT I; "EVEN" ELSE PRINT I; "ODD"
40 NEXT I
50 FOR K = 1 TO 4
60   ON K GOTO 100, 110, 120, 130
70 NEXT K
80 END
100 PRINT "ONE": GOTO 70
110 PRINT "TWO": GOTO 70
120 PRINT "THREE": GOTO 70
130 PRINT "FOUR": GOTO 70
```

---

## 부록 E — 참고 문헌과 더 읽을거리

- *Crafting Interpreters*, Robert Nystrom — 트리 워커와 바이트코드 VM 두 단계로 인터프리터를 만드는 정석.
- *Writing An Interpreter In Go*, Thorsten Ball — “Monkey” 언어의 토큰부터 평가까지를 짧게 본다.
- *Writing A Compiler In Go*, Thorsten Ball — 같은 언어를 바이트코드로 끌어내린다.
- *The GW-BASIC User's Guide*, Microsoft, 1987 — 우리가 흉내 낸 언어 명세 자체.
- *MS-BASIC sources* (microsoft/GW-BASIC, GitHub, 2020) — 어셈블리 원본을 공개한 마이크로소프트의 저장소.
- *Engineering a Compiler*, Cooper & Torczon — 컴파일러 이론서. 표현식 우선순위와 SSA 등의 개념을 더 깊게.
- *Modern Compiler Implementation in ML*, Andrew Appel — 클래식.
- 한글 자료: 「만들면서 배우는 컴파일러」 — 국내 도서.

---

## 마치며

한 권의 책이 끝났다. 이 책에서 다룬 1,500줄 남짓의 Lua 코드는 1980년대의 BASIC 인터프리터 한 대분에 거의 일대일로 대응한다. 작은 코드를 한 줄씩 채워 나가는 동안, 우리는 어휘 분석기에서 시작해 우선순위 등반 파서, 백패치, 바이트코드 설계, 호출 스택, 다차원 배열, 사용자 정의 함수, REPL까지 컴파일러/인터프리터 학습의 전 영역을 통과했다.

남은 것은 여러분의 손이다. 위에서 “연습 문제”라고 표시된 항목들 — 토큰화 .BAS 디코더, ON ERROR GOTO, OPEN/CLOSE, 그래픽 명령, 진수 리터럴 — 은 모두 이 책의 골격에 자연스럽게 얹힌다. 한 가지를 골라 먼저 만들어 보길 권한다. 읽기만 한 코드는 사라지고, 직접 짠 코드는 남는다.

— *2026, 봄*
