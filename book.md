# C로 만드는 GW-BASIC 인터프리터

**ANSI C로 직접 짠 스택 기반 바이트코드 가상 머신과 1980년대 명작 언어의 부활 — 200페이지 가이드**

저자: chobocho
판: 1.0 (2026)
대상: 컴파일러/인터프리터를 C 수준에서 직접 만들어 보고 싶은 개발자
선수 지식: C99 문법(포인터, 구조체, 동적 할당), 자료구조의 일반적 이해

---

## 머리말

이 책은 자매편 「Lua로 만드는 GW-BASIC 인터프리터」와 정확히 같은 가상 머신 설계를 C로 다시 구현한다. 명령어 집합·바이트코드 형식·실행 의미는 한 글자도 다르지 않다. 그러나 언어가 바뀌면 보이는 풍경이 다르다. C에서는 메모리 소유권을 손으로 관리해야 하고, 동적 배열을 매크로로 만들어야 하며, 문자열 연결조차 한 줄에 끝나지 않는다. 그 대신 우리가 얻는 것은 “컴퓨터에 가장 가까운 거리에서 본 인터프리터”다. 데이터 구조의 한 바이트 한 바이트가 모두 우리의 결정이며, 그 결정의 결과가 어떻게 동작하는지가 즉각적이다.

이 책은 다음의 흐름을 따라 한 줄 한 줄 빌드해 나간다.

1. **언어 명세를 BNF로 정의한다.** 무엇을 만드는지가 분명해야 무엇을 짤지가 분명해진다.
2. **어휘 분석기(lexer)를 작성한다.** 문자의 흐름을 토큰의 흐름으로 바꾼다.
3. **재귀 하강 파서를 작성한다.** 토큰을 추상 구문 트리(AST)로 바꾼다.
4. **바이트코드를 설계한다.** Lua판과 동일한 명령어 집합을 사용한다.
5. **컴파일러를 작성한다.** AST를 바이트코드로 낮춘다(lower).
6. **스택 기반 가상 머신을 작성한다.** 바이트코드를 실행한다.
7. **표준 라이브러리를 채운다.** 약 30종의 GW-BASIC 내장 함수.
8. **REPL과 파일 로더로 마무리한다.** `make && ./cgwbasic prog.bas` 한 줄로 실행된다.

이 책의 코드는 약 2,400줄의 C99로, 외부 의존성은 `libm`(수학) 하나뿐이다. 부록 C에 모든 소스를 그대로 실었으니 책 한 권만 있으면 빈 디스크에서 다시 만들어 낼 수 있다.

---

## 차례

**제1부 도입과 배경**
- 1장 GW-BASIC을 C로 다시 만드는 이유
- 2장 인터프리터의 5단계 파이프라인
- 3장 C99 빠른 복습과 우리 코딩 컨벤션
- 4장 프로젝트 구조와 빌드 시스템

**제2부 기초 자료구조**
- 5장 동적 배열 매크로 `VEC(T)`
- 6장 BASIC의 Value 타입 — 태그된 공용체
- 7장 메모리 소유권 모델과 안전 패턴

**제3부 어휘 분석**
- 8장 토큰의 정의
- 9장 손으로 짜는 어휘 분석기
- 10장 숫자/문자열 리터럴, 타입 접미어
- 11장 키워드 vs 식별자 — 가장 긴 일치

**제4부 문법과 파서**
- 12장 BNF로 표현하는 GW-BASIC 문법
- 13장 재귀 하강 파서 골격
- 14장 표현식 파서 — Pratt(precedence climbing)
- 15장 문장 파서, 라인 번호, IF/FOR/ON GOTO

**제5부 AST와 컴파일러**
- 16장 AST 노드 — 한 구조체에 모두 담기
- 17장 바이트코드 명령어 집합
- 18장 표현식 컴파일과 후위 순회
- 19장 백패치, 라인 매핑, FOR/WHILE 스택

**제6부 가상 머신**
- 20장 VM 상태와 메인 디스패치 루프
- 21장 변수 환경과 동적 슬롯
- 22장 GOSUB / RETURN 호출 스택
- 23장 다차원 배열의 평탄화와 자동 DIM

**제7부 런타임과 내장 함수**
- 24장 PRINT의 의외로 깊은 세계
- 25장 INPUT, DATA, READ, RESTORE
- 26장 수학·문자열 내장 함수 카탈로그
- 27장 DEF FN과 사용자 정의 함수

**제8부 통합과 마무리**
- 28장 REPL 만들기
- 29장 fib.bas의 전 생애 추적 — 한 명령씩 따라가기
- 30장 흔한 함정과 디버깅 패턴
- 31장 연습 문제와 다음 단계

**부록**
- 부록 A 전체 BNF
- 부록 B 바이트코드 명령어 사전
- 부록 C 전체 C 소스 코드 (헤더 + 구현)
- 부록 D 예제 .BAS 프로그램 모음
- 부록 E 참고 문헌과 더 읽을거리

---

# 제1부 — 도입과 배경

## 1장. GW-BASIC을 C로 다시 만드는 이유

### 1.1 두 권의 책, 한 개의 VM

이 책의 자매편인 「Lua판」은 같은 인터프리터를 Lua 5.1으로 만들었다. 두 책은 동일한 파이프라인, 동일한 바이트코드 명령어 집합, 동일한 의미 의미론을 가진다. 그러므로 한 권을 읽었다면 다른 권의 80%는 이미 익숙하다. 그러나 “내가 모든 메모리를 손으로 관리한다”는 사실 하나가 코드의 모양을 거의 모두 바꾼다.

이 책에서 우리는 다음을 배운다.

- C에서 다형 값(BASIC의 숫자 또는 문자열)을 안전하게 다루는 패턴
- 매크로 한 줄로 만드는 일반 `VEC(T)`과 그 한계
- 이름을 키로 쓰는 단순 변수 슬롯 vs 해시 테이블 — 작은 인터프리터에서의 trade-off
- 컴파일 시 백패치와 “보류 점프” 목록의 명시적 관리
- 스택 머신의 핸들러를 거대한 `switch` 한 덩어리로 짜는 법

### 1.2 “Lua판의 VM을 그대로 쓴다”는 약속의 의미

이 책이 시작될 때 저자가 자신에게 한 약속은 단 하나, “Lua판의 VM을 그대로 쓴다”였다. 즉 명령어 카탈로그와 의미가 변함이 없다. 그러므로 같은 .BAS 프로그램이 두 인터프리터에서 같은 결과를 낸다. `examples/` 디렉터리의 7개 프로그램은 모두 두 인터프리터에서 비트-단위로(`PRINT`의 공백 패딩까지 포함하여) 동일한 출력을 만든다.

이 약속은 학습 면에서도 중요하다. C판이 “더 멋진 VM”을 새로 짜려고 시작했다면, 어디까지가 “언어 차이”이고 어디까지가 “설계 변경”인지 분간하기 어려워진다. 우리는 언어 차이만을 본다.

### 1.3 이 책에서 만드는 것의 모양

```
.bas  ──[lexer]──▶  토큰 ──[parser]──▶  AST ──[compiler]──▶  bytecode ──[vm]──▶  표준출력
```

이 다이어그램의 다섯 화살표가 곧 다섯 모듈이다.

```
src/
├── common.[ch]   - VEC 매크로, xmalloc, 문자열 헬퍼
├── value.[ch]    - Value 태그된 공용체
├── lexer.[ch]    - 어휘 분석기
├── ast.[ch]      - AST 노드 정의
├── parser.[ch]   - 재귀 하강 파서
├── runtime.[ch]  - 내장 함수 테이블
├── compiler.[ch] - AST → bytecode
├── vm.[ch]       - 가상 머신
└── main.c        - REPL / 파일 로더
```

### 1.4 빌드와 실행

```sh
$ make
$ ./cgwbasic examples/sieve.bas
$ ./cgwbasic                    # REPL
```

빌드는 평범한 GNU `make`이며, 의존성은 표준 C99와 `libm`뿐이다.

---

## 2장. 인터프리터의 5단계 파이프라인

### 2.1 다섯 단계의 역할

| 단계 | 입력 | 출력 | 모듈 |
|---|---|---|---|
| Lexing | 문자열 | 토큰 배열 | `lexer.c` |
| Parsing | 토큰 | AST | `parser.c` |
| Compiling | AST | 바이트코드 | `compiler.c` |
| Execution | 바이트코드 | 출력/상태 | `vm.c` |
| Runtime | 호출 | 결과 | `runtime.c` |

각 단계는 “단방향 함수”에 가깝고, 단계 사이의 인터페이스는 단순한 C 구조체다.

### 2.2 한 줄로 보는 파이프라인

```basic
10 LET A = 1 + 2 * 3
```

토큰:

```
NUMBER(10) KEYWORD(LET) IDENT(A) EQ NUMBER(1) PLUS NUMBER(2) STAR NUMBER(3) EOL EOF
```

AST:

```
Program
└─ Line(10) Let(target=Var(A), expr=BinOp(+, NumLit(1), BinOp(*, NumLit(2), NumLit(3))))
```

바이트코드:

```
1: PUSHN 1
2: PUSHN 2
3: PUSHN 3
4: MUL
5: ADD
6: STORE A
7: HALT
```

VM 스택 변화:

```
PUSHN 1: [1]
PUSHN 2: [1, 2]
PUSHN 3: [1, 2, 3]
MUL    : [1, 6]
ADD    : [7]
STORE A: []     # A = 7
HALT   : 종료
```

### 2.3 “단계 분리”라는 단순한 미덕

각 단계가 독립적이라는 점이 가져다주는 이득은 다음과 같다.

- **테스트 가능성.** 어휘 분석기는 함수 하나에 입력을 넣고 토큰 배열을 받는다. 검증이 자명하다.
- **단방향 의존.** 컴파일러는 어휘 분석기를 모른다. 어휘 분석기는 파서를 모른다.
- **디버깅의 분할정복.** 출력이 이상하면 “어느 단계의 출력이 이상한지”를 먼저 묻는다.
- **재사용성.** 어휘 분석기와 파서는 인터프리터·컴파일러·포매터·정적 분석기 모두에 쓸 수 있다.

이 다섯 단계 그림은 책 내내 우리의 나침반이다.

### 2.4 컴파일 vs 즉시 실행

전통적인 BASIC 인터프리터는 “라인 단위 즉시 실행”에 가깝다. 이 책은 모든 라인을 한 번에 읽고 컴파일한 뒤, 그 결과 바이트코드를 실행한다. 트레이드오프:

| | 즉시 실행 | 사전 컴파일 (우리 방식) |
|---|---|---|
| 시작 지연 | 거의 0 | 작다 |
| 실행 속도 | 느림 | 빠름 |
| GOTO 점프 비용 | 라인 텍스트 → 다시 파싱 | 명령 인덱스 한 번 |
| 라인 수정 즉시성 | 좋음 | 재컴파일 필요 |

REPL에서는 사용자가 라인을 추가/수정할 때마다 누적된 텍스트를 통째로 다시 컴파일한다. BASIC 프로그램은 작아서 이 비용이 무시할 만하다.

---

## 3장. C99 빠른 복습과 우리 코딩 컨벤션

### 3.1 우리는 C99로 적는다

이 책의 코드는 다음 기능에 의존한다.

- 가변 길이 배열 — **사용하지 않음** (스택 안전성)
- 지정 초기자 `(struct){.x=1}` — 가끔 사용
- `bool`/`<stdbool.h>` — 사용
- C99 한 줄 주석 — 사용
- `<stdint.h>` — 미사용 (모든 정수는 `int`/`long`/`double`)

C11 이후의 `_Generic`, `static_assert`, anonymous structs/unions는 사용하지 않는다(이식성 우선).

### 3.2 메모리 함수의 안전 래퍼

```c
void *xmalloc(size_t n);
void *xrealloc(void *p, size_t n);
char *xstrdup(const char *s);
char *xstrndup(const char *s, size_t n);
void  die(const char *fmt, ...) __attribute__((noreturn));
```

이 다섯 함수가 우리의 “안전망”이다. `xmalloc(0)`은 0바이트를 요구하는 시나리오가 아예 없으므로 그저 통과시킨다. `die`는 `fprintf` 후 `exit(2)`이며 결코 반환하지 않는다.

### 3.3 명명 규칙

- 타입은 `PascalCase` (예: `Value`, `Token`, `AstNode`).
- 함수는 `snake_case` (예: `lex_string`, `compile_expr`).
- 매크로는 `UPPER_CASE` 또는 `vec_*`(소문자) 두 가지 모두 등장.
- 모듈 접두는 강제하지 않는다(헤더가 모듈 경계를 표현).

### 3.4 헤더 가드

```c
#ifndef MOD_H
#define MOD_H
...
#endif
```

`#pragma once`는 쓰지 않는다(조금이지만 이식성 우려).

### 3.5 “모든 strdup된 메모리는 누군가의 소유다”

이 책의 모든 동적 문자열은 정확히 한 곳에서 free된다. 토큰의 `text`는 `tokens_free`가, AST의 `s1/s2/slist`는 `ast_free`가, 바이트코드의 `sarg`는 `bytecode_free`가, VM의 변수/배열은 `vm_free`가 풀어낸다. 누가 누구를 소유하는지를 7장에서 더 다룬다.

---

## 4장. 프로젝트 구조와 빌드 시스템

### 4.1 디렉터리

```
c_gwbasic_book/
├── book.md             ← 이 책
├── README.md           ← 한국어 안내
├── Makefile            ← 빌드
├── src/                ← 인터프리터
│   ├── common.[ch]
│   ├── value.[ch]
│   ├── lexer.[ch]
│   ├── ast.[ch]
│   ├── parser.[ch]
│   ├── runtime.[ch]
│   ├── compiler.[ch]
│   ├── vm.[ch]
│   └── main.c
├── examples/           ← .BAS 예제
└── tests/              ← 단위 테스트(선택)
```

### 4.2 Makefile

```makefile
CC      ?= gcc
CFLAGS  ?= -O2 -std=c99 -Wall -Wextra
LDLIBS  ?= -lm

SRC := src/common.c src/value.c src/lexer.c src/ast.c src/parser.c \
       src/runtime.c src/compiler.c src/vm.c src/main.c
OBJ := $(SRC:.c=.o)
BIN := cgwbasic

all: $(BIN)
$(BIN): $(OBJ); $(CC) $(CFLAGS) -o $@ $(OBJ) $(LDLIBS)
%.o: %.c   ; $(CC) $(CFLAGS) -c -o $@ $<
clean:     ; rm -f $(OBJ) $(BIN)
```

### 4.3 모듈 의존도

```
main.c
 ├─ lexer
 ├─ parser ── ast
 ├─ compiler ── ast, runtime
 └─ vm ── runtime, ast (eval_expr_ast)

runtime ── value
common ── (없음)
```

순환 의존이 없도록 신경 썼다.

### 4.4 “외부 라이브러리 없음”의 의미

표준 C99 + libm 외에는 의존성이 없다. 그러므로 어떤 POSIX 환경(Linux, macOS, *BSD, Cygwin, Termux)에서도 곧장 빌드된다. Windows에서도 MinGW로 동일하게 동작한다(예제는 `\n` 기반이라 줄바꿈 처리가 호환됨).

### 4.5 디렉터리에서 한 명령으로 빌드/실행

```sh
$ make
$ ./cgwbasic examples/hello.bas
HELLO, GW-BASIC!
               1             1             1 
               2             4             8 
               3             9             27 
               4             16            64 
               5             25            125 
DONE.
```

---

# 제2부 — 기초 자료구조

## 5장. 동적 배열 매크로 `VEC(T)`

### 5.1 왜 매크로인가

C에는 제네릭이 없다. 동적 배열을 타입마다 새로 짜는 것은 끔찍하다. 그래서 이 책은 한 매크로로 모든 동적 배열을 처리한다.

```c
#define VEC(T) struct { T *data; int len, cap; }
```

선언:

```c
typedef VEC(int)    IntList;
typedef VEC(char*)  StrList;
typedef VEC(Token)  Tokens;
```

각 인스턴스는 `(T*, int, int)` 묶음이다. 메모리 레이아웃은 모두 같지만 컴파일러가 타입을 분리해 준다(서로 호환 안 됨).

### 5.2 push/grow

```c
#define vec_grow(v, T) do { \
    if ((v)->len == (v)->cap) { \
        (v)->cap = (v)->cap ? (v)->cap * 2 : 8; \
        (v)->data = (T*)xrealloc((v)->data, sizeof(T) * (v)->cap); \
    } \
} while(0)

#define vec_push(T, v, x) do { vec_grow(v, T); (v)->data[(v)->len++] = (x); } while(0)
```

`T`를 매크로 인자로 받는 이유는 sizeof 추론과 캐스트 때문이다. 호출은 다음과 같다.

```c
Tokens t; vec_init(&t);
Token tk = { T_NUMBER, 10, NULL, 1 };
vec_push(Token, &t, tk);
```

### 5.3 “이 매크로의 한계”

- **컴파일 시간 함수 vs 런타임 함수의 경계가 흐려진다.** 매크로는 디버깅이 까다롭다. 컴파일 에러가 길게 나오기 쉽다.
- **요소 비교/검색은 별도로 짜야 한다.** `vec_find`를 일반화하기는 까다롭다. 우리는 매번 짧은 for 루프로 짠다.
- **요소 해제(free)는 호출자의 책임이다.** push할 때 소유권이 이전됐다고 약속해야 한다.

### 5.4 free 패턴

각 모듈은 자기가 만든 `VEC`을 자기가 푼다.

```c
void tokens_free(Tokens *t) {
    for (int i = 0; i < t->len; ++i) free(t->data[i].text);
    vec_free(t);
}
```

이 한 패턴이 `ast_free`, `bytecode_free`, `vm_free`에 반복된다.

---

## 6장. BASIC의 Value 타입 — 태그된 공용체

### 6.1 Value의 모양

```c
typedef enum { V_NUM, V_STR } VType;

typedef struct {
    VType type;
    union {
        double num;
        char  *str;   /* 소유 */
    } as;
} Value;
```

이 16~24바이트짜리 구조체가 BASIC의 모든 값을 담는다. 숫자와 문자열만 있으면 된다(BASIC은 다른 타입이 없다).

### 6.2 생성/해제 API

```c
Value v_num(double n);
Value v_str_copy(const char *s);   /* 입력을 복사 */
Value v_str_take(char *s);         /* 인자의 소유권을 가져감 */
Value v_clone(Value v);            /* 깊은 복사 */
void  v_release(Value *v);         /* str 이라면 free */
```

`v_str_take`는 자주 등장한다. 함수가 `xmalloc`으로 만든 문자열을 그대로 반환할 때 한 번의 strdup을 절약해 준다.

### 6.3 강제 변환

BASIC은 “느슨한 타입”이지만 변수의 접미어로 정해진 타입이 있다.

| 접미어 | 타입 | C에서 |
|---|---|---|
| `$` | 문자열 | V_STR |
| `%` | 정수 (16비트) | V_NUM (정수화) |
| `!` | 단정도 실수 | V_NUM |
| `#` | 배정도 실수 | V_NUM |
| (없음) | 단정도 (기본) | V_NUM |

```c
Value coerce_for_var(const char *name, Value v) {
    char k = var_kind(name);   /* 's', 'i', 'n' */
    if (k == 's') {
        if (v.type == V_NUM) die("Type mismatch: ...");
        return v;
    }
    if (v.type == V_STR) die("Type mismatch: ...");
    if (k == 'i') v.as.num = floor(v.as.num + 0.5);
    return v;
}
```

이 함수는 STORE 명령에서 매번 호출되어 “변수 이름이 약속한 타입으로” 강제한다.

### 6.4 BASIC식 문자열 출력

```c
char *v_to_basic_string(Value v) {
    if (v.type == V_STR) return xstrdup(v.as.str ? v.as.str : "");
    char buf[64];
    double n = v.as.num;
    if (n == floor(n) && fabs(n) < 1e15)
        snprintf(buf, sizeof(buf), n >= 0 ? " %lld " : "%lld ", (long long)n);
    else
        snprintf(buf, sizeof(buf), n >= 0 ? " %.7g " : "%.7g ", n);
    return xstrdup(buf);
}
```

양수면 앞뒤로 한 칸 공백, 음수면 앞은 `-`, 뒤는 한 칸 공백. 이 미세한 규칙이 GW-BASIC의 PRINT를 흉내내는 데 결정적이다(21장).

---

## 7장. 메모리 소유권 모델과 안전 패턴

### 7.1 “누가 free하는가”

C에서 메모리 버그의 99%는 “누가 풀지가 모호하다”에서 시작한다. 우리는 다음과 같은 단순한 규칙을 둔다.

1. **모든 strdup된 문자열은 한 곳에서 풀린다.** 그 한 곳을 “소유자”라 부른다.
2. **소유는 push/추가의 시점에 이전된다.** 이미 push한 객체를 호출자가 free하면 안 된다.
3. **VEC가 소유한 요소는 VEC 해제 함수가 모두 푼다.**
4. **함수가 반환하는 `Value`는 호출자가 소유한다(`v_release`로 풀 책임).** 단, push한 시점에는 push 한 자료구조가 소유한다.

### 7.2 스택의 Value 다루기

```c
static void push_v(VM *vm, Value v);
static Value pop_v(VM *vm);
```

push는 인자의 소유권을 가져간다. pop은 호출자에게 소유권을 넘긴다. 그러므로 다음은 누수다.

```c
Value v = pop_v(vm);
do_something(v);    /* 결과를 안 쓰면 */
/* v_release(&v) 가 빠짐 */
```

이런 실수를 줄이기 위해 모든 “비교/연산” 핸들러는 다음 패턴을 따른다.

```c
case OP_SUB: {
    Value b = pop_v(vm); Value a = pop_v(vm);
    push_v(vm, v_num(v_to_num(a) - v_to_num(b)));
    v_release(&a); v_release(&b);
    break;
}
```

문자열을 숫자로 강제할 때 `v_to_num`만 호출하므로 원본 `Value`는 release만 하면 된다.

### 7.3 변수 슬롯의 교체

변수 STORE의 의미는 “기존 값을 풀고, 새 값을 채워 넣는다”이다.

```c
static void set_var(VM *vm, const char *name, Value v) {
    v = coerce_for_var(name, v);
    int i = find_var(vm, name);
    if (i < 0) {
        VarSlot s = { xstrdup(name), v };
        vec_push(VarSlot, &vm->vars, s);
    } else {
        v_release(&vm->vars.data[i].value);
        vm->vars.data[i].value = v;
    }
}
```

오래된 슬롯의 값을 release하지 않으면 string이 누수된다. 짧지만 가장 자주 쓰이는 “해제+덮어쓰기” 패턴이다.

### 7.4 배열 슬롯의 dim 재할당

DIM은 한 번만 일어나야 정상이지만, 우리 구현은 두 번째 DIM을 “기존 데이터 풀기 + 새 데이터”로 처리한다.

```c
if (i >= 0) {
    free(vm->arrays.data[i].name);
    free(vm->arrays.data[i].dims);
    for (int j = 0; j < vm->arrays.data[i].data_size; ++j)
        v_release(&vm->arrays.data[i].data[j]);
    free(vm->arrays.data[i].data);
}
```

이 자리가 누수의 단골 후보이므로 별도 함수 `dim_array_internal`로 분리되어 있다.

### 7.5 “분산된 자유는 결합된 자유보다 약하다”

이 책의 코드는 “모든 free를 ast_free/bytecode_free/vm_free 세 함수에 모은다”는 원칙을 따른다. 이 원칙 덕에 valgrind 결과는 항상 깨끗하다(실험으로 직접 돌려 보길 권한다 — 4장의 `make` 다음에 `valgrind ./cgwbasic examples/sieve.bas`).

---

# 제3부 — 어휘 분석

## 8장. 토큰의 정의

### 8.1 토큰의 데이터 구조

```c
typedef enum {
    T_EOF = 0,    T_EOL,
    T_NUMBER,     T_STRING,    T_IDENT,    T_KEYWORD,    T_REM,
    T_COLON,      T_SEMI,      T_COMMA,
    T_LPAREN,     T_RPAREN,
    T_PLUS,       T_MINUS,     T_STAR,     T_SLASH,
    T_BACKSLASH,  T_CARET,
    T_EQ,         T_NE,        T_LT,       T_GT,        T_LE,    T_GE
} TokType;

typedef struct {
    TokType type;
    double  num;     /* T_NUMBER 인 경우 */
    char   *text;    /* 소유: STRING/IDENT/KEYWORD */
    int     line;
} Token;
```

토큰 한 개는 24바이트 안팎이다. `num`과 `text`는 동시에 의미가 있을 수 있으므로 `union`으로 묶지 않았다. (필드 두 개에 24바이트라면 union 의 절약이 크지 않고 코드만 복잡해진다.)

### 8.2 GW-BASIC의 특이성

- 변수 이름의 마지막 한 글자가 타입 접미어다.
- 키워드는 약 40개. 그 외는 식별자.
- `?`은 `PRINT`의 약식.
- `<>`, `<=`, `>=`는 두 글자 연산자.

이 모든 것은 어휘 분석기가 한곳에서 처리한다.

### 8.3 토큰 직렬화 — 디버그용

```c
const char *tok_name(TokType t);
```

디버깅 시 다음과 같이 토큰 스트림을 한 줄씩 찍어 볼 수 있다.

```c
for (int i = 0; i < toks.len; ++i) {
    Token *t = &toks.data[i];
    fprintf(stderr, "%-7s %s %g (line %d)\n",
        tok_name(t->type), t->text ? t->text : "", t->num, t->line);
}
```

---

## 9장. 손으로 짜는 어휘 분석기

### 9.1 상태 객체

```c
typedef struct {
    const char *src;
    int   pos;
    int   line;
    Tokens *out;
} Lx;
```

`src`는 입력 문자열, `pos`는 현재 위치, `line`은 디버그용. 출력 토큰은 호출자가 제공한 `Tokens`에 누적된다.

### 9.2 핵심 헬퍼

```c
static char peek(Lx *l, int off) { return l->src[l->pos + off]; }
static char advance(Lx *l) {
    char c = l->src[l->pos];
    if (c) {
        ++l->pos;
        if (c == '\n') ++l->line;
    }
    return c;
}
static void emit(Lx *l, TokType t, const char *text, int textlen, double num);
```

`peek`은 `pos`를 옮기지 않고 글자를 본다. `advance`는 한 글자 진행한다. `emit`은 토큰을 만들어 `Tokens`에 push한다(인자 `text`가 NULL이 아니면 `xstrndup`으로 복사).

### 9.3 메인 디스패치

```c
while (l.src[l.pos]) {
    while (peek(&l,0)==' '||peek(&l,0)=='\t'||peek(&l,0)=='\r') advance(&l);
    char c = peek(&l, 0);
    if (!c) break;
    switch (c) {
    case '\n': emit(&l, T_EOL, NULL, 0, 0); advance(&l); break;
    case ':':  emit(&l, T_COLON,  NULL, 0, 0); advance(&l); break;
    case '+':  emit(&l, T_PLUS,   NULL, 0, 0); advance(&l); break;
    /* ... 한 글자 토큰들 ... */
    case '<':
        advance(&l);
        if (peek(&l, 0) == '=')      { advance(&l); emit(&l, T_LE, NULL, 0, 0); }
        else if (peek(&l, 0) == '>') { advance(&l); emit(&l, T_NE, NULL, 0, 0); }
        else                         emit(&l, T_LT, NULL, 0, 0);
        break;
    case '"': lex_string(&l); break;
    default:
        if (isdigit((unsigned char)c) || (c == '.' && isdigit((unsigned char)peek(&l,1))))
            lex_number(&l);
        else if (isalpha((unsigned char)c) || c == '_')
            lex_ident(&l);
        else
            die("알 수 없는 문자 '%c' (line %d)", c, l.line);
    }
}
emit(&l, T_EOF, NULL, 0, 0);
```

이 한 함수가 어휘 분석기의 80%다. 나머지 20%는 숫자/문자열/식별자 보조 함수들이다.

### 9.4 두 글자 연산자 처리의 함정

`<` 하나만 보고 `T_LT`를 emit하면 안 된다. 다음 글자가 `=`이면 `<=`, `>`이면 `<>`다. 위 코드처럼 “`<`를 advance한 뒤 다음 글자 분기”가 정석.

### 9.5 `?` → `PRINT`

```c
case '?': emit(&l, T_KEYWORD, "PRINT", 5, 0); advance(&l); break;
```

GW-BASIC은 `PRINT`를 `?`로 줄여 쓸 수 있다. 어휘 차원에서 이를 KEYWORD(PRINT) 토큰으로 곧장 변환한다.

---

## 10장. 숫자/문자열 리터럴, 타입 접미어

### 10.1 숫자 리터럴 lexer

```c
static void lex_number(Lx *l) {
    int start = l->pos;
    while (isdigit((unsigned char)peek(l, 0))) advance(l);
    if (peek(l, 0) == '.') {
        advance(l);
        while (isdigit((unsigned char)peek(l, 0))) advance(l);
    }
    char p = peek(l, 0);
    if (p == 'e' || p == 'E' || p == 'd' || p == 'D') {
        advance(l);
        if (peek(l, 0) == '+' || peek(l, 0) == '-') advance(l);
        while (isdigit((unsigned char)peek(l, 0))) advance(l);
    }
    char p2 = peek(l, 0);
    if (p2 == '%' || p2 == '!' || p2 == '#') advance(l);

    /* 잘라낸 텍스트를 strtod로 변환 */
    /* d/D는 e로 치환, 끝의 접미어는 제거 */
    /* ... */
    emit(l, T_NUMBER, NULL, 0, strtod(buf, NULL));
}
```

핵심은 “문자를 진행시키며 시작/끝을 표시하고, 마지막에 `strtod`로 한 번에 파싱한다”이다. 자릿수마다 곱하면 부동소수 누적 오차의 원인이 된다.

### 10.2 문자열 리터럴 lexer

```c
static void lex_string(Lx *l) {
    advance(l);              /* 여는 " */
    int start = l->pos;
    while (peek(l, 0) && peek(l, 0) != '"' && peek(l, 0) != '\n') advance(l);
    int end = l->pos;
    if (peek(l, 0) != '"') die("문자열이 닫히지 않았습니다 (line %d)", l->line);
    advance(l);              /* 닫는 " */
    emit(l, T_STRING, l->src + start, end - start, 0);
}
```

GW-BASIC은 이스케이프가 없다. `"`는 곧 종료다. `\n`이 닫히지 않은 채 와도 에러다.

### 10.3 타입 접미어 정책

이 책은 **숫자 리터럴의 접미어**(`100%`, `1.5!`, `1.234#`)는 무시한다. BASIC 차원에서는 접미어가 “이 값을 어떤 정밀도로 다룰지”의 힌트지만, 우리 VM은 모든 숫자를 `double`로 통일한다. 정밀도 차이는 무시한다.

반면 **변수 이름의 접미어**(`A`, `A%`, `A!`, `A#`, `A$`)는 의미가 있다. 어휘 분석기가 식별자의 끝 글자로 접미어를 흡수해 토큰의 `text`에 그대로 포함시킨다(`"NAME$"`).

---

## 11장. 키워드 vs 식별자 — 가장 긴 일치

### 11.1 알고리즘

```c
static void lex_ident(Lx *l) {
    int start = l->pos;
    while (isalnum((unsigned char)peek(l, 0)) || peek(l, 0) == '_') advance(l);
    char p = peek(l, 0);
    if (p == '$' || p == '%' || p == '!' || p == '#') advance(l);

    int len = l->pos - start;
    char *raw = xstrndup(l->src + start, len);
    str_upper(raw);
    /* 접미어를 뺀 본체로 키워드 검사 */
    char *probe = xstrdup(raw);
    int plen = (int)strlen(probe);
    if (plen && (probe[plen-1]=='$'||probe[plen-1]=='%'||
                 probe[plen-1]=='!'||probe[plen-1]=='#')) probe[plen-1] = 0;

    if (is_keyword(probe)) {
        if (str_ieq(probe, "REM")) {
            while (peek(l, 0) && peek(l, 0) != '\n') advance(l);
            free(raw); free(probe);
            emit(l, T_REM, NULL, 0, 0); return;
        }
        emit(l, T_KEYWORD, probe, (int)strlen(probe), 0);
        free(raw); free(probe); return;
    }
    free(probe);
    emit(l, T_IDENT, raw, (int)strlen(raw), 0);
    free(raw);
}
```

알고리즘은 다음과 같다.

1. 알파벳/숫자가 이어지는 한 끝까지 읽는다(가장 긴 일치).
2. 끝에 타입 접미어가 있으면 함께 흡수한다.
3. 결과를 대문자로 정규화한다.
4. 접미어를 빼고 키워드 사전을 조회한다.

### 11.2 REM의 특수성

REM은 키워드 인식과 동시에 “줄 끝까지 무시”로 빠진다. 일반 키워드 토큰을 emit하지 않고 `T_REM` 마커만 emit한다. 파서는 `T_REM`을 만나면 `A_REM` 노드를 만들고 끝낸다.

### 11.3 FN의 특수성

`DEF FNSQR(X) = X*X`에서 `FNSQR`은 한 식별자다(가장 긴 일치). `FN`은 키워드 사전에 등록되어 있지만, `FN` 단독으로 등장할 때만 키워드 토큰이 된다. 파서가 `IDENT(FNSQR)`를 보고 “이 이름은 FN으로 시작하므로 사용자 정의 함수”라고 결정한다(15장).

---

# 제4부 — 문법과 파서

## 12장. BNF로 표현하는 GW-BASIC 문법

### 12.1 표기 약속

- `<x>` 비단말, `"x"` 리터럴, `x | y` 분기, `x*` 0회 이상, `x+` 1회 이상, `x?` 0/1회.

### 12.2 프로그램 구조

```
<program>     ::= ( <line> <eol> )*
<line>        ::= <line-number>? <statement-list>
<statement-list> ::= <statement> ( ":" <statement> )*
```

### 12.3 문장

```
<statement> ::= <let> | <print> | <input> | <if>
              | <for> | <next> | <while> | <wend>
              | <goto> | <gosub> | <return>
              | <end> | <stop> | <rem> | <cls>
              | <dim> | <data> | <read> | <restore>
              | <def-fn> | <on-goto>
```

### 12.4 단순 문장들

```
<let>     ::= ( "LET" )? <lvalue> "=" <expr>
<lvalue>  ::= <ident> ( "(" <expr> ( "," <expr> )* ")" )?
<print>   ::= "PRINT" <print-list>?
<print-list> ::= <print-item> ( <print-sep> <print-item>? )*
<print-item> ::= <expr> | "TAB" "(" <expr> ")" | "SPC" "(" <expr> ")"
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

### 12.5 제어 흐름

```
<if>    ::= "IF" <expr> ( "THEN" | "GOTO" ) <then-branch>
            ( "ELSE" <then-branch> )?
<then-branch> ::= <line-number> | <statement-list>
<for>   ::= "FOR" <ident> "=" <expr> "TO" <expr> ( "STEP" <expr> )?
<next>  ::= "NEXT" ( <ident> ( "," <ident> )* )?
<while> ::= "WHILE" <expr>
<wend>  ::= "WEND"
<on-goto> ::= "ON" <expr> ( "GOTO" | "GOSUB" )
              <line-number> ( "," <line-number> )*
```

### 12.6 데이터 / 함수

```
<dim>     ::= "DIM" <ident> "(" <expr> ( "," <expr> )* ")"
              ( "," <ident> "(" <expr> ( "," <expr> )* ")" )*
<data>    ::= "DATA" <data-item> ( "," <data-item> )*
<data-item> ::= <number> | <string> | <unquoted-string>
<read>    ::= "READ" <lvalue> ( "," <lvalue> )*
<restore> ::= "RESTORE" <line-number>?
<def-fn>  ::= "DEF" "FN" <ident> ( "(" <ident> ( "," <ident> )* ")" )? "=" <expr>
```

### 12.7 표현식 (계층 구조)

```
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
```

이 BNF는 아래 14장에서 “precedence climbing” 한 함수로 줄어든다.

---

## 13장. 재귀 하강 파서 골격

### 13.1 파서의 상태

```c
typedef struct {
    Tokens *t;
    int pos;
} P;

static Token *cur(P *p)       { return &p->t->data[p->pos]; }
static Token *advance_t(P *p) { return &p->t->data[p->pos++]; }
static int    check(P *p, TokType t);
static int    accept_t(P *p, TokType t);
static Token *expect_t(P *p, TokType t, const char *msg);
```

다섯 함수가 파서의 알파벳이다.

### 13.2 좋은 에러 메시지

```c
static Token *expect_t(P *p, TokType t, const char *msg) {
    if (!check(p, t)) die("파서 오류: %s 가 필요한데 %s 를 만났습니다 (line %d)",
                          msg, tok_name(cur(p)->type), cur(p)->line);
    return advance_t(p);
}
```

“기대했던 것 + 만난 것 + 라인 번호”가 항상 함께 나오도록 한다.

### 13.3 BNF → 함수 매핑

| BNF | C 함수 |
|---|---|
| `<expr>` | `parse_expr` |
| `<add-expr>` | `parse_binop(8)` |
| `<atom>` | `parse_atom` |
| `<if>` | `parse_if` |
| `<for>` | `parse_for` |

이 매핑이 코드의 골격이다. 함수 이름이 곧 BNF 비단말의 이름이다.

---

## 14장. 표현식 파서 — Pratt(precedence climbing)

### 14.1 한 함수로 모든 우선순위 처리

```c
static AstNode *parse_binop(P *p, int min_prec) {
    AstNode *left = parse_unary(p);
    while (1) {
        const char *op; int prec;
        if (!peek_binop(p, &op, &prec) || prec < min_prec) break;
        advance_t(p);
        int next_min = is_left_assoc(op) ? prec + 1 : prec;
        AstNode *right = parse_binop(p, next_min);
        AstNode *bin = ast_new(A_BINOP);
        bin->s1 = xstrdup(op);
        bin->a = left; bin->b = right;
        left = bin;
    }
    return left;
}
```

핵심:

- `prec < min_prec`이면 더 약한 연산자가 와서 외부 호출자에게 반환한다.
- `next_min = prec + 1` (좌결합) 또는 `prec` (우결합).

### 14.2 우선순위 표

```c
static int peek_binop(P *p, const char **op_out, int *prec_out) {
    Token *t = cur(p);
    switch (t->type) {
        case T_PLUS:      *op_out="+";  *prec_out=8;  return 1;
        case T_MINUS:     *op_out="-";  *prec_out=8;  return 1;
        case T_STAR:      *op_out="*";  *prec_out=11; return 1;
        case T_SLASH:     *op_out="/";  *prec_out=11; return 1;
        case T_BACKSLASH: *op_out="\\"; *prec_out=10; return 1;
        case T_CARET:     *op_out="^";  *prec_out=13; return 1;
        case T_EQ:        *op_out="=";  *prec_out=7;  return 1;
        case T_NE:        *op_out="<>"; *prec_out=7;  return 1;
        case T_LT:        *op_out="<";  *prec_out=7;  return 1;
        case T_GT:        *op_out=">";  *prec_out=7;  return 1;
        case T_LE:        *op_out="<="; *prec_out=7;  return 1;
        case T_GE:        *op_out=">="; *prec_out=7;  return 1;
        case T_KEYWORD:
            if (str_ieq(t->text,"AND")) { *op_out="AND"; *prec_out=5;  return 1; }
            if (str_ieq(t->text,"OR"))  { *op_out="OR";  *prec_out=4;  return 1; }
            if (str_ieq(t->text,"XOR")) { *op_out="XOR"; *prec_out=3;  return 1; }
            if (str_ieq(t->text,"EQV")) { *op_out="EQV"; *prec_out=2;  return 1; }
            if (str_ieq(t->text,"IMP")) { *op_out="IMP"; *prec_out=1;  return 1; }
            if (str_ieq(t->text,"MOD")) { *op_out="MOD"; *prec_out=9;  return 1; }
            return 0;
        default: return 0;
    }
}
```

### 14.3 단항과 거듭제곱

```c
static AstNode *parse_unary(P *p) {
    if (accept_t(p, T_MINUS)) { /* unary minus */ ... }
    if (accept_t(p, T_PLUS))  return parse_unary(p);
    if (accept_kw(p, "NOT"))  { /* unary NOT */ ... }
    AstNode *base = parse_atom(p);
    if (check(p, T_CARET)) {
        advance_t(p);
        AstNode *exp = parse_unary(p);   /* 우결합 */
        AstNode *bin = ast_new(A_BINOP);
        bin->s1 = xstrdup("^");
        bin->a = base; bin->b = exp;
        return bin;
    }
    return base;
}
```

### 14.4 atom — 가장 흥미로운 분기

```c
static AstNode *parse_atom(P *p) {
    Token *t = cur(p);
    if (t->type == T_NUMBER) { /* NumLit */ }
    if (t->type == T_STRING) { /* StrLit */ }
    if (t->type == T_LPAREN) { /* group */ }
    if (t->type == T_KEYWORD && str_ieq(t->text, "FN")) { /* FN xxx(...) */ }
    if (t->type == T_IDENT) {
        char *name = xstrdup(t->text);
        advance_t(p);
        if (check(p, T_LPAREN)) {
            advance_t(p);
            AstNode *n;
            if (strncmp(name, "FN", 2) == 0) n = ast_new(A_FNCALL);
            else                              n = ast_new(A_CALL);
            n->s1 = name;
            /* args */
            return n;
        }
        AstNode *n = ast_new(A_VAR);
        n->s1 = name;
        return n;
    }
    die("예상치 못한 토큰...");
}
```

### 14.5 “FN으로 시작하면 사용자 함수”의 결정

이 한 줄이 GW-BASIC 의 DEF FN 처리의 본질이다. 식별자의 처음 두 글자가 `FN`이면 사용자 함수, 아니면 변수/배열/내장. 컴파일러가 같은 규칙을 다시 한 번 적용해서 `A_CALL`을 “내장이면 CALLF, 아니면 ALOAD(배열 인덱스)”로 분기한다.

---

## 15장. 문장 파서, 라인 번호, IF/FOR/ON GOTO

### 15.1 라인과 문장 목록

```c
static AstNode *parse_line(P *p) {
    AstNode *l = ast_new(A_LINE);
    if (check(p, T_NUMBER)) { l->i1 = (int)advance_t(p)->num; l->i2 = 1; }
    l->list1 = parse_stmt_list(p);
    if (check(p, T_EOL)) advance_t(p);
    return l;
}
```

### 15.2 IF 의 3형태

GW-BASIC IF는 다음 셋을 모두 받는다.

```basic
IF X > 0 THEN 100              ' 단순 GOTO
IF X > 0 GOTO 100              ' GOTO 단축 표기
IF X > 0 THEN PRINT X : Y = 1 ELSE PRINT 0
```

```c
static AstList parse_then_branch(P *p) {
    AstList out; vec_init(&out);
    if (check(p, T_NUMBER)) {
        AstNode *g = ast_new(A_GOTO);
        g->i1 = (int)advance_t(p)->num;
        vec_push(AstNode*, &out, g);
        return out;
    }
    while (1) {
        AstNode *s = parse_stmt(p);
        if (s) vec_push(AstNode*, &out, s);
        if (!accept_t(p, T_COLON)) break;
        if (check(p, T_EOL) || check(p, T_EOF) || check_kw(p, "ELSE")) break;
    }
    return out;
}
```

THEN 다음에 라인 번호 단독이면 GOTO로 변환. 그 외엔 콜론으로 이어진 문장 목록.

### 15.3 FOR / NEXT

`AstNode *parse_for(P *p)`는 평범하게 “IDENT = expr TO expr (STEP expr)”을 읽는다. 핵심은 `i1` 플래그로 “STEP이 있는가”를 표시하는 것뿐이다.

`parse_next`는 변수 이름이 옵션인 까다로움이 있다(`NEXT`, `NEXT I`, `NEXT I, J` 모두 합법).

### 15.4 ON GOTO / ON GOSUB

```c
static AstNode *parse_on(P *p) {
    AstNode *n = ast_new(A_ONJMP);
    n->a = parse_expr(p);
    if (accept_kw(p, "GOTO")) n->s2 = xstrdup("JMP");
    else if (accept_kw(p, "GOSUB")) n->s2 = xstrdup("GOSUB");
    else die("ON 다음에 GOTO 또는 GOSUB가 필요");
    Token *t1 = expect_t(p, T_NUMBER, "라인 번호");
    vec_push(int, &n->ilist, (int)t1->num);
    while (accept_t(p, T_COMMA)) {
        Token *t2 = expect_t(p, T_NUMBER, "라인 번호");
        vec_push(int, &n->ilist, (int)t2->num);
    }
    return n;
}
```

라인 번호 목록은 `IntList`로 보관. 컴파일러가 `OP_ONJMP` 한 명령에 “라인 배열을 그대로 박아 넣는다”.

### 15.5 DEF FN의 두 가지 형태

```basic
DEF FNSQR(X) = X*X
DEF FN SQR(X) = X*X
```

파서는 둘을 모두 받아 `s1 = "FNSQR"`로 저장한다. 호출 시점에 동일한 키로 조회되도록 통일.

```c
if (accept_kw(p, "FN")) {
    Token *id = expect_t(p, T_IDENT, "함수 이름");
    n->s1 = xmalloc(strlen(id->text)+3);
    snprintf(n->s1, strlen(id->text)+3, "FN%s", id->text);
} else if (check(p, T_IDENT)) {
    Token *id = advance_t(p);
    if (strncmp(id->text, "FN", 2) != 0) die("DEF FN 형식");
    n->s1 = xstrdup(id->text);
}
```

---

# 제5부 — AST와 컴파일러

## 16장. AST 노드 — 한 구조체에 모두 담기

### 16.1 설계 결정

C에는 합집합 타입(sum type)이 없다. 우리가 가진 두 가지 옵션은:

1. **태그된 공용체**: `enum Tag` + `union { struct Let; struct If; ... }`
2. **공통 슬롯**: 한 구조체에 모든 가능한 필드를 깔아 두고, tag별로 의미를 다르게.

Lua판은 1번 스타일에 가까웠지만(테이블이라 자유로움), C에서는 2번이 압도적으로 단순했다. 메모리는 약간 낭비되지만(노드 한 개 ~120바이트) 코드의 일관성이 큰 이득이다.

### 16.2 우리의 AstNode

```c
struct AstNode {
    AstTag tag;
    int    line_no;
    char   *s1, *s2;       /* 이름, op, prompt … */
    double  d1;            /* numlit value */
    int     i1, i2;        /* line target / has-flag / count … */
    AstNode *a, *b, *c;    /* 자식 (left/right/cond …) */
    AstList list1, list2;  /* 자식 리스트들 (then/else 등) */
    StrList slist;         /* 매개변수 등 */
    IntList ilist;         /* ON GOTO targets */
    DataList dlist;        /* DATA 항목들 */
    DimDeclList dimlist;   /* DIM 선언들 */
};
```

### 16.3 노드 카탈로그 (요약)

| 태그 | 사용하는 슬롯 |
|---|---|
| A_NUMLIT | d1 |
| A_STRLIT | s1 |
| A_VAR | s1, i1(has_indices), list1(인덱스) |
| A_BINOP | s1(op), a(left), b(right) |
| A_UNOP | s1(op), a |
| A_CALL | s1(name), list1(args) |
| A_FNCALL | s1(name), list1(args) |
| A_LET | a(target var), b(expr) |
| A_PRINT | list1(items) |
| A_INPUT | s1(prompt), list1(vars) |
| A_IF | a(cond), list1(then), list2(else), i1(has_else) |
| A_FOR | s1(var), a(start), b(stop), c(step), i1(has_step) |
| A_NEXT | slist(vars) |
| A_GOTO/A_GOSUB | i1(line) |
| A_DIM | dimlist |
| A_DATA | dlist |
| A_READ | list1(vars) |
| A_RESTORE | i1(line), i2(has_target) |
| A_DEFFN | s1(name), slist(params), a(body) |
| A_ONJMP | a(expr), s2(kind), ilist(targets) |
| A_PRINT_EXPR | a(expr) |
| A_PRINT_SEP | i1(',', ';') |
| A_PRINT_TAB / SPC | a(expr) |

### 16.4 ast_free의 일관성

```c
void ast_free(AstNode *n) {
    if (!n) return;
    free(n->s1); free(n->s2);
    if (n->a) ast_free(n->a);
    if (n->b) ast_free(n->b);
    if (n->c) ast_free(n->c);
    for (int i = 0; i < n->list1.len; ++i) ast_free(n->list1.data[i]);
    vec_free(&n->list1);
    /* ... 동일하게 list2, slist, ilist, dlist, dimlist 모두 ... */
    free(n);
}
```

“공통 슬롯” 설계의 장점은 ast_free가 단 하나라는 점이다. 슬롯이 비어 있으면 그냥 NULL/0이라 NOP이다.

---

## 17장. 바이트코드 명령어 집합

### 17.1 명령어 카탈로그 (Lua판과 동일)

```
[ 상수/변수 ]   PUSHN, PUSHS, LOAD, STORE, POP
[ 배열 ]        DIM, ALOAD, ASTORE
[ 산술 ]        ADD, SUB, MUL, DIV, IDIV, MOD, POW, NEG
[ 비교 ]        EQ, NE, LT, GT, LE, GE
[ 논리/비트 ]   AND, OR, XOR, EQV, IMP, NOT
[ 점프 ]        JMP, JZ, JNZ, GOSUB, RETURN, ONJMP
[ 입출력 ]      PRINT_ITEM, PRINT_NL, PRINT_TAB, PRINT_TAB_TO, PRINT_SPC, INPUT, CLS
[ 데이터 ]      READ, READ_A, RESTORE
[ 함수 ]        CALLF (내장), CALLU (사용자)
[ 종료 ]        HALT
```

총 47개. Lua판과 정확히 동일.

### 17.2 Inst 구조체

```c
typedef struct {
    OpCode op;
    int    iarg;     /* int 인자 (jump 주소, ndims, line, …) */
    int    iarg2;    /* 두번째 int (CALL argc, ON kind …) */
    double narg;     /* PUSHN */
    char  *sarg;     /* PUSHS, LOAD, STORE, CALLF 이름, INPUT prompt — 소유 */
    char  *sarg2;    /* INPUT 변수명 — 소유 */
    int   *ilist;    /* ONJMP 라인 배열 — 소유 (NULL 가능) */
    int    ilist_len;
} Inst;
```

각 명령은 36~48바이트. 1만 줄짜리 BASIC 프로그램의 바이트코드도 메모리 부담이 미미하다.

### 17.3 Bytecode 묶음

```c
typedef struct {
    InstList     ops;
    LineMap      line_addr;       /* BASIC 라인번호 → ops 주소 */
    LineDataMap  data_line_addr;  /* BASIC 라인번호 → data 인덱스 */
    DataList     data;            /* 평탄화된 DATA 항목 */
    FnList       fns;             /* DEF FN 등록표 */
} Bytecode;
```

Bytecode는 컴파일러의 출력이자 VM의 입력이다. 모든 메모리는 `bytecode_free`가 일괄 해제한다.

### 17.4 스택 효과 (요약)

| 명령 | 입력 → 출력 |
|---|---|
| PUSHN/PUSHS | () → (v) |
| LOAD | () → (v) |
| STORE | (v) → () |
| ADD/SUB/MUL/...| (a,b) → (a⋆b) |
| ALOAD ndims | (i1..in) → (v) |
| ASTORE ndims | (i1..in,v) → () |
| JZ/JNZ | (cond) → () |
| GOSUB/RETURN | () → () (call_stack 만 변경) |
| PRINT_ITEM | (v) → () |
| CALLF/CALLU n | (a1..an) → (v) |

---

## 18장. 표현식 컴파일과 후위 순회

### 18.1 일반 패턴

```c
static void compile_expr(C *c, AstNode *e) {
    switch (e->tag) {
    case A_NUMLIT: c_emit_n(c, OP_PUSHN, e->d1); return;
    case A_STRLIT: c_emit_s(c, OP_PUSHS, e->s1); return;
    case A_VAR:    /* LOAD or ALOAD */ return;
    case A_BINOP:
        compile_expr(c, e->a);
        compile_expr(c, e->b);
        c_emit(c, op_for(e->s1));
        return;
    case A_UNOP:
        compile_expr(c, e->a);
        c_emit(c, e->s1[0] == '-' ? OP_NEG : OP_NOT);
        return;
    case A_CALL:
        for (int i = 0; i < e->list1.len; ++i) compile_expr(c, e->list1.data[i]);
        if (runtime_is_builtin(e->s1)) c_emit_si2(c, OP_CALLF, e->s1, 0, e->list1.len);
        else                            c_emit_si(c, OP_ALOAD, e->s1, e->list1.len);
        return;
    case A_FNCALL:
        for (int i = 0; i < e->list1.len; ++i) compile_expr(c, e->list1.data[i]);
        c_emit_si2(c, OP_CALLU, e->s1, 0, e->list1.len);
        return;
    }
}
```

후위 순회: 자식 먼저, 자기 자신 나중. 자식의 결과가 스택에 쌓인 뒤 자기 연산이 그것을 소비한다.

### 18.2 op 매핑 표

```c
const char *op = e->s1;
OpCode oc =
    !strcmp(op,"+")   ? OP_ADD  :
    !strcmp(op,"-")   ? OP_SUB  :
    !strcmp(op,"*")   ? OP_MUL  :
    !strcmp(op,"/")   ? OP_DIV  :
    !strcmp(op,"\\")  ? OP_IDIV :
    !strcmp(op,"^")   ? OP_POW  :
    !strcmp(op,"MOD") ? OP_MOD  :
    !strcmp(op,"=")   ? OP_EQ   :
    /* ... 등 ... */
    OP_HALT;  /* fallback (실패 표시) */
if (oc == OP_HALT) die("Unknown op: %s", op);
c_emit(c, oc);
```

C에는 문자열 → 열거형의 자동 매핑이 없으니 if-else 사다리가 가장 솔직하다. 가독성을 위해 삼항 연산자로 한 줄씩 정렬할 수도 있다.

### 18.3 단축 평가는 없다

GW-BASIC의 `AND/OR`은 비트 연산이지 단축 평가가 아니다. 그러므로 양 자식을 모두 컴파일하고 명령 한 줄을 emit하면 끝이다.

```c
compile_expr(c, e->a);   /* 무조건 평가 */
compile_expr(c, e->b);   /* 무조건 평가 */
c_emit(c, OP_AND);
```

다른 언어의 `&&/||`처럼 “왼쪽이 false면 오른쪽 평가 생략”은 BASIC에 없다.

### 18.4 PRINT 항목 컴파일

```c
case A_PRINT: {
    bool last_was_sep = false;
    for (int i = 0; i < s->list1.len; ++i) {
        AstNode *it = s->list1.data[i];
        if (it->tag == A_PRINT_EXPR) {
            compile_expr(c, it->a);
            c_emit(c, OP_PRINT_ITEM);
            last_was_sep = false;
        } else if (it->tag == A_PRINT_SEP) {
            if (it->i1 == ',') c_emit(c, OP_PRINT_TAB);
            last_was_sep = true;
        } else if (it->tag == A_PRINT_TAB) {
            compile_expr(c, it->a); c_emit(c, OP_PRINT_TAB_TO); last_was_sep = true;
        } else if (it->tag == A_PRINT_SPC) {
            compile_expr(c, it->a); c_emit(c, OP_PRINT_SPC);    last_was_sep = true;
        }
    }
    if (!last_was_sep) c_emit(c, OP_PRINT_NL);
}
```

마지막 항목이 분리자(`,` 또는 `;`)이면 줄바꿈을 emit하지 않는다. GW-BASIC의 표준 동작이다.

---

## 19장. 백패치, 라인 매핑, FOR/WHILE 스택

### 19.1 두 종류의 점프

- **선행 점프**: IF/WHILE의 조건 거짓 → 끝으로. 끝 주소를 아직 모른다.
- **후방 점프**: FOR/WHILE의 루프 처음으로. 시작 주소를 이미 안다.

선행은 백패치, 후방은 즉시. 우리는 두 개의 스택을 컴파일러 안에 둔다.

```c
typedef VEC(ForFrame)   ForStack;
typedef VEC(WhileFrame) WhileStack;
```

### 19.2 IF 컴파일

```c
case A_IF: {
    compile_expr(c, s->a);
    int jz = c_emit_i(c, OP_JZ, 0);   /* 미지의 끝 주소 */
    for (int i = 0; i < s->list1.len; ++i) compile_stmt(c, s->list1.data[i]);
    if (s->i1) {
        int jmp_end = c_emit_i(c, OP_JMP, 0);
        c_patch(c, jz, c_addr(c));
        for (int i = 0; i < s->list2.len; ++i) compile_stmt(c, s->list2.data[i]);
        c_patch(c, jmp_end, c_addr(c));
    } else {
        c_patch(c, jz, c_addr(c));
    }
}
```

`c_emit_i`는 emit한 주소를 반환한다. 그 주소를 잡아 두고, 분기의 끝이 정해질 때 `c_patch`로 채운다.

### 19.3 FOR 컴파일

```c
compile_expr(c, s->a); c_emit_s(c, OP_STORE, s->s1);
compile_expr(c, s->b); c_emit_s(c, OP_STORE, "__LIMIT_<v>");
if (s->i1) compile_expr(c, s->c); else c_emit_n(c, OP_PUSHN, 1.0);
c_emit_s(c, OP_STORE, "__STEP_<v>");
int top = c_addr(c);
/* step * (i - limit) <= 0 이면 계속 */
c_emit_s(c, OP_LOAD, "__STEP_<v>");
c_emit_s(c, OP_LOAD, "<v>");
c_emit_s(c, OP_LOAD, "__LIMIT_<v>");
c_emit(c, OP_SUB); c_emit(c, OP_MUL);
c_emit_n(c, OP_PUSHN, 0); c_emit(c, OP_LE);
int jz = c_emit_i(c, OP_JZ, 0);
push_for_frame({var, top, jz});
```

종료식 `step * (i - limit) <= 0`은 부호와 무관하게 동작한다.

- step > 0: i ≤ limit ↔ step·(i-limit) ≤ 0
- step < 0: i ≥ limit ↔ step·(i-limit) ≤ 0

NEXT는 위 frame을 꺼내 “i = i + step; jmp top; patch jz”를 emit한다.

### 19.4 라인 번호 → 주소

```c
for (int i = 0; i < program->list1.len; ++i) {
    AstNode *line = program->list1.data[i];
    if (line->i2) {
        LineAddr la = { line->i1, c_addr(&ctx) };
        vec_push(LineAddr, &bc->line_addr, la);
        LineDataAddr lda = { line->i1, bc->data.len + 1 };
        vec_push(LineDataAddr, &bc->data_line_addr, lda);
    }
    for (int j = 0; j < line->list1.len; ++j) compile_stmt(&ctx, line->list1.data[j]);
}
```

각 라인의 시작 주소를 `line_addr`에 기록. 미래의 라인을 가리키는 GOTO/GOSUB은 “보류 목록”에 적어 두고, 모든 라인이 컴파일된 뒤 일괄 백패치.

```c
for (int i = 0; i < ctx.pending.len; ++i) {
    PendingJump pj = ctx.pending.data[i];
    int target = -1;
    for (int j = 0; j < bc->line_addr.len; ++j)
        if (bc->line_addr.data[j].line == pj.line) { target = bc->line_addr.data[j].addr; break; }
    if (target < 0) die("Undefined line %d", pj.line);
    bc->ops.data[pj.addr - 1].iarg = target;
}
```

선형 검색이지만 라인 수가 많지 않으므로 충분히 빠르다(필요 시 정렬+이분 검색).

---

# 제6부 — 가상 머신

## 20장. VM 상태와 메인 디스패치 루프

### 20.1 VM 구조체

```c
typedef struct VM {
    Bytecode *bc;
    int       ip;
    Value    *stack;
    int       stack_top, stack_cap;
    VEC(int)  call_stack;
    VarMap    vars;
    ArrMap    arrays;
    int       data_ptr;
    int       print_col;
    int       zone_width;
    int       line_width;
    bool      halted;

    void   (*output)(const char *s);     /* NULL = stdio */
    char  *(*input) (const char *prompt);
} VM;
```

이 구조체 하나로 GW-BASIC 프로그램을 돌리기에 충분하다.

### 20.2 스택은 동적 배열

```c
static void push_v(VM *vm, Value v) {
    if (vm->stack_top == vm->stack_cap) {
        vm->stack_cap = vm->stack_cap ? vm->stack_cap * 2 : 64;
        vm->stack = (Value*)xrealloc(vm->stack, sizeof(Value) * vm->stack_cap);
    }
    vm->stack[vm->stack_top++] = v;
}
```

값 한 개에 24바이트, 깊이 64면 1.5KB로 시작. 거의 모든 BASIC 프로그램에서 깊이가 10을 넘지 않는다.

### 20.3 메인 루프

```c
void vm_run(VM *vm) {
    Bytecode *bc = vm->bc;
    while (!vm->halted && vm->ip <= bc->ops.len) {
        Inst *op = &bc->ops.data[vm->ip - 1];
        vm->ip++;
        switch (op->op) {
        case OP_HALT:  vm->halted = true; break;
        case OP_PUSHN: push_v(vm, v_num(op->narg)); break;
        case OP_PUSHS: push_v(vm, v_str_copy(op->sarg ? op->sarg : "")); break;
        case OP_LOAD:  push_v(vm, get_var(vm, op->sarg)); break;
        case OP_STORE: { Value v = pop_v(vm); set_var(vm, op->sarg, v); break; }
        /* ... 모든 명령들 ... */
        }
    }
}
```

거대한 switch가 익숙하지 않다면 처음에 부담스럽지만, 실제로 “모든 명령이 한곳에 있다”는 점이 디버깅에 매우 유리하다. 디스패치 비용도 함수 포인터 테이블보다 낫다(보통).

### 20.4 “명령 실행 전 ip 증가”의 약속

핸들러 진입 *전에* `ip`를 +1 한다. 이로써 GOSUB는 “현재 ip를 그대로 저장”하면 곧 “다음 명령 주소”를 저장하는 것이 된다.

```c
case OP_GOSUB:
    vec_push(int, &vm->call_stack, vm->ip);
    vm->ip = op->iarg;
    break;
```

JMP는 더 단순하다.

```c
case OP_JMP: vm->ip = op->iarg; break;
case OP_JZ:  { Value v = pop_v(vm); if (!v_truthy(v)) vm->ip = op->iarg; v_release(&v); break; }
```

### 20.5 비트 연산

GW-BASIC은 AND/OR/XOR/NOT을 32비트 정수 비트연산으로 정의한다. 우리 구현은 `long`(보통 32 또는 64비트)으로 한다.

```c
static long band_l(long a, long b) { return a & b; }
static long bor_l (long a, long b) { return a | b; }
static long bxor_l(long a, long b) { return a ^ b; }
static long bnot_l(long a) { return ~a; }
static long to_long(Value v) { return (long)v_to_num(v); }
```

비교 결과의 BASIC 표현(참=−1, 거짓=0)도 이 비트 연산과 어울린다(−1은 0xFF…F).

---

## 21장. 변수 환경과 동적 슬롯

### 21.1 단순한 환경

GW-BASIC은 일반적으로 “전역 변수만” 가진다. DEF FN의 매개변수만 호출 동안 임시로 그림자(shadow)할 뿐. 그래서 우리 환경은 평면 배열이다.

```c
typedef struct { char *name; Value value; } VarSlot;
typedef VEC(VarSlot) VarMap;
```

### 21.2 선형 검색? 해시?

변수 수가 작으므로 선형 검색이 충분하다.

```c
static int find_var(VM *vm, const char *name) {
    for (int i = 0; i < vm->vars.len; ++i)
        if (strcmp(vm->vars.data[i].name, name) == 0) return i;
    return -1;
}
```

수백 개의 변수가 도는 BASIC 프로그램은 드물다. 1000개 넘어가면 해시 테이블로 바꿀 만하지만, 그때쯤이면 “BASIC”이 아니라 “큰 시스템”이다.

### 21.3 미정의 변수의 기본값

```c
static Value get_var(VM *vm, const char *name) {
    int i = find_var(vm, name);
    if (i < 0) {
        if (var_kind(name) == 's') return v_str_copy("");
        return v_num(0);
    }
    return v_clone(vm->vars.data[i].value);
}
```

“정의되지 않은 변수에 접근하면 기본값”이 BASIC의 약속이다. 에러를 띄우지 않는다.

### 21.4 set_var의 한 패턴

```c
static void set_var(VM *vm, const char *name, Value v) {
    v = coerce_for_var(name, v);
    int i = find_var(vm, name);
    if (i < 0) {
        VarSlot s = { xstrdup(name), v };
        vec_push(VarSlot, &vm->vars, s);
    } else {
        v_release(&vm->vars.data[i].value);
        vm->vars.data[i].value = v;
    }
}
```

기존 슬롯이 있으면 release 후 덮어쓰기. 없으면 새 슬롯.

### 21.5 DEF FN의 매개변수 그림자

DEF FN 호출 시점에는 매개변수가 일시적으로 변수와 같은 이름의 슬롯을 차지해야 한다. 우리는 “저장 → 설정 → 평가 → 복원” 패턴을 쓴다.

```c
Value *saved = xmalloc(sizeof(Value) * fn->params.len);
bool *had = xmalloc(sizeof(bool) * fn->params.len);
for (int i = 0; i < fn->params.len; ++i) {
    int vi = find_var(vm, fn->params.data[i]);
    had[i] = (vi >= 0);
    saved[i] = had[i] ? v_clone(vm->vars.data[vi].value) : v_num(0);
    set_var(vm, fn->params.data[i], v_clone(args[i]));
}
Value r = vm_eval_expr_ast(vm, fn->body);
/* 복원 */
for (int i = 0; i < fn->params.len; ++i) {
    if (had[i]) set_var(vm, fn->params.data[i], saved[i]);
    else { /* 새로 추가된 슬롯이면 제거 */ }
}
```

이 패턴이 재귀 호출에서도 동작한다(saved/had가 호출 프레임마다 따로 할당되므로).

---

## 22장. GOSUB / RETURN 호출 스택

### 22.1 의미

GOSUB은 “지금 위치를 기억하고 라인 N으로 점프”다. RETURN은 “마지막 GOSUB이 기억해 둔 위치로 돌아가기”다.

### 22.2 구현

```c
VEC(int) call_stack;

case OP_GOSUB:
    vec_push(int, &vm->call_stack, vm->ip);   /* 다음 명령 주소 */
    vm->ip = op->iarg;
    break;
case OP_RETURN:
    if (vm->call_stack.len == 0) die("RETURN without GOSUB");
    vm->ip = vm->call_stack.data[--vm->call_stack.len];
    break;
```

이게 전부다. 스택이라는 자료구조가 “중첩 호출”을 자연스럽게 허용해 준다.

### 22.3 ON GOSUB

```c
case OP_ONJMP: {
    Value v = pop_v(vm);
    int n = (int)floor(v_to_num(v) + 0.5);
    v_release(&v);
    if (n < 1 || n > op->ilist_len) break;     /* 범위 밖이면 무시 */
    int target_line = op->ilist[n-1];
    int target_addr = find_line_addr(bc, target_line);
    if (target_addr < 0) die("Undefined line %d", target_line);
    if (op->sarg && strcmp(op->sarg, "GOSUB") == 0)
        vec_push(int, &vm->call_stack, vm->ip);
    vm->ip = target_addr;
    break;
}
```

ON 식의 값이 1, 2, 3...일 때 각각 첫 번째, 두 번째 라인으로. 0이거나 범위 밖이면 다음 문장으로 흘러간다. GW-BASIC의 표준.

---

## 23장. 다차원 배열의 평탄화와 자동 DIM

### 23.1 데이터 구조

```c
typedef struct {
    char *name;
    int  *dims;       /* 각 차원의 max */
    int   ndims;
    Value *data;      /* 평탄화된 1차원 배열 */
    int   data_size;
    char  kind;       /* 'n','s','i' */
} ArrSlot;
```

### 23.2 평탄화 인덱스

```c
static int linear_index(ArrSlot *a, int *idxs, int n) {
    if (n != a->ndims) die("배열 차원 수 불일치 (%s)", a->name);
    int idx = 0;
    for (int i = 0; i < n; ++i) {
        int k = idxs[i];
        if (k < 0 || k > a->dims[i])
            die("Subscript out of range (%s, %d)", a->name, k);
        idx = idx * (a->dims[i] + 1) + k;
    }
    return idx;
}
```

row-major 순서. `DIM A(3, 4)` → 차원 (0..3, 0..4) → 4×5 = 20칸.

### 23.3 DIM과 자동 DIM

```c
static int dim_array_internal(VM *vm, const char *name, int *dims, int n) { /* 위 참고 */ }

static int ensure_arr(VM *vm, const char *name, int ndims) {
    int i = find_arr(vm, name);
    if (i >= 0) return i;
    int *dims = xmalloc(sizeof(int) * ndims);
    for (int k = 0; k < ndims; ++k) dims[k] = 10;   /* 기본 0..10 */
    int idx = dim_array_internal(vm, name, dims, ndims);
    free(dims);
    return idx;
}
```

DIM 없이 처음 접근하면 자동으로 DIM 10. GW-BASIC의 표준 동작.

### 23.4 ALOAD / ASTORE

```c
case OP_ALOAD: {
    int n = op->iarg;
    int *idxs = xmalloc(sizeof(int)*n);
    for (int i = n-1; i >= 0; --i) {
        Value v = pop_v(vm);
        idxs[i] = (int)floor(v_to_num(v) + 0.5);
        v_release(&v);
    }
    int ai = ensure_arr(vm, op->sarg, n);
    ArrSlot *a = &vm->arrays.data[ai];
    int li = linear_index(a, idxs, n);
    free(idxs);
    push_v(vm, v_clone(a->data[li]));
    break;
}
```

스택에서 “인덱스 → 값” 순으로 push되어 있으므로 pop은 역순. `i = n-1; i--`로 idxs를 채워 둔다.

### 23.5 인덱스 0-base, 크기 dim+1

`DIM A(10)`은 인덱스 0~10, 총 11칸. `OPTION BASE 1`을 지원하려면 `arrays[i].base`라는 추가 필드가 필요하다. 우리는 항상 0-base.

---

# 제7부 — 런타임과 내장 함수

## 24장. PRINT의 의외로 깊은 세계

### 24.1 PRINT의 두 분리자

| 식 | 결과 (• = 공백) |
|---|---|
| `PRINT "A"; "B"` | `AB` 줄바꿈 |
| `PRINT "A", "B"` | `A•••••••••••••B` 줄바꿈 |
| `PRINT "A";` | `A` 줄바꿈 *없음* |
| `PRINT 3` | `•3•` 줄바꿈 |

### 24.2 컬럼 추적

```c
static void out_str(VM *vm, const char *s) {
    if (vm->output) vm->output(s);
    else fputs(s, stdout);
    for (const char *p = s; *p; ++p) {
        if (*p == '\n') vm->print_col = 0;
        else vm->print_col++;
    }
}
```

`print_col`은 “현재 줄에서 다음에 찍을 위치”다. `,`(콤마) 분리자는 이 값을 보고 다음 영역(zone, 기본 14컬럼)으로 이동.

### 24.3 PRINT_TAB / PRINT_TAB_TO

```c
static void do_print_tab(VM *vm) {
    int col = vm->print_col;
    int next_zone = (col / vm->zone_width) * vm->zone_width + vm->zone_width;
    if (next_zone >= vm->line_width) out_newline(vm);
    else {
        char *pad = xmalloc(next_zone - col + 1);
        memset(pad, ' ', next_zone - col); pad[next_zone - col] = 0;
        out_str(vm, pad); free(pad);
    }
}
```

- `,`(콤마): 다음 zone 으로
- `TAB(n)`: 컬럼 n으로 이동(이미 지나갔으면 새 줄)

### 24.4 “마지막 분리자가 있으면 줄바꿈 없음”

이 의미는 컴파일러가 처리한다. 마지막 항목이 분리자라면 PRINT_NL을 emit하지 않는다(18장 참고).

---

## 25장. INPUT, DATA, READ, RESTORE

### 25.1 INPUT 한 줄 받기

```c
case OP_INPUT: {
    const char *prompt = op->sarg ? op->sarg : "";
    const char *vname  = op->sarg2 ? op->sarg2 : "";
    char prbuf[256];
    snprintf(prbuf, sizeof(prbuf), "%s? ", prompt);
    char *line;
    if (vm->input) line = vm->input(prbuf);
    else { /* fgets에서 stdin 읽기 */ }
    if (var_kind(vname) == 's') set_var(vm, vname, v_str_take(line));
    else { double x = strtod(line, NULL); free(line); set_var(vm, vname, v_num(x)); }
}
```

### 25.2 DATA 컴파일 시 평탄화

```c
case A_DATA: {
    for (int i = 0; i < s->dlist.len; ++i) {
        DataItem it = s->dlist.data[i];
        DataItem copy; copy.kind = it.kind; copy.num = it.num;
        copy.str = it.str ? xstrdup(it.str) : NULL;
        vec_push(DataItem, &c->bc->data, copy);
    }
}
```

DATA 문장은 컴파일 시점에 명령을 emit하지 않는다. 그저 항목을 평탄화 배열에 추가할 뿐. 라인 번호별 시작 인덱스는 `data_line_addr`에 따로 저장(RESTORE에 쓰임).

### 25.3 READ / RESTORE

```c
case OP_READ: {
    if (vm->data_ptr > bc->data.len) die("Out of DATA");
    DataItem it = bc->data.data[vm->data_ptr - 1];
    vm->data_ptr++;
    /* 변수 타입에 따라 set_var */
    break;
}
case OP_RESTORE: {
    int line = op->iarg;
    if (line < 0) vm->data_ptr = 1;
    else { /* data_line_addr 에서 라인 인덱스 찾기 */ }
}
```

---

## 26장. 수학·문자열 내장 함수 카탈로그

### 26.1 함수 등록

```c
static const Builtin BUILTINS[] = {
    {"ABS",     bi_abs,    1, 1},
    {"SGN",     bi_sgn,    1, 1},
    /* ... 약 30개 ... */
    {NULL, NULL, 0, 0}
};
```

NULL 종결 배열. `runtime_find`가 선형 검색.

### 26.2 함수 시그니처

```c
typedef Value (*BuiltinFn)(struct VM *vm, Value *args, int nargs);
```

VM 포인터를 받지만 대부분의 함수는 무시한다(`(void)vm`). `args`는 위치 인자 배열(이미 평가된 Value들), 반환은 새 Value(호출자 소유).

### 26.3 수학 함수 카탈로그

| 함수 | 의미 |
|---|---|
| ABS, SGN, INT, FIX | 절댓값/부호/내림/0방향 절단 |
| SQR, EXP, LOG | 제곱근, 지수, 자연로그 |
| SIN, COS, TAN, ATN | 삼각/역탄젠트 |
| RND | 0~1 난수 |

### 26.4 문자열 함수 카탈로그

| 함수 | 의미 |
|---|---|
| LEN, LEFT$, RIGHT$, MID$ | 길이/부분 |
| CHR$, ASC | 코드 ↔ 문자 |
| STR$, VAL | 숫자 ↔ 문자열 |
| SPACE$, STRING$ | 공백/반복 |
| INSTR | 찾기 |
| UCASE$, LCASE$ | 대/소문자 |

### 26.5 시간 함수

| 함수 | 의미 |
|---|---|
| TIMER | 시스템 시간(초) |
| DATE$ | "MM-DD-YYYY" |
| TIME$ | "HH:MM:SS" |

### 26.6 새 함수 추가하기

`runtime.c`의 `BUILTINS[]`에 한 줄 추가하고 함수를 정의하면 끝.

```c
static Value bi_hex(struct VM *vm, Value *a, int n) {
    (void)vm; (void)n;
    char buf[32];
    snprintf(buf, sizeof(buf), "%lX", (long)v_to_num(a[0]));
    return v_str_copy(buf);
}
/* BUILTINS 에 {"HEX$", bi_hex, 1, 1} 추가 */
```

---

## 27장. DEF FN과 사용자 정의 함수

### 27.1 등록

```c
case A_DEFFN: {
    FnDef f;
    f.name = xstrdup(s->s1);
    vec_init(&f.params);
    for (int i = 0; i < s->slist.len; ++i)
        vec_push(char*, &f.params, xstrdup(s->slist.data[i]));
    f.body = s->a;   /* AST 그대로 차용 (Program 이 소유) */
    vec_push(FnDef, &c->bc->fns, f);
    break;
}
```

DEF FN은 바이트코드에 명령을 emit하지 않는다. 컴파일 시점에 그저 등록될 뿐.

### 27.2 호출

`OP_CALLU` 핸들러는 매개변수 그림자 → 본문 식 평가 → 복원의 패턴을 따른다(21.5절 참고).

본문은 AST로 그대로 두고 `vm_eval_expr_ast`로 즉석 평가한다. 한 줄짜리 식이라는 본질을 살리면 즉석 평가가 가장 단순하다.

### 27.3 재귀

매개변수 그림자가 호출 프레임마다 따로 할당되므로 재귀가 자연스럽게 동작한다.

```basic
10 DEF FNG(N) = (N <= 1) * 1 + (N > 1) * N * FNG(N-1)
```

(주의: BASIC식 비교는 −1/0이므로 부호 보정이 필요할 수 있다. 정확한 팩토리얼은 IF로 별도 라인을 쓰거나, GOSUB 패턴을 쓰는 편이 분명하다.)

---

# 제8부 — 통합과 마무리

## 28장. REPL 만들기

### 28.1 REPL의 책임

- 라인 번호로 시작 → 누적
- 즉시 실행 → 한 줄만 컴파일/실행
- `RUN` → 누적된 텍스트 컴파일/실행
- `LIST` → 누적된 텍스트 출력
- `NEW` → 비우기

### 28.2 단순 구현

```c
static void repl(void) {
    fputs("CGW-BASIC 1.0  --  종료: BYE\n", stdout);
    char *prog = NULL; size_t plen = 0, pcap = 0;
    char line[1024];
    while (1) {
        fputs("Ok\n> ", stdout); fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) break;
        size_t L = strlen(line);
        while (L > 0 && (line[L-1] == '\n' || line[L-1] == '\r')) line[--L] = 0;
        if (L == 0) continue;
        if (str_ieq(line, "BYE")) break;
        if (str_ieq(line, "RUN"))      { if (prog) run_source(prog); }
        else if (str_ieq(line, "LIST")){ if (prog) fputs(prog, stdout); }
        else if (str_ieq(line, "NEW")) { free(prog); prog=NULL; plen=pcap=0; }
        else if (line[0] >= '0' && line[0] <= '9') {
            /* 라인 추가 */
        } else {
            /* 즉시 실행 */
        }
    }
    free(prog);
}
```

(전체 구현은 `src/main.c`에 있다. 부록 C 참고.)

### 28.3 라인 정렬

진짜 GW-BASIC은 라인이 추가될 때 라인 번호 순서로 정렬한다. 우리 단순 REPL은 입력 순서대로 보관한다. RUN 시점에 라인 번호 순으로 정렬해서 컴파일하면 더 충실해진다(연습 문제).

---

## 29장. fib.bas의 전 생애 추적

### 29.1 입력

```basic
10 N = 7
20 A = 0 : B = 1
30 FOR I = 2 TO N
40   C = A + B : A = B : B = C
50 NEXT I
60 PRINT B
70 END
```

기대 출력: `13`.

### 29.2 토큰

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

### 29.3 AST

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

### 29.4 바이트코드

(라인 매핑과 명령은 Lua판과 동일. 부록 B 참고.)

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
13 LOAD __STEP_I   ; 검사
14 LOAD I
15 LOAD __LIMIT_I
16 SUB; MUL; PUSHN 0; LE; JZ 32
17 LOAD A          ; 40: 본문
18 LOAD B
19 ADD
20 STORE C
21 LOAD B
22 STORE A
23 LOAD C
24 STORE B
25 LOAD I          ; 50: 증분
26 LOAD __STEP_I
27 ADD
28 STORE I
29 JMP 13
32 LOAD B          ; 60: PRINT B
33 PRINT_ITEM
34 PRINT_NL
35 HALT             ; 70: END
```

### 29.5 VM 트레이스 (요약)

| ip | op | 스택 변화 후 | vars |
|---:|---|---|---|
| 1 | PUSHN 7 | (7) | |
| 2 | STORE N | () | N=7 |
| 3 | PUSHN 0; STORE A | () | A=0 |
| 5 | PUSHN 1; STORE B | () | B=1 |
| 7 | PUSHN 2; STORE I | () | I=2 |
| 9~12 | (limit/step 설정) | () | __LIMIT_I=7, __STEP_I=1 |
| 13~16 | step·(i-limit) <= 0 | (-1) | (참=−1) |
| 17~24 | 본문 1회 | () | C=1, A=1, B=1 |
| ... | (6회 반복) | ... | ... |
| 32~34 | PRINT B | () | (출력 ` 13 \n`) |
| 35 | HALT | | 종료 |

### 29.6 추적을 켜고 직접 보자

`vm.c`의 `vm_run` 안에 한 줄 추가하면 위 표가 자동으로 만들어진다.

```c
fprintf(stderr, "[%d] %s arg=%d narg=%g sarg=%s\n",
    vm->ip, op_name(op->op), op->iarg, op->narg, op->sarg ? op->sarg : "");
```

---

## 30장. 흔한 함정과 디버깅 패턴

### 30.1 “스택이 비어 있는데 RETURN?”

`Error: RETURN without GOSUB`. 원인:

1. GOSUB 없이 RETURN 라인에 도달.
2. GOSUB 안에서 GOTO로 함수 밖으로 빠져나갔는데, 그 흐름이 RETURN을 만남.
3. ON GOSUB의 식의 값이 범위 밖이라 점프하지 않았는데, 라인이 그대로 흘러가다 RETURN.

대응: 컴파일 시 정적 추적은 하지 않는다. 런타임에 라인 번호와 함께 표시.

### 30.2 “Subscript out of range”

배열 인덱스가 차원 범위를 벗어났다. 자동 DIM의 기본값(10)에 익숙해진 코드가 11번째 칸을 쓰려 하는 경우가 가장 흔하다. 명시적인 `DIM A(N)`로 의도를 분명히 하자.

### 30.3 무한 FOR

`FOR I = 1 TO 10 STEP 0`은 무한 루프. `step·(i-limit) <= 0`이 항상 참이 된다. BASIC의 정의된 동작이지만 사용자 의도가 아닐 가능성이 크다.

### 30.4 “Type mismatch” 잡기

`A$ = 1`이나 `A = "X"`는 명시적 에러. 변수 이름의 접미어를 잘못 쓴 경우를 대부분 잡는다.

### 30.5 모듈별 디버깅 진입점

| 증상 | 들여다 볼 모듈 |
|---|---|
| 입력 자체가 안 읽힘 | `lexer.c` |
| 토큰은 맞는데 “파서 오류” | `parser.c` |
| 결과가 이상 | `vm.c`의 핸들러 |
| 라인 점프가 잘못 | `compiler.c`의 `pending_gotos`/`line_addr` |
| PRINT 포맷 어긋남 | `v_to_basic_string`, `do_print_tab` |

### 30.6 “바이트코드를 의심하라”

대부분 실수는 컴파일러에서 발생한다. 의심스러우면 디스어셈블 함수를 임시로 추가해 명령 시퀀스를 출력하자.

```c
void dump_bc(Bytecode *bc) {
    for (int i = 0; i < bc->ops.len; ++i) {
        Inst *o = &bc->ops.data[i];
        printf("%4d %-12s %-8s iarg=%d narg=%g\n",
            i+1, op_name(o->op), o->sarg ? o->sarg : "", o->iarg, o->narg);
    }
}
```

### 30.7 valgrind를 끼고 살자

```sh
$ valgrind --leak-check=full ./cgwbasic examples/sieve.bas
```

이 출력이 “definitely lost: 0 bytes”이라면 메모리 모델이 일관됨을 확인한 셈이다. 새 기능 추가 시 매번 한 번씩 돌리는 습관을 권한다.

---

## 31장. 연습 문제와 다음 단계

### 31.1 입문

1. ★ `'`를 REM 처럼 줄 끝까지 주석으로 동작하게 어휘 분석기를 고치라.
2. ★ `&H1F`(16진수)와 `&O17`(8진수) 리터럴을 인식하라.
3. ★ 이 책의 코드에 `--dump-tokens`, `--dump-ast`, `--dump-bc` 옵션을 추가하라.
4. ★ `?A`처럼 `?`로 시작하는 한 줄을 REPL이 즉시 실행으로 처리하는지 확인.

### 31.2 중급

5. ★★ DEF FN의 본문을 컴파일러가 “전용 라인”으로 컴파일하도록 바꾸어 보라(즉 일반 호출처럼 CALL 명령으로). 호출 규약을 정의하라.
6. ★★ ON ERROR GOTO / RESUME을 구현하라.
7. ★★ LINE INPUT (한 줄 통째로 받기) 추가.
8. ★★ WHILE 0 인 케이스가 의도대로 “들어가지도 않음”인지 테스트.

### 31.3 고급

9. ★★★ 컴파일 시 상수 폴딩(`1 + 2 * 3` → `7`).
10. ★★★ 변수 이름을 “슬롯 인덱스”로 컴파일하여 LOAD/STORE의 인자가 정수가 되도록.
11. ★★★ 토큰화된 .BAS(첫 바이트 0xFF) 디코더 → 평문 변환 → 우리 컴파일러로.
12. ★★★ ON ERROR GOTO 의 완전 구현. VM에 “현재 ip를 라인으로 매핑”하는 역방향 테이블을 둔다.

### 31.4 도전

13. ★★★★ 그래픽 명령(SCREEN, LINE, CIRCLE, PSET)을 SDL2 백엔드와 연결.
14. ★★★★ 우리 VM의 핸들러를 “computed goto”(GCC 확장)로 바꾸어 디스패치를 더 빠르게.
15. ★★★★ 우리 BASIC을 LLVM IR로 컴파일하는 백엔드를 추가.

### 31.5 작은 실용 과제

- 끝맺음 `Ok` 한 줄로 진짜 GW-BASIC 분위기 흉내내기
- REPL에서 같은 라인 번호 입력 → 대체/삭제 동작
- `SAVE "name.bas"`, `LOAD "name.bas"` 추가
- RUN 시점에 변수와 호출 스택을 비우는지 확인

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
              | <end> | <stop> | <rem> | <cls>
              | <dim> | <data> | <read> | <restore>
              | <def-fn> | <on-goto>

<let>     ::= ( "LET" )? <lvalue> "=" <expr>
<lvalue>  ::= <ident> ( "(" <expr> ( "," <expr> )* ")" )?
<print>   ::= "PRINT" <print-list>?
<print-list> ::= <print-item> ( <print-sep> <print-item>? )*
<print-item> ::= <expr> | "TAB" "(" <expr> ")" | "SPC" "(" <expr> ")"
<print-sep> ::= "," | ";"
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

| 명령 | iarg | iarg2 | narg | sarg / sarg2 | 스택 효과 |
|---|---|---|---|---|---|
| HALT | — | — | — | — | — |
| PUSHN | — | — | n | — | () → (n) |
| PUSHS | — | — | — | s | () → (s) |
| LOAD | — | — | — | name | () → (v) |
| STORE | — | — | — | name | (v) → () |
| POP | — | — | — | — | (v) → () |
| ALOAD | ndims | — | — | name | (i1..in) → (v) |
| ASTORE | ndims | — | — | name | (i1..in,v) → () |
| DIM | ndims | — | — | name | (d1..dn) → () |
| ADD/SUB/MUL/DIV/IDIV/MOD/POW | — | — | — | — | (a,b) → (r) |
| NEG | — | — | — | — | (a) → (-a) |
| EQ/NE/LT/GT/LE/GE | — | — | — | — | (a,b) → (-1/0) |
| AND/OR/XOR/EQV/IMP/NOT | — | — | — | — | 비트 |
| JMP | addr | — | — | — | () → () |
| JZ/JNZ | addr | — | — | — | (v) → () |
| GOSUB | addr | — | — | — | call_stack push |
| RETURN | — | — | — | — | call_stack pop |
| ONJMP | — | nlines | — | "JMP"\|"GOSUB" | (n) → ()  + ilist |
| PRINT_ITEM | — | — | — | — | (v) → () |
| PRINT_NL | — | — | — | — | () → () |
| PRINT_TAB | — | — | — | — | () → () |
| PRINT_TAB_TO | — | — | — | — | (n) → () |
| PRINT_SPC | — | — | — | — | (n) → () |
| INPUT | — | — | — | prompt / varname | () → () |
| READ | — | — | — | name | () → () |
| READ_A | ndims | — | — | name | (i1..in) → () |
| RESTORE | line/-1 | — | — | — | () → () |
| CALLF | — | argc | — | name | (a1..an) → (v) |
| CALLU | — | argc | — | name | (a1..an) → (v) |
| CLS | — | — | — | — | () → () |

---

## 부록 C — 전체 C 소스 코드

이 절은 9개 모듈 16개 파일의 전체 소스를 그대로 싣는다.

### C.1 src/common.h

```c
#ifndef COMMON_H
#define COMMON_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include <ctype.h>
#include <stdbool.h>

/* ───── 동적 배열(VEC) 매크로 ─────
 * 일반 타입에 대한 가변 배열. 임의의 T 에 대해 다음과 같이 사용한다.
 *   VEC(int) v; vec_init(&v); vec_push(int, &v, 7);
 */
#define VEC(T) struct { T *data; int len, cap; }
#define vec_init(v) do { (v)->data = NULL; (v)->len = 0; (v)->cap = 0; } while(0)
#define vec_grow(v, T) do { \
    if ((v)->len == (v)->cap) { \
        (v)->cap = (v)->cap ? (v)->cap * 2 : 8; \
        (v)->data = (T*)xrealloc((v)->data, sizeof(T) * (v)->cap); \
    } \
} while(0)
#define vec_push(T, v, x) do { vec_grow(v, T); (v)->data[(v)->len++] = (x); } while(0)
#define vec_free(v) do { free((v)->data); (v)->data=NULL; (v)->len=0; (v)->cap=0; } while(0)

/* ───── 메모리/문자열 ───── */
void  die(const char *fmt, ...) __attribute__((noreturn));
void *xmalloc(size_t n);
void *xrealloc(void *p, size_t n);
char *xstrdup(const char *s);
char *xstrndup(const char *s, size_t n);
char *str_upper(char *s);          /* 제자리에서 대문자화, 반환은 같은 포인터 */
char *str_upper_dup(const char *s);
int   str_ieq(const char *a, const char *b); /* 대소문자 무시 비교, 같으면 1 */

#endif

```

### C.2 src/common.c

```c
#include "common.h"

void die(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "fatal: ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
    exit(2);
}

void *xmalloc(size_t n) {
    void *p = malloc(n);
    if (!p) die("out of memory (%zu)", n);
    return p;
}

void *xrealloc(void *p, size_t n) {
    void *q = realloc(p, n);
    if (!q && n) die("out of memory (%zu)", n);
    return q;
}

char *xstrdup(const char *s) {
    if (!s) return NULL;
    size_t n = strlen(s);
    char *r = (char*)xmalloc(n + 1);
    memcpy(r, s, n + 1);
    return r;
}

char *xstrndup(const char *s, size_t n) {
    char *r = (char*)xmalloc(n + 1);
    memcpy(r, s, n);
    r[n] = 0;
    return r;
}

char *str_upper(char *s) {
    for (char *p = s; *p; ++p) *p = (char)toupper((unsigned char)*p);
    return s;
}

char *str_upper_dup(const char *s) {
    return str_upper(xstrdup(s));
}

int str_ieq(const char *a, const char *b) {
    if (!a || !b) return a == b;
    while (*a && *b) {
        if (toupper((unsigned char)*a) != toupper((unsigned char)*b)) return 0;
        ++a; ++b;
    }
    return *a == 0 && *b == 0;
}

```

### C.3 src/value.h

```c
#ifndef VALUE_H
#define VALUE_H
#include "common.h"

typedef enum { V_NUM, V_STR } VType;

typedef struct {
    VType type;
    union {
        double num;
        char  *str;   /* 소유: v_release 시 free */
    } as;
} Value;

Value v_num(double n);
Value v_str_copy(const char *s);   /* 입력 문자열을 복사 */
Value v_str_take(char *s);         /* s 의 소유권을 가져감 */
Value v_clone(Value v);            /* 깊은 복사 */
void  v_release(Value *v);         /* str 일 경우 free */

double v_to_num(Value v);          /* 강제 숫자화 (기본 0) */
char  *v_to_basic_string(Value v); /* malloc'd, BASIC 형식 */

bool   v_truthy(Value v);
char   var_kind(const char *name); /* 'n' | 's' | 'i'(integer) */
Value  coerce_for_var(const char *name, Value v); /* 타입 강제(소유 이전) */

#endif

```

### C.4 src/value.c

```c
#include "value.h"

Value v_num(double n) { Value v; v.type=V_NUM; v.as.num=n; return v; }
Value v_str_copy(const char *s) { Value v; v.type=V_STR; v.as.str=xstrdup(s?s:""); return v; }
Value v_str_take(char *s) { Value v; v.type=V_STR; v.as.str=s?s:xstrdup(""); return v; }

Value v_clone(Value v) {
    if (v.type == V_STR) return v_str_copy(v.as.str);
    return v;
}

void v_release(Value *v) {
    if (v->type == V_STR) {
        free(v->as.str);
        v->as.str = NULL;
    }
    v->type = V_NUM;
    v->as.num = 0;
}

double v_to_num(Value v) {
    if (v.type == V_NUM) return v.as.num;
    if (v.type == V_STR && v.as.str) return strtod(v.as.str, NULL);
    return 0.0;
}

char *v_to_basic_string(Value v) {
    if (v.type == V_STR) return xstrdup(v.as.str ? v.as.str : "");
    double n = v.as.num;
    char buf[64];
    if (isnan(n)) return xstrdup("NaN");
    if (n == INFINITY) return xstrdup("INF");
    if (n == -INFINITY) return xstrdup("-INF");
    if (n == floor(n) && fabs(n) < 1e15) {
        snprintf(buf, sizeof(buf), n >= 0 ? " %lld " : "%lld ", (long long)n);
    } else {
        snprintf(buf, sizeof(buf), n >= 0 ? " %.7g " : "%.7g ", n);
    }
    return xstrdup(buf);
}

bool v_truthy(Value v) {
    if (v.type == V_NUM) return v.as.num != 0.0;
    if (v.type == V_STR) return v.as.str && v.as.str[0] != 0;
    return false;
}

char var_kind(const char *name) {
    size_t n = strlen(name);
    if (!n) return 'n';
    char c = name[n-1];
    if (c == '$') return 's';
    if (c == '%') return 'i';
    return 'n';
}

Value coerce_for_var(const char *name, Value v) {
    char k = var_kind(name);
    if (k == 's') {
        if (v.type == V_NUM) die("Type mismatch: 문자열 변수 %s 에 숫자 대입", name);
        return v;
    }
    if (v.type == V_STR) die("Type mismatch: 숫자 변수 %s 에 문자열 대입", name);
    if (k == 'i') v.as.num = floor(v.as.num + 0.5);
    return v;
}

```

### C.5 src/lexer.h

```c
#ifndef LEXER_H
#define LEXER_H
#include "common.h"

typedef enum {
    T_EOF = 0,    T_EOL,
    T_NUMBER,     T_STRING,    T_IDENT,    T_KEYWORD,    T_REM,
    T_COLON,      T_SEMI,      T_COMMA,
    T_LPAREN,     T_RPAREN,
    T_PLUS,       T_MINUS,     T_STAR,     T_SLASH,
    T_BACKSLASH,  T_CARET,
    T_EQ,         T_NE,        T_LT,       T_GT,        T_LE,    T_GE
} TokType;

typedef struct {
    TokType type;
    double  num;     /* T_NUMBER 인 경우 */
    char   *text;    /* 소유: STRING/IDENT/KEYWORD */
    int     line;
} Token;

typedef VEC(Token) Tokens;

void  lex(const char *src, Tokens *out);
void  tokens_free(Tokens *t);
const char *tok_name(TokType t);

#endif

```

### C.6 src/lexer.c

```c
#include "lexer.h"

static const char *KEYWORDS[] = {
    "LET","PRINT","INPUT","IF","THEN","ELSE",
    "GOTO","GOSUB","RETURN",
    "FOR","TO","STEP","NEXT",
    "WHILE","WEND",
    "END","STOP","REM",
    "DIM","DATA","READ","RESTORE",
    "DEF","FN","ON",
    "AND","OR","NOT","MOD","XOR","EQV","IMP",
    "CLS","RUN","NEW","LIST",
    "TAB","SPC","USING",
    NULL
};

static int is_keyword(const char *s) {
    for (int i = 0; KEYWORDS[i]; ++i) {
        if (str_ieq(s, KEYWORDS[i])) return 1;
    }
    return 0;
}

typedef struct {
    const char *src;
    int pos;
    int line;
    Tokens *out;
} Lx;

static char peek(Lx *l, int off) {
    return l->src[l->pos + off];
}
static char advance(Lx *l) {
    char c = l->src[l->pos];
    if (c) {
        ++l->pos;
        if (c == '\n') ++l->line;
    }
    return c;
}
static void emit(Lx *l, TokType t, const char *text, int textlen, double num) {
    Token tk;
    tk.type = t;
    tk.num  = num;
    tk.text = text ? xstrndup(text, textlen) : NULL;
    tk.line = l->line;
    vec_push(Token, l->out, tk);
}

static void lex_number(Lx *l) {
    int start = l->pos;
    while (isdigit((unsigned char)peek(l, 0))) advance(l);
    if (peek(l, 0) == '.') {
        advance(l);
        while (isdigit((unsigned char)peek(l, 0))) advance(l);
    }
    char p = peek(l, 0);
    if (p == 'e' || p == 'E' || p == 'd' || p == 'D') {
        advance(l);
        if (peek(l, 0) == '+' || peek(l, 0) == '-') advance(l);
        while (isdigit((unsigned char)peek(l, 0))) advance(l);
    }
    /* 타입 접미어 (숫자 리터럴): 무시 */
    char p2 = peek(l, 0);
    if (p2 == '%' || p2 == '!' || p2 == '#') advance(l);

    int len = l->pos - start;
    char buf[64];
    if (len >= (int)sizeof(buf)) len = sizeof(buf) - 1;
    memcpy(buf, l->src + start, len);
    buf[len] = 0;
    /* d/D → e */
    for (int i = 0; buf[i]; ++i) if (buf[i]=='d' || buf[i]=='D') buf[i]='e';
    /* 끝의 접미어 제거 */
    int blen = (int)strlen(buf);
    if (blen && (buf[blen-1] == '%' || buf[blen-1] == '!' || buf[blen-1] == '#'))
        buf[blen-1] = 0;
    emit(l, T_NUMBER, NULL, 0, strtod(buf, NULL));
}

static void lex_string(Lx *l) {
    advance(l); /* 여는 " */
    int start = l->pos;
    while (peek(l, 0) && peek(l, 0) != '"' && peek(l, 0) != '\n') advance(l);
    int end = l->pos;
    if (peek(l, 0) != '"') die("문자열이 닫히지 않았습니다 (line %d)", l->line);
    advance(l); /* 닫는 " */
    emit(l, T_STRING, l->src + start, end - start, 0);
}

static void lex_ident(Lx *l) {
    int start = l->pos;
    while (isalnum((unsigned char)peek(l, 0)) || peek(l, 0) == '_') advance(l);
    /* 타입 접미어 */
    char p = peek(l, 0);
    if (p == '$' || p == '%' || p == '!' || p == '#') advance(l);

    int len = l->pos - start;
    char *raw = xstrndup(l->src + start, len);
    str_upper(raw);

    /* 접미어를 뺀 본체로 키워드 검사 */
    char *probe = xstrdup(raw);
    int  plen = (int)strlen(probe);
    if (plen && (probe[plen-1]=='$' || probe[plen-1]=='%' ||
                 probe[plen-1]=='!' || probe[plen-1]=='#'))
        probe[plen-1] = 0;

    if (is_keyword(probe)) {
        if (str_ieq(probe, "REM")) {
            /* 줄 끝까지 무시 */
            while (peek(l, 0) && peek(l, 0) != '\n') advance(l);
            free(raw);
            free(probe);
            emit(l, T_REM, NULL, 0, 0);
            return;
        }
        emit(l, T_KEYWORD, probe, (int)strlen(probe), 0);
        free(raw);
        free(probe);
        return;
    }
    free(probe);
    emit(l, T_IDENT, raw, (int)strlen(raw), 0);
    free(raw);
}

void lex(const char *src, Tokens *out) {
    Lx l = { src, 0, 1, out };
    while (l.src[l.pos]) {
        /* 공백/탭/CR 건너뛰기 (줄바꿈 제외) */
        while (peek(&l, 0)==' ' || peek(&l, 0)=='\t' || peek(&l, 0)=='\r') advance(&l);

        char c = peek(&l, 0);
        if (!c) break;

        switch (c) {
        case '\n': emit(&l, T_EOL, NULL, 0, 0); advance(&l); break;
        case ':':  emit(&l, T_COLON, NULL, 0, 0); advance(&l); break;
        case ';':  emit(&l, T_SEMI,  NULL, 0, 0); advance(&l); break;
        case ',':  emit(&l, T_COMMA, NULL, 0, 0); advance(&l); break;
        case '(':  emit(&l, T_LPAREN, NULL, 0, 0); advance(&l); break;
        case ')':  emit(&l, T_RPAREN, NULL, 0, 0); advance(&l); break;
        case '+':  emit(&l, T_PLUS,  NULL, 0, 0); advance(&l); break;
        case '-':  emit(&l, T_MINUS, NULL, 0, 0); advance(&l); break;
        case '*':  emit(&l, T_STAR,  NULL, 0, 0); advance(&l); break;
        case '/':  emit(&l, T_SLASH, NULL, 0, 0); advance(&l); break;
        case '\\': emit(&l, T_BACKSLASH, NULL, 0, 0); advance(&l); break;
        case '^':  emit(&l, T_CARET, NULL, 0, 0); advance(&l); break;
        case '?':  emit(&l, T_KEYWORD, "PRINT", 5, 0); advance(&l); break;
        case '=':  emit(&l, T_EQ,    NULL, 0, 0); advance(&l); break;
        case '<':
            advance(&l);
            if (peek(&l, 0)=='=') { advance(&l); emit(&l, T_LE, NULL,0,0); }
            else if (peek(&l, 0)=='>') { advance(&l); emit(&l, T_NE, NULL,0,0); }
            else emit(&l, T_LT, NULL, 0, 0);
            break;
        case '>':
            advance(&l);
            if (peek(&l, 0)=='=') { advance(&l); emit(&l, T_GE, NULL,0,0); }
            else if (peek(&l, 0)=='<') { advance(&l); emit(&l, T_NE, NULL,0,0); }
            else emit(&l, T_GT, NULL, 0, 0);
            break;
        case '"': lex_string(&l); break;
        default:
            if (isdigit((unsigned char)c) || (c == '.' && isdigit((unsigned char)peek(&l, 1))))
                lex_number(&l);
            else if (isalpha((unsigned char)c) || c == '_')
                lex_ident(&l);
            else
                die("알 수 없는 문자 '%c' (line %d)", c, l.line);
        }
    }
    emit(&l, T_EOF, NULL, 0, 0);
}

void tokens_free(Tokens *t) {
    for (int i = 0; i < t->len; ++i) free(t->data[i].text);
    vec_free(t);
}

const char *tok_name(TokType t) {
    switch (t) {
        case T_EOF: return "EOF"; case T_EOL: return "EOL";
        case T_NUMBER: return "NUMBER"; case T_STRING: return "STRING";
        case T_IDENT: return "IDENT"; case T_KEYWORD: return "KEYWORD";
        case T_REM: return "REM"; case T_COLON: return "COLON";
        case T_SEMI: return "SEMI"; case T_COMMA: return "COMMA";
        case T_LPAREN: return "LPAREN"; case T_RPAREN: return "RPAREN";
        case T_PLUS: return "+"; case T_MINUS: return "-";
        case T_STAR: return "*"; case T_SLASH: return "/";
        case T_BACKSLASH: return "\\"; case T_CARET: return "^";
        case T_EQ: return "="; case T_NE: return "<>";
        case T_LT: return "<"; case T_GT: return ">";
        case T_LE: return "<="; case T_GE: return ">=";
    }
    return "?";
}

```

### C.7 src/ast.h

```c
#ifndef AST_H
#define AST_H
#include "common.h"

typedef enum {
    A_PROGRAM, A_LINE,
    /* 문장 */
    A_LET, A_PRINT, A_INPUT, A_IF,
    A_FOR, A_NEXT, A_WHILE, A_WEND,
    A_GOTO, A_GOSUB, A_RETURN,
    A_END, A_STOP, A_REM, A_CLS,
    A_DIM, A_DATA, A_READ, A_RESTORE,
    A_DEFFN, A_ONJMP,
    /* 표현식 */
    A_NUMLIT, A_STRLIT, A_VAR,
    A_BINOP, A_UNOP, A_CALL, A_FNCALL,
    /* PRINT 항목 */
    A_PRINT_EXPR, A_PRINT_SEP, A_PRINT_TAB, A_PRINT_SPC
} AstTag;

typedef struct AstNode AstNode;
typedef VEC(AstNode*) AstList;
typedef VEC(char*)    StrList;
typedef VEC(int)      IntList;

typedef struct { int kind; double num; char *str; } DataItem; /* kind: 0=num, 1=str (str owned) */
typedef VEC(DataItem) DataList;

typedef struct DimDecl { char *name; AstList dims; } DimDecl;
typedef VEC(DimDecl) DimDeclList;

struct AstNode {
    AstTag tag;
    int    line_no;
    /* 공통 슬롯 (의미는 tag 별로 다름) */
    char   *s1;            /* var name, op string, prompt, fn name */
    char   *s2;            /* second string (e.g. ON kind: "JMP"|"GOSUB") */
    double  d1;            /* numlit value */
    int     i1;            /* line target, has-flag, kind */
    int     i2;            /* additional int (e.g. count) */
    AstNode *a, *b, *c;    /* 자식 (left/right/cond/etc.) */
    AstList list1;         /* 자식 리스트 (then, items, args, indices…) */
    AstList list2;         /* else 분기 등 */
    StrList slist;         /* 매개변수, NEXT 변수 등 */
    IntList ilist;         /* ON GOTO targets */
    DataList dlist;        /* DATA 항목들 */
    DimDeclList dimlist;   /* DIM 선언들 */
};

AstNode *ast_new(AstTag tag);
void     ast_free(AstNode *n);

#endif

```

### C.8 src/ast.c

```c
#include "ast.h"

AstNode *ast_new(AstTag tag) {
    AstNode *n = (AstNode*)xmalloc(sizeof(AstNode));
    memset(n, 0, sizeof(*n));
    n->tag = tag;
    vec_init(&n->list1);
    vec_init(&n->list2);
    vec_init(&n->slist);
    vec_init(&n->ilist);
    vec_init(&n->dlist);
    vec_init(&n->dimlist);
    return n;
}

void ast_free(AstNode *n) {
    if (!n) return;
    free(n->s1);
    free(n->s2);
    if (n->a) ast_free(n->a);
    if (n->b) ast_free(n->b);
    if (n->c) ast_free(n->c);
    for (int i = 0; i < n->list1.len; ++i) ast_free(n->list1.data[i]);
    vec_free(&n->list1);
    for (int i = 0; i < n->list2.len; ++i) ast_free(n->list2.data[i]);
    vec_free(&n->list2);
    for (int i = 0; i < n->slist.len; ++i) free(n->slist.data[i]);
    vec_free(&n->slist);
    vec_free(&n->ilist);
    for (int i = 0; i < n->dlist.len; ++i) free(n->dlist.data[i].str);
    vec_free(&n->dlist);
    for (int i = 0; i < n->dimlist.len; ++i) {
        free(n->dimlist.data[i].name);
        for (int j = 0; j < n->dimlist.data[i].dims.len; ++j)
            ast_free(n->dimlist.data[i].dims.data[j]);
        vec_free(&n->dimlist.data[i].dims);
    }
    vec_free(&n->dimlist);
    free(n);
}

```

### C.9 src/parser.h

```c
#ifndef PARSER_H
#define PARSER_H
#include "ast.h"
#include "lexer.h"

AstNode *parse(Tokens *t);

#endif

```

### C.10 src/parser.c

```c
#include "parser.h"

typedef struct {
    Tokens *t;
    int pos;
} P;

static Token *cur(P *p)        { return &p->t->data[p->pos]; }
static Token *peek_n(P *p,int o){ return &p->t->data[p->pos + o]; }
static Token *advance_t(P *p)  { Token *t = &p->t->data[p->pos++]; return t; }

static int check(P *p, TokType t)            { return cur(p)->type == t; }
static int check_kw(P *p, const char *kw)    {
    return cur(p)->type == T_KEYWORD && cur(p)->text && str_ieq(cur(p)->text, kw);
}
static int accept_t(P *p, TokType t) { if (check(p,t)) { advance_t(p); return 1; } return 0; }
static int accept_kw(P *p, const char *kw) {
    if (check_kw(p,kw)) { advance_t(p); return 1; } return 0;
}
static Token *expect_t(P *p, TokType t, const char *msg) {
    if (!check(p,t)) die("파서 오류: %s 가 필요한데 %s 를 만났습니다 (line %d)",
                         msg, tok_name(cur(p)->type), cur(p)->line);
    return advance_t(p);
}

/* 전방 선언 */
static AstNode *parse_expr(P *p);
static AstNode *parse_unary(P *p);
static AstNode *parse_atom(P *p);
static AstNode *parse_stmt(P *p);
static AstNode *parse_let_body(P *p);
static AstNode *parse_lvalue(P *p);
static AstList  parse_then_branch(P *p);
static AstNode *parse_if(P *p);
static AstNode *parse_for(P *p);
static AstNode *parse_next(P *p);
static AstNode *parse_print(P *p);
static AstNode *parse_input(P *p);
static AstNode *parse_dim(P *p);
static AstNode *parse_data(P *p);
static AstNode *parse_read(P *p);
static AstNode *parse_restore(P *p);
static AstNode *parse_def(P *p);
static AstNode *parse_on(P *p);

/* ─── 우선순위 ─── */
static int peek_binop(P *p, const char **op_out, int *prec_out) {
    Token *t = cur(p);
    switch (t->type) {
        case T_PLUS:      *op_out="+";  *prec_out=8;  return 1;
        case T_MINUS:     *op_out="-";  *prec_out=8;  return 1;
        case T_STAR:      *op_out="*";  *prec_out=11; return 1;
        case T_SLASH:     *op_out="/";  *prec_out=11; return 1;
        case T_BACKSLASH: *op_out="\\"; *prec_out=10; return 1;
        case T_CARET:     *op_out="^";  *prec_out=13; return 1;
        case T_EQ:        *op_out="=";  *prec_out=7;  return 1;
        case T_NE:        *op_out="<>"; *prec_out=7;  return 1;
        case T_LT:        *op_out="<";  *prec_out=7;  return 1;
        case T_GT:        *op_out=">";  *prec_out=7;  return 1;
        case T_LE:        *op_out="<="; *prec_out=7;  return 1;
        case T_GE:        *op_out=">="; *prec_out=7;  return 1;
        case T_KEYWORD:
            if (str_ieq(t->text,"AND")) { *op_out="AND"; *prec_out=5;  return 1; }
            if (str_ieq(t->text,"OR"))  { *op_out="OR";  *prec_out=4;  return 1; }
            if (str_ieq(t->text,"XOR")) { *op_out="XOR"; *prec_out=3;  return 1; }
            if (str_ieq(t->text,"EQV")) { *op_out="EQV"; *prec_out=2;  return 1; }
            if (str_ieq(t->text,"IMP")) { *op_out="IMP"; *prec_out=1;  return 1; }
            if (str_ieq(t->text,"MOD")) { *op_out="MOD"; *prec_out=9;  return 1; }
            return 0;
        default: return 0;
    }
}

static int is_left_assoc(const char *op) {
    return strcmp(op, "^") != 0;
}

static AstNode *parse_binop(P *p, int min_prec) {
    AstNode *left = parse_unary(p);
    while (1) {
        const char *op; int prec;
        if (!peek_binop(p, &op, &prec) || prec < min_prec) break;
        advance_t(p);
        int next_min = is_left_assoc(op) ? prec + 1 : prec;
        AstNode *right = parse_binop(p, next_min);
        AstNode *bin = ast_new(A_BINOP);
        bin->s1 = xstrdup(op);
        bin->a = left; bin->b = right;
        left = bin;
    }
    return left;
}

static AstNode *parse_expr(P *p) { return parse_binop(p, 0); }

static AstNode *parse_unary(P *p) {
    if (accept_t(p, T_MINUS)) {
        AstNode *u = ast_new(A_UNOP); u->s1 = xstrdup("-"); u->a = parse_unary(p); return u;
    }
    if (accept_t(p, T_PLUS)) return parse_unary(p);
    if (accept_kw(p, "NOT")) {
        AstNode *u = ast_new(A_UNOP); u->s1 = xstrdup("NOT"); u->a = parse_unary(p); return u;
    }
    /* power */
    AstNode *base = parse_atom(p);
    if (check(p, T_CARET)) {
        advance_t(p);
        AstNode *exp = parse_unary(p);
        AstNode *bin = ast_new(A_BINOP);
        bin->s1 = xstrdup("^");
        bin->a = base; bin->b = exp;
        return bin;
    }
    return base;
}

static AstNode *parse_atom(P *p) {
    Token *t = cur(p);
    if (t->type == T_NUMBER) {
        advance_t(p);
        AstNode *n = ast_new(A_NUMLIT); n->d1 = t->num; return n;
    }
    if (t->type == T_STRING) {
        advance_t(p);
        AstNode *n = ast_new(A_STRLIT); n->s1 = xstrdup(t->text ? t->text : ""); return n;
    }
    if (t->type == T_LPAREN) {
        advance_t(p);
        AstNode *e = parse_expr(p);
        expect_t(p, T_RPAREN, ")");
        return e;
    }
    if (t->type == T_KEYWORD && str_ieq(t->text, "FN")) {
        advance_t(p);
        Token *id = expect_t(p, T_IDENT, "FN 이름");
        AstNode *n = ast_new(A_FNCALL);
        /* 저장은 "FN" + name 으로 */
        size_t L = strlen(id->text) + 3;
        n->s1 = (char*)xmalloc(L);
        snprintf(n->s1, L, "FN%s", id->text);
        if (accept_t(p, T_LPAREN)) {
            if (!check(p, T_RPAREN)) {
                vec_push(AstNode*, &n->list1, parse_expr(p));
                while (accept_t(p, T_COMMA))
                    vec_push(AstNode*, &n->list1, parse_expr(p));
            }
            expect_t(p, T_RPAREN, ")");
        }
        return n;
    }
    if (t->type == T_IDENT) {
        char *name = xstrdup(t->text);
        advance_t(p);
        if (check(p, T_LPAREN)) {
            advance_t(p);
            AstNode *n;
            /* FN 접두라면 사용자 정의 함수 */
            if (strncmp(name, "FN", 2) == 0)
                n = ast_new(A_FNCALL);
            else
                n = ast_new(A_CALL);
            n->s1 = name;
            if (!check(p, T_RPAREN)) {
                vec_push(AstNode*, &n->list1, parse_expr(p));
                while (accept_t(p, T_COMMA))
                    vec_push(AstNode*, &n->list1, parse_expr(p));
            }
            expect_t(p, T_RPAREN, ")");
            return n;
        }
        AstNode *n = ast_new(A_VAR);
        n->s1 = name;
        return n;
    }
    die("예상치 못한 토큰: %s (line %d)", tok_name(t->type), t->line);
}

static AstNode *parse_lvalue(P *p) {
    Token *id = expect_t(p, T_IDENT, "변수 이름");
    AstNode *v = ast_new(A_VAR);
    v->s1 = xstrdup(id->text);
    if (accept_t(p, T_LPAREN)) {
        v->i1 = 1; /* has indices */
        vec_push(AstNode*, &v->list1, parse_expr(p));
        while (accept_t(p, T_COMMA))
            vec_push(AstNode*, &v->list1, parse_expr(p));
        expect_t(p, T_RPAREN, ")");
    }
    return v;
}

static AstNode *parse_let_body(P *p) {
    AstNode *target = parse_lvalue(p);
    expect_t(p, T_EQ, "=");
    AstNode *expr = parse_expr(p);
    AstNode *let = ast_new(A_LET);
    let->a = target; let->b = expr;
    return let;
}

static AstNode *parse_print(P *p) {
    AstNode *pr = ast_new(A_PRINT);
    while (1) {
        if (check(p, T_EOL) || check(p, T_EOF) || check(p, T_COLON) || check_kw(p,"ELSE")) break;
        if (accept_t(p, T_COMMA)) {
            AstNode *s = ast_new(A_PRINT_SEP);
            s->i1 = ',';
            vec_push(AstNode*, &pr->list1, s);
        } else if (accept_t(p, T_SEMI)) {
            AstNode *s = ast_new(A_PRINT_SEP);
            s->i1 = ';';
            vec_push(AstNode*, &pr->list1, s);
        } else if (accept_kw(p, "TAB")) {
            expect_t(p, T_LPAREN, "(");
            AstNode *e = parse_expr(p);
            expect_t(p, T_RPAREN, ")");
            AstNode *t = ast_new(A_PRINT_TAB); t->a = e;
            vec_push(AstNode*, &pr->list1, t);
        } else if (accept_kw(p, "SPC")) {
            expect_t(p, T_LPAREN, "(");
            AstNode *e = parse_expr(p);
            expect_t(p, T_RPAREN, ")");
            AstNode *t = ast_new(A_PRINT_SPC); t->a = e;
            vec_push(AstNode*, &pr->list1, t);
        } else {
            AstNode *e = parse_expr(p);
            AstNode *pe = ast_new(A_PRINT_EXPR); pe->a = e;
            vec_push(AstNode*, &pr->list1, pe);
        }
    }
    return pr;
}

static AstNode *parse_input(P *p) {
    AstNode *in = ast_new(A_INPUT);
    if (check(p, T_STRING)) {
        Token *s = advance_t(p);
        in->s1 = xstrdup(s->text ? s->text : "");
        if (accept_t(p, T_SEMI) || accept_t(p, T_COMMA)) {}
    }
    vec_push(AstNode*, &in->list1, parse_lvalue(p));
    while (accept_t(p, T_COMMA))
        vec_push(AstNode*, &in->list1, parse_lvalue(p));
    return in;
}

static AstList parse_then_branch(P *p) {
    AstList out; vec_init(&out);
    if (check(p, T_NUMBER)) {
        AstNode *g = ast_new(A_GOTO);
        g->i1 = (int)advance_t(p)->num;
        vec_push(AstNode*, &out, g);
        return out;
    }
    while (1) {
        AstNode *s = parse_stmt(p);
        if (s) vec_push(AstNode*, &out, s);
        if (!accept_t(p, T_COLON)) break;
        if (check(p, T_EOL) || check(p, T_EOF) || check_kw(p, "ELSE")) break;
    }
    return out;
}

static AstNode *parse_if(P *p) {
    AstNode *n = ast_new(A_IF);
    n->a = parse_expr(p);
    if (!accept_kw(p, "THEN")) {
        if (!accept_kw(p, "GOTO")) die("THEN 또는 GOTO 가 필요합니다 (line %d)", cur(p)->line);
    }
    n->list1 = parse_then_branch(p);
    if (accept_kw(p, "ELSE")) {
        n->i1 = 1;
        n->list2 = parse_then_branch(p);
    }
    return n;
}

static AstNode *parse_for(P *p) {
    AstNode *n = ast_new(A_FOR);
    Token *v = expect_t(p, T_IDENT, "변수");
    n->s1 = xstrdup(v->text);
    expect_t(p, T_EQ, "=");
    n->a = parse_expr(p);
    if (!accept_kw(p, "TO")) die("TO 가 필요합니다 (line %d)", cur(p)->line);
    n->b = parse_expr(p);
    if (accept_kw(p, "STEP")) { n->c = parse_expr(p); n->i1 = 1; }
    return n;
}

static AstNode *parse_next(P *p) {
    AstNode *n = ast_new(A_NEXT);
    if (check(p, T_IDENT)) {
        vec_push(char*, &n->slist, xstrdup(advance_t(p)->text));
        while (accept_t(p, T_COMMA)) {
            Token *v = expect_t(p, T_IDENT, "변수");
            vec_push(char*, &n->slist, xstrdup(v->text));
        }
    }
    return n;
}

static AstNode *parse_dim(P *p) {
    AstNode *n = ast_new(A_DIM);
    while (1) {
        Token *id = expect_t(p, T_IDENT, "배열 이름");
        DimDecl d; d.name = xstrdup(id->text); vec_init(&d.dims);
        expect_t(p, T_LPAREN, "(");
        vec_push(AstNode*, &d.dims, parse_expr(p));
        while (accept_t(p, T_COMMA))
            vec_push(AstNode*, &d.dims, parse_expr(p));
        expect_t(p, T_RPAREN, ")");
        vec_push(DimDecl, &n->dimlist, d);
        if (!accept_t(p, T_COMMA)) break;
    }
    return n;
}

static AstNode *parse_data(P *p) {
    AstNode *n = ast_new(A_DATA);
    while (1) {
        DataItem it = {0,0,NULL};
        if (check(p, T_STRING)) {
            it.kind = 1; it.str = xstrdup(advance_t(p)->text);
        } else if (check(p, T_NUMBER)) {
            it.kind = 0; it.num = advance_t(p)->num;
        } else if (check(p, T_MINUS)) {
            advance_t(p);
            Token *nm = expect_t(p, T_NUMBER, "숫자");
            it.kind = 0; it.num = -nm->num;
        } else if (check(p, T_IDENT)) {
            it.kind = 1; it.str = xstrdup(advance_t(p)->text);
        } else die("DATA 항목이 잘못되었습니다 (line %d)", cur(p)->line);
        vec_push(DataItem, &n->dlist, it);
        if (!accept_t(p, T_COMMA)) break;
    }
    return n;
}

static AstNode *parse_read(P *p) {
    AstNode *n = ast_new(A_READ);
    vec_push(AstNode*, &n->list1, parse_lvalue(p));
    while (accept_t(p, T_COMMA))
        vec_push(AstNode*, &n->list1, parse_lvalue(p));
    return n;
}

static AstNode *parse_restore(P *p) {
    AstNode *n = ast_new(A_RESTORE);
    if (check(p, T_NUMBER)) {
        n->i1 = (int)advance_t(p)->num;
        n->i2 = 1; /* has target */
    }
    return n;
}

static AstNode *parse_def(P *p) {
    AstNode *n = ast_new(A_DEFFN);
    if (accept_kw(p, "FN")) {
        Token *id = expect_t(p, T_IDENT, "함수 이름");
        size_t L = strlen(id->text) + 3;
        n->s1 = (char*)xmalloc(L);
        snprintf(n->s1, L, "FN%s", id->text);
    } else if (check(p, T_IDENT)) {
        Token *id = advance_t(p);
        if (strncmp(id->text, "FN", 2) != 0)
            die("DEF 다음에 FN 으로 시작하는 이름이 필요 (line %d)", id->line);
        n->s1 = xstrdup(id->text);
    } else die("DEF FN 형식이 잘못 (line %d)", cur(p)->line);

    if (accept_t(p, T_LPAREN)) {
        if (!check(p, T_RPAREN)) {
            Token *p1 = expect_t(p, T_IDENT, "매개변수");
            vec_push(char*, &n->slist, xstrdup(p1->text));
            while (accept_t(p, T_COMMA)) {
                Token *p2 = expect_t(p, T_IDENT, "매개변수");
                vec_push(char*, &n->slist, xstrdup(p2->text));
            }
        }
        expect_t(p, T_RPAREN, ")");
    }
    expect_t(p, T_EQ, "=");
    n->a = parse_expr(p);
    return n;
}

static AstNode *parse_on(P *p) {
    AstNode *n = ast_new(A_ONJMP);
    n->a = parse_expr(p);
    if (accept_kw(p, "GOTO")) n->s2 = xstrdup("JMP");
    else if (accept_kw(p, "GOSUB")) n->s2 = xstrdup("GOSUB");
    else die("ON 다음에 GOTO 또는 GOSUB 가 필요 (line %d)", cur(p)->line);
    Token *t1 = expect_t(p, T_NUMBER, "라인 번호");
    vec_push(int, &n->ilist, (int)t1->num);
    while (accept_t(p, T_COMMA)) {
        Token *t2 = expect_t(p, T_NUMBER, "라인 번호");
        vec_push(int, &n->ilist, (int)t2->num);
    }
    return n;
}

static AstNode *parse_stmt(P *p) {
    if (check(p, T_REM)) { advance_t(p); return ast_new(A_REM); }
    if (accept_kw(p, "LET"))     return parse_let_body(p);
    if (accept_kw(p, "PRINT"))   return parse_print(p);
    if (accept_kw(p, "INPUT"))   return parse_input(p);
    if (accept_kw(p, "IF"))      return parse_if(p);
    if (accept_kw(p, "FOR"))     return parse_for(p);
    if (accept_kw(p, "NEXT"))    return parse_next(p);
    if (accept_kw(p, "WHILE"))   { AstNode *n = ast_new(A_WHILE); n->a = parse_expr(p); return n; }
    if (accept_kw(p, "WEND"))    return ast_new(A_WEND);
    if (accept_kw(p, "GOTO"))    { AstNode *n = ast_new(A_GOTO);  n->i1 = (int)expect_t(p,T_NUMBER,"라인 번호")->num; return n; }
    if (accept_kw(p, "GOSUB"))   { AstNode *n = ast_new(A_GOSUB); n->i1 = (int)expect_t(p,T_NUMBER,"라인 번호")->num; return n; }
    if (accept_kw(p, "RETURN"))  return ast_new(A_RETURN);
    if (accept_kw(p, "END"))     return ast_new(A_END);
    if (accept_kw(p, "STOP"))    return ast_new(A_STOP);
    if (accept_kw(p, "DIM"))     return parse_dim(p);
    if (accept_kw(p, "DATA"))    return parse_data(p);
    if (accept_kw(p, "READ"))    return parse_read(p);
    if (accept_kw(p, "RESTORE")) return parse_restore(p);
    if (accept_kw(p, "DEF"))     return parse_def(p);
    if (accept_kw(p, "ON"))      return parse_on(p);
    if (accept_kw(p, "CLS"))     return ast_new(A_CLS);
    if (check(p, T_IDENT))       return parse_let_body(p);
    return NULL;
}

static AstList parse_stmt_list(P *p) {
    AstList out; vec_init(&out);
    while (!check(p, T_EOL) && !check(p, T_EOF)) {
        AstNode *s = parse_stmt(p);
        if (s) vec_push(AstNode*, &out, s);
        if (!accept_t(p, T_COLON)) break;
    }
    return out;
}

static AstNode *parse_line(P *p) {
    AstNode *l = ast_new(A_LINE);
    if (check(p, T_NUMBER)) {
        l->i1 = (int)advance_t(p)->num;
        l->i2 = 1; /* has line number */
    }
    l->list1 = parse_stmt_list(p);
    if (check(p, T_EOL)) advance_t(p);
    return l;
}

AstNode *parse(Tokens *t) {
    P p = { t, 0 };
    AstNode *prog = ast_new(A_PROGRAM);
    while (!check(&p, T_EOF)) {
        if (check(&p, T_EOL)) { advance_t(&p); continue; }
        vec_push(AstNode*, &prog->list1, parse_line(&p));
    }
    return prog;
}

```

### C.11 src/runtime.h

```c
#ifndef RUNTIME_H
#define RUNTIME_H
#include "value.h"

struct VM;
typedef Value (*BuiltinFn)(struct VM *vm, Value *args, int nargs);

typedef struct {
    const char *name;
    BuiltinFn   fn;
    int         min_args;
    int         max_args;
} Builtin;

const Builtin *runtime_find(const char *name);
bool           runtime_is_builtin(const char *name);

#endif

```

### C.12 src/runtime.c

```c
#include "runtime.h"
#include "vm.h"
#include <time.h>

static double tonum(Value v) { return v_to_num(v); }
static char *tostr_dup(Value v) {
    if (v.type == V_STR) return xstrdup(v.as.str ? v.as.str : "");
    char buf[64];
    double n = v.as.num;
    if (n == floor(n) && fabs(n) < 1e15)
        snprintf(buf, sizeof(buf), "%lld", (long long)n);
    else
        snprintf(buf, sizeof(buf), "%.14g", n);
    return xstrdup(buf);
}

static Value bi_abs(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(fabs(tonum(a[0]))); }
static Value bi_sgn(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; double v=tonum(a[0]); return v_num(v>0?1:(v<0?-1:0)); }
static Value bi_int_(struct VM *vm, Value *a, int n) { (void)vm;(void)n; return v_num(floor(tonum(a[0]))); }
static Value bi_fix(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; double v=tonum(a[0]); return v_num(v>=0?floor(v):ceil(v)); }
static Value bi_sqr(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(sqrt(tonum(a[0]))); }
static Value bi_exp(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(exp(tonum(a[0]))); }
static Value bi_log(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(log(tonum(a[0]))); }
static Value bi_sin(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(sin(tonum(a[0]))); }
static Value bi_cos(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(cos(tonum(a[0]))); }
static Value bi_tan(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(tan(tonum(a[0]))); }
static Value bi_atn(struct VM *vm, Value *a, int n)  { (void)vm;(void)n; return v_num(atan(tonum(a[0]))); }
static Value bi_rnd(struct VM *vm, Value *a, int n)  { (void)vm;(void)a;(void)n; return v_num((double)rand() / (double)RAND_MAX); }

static Value bi_len(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    char *s = tostr_dup(a[0]);
    int L = (int)strlen(s); free(s);
    return v_num((double)L);
}
static Value bi_left(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    char *s = tostr_dup(a[0]);
    int k = (int)tonum(a[1]);
    int L = (int)strlen(s);
    if (k < 0) k = 0; if (k > L) k = L;
    char *r = xstrndup(s, k);
    free(s);
    return v_str_take(r);
}
static Value bi_right(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    char *s = tostr_dup(a[0]);
    int k = (int)tonum(a[1]);
    int L = (int)strlen(s);
    if (k < 0) k = 0; if (k > L) k = L;
    char *r = xstrdup(s + (L - k));
    free(s);
    return v_str_take(r);
}
static Value bi_mid(struct VM *vm, Value *a, int n) {
    (void)vm;
    char *s = tostr_dup(a[0]);
    int i = (int)tonum(a[1]);
    int L = (int)strlen(s);
    int len = (n >= 3) ? (int)tonum(a[2]) : (L - i + 1);
    if (i < 1) i = 1;
    if (i > L) { free(s); return v_str_copy(""); }
    if (len < 0) len = 0;
    if (i - 1 + len > L) len = L - (i - 1);
    char *r = xstrndup(s + i - 1, len);
    free(s);
    return v_str_take(r);
}
static Value bi_chr(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    int c = (int)tonum(a[0]) & 0xFF;
    char buf[2] = { (char)c, 0 };
    return v_str_copy(buf);
}
static Value bi_asc(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    char *s = tostr_dup(a[0]);
    int v = (s[0] != 0) ? (unsigned char)s[0] : 0;
    free(s);
    return v_num((double)v);
}
static Value bi_str(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    double v = tonum(a[0]);
    char buf[64];
    if (v == floor(v) && fabs(v) < 1e15)
        snprintf(buf, sizeof(buf), v >= 0 ? " %lld" : "%lld", (long long)v);
    else
        snprintf(buf, sizeof(buf), v >= 0 ? " %.7g" : "%.7g", v);
    return v_str_copy(buf);
}
static Value bi_val(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    char *s = tostr_dup(a[0]);
    double v = strtod(s, NULL);
    free(s);
    return v_num(v);
}
static Value bi_space(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    int k = (int)tonum(a[0]); if (k < 0) k = 0;
    char *r = (char*)xmalloc(k + 1);
    memset(r, ' ', k); r[k] = 0;
    return v_str_take(r);
}
static Value bi_string(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    int k = (int)tonum(a[0]); if (k < 0) k = 0;
    char ch;
    if (a[1].type == V_NUM) ch = (char)((int)a[1].as.num & 0xFF);
    else { char *s = tostr_dup(a[1]); ch = s[0]; free(s); }
    char *r = (char*)xmalloc(k + 1);
    memset(r, ch, k); r[k] = 0;
    return v_str_take(r);
}
static Value bi_instr(struct VM *vm, Value *a, int n) {
    (void)vm;
    int start = 1;
    char *s, *t;
    if (n == 2) { s = tostr_dup(a[0]); t = tostr_dup(a[1]); }
    else { start = (int)tonum(a[0]); s = tostr_dup(a[1]); t = tostr_dup(a[2]); }
    if (start < 1) start = 1;
    int L = (int)strlen(s);
    double res = 0;
    if (start <= L) {
        const char *p = strstr(s + start - 1, t);
        if (p) res = (double)(p - s + 1);
    }
    free(s); free(t);
    return v_num(res);
}
static Value bi_ucase(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    char *s = tostr_dup(a[0]);
    for (char *p = s; *p; ++p) *p = (char)toupper((unsigned char)*p);
    return v_str_take(s);
}
static Value bi_lcase(struct VM *vm, Value *a, int n) {
    (void)vm;(void)n;
    char *s = tostr_dup(a[0]);
    for (char *p = s; *p; ++p) *p = (char)tolower((unsigned char)*p);
    return v_str_take(s);
}
static Value bi_timer(struct VM *vm, Value *a, int n) {
    (void)vm;(void)a;(void)n;
    return v_num((double)time(NULL));
}
static Value bi_date(struct VM *vm, Value *a, int n) {
    (void)vm;(void)a;(void)n;
    time_t t = time(NULL);
    struct tm *lt = localtime(&t);
    char buf[16]; strftime(buf, sizeof(buf), "%m-%d-%Y", lt);
    return v_str_copy(buf);
}
static Value bi_time(struct VM *vm, Value *a, int n) {
    (void)vm;(void)a;(void)n;
    time_t t = time(NULL);
    struct tm *lt = localtime(&t);
    char buf[16]; strftime(buf, sizeof(buf), "%H:%M:%S", lt);
    return v_str_copy(buf);
}

static const Builtin BUILTINS[] = {
    {"ABS",     bi_abs,    1, 1},
    {"SGN",     bi_sgn,    1, 1},
    {"INT",     bi_int_,   1, 1},
    {"FIX",     bi_fix,    1, 1},
    {"SQR",     bi_sqr,    1, 1},
    {"EXP",     bi_exp,    1, 1},
    {"LOG",     bi_log,    1, 1},
    {"SIN",     bi_sin,    1, 1},
    {"COS",     bi_cos,    1, 1},
    {"TAN",     bi_tan,    1, 1},
    {"ATN",     bi_atn,    1, 1},
    {"RND",     bi_rnd,    0, 1},

    {"LEN",     bi_len,    1, 1},
    {"LEFT$",   bi_left,   2, 2},
    {"RIGHT$",  bi_right,  2, 2},
    {"MID$",    bi_mid,    2, 3},
    {"CHR$",    bi_chr,    1, 1},
    {"ASC",     bi_asc,    1, 1},
    {"STR$",    bi_str,    1, 1},
    {"VAL",     bi_val,    1, 1},
    {"SPACE$",  bi_space,  1, 1},
    {"STRING$", bi_string, 2, 2},
    {"INSTR",   bi_instr,  2, 3},
    {"UCASE$",  bi_ucase,  1, 1},
    {"LCASE$",  bi_lcase,  1, 1},

    {"TIMER",   bi_timer,  0, 0},
    {"DATE$",   bi_date,   0, 0},
    {"TIME$",   bi_time,   0, 0},
    {NULL, NULL, 0, 0}
};

const Builtin *runtime_find(const char *name) {
    for (int i = 0; BUILTINS[i].name; ++i) {
        if (str_ieq(name, BUILTINS[i].name)) return &BUILTINS[i];
    }
    return NULL;
}

bool runtime_is_builtin(const char *name) {
    return runtime_find(name) != NULL;
}

```

### C.13 src/compiler.h

```c
#ifndef COMPILER_H
#define COMPILER_H
#include "ast.h"

typedef enum {
    OP_HALT = 0,
    OP_PUSHN, OP_PUSHS, OP_LOAD, OP_STORE, OP_POP,
    OP_ALOAD, OP_ASTORE, OP_DIM,
    OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_IDIV, OP_MOD, OP_POW, OP_NEG,
    OP_EQ, OP_NE, OP_LT, OP_GT, OP_LE, OP_GE,
    OP_AND, OP_OR, OP_XOR, OP_EQV, OP_IMP, OP_NOT,
    OP_JMP, OP_JZ, OP_JNZ, OP_GOSUB, OP_RETURN, OP_ONJMP,
    OP_PRINT_ITEM, OP_PRINT_NL, OP_PRINT_TAB, OP_PRINT_TAB_TO, OP_PRINT_SPC,
    OP_INPUT, OP_READ, OP_READ_A, OP_RESTORE,
    OP_CALLF, OP_CALLU, OP_CLS
} OpCode;

typedef struct {
    OpCode op;
    int    iarg;     /* int 인자 (jump 주소, ndims, line, …) */
    int    iarg2;    /* 두번째 int (CALL argc, ON kind 0/1) */
    double narg;     /* PUSHN */
    char  *sarg;     /* PUSHS, LOAD, STORE, CALLF/CALLU 이름, INPUT prompt; 소유 */
    char  *sarg2;    /* INPUT 변수명 등; 소유 */
    int   *ilist;    /* ONJMP 라인 배열; 소유 (NULL 가능) */
    int    ilist_len;
} Inst;

typedef VEC(Inst) InstList;

typedef struct { int line; int addr; } LineAddr;
typedef struct { int line; int data_index; } LineDataAddr;
typedef VEC(LineAddr) LineMap;
typedef VEC(LineDataAddr) LineDataMap;

typedef struct {
    char *name;          /* "FNxxx" 대문자 */
    StrList params;      /* 매개변수 이름들 */
    AstNode *body;       /* AST 표현식 (소유 X — Program 노드의 일부) */
} FnDef;
typedef VEC(FnDef) FnList;

typedef struct {
    InstList ops;
    LineMap  line_addr;
    LineDataMap data_line_addr;
    DataList data;
    FnList   fns;
} Bytecode;

Bytecode *compile(AstNode *program);
void      bytecode_free(Bytecode *bc);
const char *op_name(OpCode op);

#endif

```

### C.14 src/compiler.c

```c
#include "compiler.h"
#include "runtime.h"

typedef struct {
    int addr;       /* ops 인덱스 (0-base) */
    int line;       /* 대상 BASIC 라인 번호 */
} PendingJump;

typedef struct ForFrame {
    char *var;      /* 루프 변수 이름 (소유) */
    int   top;      /* loop top 주소 */
    int   exit_jz;  /* 백패치할 JZ 주소 */
} ForFrame;

typedef struct WhileFrame {
    int top;
    int exit_jz;
} WhileFrame;

typedef VEC(PendingJump) PendingList;
typedef VEC(ForFrame)    ForStack;
typedef VEC(WhileFrame)  WhileStack;

typedef struct {
    Bytecode *bc;
    PendingList pending;
    ForStack    for_stack;
    WhileStack  while_stack;
} C;

static int c_emit(C *c, OpCode op) {
    Inst i = {0};
    i.op = op;
    vec_push(Inst, &c->bc->ops, i);
    return c->bc->ops.len; /* 1-base */
}
static int c_emit_n(C *c, OpCode op, double n) {
    int a = c_emit(c, op); c->bc->ops.data[a-1].narg = n; return a;
}
static int c_emit_s(C *c, OpCode op, const char *s) {
    int a = c_emit(c, op); c->bc->ops.data[a-1].sarg = xstrdup(s); return a;
}
static int c_emit_i(C *c, OpCode op, int v) {
    int a = c_emit(c, op); c->bc->ops.data[a-1].iarg = v; return a;
}
static int c_emit_si(C *c, OpCode op, const char *s, int v) {
    int a = c_emit_s(c, op, s); c->bc->ops.data[a-1].iarg = v; return a;
}
static int c_emit_si2(C *c, OpCode op, const char *s, int v1, int v2) {
    int a = c_emit_si(c, op, s, v1); c->bc->ops.data[a-1].iarg2 = v2; return a;
}
static int c_addr(C *c) { return c->bc->ops.len + 1; } /* next addr (1-base) */
static void c_patch(C *c, int addr_1based, int target) {
    c->bc->ops.data[addr_1based - 1].iarg = target;
}

static void compile_expr(C *c, AstNode *e);
static void compile_stmt(C *c, AstNode *s);

static void compile_expr(C *c, AstNode *e) {
    switch (e->tag) {
    case A_NUMLIT: c_emit_n(c, OP_PUSHN, e->d1); return;
    case A_STRLIT: c_emit_s(c, OP_PUSHS, e->s1 ? e->s1 : ""); return;
    case A_VAR:
        if (e->i1) {
            for (int i = 0; i < e->list1.len; ++i) compile_expr(c, e->list1.data[i]);
            c_emit_si(c, OP_ALOAD, e->s1, e->list1.len);
        } else {
            c_emit_s(c, OP_LOAD, e->s1);
        }
        return;
    case A_BINOP: {
        compile_expr(c, e->a);
        compile_expr(c, e->b);
        const char *op = e->s1;
        OpCode oc = OP_HALT;
        if      (!strcmp(op, "+"))   oc = OP_ADD;
        else if (!strcmp(op, "-"))   oc = OP_SUB;
        else if (!strcmp(op, "*"))   oc = OP_MUL;
        else if (!strcmp(op, "/"))   oc = OP_DIV;
        else if (!strcmp(op, "\\"))  oc = OP_IDIV;
        else if (!strcmp(op, "^"))   oc = OP_POW;
        else if (!strcmp(op, "MOD")) oc = OP_MOD;
        else if (!strcmp(op, "="))   oc = OP_EQ;
        else if (!strcmp(op, "<>"))  oc = OP_NE;
        else if (!strcmp(op, "<"))   oc = OP_LT;
        else if (!strcmp(op, ">"))   oc = OP_GT;
        else if (!strcmp(op, "<="))  oc = OP_LE;
        else if (!strcmp(op, ">="))  oc = OP_GE;
        else if (!strcmp(op, "AND")) oc = OP_AND;
        else if (!strcmp(op, "OR"))  oc = OP_OR;
        else if (!strcmp(op, "XOR")) oc = OP_XOR;
        else if (!strcmp(op, "EQV")) oc = OP_EQV;
        else if (!strcmp(op, "IMP")) oc = OP_IMP;
        else die("Unknown op: %s", op);
        c_emit(c, oc);
        return;
    }
    case A_UNOP:
        compile_expr(c, e->a);
        if (!strcmp(e->s1, "-")) c_emit(c, OP_NEG);
        else if (!strcmp(e->s1, "NOT")) c_emit(c, OP_NOT);
        else die("Unknown unary: %s", e->s1);
        return;
    case A_CALL:
        for (int i = 0; i < e->list1.len; ++i) compile_expr(c, e->list1.data[i]);
        if (runtime_is_builtin(e->s1)) {
            c_emit_si2(c, OP_CALLF, e->s1, 0, e->list1.len);
        } else {
            /* 배열 인덱싱으로 간주 */
            c_emit_si(c, OP_ALOAD, e->s1, e->list1.len);
        }
        return;
    case A_FNCALL:
        for (int i = 0; i < e->list1.len; ++i) compile_expr(c, e->list1.data[i]);
        c_emit_si2(c, OP_CALLU, e->s1, 0, e->list1.len);
        return;
    default: die("compile_expr: 알 수 없는 표현 tag %d", e->tag);
    }
}

static void compile_stmt(C *c, AstNode *s) {
    switch (s->tag) {
    case A_REM: case A_WEND: /* 따로 처리 */
        if (s->tag == A_REM) return;
        /* WEND: 가장 최근 while frame 닫기 */
        if (c->while_stack.len == 0) die("WEND without WHILE");
        {
            WhileFrame f = c->while_stack.data[--c->while_stack.len];
            c_emit_i(c, OP_JMP, f.top);
            c_patch(c, f.exit_jz, c_addr(c));
        }
        return;
    case A_LET: {
        AstNode *t = s->a;
        if (t->i1) {
            for (int i = 0; i < t->list1.len; ++i) compile_expr(c, t->list1.data[i]);
            compile_expr(c, s->b);
            c_emit_si(c, OP_ASTORE, t->s1, t->list1.len);
        } else {
            compile_expr(c, s->b);
            c_emit_s(c, OP_STORE, t->s1);
        }
        return;
    }
    case A_PRINT: {
        bool last_was_sep = false;
        for (int i = 0; i < s->list1.len; ++i) {
            AstNode *it = s->list1.data[i];
            if (it->tag == A_PRINT_EXPR) {
                compile_expr(c, it->a);
                c_emit(c, OP_PRINT_ITEM);
                last_was_sep = false;
            } else if (it->tag == A_PRINT_SEP) {
                if (it->i1 == ',') c_emit(c, OP_PRINT_TAB);
                last_was_sep = true;
            } else if (it->tag == A_PRINT_TAB) {
                compile_expr(c, it->a);
                c_emit(c, OP_PRINT_TAB_TO);
                last_was_sep = true;
            } else if (it->tag == A_PRINT_SPC) {
                compile_expr(c, it->a);
                c_emit(c, OP_PRINT_SPC);
                last_was_sep = true;
            }
        }
        if (!last_was_sep) c_emit(c, OP_PRINT_NL);
        return;
    }
    case A_INPUT: {
        for (int i = 0; i < s->list1.len; ++i) {
            AstNode *v = s->list1.data[i];
            int a = c_emit(c, OP_INPUT);
            /* sarg = prompt (첫 변수에만), sarg2 = 변수명 */
            c->bc->ops.data[a-1].sarg  = (s->s1 && i == 0) ? xstrdup(s->s1) : NULL;
            c->bc->ops.data[a-1].sarg2 = xstrdup(v->s1);
        }
        return;
    }
    case A_IF: {
        compile_expr(c, s->a);
        int jz = c_emit_i(c, OP_JZ, 0);
        for (int i = 0; i < s->list1.len; ++i) compile_stmt(c, s->list1.data[i]);
        if (s->i1) {
            int jmp_end = c_emit_i(c, OP_JMP, 0);
            c_patch(c, jz, c_addr(c));
            for (int i = 0; i < s->list2.len; ++i) compile_stmt(c, s->list2.data[i]);
            c_patch(c, jmp_end, c_addr(c));
        } else {
            c_patch(c, jz, c_addr(c));
        }
        return;
    }
    case A_FOR: {
        compile_expr(c, s->a); c_emit_s(c, OP_STORE, s->s1);
        compile_expr(c, s->b);
        char buf[256]; snprintf(buf, sizeof(buf), "__LIMIT_%s", s->s1);
        c_emit_s(c, OP_STORE, buf);
        if (s->i1) compile_expr(c, s->c); else c_emit_n(c, OP_PUSHN, 1.0);
        char buf2[256]; snprintf(buf2, sizeof(buf2), "__STEP_%s", s->s1);
        c_emit_s(c, OP_STORE, buf2);
        int top = c_addr(c);
        c_emit_s(c, OP_LOAD, buf2);
        c_emit_s(c, OP_LOAD, s->s1);
        c_emit_s(c, OP_LOAD, buf);
        c_emit(c, OP_SUB); c_emit(c, OP_MUL);
        c_emit_n(c, OP_PUSHN, 0); c_emit(c, OP_LE);
        int jz = c_emit_i(c, OP_JZ, 0);
        ForFrame f; f.var = xstrdup(s->s1); f.top = top; f.exit_jz = jz;
        vec_push(ForFrame, &c->for_stack, f);
        return;
    }
    case A_NEXT: {
        int n = s->slist.len > 0 ? s->slist.len : 1;
        for (int i = 0; i < n; ++i) {
            if (c->for_stack.len == 0) die("NEXT 짝이 없음");
            ForFrame f = c->for_stack.data[--c->for_stack.len];
            const char *want = s->slist.len > 0 ? s->slist.data[i] : NULL;
            if (want && strcmp(want, f.var) != 0)
                die("NEXT %s 인데 FOR %s 입니다", want, f.var);
            char buf2[256]; snprintf(buf2, sizeof(buf2), "__STEP_%s", f.var);
            c_emit_s(c, OP_LOAD, f.var);
            c_emit_s(c, OP_LOAD, buf2);
            c_emit(c, OP_ADD);
            c_emit_s(c, OP_STORE, f.var);
            c_emit_i(c, OP_JMP, f.top);
            c_patch(c, f.exit_jz, c_addr(c));
            free(f.var);
        }
        return;
    }
    case A_WHILE: {
        int top = c_addr(c);
        compile_expr(c, s->a);
        int jz = c_emit_i(c, OP_JZ, 0);
        WhileFrame f; f.top = top; f.exit_jz = jz;
        vec_push(WhileFrame, &c->while_stack, f);
        return;
    }
    case A_GOTO: {
        int a = c_emit_i(c, OP_JMP, 0);
        PendingJump pj; pj.addr = a; pj.line = s->i1;
        vec_push(PendingJump, &c->pending, pj);
        return;
    }
    case A_GOSUB: {
        int a = c_emit_i(c, OP_GOSUB, 0);
        PendingJump pj; pj.addr = a; pj.line = s->i1;
        vec_push(PendingJump, &c->pending, pj);
        return;
    }
    case A_RETURN: c_emit(c, OP_RETURN); return;
    case A_END:    c_emit(c, OP_HALT);   return;
    case A_STOP:   c_emit(c, OP_HALT);   return;
    case A_CLS:    c_emit(c, OP_CLS);    return;
    case A_DIM: {
        for (int i = 0; i < s->dimlist.len; ++i) {
            DimDecl d = s->dimlist.data[i];
            for (int j = 0; j < d.dims.len; ++j) compile_expr(c, d.dims.data[j]);
            c_emit_si(c, OP_DIM, d.name, d.dims.len);
        }
        return;
    }
    case A_DATA: {
        /* 데이터 항목들을 평탄화 배열로 추가 */
        for (int i = 0; i < s->dlist.len; ++i) {
            DataItem it = s->dlist.data[i];
            DataItem copy; copy.kind = it.kind; copy.num = it.num;
            copy.str = it.str ? xstrdup(it.str) : NULL;
            vec_push(DataItem, &c->bc->data, copy);
        }
        return;
    }
    case A_READ: {
        for (int i = 0; i < s->list1.len; ++i) {
            AstNode *v = s->list1.data[i];
            if (v->i1) {
                for (int j = 0; j < v->list1.len; ++j) compile_expr(c, v->list1.data[j]);
                c_emit_si(c, OP_READ_A, v->s1, v->list1.len);
            } else {
                c_emit_s(c, OP_READ, v->s1);
            }
        }
        return;
    }
    case A_RESTORE:
        c_emit_i(c, OP_RESTORE, s->i2 ? s->i1 : -1);
        return;
    case A_DEFFN: {
        FnDef f;
        f.name = xstrdup(s->s1);
        vec_init(&f.params);
        for (int i = 0; i < s->slist.len; ++i)
            vec_push(char*, &f.params, xstrdup(s->slist.data[i]));
        f.body = s->a; /* AST 그대로 차용 (Program 이 소유) */
        vec_push(FnDef, &c->bc->fns, f);
        return;
    }
    case A_ONJMP: {
        compile_expr(c, s->a);
        int a = c_emit_si2(c, OP_ONJMP, s->s2, 0, s->ilist.len);
        /* 라인 배열 복사 */
        int *arr = (int*)xmalloc(sizeof(int) * s->ilist.len);
        for (int i = 0; i < s->ilist.len; ++i) arr[i] = s->ilist.data[i];
        c->bc->ops.data[a-1].ilist = arr;
        c->bc->ops.data[a-1].ilist_len = s->ilist.len;
        return;
    }
    default: die("compile_stmt: tag %d", s->tag);
    }
}

Bytecode *compile(AstNode *program) {
    Bytecode *bc = (Bytecode*)xmalloc(sizeof(Bytecode));
    memset(bc, 0, sizeof(*bc));
    vec_init(&bc->ops);
    vec_init(&bc->line_addr);
    vec_init(&bc->data_line_addr);
    vec_init(&bc->data);
    vec_init(&bc->fns);

    C ctx;
    ctx.bc = bc;
    vec_init(&ctx.pending);
    vec_init(&ctx.for_stack);
    vec_init(&ctx.while_stack);

    for (int i = 0; i < program->list1.len; ++i) {
        AstNode *line = program->list1.data[i];
        if (line->i2) {
            LineAddr la = { line->i1, c_addr(&ctx) };
            vec_push(LineAddr, &bc->line_addr, la);
            LineDataAddr lda = { line->i1, bc->data.len + 1 };
            vec_push(LineDataAddr, &bc->data_line_addr, lda);
        }
        for (int j = 0; j < line->list1.len; ++j)
            compile_stmt(&ctx, line->list1.data[j]);
    }
    c_emit(&ctx, OP_HALT);

    /* pending GOTO/GOSUB 백패치 */
    for (int i = 0; i < ctx.pending.len; ++i) {
        PendingJump pj = ctx.pending.data[i];
        int target = -1;
        for (int j = 0; j < bc->line_addr.len; ++j) {
            if (bc->line_addr.data[j].line == pj.line) {
                target = bc->line_addr.data[j].addr; break;
            }
        }
        if (target < 0) die("Undefined line %d", pj.line);
        bc->ops.data[pj.addr - 1].iarg = target;
    }
    vec_free(&ctx.pending);
    vec_free(&ctx.for_stack);
    vec_free(&ctx.while_stack);
    return bc;
}

void bytecode_free(Bytecode *bc) {
    for (int i = 0; i < bc->ops.len; ++i) {
        free(bc->ops.data[i].sarg);
        free(bc->ops.data[i].sarg2);
        free(bc->ops.data[i].ilist);
    }
    vec_free(&bc->ops);
    vec_free(&bc->line_addr);
    vec_free(&bc->data_line_addr);
    for (int i = 0; i < bc->data.len; ++i) free(bc->data.data[i].str);
    vec_free(&bc->data);
    for (int i = 0; i < bc->fns.len; ++i) {
        free(bc->fns.data[i].name);
        for (int j = 0; j < bc->fns.data[i].params.len; ++j)
            free(bc->fns.data[i].params.data[j]);
        vec_free(&bc->fns.data[i].params);
    }
    vec_free(&bc->fns);
    free(bc);
}

const char *op_name(OpCode op) {
    static const char *NAMES[] = {
        "HALT","PUSHN","PUSHS","LOAD","STORE","POP",
        "ALOAD","ASTORE","DIM",
        "ADD","SUB","MUL","DIV","IDIV","MOD","POW","NEG",
        "EQ","NE","LT","GT","LE","GE",
        "AND","OR","XOR","EQV","IMP","NOT",
        "JMP","JZ","JNZ","GOSUB","RETURN","ONJMP",
        "PRINT_ITEM","PRINT_NL","PRINT_TAB","PRINT_TAB_TO","PRINT_SPC",
        "INPUT","READ","READ_A","RESTORE",
        "CALLF","CALLU","CLS"
    };
    return NAMES[op];
}

```

### C.15 src/vm.h

```c
#ifndef VM_H
#define VM_H
#include "compiler.h"
#include "value.h"

typedef struct { char *name; Value value; } VarSlot;
typedef VEC(VarSlot) VarMap;

typedef struct {
    char *name;
    int  *dims;       /* 차원별 max */
    int   ndims;
    Value *data;      /* 평탄화된 배열 */
    int   data_size;
    char  kind;       /* 'n','s','i' */
} ArrSlot;
typedef VEC(ArrSlot) ArrMap;

typedef struct VM {
    Bytecode *bc;
    int       ip;
    Value    *stack;
    int       stack_top;   /* 다음 push 위치 */
    int       stack_cap;
    VEC(int)  call_stack;
    VarMap    vars;
    ArrMap    arrays;
    int       data_ptr;    /* 1-base: bc->data 의 다음 항목 */
    int       print_col;
    int       zone_width;
    int       line_width;
    bool      halted;

    /* I/O 후크 (NULL = stdio) */
    void   (*output)(const char *s);
    char  *(*input) (const char *prompt);   /* 호출자가 free */
} VM;

VM   *vm_new(Bytecode *bc);
void  vm_run(VM *vm);
void  vm_free(VM *vm);

/* 디버그/AST 평가용 외부 API */
Value vm_eval_expr_ast(VM *vm, struct AstNode *e);

#endif

```

### C.16 src/vm.c

```c
#include "vm.h"
#include "runtime.h"
#include "ast.h"

/* ───── 도우미 ───── */

static void push_v(VM *vm, Value v) {
    if (vm->stack_top == vm->stack_cap) {
        vm->stack_cap = vm->stack_cap ? vm->stack_cap * 2 : 64;
        vm->stack = (Value*)xrealloc(vm->stack, sizeof(Value) * vm->stack_cap);
    }
    vm->stack[vm->stack_top++] = v;
}
static Value pop_v(VM *vm) {
    if (vm->stack_top == 0) die("stack underflow");
    return vm->stack[--vm->stack_top];
}

static int find_var(VM *vm, const char *name) {
    for (int i = 0; i < vm->vars.len; ++i)
        if (strcmp(vm->vars.data[i].name, name) == 0) return i;
    return -1;
}
static Value get_var(VM *vm, const char *name) {
    int i = find_var(vm, name);
    if (i < 0) {
        if (var_kind(name) == 's') return v_str_copy("");
        return v_num(0);
    }
    return v_clone(vm->vars.data[i].value);
}
static void set_var(VM *vm, const char *name, Value v) {
    v = coerce_for_var(name, v);
    int i = find_var(vm, name);
    if (i < 0) {
        VarSlot s; s.name = xstrdup(name); s.value = v;
        vec_push(VarSlot, &vm->vars, s);
    } else {
        v_release(&vm->vars.data[i].value);
        vm->vars.data[i].value = v;
    }
}

static int find_arr(VM *vm, const char *name) {
    for (int i = 0; i < vm->arrays.len; ++i)
        if (strcmp(vm->arrays.data[i].name, name) == 0) return i;
    return -1;
}
static int prod_dims(int *dims, int n) {
    int p = 1;
    for (int i = 0; i < n; ++i) p *= (dims[i] + 1);
    return p;
}
static int dim_array_internal(VM *vm, const char *name, int *dims, int n) {
    int i = find_arr(vm, name);
    if (i >= 0) {
        free(vm->arrays.data[i].name);
        free(vm->arrays.data[i].dims);
        for (int j = 0; j < vm->arrays.data[i].data_size; ++j)
            v_release(&vm->arrays.data[i].data[j]);
        free(vm->arrays.data[i].data);
        /* 자리 비움 — len 는 그대로 두고 덮어쓰기 */
    }
    ArrSlot s;
    s.name = xstrdup(name);
    s.kind = var_kind(name);
    s.ndims = n;
    s.dims = (int*)xmalloc(sizeof(int) * n);
    memcpy(s.dims, dims, sizeof(int) * n);
    s.data_size = prod_dims(dims, n);
    s.data = (Value*)xmalloc(sizeof(Value) * s.data_size);
    Value fill = (s.kind == 's') ? v_str_copy("") : v_num(0);
    for (int k = 0; k < s.data_size; ++k) s.data[k] = v_clone(fill);
    v_release(&fill);
    if (i >= 0) {
        vm->arrays.data[i] = s;
        return i;
    }
    vec_push(ArrSlot, &vm->arrays, s);
    return vm->arrays.len - 1;
}
static int ensure_arr(VM *vm, const char *name, int ndims) {
    int i = find_arr(vm, name);
    if (i >= 0) return i;
    int *dims = (int*)xmalloc(sizeof(int) * ndims);
    for (int k = 0; k < ndims; ++k) dims[k] = 10;
    int idx = dim_array_internal(vm, name, dims, ndims);
    free(dims);
    return idx;
}
static int linear_index(ArrSlot *a, int *idxs, int n) {
    if (n != a->ndims) die("배열 차원 수 불일치 (%s)", a->name);
    int idx = 0;
    for (int i = 0; i < n; ++i) {
        int k = idxs[i];
        if (k < 0 || k > a->dims[i])
            die("Subscript out of range (%s, %d)", a->name, k);
        idx = idx * (a->dims[i] + 1) + k;
    }
    return idx;
}

/* ───── 비트 연산 (32비트) ───── */
static long band_l(long a, long b) { return a & b; }
static long bor_l (long a, long b) { return a | b; }
static long bxor_l(long a, long b) { return a ^ b; }
static long bnot_l(long a) { return ~a; }
static long to_long(Value v) { return (long)v_to_num(v); }

/* ───── 출력 ───── */
static void out_str(VM *vm, const char *s) {
    if (vm->output) vm->output(s);
    else fputs(s, stdout);
    for (const char *p = s; *p; ++p) {
        if (*p == '\n') vm->print_col = 0;
        else vm->print_col++;
    }
}
static void out_newline(VM *vm) { out_str(vm, "\n"); }

/* ───── int 비교에 의한 boolean → BASIC bool ───── */
static double basic_bool(int b) { return b ? -1.0 : 0.0; }

static int values_equal(Value a, Value b) {
    if (a.type == V_STR && b.type == V_STR)
        return strcmp(a.as.str ? a.as.str : "", b.as.str ? b.as.str : "") == 0;
    return v_to_num(a) == v_to_num(b);
}
static int values_cmp(Value a, Value b) {
    if (a.type == V_STR && b.type == V_STR)
        return strcmp(a.as.str ? a.as.str : "", b.as.str ? b.as.str : "");
    double x = v_to_num(a), y = v_to_num(b);
    return (x < y) ? -1 : (x > y ? 1 : 0);
}

/* ───── 표현식 AST 평가 (DEF FN 본문용) ───── */

Value vm_eval_expr_ast(VM *vm, AstNode *e) {
    switch (e->tag) {
    case A_NUMLIT: return v_num(e->d1);
    case A_STRLIT: return v_str_copy(e->s1 ? e->s1 : "");
    case A_VAR: {
        if (e->i1) {
            int n = e->list1.len;
            int *idxs = (int*)xmalloc(sizeof(int)*n);
            for (int i = 0; i < n; ++i) {
                Value vi = vm_eval_expr_ast(vm, e->list1.data[i]);
                idxs[i] = (int)floor(v_to_num(vi) + 0.5);
                v_release(&vi);
            }
            int ai = ensure_arr(vm, e->s1, n);
            ArrSlot *a = &vm->arrays.data[ai];
            int li = linear_index(a, idxs, n);
            free(idxs);
            return v_clone(a->data[li]);
        }
        return get_var(vm, e->s1);
    }
    case A_BINOP: {
        Value x = vm_eval_expr_ast(vm, e->a);
        Value y = vm_eval_expr_ast(vm, e->b);
        const char *op = e->s1;
        Value r = v_num(0);
        if (!strcmp(op, "+")) {
            if (x.type == V_STR || y.type == V_STR) {
                char *xs = v_to_basic_string(x);
                char *ys = v_to_basic_string(y);
                /* '+' 연결 시에는 BASIC formatting 의 패딩을 넣지 않는다 */
                free(xs); free(ys);
                char *xs2 = (x.type == V_STR) ? xstrdup(x.as.str) : v_to_basic_string(x);
                char *ys2 = (y.type == V_STR) ? xstrdup(y.as.str) : v_to_basic_string(y);
                size_t L = strlen(xs2) + strlen(ys2) + 1;
                char *out = (char*)xmalloc(L);
                snprintf(out, L, "%s%s", xs2, ys2);
                free(xs2); free(ys2);
                r = v_str_take(out);
            } else r = v_num(v_to_num(x) + v_to_num(y));
        }
        else if (!strcmp(op, "-"))   r = v_num(v_to_num(x) - v_to_num(y));
        else if (!strcmp(op, "*"))   r = v_num(v_to_num(x) * v_to_num(y));
        else if (!strcmp(op, "/"))   { double d=v_to_num(y); if(d==0) die("Division by zero"); r = v_num(v_to_num(x)/d); }
        else if (!strcmp(op, "\\"))  { double d=v_to_num(y); if(d==0) die("Division by zero"); r = v_num(floor(v_to_num(x)/d)); }
        else if (!strcmp(op, "MOD")) { double a_=v_to_num(x), b_=v_to_num(y); r = v_num(a_ - floor(a_/b_)*b_); }
        else if (!strcmp(op, "^"))   r = v_num(pow(v_to_num(x), v_to_num(y)));
        else if (!strcmp(op, "="))   r = v_num(basic_bool(values_equal(x,y)));
        else if (!strcmp(op, "<>"))  r = v_num(basic_bool(!values_equal(x,y)));
        else if (!strcmp(op, "<"))   r = v_num(basic_bool(values_cmp(x,y) < 0));
        else if (!strcmp(op, ">"))   r = v_num(basic_bool(values_cmp(x,y) > 0));
        else if (!strcmp(op, "<="))  r = v_num(basic_bool(values_cmp(x,y) <= 0));
        else if (!strcmp(op, ">="))  r = v_num(basic_bool(values_cmp(x,y) >= 0));
        else if (!strcmp(op, "AND")) r = v_num((double)band_l(to_long(x), to_long(y)));
        else if (!strcmp(op, "OR"))  r = v_num((double)bor_l (to_long(x), to_long(y)));
        else if (!strcmp(op, "XOR")) r = v_num((double)bxor_l(to_long(x), to_long(y)));
        else if (!strcmp(op, "EQV")) r = v_num((double)bnot_l(bxor_l(to_long(x), to_long(y))));
        else if (!strcmp(op, "IMP")) r = v_num((double)bor_l(bnot_l(to_long(x)), to_long(y)));
        else die("Unknown op %s", op);
        v_release(&x); v_release(&y);
        return r;
    }
    case A_UNOP: {
        Value x = vm_eval_expr_ast(vm, e->a);
        Value r = v_num(0);
        if (!strcmp(e->s1, "-")) r = v_num(-v_to_num(x));
        else if (!strcmp(e->s1, "NOT")) r = v_num((double)bnot_l(to_long(x)));
        v_release(&x);
        return r;
    }
    case A_CALL: {
        int n = e->list1.len;
        Value *args = (Value*)xmalloc(sizeof(Value) * (n>0?n:1));
        for (int i = 0; i < n; ++i) args[i] = vm_eval_expr_ast(vm, e->list1.data[i]);
        Value r;
        const Builtin *b = runtime_find(e->s1);
        if (b) r = b->fn(vm, args, n);
        else {
            int ai = ensure_arr(vm, e->s1, n);
            ArrSlot *a = &vm->arrays.data[ai];
            int *idxs = (int*)xmalloc(sizeof(int)*n);
            for (int i = 0; i < n; ++i) idxs[i] = (int)floor(v_to_num(args[i]) + 0.5);
            int li = linear_index(a, idxs, n);
            free(idxs);
            r = v_clone(a->data[li]);
        }
        for (int i = 0; i < n; ++i) v_release(&args[i]);
        free(args);
        return r;
    }
    case A_FNCALL: {
        FnDef *fn = NULL;
        for (int i = 0; i < vm->bc->fns.len; ++i)
            if (str_ieq(vm->bc->fns.data[i].name, e->s1)) { fn = &vm->bc->fns.data[i]; break; }
        if (!fn) die("Undefined FN: %s", e->s1);
        int n = e->list1.len;
        Value *args = (Value*)xmalloc(sizeof(Value) * (n>0?n:1));
        for (int i = 0; i < n; ++i) args[i] = vm_eval_expr_ast(vm, e->list1.data[i]);

        /* 매개변수 그림자 */
        Value *saved = (Value*)xmalloc(sizeof(Value) * fn->params.len);
        bool *had = (bool*)xmalloc(sizeof(bool) * fn->params.len);
        for (int i = 0; i < fn->params.len; ++i) {
            int vi = find_var(vm, fn->params.data[i]);
            had[i] = (vi >= 0);
            saved[i] = had[i] ? v_clone(vm->vars.data[vi].value) : v_num(0);
            set_var(vm, fn->params.data[i], v_clone(args[i]));
        }
        Value r = vm_eval_expr_ast(vm, fn->body);
        /* 복원 */
        for (int i = 0; i < fn->params.len; ++i) {
            if (had[i]) set_var(vm, fn->params.data[i], saved[i]);
            else {
                int vi = find_var(vm, fn->params.data[i]);
                if (vi >= 0) {
                    v_release(&vm->vars.data[vi].value);
                    free(vm->vars.data[vi].name);
                    vm->vars.data[vi] = vm->vars.data[--vm->vars.len];
                }
                v_release(&saved[i]);
            }
        }
        free(saved); free(had);
        for (int i = 0; i < n; ++i) v_release(&args[i]);
        free(args);
        return r;
    }
    default: die("eval_expr_ast: tag %d", e->tag);
    }
}

/* ───── 명령 실행 ───── */

static void do_print_tab(VM *vm) {
    int col = vm->print_col;
    int next_zone = (col / vm->zone_width) * vm->zone_width + vm->zone_width;
    if (next_zone >= vm->line_width) out_newline(vm);
    else {
        char *pad = (char*)xmalloc(next_zone - col + 1);
        memset(pad, ' ', next_zone - col); pad[next_zone - col] = 0;
        out_str(vm, pad); free(pad);
    }
}
static void do_print_tab_to(VM *vm, int target) {
    if (target < 1) target = 1;
    if (vm->print_col >= target) out_newline(vm);
    int n = target - 1 - vm->print_col;
    if (n > 0) {
        char *pad = (char*)xmalloc(n + 1);
        memset(pad, ' ', n); pad[n] = 0;
        out_str(vm, pad); free(pad);
    }
}

static int find_line_addr(Bytecode *bc, int line) {
    for (int i = 0; i < bc->line_addr.len; ++i)
        if (bc->line_addr.data[i].line == line) return bc->line_addr.data[i].addr;
    return -1;
}

void vm_run(VM *vm) {
    Bytecode *bc = vm->bc;
    while (!vm->halted && vm->ip <= bc->ops.len) {
        Inst *op = &bc->ops.data[vm->ip - 1];
        vm->ip++;
        switch (op->op) {
        case OP_HALT: vm->halted = true; break;
        case OP_PUSHN: push_v(vm, v_num(op->narg)); break;
        case OP_PUSHS: push_v(vm, v_str_copy(op->sarg ? op->sarg : "")); break;
        case OP_POP:   { Value v = pop_v(vm); v_release(&v); break; }
        case OP_LOAD:  push_v(vm, get_var(vm, op->sarg)); break;
        case OP_STORE: { Value v = pop_v(vm); set_var(vm, op->sarg, v); break; }
        case OP_ALOAD: {
            int n = op->iarg;
            int *idxs = (int*)xmalloc(sizeof(int)*n);
            for (int i = n-1; i >= 0; --i) {
                Value v = pop_v(vm);
                idxs[i] = (int)floor(v_to_num(v) + 0.5);
                v_release(&v);
            }
            int ai = ensure_arr(vm, op->sarg, n);
            ArrSlot *a = &vm->arrays.data[ai];
            int li = linear_index(a, idxs, n);
            free(idxs);
            push_v(vm, v_clone(a->data[li]));
            break;
        }
        case OP_ASTORE: {
            int n = op->iarg;
            Value val = pop_v(vm);
            int *idxs = (int*)xmalloc(sizeof(int)*n);
            for (int i = n-1; i >= 0; --i) {
                Value v = pop_v(vm);
                idxs[i] = (int)floor(v_to_num(v) + 0.5);
                v_release(&v);
            }
            int ai = ensure_arr(vm, op->sarg, n);
            ArrSlot *a = &vm->arrays.data[ai];
            int li = linear_index(a, idxs, n);
            free(idxs);
            v_release(&a->data[li]);
            a->data[li] = coerce_for_var(op->sarg, val);
            break;
        }
        case OP_DIM: {
            int n = op->iarg;
            int *dims = (int*)xmalloc(sizeof(int)*n);
            for (int i = n-1; i >= 0; --i) {
                Value v = pop_v(vm);
                dims[i] = (int)floor(v_to_num(v) + 0.5);
                v_release(&v);
            }
            dim_array_internal(vm, op->sarg, dims, n);
            free(dims);
            break;
        }
        case OP_ADD: {
            Value b = pop_v(vm); Value a = pop_v(vm);
            if (a.type == V_STR || b.type == V_STR) {
                char *as = (a.type == V_STR) ? xstrdup(a.as.str) : v_to_basic_string(a);
                char *bs = (b.type == V_STR) ? xstrdup(b.as.str) : v_to_basic_string(b);
                size_t L = strlen(as) + strlen(bs) + 1;
                char *out = (char*)xmalloc(L);
                snprintf(out, L, "%s%s", as, bs); free(as); free(bs);
                push_v(vm, v_str_take(out));
            } else push_v(vm, v_num(a.as.num + b.as.num));
            v_release(&a); v_release(&b);
            break;
        }
#define BINOP_NUM(OP,EXPR) case OP: { Value b=pop_v(vm); Value a=pop_v(vm); double x=v_to_num(a), y=v_to_num(b); push_v(vm, v_num(EXPR)); v_release(&a); v_release(&b); break; }
        BINOP_NUM(OP_SUB,  x - y)
        BINOP_NUM(OP_MUL,  x * y)
        case OP_DIV: { Value b=pop_v(vm); Value a=pop_v(vm); double y=v_to_num(b); if(y==0) die("Division by zero"); push_v(vm, v_num(v_to_num(a)/y)); v_release(&a); v_release(&b); break; }
        case OP_IDIV: { Value b=pop_v(vm); Value a=pop_v(vm); double y=v_to_num(b); if(y==0) die("Division by zero"); push_v(vm, v_num(floor(v_to_num(a)/y))); v_release(&a); v_release(&b); break; }
        case OP_MOD: { Value b=pop_v(vm); Value a=pop_v(vm); double x=v_to_num(a), y=v_to_num(b); push_v(vm, v_num(x - floor(x/y)*y)); v_release(&a); v_release(&b); break; }
        BINOP_NUM(OP_POW,  pow(x, y))
        case OP_NEG: { Value a=pop_v(vm); push_v(vm, v_num(-v_to_num(a))); v_release(&a); break; }
#undef BINOP_NUM

        case OP_EQ: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num(basic_bool(values_equal(a,b)))); v_release(&a); v_release(&b); break; }
        case OP_NE: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num(basic_bool(!values_equal(a,b)))); v_release(&a); v_release(&b); break; }
        case OP_LT: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num(basic_bool(values_cmp(a,b) < 0))); v_release(&a); v_release(&b); break; }
        case OP_GT: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num(basic_bool(values_cmp(a,b) > 0))); v_release(&a); v_release(&b); break; }
        case OP_LE: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num(basic_bool(values_cmp(a,b) <= 0))); v_release(&a); v_release(&b); break; }
        case OP_GE: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num(basic_bool(values_cmp(a,b) >= 0))); v_release(&a); v_release(&b); break; }

#define LOGIC(OP,FN) case OP: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num((double)FN(to_long(a), to_long(b)))); v_release(&a); v_release(&b); break; }
        LOGIC(OP_AND, band_l)
        LOGIC(OP_OR,  bor_l)
        LOGIC(OP_XOR, bxor_l)
        case OP_EQV: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num((double)bnot_l(bxor_l(to_long(a), to_long(b))))); v_release(&a); v_release(&b); break; }
        case OP_IMP: { Value b=pop_v(vm); Value a=pop_v(vm); push_v(vm, v_num((double)bor_l(bnot_l(to_long(a)), to_long(b)))); v_release(&a); v_release(&b); break; }
        case OP_NOT: { Value a=pop_v(vm); push_v(vm, v_num((double)bnot_l(to_long(a)))); v_release(&a); break; }
#undef LOGIC

        case OP_JMP: vm->ip = op->iarg; break;
        case OP_JZ:  { Value v = pop_v(vm); if (!v_truthy(v)) vm->ip = op->iarg; v_release(&v); break; }
        case OP_JNZ: { Value v = pop_v(vm); if ( v_truthy(v)) vm->ip = op->iarg; v_release(&v); break; }
        case OP_GOSUB: vec_push(int, &vm->call_stack, vm->ip); vm->ip = op->iarg; break;
        case OP_RETURN: {
            if (vm->call_stack.len == 0) die("RETURN without GOSUB");
            vm->ip = vm->call_stack.data[--vm->call_stack.len];
            break;
        }
        case OP_ONJMP: {
            Value v = pop_v(vm);
            int n = (int)floor(v_to_num(v) + 0.5);
            v_release(&v);
            if (n < 1 || n > op->ilist_len) break;
            int target_line = op->ilist[n-1];
            int target_addr = find_line_addr(bc, target_line);
            if (target_addr < 0) die("Undefined line %d", target_line);
            if (op->sarg && strcmp(op->sarg, "GOSUB") == 0)
                vec_push(int, &vm->call_stack, vm->ip);
            vm->ip = target_addr;
            break;
        }
        case OP_PRINT_ITEM: {
            Value v = pop_v(vm);
            char *s = v_to_basic_string(v);
            out_str(vm, s);
            free(s); v_release(&v);
            break;
        }
        case OP_PRINT_NL:     out_newline(vm); break;
        case OP_PRINT_TAB:    do_print_tab(vm); break;
        case OP_PRINT_TAB_TO: { Value v=pop_v(vm); do_print_tab_to(vm, (int)floor(v_to_num(v))); v_release(&v); break; }
        case OP_PRINT_SPC: {
            Value v = pop_v(vm);
            int n = (int)floor(v_to_num(v));
            v_release(&v);
            if (n > 0) { char *p = (char*)xmalloc(n+1); memset(p,' ',n); p[n]=0; out_str(vm,p); free(p); }
            break;
        }
        case OP_INPUT: {
            const char *prompt = op->sarg ? op->sarg : "";
            const char *vname  = op->sarg2 ? op->sarg2 : "";
            char prbuf[256];
            snprintf(prbuf, sizeof(prbuf), "%s%s", prompt, prompt[0] ? "? " : "? ");
            char *line;
            if (vm->input) line = vm->input(prbuf);
            else {
                fputs(prbuf, stdout); fflush(stdout);
                size_t cap = 256; line = (char*)xmalloc(cap);
                if (!fgets(line, (int)cap, stdin)) { line[0] = 0; }
                size_t L = strlen(line);
                while (L > 0 && (line[L-1] == '\n' || line[L-1] == '\r')) line[--L] = 0;
            }
            if (var_kind(vname) == 's') set_var(vm, vname, v_str_take(line));
            else { double x = strtod(line, NULL); free(line); set_var(vm, vname, v_num(x)); }
            break;
        }
        case OP_READ: {
            if (vm->data_ptr > bc->data.len) die("Out of DATA");
            DataItem it = bc->data.data[vm->data_ptr - 1];
            vm->data_ptr++;
            const char *vname = op->sarg;
            if (var_kind(vname) == 's') {
                set_var(vm, vname, v_str_copy(it.kind==1 ? (it.str?it.str:"") : ""));
            } else {
                double x = (it.kind == 0) ? it.num : strtod(it.str?it.str:"0", NULL);
                set_var(vm, vname, v_num(x));
            }
            break;
        }
        case OP_READ_A: {
            if (vm->data_ptr > bc->data.len) die("Out of DATA");
            DataItem it = bc->data.data[vm->data_ptr - 1];
            vm->data_ptr++;
            int n = op->iarg;
            int *idxs = (int*)xmalloc(sizeof(int)*n);
            for (int i = n-1; i >= 0; --i) {
                Value v = pop_v(vm);
                idxs[i] = (int)floor(v_to_num(v) + 0.5);
                v_release(&v);
            }
            int ai = ensure_arr(vm, op->sarg, n);
            ArrSlot *a = &vm->arrays.data[ai];
            int li = linear_index(a, idxs, n);
            free(idxs);
            v_release(&a->data[li]);
            if (a->kind == 's') a->data[li] = v_str_copy(it.kind==1 ? it.str : "");
            else a->data[li] = v_num(it.kind == 0 ? it.num : strtod(it.str?it.str:"0", NULL));
            break;
        }
        case OP_RESTORE: {
            int line = op->iarg;
            if (line < 0) vm->data_ptr = 1;
            else {
                int found = -1;
                for (int i = 0; i < bc->data_line_addr.len; ++i)
                    if (bc->data_line_addr.data[i].line == line) { found = bc->data_line_addr.data[i].data_index; break; }
                vm->data_ptr = (found > 0) ? found : 1;
            }
            break;
        }
        case OP_CALLF: {
            int n = op->iarg2;
            Value *args = (Value*)xmalloc(sizeof(Value) * (n>0?n:1));
            for (int i = n-1; i >= 0; --i) args[i] = pop_v(vm);
            const Builtin *b = runtime_find(op->sarg);
            if (!b) die("정의되지 않은 함수: %s", op->sarg);
            push_v(vm, b->fn(vm, args, n));
            for (int i = 0; i < n; ++i) v_release(&args[i]);
            free(args);
            break;
        }
        case OP_CALLU: {
            int n = op->iarg2;
            FnDef *fn = NULL;
            for (int i = 0; i < bc->fns.len; ++i)
                if (str_ieq(bc->fns.data[i].name, op->sarg)) { fn = &bc->fns.data[i]; break; }
            if (!fn) die("Undefined FN: %s", op->sarg);
            Value *args = (Value*)xmalloc(sizeof(Value) * (n>0?n:1));
            for (int i = n-1; i >= 0; --i) args[i] = pop_v(vm);

            Value *saved = (Value*)xmalloc(sizeof(Value) * fn->params.len);
            bool *had = (bool*)xmalloc(sizeof(bool) * fn->params.len);
            for (int i = 0; i < fn->params.len; ++i) {
                int vi = find_var(vm, fn->params.data[i]);
                had[i] = (vi >= 0);
                saved[i] = had[i] ? v_clone(vm->vars.data[vi].value) : v_num(0);
                set_var(vm, fn->params.data[i], v_clone(i < n ? args[i] : v_num(0)));
            }
            Value r = vm_eval_expr_ast(vm, fn->body);
            for (int i = 0; i < fn->params.len; ++i) {
                if (had[i]) set_var(vm, fn->params.data[i], saved[i]);
                else {
                    int vi = find_var(vm, fn->params.data[i]);
                    if (vi >= 0) {
                        v_release(&vm->vars.data[vi].value);
                        free(vm->vars.data[vi].name);
                        vm->vars.data[vi] = vm->vars.data[--vm->vars.len];
                    }
                    v_release(&saved[i]);
                }
            }
            free(saved); free(had);
            push_v(vm, r);
            for (int i = 0; i < n; ++i) v_release(&args[i]);
            free(args);
            break;
        }
        case OP_CLS:
            out_str(vm, "\033[2J\033[H");
            vm->print_col = 0;
            break;
        }
    }
}

VM *vm_new(Bytecode *bc) {
    VM *vm = (VM*)xmalloc(sizeof(VM));
    memset(vm, 0, sizeof(*vm));
    vm->bc = bc;
    vm->ip = 1;
    vm->stack = NULL; vm->stack_top = 0; vm->stack_cap = 0;
    vec_init(&vm->call_stack);
    vec_init(&vm->vars);
    vec_init(&vm->arrays);
    vm->data_ptr = 1;
    vm->print_col = 0;
    vm->zone_width = 14;
    vm->line_width = 80;
    vm->halted = false;
    return vm;
}

void vm_free(VM *vm) {
    for (int i = 0; i < vm->stack_top; ++i) v_release(&vm->stack[i]);
    free(vm->stack);
    vec_free(&vm->call_stack);
    for (int i = 0; i < vm->vars.len; ++i) {
        free(vm->vars.data[i].name);
        v_release(&vm->vars.data[i].value);
    }
    vec_free(&vm->vars);
    for (int i = 0; i < vm->arrays.len; ++i) {
        ArrSlot *a = &vm->arrays.data[i];
        free(a->name); free(a->dims);
        for (int k = 0; k < a->data_size; ++k) v_release(&a->data[k]);
        free(a->data);
    }
    vec_free(&vm->arrays);
    free(vm);
}

```

### C.17 src/main.c

```c
/* main.c : C GW-BASIC 인터프리터 진입점 */
#include "common.h"
#include "lexer.h"
#include "parser.h"
#include "compiler.h"
#include "vm.h"
#include <time.h>

static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) die("파일을 열 수 없습니다: %s", path);
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = (char*)xmalloc(n + 2);
    size_t r = fread(buf, 1, n, f); (void)r;
    buf[n] = '\n';
    buf[n+1] = 0;
    fclose(f);
    return buf;
}

static int run_source(const char *src) {
    Tokens t; vec_init(&t);
    lex(src, &t);
    AstNode *prog = parse(&t);
    Bytecode *bc = compile(prog);
    VM *vm = vm_new(bc);
    vm_run(vm);
    vm_free(vm);
    bytecode_free(bc);
    ast_free(prog);
    tokens_free(&t);
    return 0;
}

static void repl(void) {
    fputs("CGW-BASIC 1.0  --  종료: BYE\n", stdout);
    char *prog_buf = NULL;
    size_t prog_len = 0, prog_cap = 0;
    char line[1024];
    while (1) {
        fputs("Ok\n> ", stdout); fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) break;
        size_t L = strlen(line);
        while (L > 0 && (line[L-1] == '\n' || line[L-1] == '\r')) line[--L] = 0;
        if (L == 0) continue;
        if (str_ieq(line, "BYE") || str_ieq(line, "QUIT")) break;
        if (str_ieq(line, "RUN")) {
            if (prog_buf) run_source(prog_buf);
        } else if (str_ieq(line, "LIST")) {
            if (prog_buf) fputs(prog_buf, stdout);
        } else if (str_ieq(line, "NEW")) {
            free(prog_buf); prog_buf = NULL; prog_len = 0; prog_cap = 0;
        } else {
            int starts_with_digit = (line[0] >= '0' && line[0] <= '9');
            if (starts_with_digit) {
                size_t add = L + 2;
                if (prog_len + add >= prog_cap) {
                    prog_cap = (prog_cap + add) * 2;
                    prog_buf = (char*)xrealloc(prog_buf, prog_cap);
                }
                memcpy(prog_buf + prog_len, line, L);
                prog_buf[prog_len + L] = '\n';
                prog_buf[prog_len + L + 1] = 0;
                prog_len += L + 1;
            } else {
                /* 즉시 실행 */
                size_t need = L + 2;
                char *one = (char*)xmalloc(need);
                memcpy(one, line, L); one[L]='\n'; one[L+1]=0;
                run_source(one);
                free(one);
            }
        }
    }
    free(prog_buf);
}

int main(int argc, char **argv) {
    srand((unsigned)time(NULL));
    if (argc < 2) {
        repl();
    } else {
        char *src = read_file(argv[1]);
        run_source(src);
        free(src);
    }
    return 0;
}

```

### C.18 Makefile

```makefile
CC      ?= gcc
CFLAGS  ?= -O2 -std=c99 -Wall -Wextra -Wno-unused-parameter -Wno-unused-but-set-variable
LDLIBS  ?= -lm

SRC := src/common.c src/value.c src/lexer.c src/ast.c src/parser.c \
       src/runtime.c src/compiler.c src/vm.c src/main.c
OBJ := $(SRC:.c=.o)
BIN := cgwbasic

all: $(BIN)

$(BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(LDLIBS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJ) $(BIN)

run: $(BIN)
	./$(BIN) examples/hello.bas

test: $(BIN)
	@for f in examples/*.bas; do \
	  echo "=== $$f ==="; ./$(BIN) $$f; \
	done

.PHONY: all clean run test

```

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

### D.4 string_demo.bas

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

### D.5 data_demo.bas

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

### D.6 gosub_demo.bas

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

### D.7 ctrl_demo.bas

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

## 부록 E — 참고 문헌

- *Crafting Interpreters*, Robert Nystrom — C판 jlox/clox로 인터프리터를 두 번 만든다.
- *Writing An Interpreter In Go*, Thorsten Ball — 토큰부터 평가까지를 짧게.
- *Writing A Compiler In Go*, Thorsten Ball — 같은 언어를 바이트코드로.
- *Engineering a Compiler*, Cooper & Torczon — 컴파일러 이론서.
- *Modern Compiler Implementation in C*, Andrew Appel — C 기반 클래식.
- *The C Programming Language*, K&R — 여전히 가장 좋은 C 안내서.
- *21st Century C*, Ben Klemens — C99 이후의 실용 패턴.
- *The GW-BASIC User's Guide*, Microsoft, 1987 — 우리 흉내의 원본.
- *MS-BASIC sources* (microsoft/GW-BASIC, GitHub, 2020) — 어셈블리 원본.
- 한글 자료: 「만들면서 배우는 컴파일러」 — 국내 도서.

---

## 마치며

이 책의 자매편 「Lua판」을 쓰는 동안 저자는 세 번 “이 부분은 Lua라서 쉽다”고 적었다. 이 C판을 쓰는 동안엔 매 챕터에서 그 비슷한 생각을 했다. C에서는 모든 것이 명시적이다. 그러므로 모든 결정이 자기 것이다. 한 줄 한 줄에 이름을 매기고 free 시점을 정하고 인덱스의 1-base/0-base를 결정하는 그 모든 노동이, 결국에는 “이 데이터가 어떻게 흐르는지”를 가장 정직하게 보여 준다.

같은 VM 설계를 Lua와 C로 두 번 만들어 본 독자는 이제 “언어가 결정하는 것”과 “설계가 결정하는 것”을 가르는 감각을 얻었을 것이다. 다음 단계로는 이 VM을 다른 언어로 다시 한 번 옮겨 보길 권한다. Rust, Go, Zig, Swift, Kotlin — 어느 쪽으로 가도 좋다. 같은 다이어그램의 다섯 화살표가 세 번째 책의 골격이 될 것이다.

— *2026, 봄*
