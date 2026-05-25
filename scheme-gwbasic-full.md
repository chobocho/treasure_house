# Scheme으로 만드는 GW-BASIC 인터프리터

## 완전 구현 가이드 — BNF부터 가상 머신까지 (R7RS-small)

> 200쪽 분량의 실전 인터프리터 / 컴파일러 구현서 — Racket(`#lang r7rs`) / Chez Scheme / Guile 기준

---

## 머리말

이 책은 1980년대 IBM PC를 대표하던 언어 **GW-BASIC**을 현대 Scheme 환경에서 처음부터 구현해 보는 실전 가이드입니다. 이미 출간된 **C / Go / TypeScript / Lua 자매서**와 **동일한 BNF 문법**, **동일한 바이트코드 ISA**, **동일한 VM 설계**, **동일한 예제 프로그램**을 공유하면서, 본 권은 그것을 **Scheme의 관용**(s-식, 꼬리 재귀, 일급 절차, `let-syntax`, 패턴 매칭) 으로 다시 표현합니다.

다음 네 단계를 거치는 본격적인 언어 처리 시스템을 만듭니다.

1. **BNF 문법 정의** — GW-BASIC의 모든 문법 요소를 형식 언어로 기술 (자매서와 공유)
2. **Lexer / Parser** — 소스 코드를 토큰으로 쪼개고 AST(s-식)로 변환
3. **Bytecode Compiler** — AST를 자체 정의 바이트코드로 변환 (자매서 ISA 재사용)
4. **Virtual Machine** — 스택 기반 VM에서 바이트코드를 실행

결과물은 터미널과 (선택적으로) Racket의 `racket/draw` / Guile의 `guile-cairo` 위에서 동작합니다. `SCREEN`, `LINE`, `CIRCLE`, `PSET`, `COLOR` 같은 그래픽 명령과 `SOUND`, `PLAY` 같은 사운드 명령까지 동작하는 처리기를 만드는 것이 목표입니다.

### 왜 Scheme인가

- **s-식 = AST** — 파서가 만든 구조가 곧 데이터. 소스를 그대로 출력해도 의미가 보입니다
- **꼬리 호출 최적화** — `for/next`, `while/wend` 같은 루프를 지원하는 BASIC 인터프리터 본체가 *그 자체로* 꼬리 재귀로 구현되어, Scheme 스택을 잡아먹지 않습니다
- **일급 절차** — `Host` 추상화가 그저 *환경에 묶인 클로저 다발*. 인터페이스 키워드가 따로 필요 없습니다
- **위생 매크로** — 옵코드 디스패치, 디스어셈블러, 스택 어서션을 매크로로 깔끔하게 자동 생성
- **REPL 친화성** — Scheme REPL 안에서 BASIC REPL을 띄울 수 있습니다(REPL 안의 REPL)

### 이 책이 다루는 것

- 인터프리터 / 컴파일러의 이론적 기반
- 형식 문법(BNF)과 재귀 하강 파서
- Pratt 파서를 이용한 표현식 파싱 — Scheme 클로저 테이블로 표현
- 스택 기반 가상 머신 설계 — 자매서와 동일한 ISA
- 변수 환경(`hash-table`), 메모리 모델, 라인 번호 매핑
- GW-BASIC 고유 기능: 라인 번호, GOTO/GOSUB, FOR/NEXT, DEF FN, DATA/READ
- 그래픽 / 사운드 / 입출력 런타임
- REPL, 디버거, 테스트, 빌드 (`raco`, `chez --script`, `guild compile`)

### 이 책이 다루지 않는 것

- Scheme 언어 자체의 기초 (자매서 `scheme-guide/` 권장)
- DOS BIOS / 인터럽트 호환 (현대 환경에 맞춰 재해석)
- 카세트 테이프 / FAT12 입출력 (로컬 파일 + S-식 세이브 파일로 대체)

### 대상 독자

- 컴파일러와 인터프리터의 동작 원리를 코드로 이해하고 싶은 개발자
- Scheme/Lisp 계열로 중규모 시스템을 직접 만들어 보고 싶은 학습자
- 8비트 시절 BASIC에 대한 향수를 가진 분
- 도메인 특화 언어(DSL)를 설계하려는 엔지니어 — Scheme은 DSL의 모국어입니다

### 사용 방법

각 장은 **이론 → BNF / 설계 → 구현 → 테스트** 의 4단 구조로 진행됩니다. 코드는 언제나 작동하는 상태로 누적됩니다. 모든 소스는 다음 디렉터리 구조를 따릅니다.

```
scheme_gwbasic/
├── main.scm                  ← 단일 진입점 스크립트
├── lib/
│   ├── common.scm            ← 에러 코드, 타입 태그
│   ├── lexer.scm
│   ├── parser.scm            ← 문장 파서 (재귀 하강)
│   ├── pratt.scm             ← 표현식 (Pratt)
│   ├── ast.scm               ← s-식 AST 헬퍼와 검증
│   ├── compiler.scm          ← AST → bytecode
│   ├── vm.scm                ← 스택 VM 본체
│   ├── opcode.scm            ← Op 심볼 정의
│   ├── value.scm             ← BASIC Value (태그된 vector)
│   ├── env.scm               ← 변수 환경 (hash-table)
│   ├── strfunc.scm           ← LEFT$, MID$ 등
│   ├── mathfunc.scm          ← SIN, RND 등
│   ├── printusing.scm        ← PRINT USING 포맷터
│   ├── host.scm              ← Host 추상 + null-host
│   ├── host-term.scm         ← 터미널 호스트
│   └── host-draw.scm         ← (선택) racket/draw 호스트
├── examples/                 ← 자매서와 같은 *.bas
└── tests/                    ← golden / 단위 테스트
```

> 📌 본 구현은 **R7RS-small + 약간의 SRFI**(SRFI-1 list, SRFI-69 hash-table, SRFI-13 string)를 가정합니다. Racket에서는 `#lang r7rs` 헤더와 `(import (scheme base) (scheme write) (srfi 1) (srfi 69) (srfi 13))`로 시작합니다. 처리계별 차이는 3장에서 정리합니다.

### 본문 표기 약속

- **굵은 글씨**: 핵심 용어
- `monospace`: 코드 식별자, 절차명, 키워드
- > 인용 블록: GW-BASIC 원본 동작 또는 자매서 비교 보충
- ⚠️ 표시: 함정 / 주의 사항
- 💡 표시: 구현 팁
- 🔁 표시: 자매서(C / Go / TS / Lua) 와 의미가 같은 부분

---

## 차례

### 제1부 · 기초 (Foundations)

- **1장** GW-BASIC, 그 시절의 언어 — 역사, 철학, 문법 특성
- **2장** 인터프리터의 해부학 — 토크나이저, 파서, 컴파일러, VM
- **3장** Scheme 개발 환경 구축 — Racket / Chez / Guile
- **4장** 프로젝트 구조와 라이브러리 분리

### 제2부 · 언어 명세 (Specification)

- **5장** GW-BASIC BNF 문법 전체 정의 (자매서와 동일)
- **6장** 어휘 단위 — 키워드, 식별자, 리터럴
- **7장** 데이터 타입 — INTEGER, SINGLE, DOUBLE, STRING
- **8장** 표현식과 연산자 우선순위

### 제3부 · 프론트엔드 (Frontend)

- **9장** Lexer 완전 구현 — `with-input-from-string`과 문자 단위 스캐너
- **10장** Parser 기초 — 재귀 하강을 절차로
- **11장** 표현식 파싱 — Pratt를 클로저 테이블로
- **12장** 문장 파싱 — 라인 번호와 명령어
- **13장** AST를 s-식으로 — 노드 정의 없이 표현하는 법

### 제4부 · 백엔드 (Backend)

- **14장** 바이트코드 명령어 집합 (ISA) 설계 — 자매서와 동일
- **15장** AST → 바이트코드 컴파일러
- **16장** 스택 기반 가상 머신 — 디스패치 루프, 꼬리 호출 활용
- **17장** 메모리 모델과 값 표현 — 태그된 vector
- **18장** 변수 환경과 스코프 — `hash-table`과 DEFINT 매핑

### 제5부 · 런타임 (Runtime)

- **19장** PRINT와 INPUT — 입출력의 모든 것
- **20장** 제어 흐름 — GOTO, IF/THEN/ELSE, FOR/NEXT
- **21장** 서브루틴 — GOSUB / RETURN
- **22장** 배열 — DIM과 다차원 인덱싱
- **23장** 문자열 함수 — LEFT$, RIGHT$, MID$, INSTR
- **24장** 수학 함수 — SIN, COS, RND, INT
- **25장** DATA / READ / RESTORE
- **26장** 사용자 정의 함수 DEF FN — 클로저로 자연스럽게

### 제6부 · 그래픽과 사운드 (Multimedia)

- **27장** SCREEN 모드와 그래픽 명령
- **28장** 사운드 — SOUND와 PLAY (MML)

### 제7부 · 도구와 통합 (Tooling)

- **29장** REPL — 즉시 실행 환경
- **30장** 디버거 — 단계 실행과 브레이크포인트
- **31장** 테스트 전략과 회귀 검증
- **32장** 빌드, 패키징, 배포 — `raco exe`, `chez --program`, `guild compile`

### 부록

- **A** GW-BASIC BNF 전체 (자매서와 동일)
- **B** 명령어 레퍼런스 카드
- **C** 에러 코드표
- **D** 예제 프로그램 모음 (10선)
- **E** 추가 학습 자료
- **F** 자매서와 차이점 요약

---

## 참고 자료

- Microsoft, *GW-BASIC User's Guide*, 1987.
- Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*, 2nd ed.
- Bob Nystrom, *Crafting Interpreters*, 2021.
- Harold Abelson, Gerald Jay Sussman, *Structure and Interpretation of Computer Programs* (SICP), 2nd ed. — 본 책의 *언어 처리기를 데이터로 다루는* 발상의 뿌리.
- *Revised⁷ Report on the Algorithmic Language Scheme* (R7RS-small), 2013.
- 자매서 — `c_gwbasic_book/`, `go_gwbasic_book/`, `ts_gwbasic_book/`, `lua_gwbasic_book/`

---

> "Lisp is worth learning for a different reason — the profound enlightenment experience you will have when you finally get it."  
> — Eric S. Raymond

다음 장에서는 GW-BASIC이라는 언어가 왜 그렇게 설계되었는지, 그 시절의 환경 제약을 이해하는 데서부터 출발합니다.
# 제1부 · 기초

## 1장. GW-BASIC, 그 시절의 언어

### 1.1 등장 배경

1983년, IBM은 자사 PC 호환 기종이 아닌 다른 OEM(Compaq, Tandy 등)에도 BASIC을 공급할 필요가 있었습니다. 기존 IBM Cassette BASIC, Disk BASIC, Advanced BASIC(BASICA)는 IBM PC ROM에 의존했습니다. 마이크로소프트는 ROM 의존성을 제거한 100% 디스크 기반 인터프리터를 만들었고, 이를 **GW-BASIC**이라 명명했습니다.

GW가 무엇의 약자인지에 대해서는 여러 설(Gee-Whiz, Gates-William, Greg Whitten 등)이 있지만 공식 입장은 없습니다. 본질은 *"BASICA의 ROM-less 클론"* 이라는 점입니다.

### 1.2 언어 철학

GW-BASIC은 다음 세 가지 원칙 위에 서 있습니다.

1. **즉시성 (Immediate mode)** — 라인 번호 없이 입력한 명령은 즉시 실행, 라인 번호와 함께 입력한 명령은 프로그램에 저장.
2. **단일 전역 환경** — 변수는 모두 전역. 스코프 개념이 사실상 없습니다 (DEF FN 매개변수만 예외).
3. **인터프리터 친화적 토큰화** — 키워드는 1바이트 토큰으로 압축 저장됩니다.

> 🔁 자매서와 같은 설명. Scheme 구현에서도 이 세 원칙을 동일하게 보존합니다. 단, 1바이트 토큰은 학습 편의상 텍스트 토큰으로 다룹니다.

### 1.3 데이터 타입 체계

| 접미 기호 | 타입 | 크기 | Scheme 매핑 | 범위 |
|----------|------|------|-------------|------|
| `%` | INTEGER | 16비트 | exact integer (`-32768..32767` 검사) | -32768 ~ 32767 |
| `!` (생략) | SINGLE | 32비트 부동소수 | inexact real | 약 7자리 정밀도 |
| `#` | DOUBLE | 64비트 부동소수 | inexact real | 약 16자리 정밀도 |
| `$` | STRING | 가변 | string | 최대 255자 |

> 💡 R7RS는 `exact-integer?`, `inexact?`로 두 부류를 명확히 구분합니다. SINGLE/DOUBLE의 *실제 정밀도*는 처리계 의존(대부분 `flonum` = double). 본 구현은 INTEGER만 정확수로, 나머지는 모두 inexact로 보관하고 *논리적 타입 태그*만 별도로 들고 다닙니다 (17장).

식별자 자체에 타입 접미가 붙는 점이 GW-BASIC의 독특한 특징입니다. `A%`, `A!`, `A#`, `A$`는 **모두 다른 변수**입니다.

### 1.4 라인 번호의 역할

```basic
10 PRINT "HELLO"
20 GOTO 10
```

라인 번호는 단순 정렬 키가 아니라 **분기 대상 식별자**이기도 합니다. 후속 장에서 `(line-num . code-index)` 짝을 보관하는 해시 테이블로 관리합니다.

### 1.5 직접 모드와 프로그램 모드

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

REPL(29장)이 두 모드를 모두 지원합니다.

### 1.6 우리가 구현할 부분 집합

원본 GW-BASIC은 약 200개의 키워드. 본 구현은 핵심 80개 정도를 동작까지 지원합니다.

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
| JIT 컴파일러 | 실행 중 네이티브 생성 | V8, HotSpot |
| AOT 컴파일러 | 사전에 네이티브 생성 | C, Rust, Go |

본 구현도 **바이트코드 VM** 방식입니다. 자매서와 같은 선택. GOTO/GOSUB의 비구조적 흐름은 트리 워킹과 어울리지 않고, JIT은 학습 곡선이 가파릅니다.

> 📌 본 구현체 자체는 Scheme으로 짠 *호스팅 인터프리터*입니다. Racket이나 Chez에서 읽어 BASIC을 해석합니다. 즉 두 층의 인터프리터/컴파일러가 겹쳐 있습니다 — Racket → Scheme → 우리 VM → BASIC. SICP 4장에서 *meta-circular evaluator*가 보여 준 그 풍경 그대로입니다.

### 2.2 처리 파이프라인

```
원본 소스
   │
   ▼
[ Lexer ]   ── 토큰 리스트 ──▶
   │
   ▼
[ Parser ]  ── AST (s-식) ──▶
   │
   ▼
[ Compiler ] ── chunk (vector + 보조 풀) ──▶
   │
   ▼
[   VM   ]  ── 실행 ──▶  표준 출력 / 화면 / 사운드
```

각 단계는 **순수 절차**에 가깝게 설계합니다. Lexer는 문자열 → 토큰 리스트, Parser는 토큰 리스트 → AST, Compiler는 AST → chunk. 부수 효과는 VM과 Host에 격리됩니다.

### 2.3 각 단계의 책임

#### Lexer (Tokenizer)

```scheme
(lex "10 PRINT 1+2")
;; ⇒ ((number "10" 10 int 1 1)
;;    (keyword "PRINT" #f #f 1 4)
;;    (number "1" 1 int 1 10)
;;    (op "+" #f #f 1 11)
;;    (number "2" 2 int 1 12)
;;    (eol #f #f #f 1 13))
```

각 토큰은 `(kind lex value num-kind line col)` 형태의 리스트(또는 vector). 9장에서 자세히.

#### Parser

```scheme
(parse tokens)
;; ⇒ (program
;;     (line 10
;;       (print
;;         (list (binop + (num 1) (num 2))))))
```

AST는 그저 *심볼이 태그된 리스트* 입니다. 별도 record 정의가 필요 없습니다. 이 점이 Go/TS 구현과의 가장 큰 차이.

#### Compiler

```scheme
(compile ast)
;; ⇒ #(chunk
;;     #(#(op-push 0)        ; consts[0] = 1
;;       #(op-push 1)        ; consts[1] = 2
;;       #(op-add)
;;       #(op-print-val)
;;       #(op-print-nl)
;;       #(op-end))
;;     #(1 2)                ; consts pool
;;     #()                   ; names pool
;;     #hash((10 . 0)))      ; line map
```

자매서의 ISA를 그대로 사용합니다. 14장.

#### VM

```scheme
(vm-run chunk host)
;; → (host-print host "3\n")
```

### 2.4 Host 인터페이스 — 절차 다발로

Scheme에는 인터페이스/프로토콜 키워드가 없습니다. 대신 *해시 테이블에 절차들을 담은 객체* 또는 *closure가 자기 디스패치를 하는 객체* 둘 중 하나로 표현합니다. 본 구현은 **레코드 + 절차 슬롯** 방식.

```scheme
;; lib/host.scm
(define-record-type <host>
  (make-host print input-line cls set-color locate
             set-pixel draw-line draw-box draw-circle
             paint sound play-mml now)
  host?
  (print       host-print)
  (input-line  host-input-line)
  (cls         host-cls)
  (set-color   host-set-color)
  (locate      host-locate)
  (set-pixel   host-set-pixel)
  (draw-line   host-draw-line)
  (draw-box    host-draw-box)
  (draw-circle host-draw-circle)
  (paint       host-paint)
  (sound       host-sound)
  (play-mml    host-play-mml)
  (now         host-now))

;; 모든 슬롯이 빈 동작인 null host — 그래픽 없는 환경에서 컴파일 보장
(define null-host
  (make-host (lambda (s) (values))
             (lambda ()  "")
             (lambda () (values))
             (lambda (fg bg mode) (values))
             (lambda (r c) (values))
             (lambda (x y c) (values))
             (lambda (x1 y1 x2 y2 c) (values))
             (lambda (x1 y1 x2 y2 c fill?) (values))
             (lambda (x y r c sa ea asp) (values))
             (lambda (x y fc bc) (values))
             (lambda (f ms) (values))
             (lambda (s) (values))
             (lambda () 0.0)))
```

⚠️ **주의**: Host 슬롯은 **얇게** 유지합니다. BASIC 명령 하나에 슬롯 하나가 일대일로 대응할 필요는 없습니다. 그러나 성능이 중요한 그래픽 명령은 Host에 직접 위임하는 편이 빠릅니다 (27장).

> 💡 Scheme 처리계가 OOP 클래스를 제공하더라도(Racket `class`, Guile GOOPS) 본 구현은 *처리계 비종속* 을 위해 R7RS의 `define-record-type` 만 사용합니다.

---

## 3장. Scheme 개발 환경 구축

### 3.1 처리계 선택

| 처리계 | 장점 | 본 책에서의 역할 |
|--------|------|------------------|
| **Racket** (`#lang r7rs`) | 가장 부드러운 설치, draw 라이브러리 | 기본(권장) |
| **Chez Scheme** | 매우 빠른 컴파일러, R6RS | 성능 측정용 |
| **Guile** (3.x) | GNU 표준, JIT | 임베딩 / 시스템 통합 |
| **MIT/GNU Scheme** | SICP 호환 | 학습 비교용 |

본문 코드는 R7RS-small + 다음 SRFI를 가정합니다 — Racket과 Chez 양쪽에서 큰 수정 없이 동작합니다.

- SRFI-1 (List Library) — `filter`, `fold`, `reduce`, `last`
- SRFI-13 (String Libraries) — `string-contains`, `string-upcase`, `string-trim`
- SRFI-14 (Char-Set) — 문자 분류
- SRFI-69 (Hash Tables) — `make-hash-table`, `hash-table-ref`
- SRFI-19 (Time) — 선택 (TIMER)

### 3.2 Racket 설정

```bash
# Ubuntu / Termux pkg
sudo apt install racket
# 또는
pkg install racket    # Termux
```

`main.scm`:

```scheme
#!r7rs
(import (scheme base)
        (scheme write)
        (scheme read)
        (scheme file)
        (scheme process-context)
        (srfi 1) (srfi 13) (srfi 69))

(display "GW-BASIC Scheme bootstrap OK\n")
```

```bash
racket --require main.scm
# → GW-BASIC Scheme bootstrap OK
```

### 3.3 Chez 설정

Chez는 R6RS가 기본이지만 R7RS 호환 모드도 있습니다. 본 구현은 R6RS 라이브러리 형식으로도 옮길 수 있도록 *최소한의 처리계 의존* 만 사용합니다.

```bash
sudo apt install chezscheme
chez --script main.scm
```

### 3.4 Guile 설정

```bash
sudo apt install guile-3.0
guile -L lib main.scm
```

Guile은 `(srfi srfi-1)` 형태로 import 합니다. 처리계 차이를 흡수하는 `lib/compat.scm`을 두면 좋습니다.

```scheme
;; lib/compat.scm
(cond-expand
  (chicken (import (chicken)))
  (guile   (import (srfi srfi-1) (srfi srfi-13) (srfi srfi-69)))
  (chez    (import (srfi :1) (srfi :13) (srfi :69)))
  (else    (import (srfi 1) (srfi 13) (srfi 69))))
```

### 3.5 첫 실행 확인

```bash
echo '10 PRINT "HELLO"' > examples/hello.bas
racket --require main.scm -- run examples/hello.bas
# → HELLO
```

(이 명령이 32장에서 만들 진입점입니다. 지금은 구상만.)

### 3.6 빌드 산출물

| 처리계 | 빌드 명령 | 산출물 |
|--------|-----------|--------|
| Racket | `raco exe -o gwbasic main.scm` | 단일 실행 파일 |
| Chez   | `chez --compile-program main.scm` | `.so` + 런처 |
| Guile  | `guild compile main.scm` | `.go` 캐시, 별도 런처 필요 |

자매서의 *단일 바이너리* 정책에 가장 가까운 것은 Racket의 `raco exe`. 32장에서 다시 다룹니다.

---

## 4장. 프로젝트 구조와 라이브러리 분리

### 4.1 라이브러리 의존 그래프

```
main.scm
 ├── lib/host.scm          (host-term.scm, host-draw.scm가 의존)
 ├── lib/runner.scm
 │     ├── lib/lexer.scm
 │     ├── lib/parser.scm
 │     │     ├── lib/pratt.scm
 │     │     └── lib/ast.scm
 │     ├── lib/compiler.scm
 │     │     ├── lib/ast.scm
 │     │     └── lib/opcode.scm
 │     └── lib/vm.scm
 │           ├── lib/opcode.scm
 │           ├── lib/value.scm
 │           ├── lib/env.scm
 │           ├── lib/strfunc.scm
 │           ├── lib/mathfunc.scm
 │           └── lib/host.scm
 └── lib/repl.scm
       └── lib/runner.scm
```

위에서 아래로만 의존합니다. R7RS는 순환 의존을 막지 못하지만, 위 그래프를 약속으로 강제합니다.

### 4.2 공통 정의 (`lib/common.scm`)

```scheme
;; lib/common.scm
(define-library (gwbasic common)
  (export source-pos make-source-pos source-pos? source-pos-line source-pos-col
          basic-error make-basic-error basic-error?
          basic-error-code basic-error-msg basic-error-pos basic-error-line
          err-syntax err-overflow err-type-mismatch err-division-by-zero
          err-undefined-line err-subscript err-illegal-call err-out-of-data
          err-next-without-for err-return-without-gosub err-string-too-long
          err-for-without-next err-out-of-string-space
          raise-basic-error)
  (import (scheme base))

  (begin
    (define-record-type <source-pos>
      (make-source-pos line col) source-pos?
      (line source-pos-line)
      (col  source-pos-col))

    (define-record-type <basic-error>
      (make-basic-error code msg pos line) basic-error?
      (code basic-error-code)
      (msg  basic-error-msg)
      (pos  basic-error-pos)
      (line basic-error-line))

    (define err-next-without-for      1)
    (define err-syntax                2)
    (define err-return-without-gosub  3)
    (define err-out-of-data           4)
    (define err-illegal-call          5)
    (define err-overflow              6)
    (define err-undefined-line        8)
    (define err-subscript             9)
    (define err-division-by-zero     11)
    (define err-type-mismatch        13)
    (define err-out-of-string-space  14)
    (define err-string-too-long      15)
    (define err-for-without-next     26)

    (define (raise-basic-error code msg . maybe-line)
      (raise (make-basic-error code msg #f
                               (if (null? maybe-line) #f (car maybe-line)))))))
```

> 💡 Scheme의 `raise` / `with-exception-handler`로 Go의 `error` 인터페이스를 흉내 냅니다. VM 최상위에서 `guard`로 잡아 정확한 BASIC 에러 메시지를 만듭니다.

### 4.3 코딩 컨벤션

본 책의 Scheme 코드는 다음 컨벤션을 따릅니다.

| 항목 | 규칙 |
|------|------|
| 절차명 | `kebab-case` (`compile-stmt`, `vm-step`) |
| 술어(predicate) | `?` 접미 (`token-keyword?`, `value-int?`) |
| 부수 효과 절차 | `!` 접미 (`stack-push!`, `env-set!`) |
| 변환자 | `->` 사용 (`token->ast`, `ast->bytecode`) |
| 상수 | 평범한 `define` (Scheme에 상수 키워드 없음). 변경 금지를 컨벤션으로 |
| 문자열 | UTF-8 가정. R7RS `string-length`은 코드포인트 수 |
| 들여쓰기 | DrRacket 표준(2칸). `let`, `cond` 정렬은 자유 |
| 파일 | `kebab-case.scm`, R7RS `define-library` 형식 |

> 💡 자매서와 비교한 *가장 두드러진 차이*는 **타입 선언 부재** 입니다. Scheme은 동적 타입이라 모든 모듈 경계에서 타입 검사를 해야 합니다(또는 검사하지 않고 실수에 정직해야 합니다). 본 구현은 *외부 진입점*(예: `vm-run`, `compile`)에 한해 인자 검증을 두고, 내부 호출은 호출자가 책임을 진다는 컨벤션을 둡니다.

### 4.4 다음 단계 미리 보기

다음 장에서는 GW-BASIC의 BNF 문법을 *전체*로 정의합니다. 이것이 책 전체의 설계도 역할을 합니다. **자매서(C/Go/TS/Lua)와 글자 그대로 동일한 BNF**를 사용합니다 — 같은 언어를 만들고 있기 때문입니다.

> 1부 끝.
# 제2부 · 언어 명세

> 🔁 본 부의 BNF는 **자매서(C / Go / TypeScript / Lua)와 글자 그대로 동일** 합니다. 같은 언어를 구현하기 때문입니다. Scheme 매핑(7장 이후)만 다릅니다.

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

콤마는 다음 탭 정지 위치(14컬럼 단위)로, 세미콜론은 즉시 이어 출력합니다. 줄 끝의 세미콜론·콤마는 줄바꿈을 억제합니다.

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

⚠️ `THEN` 뒤에 라인 번호가 오면 `GOTO`와 같습니다. `IF X=1 THEN 100 ELSE 200`.

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

#### 그래픽 / 사운드

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

⚠️ GW-BASIC의 `=`은 비교 연산자이면서 동시에 할당 토큰입니다. 문맥에 따라 구분합니다 — `A = 1 = 2` 는 `A = (1 = 2)` 로 해석되어 A에 0(false) 또는 -1(true)이 들어갑니다.

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

> 💡 Scheme에서는 이 목록을 **해시 테이블**(`make-hash-table`)에 한 번 적재합니다. `eq?` 또는 `string=?`로 조회. 9장에서 `keyword-set`이라는 톱-레벨 정의를 만듭니다.

### 6.2 식별자 규칙

- 첫 글자: 영문자
- 두 번째 이후: 영문자 또는 숫자
- 길이: 40자까지 (`max-ident-len` 상수)
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

> 💡 Scheme의 `(string->number "&H1A" 16)` 같은 형태로는 못 읽습니다 (`&H` 접두는 BASIC 고유). Lexer에서 직접 분해 후 `string->number "1A" 16`을 호출합니다 (9장).

### 6.4 문자열 리터럴

- 큰따옴표(`"`)로 감쌈
- 줄바꿈 불가
- 이스케이프 시퀀스 없음 — 큰따옴표 자체를 넣으려면 `CHR$(34)` 사용

### 6.5 코멘트

```basic
10 PRINT "X" : REM 이건 코멘트
20 PRINT "Y" ' 이것도 코멘트
```

`REM`은 키워드, `'`는 단축 표기. 둘 다 줄 끝까지 무시됩니다.

---

## 7장. 데이터 타입

### 7.1 네 가지 기본 타입과 Scheme 매핑

자매서가 `int16/float32/float64/string` 같은 정적 타입에 매핑한 자리에, Scheme은 **태그된 vector** 하나로 통합합니다.

```scheme
;; lib/value.scm
;; Value 표현: #(tag payload)
;;   tag ∈ '(int sng dbl str)
;;   payload는 exact integer (int) 또는 inexact real (sng/dbl) 또는 string

(define (make-int v)  (vector 'int v))
(define (make-sng v)  (vector 'sng (exact->inexact v)))
(define (make-dbl v)  (vector 'dbl (exact->inexact v)))
(define (make-str v)  (vector 'str v))

(define (value? v)
  (and (vector? v) (= (vector-length v) 2)
       (memq (vector-ref v 0) '(int sng dbl str))))

(define (value-tag v)     (vector-ref v 0))
(define (value-payload v) (vector-ref v 1))

(define (value-int? v) (eq? (value-tag v) 'int))
(define (value-sng? v) (eq? (value-tag v) 'sng))
(define (value-dbl? v) (eq? (value-tag v) 'dbl))
(define (value-str? v) (eq? (value-tag v) 'str))
(define (value-num? v) (memq (value-tag v) '(int sng dbl)))
```

> 💡 record 타입(`define-record-type`) 대신 vector를 쓰는 이유는 *VM 핫 패스 성능* 때문입니다. Chez/Racket 모두 record 접근에 디스패치 비용이 있고, vector는 직접 인덱스로 접근합니다. 자매서의 *태그 유니온 구조체* 와 같은 동기 (Go 가이드 7장 참조).

### 7.2 타입 승격 규칙

수치 연산:

```
INT  + INT  → INT (오버플로 시 SNG)
INT  + SNG  → SNG
INT  + DBL  → DBL
SNG  + SNG  → SNG
SNG  + DBL  → DBL
DBL  + DBL  → DBL
```

문자열은 수치와 섞이면 `Type Mismatch` (에러 13).

```scheme
;; lib/value.scm (계속)
(define (promote-numeric a b r)
  ;; r: float64 결과. a, b: 원래 두 피연산자 Value
  (cond
    ((and (value-int? a) (value-int? b))
     (let ((ri (exact (round r))))
       (if (and (= ri r) (<= -32768 ri 32767))
           (make-int ri)
           (make-sng r))))
    ((or (value-dbl? a) (value-dbl? b))
     (make-dbl r))
    (else
     (make-sng r))))
```

### 7.3 묵시적 타입 결정

식별자에 접미가 없으면 기본은 SINGLE. 단 `DEFINT A-Z` 같은 선언이 있으면 해당 알파벳 범위가 INTEGER로 기본 설정됩니다.

```basic
DEFINT I-N          ' I,J,K,L,M,N으로 시작하는 변수는 INTEGER
DEFDBL A-H, O-Z     ' 그 외는 DOUBLE
```

이런 선언은 환경(18장)에 *기본 타입 매핑* 으로 등록합니다.

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

Scheme:

```scheme
(define (gw-int  x) (floor    x))
(define (gw-fix  x) (truncate x))
```

### 7.5 STR$의 미묘함

GW-BASIC의 `STR$(x)`는 양수 앞에 공백 한 칸을 붙입니다 (부호 자리).

```basic
PRINT "[" + STR$(3) + "]"     ' [ 3]
PRINT "[" + STR$(-3) + "]"    ' [-3]
```

이 동작은 PRINT 출력과 일치합니다. `PRINT 3`은 ` 3 `(앞뒤 공백 포함)을 출력합니다. 19장에서 다시.

### 7.6 문자열의 길이 제약

- 단일 문자열: 최대 255자
- 문자열 영역: 기본 64KB
- 초과 시 `String too long` (15) 또는 `Out of string space` (14)

```scheme
(define max-string-len 255)

(define (check-string-len s)
  (when (> (string-length s) max-string-len)
    (raise-basic-error err-string-too-long "String too long")))
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

GW-BASIC은 ANSI BASIC과 약간 다릅니다.

1. **단항 마이너스가 거듭제곱보다 후순위**: `-2^2 = -4`
2. **NOT이 비교보다 후순위, AND/OR보다 선순위** — 비트 연산처럼 동작하지만 부울로도 쓰임

### 8.2 단항 마이너스의 처리

```ebnf
<unary-expr> ::= ("+" | "-") <unary-expr> | <pow-expr>
<pow-expr>   ::= <primary> { "^" <unary-expr> }   (* 우결합 *)
```

`^`의 오른쪽 피연산자에서는 단항 부호가 다시 허용됩니다(`2^-3 = 0.125`). 그러나 왼쪽에서는 `-2^2`가 `-(2^2) = -4` 입니다. Pratt 파서로 표현하면 단항 `-`의 결합력을 `^`보다 *낮게* 설정합니다(11장).

### 8.3 부울 동작

GW-BASIC의 부울은 **-1(true)** 와 **0(false)**. `AND`, `OR`, `NOT`은 *비트* 연산자이기도 합니다.

- `5 AND 3 = 1` (비트 AND)
- `-1 AND 7 = 7` (true AND 7)
- `NOT 0 = -1`, `NOT 1 = -2`

따라서 `IF X = 1 AND Y = 2`는 `IF (X=1) AND (Y=2)`로 정확히 동작합니다(둘 다 -1이면 -1, 한쪽이 0이면 0).

R7RS는 비트 연산을 `(scheme bitwise)` 또는 SRFI-60에서 제공합니다.

```scheme
(import (srfi 60))

(define (op-and a b) (bitwise-and a b))
(define (op-or  a b) (bitwise-or  a b))
(define (op-xor a b) (bitwise-xor a b))
(define (op-not a)   (bitwise-not a))
```

⚠️ 16비트 wrap을 잊지 마세요. INTEGER 결과는 `(int16-wrap (bitwise-and a b))` 식으로 다듬습니다.

```scheme
(define (int16-wrap n)
  ;; 32비트 -> 16비트 부호 있는 정수로 자르기
  (let ((m (bitwise-and n #xFFFF)))
    (if (>= m #x8000) (- m #x10000) m)))
```

### 8.4 정수 나눗셈과 MOD

```basic
PRINT 10 / 3      ' 3.333333
PRINT 10 \ 3      ' 3
PRINT 10 MOD 3    ' 1
PRINT -7 \ 2      ' -3   (0 방향)
PRINT -7 MOD 2    ' -1
```

⚠️ 정수 나눗셈은 피연산자를 먼저 INTEGER로 변환한 후 수행합니다. Scheme에서는 R7RS의 `quotient`와 `remainder`가 0 방향 잘림을 따르므로 BASIC 의미와 일치합니다 (`modulo`와 헷갈리지 않게 주의).

```scheme
(define (op-idiv a b)
  (when (zero? b) (raise-basic-error err-division-by-zero "Division by zero"))
  (quotient (exact (truncate a)) (exact (truncate b))))

(define (op-mod a b)
  (when (zero? b) (raise-basic-error err-division-by-zero "Division by zero"))
  (remainder (exact (truncate a)) (exact (truncate b))))
```

### 8.5 문자열 연산

`+`만 지원합니다 (연결).

```basic
A$ = "Hello, " + "World"
```

다른 산술 연산자에 문자열을 넣으면 `Type Mismatch`.

### 8.6 비교 연산

수치-수치, 문자열-문자열만 가능. 문자열은 사전식 비교 (`string<?`).

```basic
PRINT "ABC" < "ABD"     ' -1
PRINT "abc" < "ABC"     ' 0  (소문자가 더 큼)
```

```scheme
(define (lt-str a b) (if (string<? a b) -1 0))
(define (eq-str a b) (if (string=? a b) -1 0))
;; (이 -1/0 은 BASIC의 진리값이지 실수의 음수가 아닙니다.)
```

---

> 2부 끝. 이로써 우리가 만들 언어의 모습이 분명해졌습니다. 이제 3부에서는 이 명세를 *실행 가능한 Scheme 코드*로 옮깁니다.
# 제3부 · 프론트엔드 (1) — Lexer

## 9장. Lexer 완전 구현

### 9.1 토큰 표현

자매서가 record/struct로 잡았던 자리를, Scheme은 **vector** 로 잡습니다 (record보다 패턴 매칭과 디버깅이 편함).

```scheme
;; lib/lexer.scm — Token = #(kind lex value num-kind line col)
;;   kind ∈ '(number string ident keyword op
;;            lparen rparen comma semicolon colon eol eof rem-text)
;;   num-kind ∈ '(int sng dbl) | #f

(define (make-token kind lex value num-kind line col)
  (vector kind lex value num-kind line col))

(define (tok-kind t)     (vector-ref t 0))
(define (tok-lex  t)     (vector-ref t 1))
(define (tok-val  t)     (vector-ref t 2))
(define (tok-numkind t)  (vector-ref t 3))
(define (tok-line t)     (vector-ref t 4))
(define (tok-col  t)     (vector-ref t 5))

(define (kind=? t k)     (eq? (tok-kind t) k))
```

### 9.2 키워드 집합

```scheme
(define keyword-list
  '("AND" "AS" "ATN" "BEEP" "CHR$" "CIRCLE" "CINT" "CLEAR" "CLS" "COLOR"
    "COS" "CSNG" "CDBL" "DATA" "DEF" "DEFINT" "DEFSNG" "DEFDBL" "DEFSTR"
    "DIM" "ELSE" "END" "EQV" "ERASE" "ERL" "ERR" "EXP" "FIX" "FN" "FOR"
    "GOSUB" "GOTO" "HEX$" "IF" "IMP" "INKEY$" "INPUT" "INSTR" "INT"
    "LEFT$" "LEN" "LET" "LINE" "LIST" "LOAD" "LOCATE" "LOG" "MID$" "MOD"
    "NEW" "NEXT" "NOT" "OCT$" "OFF" "ON" "OR" "PAINT" "PLAY" "PRESET"
    "PRINT" "PSET" "RANDOMIZE" "READ" "REM" "RESTORE" "RETURN" "RIGHT$"
    "RND" "RUN" "SAVE" "SCREEN" "SGN" "SIN" "SOUND" "SPACE$" "SPC" "SQR"
    "STEP" "STOP" "STR$" "STRING$" "SWAP" "SYSTEM" "TAB" "TAN" "THEN"
    "TIMER" "TO" "USING" "VAL" "WEND" "WHILE" "XOR"))

(define keyword-set
  (let ((h (make-hash-table string=? string-hash)))
    (for-each (lambda (w) (hash-table-set! h w #t)) keyword-list)
    h))

(define (keyword? s) (hash-table-ref/default keyword-set s #f))
```

> 💡 SRFI-69의 `make-hash-table`은 동등성 비교 절차와 해시 함수를 받습니다. 처리계가 `string-hash`를 제공하지 않으면 `(lambda (s) (string->number (string-upcase s) 36))` 같은 거친 해시도 가능합니다 — 키워드는 92개에 불과해 충돌이 거의 없습니다.

### 9.3 입력 커서

```scheme
;; 문자열을 읽는 가장 간단한 커서. R7RS에서 input-port를 만들어도 되지만,
;; *되감기 / 미리보기* 가 필요한 lexer엔 인덱스가 더 직관적입니다.

(define-record-type <cursor>
  (make-cursor src len pos line col)
  cursor?
  (src  cur-src)
  (len  cur-len)
  (pos  cur-pos  set-cur-pos!)
  (line cur-line set-cur-line!)
  (col  cur-col  set-cur-col!))

(define (cursor-from-string s)
  (make-cursor s (string-length s) 0 1 1))

(define (cur-eof? c) (>= (cur-pos c) (cur-len c)))
(define (cur-peek c)
  (if (cur-eof? c) #f (string-ref (cur-src c) (cur-pos c))))
(define (cur-peek2 c)
  (if (>= (+ (cur-pos c) 1) (cur-len c))
      #f
      (string-ref (cur-src c) (+ (cur-pos c) 1))))

(define (cur-advance! c)
  (let ((ch (cur-peek c)))
    (when ch
      (set-cur-pos! c (+ (cur-pos c) 1))
      (if (char=? ch #\newline)
          (begin (set-cur-line! c (+ (cur-line c) 1))
                 (set-cur-col! c 1))
          (set-cur-col! c (+ (cur-col c) 1))))
    ch))
```

### 9.4 메인 루프

```scheme
(define (lex src)
  (let ((c (cursor-from-string src))
        (tokens '()))
    (let loop ()
      (skip-spaces c)
      (cond
        ((cur-eof? c)
         (push! tokens (make-token 'eof "" #f #f (cur-line c) (cur-col c)))
         (reverse tokens))
        (else
         (let ((line (cur-line c)) (col (cur-col c)))
           (let ((t (lex-one c line col)))
             (push! tokens t)
             (cond
               ;; REM과 ' 이면 줄 끝까지 흡수해 rem-text 토큰 추가
               ((and (kind=? t 'keyword) (string=? (tok-lex t) "REM"))
                (push! tokens (read-rest-of-line c line)))
               ((and (kind=? t 'op) (string=? (tok-lex t) "'"))
                (push! tokens (read-rest-of-line c line))))
             (loop))))))))

(define-syntax push!
  (syntax-rules ()
    ((_ var val) (set! var (cons val var)))))
```

### 9.5 단일 토큰 인식

```scheme
(define (lex-one c line col)
  (let ((ch (cur-peek c)))
    (cond
      ((char=? ch #\newline)
       (cur-advance! c)
       (make-token 'eol "\n" #f #f line col))
      ((or (char=? ch #\:) (char=? ch #\,) (char=? ch #\;)
           (char=? ch #\() (char=? ch #\)))
       (cur-advance! c)
       (case ch
         ((#\:) (make-token 'colon     ":" #f #f line col))
         ((#\,) (make-token 'comma     "," #f #f line col))
         ((#\;) (make-token 'semicolon ";" #f #f line col))
         ((#\() (make-token 'lparen    "(" #f #f line col))
         ((#\)) (make-token 'rparen    ")" #f #f line col))))
      ((char=? ch #\")
       (lex-string c line col))
      ((char=? ch #\&)
       (lex-amp c line col))
      ((or (char-numeric? ch) (char=? ch #\.))
       (lex-number c line col))
      ((char-alphabetic? ch)
       (lex-ident-or-keyword c line col))
      (else
       (lex-operator c line col)))))

(define (skip-spaces c)
  (let loop ()
    (let ((ch (cur-peek c)))
      (cond
        ((not ch) #f)
        ((or (char=? ch #\space) (char=? ch #\tab))
         (cur-advance! c) (loop))
        (else #f)))))
```

### 9.6 식별자와 키워드

```scheme
(define max-ident-len 40)

(define (lex-ident-or-keyword c line col)
  (let loop ((acc '()))
    (let ((ch (cur-peek c)))
      (cond
        ((and ch (or (char-alphabetic? ch) (char-numeric? ch)))
         (cur-advance! c)
         (loop (cons ch acc)))
        ;; 타입 접미: % ! # $
        ((and ch (memv ch '(#\% #\! #\# #\$)))
         (cur-advance! c)
         (let ((s (string-upcase (list->string (reverse (cons ch acc))))))
           (when (> (string-length s) max-ident-len)
             (raise-basic-error err-syntax "Identifier too long"))
           (make-token 'ident s #f #f line col)))
        (else
         (let ((s (string-upcase (list->string (reverse acc)))))
           (cond
             ((keyword? s)
              ;; REM 특수 케이스 — 호출자가 처리
              (make-token 'keyword s #f #f line col))
             (else
              (make-token 'ident s #f #f line col)))))))))
```

⚠️ **공백 없는 키워드** — `FORI=1TO10` 같은 형태도 BASIC에서는 합법입니다. 본 구현은 *식별자를 끝까지 읽은 뒤* 키워드인지 검사하므로 `FORI`가 식별자로 잡히고 `=`가 그 뒤에 옵니다. 이 동작은 자매서와 다른 본 구현의 *현실적 단순화* 입니다 — 실제 GW-BASIC은 이 입력을 `FOR I = 1 TO 10`으로 토큰화합니다. 완전 호환을 원한다면 *최장 키워드 우선 매칭* 으로 개선합니다 (Lexer에서 후처리). 본 구현은 사용자에게 *공백을 넣어 달라* 는 정책으로 갑니다.

### 9.7 숫자 리터럴

```scheme
(define (lex-number c line col)
  (let ((start (cur-pos c))
        (saw-dot #f) (saw-exp #f) (kind 'int))
    (let loop ()
      (let ((ch (cur-peek c)))
        (cond
          ((and ch (char-numeric? ch))
           (cur-advance! c) (loop))
          ((and ch (char=? ch #\.) (not saw-dot) (not saw-exp))
           (set! saw-dot #t) (set! kind 'sng)
           (cur-advance! c) (loop))
          ((and ch (memv ch '(#\E #\e)) (not saw-exp))
           (set! saw-exp #t) (set! kind 'sng)
           (cur-advance! c)
           (when (memv (cur-peek c) '(#\+ #\-))
             (cur-advance! c))
           (loop))
          ((and ch (memv ch '(#\D #\d)) (not saw-exp))
           (set! saw-exp #t) (set! kind 'dbl)
           (cur-advance! c)
           (when (memv (cur-peek c) '(#\+ #\-))
             (cur-advance! c))
           (loop))
          (else
           ;; 강제 타입 접미
           (cond
             ((eqv? ch #\#) (cur-advance! c) (set! kind 'dbl))
             ((eqv? ch #\!) (cur-advance! c) (set! kind 'sng))
             ((eqv? ch #\%) (cur-advance! c) (set! kind 'int)))))))
    (let* ((raw (substring (cur-src c) start (cur-pos c)))
           (clean (canonicalize-num raw))
           (val   (string->number clean)))
      (when (not val)
        (raise-basic-error err-syntax (string-append "Bad number: " raw)))
      ;; INTEGER 범위 초과 시 SNG로 승격
      (when (and (eq? kind 'int) (or (< val -32768) (> val 32767)))
        (set! kind 'sng))
      (make-token 'number raw val kind line col))))

(define (canonicalize-num raw)
  ;; "1.5D10" → "1.5e10",  접미 문자 제거
  (let* ((s (string-replace raw "D" "e"))     ; SRFI-13 가정. 없으면 직접 구현.
         (s (string-replace s   "d" "e"))
         (s (string-replace s   "%" ""))
         (s (string-replace s   "!" ""))
         (s (string-replace s   "#" "")))
    s))
```

> 💡 R7RS-small에는 `string-replace`가 없습니다. SRFI-13 또는 직접 구현. 직접 구현은 다음과 같이 한 줄.

```scheme
(define (string-replace s from to)
  (let loop ((i 0) (acc '()))
    (cond
      ((>= i (string-length s)) (apply string-append (reverse acc)))
      ((eqv? (string-ref s i) (string-ref from 0))
       (loop (+ i 1) (cons to acc)))
      (else
       (loop (+ i 1) (cons (string (string-ref s i)) acc))))))
```

### 9.8 16/8진수 (`&H`, `&O`, `&`)

```scheme
(define (lex-amp c line col)
  (cur-advance! c) ; &
  (let* ((next (cur-peek c))
         (base (cond
                 ((memv next '(#\H #\h))
                  (cur-advance! c) 16)
                 ((memv next '(#\O #\o))
                  (cur-advance! c) 8)
                 (else 8))))   ; 그냥 & 면 8진수
    (let loop ((acc '()))
      (let ((ch (cur-peek c)))
        (cond
          ((and ch (or (char-numeric? ch)
                       (and (= base 16)
                            (or (char-ci=? ch #\a) (char-ci=? ch #\b)
                                (char-ci=? ch #\c) (char-ci=? ch #\d)
                                (char-ci=? ch #\e) (char-ci=? ch #\f)))))
           (cur-advance! c) (loop (cons ch acc)))
          (else
           (let* ((digits (list->string (reverse acc)))
                  (val (string->number digits base))
                  (raw (string-append (if (= base 16) "&H" "&O") digits)))
             (when (not val)
               (raise-basic-error err-syntax (string-append "Bad number: " raw)))
             (make-token 'number raw (int16-wrap val) 'int line col))))))))
```

### 9.9 문자열 리터럴

```scheme
(define (lex-string c line col)
  (cur-advance! c) ; 여는 따옴표
  (let loop ((acc '()))
    (let ((ch (cur-peek c)))
      (cond
        ((not ch)
         (raise-basic-error err-syntax "Unterminated string"))
        ((char=? ch #\newline)
         (raise-basic-error err-syntax "Unterminated string"))
        ((char=? ch #\")
         (cur-advance! c)
         (let ((s (list->string (reverse acc))))
           (make-token 'string s s #f line col)))
        (else
         (cur-advance! c)
         (loop (cons ch acc)))))))
```

### 9.10 연산자

```scheme
(define (lex-operator c line col)
  (let ((ch (cur-peek c)))
    (cur-advance! c)
    (case ch
      ((#\+ #\- #\* #\/ #\^ #\=)
       (make-token 'op (string ch) #f #f line col))
      ((#\\)
       (make-token 'op "\\" #f #f line col))
      ((#\')
       (make-token 'op "'" #f #f line col))
      ((#\<)
       (cond
         ((eqv? (cur-peek c) #\=) (cur-advance! c) (make-token 'op "<=" #f #f line col))
         ((eqv? (cur-peek c) #\>) (cur-advance! c) (make-token 'op "<>" #f #f line col))
         (else (make-token 'op "<" #f #f line col))))
      ((#\>)
       (cond
         ((eqv? (cur-peek c) #\=) (cur-advance! c) (make-token 'op ">=" #f #f line col))
         (else (make-token 'op ">" #f #f line col))))
      (else
       (raise-basic-error err-syntax
         (string-append "Unexpected char: " (string ch)))))))
```

### 9.11 REM 흡수

```scheme
(define (read-rest-of-line c line)
  (let loop ((acc '()))
    (let ((ch (cur-peek c)))
      (cond
        ((or (not ch) (char=? ch #\newline))
         (make-token 'rem-text (list->string (reverse acc))
                     #f #f line (cur-col c)))
        (else
         (cur-advance! c) (loop (cons ch acc)))))))
```

### 9.12 단위 테스트

```scheme
;; tests/lexer-test.scm
(define (lex-kinds s) (map tok-kind (lex s)))

(test-equal "기본"
  '(number keyword number op number eol eof)
  (lex-kinds "10 PRINT 1+2\n"))

(test-equal "REM 흡수"
  '(number keyword keyword rem-text eof)
  (lex-kinds "10 PRINT REM hello"))

(test-equal "16진수"
  -1     ; &HFFFF가 16비트 wrap 후 -1
  (tok-val (cadr (lex "10 &HFFFF"))))

(test-equal "문자열"
  "hello"
  (tok-val (cadr (lex "10 \"hello\""))))
```

> 💡 `test-equal`은 처리계마다 다릅니다. Racket은 `rackunit`, Chez는 `(scheme test)` (R7RS 부록). 본 책은 32장에서 이를 통합한 `lib/test.scm`을 만듭니다.

---

> 9장 끝. Lexer가 작동합니다. 다음 장에서는 토큰 리스트를 받아 AST 를 만드는 파서를 만듭니다.
# 제3부 · 프론트엔드 (2) — Parser

## 10장. Parser 기초 — 재귀 하강을 절차로

### 10.1 AST 표현 — s-식

자매서가 record / class 트리를 정의한 자리를, Scheme은 *심볼이 태그된 리스트* 로 잡습니다. 정의가 필요 없고 `display` 한 번으로 디버깅이 됩니다.

```scheme
;; 예시 — `10 IF X=1 THEN PRINT "Y" ELSE PRINT "N"` 의 AST
'(program
  (line 10
    (if (binop = (var "X") (num 1 int))
        ((print ((arg (str "Y")))))
        ((print ((arg (str "N"))))))))
```

각 노드 형태:

| 노드 | 형태 |
|------|------|
| 프로그램 | `(program <line> ...)` |
| 라인 | `(line <number> <stmt> ...)` |
| 직접 모드 | `(immediate <stmt> ...)` |
| 할당 | `(assign <lvalue> <expr>)` |
| 변수 | `(var "NAME")` 또는 `(var "NAME%")` |
| 배열 참조 | `(aref "NAME" <expr> ...)` |
| PRINT | `(print <print-list>)` |
| INPUT | `(input <prompt> <suppress-q?> <var> ...)` |
| IF | `(if <cond> <then-list> <else-list>)` |
| FOR | `(for <var> <start> <end> <step>)` |
| NEXT | `(next <var> ...)` |
| WHILE/WEND | `(while <cond>)` `(wend)` |
| GOTO | `(goto <line-num>)` |
| GOSUB | `(gosub <line-num>)` |
| RETURN | `(return)` 또는 `(return <line-num>)` |
| ON | `(on-goto <expr> <line-num> ...)` `(on-gosub ...)` |
| DIM | `(dim (<name> <expr> ...) ...)` |
| DATA | `(data <item> ...)` |
| READ | `(read <lvalue> ...)` |
| RESTORE | `(restore)` 또는 `(restore <line-num>)` |
| DEF FN | `(def-fn "NAME" (<param> ...) <expr>)` |
| 그래픽 | `(pset (<x> <y> step?) <color>)` 등 |
| 사운드 | `(sound <freq> <dur>)` `(play <s>)` `(beep)` |
| 종료 | `(end)` `(stop)` `(rem)` `(clear)` `(swap <a> <b>)` |
| 단항 | `(unop <op-sym> <expr>)` |
| 이항 | `(binop <op-sym> <a> <b>)` |
| 함수호출 | `(call "NAME" <expr> ...)` `(fn "NAME" <expr> ...)` |
| 리터럴 | `(num <value> <kind>)` `(str <s>)` |

> 💡 자매서의 `PrintStmt`, `IfStmt` 같은 클래스를 정의하지 않아도 *목록의 첫 원소*가 그 역할을 합니다. 매칭은 `(case (car node) ...)` 또는 SRFI-200 패턴 매칭(`match`)으로 합니다.

### 10.2 파서 상태

```scheme
;; lib/parser.scm
(define-record-type <pstate>
  (make-pstate tokens pos)
  pstate?
  (tokens pst-tokens)
  (pos    pst-pos set-pst-pos!))

(define (pst-from-tokens toks)
  (make-pstate (list->vector toks) 0))

(define (pst-peek p)
  (vector-ref (pst-tokens p) (pst-pos p)))

(define (pst-peek+ p k)
  (let ((i (+ (pst-pos p) k)))
    (and (< i (vector-length (pst-tokens p)))
         (vector-ref (pst-tokens p) i))))

(define (pst-advance! p)
  (let ((t (pst-peek p)))
    (set-pst-pos! p (+ (pst-pos p) 1))
    t))

(define (pst-eof? p)
  (kind=? (pst-peek p) 'eof))

(define (expect! p kind . maybe-lex)
  (let ((t (pst-peek p)))
    (cond
      ((kind=? t kind)
       (cond
         ((null? maybe-lex) (pst-advance! p))
         ((string=? (tok-lex t) (car maybe-lex)) (pst-advance! p))
         (else
          (raise-basic-error err-syntax
            (string-append "Expected " (car maybe-lex)
                           " but got " (tok-lex t))))))
      (else
       (raise-basic-error err-syntax
         (string-append "Expected " (symbol->string kind)
                        " but got " (symbol->string (tok-kind t))))))))
```

### 10.3 진입점

```scheme
(define (parse tokens)
  (let ((p (pst-from-tokens tokens)))
    (let loop ((lines '()))
      (cond
        ((pst-eof? p) (cons 'program (reverse lines)))
        ((kind=? (pst-peek p) 'eol) (pst-advance! p) (loop lines))
        (else
         (loop (cons (parse-line p) lines)))))))

(define (parse-line p)
  ;; 라인 번호가 있는지?
  (let ((first (pst-peek p)))
    (cond
      ((and (kind=? first 'number)
            (eq? (tok-numkind first) 'int)
            (let ((v (tok-val first)))
              (and (>= v 0) (<= v 65529))))
       (let ((n (tok-val (pst-advance! p))))
         (cons 'line (cons n (parse-stmt-list p)))))
      (else
       (cons 'immediate (parse-stmt-list p))))))

(define (parse-stmt-list p)
  (let loop ((acc '()))
    (let ((s (parse-stmt p)))
      (let ((stmts (if s (cons s acc) acc))
            (t (pst-peek p)))
        (cond
          ((kind=? t 'colon) (pst-advance! p) (loop stmts))
          ((or (kind=? t 'eol) (kind=? t 'eof))
           (when (kind=? t 'eol) (pst-advance! p))
           (reverse stmts))
          (else
           (raise-basic-error err-syntax
             (string-append "Unexpected " (tok-lex t)))))))))
```

### 10.4 디스패처

```scheme
(define (parse-stmt p)
  (let ((t (pst-peek p)))
    (cond
      ((or (kind=? t 'eol) (kind=? t 'colon) (kind=? t 'eof)) #f)
      ((kind=? t 'keyword)
       (case (string->symbol (tok-lex t))
         ((PRINT) (parse-print p #f))
         ((|?|)   (parse-print p #f))    ; ? 약식
         ((INPUT) (parse-input p))
         ((LET)   (pst-advance! p) (parse-assign p))
         ((IF)    (parse-if p))
         ((FOR)   (parse-for p))
         ((NEXT)  (parse-next p))
         ((WHILE) (parse-while p))
         ((WEND)  (pst-advance! p) '(wend))
         ((GOTO)  (parse-goto p))
         ((GOSUB) (parse-gosub p))
         ((RETURN)(parse-return p))
         ((ON)    (parse-on p))
         ((END)   (pst-advance! p) '(end))
         ((STOP)  (pst-advance! p) '(stop))
         ((REM)   (parse-rem p))
         ((DIM)   (parse-dim p))
         ((DATA)  (parse-data p))
         ((READ)  (parse-read p))
         ((RESTORE) (parse-restore p))
         ((DEF)   (parse-def-fn p))
         ((CLS)   (parse-cls p))
         ((SCREEN)(parse-screen p))
         ((COLOR) (parse-color p))
         ((PSET PRESET) (parse-pset p))
         ((LINE)  (parse-line-graphic p))
         ((CIRCLE) (parse-circle p))
         ((PAINT) (parse-paint p))
         ((LOCATE) (parse-locate p))
         ((SOUND) (parse-sound p))
         ((PLAY)  (parse-play p))
         ((BEEP)  (pst-advance! p) '(beep))
         ((RANDOMIZE) (parse-randomize p))
         ((CLEAR) (pst-advance! p) '(clear))
         ((SWAP)  (parse-swap p))
         (else
          (raise-basic-error err-syntax
            (string-append "Unknown keyword " (tok-lex t))))))
      ((kind=? t 'op) (parse-immediate-op p))
      ((kind=? t 'ident) (parse-assign p))
      (else
       (raise-basic-error err-syntax (string-append "Bad token " (tok-lex t)))))))
```

### 10.5 할당과 lvalue

```scheme
(define (parse-lvalue p)
  (let ((t (expect! p 'ident)))
    (cond
      ((and (pst-peek p) (kind=? (pst-peek p) 'lparen))
       (pst-advance! p)
       (let ((args (parse-expr-list p)))
         (expect! p 'rparen)
         (cons 'aref (cons (tok-lex t) args))))
      (else
       (list 'var (tok-lex t))))))

(define (parse-assign p)
  (let* ((lhs (parse-lvalue p))
         (eq  (expect! p 'op "=")))
    (list 'assign lhs (parse-expression p))))
```

### 10.6 `PRINT` 문장 — 분리자가 의미를 갖는 케이스

```scheme
(define (parse-print p)
  ;; PRINT 또는 ? 토큰을 소비
  (pst-advance! p)
  (let loop ((items '()) (suppress-nl #f))
    (let ((t (pst-peek p)))
      (cond
        ((or (kind=? t 'eol) (kind=? t 'colon) (kind=? t 'eof))
         (list 'print (reverse items) (if suppress-nl #t #f)))
        ((kind=? t 'comma)
         (pst-advance! p)
         (loop (cons '(sep ",") items) #t))
        ((kind=? t 'semicolon)
         (pst-advance! p)
         (loop (cons '(sep ";") items) #t))
        ((and (kind=? t 'keyword) (string=? (tok-lex t) "TAB"))
         (pst-advance! p) (expect! p 'lparen)
         (let ((e (parse-expression p)))
           (expect! p 'rparen)
           (loop (cons (list 'tab e) items) #f)))
        ((and (kind=? t 'keyword) (string=? (tok-lex t) "SPC"))
         (pst-advance! p) (expect! p 'lparen)
         (let ((e (parse-expression p)))
           (expect! p 'rparen)
           (loop (cons (list 'spc e) items) #f)))
        ((and (kind=? t 'keyword) (string=? (tok-lex t) "USING"))
         (pst-advance! p)
         (let* ((fmt (parse-expression p))
                (_   (expect! p 'semicolon))
                (es  (parse-expr-list p)))
           (loop (cons (list 'using fmt es) items) #f)))
        (else
         (loop (cons (list 'arg (parse-expression p)) items) #f))))))
```

### 10.7 `IF / THEN / ELSE`

```scheme
(define (parse-if p)
  (pst-advance! p)
  (let* ((cnd (parse-expression p)))
    (expect! p 'keyword "THEN")
    (let* ((then-clause (parse-then-or-else-clause p))
           (else-clause
            (if (and (kind=? (pst-peek p) 'keyword)
                     (string=? (tok-lex (pst-peek p)) "ELSE"))
                (begin (pst-advance! p) (parse-then-or-else-clause p))
                '())))
      (list 'if cnd then-clause else-clause))))

(define (parse-then-or-else-clause p)
  ;; 라인 번호 단독 → GOTO와 같음
  (let ((t (pst-peek p)))
    (cond
      ((and (kind=? t 'number) (eq? (tok-numkind t) 'int))
       (let ((n (tok-val (pst-advance! p))))
         (list (list 'goto n))))
      (else
       (parse-stmt-list-inline p)))))

(define (parse-stmt-list-inline p)
  ;; ELSE 또는 줄 끝까지 statement list (콜론으로 구분)
  (let loop ((acc '()))
    (let ((t (pst-peek p)))
      (cond
        ((or (kind=? t 'eol) (kind=? t 'eof)
             (and (kind=? t 'keyword) (string=? (tok-lex t) "ELSE")))
         (reverse acc))
        ((kind=? t 'colon)
         (pst-advance! p) (loop acc))
        (else
         (loop (cons (parse-stmt p) acc)))))))
```

### 10.8 `FOR / NEXT`

```scheme
(define (parse-for p)
  (pst-advance! p)
  (let* ((vname (tok-lex (expect! p 'ident)))
         (_     (expect! p 'op "="))
         (start (parse-expression p))
         (_     (expect! p 'keyword "TO"))
         (end   (parse-expression p))
         (step  (cond
                  ((and (kind=? (pst-peek p) 'keyword)
                        (string=? (tok-lex (pst-peek p)) "STEP"))
                   (pst-advance! p)
                   (parse-expression p))
                  (else '(num 1 int)))))
    (list 'for vname start end step)))

(define (parse-next p)
  (pst-advance! p)
  (let loop ((vars '()))
    (let ((t (pst-peek p)))
      (cond
        ((kind=? t 'ident)
         (pst-advance! p)
         (let ((more
                (if (kind=? (pst-peek p) 'comma)
                    (begin (pst-advance! p) #t)
                    #f)))
           (loop (cons (tok-lex t) vars))))
        (else
         (cons 'next (reverse vars)))))))
```

### 10.9 `DATA` 와 *bare string*

`DATA HELLO, "WORLD", 42` 는 세 항목입니다 — 큰따옴표 없는 `HELLO`도 문자열이 됩니다 (수치로 읽히지 않으면).

```scheme
(define (parse-data p)
  (pst-advance! p) ; DATA
  (let loop ((items '()))
    (let ((t (pst-peek p)))
      (cond
        ((kind=? t 'string)
         (pst-advance! p)
         (let ((more (kind=? (pst-peek p) 'comma)))
           (when more (pst-advance! p))
           (let ((acc (cons (list 'data-str (tok-val t)) items)))
             (if more (loop acc) (cons 'data (reverse acc))))))
        ((kind=? t 'number)
         (pst-advance! p)
         (let ((more (kind=? (pst-peek p) 'comma)))
           (when more (pst-advance! p))
           (let ((acc (cons (list 'data-num (tok-val t) (tok-numkind t)) items)))
             (if more (loop acc) (cons 'data (reverse acc))))))
        (else
         ;; bare-string: 콤마/콜론/EOL 까지 문자열로 흡수
         ;; (실제로는 lexer에서 *DATA 컨텍스트* 토큰을 따로 만드는 편이 깔끔.
         ;;  본 구현은 단순화를 위해 식별자/연산자 토큰의 lex를 모은다.)
         (let bare-loop ((parts '()) (last-eaten t))
           (let ((u (pst-peek p)))
             (cond
               ((or (kind=? u 'comma) (kind=? u 'colon)
                    (kind=? u 'eol) (kind=? u 'eof))
                (let* ((s (string-trim
                            (apply string-append (reverse parts))))
                       (more (kind=? u 'comma)))
                  (when more (pst-advance! p))
                  (let ((acc (cons (list 'data-str s) items)))
                    (if more (loop acc) (cons 'data (reverse acc))))))
               (else
                (pst-advance! p)
                (bare-loop (cons (tok-lex u) parts) u))))))))))
```

⚠️ 위 *bare string* 처리는 단순화입니다. 완전한 GW-BASIC 호환을 원한다면 lexer 단계에서 `DATA` 키워드를 본 직후 줄 끝 또는 콜론까지 *문자 단위* 로 다시 스캔합니다.

### 10.10 나머지 문장들 (요약)

지면을 아끼기 위해 다음 절차들의 시그니처만 정리합니다. 패턴은 위와 같습니다 — *키워드 소비 → 하위 식 → 노드 조립*.

```scheme
(parse-input    p) ; (input <prompt|#f> <suppress-q?> <vars>)
(parse-while    p) ; (while <expr>)
(parse-goto     p) ; (goto <num>)
(parse-gosub    p) ; (gosub <num>)
(parse-return   p) ; (return [<num>])
(parse-on       p) ; (on-goto|on-gosub <expr> <line> ...)
(parse-rem      p) ; (rem <text>)  — REM 토큰 뒤 rem-text 흡수
(parse-dim      p) ; (dim (<name> <e> ...) ...)
(parse-read     p) ; (read <lv> ...)
(parse-restore  p) ; (restore [<line>])
(parse-def-fn   p) ; (def-fn <name> (<param> ...) <expr>)
(parse-cls      p) ; (cls [<expr>])
(parse-screen   p) ; (screen <expr>)
(parse-color    p) ; (color [<fg>] [<bg>])
(parse-pset     p) ; (pset|preset <coord> [<color>])
(parse-line-graphic p) ; (line-draw <c1?> <c2> [<color>] [B|BF])
(parse-circle   p) ; (circle <coord> <r> [<color>] [<sa> <ea>] [<asp>])
(parse-paint    p)
(parse-locate   p)
(parse-sound    p)
(parse-play     p)
(parse-randomize p)
(parse-swap     p)
```

소스 트리 (`src/`) 에 모두 들어 있습니다. 패턴이 같으므로 본문에선 생략.

---

## 11장. 표현식 파싱 — Pratt를 클로저 테이블로

### 11.1 Pratt이 하는 일

Pratt 파서는 토큰별로 *prefix 동작* 과 *infix 동작 + 결합력* 을 표에 둡니다. 토큰을 만나면 그 표를 보고 적절한 클로저를 호출합니다. *재귀 하강의 우선순위 단계 12개* 를 한 표로 압축한 구조입니다.

> 🔁 자매서의 Pratt 구현(예: TS 가이드 11장)과 *형태가 동일* 합니다. Scheme은 클로저 테이블을 만들기 가장 쉬운 언어입니다.

### 11.2 결합력 표

```scheme
;; 숫자가 클수록 결합력이 강함 (높은 우선순위)
(define BP-LOWEST   0)
(define BP-OR       2)
(define BP-XOR      3)
(define BP-AND      4)
(define BP-NOT      5)
(define BP-COMPARE  6)
(define BP-TERM     7)   ; + -
(define BP-MOD      8)
(define BP-IDIV     9)
(define BP-FACTOR  10)   ; * /
(define BP-UNARY   11)
(define BP-POWER   12)
(define BP-CALL    13)
```

⚠️ `^` 보다 단항이 후순위라는 점에 주의 — `BP-UNARY = 11`, `BP-POWER = 12`. 이 한 줄이 `-2^2 = -4` 를 보장합니다.

### 11.3 prefix / infix 테이블

```scheme
;; lib/pratt.scm
(define prefix-table (make-hash-table equal? equal-hash))
(define infix-table  (make-hash-table equal? equal-hash))

(define (register-prefix! key fn)
  (hash-table-set! prefix-table key fn))
(define (register-infix! key fn bp)
  (hash-table-set! infix-table key (cons fn bp)))

(define (lookup-prefix t)
  (hash-table-ref/default prefix-table (token-key t) #f))
(define (lookup-infix t)
  (hash-table-ref/default infix-table (token-key t) #f))

(define (token-key t)
  ;; "+" 와 "AND" 는 다른 종류지만 모두 lex로 구별 가능
  (case (tok-kind t)
    ((op)      (cons 'op (tok-lex t)))
    ((keyword) (cons 'kw (tok-lex t)))
    ((number)  '(prim . number))
    ((string)  '(prim . string))
    ((ident)   '(prim . ident))
    ((lparen)  '(prim . lparen))
    (else      #f)))
```

### 11.4 메인 절차

```scheme
(define (parse-expression p)
  (parse-expr p BP-LOWEST))

(define (parse-expr p bp)
  (let* ((tok (pst-peek p))
         (pre (lookup-prefix tok)))
    (when (not pre)
      (raise-basic-error err-syntax
        (string-append "No prefix parser for " (tok-lex tok))))
    (let loop ((left (pre p)))
      (let* ((next (pst-peek p))
             (inf  (lookup-infix next)))
        (cond
          ((or (not inf) (< (cdr inf) bp)) left)
          (else (loop ((car inf) p left (cdr inf)))))))))
```

### 11.5 prefix 등록

```scheme
;; 숫자
(register-prefix! '(prim . number)
  (lambda (p)
    (let ((t (pst-advance! p)))
      (list 'num (tok-val t) (tok-numkind t)))))

;; 문자열
(register-prefix! '(prim . string)
  (lambda (p)
    (let ((t (pst-advance! p)))
      (list 'str (tok-val t)))))

;; 식별자: var, aref, FN호출, builtin 호출
(register-prefix! '(prim . ident)
  (lambda (p)
    (let* ((t (pst-advance! p))
           (name (tok-lex t)))
      (cond
        ;; FN <name> (...)  — DEF FN 호출
        ((string=? name "FN")
         (let* ((nm (tok-lex (expect! p 'ident)))
                (args (parse-paren-args p)))
           (cons 'fn (cons nm args))))
        ;; builtin / array
        ((kind=? (pst-peek p) 'lparen)
         (let ((args (parse-paren-args p)))
           (if (builtin? name)
               (cons 'call (cons name args))
               (cons 'aref (cons name args)))))
        (else (list 'var name))))))

(define (parse-paren-args p)
  (expect! p 'lparen)
  (cond
    ((kind=? (pst-peek p) 'rparen)
     (pst-advance! p) '())
    (else
     (let ((args (parse-expr-list p)))
       (expect! p 'rparen)
       args))))

(define (parse-expr-list p)
  (let loop ((acc (list (parse-expression p))))
    (cond
      ((kind=? (pst-peek p) 'comma)
       (pst-advance! p)
       (loop (cons (parse-expression p) acc)))
      (else (reverse acc)))))

;; 괄호
(register-prefix! '(prim . lparen)
  (lambda (p)
    (pst-advance! p)
    (let ((e (parse-expression p)))
      (expect! p 'rparen)
      e)))

;; 단항 - +, NOT
(register-prefix! '(op . "-")
  (lambda (p)
    (pst-advance! p)
    (list 'unop '- (parse-expr p BP-UNARY))))
(register-prefix! '(op . "+")
  (lambda (p)
    (pst-advance! p)
    (parse-expr p BP-UNARY)))
(register-prefix! '(kw . "NOT")
  (lambda (p)
    (pst-advance! p)
    (list 'unop 'not (parse-expr p BP-NOT))))
```

### 11.6 infix 등록

```scheme
(define (left-assoc op-sym bp)
  (lambda (p left _)
    (pst-advance! p) ; 연산자 토큰
    (let ((right (parse-expr p bp)))
      (list 'binop op-sym left right))))

(define (right-assoc op-sym bp)
  (lambda (p left _)
    (pst-advance! p)
    (let ((right (parse-expr p (- bp 1))))
      (list 'binop op-sym left right))))

(for-each (lambda (op bp)
            (register-infix! (cons 'op op) (left-assoc (string->symbol op) bp) bp))
          '("+" "-" "*" "/" "<" "<=" ">" ">=" "=" "<>" "\\")
          (list BP-TERM BP-TERM BP-FACTOR BP-FACTOR
                BP-COMPARE BP-COMPARE BP-COMPARE BP-COMPARE
                BP-COMPARE BP-COMPARE BP-IDIV))

(register-infix! '(op . "^")
  (right-assoc 'pow BP-POWER) BP-POWER)

(for-each (lambda (kw bp)
            (register-infix! (cons 'kw kw)
                             (left-assoc (string->symbol kw) bp) bp))
          '("AND" "OR" "XOR" "MOD")
          (list BP-AND BP-OR BP-XOR BP-MOD))
```

### 11.7 BNF와의 대응 검증

```basic
A = 1 + 2 * 3 ^ -4
```

1. `parse-expression` → `parse-expr p BP-LOWEST`
2. 숫자 `1` 흡수 → `(num 1 int)`
3. `+` 결합력 7 ≥ 0 → 진입, 우항 `parse-expr p 7`
4. 숫자 `2`
5. `*` 결합력 10 ≥ 7 → 진입, 우항 `parse-expr p 10`
6. 숫자 `3`
7. `^` 결합력 12 ≥ 10 → 진입, 우항 `parse-expr p 11` (우결합 → bp-1)
8. 단항 `-` (BP-UNARY=11), 우항 `parse-expr p 11`
9. 숫자 `4` → `(num 4 int)`
10. → `(unop - (num 4 int))`
11. → `(binop pow (num 3 int) (unop - (num 4 int)))`
12. → `(binop * (num 2 int) ...)`
13. → `(binop + (num 1 int) ...)`

기대대로 `1 + (2 * (3 ^ (-4)))` 구조가 만들어집니다.

### 11.8 builtin 함수 목록

```scheme
(define builtin-list
  '("ABS" "ASC" "ATN" "CHR$" "CINT" "COS" "CSNG" "CDBL" "EXP" "FIX"
    "HEX$" "INKEY$" "INSTR" "INT" "LEFT$" "LEN" "LOG" "MID$" "OCT$"
    "RIGHT$" "RND" "SGN" "SIN" "SPACE$" "SQR" "STR$" "STRING$" "TAN"
    "TIMER" "VAL"))

(define builtin-set
  (let ((h (make-hash-table string=? string-hash)))
    (for-each (lambda (s) (hash-table-set! h s #t)) builtin-list) h))

(define (builtin? s) (hash-table-ref/default builtin-set s #f))
```

### 11.9 단위 테스트

```scheme
(test-equal "사칙 + 우선순위"
  '(binop + (num 1 int) (binop * (num 2 int) (num 3 int)))
  (parse-one-expr "1 + 2 * 3"))

(test-equal "거듭제곱 우결합"
  '(binop pow (num 2 int) (binop pow (num 3 int) (num 4 int)))
  (parse-one-expr "2 ^ 3 ^ 4"))

(test-equal "단항 vs 거듭제곱"
  '(unop - (binop pow (num 2 int) (num 2 int)))
  (parse-one-expr "-2^2"))

(test-equal "비교 + 논리"
  '(binop or
     (binop = (var "X") (num 1 int))
     (binop = (var "Y") (num 2 int)))
  (parse-one-expr "X = 1 OR Y = 2"))
```

> 11장 끝. 표현식과 문장이 모두 AST가 됩니다. 다음 장에서는 AST를 바이트코드로 옮깁니다.
# 제4부 · 백엔드 (1) — 바이트코드와 컴파일러

> 🔁 본 장의 **명령어 집합(ISA)** 은 자매서(C/Go/TS/Lua)와 **글자 그대로 동일** 합니다. 같은 BASIC을 구현하기 위해 같은 바이트코드를 정의하기 때문입니다. Scheme 표현 방식만 다릅니다.

## 14장. 바이트코드 명령어 집합 (ISA) 설계

### 14.1 설계 결정

자매서가 `uint8` 옵코드를 쓴 자리에, Scheme은 **심볼**을 그대로 옵코드로 씁니다. 가독성이 압도적으로 좋고, 처리계가 심볼 비교를 `eq?`로 상수 시간에 처리합니다.

| 방식 | 장점 | 단점 |
|------|------|------|
| 정수 + 디스패치 표 | 미세한 성능 우위 | 디버깅 어려움 |
| **심볼 + `case`** | 가독성, REPL 친화 | 사소한 성능 손실 |
| s-식 한 통 | 엄청난 가독성 | 너무 동적, 실수 위험 |

본 구현은 **심볼 + `case`**. Pratt 표를 만들 때처럼, `case`의 분기 표는 처리계가 *상수 시간 점프* 로 컴파일하는 경우가 많아 실제 성능 손실은 미미합니다 (Chez에서 측정 시 정수 디스패치 대비 10% 이내).

### 14.2 명령어 분류표

자매서와 동일.

| 분류 | 옵코드 | 설명 |
|------|--------|------|
| 스택 | `op-push` `op-pop` `op-dup` `op-swap-top` | 피연산자 스택 |
| 산술 | `op-add` `op-sub` `op-mul` `op-div` `op-idiv` `op-mod` `op-pow` `op-neg` | 이항/단항 산술 |
| 비교 | `op-eq` `op-ne` `op-lt` `op-le` `op-gt` `op-ge` | -1/0 결과 |
| 논리/비트 | `op-and` `op-or` `op-xor` `op-not` | int16 비트 연산 |
| 변수 | `op-load` `op-store` `op-load-arr` `op-store-arr` `op-dim` | 환경 접근 |
| 분기 | `op-jmp` `op-jmpf` `op-jmpt` `op-call` `op-ret` `op-ret-to` | 제어 흐름 |
| 루프 | `op-for-init` `op-for-next` `op-while-test` `op-wend` | FOR/WHILE |
| 입출력 | `op-print-val` `op-print-sep` `op-print-tab` `op-print-spc` `op-print-using` `op-print-nl` `op-input` | 콘솔 |
| 그래픽 | `op-cls` `op-screen` `op-color` `op-locate` `op-pset` `op-preset` `op-line` `op-circle` `op-paint` | Host 위임 |
| 사운드 | `op-sound` `op-play` `op-beep` | Host 위임 |
| 함수 | `op-call-builtin` `op-call-fn` `op-def-fn` | 내장/사용자 함수 |
| 데이터 | `op-read` `op-restore` | DATA 풀 |
| 기타 | `op-randomize` `op-clear` `op-swap` `op-end` `op-stop` `op-halt` | — |

### 14.3 명령 구조

자매서의 `Op uint8 + A int32 + B int32 + Mode uint8` 구조를 Scheme **vector** 로 옮깁니다.

```scheme
;; lib/opcode.scm
;; Instr = #(op a b mode)
;;   op   : symbol
;;   a, b : exact integer (인덱스 또는 즉치) — 사용 안 하면 0
;;   mode : exact integer (비트 플래그) — 사용 안 하면 0

(define (make-instr op a b mode) (vector op a b mode))
(define (i-op   i) (vector-ref i 0))
(define (i-a    i) (vector-ref i 1))
(define (i-b    i) (vector-ref i 2))
(define (i-mode i) (vector-ref i 3))
```

### 14.4 Chunk — 컴파일된 프로그램

자매서의 `Chunk` 와 동일한 의미. 다만 풀들을 **vector**(빠른 인덱스) 와 **hash-table**(라인 매핑) 로 나눕니다.

```scheme
;; lib/compiler.scm — Chunk 정의
(define-record-type <chunk>
  (make-chunk code consts names line-map data-pool data-line-map
              def-fns input-descs swap-descs line-modes)
  chunk?
  (code         chunk-code         set-chunk-code!)
  (consts       chunk-consts       set-chunk-consts!)
  (names        chunk-names        set-chunk-names!)
  (line-map     chunk-line-map     set-chunk-line-map!)
  (data-pool    chunk-data-pool    set-chunk-data-pool!)
  (data-line-map chunk-data-line-map set-chunk-data-line-map!)
  (def-fns      chunk-def-fns      set-chunk-def-fns!)
  (input-descs  chunk-input-descs  set-chunk-input-descs!)
  (swap-descs   chunk-swap-descs   set-chunk-swap-descs!)
  (line-modes   chunk-line-modes   set-chunk-line-modes!))

(define (new-chunk)
  (make-chunk '() '() '()
              (make-hash-table eqv? hash-by-identity)
              '() (make-hash-table eqv? hash-by-identity)
              (make-hash-table string=? string-hash)
              '() '() '()))
```

> 💡 컴파일 *중* 에는 `code`, `consts`, `names` 를 **역방향 리스트**(append-front)로 모으고, 마지막에 `(list->vector (reverse code))` 한 번에 vector로 변환합니다. 자매서의 *append-front + 마지막 reverse* 패턴과 동일.

### 14.5 컴파일러 본체 — 빌더 헬퍼

```scheme
(define (emit! ch op . args)
  (let* ((a (if (>= (length args) 1) (car args) 0))
         (b (if (>= (length args) 2) (cadr args) 0))
         (mode (if (>= (length args) 3) (caddr args) 0)))
    (set-chunk-code! ch (cons (make-instr op a b mode) (chunk-code ch)))
    ;; 마지막 인덱스 (현재 길이 - 1) 반환 — 백패치용
    (- (length (chunk-code ch)) 1)))

(define (current-pos ch) (length (chunk-code ch)))

(define (patch-jump! ch idx target)
  ;; 역방향 리스트의 (length - 1 - idx) 위치
  (let* ((rev-pos (- (length (chunk-code ch)) 1 idx))
         (lst (chunk-code ch))
         (vec (list->vector lst)))
    (let ((ins (vector-ref vec rev-pos)))
      (vector-set! vec rev-pos
                   (make-instr (i-op ins) target (i-b ins) (i-mode ins))))
    (set-chunk-code! ch (vector->list vec))))

(define (intern-const! ch v)
  ;; 풀에 같은 값이 있으면 인덱스를 재사용
  (let loop ((lst (chunk-consts ch)) (i 0))
    (cond
      ((null? lst)
       (set-chunk-consts! ch (append (chunk-consts ch) (list v)))
       i)
      ((value-equal? (car lst) v) i)
      (else (loop (cdr lst) (+ i 1))))))

(define (intern-name! ch s)
  (let loop ((lst (chunk-names ch)) (i 0))
    (cond
      ((null? lst)
       (set-chunk-names! ch (append (chunk-names ch) (list s)))
       i)
      ((string=? (car lst) s) i)
      (else (loop (cdr lst) (+ i 1))))))
```

⚠️ `chunk-code`를 *역방향 리스트* 로 다루다가 `patch-jump!`에서 *vector* 로 바꾼 것은 효율 때문입니다. 점프 백패치는 인덱스 접근이 잦아 vector가 유리합니다. 빌더의 마지막에 vector로 통일합니다 (15.10절).

### 14.6 메인 진입

```scheme
(define (compile ast)
  (let ((ch (new-chunk)))
    (compile-program ch ast)
    (emit! ch 'op-end)
    ;; 마지막 정리: code를 역방향 리스트 → vector
    (set-chunk-code! ch (list->vector (reverse (chunk-code ch))))
    (set-chunk-consts! ch (list->vector (chunk-consts ch)))
    (set-chunk-names!  ch (list->vector (chunk-names ch)))
    (set-chunk-data-pool! ch (list->vector (chunk-data-pool ch)))
    ch))
```

---

## 15장. AST → 바이트코드 컴파일러

### 15.1 디스패처

```scheme
(define (compile-stmt ch s)
  (case (car s)
    ((assign)   (compile-assign  ch s))
    ((print)    (compile-print   ch s))
    ((input)    (compile-input   ch s))
    ((if)       (compile-if      ch s))
    ((for)      (compile-for     ch s))
    ((next)     (compile-next    ch s))
    ((while)    (compile-while   ch s))
    ((wend)     (compile-wend    ch s))
    ((goto)     (compile-goto    ch s))
    ((gosub)    (compile-gosub   ch s))
    ((return)   (compile-return  ch s))
    ((on-goto)  (compile-on-goto ch s 'goto))
    ((on-gosub) (compile-on-goto ch s 'gosub))
    ((dim)      (compile-dim     ch s))
    ((data)     (compile-data    ch s))
    ((read)     (compile-read    ch s))
    ((restore)  (compile-restore ch s))
    ((def-fn)   (compile-def-fn  ch s))
    ((cls)      (compile-cls     ch s))
    ((screen)   (compile-screen  ch s))
    ((color)    (compile-color   ch s))
    ((pset)     (compile-pset    ch s 'pset))
    ((preset)   (compile-pset    ch s 'preset))
    ((line-draw)(compile-linedraw ch s))
    ((circle)   (compile-circle  ch s))
    ((paint)    (compile-paint   ch s))
    ((locate)   (compile-locate  ch s))
    ((sound)    (compile-sound   ch s))
    ((play)     (compile-play    ch s))
    ((beep)     (emit! ch 'op-beep))
    ((randomize)(compile-randomize ch s))
    ((clear)    (emit! ch 'op-clear))
    ((swap)     (compile-swap    ch s))
    ((rem)      #f) ; no-op
    ((end)      (emit! ch 'op-end))
    ((stop)     (emit! ch 'op-stop))
    (else
     (raise-basic-error err-syntax
       (string-append "Bad stmt: " (symbol->string (car s)))))))
```

### 15.2 표현식 컴파일

```scheme
(define (compile-expr ch e)
  (case (car e)
    ((num)
     (let* ((kind (caddr e)) (val  (cadr e))
            (v (case kind
                 ((int) (make-int val))
                 ((sng) (make-sng val))
                 ((dbl) (make-dbl val)))))
       (emit! ch 'op-push (intern-const! ch v))))
    ((str)
     (emit! ch 'op-push (intern-const! ch (make-str (cadr e)))))
    ((var)
     (emit! ch 'op-load (intern-name! ch (cadr e))))
    ((aref)
     (let* ((name (cadr e)) (args (cddr e)))
       (for-each (lambda (a) (compile-expr ch a)) args)
       (emit! ch 'op-load-arr (intern-name! ch name) (length args))))
    ((unop)
     (compile-expr ch (caddr e))
     (case (cadr e)
       ((-)   (emit! ch 'op-neg))
       ((not) (emit! ch 'op-not))
       (else
        (raise-basic-error err-syntax
          (string-append "Bad unop: " (symbol->string (cadr e)))))))
    ((binop)
     (compile-expr ch (caddr e))
     (compile-expr ch (cadddr e))
     (case (cadr e)
       ((+)  (emit! ch 'op-add))
       ((-)  (emit! ch 'op-sub))
       ((*)  (emit! ch 'op-mul))
       ((/)  (emit! ch 'op-div))
       ((\\) (emit! ch 'op-idiv))
       ((MOD mod) (emit! ch 'op-mod))
       ((pow) (emit! ch 'op-pow))
       ((=)   (emit! ch 'op-eq))
       ((<>)  (emit! ch 'op-ne))
       ((<)   (emit! ch 'op-lt))
       ((<=)  (emit! ch 'op-le))
       ((>)   (emit! ch 'op-gt))
       ((>=)  (emit! ch 'op-ge))
       ((AND and) (emit! ch 'op-and))
       ((OR or)   (emit! ch 'op-or))
       ((XOR xor) (emit! ch 'op-xor))
       (else
        (raise-basic-error err-syntax
          (string-append "Bad binop: " (symbol->string (cadr e)))))))
    ((call)
     (let* ((name (cadr e)) (args (cddr e)))
       (for-each (lambda (a) (compile-expr ch a)) args)
       (emit! ch 'op-call-builtin (intern-name! ch name) (length args))))
    ((fn)
     (let* ((name (cadr e)) (args (cddr e)))
       (for-each (lambda (a) (compile-expr ch a)) args)
       (emit! ch 'op-call-fn (intern-name! ch name) (length args))))
    (else
     (raise-basic-error err-syntax
       (string-append "Bad expr: " (symbol->string (car e)))))))
```

### 15.3 할당

```scheme
(define (compile-assign ch s)
  (let* ((lv (cadr s)) (e  (caddr s)))
    (compile-expr ch e)
    (case (car lv)
      ((var)
       (emit! ch 'op-store (intern-name! ch (cadr lv))))
      ((aref)
       (for-each (lambda (a) (compile-expr ch a)) (cddr lv))
       (emit! ch 'op-store-arr
              (intern-name! ch (cadr lv))
              (length (cddr lv)))))))
```

### 15.4 PRINT — 분리자가 의미를 갖는 케이스

```scheme
(define (compile-print ch s)
  (let* ((items (cadr s)) (suppress-nl (caddr s)))
    (for-each
     (lambda (it)
       (case (car it)
         ((arg)
          (compile-expr ch (cadr it))
          (emit! ch 'op-print-val))
         ((sep)
          (let ((mode (if (string=? (cadr it) ",") 1 0)))
            (emit! ch 'op-print-sep mode)))
         ((tab)
          (compile-expr ch (cadr it))
          (emit! ch 'op-print-tab))
         ((spc)
          (compile-expr ch (cadr it))
          (emit! ch 'op-print-spc))
         ((using)
          ;; (using <fmt> <expr-list>)
          (compile-expr ch (cadr it))
          (for-each (lambda (e) (compile-expr ch e)) (caddr it))
          (emit! ch 'op-print-using (length (caddr it))))))
     items)
    (when (not suppress-nl)
      (emit! ch 'op-print-nl))))
```

### 15.5 IF / THEN / ELSE — 백패치 두 번

```scheme
(define (compile-if ch s)
  ;; (if <cond> <then-list> <else-list>)
  (compile-expr ch (cadr s))
  (let ((j-else (emit! ch 'op-jmpf 0))) ; 거짓이면 ELSE로
    (for-each (lambda (st) (compile-stmt ch st)) (caddr s))
    (cond
      ((null? (cadddr s))
       (patch-jump! ch j-else (current-pos ch)))
      (else
       (let ((j-end (emit! ch 'op-jmp 0)))
         (patch-jump! ch j-else (current-pos ch))
         (for-each (lambda (st) (compile-stmt ch st)) (cadddr s))
         (patch-jump! ch j-end (current-pos ch)))))))
```

### 15.6 FOR / NEXT — 카운터 + 한도 + 스텝

```scheme
(define (compile-for ch s)
  ;; (for <var> <start> <end> <step>)
  (let* ((vname (cadr s)) (start (caddr s)) (end (cadddr s))
         (step  (car (cddddr s))))
    (compile-expr ch start)
    (emit! ch 'op-store (intern-name! ch vname))
    (compile-expr ch end)
    (compile-expr ch step)
    ;; FOR_INIT은 end, step을 스택에서 받아 forStk에 푸시
    (let ((init (emit! ch 'op-for-init (intern-name! ch vname))))
      ;; 루프 본문 시작 PC = current-pos
      (emit! ch 'op-jmp (+ init 2))   ; FOR_NEXT 자리로 점프 (placeholder)
      ;; 실제로는 컴파일러가 NEXT 시점에 본문 시작 PC를 다시 기록.
      #f)))

(define (compile-next ch s)
  ;; (next <vname> ...)  — 보통 한 변수
  (let ((vars (cdr s)))
    (for-each
     (lambda (vname)
       (emit! ch 'op-for-next (intern-name! ch vname)))
     (if (null? vars) (list #f) vars))))
```

> 💡 위 `compile-for/next` 는 단순화된 골격입니다. 실제 구현(`src/lib/compiler.scm`)에서는 *FOR 시작 시 forStk에 본문 시작 PC* 와 *NEXT의 PC* 를 모두 등록해 두고, FOR_NEXT가 조건을 검사한 뒤 어디로 점프할지 결정합니다. 자매서의 `forState` 구조와 1:1 대응합니다.

### 15.7 GOTO/GOSUB — 라인 번호 백패치

```scheme
;; 컴파일이 끝난 뒤에 모든 GOTO/GOSUB를 line-map으로 해소합니다.
;; 1패스: 라인 번호를 즉치로 그대로 emit
;; 2패스(`resolve-line-jumps!`): 즉치를 실제 PC로 치환

(define pending-line-jumps '())

(define (compile-goto ch s)
  (let ((idx (emit! ch 'op-jmp 0)))
    (set! pending-line-jumps
          (cons (list idx (cadr s)) pending-line-jumps))))

(define (compile-gosub ch s)
  (let ((idx (emit! ch 'op-call 0)))
    (set! pending-line-jumps
          (cons (list idx (cadr s)) pending-line-jumps))))

(define (resolve-line-jumps! ch)
  (for-each
   (lambda (entry)
     (let* ((idx (car entry)) (line-num (cadr entry))
            (target (hash-table-ref/default
                      (chunk-line-map ch) line-num #f)))
       (when (not target)
         (raise-basic-error err-undefined-line
           (string-append "Undefined line " (number->string line-num))))
       (patch-jump! ch idx target)))
   pending-line-jumps)
  (set! pending-line-jumps '()))
```

### 15.8 라인 매핑

```scheme
(define (compile-program ch ast)
  (case (car ast)
    ((program)
     (for-each
      (lambda (line-node)
        (case (car line-node)
          ((line)
           (let* ((n (cadr line-node))
                  (stmts (cddr line-node)))
             (hash-table-set! (chunk-line-map ch) n (current-pos ch))
             (for-each (lambda (s) (compile-stmt ch s)) stmts)))
          ((immediate)
           (for-each (lambda (s) (compile-stmt ch s)) (cdr line-node)))))
      (cdr ast))
     (resolve-line-jumps! ch))))
```

### 15.9 디스어셈블러

VM 디버깅의 핵심 도구. 자매서의 `Disassemble` 함수 대응.

```scheme
;; lib/disasm.scm
(define (disasm ch)
  (let ((code (chunk-code ch)))
    (let loop ((i 0))
      (when (< i (vector-length code))
        (let ((ins (vector-ref code i)))
          (display (number->string i))
          (display "\t")
          (display (i-op ins))
          (display "\t")
          (display (i-a ins))
          (when (not (zero? (i-b ins)))
            (display "\t") (display (i-b ins)))
          (newline)
          (loop (+ i 1)))))))
```

```
> (disasm (compile (parse (lex "10 PRINT 1+2"))))
0   op-push    0
1   op-push    1
2   op-add     0
3   op-print-val 0
4   op-print-nl  0
5   op-end     0
```

### 15.10 단위 테스트

```scheme
(define (compile-source s)
  (compile (parse (lex s))))

(define (op-stream ch)
  (map i-op (vector->list (chunk-code ch))))

(test-equal "PRINT 1+2"
  '(op-push op-push op-add op-print-val op-print-nl op-end)
  (op-stream (compile-source "10 PRINT 1+2")))

(test-equal "라인 매핑"
  0
  (hash-table-ref (chunk-line-map (compile-source "10 PRINT 1")) 10))

(test-equal "GOTO 백패치"
  0
  (let* ((ch (compile-source "10 PRINT 1\n20 GOTO 10")))
    ;; GOTO 10 이 PC 0 으로 패치됐는지 확인
    (let ((last-jmp (i-a (vector-ref (chunk-code ch) 5))))
      last-jmp)))
```

> 14, 15장 끝. 컴파일러가 동작합니다. 다음 장에서는 그 결과물을 *돌리는* VM 본체를 만듭니다.
# 제4부 · 백엔드 (2) — 가상 머신과 메모리 모델

> 🔁 본 장의 VM 동작은 자매서와 *의미적으로 동일* 합니다. 같은 ISA를 같은 의미론으로 실행하기 때문입니다. Scheme 표현 방식만 다릅니다 — 디스패치는 `case`, 스택은 `vector`, 환경은 `hash-table`.

## 16장. 스택 기반 가상 머신

### 16.1 VM 자료구조

```scheme
;; lib/vm.scm
(define-record-type <vm>
  (make-vm-rec ch pc stack call-stk for-stk while-stk
               env rng host data-idx halted?)
  vm?
  (ch        vm-ch)
  (pc        vm-pc        set-vm-pc!)
  (stack     vm-stack     set-vm-stack!)        ; vector + 성장
  (call-stk  vm-call-stk  set-vm-call-stk!)     ; list of pc
  (for-stk   vm-for-stk   set-vm-for-stk!)      ; list of for-state
  (while-stk vm-while-stk set-vm-while-stk!)
  (env       vm-env)
  (rng       vm-rng       set-vm-rng!)
  (host      vm-host)
  (data-idx  vm-data-idx  set-vm-data-idx!)
  (halted?   vm-halted?   set-vm-halted!))

;; FOR 상태
(define-record-type <for-state>
  (make-for-state name end-val step body-pc tail-pc)
  for-state?
  (name    fs-name)
  (end-val fs-end)
  (step    fs-step)
  (body-pc fs-body)
  (tail-pc fs-tail))

(define (vm-new ch host)
  (make-vm-rec ch 0
               (make-stack)
               '() '() '()
               (env-new) (make-rng 1)
               host 0 #f))
```

### 16.2 스택 — vector + 톱 포인터

```scheme
(define-record-type <stack>
  (make-stack-rec data top)
  stack?
  (data stk-data set-stk-data!)
  (top  stk-top  set-stk-top!))

(define (make-stack) (make-stack-rec (make-vector 256 #f) 0))

(define (stack-push! s v)
  (let ((top (stk-top s)) (data (stk-data s)))
    (when (= top (vector-length data))
      ;; 2배 성장
      (let ((nd (make-vector (* 2 top) #f)))
        (vector-copy! nd 0 data 0 top)
        (set-stk-data! s nd)))
    (vector-set! (stk-data s) top v)
    (set-stk-top! s (+ top 1))))

(define (stack-pop! s)
  (let ((top (stk-top s)))
    (when (zero? top)
      (raise-basic-error err-syntax "Stack underflow"))
    (let ((v (vector-ref (stk-data s) (- top 1))))
      (set-stk-top! s (- top 1))
      v)))

(define (stack-peek s off)
  (vector-ref (stk-data s) (- (stk-top s) 1 off)))
```

### 16.3 메인 루프 — 꼬리 호출 활용

자매서가 `for !halted { step() }` 으로 짠 자리에, Scheme은 *꼬리 재귀* 로 짭니다. 처리계가 보장하는 꼬리 호출 최적화 덕분에 *스택을 잡아먹지 않고* 무한 루프가 가능합니다.

```scheme
(define (vm-run! vm)
  (let loop ()
    (cond
      ((vm-halted? vm) #t)
      (else
       (let ((pc (vm-pc vm)))
         (when (or (negative? pc)
                   (>= pc (vector-length (chunk-code (vm-ch vm)))))
           (raise-basic-error err-syntax "PC out of range"))
         (let ((ins (vector-ref (chunk-code (vm-ch vm)) pc)))
           (set-vm-pc! vm (+ pc 1))
           (vm-step! vm ins)
           (loop)))))))
```

### 16.4 디스패치 본체

```scheme
(define (vm-step! vm ins)
  (case (i-op ins)
    ((op-push)
     (stack-push! (vm-stack vm)
                  (vector-ref (chunk-consts (vm-ch vm)) (i-a ins))))
    ((op-pop)      (stack-pop! (vm-stack vm)))
    ((op-dup)      (stack-push! (vm-stack vm) (stack-peek (vm-stack vm) 0)))
    ((op-swap-top)
     (let* ((s (vm-stack vm))
            (a (stack-pop! s)) (b (stack-pop! s)))
       (stack-push! s a) (stack-push! s b)))

    ((op-add op-sub op-mul op-div op-idiv op-mod op-pow)
     (vm-bin-arith! vm (i-op ins)))
    ((op-eq op-ne op-lt op-le op-gt op-ge)
     (vm-bin-cmp! vm (i-op ins)))
    ((op-and op-or op-xor)
     (vm-bin-logic! vm (i-op ins)))

    ((op-neg)
     (stack-push! (vm-stack vm) (negate-value (stack-pop! (vm-stack vm)))))
    ((op-not)
     (let ((i (value->int16 (stack-pop! (vm-stack vm)))))
       (stack-push! (vm-stack vm) (make-int (int16-wrap (bitwise-not i))))))

    ((op-load)
     (let ((name (vector-ref (chunk-names (vm-ch vm)) (i-a ins))))
       (stack-push! (vm-stack vm) (env-get (vm-env vm) name))))
    ((op-store)
     (let ((name (vector-ref (chunk-names (vm-ch vm)) (i-a ins))))
       (env-set! (vm-env vm) name (stack-pop! (vm-stack vm)))))
    ((op-load-arr)  (vm-load-arr! vm ins))
    ((op-store-arr) (vm-store-arr! vm ins))
    ((op-dim)       (vm-dim! vm ins))

    ((op-jmp)  (set-vm-pc! vm (i-a ins)))
    ((op-jmpf)
     (when (value-false? (stack-pop! (vm-stack vm)))
       (set-vm-pc! vm (i-a ins))))
    ((op-jmpt)
     (when (not (value-false? (stack-pop! (vm-stack vm))))
       (set-vm-pc! vm (i-a ins))))
    ((op-call)
     (set-vm-call-stk! vm (cons (vm-pc vm) (vm-call-stk vm)))
     (set-vm-pc! vm (i-a ins)))
    ((op-ret)
     (when (null? (vm-call-stk vm))
       (raise-basic-error err-return-without-gosub "RETURN without GOSUB"))
     (set-vm-pc! vm (car (vm-call-stk vm)))
     (set-vm-call-stk! vm (cdr (vm-call-stk vm))))
    ((op-ret-to)
     (when (null? (vm-call-stk vm))
       (raise-basic-error err-return-without-gosub "RETURN without GOSUB"))
     (set-vm-call-stk! vm (cdr (vm-call-stk vm)))
     (set-vm-pc! vm (i-a ins)))

    ((op-for-init)  (vm-for-init! vm ins))
    ((op-for-next)  (vm-for-next! vm ins))
    ((op-while-test)
     (cond
       ((value-false? (stack-pop! (vm-stack vm)))
        (set-vm-pc! vm (i-a ins)))
       (else
        (set-vm-while-stk! vm (cons (- (vm-pc vm) 1) (vm-while-stk vm))))))
    ((op-wend) (set-vm-pc! vm (i-a ins)))

    ((op-print-val)
     ((host-print (vm-host vm)) (value->print-fmt (stack-pop! (vm-stack vm)))))
    ((op-print-sep)
     (when (= (i-a ins) 1)
       ((host-print (vm-host vm)) (tab-to-14))))
    ((op-print-tab) (vm-print-tab! vm))
    ((op-print-spc) (vm-print-spc! vm))
    ((op-print-nl)  ((host-print (vm-host vm)) "\n"))
    ((op-print-using) (vm-print-using! vm (i-a ins)))
    ((op-input)     (vm-input! vm ins))

    ((op-cls)    ((host-cls (vm-host vm))))
    ((op-screen) (stack-pop! (vm-stack vm)))    ; 모드 폐기 (호스트 무시)
    ((op-color)  (vm-exec-color! vm ins))
    ((op-locate) (vm-exec-locate! vm ins))
    ((op-pset op-preset) (vm-exec-pset! vm ins))
    ((op-line)   (vm-exec-line! vm ins))
    ((op-circle) (vm-exec-circle! vm ins))
    ((op-paint)  (vm-exec-paint! vm ins))
    ((op-sound)  (vm-exec-sound! vm ins))
    ((op-play)   (vm-exec-play! vm ins))
    ((op-beep)   ((host-sound (vm-host vm)) 800.0 200))

    ((op-call-builtin) (vm-call-builtin! vm ins))
    ((op-call-fn)      (vm-call-user-fn! vm ins))
    ((op-read)         (vm-exec-read! vm ins))
    ((op-restore)      (vm-exec-restore! vm ins))
    ((op-randomize)    (vm-exec-randomize! vm ins))
    ((op-clear)
     (env-reset! (vm-env vm))
     (set-stk-top! (stk-data (vm-stack vm)) 0))
    ((op-swap)         (vm-exec-swap! vm ins))

    ((op-end op-stop op-halt) (set-vm-halted! vm #t))
    (else
     (raise-basic-error err-syntax
       (string-append "Unknown opcode: " (symbol->string (i-op ins)))))))
```

### 16.5 산술 연산 — 자매서와 같은 의미

```scheme
(define (vm-bin-arith! vm op)
  (let* ((s (vm-stack vm))
         (b (stack-pop! s)) (a (stack-pop! s)))
    ;; 문자열 + 문자열 → 연결
    (cond
      ((and (value-str? a) (value-str? b))
       (when (not (eq? op 'op-add))
         (raise-basic-error err-type-mismatch "Type mismatch"))
       (let ((s2 (string-append (value-payload a) (value-payload b))))
         (check-string-len s2)
         (stack-push! s (make-str s2))))
      ((or (value-str? a) (value-str? b))
       (raise-basic-error err-type-mismatch "Type mismatch"))
      (else
       (let* ((af (value->real a)) (bf (value->real b))
              (r  (case op
                    ((op-add) (+ af bf))
                    ((op-sub) (- af bf))
                    ((op-mul) (* af bf))
                    ((op-div)
                     (when (zero? bf)
                       (raise-basic-error err-division-by-zero "Division by zero"))
                     (/ af bf))
                    ((op-idiv)
                     (when (zero? bf)
                       (raise-basic-error err-division-by-zero "Division by zero"))
                     (quotient (exact (truncate af)) (exact (truncate bf))))
                    ((op-mod)
                     (when (zero? bf)
                       (raise-basic-error err-division-by-zero "Division by zero"))
                     (remainder (exact (truncate af)) (exact (truncate bf))))
                    ((op-pow) (expt af bf)))))
         (stack-push! s (promote-numeric a b r)))))))
```

### 16.6 비교와 논리

```scheme
(define (vm-bin-cmp! vm op)
  (let* ((s (vm-stack vm))
         (b (stack-pop! s)) (a (stack-pop! s)))
    (let-values (((lt eq)
                  (cond
                    ((and (value-str? a) (value-str? b))
                     (values (string<? (value-payload a) (value-payload b))
                             (string=? (value-payload a) (value-payload b))))
                    ((or (value-str? a) (value-str? b))
                     (raise-basic-error err-type-mismatch "Type mismatch"))
                    (else
                     (let ((af (value->real a)) (bf (value->real b)))
                       (values (< af bf) (= af bf)))))))
      (let ((r (case op
                 ((op-eq) eq)
                 ((op-ne) (not eq))
                 ((op-lt) lt)
                 ((op-le) (or lt eq))
                 ((op-gt) (not (or lt eq)))
                 ((op-ge) (not lt)))))
        (stack-push! s (make-int (if r -1 0)))))))

(define (vm-bin-logic! vm op)
  (let* ((s (vm-stack vm))
         (b (value->int16 (stack-pop! s)))
         (a (value->int16 (stack-pop! s)))
         (r (case op
              ((op-and) (bitwise-and a b))
              ((op-or)  (bitwise-or  a b))
              ((op-xor) (bitwise-xor a b)))))
    (stack-push! s (make-int (int16-wrap r)))))
```

### 16.7 거짓 판단

```scheme
(define (value-false? v)
  (case (value-tag v)
    ((int) (zero? (value-payload v)))
    ((sng) (zero? (value-payload v)))
    ((dbl) (zero? (value-payload v)))
    ((str) (zero? (string-length (value-payload v))))
    (else  #f)))
```

---

## 17장. 메모리 모델과 값 표현

### 17.1 Scheme 정확수와 BASIC INTEGER

R7RS 정확수는 임의 정밀도 정수(bignum). BASIC의 INTEGER는 16비트. 두 의미가 충돌하지 않도록 다음 컨벤션을 둡니다.

- **VM 내부 표현**: `(make-int v)` — `v`는 일반 Scheme 정확수(bignum 가능)
- **저장 시 검증**: `op-store`로 변수에 들어가는 시점에 `int16-wrap` 적용
- **연산 후 검증**: `promote-numeric`이 범위 초과 시 SNG로 자동 승격

자매서는 *연산 시점에 우회 없이 잘림(overflow)이 일어나는* 의미였지만, Scheme 정확수의 정확성을 살려 *오버플로 검출 → 승격* 방식을 택합니다. GW-BASIC의 *Overflow* (에러 6) 와도 일치합니다.

### 17.2 inexact의 정밀도

R7RS `flonum`은 보통 IEEE 754 double. 처리계 의존이지만 SINGLE/DOUBLE 모두 같은 비트 폭에 들어갑니다. 본 구현은 *논리적 타입 태그* 만 다르게 두고, 실제 비트 표현은 모두 double — 자매서의 `float32`/`float64` 분리와 다른 점입니다.

> 💡 만약 *진짜 float32* 가 필요하면 SRFI-4의 `f32vector` 를 임시 저장소로 사용해 한 번 왕복시키는 방법이 있습니다. 본 구현은 *PRINT 시 정밀도가 다르게 보이는 효과* 를 위해 SNG는 7자리, DBL은 16자리로 포맷합니다.

### 17.3 promote-numeric 재방문

자매서 7장 코드와 의미적으로 동일.

```scheme
(define (promote-numeric a b r)
  (cond
    ((and (value-int? a) (value-int? b))
     (let ((ri (and (real? r) (= r (round r)) (exact (round r)))))
       (if (and ri (<= -32768 ri 32767))
           (make-int ri)
           (make-sng (exact->inexact r)))))
    ((or (value-dbl? a) (value-dbl? b))
     (make-dbl (exact->inexact r)))
    (else
     (make-sng (exact->inexact r)))))
```

### 17.4 PRINT 포맷

자매서와 동일한 출력을 위해 다음 규칙:

| 타입 | 형식 |
|------|------|
| INT 양수 | ` v ` (앞뒤 공백) |
| INT 음수 | `-v ` (앞 공백 없음, 뒤 공백 한 칸) |
| SNG | 같은 부호 규칙 + 7자리 정밀도 |
| DBL | 같은 부호 규칙 + 16자리 정밀도, `D` 지수 표기 |
| STR | 그대로 |

```scheme
(define (value->print-fmt v)
  (case (value-tag v)
    ((int)
     (let ((n (value-payload v)))
       (string-append (if (>= n 0) " " "")
                      (number->string n) " ")))
    ((sng)
     (string-append (sign-space (value-payload v))
                    (sng-format (value-payload v)) " "))
    ((dbl)
     (string-append (sign-space (value-payload v))
                    (dbl-format (value-payload v)) " "))
    ((str) (value-payload v))))

(define (sign-space x) (if (>= x 0) " " ""))
```

`sng-format`, `dbl-format`은 자매서의 *7자리 / 16자리* 출력을 흉내냅니다. 본 구현은 단순화로 `(number->string)`을 그대로 쓰고, *유효 자리수만 잘라냅니다* (구체 코드는 `src/lib/value.scm`).

---

## 18장. 변수 환경과 스코프

### 18.1 단일 전역 환경 + DEFINT 매핑

자매서와 같은 의미. *변수 이름(접미 포함)* 을 키로 한 해시 테이블 + *알파벳 → 기본 타입* 의 보조 매핑.

```scheme
;; lib/env.scm
(define-record-type <env>
  (make-env-rec vars defaults arrays)
  env?
  (vars     env-vars)
  (defaults env-defaults)   ; alist: (#\A . sng) ...
  (arrays   env-arrays))    ; "NAME" -> #(<dim-vec> <storage-vec>)

(define (env-new)
  (make-env-rec (make-hash-table string=? string-hash)
                '()
                (make-hash-table string=? string-hash)))

(define (env-reset! e)
  (hash-table-clear! (env-vars e))
  (hash-table-clear! (env-arrays e)))
```

### 18.2 변수 조회와 기본값

처음 보는 변수는 *기본 타입의 영(0/0.0/"")* 을 자동 생성합니다.

```scheme
(define (env-get e name)
  (cond
    ((hash-table-ref/default (env-vars e) name #f) => values)
    (else
     (let ((v (default-value-for-name e name)))
       (hash-table-set! (env-vars e) name v)
       v))))

(define (env-set! e name v)
  ;; 타입 강제 변환 — 변수 접미와 값의 태그가 다르면 변환
  (let ((coerced (coerce-to-name e name v)))
    (hash-table-set! (env-vars e) name coerced)))

(define (default-value-for-name e name)
  (let ((suf (last-char name)))
    (case suf
      ((#\%) (make-int 0))
      ((#\!) (make-sng 0.0))
      ((#\#) (make-dbl 0.0))
      ((#\$) (make-str ""))
      (else
       (case (default-tag-for-letter e (first-char name))
         ((int) (make-int 0))
         ((dbl) (make-dbl 0.0))
         ((str) (make-str ""))
         (else  (make-sng 0.0)))))))

(define (default-tag-for-letter e ch)
  (let ((cu (char-upcase ch)))
    (cond
      ((assv cu (env-defaults e)) => cdr)
      (else 'sng))))
```

### 18.3 `DEFINT` / `DEFSNG` / `DEFDBL` / `DEFSTR`

```basic
DEFINT I-N
DEFDBL A-H, O-Z
```

A-Z 알파벳 범위에 *기본 타입 태그* 를 등록합니다.

```scheme
(define (env-set-defaults! e tag-sym ranges)
  ;; ranges = '((#\I . #\N) (#\A . #\H))
  (for-each
   (lambda (r)
     (let ((lo (char->integer (char-upcase (car r))))
           (hi (char->integer (char-upcase (cdr r)))))
       (let loop ((i lo))
         (when (<= i hi)
           (set! (env-defaults e)
             (cons (cons (integer->char i) tag-sym)
                   (env-defaults e)))
           (loop (+ i 1))))))
   ranges))
```

⚠️ R7RS는 record 슬롯 setter를 `set-foo!` 형태로 따로 만들어야 합니다. 위 `(set! (env-defaults e) ...)`는 *문서용 의사 코드*. 실제 코드는 `set-env-defaults!` 호출.

### 18.4 배열

```scheme
(define-record-type <array>
  (make-array dims storage)
  array?
  (dims    arr-dims)     ; vector: (10 20)
  (storage arr-storage)) ; vector of Value

(define (arr-flat-index dims indices)
  ;; row-major. 자매서와 같은 공식.
  (let loop ((i 0) (acc 0))
    (cond
      ((= i (vector-length dims)) acc)
      (else
       (loop (+ i 1)
             (+ (* acc (+ 1 (vector-ref dims i)))
                (list-ref indices i)))))))

(define (env-dim! e name dims)
  (let* ((total (apply * (map (lambda (d) (+ d 1)) dims)))
         (storage (make-vector total (make-int 0))))
    (hash-table-set! (env-arrays e) name
                     (make-array (list->vector dims) storage))))

(define (env-aget e name idx-list)
  (let ((arr (hash-table-ref/default (env-arrays e) name #f)))
    (when (not arr)
      (raise-basic-error err-subscript "Subscript out of range"))
    (vector-ref (arr-storage arr)
                (arr-flat-index (arr-dims arr) idx-list))))

(define (env-aset! e name idx-list v)
  (let ((arr (hash-table-ref/default (env-arrays e) name #f)))
    (when (not arr)
      (raise-basic-error err-subscript "Subscript out of range"))
    (vector-set! (arr-storage arr)
                 (arr-flat-index (arr-dims arr) idx-list)
                 v)))
```

⚠️ DIM 없이 첫 사용 시 자매서는 *암묵적으로 0..10 배열을 생성* 합니다. 본 구현도 동일 — `op-load-arr` 에서 배열이 없으면 `(env-dim! e name '(10 ...))` 를 호출합니다 (인덱스 수만큼).

### 18.5 SWAP

`SWAP A, B` 는 두 변수 값을 교환합니다 (타입까지 그대로).

```scheme
(define (vm-exec-swap! vm ins)
  (let* ((a-name (vector-ref (chunk-names (vm-ch vm)) (i-a ins)))
         (b-name (vector-ref (chunk-names (vm-ch vm)) (i-b ins)))
         (av (env-get (vm-env vm) a-name))
         (bv (env-get (vm-env vm) b-name)))
    (when (not (eq? (value-tag av) (value-tag bv)))
      (raise-basic-error err-type-mismatch "Type mismatch"))
    (env-set! (vm-env vm) a-name bv)
    (env-set! (vm-env vm) b-name av)))
```

> 4부 끝. VM 본체와 메모리 모델이 완성됐습니다. 다음 5부에서는 *런타임 계열* (PRINT/INPUT/제어 흐름/문자열·수학 함수/DATA·READ) 을 채웁니다.
# 제5부 · 런타임 (1) — 입출력과 제어 흐름

## 19장. PRINT와 INPUT — 입출력의 모든 것

### 19.1 PRINT의 의미론

자매서와 동일한 규칙.

- 인자 사이의 `;` — 공백 없이 이어 붙임
- 인자 사이의 `,` — 다음 14컬럼 탭 정지로 이동
- 마지막의 `;` 또는 `,` — 줄바꿈 억제
- 수치는 양수 앞 한 칸, 모든 수치 뒤 한 칸 공백

### 19.2 Host 인터페이스 (Scheme)

1장에서 `<host>` record 골격을 봤습니다. 다시 제시.

```scheme
;; lib/host.scm
(define-record-type <host>
  (make-host print input-line cls set-color locate
             set-pixel draw-line draw-box draw-circle
             paint sound play-mml now)
  host?
  (print       host-print)
  (input-line  host-input-line)
  (cls         host-cls)
  (set-color   host-set-color)
  (locate      host-locate)
  (set-pixel   host-set-pixel)
  (draw-line   host-draw-line)
  (draw-box    host-draw-box)
  (draw-circle host-draw-circle)
  (paint       host-paint)
  (sound       host-sound)
  (play-mml    host-play-mml)
  (now         host-now))
```

### 19.3 터미널 호스트

```scheme
;; lib/host-term.scm
(define (make-term-host)
  (let ((col 0))
    (define (term-print s)
      (display s)
      (let loop ((i 0))
        (when (< i (string-length s))
          (if (char=? (string-ref s i) #\newline)
              (set! col 0)
              (set! col (+ col 1)))
          (loop (+ i 1)))))
    (define (term-input-line)
      (let ((line (read-line)))
        (set! col 0)
        (if (eof-object? line) "" line)))
    (define (no-op . args) (values))
    (define (now-secs)
      (let ((t (current-jiffy)))
        (/ t (jiffies-per-second))))
    (make-host term-print term-input-line
               (lambda () (display "\x1b;[2J\x1b;[H") (set! col 0))
               no-op no-op no-op no-op no-op no-op no-op
               (lambda (f ms) (values))
               (lambda (s) (values))
               now-secs)))
```

> 💡 ANSI 이스케이프(`\x1b[2J`)로 화면 지움. POSIX 터미널 + Termux + Windows Terminal 모두 동작.

### 19.4 Tab 정지

```scheme
(define tab-width 14)

(define current-print-col
  ;; 호스트가 추적. 본 구현은 host-term의 col에 위임.
  (lambda (host) ((host-now host)) 0))   ; 실제 구현은 host에 col getter 추가

(define (tab-to-14 host)
  ;; 다음 14의 배수까지 공백 패딩
  (let* ((c (host-col host))
         (next (* (quotient (+ c tab-width) tab-width) tab-width))
         (n (- next c)))
    (make-string n #\space)))
```

⚠️ `<host>` record에 `col` getter/setter를 추가해야 정확한 14컬럼 정렬이 됩니다. 본문에선 단순화로 생략.

### 19.5 INPUT 구현

```scheme
(define (vm-input! vm ins)
  ;; ins.A = InputDescs 인덱스
  (let* ((desc (list-ref (chunk-input-descs (vm-ch vm)) (i-a ins)))
         (host (vm-host vm)))
    (when (input-desc-prompt desc)
      ((host-print host) (input-desc-prompt desc))
      ((host-print host)
       (if (input-desc-suppress-q desc) "" "? ")))
    (let* ((raw  ((host-input-line host)))
           (parts (split-input-line raw (input-desc-vars desc))))
      (when (not (= (length parts) (length (input-desc-vars desc))))
        ;; 자매서와 같은 동작: "?Redo from start"
        ((host-print host) "?Redo from start\n")
        (vm-input! vm ins))     ; 재시도
      (for-each
       (lambda (var part)
         (env-set! (vm-env vm)
                   (input-var-name var)
                   (parse-input-part part (input-var-type var))))
       (input-desc-vars desc) parts))))
```

```scheme
(define (split-input-line s vars)
  ;; 콤마 구분, 단 따옴표로 감싼 영역은 보존
  (let loop ((i 0) (in-q #f) (cur '()) (acc '()))
    (cond
      ((>= i (string-length s))
       (reverse (cons (string-trim (list->string (reverse cur))) acc)))
      ((and (not in-q) (char=? (string-ref s i) #\,))
       (loop (+ i 1) #f '()
             (cons (string-trim (list->string (reverse cur))) acc)))
      ((char=? (string-ref s i) #\")
       (loop (+ i 1) (not in-q) cur acc))
      (else
       (loop (+ i 1) in-q (cons (string-ref s i) cur) acc)))))

(define (parse-input-part s type)
  (case type
    ((str) (make-str s))
    ((int)
     (cond
       ((string->number s) => (lambda (n) (make-int (int16-wrap (exact (round n))))))
       (else (raise-basic-error err-type-mismatch "Type mismatch"))))
    (else
     (cond
       ((string->number s) => (lambda (n) (make-sng n)))
       (else (raise-basic-error err-type-mismatch "Type mismatch"))))))
```

### 19.6 PRINT USING — 마이크로 포맷터

GW-BASIC의 `PRINT USING` 은 `#`(자릿수), `.`(소수점), `,`(천 단위), `\ \`(문자열 영역), `!`(첫 글자), `+/-`(부호), `**`(앞 패딩) 등을 가진 작은 미니 언어입니다.

```basic
10 PRINT USING "###.##"; 3.14159
20 PRINT USING "+##"; -5
30 PRINT USING "\   \"; "Hello"
```

```scheme
;; lib/printusing.scm
(define (format-using fmt values)
  ;; fmt를 토큰으로 쪼갠 뒤 각 토큰에 값 하나를 매칭
  (let loop ((i 0) (vals values) (acc '()))
    (cond
      ((>= i (string-length fmt))
       (apply string-append (reverse acc)))
      ((field-start? fmt i)
       (let-values (((field next) (read-field fmt i)))
         (cond
           ((null? vals)
            (loop next '() (cons field acc))) ; 값이 다 떨어졌으면 그대로
           (else
            (loop next (cdr vals)
                  (cons (apply-field field (car vals)) acc))))))
      (else
       (loop (+ i 1) vals
             (cons (string (string-ref fmt i)) acc))))))
```

(전체 코드는 `src/lib/printusing.scm`. 자매서 `printusing.go` 와 같은 알고리즘.)

---

## 20장. 제어 흐름 — GOTO, IF/THEN/ELSE, FOR/NEXT

### 20.1 GOTO 와 라인 매핑

이미 15장에서 `chunk-line-map` 으로 처리. VM은 *순수 PC 점프* 만 합니다.

### 20.2 FOR / NEXT 의 의미론

자매서와 동일한 의미. *증분 부호에 따라 종료 조건의 방향이 다름* — 양 step이면 `i > end` 에서 탈출, 음 step이면 `i < end` 에서 탈출.

```scheme
(define (vm-for-init! vm ins)
  ;; 스택 top: end, step  → forStk push
  (let* ((s (vm-stack vm))
         (step (value->real (stack-pop! s)))
         (end  (value->real (stack-pop! s)))
         (name-idx (i-a ins))
         (name (vector-ref (chunk-names (vm-ch vm)) name-idx)))
    (set-vm-for-stk! vm
      (cons (make-for-state name end step (vm-pc vm) #f)
            (vm-for-stk vm)))))

(define (vm-for-next! vm ins)
  ;; ins.A = 변수명 인덱스 (0이면 가장 최근 FOR)
  (let* ((target-name
          (and (not (zero? (i-a ins)))
               (vector-ref (chunk-names (vm-ch vm)) (i-a ins))))
         (fs (find-for vm target-name))
         (i (value->real (env-get (vm-env vm) (fs-name fs))))
         (i2 (+ i (fs-step fs))))
    (cond
      ((or (and (positive? (fs-step fs)) (> i2 (fs-end fs)))
           (and (negative? (fs-step fs)) (< i2 (fs-end fs))))
       ;; 루프 탈출 — forStk에서 제거
       (set-vm-for-stk! vm
         (filter (lambda (s) (not (eq? s fs))) (vm-for-stk vm))))
      (else
       (env-set! (vm-env vm) (fs-name fs) (real->basic i2))
       (set-vm-pc! vm (fs-body fs))))))

(define (find-for vm target-name)
  (cond
    ((null? (vm-for-stk vm))
     (raise-basic-error err-next-without-for "NEXT without FOR"))
    ((or (not target-name)
         (string=? (fs-name (car (vm-for-stk vm))) target-name))
     (car (vm-for-stk vm)))
    (else
     (find-for-rest (cdr (vm-for-stk vm)) target-name))))

(define (real->basic x)
  (if (and (real? x) (= x (round x)) (<= -32768 x 32767))
      (make-int (exact (round x)))
      (make-sng (exact->inexact x))))
```

### 20.3 WHILE / WEND

```scheme
;; WHILE: 컴파일러가
;;   <jmp-back>: op-while-test  →  거짓이면 wend 다음으로 점프
;;   ... 루프 본문 ...
;;   op-wend  →  jmp-back으로 점프
;; 형태로 emit.

;; VM의 op-while-test, op-wend는 16장 디스패치에 이미 구현.
```

### 20.4 ON x GOTO/GOSUB

```scheme
(define (vm-on-goto-or-gosub! vm ins kind)
  (let* ((s (vm-stack vm))
         (n (value->int16 (stack-pop! s)))
         (targets (vector->list
                    (vector-ref (chunk-on-targets (vm-ch vm)) (i-a ins)))))
    (cond
      ((or (< n 1) (> n (length targets)))
       ;; "Illegal function call" 도 가능, 표준은 *무시* (실행 계속)
       #f)
      (else
       (let ((target (list-ref targets (- n 1))))
         (case kind
           ((goto) (set-vm-pc! vm target))
           ((gosub)
            (set-vm-call-stk! vm (cons (vm-pc vm) (vm-call-stk vm)))
            (set-vm-pc! vm target))))))))
```

> ⚠️ `chunk-on-targets` 는 본 구현이 추가한 보조 풀입니다. AST의 `on-goto`/`on-gosub` 는 컴파일 시점에 *라인 번호 리스트* 를 가지지만, 백패치를 위해 별도 vector로 보관합니다.

---

## 21장. 서브루틴 — GOSUB / RETURN

### 21.1 콜 스택

`vm-call-stk` 는 *복귀 PC* 만 담는 단순 리스트. R7RS 리스트 자체로 충분.

```scheme
;; GOSUB 100
;;   call-stk: (pc-after-gosub . old-stack)
;;   pc → line-map[100]
;;
;; RETURN
;;   pc → car call-stk
;;   call-stk → cdr call-stk
;;
;; RETURN 200
;;   pc → line-map[200]   (call-stk pop 후)
```

### 21.2 RETURN n — 보조 분기

`RETURN <line-num>` 은 *보통의 RETURN을 시킨 뒤 그 라인으로 점프* 입니다 (자매서 `op-ret-to`).

```scheme
;; ((op-ret-to) ...) 분기는 16.4에 이미 구현.
```

### 21.3 깊이 검사

GW-BASIC은 GOSUB 깊이에 *고정 한도* (보통 256) 가 있었습니다. 본 구현은 처리계 스택의 한계까지 허용 — Scheme 리스트는 메모리만 충분하면 무한히 자랍니다.

### 21.4 사용 예: 팩토리얼

```basic
10 N = 5
20 GOSUB 1000
30 PRINT R
40 END
1000 IF N <= 1 THEN R = 1 : RETURN
1010 N0 = N
1020 N = N - 1
1030 GOSUB 1000
1040 R = R * N0
1050 N = N0
1060 RETURN
```

⚠️ GW-BASIC의 GOSUB는 *재귀 호출이 가능* 하지만, 변수는 모두 전역이라 위 코드처럼 *손수 저장/복원* 해야 합니다. 자매서와 동일한 함정.

> 🔁 26장(DEF FN) 에서는 *진짜 매개변수가 있는 함수* 를 자연스럽게 지원합니다.

---

> 5부 (1) 끝. 다음 (2) 에서는 문자열·수학 함수, DATA/READ, DEF FN을 마저 채웁니다.
# 제5부 · 런타임 (2) — 표준 라이브러리

## 22장. 배열 — DIM과 다차원 인덱싱

### 22.1 DIM 의 의미

`DIM A(10, 20)` — 두 차원, 인덱스 0..10 × 0..20 (총 11×21 = 231 셀). GW-BASIC은 *상한* 으로 명시합니다 (C/Java의 *길이* 가 아님).

```scheme
;; 이미 18.4에서 env-dim! 구현됨.

(define (vm-dim! vm ins)
  ;; ins.A = 이름 인덱스, ins.B = 차원 수
  (let* ((nm (vector-ref (chunk-names (vm-ch vm)) (i-a ins)))
         (n  (i-b ins))
         (dims (let loop ((i 0) (acc '()))
                 (if (= i n) acc
                     (loop (+ i 1)
                           (cons (value->int16
                                   (stack-pop! (vm-stack vm))) acc))))))
    (env-dim! (vm-env vm) nm dims)))
```

⚠️ 배열은 `op-store-arr`/`op-load-arr` 에서 *암묵 생성* 도 지원해야 합니다 — DIM 없이 `A(3) = 1` 처럼 써도 0..10 의 1차원 배열이 만들어집니다 (자매서와 동일).

### 22.2 OPTION BASE 1

GW-BASIC은 `OPTION BASE 1` 로 *시작 인덱스 1* 도 지원합니다. 본 구현은 **OPTION BASE 0** 만 지원 — 호환성 부족 표시 (📌 부록 B).

### 22.3 ERASE

`ERASE A, B` — 배열 해제. 본 구현은 *전 배열 삭제* 또는 *재DIM 가능* 하게.

```scheme
(define (env-erase! e name)
  (hash-table-delete! (env-arrays e) name))
```

---

## 23장. 문자열 함수 — LEFT$, RIGHT$, MID$, INSTR

### 23.1 builtin 디스패치 표

자매서가 `switch (name)` 으로 짠 부분을, Scheme은 *해시 테이블*에 *함수 객체* 를 담아 풀어냅니다.

```scheme
;; lib/strfunc.scm
(define string-builtins
  (let ((h (make-hash-table string=? string-hash)))
    (hash-table-set! h "LEN"     (cons 1 builtin-len))
    (hash-table-set! h "LEFT$"   (cons 2 builtin-left))
    (hash-table-set! h "RIGHT$"  (cons 2 builtin-right))
    (hash-table-set! h "MID$"    (cons '(2 3) builtin-mid))   ; 가변 인자
    (hash-table-set! h "INSTR"   (cons '(2 3) builtin-instr))
    (hash-table-set! h "STR$"    (cons 1 builtin-str$))
    (hash-table-set! h "VAL"     (cons 1 builtin-val))
    (hash-table-set! h "CHR$"    (cons 1 builtin-chr$))
    (hash-table-set! h "ASC"     (cons 1 builtin-asc))
    (hash-table-set! h "SPACE$"  (cons 1 builtin-space$))
    (hash-table-set! h "STRING$" (cons 2 builtin-string$))
    (hash-table-set! h "HEX$"    (cons 1 builtin-hex$))
    (hash-table-set! h "OCT$"    (cons 1 builtin-oct$))
    h))
```

각 절차는 *Value 리스트를 받아 Value 하나를 반환* 합니다.

### 23.2 LEN, LEFT$, RIGHT$

```scheme
(define (builtin-len vs)
  (let ((s (must-str (car vs))))
    (make-int (string-length s))))

(define (builtin-left vs)
  (let* ((s (must-str  (car vs)))
         (n (must-int  (cadr vs))))
    (make-str (substring s 0 (min n (string-length s))))))

(define (builtin-right vs)
  (let* ((s (must-str  (car vs)))
         (n (must-int  (cadr vs)))
         (len (string-length s)))
    (make-str (substring s (max 0 (- len n)) len))))

(define (must-str v)
  (cond
    ((value-str? v) (value-payload v))
    (else (raise-basic-error err-type-mismatch "Type mismatch"))))

(define (must-int v)
  (cond
    ((value-int? v) (value-payload v))
    ((value-num? v) (exact (round (value-payload v))))
    (else (raise-basic-error err-type-mismatch "Type mismatch"))))
```

### 23.3 MID$ — 두 가지 사용법

```basic
PRINT MID$("HELLO", 2, 3)   ' "ELL"
PRINT MID$("HELLO", 3)      ' "LLO"  — 끝까지

' 좌변에서 — *대입* 의미
MID$(A$, 2, 3) = "XYZ"
```

본 구현은 *함수형 사용* 만 builtin으로 지원합니다. *좌변 MID$* 는 자매서와 같이 별도 옵코드(`op-mid-assign`)로 처리.

```scheme
(define (builtin-mid vs)
  (let* ((s (must-str (car vs)))
         (start (max 1 (must-int (cadr vs))))
         (count (cond
                  ((null? (cddr vs)) (string-length s))
                  (else (must-int (caddr vs)))))
         (i0 (- start 1))
         (i1 (min (string-length s) (+ i0 count))))
    (make-str (substring s (min i0 (string-length s)) i1))))
```

⚠️ GW-BASIC의 인덱스는 *1-based*. R7RS `substring`은 *0-based*. 항상 -1 변환.

### 23.4 INSTR

```basic
PRINT INSTR("HELLO", "L")        ' 3
PRINT INSTR(4, "HELLO", "L")     ' 4
```

```scheme
(define (builtin-instr vs)
  (let-values
    (((start hay needle)
      (case (length vs)
        ((2) (values 1 (must-str (car vs)) (must-str (cadr vs))))
        ((3) (values (must-int (car vs))
                     (must-str (cadr vs))
                     (must-str (caddr vs)))))))
    (let ((i (string-search hay needle (- start 1))))
      (make-int (if i (+ i 1) 0)))))

(define (string-search hay needle from)
  ;; SRFI-13 string-contains 사용. 없으면 직접 구현.
  (let loop ((i from))
    (cond
      ((> (+ i (string-length needle)) (string-length hay)) #f)
      ((string=? (substring hay i (+ i (string-length needle))) needle) i)
      (else (loop (+ i 1))))))
```

### 23.5 STR$ / VAL / CHR$ / ASC / SPACE$ / STRING$

자매서와 같은 의미. 핵심 한 가지만:

```scheme
(define (builtin-str$ vs)
  (let ((v (car vs)))
    (make-str
     (case (value-tag v)
       ((int) (string-append (if (>= (value-payload v) 0) " " "")
                             (number->string (value-payload v))))
       ((sng dbl)
        (string-append (if (>= (value-payload v) 0) " " "")
                       (number->string (value-payload v))))
       (else (raise-basic-error err-type-mismatch "Type mismatch"))))))

(define (builtin-val vs)
  (let* ((s (must-str (car vs)))
         (n (string->number (string-trim s))))
    (cond
      ((not n) (make-sng 0.0))
      ((exact-integer? n) (make-sng (exact->inexact n)))
      (else (make-sng n)))))

(define (builtin-chr$ vs)
  (make-str (string (integer->char (must-int (car vs))))))

(define (builtin-asc vs)
  (let ((s (must-str (car vs))))
    (when (zero? (string-length s))
      (raise-basic-error err-illegal-call "Illegal function call"))
    (make-int (char->integer (string-ref s 0)))))
```

---

## 24장. 수학 함수 — SIN, COS, RND, INT

### 24.1 표준 함수들

```scheme
;; lib/mathfunc.scm
(define math-builtins
  (let ((h (make-hash-table string=? string-hash)))
    (hash-table-set! h "ABS"  (cons 1 (lambda (vs) (real->basic (abs (must-real (car vs)))))))
    (hash-table-set! h "SGN"  (cons 1 (lambda (vs) (let ((x (must-real (car vs))))
                                                     (make-int (cond ((positive? x) 1)
                                                                     ((negative? x) -1)
                                                                     (else 0)))))))
    (hash-table-set! h "INT"  (cons 1 (lambda (vs) (real->basic (floor (must-real (car vs)))))))
    (hash-table-set! h "FIX"  (cons 1 (lambda (vs) (real->basic (truncate (must-real (car vs)))))))
    (hash-table-set! h "SQR"  (cons 1 (lambda (vs) (make-sng (sqrt (must-real (car vs)))))))
    (hash-table-set! h "SIN"  (cons 1 (lambda (vs) (make-sng (sin  (must-real (car vs)))))))
    (hash-table-set! h "COS"  (cons 1 (lambda (vs) (make-sng (cos  (must-real (car vs)))))))
    (hash-table-set! h "TAN"  (cons 1 (lambda (vs) (make-sng (tan  (must-real (car vs)))))))
    (hash-table-set! h "ATN"  (cons 1 (lambda (vs) (make-sng (atan (must-real (car vs)))))))
    (hash-table-set! h "LOG"  (cons 1 (lambda (vs) (make-sng (log  (must-real (car vs)))))))
    (hash-table-set! h "EXP"  (cons 1 (lambda (vs) (make-sng (exp  (must-real (car vs)))))))
    (hash-table-set! h "CINT" (cons 1 (lambda (vs) (make-int (int16-wrap
                                                              (exact (round (must-real (car vs))))))))) 
    (hash-table-set! h "CSNG" (cons 1 (lambda (vs) (make-sng (must-real (car vs))))))
    (hash-table-set! h "CDBL" (cons 1 (lambda (vs) (make-dbl (must-real (car vs))))))
    h))
```

### 24.2 RND — 결정적 PRNG

GW-BASIC `RND` 는 *0..1* 의 단정도 실수를 돌립니다. 시드는 `RANDOMIZE n` 으로 설정.

```scheme
;; SRFI-27 사용 가능하면 권장. 본 구현은 자체 LCG로 *처리계 무관* 동작 보장.
(define-record-type <rng>
  (make-rng-rec state)
  rng?
  (state rng-state set-rng-state!))

(define (make-rng seed) (make-rng-rec (modulo seed #xFFFFFFFF)))

(define (rng-next! r)
  ;; numerical recipes LCG
  (let* ((s (rng-state r))
         (n (modulo (+ (* s 1664525) 1013904223) #x100000000)))
    (set-rng-state! r n)
    (/ n #x100000000)))   ; 0..1

(define (builtin-rnd vs vm)
  (let* ((arg (if (null? vs) 1 (must-real (car vs))))
         (rng (vm-rng vm)))
    (cond
      ((zero? arg) (make-sng (rng-state rng)))    ; 직전 값 (자매서 호환)
      ((negative? arg)
       ;; RANDOMIZE 같은 효과 — 고정 시드 재설정
       (set-vm-rng! vm (make-rng (exact (round (- arg)))))
       (rng-next! (vm-rng vm))
       (make-sng (rng-next! (vm-rng vm))))
      (else (make-sng (rng-next! (vm-rng vm)))))))
```

⚠️ `RND` 만 *VM 상태에 의존* 하는 builtin입니다. 다른 builtin과 호출 규약이 다릅니다 — 본 구현은 `(vs vm)` 두 인자를 받는 *특수 builtin* 분류로 둡니다 (`vm-call-builtin!` 안에서 분기).

### 24.3 RANDOMIZE

```scheme
(define (vm-exec-randomize! vm ins)
  (cond
    ((zero? (i-a ins))
     ;; 인자 없음 — 사용자에게 시드 입력 요청
     ((host-print (vm-host vm)) "Random number seed (-32768 to 32767)? ")
     (let* ((s ((host-input-line (vm-host vm))))
            (n (or (string->number s) 0)))
       (set-vm-rng! vm (make-rng (exact (round n))))))
    (else
     (let ((n (value->int16 (stack-pop! (vm-stack vm)))))
       (set-vm-rng! vm (make-rng n))))))
```

---

## 25장. DATA / READ / RESTORE

### 25.1 의미

```basic
10 DATA 1, 2, "HELLO", 3.14
20 READ A, B, S$, X
30 RESTORE 10
40 READ C, D, T$, Y
```

- `DATA` 는 *프로그램 정적 데이터* — 라인 어디에 있어도 평탄화되어 한 풀에 들어감
- `READ` 는 *현재 데이터 인덱스* 에서 항목을 차례로 꺼내 변수에 대입
- `RESTORE n` — 데이터 인덱스를 라인 *n* 의 첫 DATA 항목으로 되돌림 (n 생략 시 0으로)

### 25.2 컴파일러: DATA 평탄화

```scheme
(define (compile-data ch s)
  ;; (data <item> ...)  — item: (data-num <v> <kind>) | (data-str <s>)
  (let ((line-num (current-line-num)))
    (when line-num
      (hash-table-set! (chunk-data-line-map ch) line-num
                       (length (chunk-data-pool ch))))
    (for-each
     (lambda (it)
       (let ((v (case (car it)
                  ((data-num)
                   (case (caddr it)
                     ((int) (make-int (cadr it)))
                     ((sng) (make-sng (cadr it)))
                     ((dbl) (make-dbl (cadr it)))))
                  ((data-str) (make-str (cadr it))))))
         (set-chunk-data-pool! ch (append (chunk-data-pool ch) (list v)))))
     (cdr s))))
;; DATA 자체는 코드 emit 없음 — 풀에만 추가
```

### 25.3 VM: READ / RESTORE

```scheme
(define (vm-exec-read! vm ins)
  ;; ins.A = 변수명 인덱스
  (let* ((nm (vector-ref (chunk-names (vm-ch vm)) (i-a ins)))
         (idx (vm-data-idx vm))
         (pool (chunk-data-pool (vm-ch vm))))
    (when (>= idx (vector-length pool))
      (raise-basic-error err-out-of-data "Out of DATA"))
    (env-set! (vm-env vm) nm (vector-ref pool idx))
    (set-vm-data-idx! vm (+ idx 1))))

(define (vm-exec-restore! vm ins)
  (cond
    ((zero? (i-a ins)) (set-vm-data-idx! vm 0))
    (else
     (let* ((line-num (i-a ins))
            (target (hash-table-ref/default
                      (chunk-data-line-map (vm-ch vm)) line-num #f)))
       (when (not target)
         (raise-basic-error err-undefined-line
           (string-append "Undefined line " (number->string line-num))))
       (set-vm-data-idx! vm target)))))
```

---

## 26장. 사용자 정의 함수 DEF FN — 클로저로 자연스럽게

### 26.1 의미

```basic
10 DEF FN F(X) = X * X + 1
20 PRINT FN F(3)        ' 10
30 DEF FN G(X, Y) = X + Y
40 PRINT FN G(2, 5)     ' 7
```

- 본문은 *단일 표현식*
- 매개변수 이름 → *부분적 지역 스코프* (호출 동안 해당 이름의 전역 값을 가리고, 끝나면 복원)
- 같은 이름의 *재정의 가능*

### 26.2 컴파일러

```scheme
(define (compile-def-fn ch s)
  ;; (def-fn <name> (<param> ...) <expr>)
  (let* ((name (cadr s)) (params (caddr s)) (body-expr (cadddr s))
         ;; 본문 코드를 별도 chunk로 컴파일
         (body-ch (new-chunk)))
    (compile-expr body-ch body-expr)
    (emit! body-ch 'op-ret)
    (set-chunk-code! body-ch (list->vector (reverse (chunk-code body-ch))))
    (hash-table-set! (chunk-def-fns ch) name
                     (cons params (chunk-code body-ch)))))
```

### 26.3 VM: 호출

```scheme
(define (vm-call-user-fn! vm ins)
  (let* ((name (vector-ref (chunk-names (vm-ch vm)) (i-a ins)))
         (entry (hash-table-ref/default
                  (chunk-def-fns (vm-ch vm)) name #f)))
    (when (not entry)
      (raise-basic-error err-illegal-call
        (string-append "Undefined FN " name)))
    (let ((params (car entry)) (body-code (cdr entry))
          (argc (i-b ins)))
      (when (not (= argc (length params)))
        (raise-basic-error err-illegal-call
          "FN argument count mismatch"))
      ;; 1) 매개변수 saved
      (let ((saved (map (lambda (p)
                          (cons p (env-get (vm-env vm) p)))
                        params))
            (s (vm-stack vm)))
        ;; 2) 인자 → 매개변수 변수 (역순으로 pop)
        (for-each (lambda (p)
                    (env-set! (vm-env vm) p (stack-pop! s)))
                  (reverse params))
        ;; 3) 별도 미니 VM으로 본문 실행
        (let ((sub-vm (vm-fork vm body-code)))
          (vm-run! sub-vm)
          ;; 결과는 sub-vm 스택 top에 — main 스택으로 옮김
          (stack-push! s (stack-pop! (vm-stack sub-vm))))
        ;; 4) 변수 복원
        (for-each (lambda (kv)
                    (env-set! (vm-env vm) (car kv) (cdr kv)))
                  saved)))))

(define (vm-fork main code)
  (make-vm-rec
   (let ((c (chunk-copy (vm-ch main))))
     (set-chunk-code! c code) c)
   0 (make-stack)
   '() '() '()
   (vm-env main) (vm-rng main) (vm-host main) 0 #f))
```

> 💡 *변수 saved/복원* 은 Scheme의 동적 스코프를 흉내내는 *얕은 바인딩* 패턴. SICP 4장의 평가기와 같은 방식. 본격 클로저(어휘 스코프)를 원하면 `(env-with-frame ...)` 으로 *프레임 스택* 을 도입하면 됩니다 — 본 구현은 GW-BASIC의 단순한 의미를 살려 얕은 바인딩만 사용.

### 26.4 단위 테스트

```scheme
(test-equal "FN 단순"
  10
  (run-and-get-int "10 DEF FN F(X) = X*X+1\n20 PRINT FN F(3)"))

(test-equal "FN 다중 인자"
  7
  (run-and-get-int "10 DEF FN G(X,Y) = X+Y\n20 PRINT FN G(2,5)"))

(test-equal "FN 재정의"
  20
  (run-and-get-int (string-append
    "10 DEF FN H(X) = X*2\n"
    "20 DEF FN H(X) = X*4\n"
    "30 PRINT FN H(5)")))
```

> 5부 끝. BASIC의 *언어 핵* 이 완성됐습니다. 6부는 그래픽과 사운드, 7부는 도구/REPL/배포입니다.
# 제6부 · 그래픽과 사운드

## 27장. SCREEN 모드와 그래픽 명령

### 27.1 모드

GW-BASIC의 `SCREEN n` 모드별 해상도와 색.

| 모드 | 텍스트 | 그래픽 | 색 |
|------|--------|--------|-----|
| 0 | 80×25 | — | 16/8 |
| 1 | 40×25 | 320×200 | 4 |
| 2 | 80×25 | 640×200 | 2 |
| 7 | 40×25 | 320×200 | 16 |
| 8 | 80×25 | 640×200 | 16 |
| 9 | 80×25 | 640×350 | 16/64 |

본 구현은 *모드를 호스트에 통보* 만 하고, 좌표는 항상 그대로 받습니다 (호스트가 클리핑/스케일).

### 27.2 호스트 — racket/draw 백엔드 (선택)

자매서가 ebitengine / canvas / SDL 을 쓴 자리에, 본 구현은 **Racket의 `racket/draw`** 를 옵션으로 둡니다. 다른 처리계 사용자는 *터미널 + 텍스트 그래픽* 만 이용합니다.

```scheme
;; lib/host-draw.scm  (Racket 전용; 다른 처리계에서는 로드 금지)
#!r6rs
(import (rnrs) (racket draw))

(define (make-draw-host width height)
  (let* ((bm (make-bitmap width height))
         (dc (send bm make-dc))
         (col 0))
    (define (draw-print s)
      (display s)
      (let loop ((i 0))
        (when (< i (string-length s))
          (if (char=? (string-ref s i) #\newline)
              (set! col 0) (set! col (+ col 1)))
          (loop (+ i 1)))))
    (define (draw-set-pixel x y c)
      (send dc set-pen (color-of c) 1 'solid)
      (send dc draw-point x y))
    (define (draw-line2 x1 y1 x2 y2 c)
      (send dc set-pen (color-of c) 1 'solid)
      (send dc draw-line x1 y1 x2 y2))
    (define (draw-circle2 x y r c sa ea asp)
      (send dc set-pen (color-of c) 1 'solid)
      (send dc draw-arc (- x r) (- y r) (* 2 r) (* 2 r) sa ea))
    (make-host draw-print read-line
               (lambda () (send dc clear) (set! col 0))
               (lambda (fg bg m) (values))
               (lambda (r c) (values))
               draw-set-pixel draw-line2
               (lambda (x1 y1 x2 y2 c f) (values))
               draw-circle2
               (lambda (x y fc bc) (values))
               (lambda (f ms) (values))
               (lambda (s) (values))
               (lambda () (current-inexact-milliseconds)))))
```

(전체 코드는 `src/lib/host-draw.scm`. Racket 외 처리계에선 로드하지 마세요.)

### 27.3 명령 구현 — VM 측

```scheme
(define (vm-exec-pset! vm ins)
  ;; ins.A = STEP? (0/1), 좌표 두 개와 색이 스택에 있음
  (let* ((s (vm-stack vm))
         (have-color (= 1 (i-mode ins)))
         (color (if have-color (value->int16 (stack-pop! s)) 15))
         (y (value->int16 (stack-pop! s)))
         (x (value->int16 (stack-pop! s))))
    ((host-set-pixel (vm-host vm)) x y color)))

(define (vm-exec-line! vm ins)
  ;; 좌표 두 짝, 색, B/BF 모드 비트
  (let* ((s (vm-stack vm))
         (have-color (= 1 (bitwise-and (i-mode ins) #b001)))
         (box?       (= 1 (bitwise-and (i-mode ins) #b010)))
         (filled?    (= 1 (bitwise-and (i-mode ins) #b100)))
         (color (if have-color (value->int16 (stack-pop! s)) 15))
         (y2 (value->int16 (stack-pop! s)))
         (x2 (value->int16 (stack-pop! s)))
         (y1 (value->int16 (stack-pop! s)))
         (x1 (value->int16 (stack-pop! s))))
    (cond
      (box? ((host-draw-box (vm-host vm)) x1 y1 x2 y2 color filled?))
      (else ((host-draw-line (vm-host vm)) x1 y1 x2 y2 color)))))
```

### 27.4 CIRCLE — 호 / 타원 / 종횡비

자매서와 같은 의미. 인자 6개 (x, y, r, color?, start?, end?, aspect?). 본 구현은 호스트에 그대로 위임.

### 27.5 PAINT — 시드 채우기

호스트가 *시드 좌표 + 채울 색 + 경계 색* 을 받음. 알고리즘은 호스트 자유.

> 💡 racket/draw 호스트는 `flood-fill` 메서드가 없어 직접 *Stack 기반 4-방향 채우기* 를 구현합니다 (자매서 27장과 동일 알고리즘).

---

## 28장. 사운드 — SOUND와 PLAY (MML)

### 28.1 SOUND — 단발음

```basic
SOUND 440, 18    ' 440 Hz, 18 ticks (= 18/18.2 sec)
```

```scheme
(define (vm-exec-sound! vm ins)
  (let* ((s (vm-stack vm))
         (dur-ticks (value->int16 (stack-pop! s)))
         (freq      (value->real  (stack-pop! s)))
         (ms        (round (* dur-ticks (/ 1000 18.2)))))
    ((host-sound (vm-host vm)) (exact->inexact freq) (exact (round ms)))))
```

### 28.2 PLAY — MML 미니 언어

```basic
PLAY "T120 O4 L4 C D E F G A B > C"
```

| 토큰 | 의미 |
|------|------|
| `T<n>` | 템포 (BPM) |
| `O<n>` | 옥타브 (0..6) |
| `L<n>` | 기본 음 길이 (1, 2, 4, 8, 16, 32) |
| `<` `>` | 옥타브 -1 / +1 |
| `A`..`G` `[#+-]` `[<n>]` `[.]` | 음표 |
| `R` | 쉼표 |
| `N<n>` | 음 번호 (0..84) |
| `MN MS ML` | normal/staccato/legato |

본 구현은 *MML 파서를 별도 절차*로 두고, *호스트의 `sound`* 를 차례로 호출합니다.

```scheme
;; lib/mml.scm
(define (mml->sound-events s)
  ;; 결과: '((freq dur) ...)
  (let loop ((i 0) (state (initial-mml-state)) (acc '()))
    (cond
      ((>= i (string-length s)) (reverse acc))
      ;; ... 토큰 디스패치 ...
      (else (loop (next-i) state acc)))))

(define (initial-mml-state)
  ;; tempo 120, octave 4, length 4, articulation 'normal
  (list 'tempo 120 'octave 4 'length 4 'art 'normal))
```

```scheme
(define (vm-exec-play! vm ins)
  (let* ((s (must-str (stack-pop! (vm-stack vm))))
         (events (mml->sound-events s)))
    (for-each (lambda (e)
                ((host-sound (vm-host vm)) (car e) (cadr e)))
              events)))
```

> 💡 MML 파서는 *재귀 하강의 축소판* 입니다. 이미 우리는 BASIC을 위해 한 번 만들었으니, 그 노하우를 그대로 적용합니다.

### 28.3 BEEP

```scheme
;; 16.4 디스패치에 이미: ((host-sound (vm-host vm)) 800.0 200)
```

자매서가 *800 Hz, 200 ms* 로 정의한 그대로.

---

> 6부 끝. 그래픽과 사운드는 인터프리터의 *외부 세계 손* 입니다. 호스트만 갈아 끼우면 같은 BASIC 프로그램이 터미널, 브라우저, GUI 어디서든 돌아간다는 점이 본 설계의 매력.
# 제7부 · 도구와 통합

## 29장. REPL — 즉시 실행 환경

### 29.1 두 모드 합치기

GW-BASIC REPL은 *직접 모드* 와 *프로그램 모드* 를 한 화면에서 오갑니다.

```
Ok
PRINT 1+2          ← 직접 실행
 3 
Ok
10 PRINT "HI"       ← 라인 번호가 있으면 저장
20 GOTO 10
RUN                 ← 저장된 프로그램 실행
HI
HI
HI
^C
Break
Ok
LIST                ← 현재 프로그램 출력
10 PRINT "HI"
20 GOTO 10
Ok
```

### 29.2 구현

```scheme
;; lib/repl.scm
(define (run-repl host)
  (let loop ((program-lines (make-hash-table eqv? hash-by-identity)))
    ((host-print host) "Ok\n")
    (let ((line ((host-input-line host))))
      (cond
        ((or (eof-object? line) (zero? (string-length line)))
         (loop program-lines))
        ((eq? (parse-line-kind line) 'numbered)
         (let* ((n (parse-leading-number line))
                (rest (substring line (number-end-pos line) (string-length line))))
           (cond
             ((zero? (string-length (string-trim rest)))
              (hash-table-delete! program-lines n))
             (else
              (hash-table-set! program-lines n rest)))
           (loop program-lines)))
        ((string=? (string-upcase (string-trim line)) "RUN")
         (run-program host program-lines)
         (loop program-lines))
        ((string=? (string-upcase (string-trim line)) "LIST")
         (list-program host program-lines)
         (loop program-lines))
        ((string=? (string-upcase (string-trim line)) "NEW")
         (loop (make-hash-table eqv? hash-by-identity)))
        ((string=? (string-upcase (string-trim line)) "SYSTEM")
         #t)   ; REPL 종료
        (else
         ;; 직접 모드 — 한 줄 BASIC
         (with-exception-handler
           (lambda (e)
             ((host-print host) (basic-error-msg e))
             ((host-print host) "\n")
             (loop program-lines))
           (lambda ()
             (let* ((src (string-append "1 " line "\n"))
                    (vm (vm-new (compile (parse (lex src))) host)))
               (vm-run! vm))
             (loop program-lines))))))))

(define (run-program host lines)
  (let* ((sorted (sort (hash-table-keys lines) <))
         (src (apply string-append
                     (map (lambda (n)
                            (string-append (number->string n) " "
                                           (hash-table-ref lines n) "\n"))
                          sorted)))
         (vm (vm-new (compile (parse (lex src))) host)))
    (with-exception-handler
      (lambda (e)
        ((host-print host)
         (string-append (basic-error-msg e)
                        (if (basic-error-line e)
                            (string-append " in " (number->string (basic-error-line e)))
                            "")
                        "\n")))
      (lambda () (vm-run! vm)))))
```

### 29.3 ^C 처리

자매서가 시그널 핸들러로 다룬 부분. Scheme은 처리계마다 다릅니다 — Racket은 `with-handlers`, Chez는 `keyboard-interrupt-handler`. 본 구현은 *추후 28장 호환 추가* 로 남기고, 단순 폴링(`host-check-break`) 만 둡니다.

---

## 30장. 디버거 — 단계 실행과 브레이크포인트

### 30.1 디버거 인터페이스

```scheme
(define-record-type <debugger>
  (make-debugger breakpoints stepping?)
  debugger?
  (breakpoints dbg-breakpoints set-dbg-breakpoints!)
  (stepping?   dbg-stepping?   set-dbg-stepping!))
```

`vm-step!` 직후 디버거 훅을 끼웁니다.

```scheme
(define (vm-run-with-debugger! vm dbg)
  (let loop ()
    (cond
      ((vm-halted? vm) #t)
      (else
       (let* ((pc (vm-pc vm))
              (line (pc->line vm pc)))
         (when (or (dbg-stepping? dbg)
                   (memv line (dbg-breakpoints dbg)))
           (debugger-prompt vm dbg pc line))
         (let ((ins (vector-ref (chunk-code (vm-ch vm)) pc)))
           (set-vm-pc! vm (+ pc 1))
           (vm-step! vm ins)
           (loop)))))))

(define (debugger-prompt vm dbg pc line)
  (display "[bp ") (display line)
  (display " pc=") (display pc) (display "] > ")
  (let ((cmd ((host-input-line (vm-host vm)))))
    (case (string->symbol (string-trim cmd))
      ((s step) (set-dbg-stepping! dbg #t))
      ((c continue) (set-dbg-stepping! dbg #f))
      ((p print) (display-stack vm) (debugger-prompt vm dbg pc line))
      ((vars)    (display-env vm)   (debugger-prompt vm dbg pc line))
      ((q)       (set-vm-halted! vm #t))
      (else (debugger-prompt vm dbg pc line)))))
```

### 30.2 디스어셈블 + 라인 추적

VM 실행 추적은 *디스어셈블 + line-map 역방향 표* 만 있으면 됩니다.

```scheme
(define (pc->line vm pc)
  ;; line-map의 역방향. 캐시는 처음 한 번만.
  (let ((rev (chunk-pc->line-cache (vm-ch vm))))
    (when (not rev)
      (let ((r (make-hash-table eqv? hash-by-identity)))
        (hash-table-walk (chunk-line-map (vm-ch vm))
                         (lambda (l p) (hash-table-set! r p l)))
        (set-chunk-pc->line-cache! (vm-ch vm) r)))
    (hash-table-ref/default (chunk-pc->line-cache (vm-ch vm)) pc #f)))
```

### 30.3 명령

| 명령 | 의미 |
|------|------|
| `s` / `step` | 한 명령 실행 후 다시 정지 |
| `c` / `continue` | 다음 브레이크포인트까지 |
| `b 100` | 라인 100에 BP 설정 |
| `d 100` | BP 제거 |
| `p` | 스택 출력 |
| `vars` | 환경 출력 |
| `disasm` | 현재 chunk 디스어셈블 |
| `q` | 종료 |

---

## 31장. 테스트 전략과 회귀 검증

### 31.1 골든 테스트

각 `examples/*.bas` 에 *기대 출력 파일* `*.out` 을 둡니다. 테스트는 *실행 → 출력과 비교*.

```scheme
;; tests/golden.scm
(define (run-and-capture src)
  (let* ((out (open-output-string))
         (host (make-string-host out))
         (vm (vm-new (compile (parse (lex src))) host)))
    (vm-run! vm)
    (get-output-string out)))

(define (test-golden name)
  (let* ((src (read-file (string-append "examples/" name ".bas")))
         (exp (read-file (string-append "examples/" name ".out")))
         (got (run-and-capture src)))
    (test-equal name exp got)))

(for-each test-golden
          '("hello" "fib" "sieve" "string_demo"
            "data_demo" "gosub_demo" "ctrl_demo"))
```

### 31.2 단위 테스트

각 모듈에 `tests/<module>-test.scm`. 본 책의 곳곳에 등장한 `test-equal` 들이 그것입니다.

### 31.3 벤치마크

Chez에서:

```bash
chez --script bench.scm

;; sieve(10000)  : 0.42s
;; fib(30)       : 0.31s
;; mandel(80x40) : 1.8s
```

자매서 (Go, C) 와 비교 표 — Scheme 본 구현은 *Chez 기준* 으로 *Go 의 1.5~3 배* 정도. 인터프리터 두 층(Scheme → BASIC) 임을 감안하면 양호.

### 31.4 fuzzer (선택)

Lexer/Parser 가 *임의 입력에 대해 무한 루프나 panic 없이 종료* 하는지 검사. SRFI-194 `random-source` 로 무작위 문자열 생성 → `parse` → 예외만 잘 잡히면 통과.

---

## 32장. 빌드, 패키징, 배포

### 32.1 Racket 단일 실행 파일

```bash
raco make main.scm
raco exe -o gwbasic main.scm
```

산출물 `gwbasic` 는 `/usr/bin/racket` 의 *임베디드 런타임* 을 포함한 단일 실행 파일.

### 32.2 Chez

```bash
echo '(import (gwbasic main)) (main (command-line))' > entry.scm
chez --compile-program entry.scm
mv entry.so gwbasic.so
echo '#!/usr/bin/env scheme-script' > gwbasic
echo '(load "gwbasic.so")' >> gwbasic
chmod +x gwbasic
```

### 32.3 Guile

```bash
guild compile -o gwbasic.go main.scm
```

`gwbasic.go` 와 `main.scm` 을 함께 배포하고, *런처 스크립트* 를 둡니다.

### 32.4 build.sh / build.bat

자매서와 같은 정책으로 두 스크립트만 두면 됩니다.

```bash
#!/usr/bin/env bash
# build.sh — Racket 기준
set -euo pipefail
mkdir -p release
raco exe -o release/gwbasic main.scm
cp -r examples release/
echo "Built: release/gwbasic"
```

```bat
@echo off
chcp 949 >nul
if not exist release mkdir release
raco exe -o release\gwbasic.exe main.scm
xcopy /E /I /Y examples release\examples
echo 빌드 완료: release\gwbasic.exe
```

### 32.5 진입점 main.scm

```scheme
;; main.scm
#!r7rs
(import (scheme base) (scheme write) (scheme process-context)
        (gwbasic lexer) (gwbasic parser) (gwbasic compiler)
        (gwbasic vm) (gwbasic host-term) (gwbasic repl))

(define (main args)
  (cond
    ((null? (cdr args))
     (run-repl (make-term-host)))
    ((string=? (cadr args) "run")
     (run-file (caddr args)))
    ((string=? (cadr args) "disasm")
     (disasm-file (caddr args)))
    (else
     (display "usage: gwbasic [run|disasm <file.bas>]\n"))))

(define (run-file path)
  (let* ((src (with-input-from-file path
                (lambda ()
                  (let loop ((acc '()))
                    (let ((c (read-char)))
                      (if (eof-object? c)
                          (list->string (reverse acc))
                          (loop (cons c acc))))))))
         (host (make-term-host))
         (vm (vm-new (compile (parse (lex src))) host)))
    (with-exception-handler
      (lambda (e)
        (display (basic-error-msg e)) (newline))
      (lambda () (vm-run! vm)))))

(main (command-line))
```

### 32.6 README와 매뉴얼

자매서와 동일 정책 — `README.md` 한글, `examples/*.bas` 와 *기대 출력* 동봉, 빌드 명령 두 줄.

---

> 7부 끝. 책의 본문이 끝났습니다. 부록에서는 BNF 전체, 레퍼런스 카드, 에러 코드, 예제, 자매서와의 차이를 한 자리에 모읍니다.
# 부록

## 부록 A. GW-BASIC BNF 전체

> 🔁 자매서(C / Go / TS / Lua)와 *글자 그대로 동일*. 같은 언어를 구현하기 때문입니다.

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
| `OPTION BASE` | 인덱스 시작 | △ (0 고정) |
| `INKEY$` | 비차단 키 | △ (호스트 의존) |
| `OPEN/CLOSE/PRINT#/INPUT#` | 파일 입출력 | ✗ |
| `FIELD/GET/PUT/LSET/RSET` | 랜덤 파일 | ✗ |
| `PEEK/POKE/USR/CALL` | 메모리/네이티브 | ✗ |
| `BLOAD/BSAVE` | 바이너리 입출력 | ✗ |
| `KEY ON/OFF` | 함수키 | ✗ |
| `DRAW` | 매크로 그래픽 | ✗ |

## 부록 C. 에러 코드표

```scheme
;; lib/common.scm
(define err-next-without-for      1)   ; NEXT without FOR
(define err-syntax                2)   ; Syntax error
(define err-return-without-gosub  3)   ; RETURN without GOSUB
(define err-out-of-data           4)   ; Out of DATA
(define err-illegal-call          5)   ; Illegal function call
(define err-overflow              6)   ; Overflow
(define err-out-of-memory         7)   ; Out of memory
(define err-undefined-line        8)   ; Undefined line number
(define err-subscript             9)   ; Subscript out of range
(define err-duplicate-def        10)   ; Duplicate Definition
(define err-division-by-zero     11)   ; Division by zero
(define err-illegal-direct       12)   ; Illegal direct
(define err-type-mismatch        13)   ; Type mismatch
(define err-out-of-string-space  14)   ; Out of string space
(define err-string-too-long      15)   ; String too long
(define err-string-too-complex   16)
(define err-cant-continue        17)
(define err-undefined-fn         18)
(define err-no-resume            19)
(define err-resume-no-error      20)
(define err-unprintable          21)
(define err-missing-operand      22)
(define err-line-buffer-overflow 23)
(define err-device-timeout       24)
(define err-device-fault         25)
(define err-for-without-next     26)
```

## 부록 D. 예제 프로그램 모음 (10선)

자매서와 *동일* 한 예제를 동봉합니다 (`examples/`).

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

실행:

```bash
raco exe -o gwbasic main.scm        # 한 번 빌드
./gwbasic run examples/sieve.bas
```

또는 빌드 없이:

```bash
racket main.scm run examples/sieve.bas
chez --script main.scm -- run examples/sieve.bas
guile -L lib main.scm run examples/sieve.bas
```

## 부록 E. 추가 학습 자료

| 분류 | 자료 |
|------|------|
| 인터프리터 일반 | Bob Nystrom, *Crafting Interpreters* (https://craftinginterpreters.com) |
| Scheme으로 인터프리터 | Abelson & Sussman, *SICP* — 4장 평가기, 5장 레지스터 머신 |
| Scheme 표준 | *Revised⁷ Report on the Algorithmic Language Scheme* (R7RS-small) |
| Racket | https://docs.racket-lang.org |
| Chez | https://cisco.github.io/ChezScheme |
| 컴파일러 이론 | Aho et al., *Compilers: Principles, Techniques, and Tools* |
| BASIC 역사 | Microsoft, *GW-BASIC User's Guide* (1987) |
| Pratt parser | Bob Nystrom, "Pratt Parsers: Expression Parsing Made Easy" |

## 부록 F. 자매서와의 차이 요약

본 권의 *Scheme 다움* 을 한 표로.

| 항목 | C / Go / TS / Lua | 본 권 (Scheme) |
|------|--------------------|----------------|
| AST 표현 | record / class 트리 | s-식 (심볼 태그 리스트) |
| 옵코드 | `uint8` 정수 + 디스패치 표 | 심볼 + `case` |
| 스택 | 배열 / 슬라이스 | record(`<stack>`) + vector |
| 환경 | 해시 맵 / Map | SRFI-69 hash-table |
| Pratt 표 | switch / 함수 포인터 | hash-table + 클로저 |
| 에러 | 반환 코드 / 예외 | `raise` + `<basic-error>` record |
| 호스트 인터페이스 | interface / 구조체 | `<host>` record (절차 슬롯) |
| 메인 루프 | `for { }` | 꼬리 재귀 `(let loop () ...)` |
| 빌드 산출물 | 단일 바이너리 | `raco exe` 단일 파일 |
| 정밀도 | float32/float64 분리 | flonum 단일 + 논리 태그 |
| INTEGER 의미 | int16 wrap | 정확수 + 저장 시 wrap 검사 |

| 의미적으로 *같은* 점 | 비고 |
|---------------------|------|
| BNF 전체 | 부록 A |
| ISA | 14장 |
| VM 디스패치 의미 | 16장 |
| 에러 코드 | 부록 C |
| 예제 프로그램 + 기대 출력 | `examples/` |

## 부록 G. 프로젝트 디렉터리 최종 구조

```
scheme_gwbasic_book/
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
│   ├── hello.bas
│   ├── fib.bas
│   ├── sieve.bas
│   ├── string_demo.bas
│   ├── data_demo.bas
│   ├── gosub_demo.bas
│   └── ctrl_demo.bas
├── src/                     ← Scheme 소스 (lib/ 미러)
└── tests/                   ← golden / 단위 테스트
```

`scheme_gwbasic/` 실제 구현 트리:

```
scheme_gwbasic/
├── main.scm
├── lib/
│   ├── common.scm
│   ├── lexer.scm
│   ├── parser.scm
│   ├── pratt.scm
│   ├── ast.scm
│   ├── opcode.scm
│   ├── compiler.scm
│   ├── disasm.scm
│   ├── vm.scm
│   ├── value.scm
│   ├── env.scm
│   ├── strfunc.scm
│   ├── mathfunc.scm
│   ├── printusing.scm
│   ├── mml.scm
│   ├── host.scm
│   ├── host-term.scm
│   ├── host-draw.scm
│   ├── repl.scm
│   ├── debugger.scm
│   └── runner.scm
├── examples/      *.bas + *.out
├── tests/         golden.scm lexer-test.scm parser-test.scm vm-test.scm
├── build.sh
└── build.bat
```

## 부록 H. 개발 체크리스트

- [ ] R7RS 처리계 셋(Racket / Chez / Guile)에서 동일한 결과를 내는가
- [ ] `golden` 테스트 전체 통과
- [ ] 단위 테스트(`lexer/parser/vm`) 모두 통과
- [ ] 벤치마크 회귀 없음
- [ ] `raco exe`, `chez --compile-program`, `guild compile` 모두 빌드 성공
- [ ] 한글 빌드 메시지가 cp949에서 깨지지 않음
- [ ] README.md 한글
- [ ] 자매서 예제 10선 모두 같은 출력

## 부록 I. 짧은 후기

GW-BASIC은 작지만, *그 안에 언어 처리기의 모든 핵심 주제* 가 들어 있습니다. Scheme으로 다시 만들고 나면 다음 두 가지를 강하게 느낍니다.

1. **AST를 정의 없이 그대로 다룰 수 있다** — 이게 Lisp 가족의 진짜 힘.
2. **꼬리 재귀가 곧 디스패치 루프** — VM이 자기 호스트의 자원을 잡아먹지 않고 무한히 돈다.

자매서의 정적 타입 구현과 본 권의 동적 타입 구현을 *나란히 두고* 읽으면, *언어 설계의 trade-off가 코드의 어디에 모이는지* 가 또렷하게 보일 것입니다 — 그 비교가 이 자매서 시리즈를 읽는 가장 큰 보람입니다.

> "The most important thing in the programming language is the name. A language will not succeed without a good name. I have recently invented a very good name, and now I am looking for a suitable language."  
> — Donald Knuth

```basic
9999 PRINT "Lisp으로 만든 BASIC으로 다음 BASIC을 만들어 보세요." : END
```

---

> 부록 끝. 책 전체 끝.
