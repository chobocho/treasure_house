# TypeScript로 만드는 GW-BASIC 인터프리터

## 완전 구현 가이드 — BNF부터 가상 머신까지

> 200페이지 분량의 실전 컴파일러 / 인터프리터 구현서

---

## 머리말

이 책은 1980년대 IBM PC 시절의 기념비적 언어인 **GW-BASIC**을 현대 TypeScript 환경에서 처음부터 구현해 보는 실전 가이드입니다. 단순히 BASIC을 흉내 내는 것이 아니라, 다음의 네 가지 단계를 모두 거치는 본격적인 언어 처리 시스템을 만듭니다.

1. **BNF 문법 정의** — GW-BASIC의 모든 문법 요소를 형식 언어로 기술
2. **Lexer / Parser** — 소스 코드를 토큰화하고 AST로 변환
3. **Bytecode Compiler** — AST를 자체 정의 바이트코드로 변환
4. **Virtual Machine** — 스택 기반 VM에서 바이트코드를 실행

결과물은 브라우저(HTML5 Canvas)와 Node.js 양쪽에서 동작합니다. SCREEN, LINE, CIRCLE, PSET, COLOR 같은 그래픽 명령어와 SOUND, PLAY 같은 사운드 명령어까지 동작하는 완전한 처리기를 만드는 것이 목표입니다.

### 이 책이 다루는 것

- 인터프리터 / 컴파일러의 이론적 기반
- 형식 문법(BNF)과 재귀 하강 파서
- Pratt 파서를 이용한 표현식 파싱
- 스택 기반 가상 머신 설계
- 변수 환경, 메모리 모델, 가비지 컬렉션
- GW-BASIC 고유 기능: 라인 번호, GOTO/GOSUB, FOR/NEXT, DEF FN, DATA/READ
- 그래픽 / 사운드 / 입출력 런타임
- REPL, 디버거, 테스트, 빌드 시스템

### 이 책이 다루지 않는 것

- TypeScript 언어 자체의 기초 (별도 학습 권장)
- DOS의 BIOS / 인터럽트 호환 (현대 환경에 맞춰 재해석)
- 카세트 테이프 / FAT12 입출력 (브라우저 IndexedDB로 대체)

### 대상 독자

- 컴파일러와 인터프리터의 동작 원리를 코드로 이해하고 싶은 개발자
- TypeScript로 중규모 시스템을 직접 만들어 보고 싶은 학습자
- 8비트 시절 BASIC에 대한 향수를 가진 분들
- 도메인 특화 언어(DSL)를 설계하려는 엔지니어

### 사용 방법

각 장은 **이론 → BNF / 설계 → 구현 → 테스트** 의 4단 구조로 진행됩니다. 코드는 언제나 작동하는 상태로 누적됩니다. 단순히 읽기보다는 직접 따라 치며 작성하기를 권합니다. 모든 소스는 다음 디렉터리 구조를 따릅니다.

```
ts_gwbasic/
├── src/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── compiler/
│   ├── vm/
│   ├── runtime/
│   └── main.ts
├── tests/
├── examples/
└── public/
    └── index.html
```

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
- **3장** TypeScript 개발 환경 구축 — Node, esbuild, Vitest
- **4장** 프로젝트 구조와 모듈 분리

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
- Thorsten Ball, *Writing an Interpreter in Go* / *Writing a Compiler in Go*.
- IBM, *PC BASIC Reference Manual*.

---

> "BASIC is to computer programming as QWERTY is to typing."  
> — Alan Kay (paraphrased)

다음 장에서는 GW-BASIC이라는 언어가 왜 그렇게 설계되었는지, 그 시절 환경의 제약을 이해하는 것에서부터 출발합니다.
# 제1부 · 기초

## 1장. GW-BASIC, 그 시절의 언어

### 1.1 등장 배경

1983년, IBM은 자사의 PC 호환 기종이 아닌 다른 OEM(컴팩, 탠디 등)에도 BASIC을 공급할 필요가 있었습니다. 기존 IBM Cassette BASIC, Disk BASIC, Advanced BASIC(BASICA)는 IBM PC의 ROM에 의존했습니다. 마이크로소프트는 ROM 의존성을 제거한 100% 디스크 기반 인터프리터를 만들었고, 이를 **GW-BASIC**이라 명명했습니다.

GW가 무엇의 약자인지에 대해서는 여러 설(Gee-Whiz, Gates-William, Greg Whitten 등)이 있지만 공식 입장은 없습니다. 본질은 *"BASICA의 ROM-less 클론"* 이라는 점입니다.

### 1.2 언어 철학

GW-BASIC은 다음 세 가지 원칙 위에 서 있습니다.

1. **즉시성 (Immediate mode)** — 라인 번호 없이 입력한 명령은 즉시 실행되고, 라인 번호와 함께 입력한 명령은 프로그램에 저장됩니다.
2. **단일 전역 환경** — 변수는 모두 전역. 스코프 개념이 사실상 없습니다 (DEF FN의 매개변수 정도가 예외).
3. **인터프리터 친화적 토큰화** — 키워드는 1바이트 토큰으로 압축 저장됩니다. 메모리가 64KB 단위로 귀했던 시절의 흔적입니다.

### 1.3 데이터 타입 체계

| 접미 기호 | 타입 | 크기 | 범위 |
|----------|------|------|------|
| `%` | INTEGER | 16비트 | -32768 ~ 32767 |
| `!` (생략) | SINGLE | 32비트 부동소수 | 약 7자리 정밀도 |
| `#` | DOUBLE | 64비트 부동소수 | 약 16자리 정밀도 |
| `$` | STRING | 가변 | 최대 255자 |

식별자 자체에 타입 접미가 붙는 점이 GW-BASIC의 독특한 특징입니다. `A%`, `A!`, `A#`, `A$`는 **모두 다른 변수**입니다.

### 1.4 라인 번호의 역할

```basic
10 PRINT "HELLO"
20 GOTO 10
```

라인 번호는 단순히 정렬 키가 아니라 **분기 대상 식별자**이기도 합니다. 우리는 후속 장에서 라인 번호를 별도의 심볼 테이블로 관리할 것입니다.

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

(숫자 앞의 공백 한 칸은 양수의 부호 자리입니다 — 7.5절 참고.)

본 구현에서도 REPL이 두 모드를 모두 지원하도록 설계합니다.

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
| 트리 워킹 인터프리터 | AST를 직접 순회 | 초기 Ruby, AST 기반 학습용 구현 |
| 바이트코드 VM | 중간 코드 컴파일 후 VM 실행 | Python, Lua, Ruby YARV, JVM |
| JIT 컴파일러 | 실행 중 네이티브 코드 생성 | V8, HotSpot |
| AOT 컴파일러 | 사전에 네이티브 생성 | C, Rust, Go |

우리는 **바이트코드 VM** 방식을 택합니다. 트리 워킹은 단순하지만 GOTO/GOSUB 같은 비구조적 제어 흐름을 다루기에 부자연스럽고, JIT은 학습 곡선이 너무 가파릅니다. 바이트코드 VM은 두 마리 토끼를 잡는 균형점입니다.

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

각 단계는 **순수 함수**에 가깝게 설계합니다. Lexer는 문자열을 받아 토큰 배열을 반환하고, Parser는 토큰 배열을 받아 AST를 반환하며, Compiler는 AST를 받아 명령어 배열을 반환합니다. 부수 효과는 VM에 격리됩니다.

### 2.3 각 단계의 책임

#### Lexer (Tokenizer)

```ts
const tokens = lex("10 PRINT 1+2");
// [
//   { type: "NUMBER", value: 10, line: 1, col: 1 },
//   { type: "KEYWORD", value: "PRINT", line: 1, col: 4 },
//   { type: "NUMBER", value: 1, line: 1, col: 10 },
//   { type: "OP", value: "+", line: 1, col: 11 },
//   { type: "NUMBER", value: 2, line: 1, col: 12 },
//   { type: "EOF", line: 1, col: 13 },
// ]
```

#### Parser

```ts
const ast = parse(tokens);
// Program {
//   lines: [
//     Line {
//       number: 10,
//       statements: [
//         PrintStmt {
//           args: [ BinaryExpr { op: "+", lhs: 1, rhs: 2 } ]
//         }
//       ]
//     }
//   ]
// }
```

#### Compiler

```ts
const program = compile(ast);
// instructions: [
//   PUSH_NUM 1
//   PUSH_NUM 2
//   ADD
//   PRINT
//   END
// ]
// lineMap: Map { 10 => 0 }   // 라인 10은 명령어 인덱스 0번부터
```

#### VM

```ts
const vm = new VM(program, host);
vm.run();
// → " 3 " 출력 후 줄바꿈 (host.printAt / host.println)
```

### 2.4 호스트 인터페이스 (Host)

VM은 *외부 세계*와 통신하기 위해 **Host** 인터페이스를 사용합니다. 이렇게 분리하면 Node.js 콘솔, 브라우저 Canvas, 테스트용 Mock 등 어떤 환경에서도 같은 VM이 동작합니다.

```ts
// src/host/host.ts — 이 인터페이스가 VM·테스트 mock·CanvasHost가 공유하는 최종 계약이다
export interface Host {
  // 텍스트 입출력
  printAt(s: string): void;                 // 커서 위치에 출력 (컬럼 추적 포함)
  println(s: string): void;
  column(): number;                         // 현재 커서 컬럼 (1-based)
  row(): number;                            // 현재 커서 행 (1-based)
  inputLine(prompt: string): Promise<string | null>;
  inkey(): string;                          // 비차단 키 입력 (없으면 "")
  // 화면 제어
  cls(mode: number): void;
  setScreen(mode: number): void;
  setColor(fg: number | null, bg: number | null): void;
  locate(row: number | null, col: number | null): void;
  // 그래픽
  pset(x: number, y: number, color: number | null, step: boolean, preset: boolean): void;
  drawLine(x1: number | null, y1: number | null, x2: number, y2: number,
           color: number | null, fromStep: boolean, toStep: boolean,
           mode: "B" | "BF" | null): void;
  drawCircle(x: number, y: number, r: number, color: number | null,
             start: number | null, end: number | null,
             aspect: number | null, step: boolean): void;
  paint(x: number, y: number, fill: number | null, border: number | null, step: boolean): void;
  // 사운드
  sound(freq: number, durationMs: number): Promise<void>;
  play(mml: string): Promise<void>;
  // 시간 / 난수
  now(): number;
  random(): number;
  lastRandom(): number;
  seedRandom(s: number): void;
}
```

⚠️ **주의**: Host는 가능하면 **얇게** 유지합니다. BASIC 명령 하나에 메서드 하나가 일대일로 대응될 필요는 없습니다. 예를 들어 `LINE`은 내부적으로 `pset`을 반복 호출해도 충분합니다. 그러나 성능이 중요한 그래픽 명령은 Host에 직접 위임하는 편이 빠릅니다. 이 균형은 27장에서 다룹니다.

---

## 3장. TypeScript 개발 환경 구축

### 3.1 도구 선택

- **런타임**: Node.js 20 이상 (또는 Bun)
- **언어**: TypeScript 5.4 이상
- **번들러**: esbuild — 빠르고 설정이 거의 필요 없음
- **테스트**: Vitest — Jest 호환 + ESM 친화적
- **린트**: ESLint + Prettier (선택)

### 3.2 초기 프로젝트 생성

```bash
mkdir ts_gwbasic && cd ts_gwbasic
npm init -y
npm i -D typescript @types/node esbuild vitest tsx
npx tsc --init --target ES2022 --module ESNext --moduleResolution Bundler \
  --strict --esModuleInterop --skipLibCheck --outDir dist
```

생성된 `tsconfig.json`을 다음과 같이 다듬습니다.

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "outDir": "dist",
    "rootDir": "src",
    "lib": ["ES2022", "DOM"]
  },
  "include": ["src", "tests"]
}
```

💡 **팁**: `noUncheckedIndexedAccess`를 켜면 `arr[i]`의 결과가 `T | undefined`가 되어 안전합니다. 처음에는 귀찮지만, VM이나 파서에서 인덱스 실수를 컴파일 시점에 잡아 줍니다.

### 3.3 package.json 스크립트

```json
{
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/main.ts",
    "build": "esbuild src/main.ts --bundle --outfile=dist/dist.js --format=esm --target=es2022",
    "build:web": "esbuild src/web.ts --bundle --outfile=public/dist.js --format=iife --target=es2022",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

CLAUDE.md 규칙에 따라 `dist.js` 단일 산출물이 나오도록 했습니다.

### 3.4 디렉터리 만들기

```bash
mkdir -p src/{lexer,parser,ast,compiler,vm,runtime,host}
mkdir -p tests examples public data
```

### 3.5 첫 실행 확인

`src/main.ts`:

```ts
console.log("GW-BASIC TS bootstrap OK");
```

```bash
npm run dev
# → GW-BASIC TS bootstrap OK
```

여기까지 동작하면 환경은 준비된 것입니다.

---

## 4장. 프로젝트 구조와 모듈 분리

### 4.1 모듈 의존 그래프

```
main.ts
  ├── repl.ts
  │     ├── lexer/
  │     ├── parser/
  │     ├── compiler/
  │     ├── vm/
  │     └── host/
  │
  └── runner.ts (배치 실행)

각 단계는 위에서 아래로만 의존:
  lexer → parser → ast → compiler → vm → runtime
                                 ↑
                                 host
```

순환 의존을 만들지 않는 것이 핵심입니다. AST는 parser와 compiler가 공유하지만, AST 자체는 어떤 다른 모듈도 import 하지 않습니다.

### 4.2 공통 타입 (src/common/types.ts)

```ts
export interface SourcePos {
  line: number;
  col: number;
}

export class BasicError extends Error {
  constructor(
    public code: number,
    message: string,
    public pos?: SourcePos,
    public basicLine?: number,
  ) {
    super(message);
  }
}

export const ERR = {
  SYNTAX: 2,
  RETURN_WITHOUT_GOSUB: 3,
  OUT_OF_DATA: 4,
  ILLEGAL_FUNCTION_CALL: 5,
  OVERFLOW: 6,
  OUT_OF_MEMORY: 7,
  UNDEFINED_LINE_NUMBER: 8,
  SUBSCRIPT_OUT_OF_RANGE: 9,
  DUPLICATE_DEFINITION: 10,
  TYPE_MISMATCH: 13,
  STRING_TOO_LONG: 15,
  DIVISION_BY_ZERO: 11,
  NEXT_WITHOUT_FOR: 1,
  FOR_WITHOUT_NEXT: 26,
} as const;
```

GW-BASIC의 표준 에러 코드를 그대로 가져옵니다. 부록 C에 전체 표가 있습니다.

### 4.3 코딩 컨벤션

CLAUDE.md를 따릅니다.

- 변수: `camelCase`
- 클래스: `PascalCase`
- 상수: `UPPER_SNAKE`
- 파일: `kebab-case` 또는 `lowercase`
- import는 절대 경로보다 상대 경로(`./`, `../`) 우선
- 모듈 간 데이터는 `interface`로, 동작은 `class`로

### 4.4 다음 단계 미리 보기

다음 장(5장)에서는 GW-BASIC의 BNF 문법을 *전체*로 정의합니다. 이것이 책 전체의 설계도 역할을 합니다. BNF가 머릿속에 들어와야 Lexer, Parser, Compiler를 일관성 있게 만들 수 있습니다.

> 1부 끝.
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
              | <for-stmt>
              | <next-stmt>
              | <while-stmt>
              | <wend-stmt>
              | <goto-stmt>
              | <gosub-stmt>
              | <return-stmt>
              | <end-stmt>
              | <stop-stmt>
              | <rem-stmt>
              | <dim-stmt>
              | <data-stmt>
              | <read-stmt>
              | <restore-stmt>
              | <def-fn-stmt>
              | <on-goto-stmt>
              | <on-gosub-stmt>
              | <cls-stmt>
              | <screen-stmt>
              | <color-stmt>
              | <pset-stmt>
              | <line-stmt>
              | <circle-stmt>
              | <paint-stmt>
              | <locate-stmt>
              | <sound-stmt>
              | <play-stmt>
              | <beep-stmt>
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
<if-stmt>    ::= "IF" <expression> "THEN" <then-clause> [ "ELSE" <else-clause> ]
<then-clause> ::= <line-number>
                | <statement-list>
<else-clause> ::= <line-number>
                | <statement-list>
```

⚠️ THEN 뒤에 라인 번호가 오면 `GOTO`와 같습니다. `IF X=1 THEN 100 ELSE 200`.

#### FOR / NEXT

```ebnf
<for-stmt>   ::= "FOR" <variable> "=" <expression> "TO" <expression>
                 [ "STEP" <expression> ]
<next-stmt>  ::= "NEXT" [ <variable> { "," <variable> } ]
```

#### WHILE / WEND

```ebnf
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

#### 데이터

```ebnf
<dim-stmt>      ::= "DIM" <dim-decl> { "," <dim-decl> }
<dim-decl>      ::= <variable> "(" <expression> { "," <expression> } ")"
<data-stmt>     ::= "DATA" <data-item> { "," <data-item> }
<data-item>     ::= <number> | <string> | <bare-string>
<read-stmt>     ::= "READ" <lvalue> { "," <lvalue> }
<restore-stmt>  ::= "RESTORE" [ <line-number> ]
```

#### 정의

```ebnf
<def-fn-stmt> ::= "DEF" "FN" <ident> [ "(" <param-list> ")" ] "=" <expression>
<param-list>  ::= <variable> { "," <variable> }
```

#### 종료 / 기타

```ebnf
<end-stmt>   ::= "END"
<stop-stmt>  ::= "STOP"
<rem-stmt>   ::= "REM" /.*/
               | "'" /.*/
<clear-stmt> ::= "CLEAR"
<randomize-stmt> ::= "RANDOMIZE" [ <expression> ]
<swap-stmt>  ::= "SWAP" <variable> "," <variable>
```

#### 그래픽 (제27장에서 자세히)

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
```

#### 사운드

```ebnf
<sound-stmt> ::= "SOUND" <expression> "," <expression>
<play-stmt>  ::= "PLAY" <string-expr>
<beep-stmt>  ::= "BEEP"
```

### 5.4 표현식

```ebnf
<expression>     ::= <or-expr>
<or-expr>        ::= <xor-expr>  { "OR"  <xor-expr> }
<xor-expr>       ::= <and-expr>  { "XOR" <and-expr> }
<and-expr>       ::= <not-expr>  { "AND" <not-expr> }
<not-expr>       ::= [ "NOT" ] <rel-expr>
<rel-expr>       ::= <add-expr> [ <rel-op> <add-expr> ]
<rel-op>         ::= "=" | "<>" | "<" | "<=" | ">" | ">="
<add-expr>       ::= <mod-expr>  { ("+" | "-") <mod-expr> }
<mod-expr>       ::= <intdiv-expr> { "MOD" <intdiv-expr> }
<intdiv-expr>    ::= <mul-expr>  { "\\" <mul-expr> }
<mul-expr>       ::= <unary-expr> { ("*" | "/") <unary-expr> }
<unary-expr>     ::= ("+" | "-") <unary-expr> | <pow-expr>
<pow-expr>       ::= <primary> { "^" <unary-expr> }        (* 우결합 *)
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
- 원본 GW-BASIC은 키워드 사이에 공백이 없어도 됨: `FORI=1TO10` ← 합법 (키워드 최장 일치 크런치). 본 구현의 Lexer는 *식별자* 최장 일치를 쓰므로 키워드 **앞**에는 공백이 필요합니다 — 6.2절의 완화와 같은 결정

이런 점들 때문에 Lexer에는 약간의 *문맥* 이 필요합니다. 9장에서 전략을 다룹니다.

---

## 6장. 어휘 단위 — 키워드, 식별자, 리터럴

### 6.1 키워드 목록

본 구현에서 인식하는 키워드는 다음과 같습니다 (대문자 정규화 후 비교).

```
ABS  AND  AS  ASC  ATN  AUTO  BEEP  BLOAD  BSAVE  CALL  CDBL  CHAIN  CHR$  CINT
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

### 6.2 식별자 규칙

- 첫 글자: 영문자
- 두 번째 이후: 영문자 또는 숫자
- 길이: 40자까지
- 마지막에 타입 접미(`%`, `!`, `#`, `$`) 가능
- 키워드와 같은 이름 금지(부분 포함도 금지: `PRINTER`는 `PRINT`로 시작하므로 금지 — 단, 본 구현에서는 완화)

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

TypeScript에서 우리는 다음과 같이 모델링합니다.

```ts
// src/runtime/value.ts
export type BasicType = "INT" | "SNG" | "DBL" | "STR";

export type BasicValue =
  | { tag: "INT"; v: number }   // 16비트 범위 보장
  | { tag: "SNG"; v: number }
  | { tag: "DBL"; v: number }
  | { tag: "STR"; v: string };

export const INT = (v: number): BasicValue => ({ tag: "INT", v: v | 0 });
export const SNG = (v: number): BasicValue => ({ tag: "SNG", v: Math.fround(v) });
export const DBL = (v: number): BasicValue => ({ tag: "DBL", v });
export const STR = (v: string): BasicValue => ({ tag: "STR", v });
```

💡 `Math.fround(v)`로 SINGLE 정밀도를 흉내 냅니다. `1/3` 이 `0.3333333432674408`이 되는 등, 원래의 32비트 부동소수 동작이 재현됩니다.

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

본 구현에서는 JavaScript 문자열의 자연스러운 크기를 그대로 쓰되, BASIC 단일 변수에 할당될 때 255자를 넘으면 `String too long` 에러를 던지는 검사 함수를 둡니다.

```ts
export function checkStringLen(s: string): void {
  if (s.length > 255) {
    throw new BasicError(ERR.STRING_TOO_LONG, "String too long");
  }
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

이 정의를 보면 `^`의 오른쪽 피연산자에서는 다시 단항 부호가 허용됩니다(`2^-3 = 0.125`). 그러나 왼쪽에서는 `-2^2`가 `-(2^2) = -4`가 됩니다. Pratt 파서로 표현하면 단항 `-`의 결합력을 `^`보다 *낮게* 설정합니다.

### 8.3 부울 동작

GW-BASIC의 부울은 **-1(true)** 와 **0(false)** 입니다. 그런데 `AND`, `OR`, `NOT`은 *비트* 연산자이기도 합니다.

- `5 AND 3 = 1` (비트 AND)
- `-1 AND 7 = 7` (true AND 7)
- `NOT 0 = -1`, `NOT 1 = -2`

따라서 `IF X = 1 AND Y = 2`는 `IF (X=1) AND (Y=2)`로 정확히 동작합니다(둘 다 -1이면 -1, 한쪽이 0이면 0).

### 8.4 정수 나눗셈과 MOD

```basic
PRINT 10 / 3      ' 3.333333
PRINT 10 \ 3      ' 3
PRINT 10 MOD 3    ' 1
PRINT -7 \ 2      ' -3   (0 방향)
PRINT -7 MOD 2    ' -1
```

⚠️ 정수 나눗셈은 피연산자를 먼저 INTEGER로 변환한 후 수행합니다(범위 초과면 오버플로).

### 8.5 문자열 연산

`+`만 지원합니다 (연결).

```basic
A$ = "Hello, " + "World"
```

다른 산술 연산자에 문자열을 넣으면 `Type Mismatch`.

### 8.6 비교 연산

수치-수치, 문자열-문자열만 가능. 문자열은 사전식 비교 (ASCII 코드 순).

```basic
PRINT "ABC" < "ABD"     ' -1
PRINT "abc" < "ABC"     ' 0  (소문자가 더 큼)
```

---

> 2부 끝. 이로써 우리가 만들 언어의 모습이 분명해졌습니다. 이제 3부에서는 이 명세를 *실행 가능한 코드*로 옮깁니다.
# 제3부 · 프론트엔드 (1) — Lexer

## 9장. Lexer 완전 구현

### 9.1 토큰 타입 정의

가장 먼저 토큰의 형태를 정의합니다. `src/lexer/token.ts`:

```ts
// src/lexer/token.ts
export type TokenType =
  | "NUMBER"
  | "STRING"
  | "IDENT"
  | "KEYWORD"
  | "OP"
  | "LPAREN" | "RPAREN"
  | "COMMA" | "SEMICOLON" | "COLON"
  | "EOL" | "EOF"
  | "REM_TEXT";

export interface Token {
  type: TokenType;
  value: string;          // 원시 텍스트
  num?: number;           // NUMBER일 때 파싱된 값
  numType?: "INT" | "SNG" | "DBL";
  line: number;           // 1-based
  col: number;            // 1-based
}

export const KEYWORDS = new Set<string>([
  "ABS","AND","AS","ASC","ATN","BEEP","CHR$","CIRCLE","CINT","CLEAR","CLS",
  "COLOR","COS","CSNG","CSRLIN","CDBL","DATA","DEF","DEFINT","DEFSNG","DEFDBL",
  "DEFSTR","DIM","ELSE","END","EQV","ERASE","ERL","ERR","EXP","FIX","FN","FOR",
  "GOSUB","GOTO","HEX$","IF","IMP","INKEY$","INPUT","INSTR","INT","LEFT$",
  "LEN","LET","LINE","LIST","LOAD","LOCATE","LOG","MID$","MOD","NEW",
  "NEXT","NOT","OCT$","OFF","ON","OR","PAINT","PLAY","POS","PRESET","PRINT",
  "PSET","RANDOMIZE","READ","REM","RESTORE","RETURN","RIGHT$","RND",
  "RUN","SAVE","SCREEN","SGN","SIN","SOUND","SPACE$","SPC","SQR","STEP",
  "STOP","STR$","STRING$","SWAP","SYSTEM","TAB","TAN","THEN","TIMER",
  "TO","USING","VAL","WEND","WHILE","XOR",
]);

export const TWO_CHAR_OPS = new Set(["<=", ">=", "<>"]);
export const SINGLE_OPS  = new Set(["+", "-", "*", "/", "\\", "^", "=", "<", ">"]);
```

### 9.2 Lexer 클래스 골격

```ts
// src/lexer/lexer.ts
import { Token, KEYWORDS, TWO_CHAR_OPS, SINGLE_OPS } from "./token.js";
import { BasicError, ERR } from "../common/types.js";

export class Lexer {
  private pos = 0;
  private line = 1;
  private col = 1;
  private src: string;
  private tokens: Token[] = [];

  constructor(src: string) {
    this.src = src;
  }

  static tokenize(src: string): Token[] {
    return new Lexer(src).run();
  }

  run(): Token[] {
    while (this.pos < this.src.length) {
      this.scanToken();
    }
    this.push("EOF", "");
    return this.tokens;
  }

  // ─── 보조 ─────────────────────────────────────────
  private peek(off = 0): string {
    return this.src[this.pos + off] ?? "";
  }

  private advance(): string {
    const ch = this.src[this.pos++] ?? "";
    if (ch === "\n") { this.line++; this.col = 1; }
    else { this.col++; }
    return ch;
  }

  private push(type: Token["type"], value: string, extra: Partial<Token> = {}): void {
    this.tokens.push({
      type, value,
      line: this.line, col: this.col - value.length,
      ...extra,
    });
  }

  private err(msg: string): never {
    throw new BasicError(ERR.SYNTAX, msg, { line: this.line, col: this.col });
  }
}
```

### 9.3 메인 스캐너

```ts
private scanToken(): void {
  const ch = this.peek();

  // 공백 스킵 (개행 제외)
  if (ch === " " || ch === "\t" || ch === "\r") {
    this.advance();
    return;
  }

  // 개행 → EOL
  if (ch === "\n") {
    this.advance();
    this.push("EOL", "\n");
    return;
  }

  // 코멘트
  if (ch === "'") {
    this.scanRem();
    return;
  }

  // 숫자
  if (this.isDigit(ch) || (ch === "." && this.isDigit(this.peek(1)))) {
    this.scanNumber();
    return;
  }

  // 16진수 / 8진수
  if (ch === "&") {
    this.scanRadixNumber();
    return;
  }

  // 문자열
  if (ch === '"') {
    this.scanString();
    return;
  }

  // 식별자 / 키워드
  if (this.isAlpha(ch)) {
    this.scanIdentOrKeyword();
    return;
  }

  // 구두점
  switch (ch) {
    case "(": this.advance(); this.push("LPAREN", "("); return;
    case ")": this.advance(); this.push("RPAREN", ")"); return;
    case ",": this.advance(); this.push("COMMA", ","); return;
    case ";": this.advance(); this.push("SEMICOLON", ";"); return;
    case ":": this.advance(); this.push("COLON", ":"); return;
    case "?": this.advance(); this.push("KEYWORD", "PRINT"); return;
  }

  // 두 글자 연산자
  const two = ch + this.peek(1);
  if (TWO_CHAR_OPS.has(two)) {
    this.advance(); this.advance();
    this.push("OP", two);
    return;
  }

  // 한 글자 연산자
  if (SINGLE_OPS.has(ch)) {
    this.advance();
    this.push("OP", ch);
    return;
  }

  this.err(`Unexpected character: ${JSON.stringify(ch)}`);
}

private isDigit(ch: string): boolean { return ch >= "0" && ch <= "9"; }
private isAlpha(ch: string): boolean {
  return (ch >= "A" && ch <= "Z") || (ch >= "a" && ch <= "z");
}
private isAlnum(ch: string): boolean { return this.isAlpha(ch) || this.isDigit(ch); }
```

### 9.4 숫자 스캐너

```ts
private scanNumber(): void {
  const startCol = this.col;
  let s = "";
  let hasDot = false, hasExp = false;
  let typeHint: "INT" | "SNG" | "DBL" = "INT";

  // 정수 부분
  while (this.isDigit(this.peek())) s += this.advance();

  // 소수점
  if (this.peek() === ".") {
    hasDot = true;
    s += this.advance();
    while (this.isDigit(this.peek())) s += this.advance();
  }

  // 지수
  const e = this.peek().toUpperCase();
  if (e === "E" || e === "D") {
    hasExp = true;
    typeHint = (e === "D") ? "DBL" : "SNG";
    s += this.advance();
    if (this.peek() === "+" || this.peek() === "-") s += this.advance();
    if (!this.isDigit(this.peek())) this.err("Malformed exponent");
    while (this.isDigit(this.peek())) s += this.advance();
  }

  // 타입 접미
  const suffix = this.peek();
  if (suffix === "%") { this.advance(); typeHint = "INT"; }
  else if (suffix === "!") { this.advance(); typeHint = "SNG"; }
  else if (suffix === "#") { this.advance(); typeHint = "DBL"; }
  else if (!hasDot && !hasExp) {
    // 정수처럼 보이지만 32767 초과면 SNG로 승격
    const v = parseInt(s, 10);
    typeHint = (v > 32767 || v < -32768) ? "SNG" : "INT";
  } else {
    if (typeHint === "INT") typeHint = "SNG";
  }

  // E 표기를 D로 정규화하지 않고 그대로 parseFloat
  const numeric = parseFloat(s.replace(/D/i, "E"));
  this.tokens.push({
    type: "NUMBER",
    value: s,
    num: numeric,
    numType: typeHint,
    line: this.line,
    col: startCol,
  });
}

private scanRadixNumber(): void {
  const startCol = this.col;
  this.advance(); // &
  let radix = 8;
  let prefix = "&";
  if (this.peek().toUpperCase() === "H") { radix = 16; prefix += "H"; this.advance(); }
  else if (this.peek().toUpperCase() === "O") { prefix += "O"; this.advance(); }

  let s = "";
  const isDigitOk = (ch: string): boolean => {
    if (radix === 16) return /[0-9A-Fa-f]/.test(ch);
    return /[0-7]/.test(ch);
  };
  while (isDigitOk(this.peek())) s += this.advance();
  if (s.length === 0) this.err("Bad &-literal");

  const v = parseInt(s, radix);
  this.tokens.push({
    type: "NUMBER",
    value: prefix + s,
    num: v,
    numType: "INT",
    line: this.line,
    col: startCol,
  });
}
```

### 9.5 문자열 스캐너

```ts
private scanString(): void {
  const startCol = this.col;
  this.advance(); // "
  let s = "";
  while (this.peek() !== '"' && this.peek() !== "\n" && this.peek() !== "") {
    s += this.advance();
  }
  if (this.peek() !== '"') this.err("Unterminated string");
  this.advance(); // 닫는 "
  this.tokens.push({
    type: "STRING",
    value: s,
    line: this.line,
    col: startCol,
  });
}
```

### 9.6 식별자 / 키워드

```ts
private scanIdentOrKeyword(): void {
  const startCol = this.col;
  let s = "";
  while (this.isAlnum(this.peek())) s += this.advance();
  // 타입 접미 흡수 (식별자에 한해)
  const suffix = this.peek();
  let withSuffix = s;
  if (suffix === "$" || suffix === "%" || suffix === "!" || suffix === "#") {
    withSuffix += this.advance();
  }

  const upper = withSuffix.toUpperCase();

  // 키워드 검사 (접미 포함 여부 둘 다)
  if (KEYWORDS.has(upper)) {
    // REM은 특별 처리
    if (upper === "REM") {
      this.tokens.push({ type: "KEYWORD", value: "REM", line: this.line, col: startCol });
      this.scanRemRest();
      return;
    }
    this.tokens.push({ type: "KEYWORD", value: upper, line: this.line, col: startCol });
    return;
  }

  this.tokens.push({
    type: "IDENT",
    value: withSuffix,
    line: this.line,
    col: startCol,
  });
}

private scanRem(): void {
  this.advance(); // '
  this.scanRemRest();
}

private scanRemRest(): void {
  let s = "";
  while (this.peek() !== "\n" && this.peek() !== "") s += this.advance();
  this.tokens.push({ type: "REM_TEXT", value: s, line: this.line, col: this.col });
}
```

### 9.7 키워드 충돌 처리

`PRINT`, `END`, `INT` 같은 키워드를 식별자로 쓸 수 없는 것은 명확합니다. 그러나 `LEFT$`, `MID$` 처럼 `$`를 포함한 *함수형 키워드*는 식별자처럼 보입니다. 우리는 두 가지 전략을 씁니다.

1. 토큰화 시 식별자 + 접미를 합쳐 한 단어로 만든 후, 키워드 집합에 있으면 KEYWORD로 분류.
2. `INT`, `LEN` 같은 *접미 없는* 함수명도 KEYWORD로 분류. 사용자는 같은 이름을 변수로 쓸 수 없게 됩니다 (BASIC 표준).

⚠️ 이 결정으로 사용자가 `INT = 5` 라고 쓰면 파싱 에러가 납니다. 이는 GW-BASIC 동작과 동일합니다.

### 9.8 라인 번호의 처리

라인 번호 자체는 별도의 토큰 타입이 아니라 **라인 시작 위치의 NUMBER 토큰**으로 표현됩니다. Parser가 줄 시작에서 NUMBER를 만나면 라인 번호로 해석합니다.

### 9.9 테스트

`tests/lexer.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { Lexer } from "../src/lexer/lexer.js";

describe("Lexer", () => {
  it("기본 토큰 인식", () => {
    const t = Lexer.tokenize('10 PRINT "HELLO", A%+1');
    const types = t.map(x => x.type);
    expect(types).toEqual([
      "NUMBER","KEYWORD","STRING","COMMA","IDENT","OP","NUMBER","EOF"
    ]);
    expect(t[0].num).toBe(10);
    expect(t[2].value).toBe("HELLO");
    expect(t[4].value).toBe("A%");
  });

  it("16진수 / 8진수", () => {
    const t = Lexer.tokenize("&H1A &O17 &7");
    expect(t[0].num).toBe(26);
    expect(t[1].num).toBe(15);
    expect(t[2].num).toBe(7);
  });

  it("REM은 줄 끝까지", () => {
    const t = Lexer.tokenize("10 REM hello world\n20 PRINT 1");
    expect(t.find(x => x.type === "REM_TEXT")?.value).toBe(" hello world");
  });

  it("작은따옴표 코멘트", () => {
    const t = Lexer.tokenize("10 PRINT 1 ' tail comment");
    const rem = t.find(x => x.type === "REM_TEXT");
    expect(rem?.value).toBe(" tail comment");
  });

  it("두 글자 연산자", () => {
    const t = Lexer.tokenize("A <= B >= C <> D");
    const ops = t.filter(x => x.type === "OP").map(x => x.value);
    expect(ops).toEqual(["<=", ">=", "<>"]);
  });

  it("부동소수와 지수", () => {
    const t = Lexer.tokenize("3.14 1.5E10 .5#");
    expect(t[0].num).toBeCloseTo(3.14);
    expect(t[1].num).toBe(1.5e10);
    expect(t[2].numType).toBe("DBL");
  });

  it("? → PRINT 변환", () => {
    const t = Lexer.tokenize("? 1");
    expect(t[0].value).toBe("PRINT");
  });
});
```

### 9.10 엣지 케이스 정리

| 입력 | 토큰 | 비고 |
|------|------|------|
| `100A=1` | NUMBER(100), IDENT(A), OP(=), NUMBER(1) | 라인 100, A=1 |
| `IF A=1THEN` | KEYWORD(IF), IDENT(A), OP(=), NUMBER(1), KEYWORD(THEN) | 숫자 *뒤* 키워드는 공백 불요. `IFA=...`는 IDENT(IFA)로 읽힘 (5.7절) |
| `A$="x"` | IDENT(A$), OP(=), STRING("x") | $는 식별자에 흡수 |
| `1.E5` | NUMBER(100000) | `1.` 도 부동소수 |
| `.5` | NUMBER(0.5) | 정수부 생략 가능 |
| `&H10` | NUMBER(16) | 16진수 |

### 9.11 성능 노트

Lexer는 한 번 만들고 버리는 객체로 설계했지만, 큰 프로그램에서는 **재할당을 줄이는** 것이 중요합니다.

- `tokens.push`는 V8에서 매우 빠름 (배열 grow 비용은 amortized O(1))
- 문자열 추가는 가능하면 `s += ch` 보다 `chars.push(ch); chars.join("")` 가 빠를 수 있으나, 짧은 토큰에서는 차이가 미미
- 정규식보다 *문자 비교* 가 일반적으로 빠름

본 구현은 가독성을 우선했지만, 1만 라인 이상의 BASIC 프로그램에서도 수십 ms 안에 토큰화가 끝납니다.

### 9.12 다음 장 예고

10장에서는 이 토큰 스트림을 받아 AST를 만드는 Parser의 골격을 세웁니다. *재귀 하강* 방식으로 시작해, 표현식 부분만 *Pratt* 알고리즘으로 전환하는 하이브리드 구조입니다.

---

> 9장 끝.
# 제3부 · 프론트엔드 (2) — Parser와 AST

## 10장. Parser 기초 — 재귀 하강

### 10.1 파서의 역할

Parser는 토큰 시퀀스를 받아 **추상 구문 트리(AST)** 를 만듭니다. 우리는 두 가지 기법을 결합합니다.

- **재귀 하강 (Recursive descent)**: 문장 단위 파싱
- **Pratt parsing**: 표현식 단위 파싱 (연산자 우선순위)

### 10.2 토큰 커서

```ts
// src/parser/cursor.ts
import { Token } from "../lexer/token.js";
import { BasicError, ERR } from "../common/types.js";

export class Cursor {
  private i = 0;
  constructor(private tokens: Token[]) {}

  peek(off = 0): Token {
    return this.tokens[this.i + off] ?? this.tokens[this.tokens.length - 1]!;
  }

  next(): Token {
    return this.tokens[this.i++] ?? this.tokens[this.tokens.length - 1]!;
  }

  check(type: string, value?: string): boolean {
    const t = this.peek();
    if (t.type !== type) return false;
    if (value !== undefined && t.value !== value) return false;
    return true;
  }

  match(type: string, value?: string): boolean {
    if (!this.check(type, value)) return false;
    this.next();
    return true;
  }

  expect(type: string, value?: string): Token {
    if (!this.check(type, value)) {
      const t = this.peek();
      throw new BasicError(
        ERR.SYNTAX,
        `Expected ${type}${value ? `(${value})` : ""}, got ${t.type}(${t.value})`,
        { line: t.line, col: t.col },
      );
    }
    return this.next();
  }

  isEOF(): boolean { return this.peek().type === "EOF"; }
  isEOL(): boolean { return this.peek().type === "EOL" || this.isEOF(); }
}
```

### 10.3 AST 노드 (요약)

상세 정의는 13장에 모아 둡니다. 여기서는 시그니처만:

```ts
// src/ast/nodes.ts (일부)
export type Stmt =
  | AssignStmt | PrintStmt | InputStmt
  | IfStmt | ForStmt | NextStmt
  | WhileStmt | WendStmt
  | GotoStmt | GosubStmt | ReturnStmt | OnGotoStmt
  | EndStmt | StopStmt | RemStmt
  | DimStmt | DataStmt | ReadStmt | RestoreStmt
  | DefFnStmt
  | ClsStmt | ScreenStmt | ColorStmt | LocateStmt
  | PsetStmt | LineStmt | CircleStmt | PaintStmt
  | SoundStmt | PlayStmt | BeepStmt
  | RandomizeStmt | ClearStmt | SwapStmt;

export type Expr =
  | NumLit | StrLit | VarRef | ArrayRef | FnCall
  | UnaryExpr | BinaryExpr;

export interface ProgramLine {
  number: number | null;     // null이면 직접 모드
  statements: Stmt[];
  sourceLine: number;
}

export interface Program {
  lines: ProgramLine[];
}
```

### 10.4 메인 파싱 루프

```ts
// src/parser/parser.ts
import { Cursor } from "./cursor.js";
import { Token } from "../lexer/token.js";
import * as A from "../ast/nodes.js";
import { BasicError, ERR } from "../common/types.js";
import { parseExpression } from "./expr.js";
import { parseStatement } from "./stmt.js";

export class Parser {
  cur: Cursor;

  constructor(tokens: Token[]) {
    this.cur = new Cursor(tokens);
  }

  parseProgram(): A.Program {
    const lines: A.ProgramLine[] = [];
    while (!this.cur.isEOF()) {
      // 빈 줄 스킵
      if (this.cur.match("EOL")) continue;

      const line = this.parseLine();
      lines.push(line);
    }
    return { lines };
  }

  parseLine(): A.ProgramLine {
    const first = this.cur.peek();
    let number: number | null = null;

    // 줄 시작 NUMBER → 라인 번호
    if (first.type === "NUMBER" && first.col === 1) {
      number = first.num! | 0;
      this.cur.next();
    } else if (first.type === "NUMBER") {
      // 줄 시작은 아니지만 첫 토큰이 숫자인 경우도 라인 번호로 인정
      // (Lexer가 col 정보를 정확히 줄 시작에 매겨 두므로 1=시작)
      number = first.num! | 0;
      this.cur.next();
    }

    const statements: A.Stmt[] = [];

    // 첫 문장
    statements.push(parseStatement(this.cur));

    // 콜론으로 이어지는 문장들
    while (this.cur.match("COLON")) {
      if (this.cur.isEOL()) break;
      statements.push(parseStatement(this.cur));
    }

    // 문장 끝에 붙은 ' 코멘트 (REM_TEXT) 흡수
    // 이것이 없으면 `PRINT 1 ' 코멘트` 같은 줄이 Syntax error가 된다
    if (this.cur.peek().type === "REM_TEXT") {
      statements.push({ kind: "Rem", text: this.cur.next().value });
    }

    // EOL 소비
    if (!this.cur.isEOF()) this.cur.expect("EOL");

    return { number, statements, sourceLine: first.line };
  }
}
```

### 10.5 분리 전략

문장 파서(`parseStatement`)와 표현식 파서(`parseExpression`)를 별도 파일로 둡니다. 이유는 *코드 양*과 *재사용성*입니다. 표현식 파서는 IF, PRINT, INPUT, FOR, LET 등 거의 모든 문장에서 호출됩니다.

---

## 11장. 표현식 파싱 — Pratt 알고리즘

### 11.1 왜 Pratt인가

전통적 재귀 하강으로 `or-expr → xor-expr → and-expr → not-expr → ...` 식으로 12단계 함수를 만들면 깊고 장황합니다. Pratt 알고리즘은 *우선순위 표 한 장*과 *루프 한 개*로 모든 이항 연산자를 다룹니다.

핵심 아이디어:

> 각 연산자에 **결합력(binding power)** 을 부여하고, 표현식을 파싱할 때 *현재 결합력보다 강한* 연산자가 보이는 동안만 흡수한다.

### 11.2 결합력 표

```ts
// src/parser/expr.ts
const BP: Record<string, [number, number]> = {
  // value: [left bp, right bp]
  "OR":  [10, 11],
  "XOR": [12, 13],
  "AND": [14, 15],
  "=":   [20, 21],
  "<>":  [20, 21],
  "<":   [20, 21],
  "<=":  [20, 21],
  ">":   [20, 21],
  ">=":  [20, 21],
  "+":   [30, 31],
  "-":   [30, 31],
  "MOD": [40, 41],
  "\\":  [42, 43],
  "*":   [44, 45],
  "/":   [44, 45],
  "^":   [61, 60],   // 우결합
};

const UNARY_BP = 50;   // 단항 + - 의 우측 결합력
const NOT_BP   = 16;   // NOT의 결합력 (비교(20)보다 약하고 AND(14)보다 강함)
```

좌결합은 `[L, L+1]`, 우결합은 `[L, L-1]`로 표현합니다(우측 bp가 작으면 같은 우선순위에서 오른쪽으로 묶임).

### 11.3 핵심 함수

```ts
import { Cursor } from "./cursor.js";
import * as A from "../ast/nodes.js";
import { BasicError, ERR } from "../common/types.js";

export function parseExpression(cur: Cursor, minBP = 0): A.Expr {
  let lhs = parsePrefix(cur);

  while (true) {
    const t = cur.peek();
    let opName: string | null = null;

    if (t.type === "OP") opName = t.value;
    else if (t.type === "KEYWORD" &&
             (t.value === "AND" || t.value === "OR" || t.value === "XOR" || t.value === "MOD")) {
      opName = t.value;
    }

    if (!opName || !(opName in BP)) break;
    const [lbp, rbp] = BP[opName]!;
    if (lbp < minBP) break;

    cur.next(); // 연산자 소비
    const rhs = parseExpression(cur, rbp);
    lhs = { kind: "Binary", op: opName, lhs, rhs };
  }

  return lhs;
}

function parsePrefix(cur: Cursor): A.Expr {
  const t = cur.peek();

  // 단항 부호
  if (t.type === "OP" && (t.value === "+" || t.value === "-")) {
    cur.next();
    const operand = parseExpression(cur, UNARY_BP);
    return { kind: "Unary", op: t.value, operand };
  }

  // NOT
  if (t.type === "KEYWORD" && t.value === "NOT") {
    cur.next();
    const operand = parseExpression(cur, NOT_BP);
    return { kind: "Unary", op: "NOT", operand };
  }

  // 괄호
  if (t.type === "LPAREN") {
    cur.next();
    const e = parseExpression(cur);
    cur.expect("RPAREN");
    return e;
  }

  // 숫자
  if (t.type === "NUMBER") {
    cur.next();
    return { kind: "NumLit", value: t.num!, numType: t.numType! };
  }

  // 문자열
  if (t.type === "STRING") {
    cur.next();
    return { kind: "StrLit", value: t.value };
  }

  // FN 사용자 함수 호출
  if (t.type === "KEYWORD" && t.value === "FN") {
    cur.next();
    const id = cur.expect("IDENT");
    let args: A.Expr[] = [];
    if (cur.match("LPAREN")) {
      args = parseExprList(cur);
      cur.expect("RPAREN");
    }
    return { kind: "FnCall", target: "FN_" + id.value.toUpperCase(), args };
  }

  // 내장 함수: KEYWORD + (
  if (t.type === "KEYWORD" && isBuiltinFunc(t.value)) {
    cur.next();
    let args: A.Expr[] = [];
    if (cur.match("LPAREN")) {
      args = parseExprList(cur);
      cur.expect("RPAREN");
    }
    return { kind: "FnCall", target: t.value, args };
  }

  // 식별자: 변수 또는 배열 참조
  if (t.type === "IDENT") {
    cur.next();
    if (cur.match("LPAREN")) {
      const indices = parseExprList(cur);
      cur.expect("RPAREN");
      return { kind: "ArrayRef", name: t.value, indices };
    }
    return { kind: "VarRef", name: t.value };
  }

  throw new BasicError(ERR.SYNTAX, `Unexpected token in expression: ${t.type}(${t.value})`,
    { line: t.line, col: t.col });
}

function parseExprList(cur: Cursor): A.Expr[] {
  const list: A.Expr[] = [];
  if (cur.peek().type === "RPAREN") return list;
  list.push(parseExpression(cur));
  while (cur.match("COMMA")) list.push(parseExpression(cur));
  return list;
}

const BUILTIN_FUNCS = new Set([
  "ABS","ASC","ATN","CDBL","CHR$","CINT","COS","CSNG","CSRLIN","EXP","FIX","HEX$",
  "INKEY$","INSTR","INT","LEFT$","LEN","LOG","MID$","OCT$","POS","RIGHT$","RND",
  "SGN","SIN","SPACE$","SQR","STR$","STRING$","TAB","TAN","TIMER","VAL",
]);
function isBuiltinFunc(kw: string): boolean { return BUILTIN_FUNCS.has(kw); }
```

### 11.4 동작 검증

`PRINT 1 + 2 * 3 ^ 2`를 파싱해 보면:

```
Binary(+,
  NumLit(1),
  Binary(*,
    NumLit(2),
    Binary(^, NumLit(3), NumLit(2))))
```

`PRINT NOT 1 = 0`은:

```
Unary(NOT,
  Binary(=, NumLit(1), NumLit(0)))
```

NOT의 결합력(16)이 비교(20)보다 *낮기* 때문에 비교가 먼저 묶이고 NOT이 그 결과를 받습니다. 이는 GW-BASIC 동작과 일치합니다.

### 11.5 단항 마이너스의 함정

`-2^2`는 GW-BASIC에서 -4 입니다. 우리 표에서 단항 `-`의 결합력은 50이고 `^`의 좌결합력은 61입니다. 단항이 먼저 호출되어 `parseExpression(cur, 50)`을 재귀 호출하면, 그 안에서 `^`(lbp=61)가 보이고 50 ≥ 50 이므로 흡수됩니다. 결과는 `-(2^2)` = -4. 정확합니다.

반대로 `2^-2`는 `^`의 우측에서 단항이 다시 시작되므로 `2^(-2) = 0.25`. 이것도 GW-BASIC과 일치.

### 11.6 테스트

```ts
import { describe, it, expect } from "vitest";
import { Lexer } from "../src/lexer/lexer.js";
import { Cursor } from "../src/parser/cursor.js";
import { parseExpression } from "../src/parser/expr.js";

function parse(src: string) {
  const t = Lexer.tokenize(src);
  return parseExpression(new Cursor(t));
}

describe("Pratt 표현식 파서", () => {
  it("우선순위", () => {
    const e = parse("1 + 2 * 3");
    expect(e).toMatchObject({
      kind: "Binary", op: "+",
      rhs: { kind: "Binary", op: "*" },
    });
  });

  it("거듭제곱은 우결합", () => {
    const e = parse("2^3^2");  // 2^(3^2) = 512
    expect(e).toMatchObject({
      kind: "Binary", op: "^",
      lhs: { kind: "NumLit", value: 2 },
      rhs: { kind: "Binary", op: "^",
             lhs: { kind: "NumLit", value: 3 },
             rhs: { kind: "NumLit", value: 2 } },
    });
  });

  it("단항 마이너스와 거듭제곱", () => {
    const e = parse("-2^2");
    expect(e).toMatchObject({
      kind: "Unary", op: "-",
      operand: { kind: "Binary", op: "^" },
    });
  });

  it("논리 연산", () => {
    const e = parse("A=1 AND B=2");
    expect(e).toMatchObject({
      kind: "Binary", op: "AND",
      lhs: { kind: "Binary", op: "=" },
      rhs: { kind: "Binary", op: "=" },
    });
  });

  it("함수 호출", () => {
    const e = parse('LEFT$("hello", 3)');
    expect(e).toMatchObject({
      kind: "FnCall", target: "LEFT$",
      args: [
        { kind: "StrLit", value: "hello" },
        { kind: "NumLit", value: 3 },
      ],
    });
  });
});
```

---

## 12장. 문장 파싱

### 12.1 디스패치 테이블

```ts
// src/parser/stmt.ts
import { Cursor } from "./cursor.js";
import * as A from "../ast/nodes.js";
import { parseExpression } from "./expr.js";
import { BasicError, ERR } from "../common/types.js";

type Parser = (cur: Cursor) => A.Stmt;

const STMT_PARSERS: Record<string, Parser> = {
  PRINT: parsePrint,
  INPUT: parseInput,
  LET:   parseLet,
  IF:    parseIf,
  FOR:   parseFor,
  NEXT:  parseNext,
  WHILE: parseWhile,
  WEND:  parseWend,
  GOTO:  parseGoto,
  GOSUB: parseGosub,
  RETURN:parseReturn,
  ON:    parseOn,
  END:   () => ({ kind: "End" }),
  STOP:  () => ({ kind: "Stop" }),
  REM:   parseRemKw,
  DIM:   parseDim,
  DATA:  parseData,
  READ:  parseRead,
  RESTORE: parseRestore,
  DEF:   parseDef,
  CLS:   parseCls,
  SCREEN:parseScreen,
  COLOR: parseColor,
  PSET:  (c) => parsePsetLike(c, "PSET"),
  PRESET:(c) => parsePsetLike(c, "PRESET"),
  LINE:  parseLine,
  CIRCLE:parseCircle,
  PAINT: parsePaint,
  LOCATE:parseLocate,
  SOUND: parseSound,
  PLAY:  parsePlay,
  BEEP:  () => ({ kind: "Beep" }),
  RANDOMIZE: parseRandomize,
  CLEAR: () => ({ kind: "Clear" }),
  SWAP:  parseSwap,
  RUN:   () => ({ kind: "Run" }),
  NEW:   () => ({ kind: "New" }),
  LIST:  parseList,
};

export function parseStatement(cur: Cursor): A.Stmt {
  const t = cur.peek();

  // REM_TEXT: 단축 ' 코멘트는 Lexer가 KEYWORD를 만들지 않고 바로 REM_TEXT만 남김
  if (t.type === "REM_TEXT") {
    cur.next();
    return { kind: "Rem", text: t.value };
  }

  if (t.type === "KEYWORD") {
    const fn = STMT_PARSERS[t.value];
    if (fn) {
      cur.next();
      return fn(cur);
    }
    // 키워드인데 파서가 없으면 'Unimplemented' AST 노드
    cur.next();
    return { kind: "Unimplemented", name: t.value };
  }

  // 키워드 없이 변수로 시작 → 묵시적 LET
  if (t.type === "IDENT") {
    return parseAssign(cur);
  }

  throw new BasicError(ERR.SYNTAX,
    `Unexpected token: ${t.type}(${t.value})`,
    { line: t.line, col: t.col });
}
```

### 12.2 LET / 묵시적 할당

```ts
function parseLet(cur: Cursor): A.Stmt { return parseAssign(cur); }

function parseAssign(cur: Cursor): A.Stmt {
  const target = parseLvalue(cur);
  cur.expect("OP", "=");
  const value = parseExpression(cur);
  return { kind: "Assign", target, value };
}

function parseLvalue(cur: Cursor): A.Lvalue {
  const id = cur.expect("IDENT");
  if (cur.match("LPAREN")) {
    const indices: A.Expr[] = [parseExpression(cur)];
    while (cur.match("COMMA")) indices.push(parseExpression(cur));
    cur.expect("RPAREN");
    return { kind: "ArrayRef", name: id.value, indices };
  }
  return { kind: "VarRef", name: id.value };
}
```

### 12.3 PRINT

```ts
function parsePrint(cur: Cursor): A.Stmt {
  const items: A.PrintItem[] = [];
  let trailing: ";" | "," | null = null;

  while (!cur.isEOL() && !cur.check("COLON") && !cur.check("KEYWORD","ELSE")
         && !cur.check("REM_TEXT")) {
    if (cur.match("SEMICOLON")) {
      items.push({ kind: "sep", value: ";" });
      trailing = ";";
      continue;
    }
    if (cur.match("COMMA")) {
      items.push({ kind: "sep", value: "," });
      trailing = ",";
      continue;
    }
    // TAB / SPC
    if (cur.check("KEYWORD","TAB") || cur.check("KEYWORD","SPC")) {
      const which = cur.next().value as "TAB" | "SPC";
      cur.expect("LPAREN");
      const arg = parseExpression(cur);
      cur.expect("RPAREN");
      items.push({ kind: "func", name: which, arg });
      trailing = null;
      continue;
    }
    // USING
    if (cur.match("KEYWORD","USING")) {
      const fmt = parseExpression(cur);
      cur.expect("SEMICOLON");
      const args: A.Expr[] = [parseExpression(cur)];
      while (cur.match("SEMICOLON")) args.push(parseExpression(cur));
      items.push({ kind: "using", fmt, args });
      trailing = null;
      continue;
    }
    items.push({ kind: "expr", value: parseExpression(cur) });
    trailing = null;
  }

  return { kind: "Print", items, suppressNewline: trailing !== null };
}
```

### 12.4 INPUT

```ts
function parseInput(cur: Cursor): A.Stmt {
  let suppressQuestion = false;
  if (cur.match("SEMICOLON")) suppressQuestion = true;

  let prompt = "";
  let promptSep: ";" | "," = ";";
  if (cur.peek().type === "STRING") {
    prompt = cur.next().value;
    if (cur.match("SEMICOLON")) promptSep = ";";
    else if (cur.match("COMMA")) promptSep = ",";
    else throw new BasicError(ERR.SYNTAX, "Expected ; or , after INPUT prompt");
  }

  const targets: A.Lvalue[] = [parseLvalue(cur)];
  while (cur.match("COMMA")) targets.push(parseLvalue(cur));

  return { kind: "Input", prompt, promptSep, targets, suppressQuestion };
}
```

### 12.5 IF / THEN / ELSE

```ts
function parseIf(cur: Cursor): A.Stmt {
  const cond = parseExpression(cur);
  cur.expect("KEYWORD", "THEN");

  const thenBranch = parseThenOrElse(cur);
  let elseBranch: A.Stmt[] | { goto: number } | null = null;
  if (cur.match("KEYWORD", "ELSE")) {
    elseBranch = parseThenOrElse(cur);
  }

  return { kind: "If", cond, thenBranch, elseBranch };
}

function parseThenOrElse(cur: Cursor): A.Stmt[] | { goto: number } {
  // 다음 토큰이 NUMBER 단독이면 GOTO 의미
  if (cur.peek().type === "NUMBER") {
    const n = cur.next();
    return { goto: n.num! | 0 };
  }
  // 그렇지 않으면 문장 리스트
  const stmts: A.Stmt[] = [parseStatement(cur)];
  while (cur.match("COLON")) {
    if (cur.isEOL() || cur.check("KEYWORD","ELSE")) break;
    stmts.push(parseStatement(cur));
  }
  return stmts;
}
```

### 12.6 FOR / NEXT

```ts
function parseFor(cur: Cursor): A.Stmt {
  const id = cur.expect("IDENT");
  cur.expect("OP", "=");
  const start = parseExpression(cur);
  cur.expect("KEYWORD", "TO");
  const end = parseExpression(cur);
  let step: A.Expr | null = null;
  if (cur.match("KEYWORD", "STEP")) {
    step = parseExpression(cur);
  }
  return { kind: "For", varName: id.value, start, end, step };
}

function parseNext(cur: Cursor): A.Stmt {
  const vars: string[] = [];
  if (cur.peek().type === "IDENT") {
    vars.push(cur.next().value);
    while (cur.match("COMMA")) {
      vars.push(cur.expect("IDENT").value);
    }
  }
  return { kind: "Next", vars };
}
```

### 12.7 WHILE / WEND

```ts
function parseWhile(cur: Cursor): A.Stmt {
  const cond = parseExpression(cur);
  return { kind: "While", cond };
}
function parseWend(_cur: Cursor): A.Stmt {
  return { kind: "Wend" };
}
```

### 12.8 GOTO / GOSUB / RETURN / ON

```ts
function parseGoto(cur: Cursor): A.Stmt {
  const n = cur.expect("NUMBER");
  return { kind: "Goto", target: n.num! | 0 };
}
function parseGosub(cur: Cursor): A.Stmt {
  const n = cur.expect("NUMBER");
  return { kind: "Gosub", target: n.num! | 0 };
}
function parseReturn(cur: Cursor): A.Stmt {
  let target: number | null = null;
  if (cur.peek().type === "NUMBER") target = cur.next().num! | 0;
  return { kind: "Return", target };
}
function parseOn(cur: Cursor): A.Stmt {
  const expr = parseExpression(cur);
  let mode: "GOTO" | "GOSUB";
  if (cur.match("KEYWORD","GOTO")) mode = "GOTO";
  else if (cur.match("KEYWORD","GOSUB")) mode = "GOSUB";
  else throw new BasicError(ERR.SYNTAX, "Expected GOTO or GOSUB after ON");
  const targets: number[] = [cur.expect("NUMBER").num! | 0];
  while (cur.match("COMMA")) targets.push(cur.expect("NUMBER").num! | 0);
  return { kind: "OnGoto", expr, mode, targets };
}
```

### 12.9 DIM / DATA / READ / RESTORE

```ts
function parseDim(cur: Cursor): A.Stmt {
  const decls: A.DimDecl[] = [parseDimDecl(cur)];
  while (cur.match("COMMA")) decls.push(parseDimDecl(cur));
  return { kind: "Dim", decls };
}
function parseDimDecl(cur: Cursor): A.DimDecl {
  const id = cur.expect("IDENT");
  cur.expect("LPAREN");
  const dims: A.Expr[] = [parseExpression(cur)];
  while (cur.match("COMMA")) dims.push(parseExpression(cur));
  cur.expect("RPAREN");
  return { name: id.value, dims };
}

function parseData(cur: Cursor): A.Stmt {
  // DATA는 콤마로 구분된 리터럴 (수치 또는 문자열, 또는 bare-string)
  const items: A.DataItem[] = [];
  items.push(readDataItem(cur));
  while (cur.match("COMMA")) items.push(readDataItem(cur));
  return { kind: "Data", items };
}
function readDataItem(cur: Cursor): A.DataItem {
  const t = cur.peek();
  if (t.type === "NUMBER") { cur.next(); return { kind: "num", value: t.num! }; }
  if (t.type === "STRING") { cur.next(); return { kind: "str", value: t.value }; }
  // bare string: 콤마/콜론/EOL이 나올 때까지 토큰 텍스트 합치기 (단순화)
  let s = "";
  while (!cur.check("COMMA") && !cur.check("COLON") && !cur.isEOL()) {
    s += cur.next().value;
  }
  return { kind: "str", value: s.trim() };
}

function parseRead(cur: Cursor): A.Stmt {
  const targets: A.Lvalue[] = [parseLvalue(cur)];
  while (cur.match("COMMA")) targets.push(parseLvalue(cur));
  return { kind: "Read", targets };
}
function parseRestore(cur: Cursor): A.Stmt {
  let line: number | null = null;
  if (cur.peek().type === "NUMBER") line = cur.next().num! | 0;
  return { kind: "Restore", line };
}
```

### 12.10 DEF FN

```ts
function parseDef(cur: Cursor): A.Stmt {
  cur.expect("KEYWORD", "FN");
  const id = cur.expect("IDENT");
  let params: string[] = [];
  if (cur.match("LPAREN")) {
    params.push(cur.expect("IDENT").value);
    while (cur.match("COMMA")) params.push(cur.expect("IDENT").value);
    cur.expect("RPAREN");
  }
  cur.expect("OP", "=");
  const body = parseExpression(cur);
  return { kind: "DefFn", name: "FN_" + id.value.toUpperCase(), params, body };
}
```

### 12.11 그래픽 / 사운드 (간단 형태)

```ts
function parseCls(cur: Cursor): A.Stmt {
  let mode: A.Expr | null = null;
  if (!cur.isEOL() && !cur.check("COLON")) mode = parseExpression(cur);
  return { kind: "Cls", mode };
}
function parseScreen(cur: Cursor): A.Stmt {
  return { kind: "Screen", mode: parseExpression(cur) };
}
function parseColor(cur: Cursor): A.Stmt {
  let fg: A.Expr | null = null, bg: A.Expr | null = null;
  if (!cur.isEOL() && !cur.check("COMMA") && !cur.check("COLON")) fg = parseExpression(cur);
  if (cur.match("COMMA")) bg = parseExpression(cur);
  return { kind: "Color", fg, bg };
}
function parseLocate(cur: Cursor): A.Stmt {
  let row: A.Expr | null = null, col: A.Expr | null = null;
  if (!cur.check("COMMA") && !cur.isEOL()) row = parseExpression(cur);
  if (cur.match("COMMA")) col = parseExpression(cur);
  return { kind: "Locate", row, col };
}
function parsePsetLike(cur: Cursor, op: "PSET" | "PRESET"): A.Stmt {
  const coord = parseCoord(cur);
  let color: A.Expr | null = null;
  if (cur.match("COMMA")) color = parseExpression(cur);
  return { kind: op === "PSET" ? "Pset" : "Preset", coord, color };
}
function parseCoord(cur: Cursor): A.Coord {
  const isStep = cur.match("KEYWORD", "STEP");
  cur.expect("LPAREN");
  const x = parseExpression(cur);
  cur.expect("COMMA");
  const y = parseExpression(cur);
  cur.expect("RPAREN");
  return { isStep, x, y };
}
function parseLine(cur: Cursor): A.Stmt {
  let from: A.Coord | null = null;
  if (!cur.check("OP","-")) from = parseCoord(cur);
  cur.expect("OP", "-");
  const to = parseCoord(cur);
  let color: A.Expr | null = null, mode: "B"|"BF"|null = null;
  if (cur.match("COMMA")) {
    if (!cur.check("COMMA")) color = parseExpression(cur);
    if (cur.match("COMMA")) {
      const id = cur.expect("IDENT").value.toUpperCase();
      if (id !== "B" && id !== "BF") {
        throw new BasicError(ERR.SYNTAX, "LINE expects B or BF");
      }
      mode = id as "B" | "BF";
    }
  }
  return { kind: "Line", from, to, color, mode };
}
function parseCircle(cur: Cursor): A.Stmt {
  const center = parseCoord(cur);
  cur.expect("COMMA");
  const radius = parseExpression(cur);
  let color: A.Expr | null = null, start: A.Expr | null = null;
  let endA: A.Expr | null = null, aspect: A.Expr | null = null;
  if (cur.match("COMMA")) { if (!cur.check("COMMA")) color = parseExpression(cur); }
  if (cur.match("COMMA")) { if (!cur.check("COMMA")) start = parseExpression(cur); }
  if (cur.match("COMMA")) { if (!cur.check("COMMA")) endA = parseExpression(cur); }
  if (cur.match("COMMA")) aspect = parseExpression(cur);
  return { kind: "Circle", center, radius, color, start, end: endA, aspect };
}
function parsePaint(cur: Cursor): A.Stmt {
  const point = parseCoord(cur);
  let fill: A.Expr | null = null, border: A.Expr | null = null;
  if (cur.match("COMMA")) fill = parseExpression(cur);
  if (cur.match("COMMA")) border = parseExpression(cur);
  return { kind: "Paint", point, fill, border };
}
function parseSound(cur: Cursor): A.Stmt {
  const freq = parseExpression(cur);
  cur.expect("COMMA");
  const dur = parseExpression(cur);
  return { kind: "Sound", freq, dur };
}
function parsePlay(cur: Cursor): A.Stmt {
  return { kind: "Play", mml: parseExpression(cur) };
}
function parseRandomize(cur: Cursor): A.Stmt {
  let seed: A.Expr | null = null;
  if (!cur.isEOL() && !cur.check("COLON")) seed = parseExpression(cur);
  return { kind: "Randomize", seed };
}
function parseSwap(cur: Cursor): A.Stmt {
  const a = parseLvalue(cur);
  cur.expect("COMMA");
  const b = parseLvalue(cur);
  return { kind: "Swap", a, b };
}
function parseList(cur: Cursor): A.Stmt {
  // 단순 형태만 지원: LIST [from] [- to]
  let from: number | null = null, to: number | null = null;
  if (cur.peek().type === "NUMBER") from = cur.next().num! | 0;
  if (cur.match("OP","-") && cur.peek().type === "NUMBER") to = cur.next().num! | 0;
  return { kind: "List", from, to };
}
function parseRemKw(cur: Cursor): A.Stmt {
  // KEYWORD(REM) 다음에 REM_TEXT가 따라옴 (Lexer가 그렇게 만듦)
  let text = "";
  if (cur.peek().type === "REM_TEXT") text = cur.next().value;
  return { kind: "Rem", text };
}
```

### 12.12 파서 테스트

```ts
import { describe, it, expect } from "vitest";
import { Lexer } from "../src/lexer/lexer.js";
import { Parser } from "../src/parser/parser.js";

function parse(src: string) {
  return new Parser(Lexer.tokenize(src)).parseProgram();
}

describe("Parser", () => {
  it("간단 프로그램", () => {
    const p = parse('10 PRINT "Hi"\n20 END');
    expect(p.lines.length).toBe(2);
    expect(p.lines[0].number).toBe(10);
    expect(p.lines[0].statements[0].kind).toBe("Print");
  });

  it("FOR/NEXT", () => {
    const p = parse("10 FOR I=1 TO 10 STEP 2\n20 NEXT I");
    expect(p.lines[0].statements[0]).toMatchObject({
      kind: "For", varName: "I",
    });
  });

  it("IF THEN ELSE", () => {
    const p = parse('10 IF X=1 THEN PRINT "A" ELSE PRINT "B"');
    expect(p.lines[0].statements[0].kind).toBe("If");
  });

  it("콜론 분리", () => {
    const p = parse("10 A=1 : B=2 : PRINT A+B");
    expect(p.lines[0].statements.length).toBe(3);
  });

  it("DIM 다차원", () => {
    const p = parse("10 DIM A(10, 5)");
    expect(p.lines[0].statements[0]).toMatchObject({
      kind: "Dim",
      decls: [{ name: "A", dims: [{}, {}] }],
    });
  });
});
```

---

## 13장. AST 노드 정의 (전체)

```ts
// src/ast/nodes.ts
export interface NumLit  { kind: "NumLit"; value: number; numType: "INT"|"SNG"|"DBL"; }
export interface StrLit  { kind: "StrLit"; value: string; }
export interface VarRef  { kind: "VarRef"; name: string; }
export interface ArrayRef{ kind: "ArrayRef"; name: string; indices: Expr[]; }
export interface FnCall  { kind: "FnCall"; target: string; args: Expr[]; }
export interface UnaryExpr  { kind: "Unary";  op: string; operand: Expr; }
export interface BinaryExpr { kind: "Binary"; op: string; lhs: Expr; rhs: Expr; }

export type Expr =
  | NumLit | StrLit | VarRef | ArrayRef | FnCall | UnaryExpr | BinaryExpr;

export type Lvalue = VarRef | ArrayRef;

export interface AssignStmt { kind: "Assign"; target: Lvalue; value: Expr; }

export type PrintItem =
  | { kind: "expr"; value: Expr }
  | { kind: "sep"; value: ";" | "," }
  | { kind: "func"; name: "TAB" | "SPC"; arg: Expr }
  | { kind: "using"; fmt: Expr; args: Expr[] };

export interface PrintStmt { kind: "Print"; items: PrintItem[]; suppressNewline: boolean; }

export interface InputStmt {
  kind: "Input"; prompt: string; promptSep: ";" | ",";
  targets: Lvalue[]; suppressQuestion: boolean;
}

export interface IfStmt {
  kind: "If"; cond: Expr;
  thenBranch: Stmt[] | { goto: number };
  elseBranch: Stmt[] | { goto: number } | null;
}
export interface ForStmt {
  kind: "For"; varName: string; start: Expr; end: Expr; step: Expr | null;
}
export interface NextStmt { kind: "Next"; vars: string[]; }
export interface WhileStmt { kind: "While"; cond: Expr; }
export interface WendStmt  { kind: "Wend"; }

export interface GotoStmt   { kind: "Goto"; target: number; }
export interface GosubStmt  { kind: "Gosub"; target: number; }
export interface ReturnStmt { kind: "Return"; target: number | null; }
export interface OnGotoStmt { kind: "OnGoto"; expr: Expr; mode: "GOTO"|"GOSUB"; targets: number[]; }

export interface EndStmt   { kind: "End"; }
export interface StopStmt  { kind: "Stop"; }
export interface RemStmt   { kind: "Rem"; text: string; }
export interface RunStmt   { kind: "Run"; }
export interface NewStmt   { kind: "New"; }
export interface ListStmt  { kind: "List"; from: number|null; to: number|null; }
export interface ClearStmt { kind: "Clear"; }
export interface SwapStmt  { kind: "Swap"; a: Lvalue; b: Lvalue; }
export interface RandomizeStmt { kind: "Randomize"; seed: Expr | null; }

export interface DimDecl { name: string; dims: Expr[]; }
export interface DimStmt { kind: "Dim"; decls: DimDecl[]; }
export type DataItem = { kind: "num"; value: number } | { kind: "str"; value: string };
export interface DataStmt    { kind: "Data"; items: DataItem[]; }
export interface ReadStmt    { kind: "Read"; targets: Lvalue[]; }
export interface RestoreStmt { kind: "Restore"; line: number | null; }
export interface DefFnStmt   { kind: "DefFn"; name: string; params: string[]; body: Expr; }

export interface Coord { isStep: boolean; x: Expr; y: Expr; }
export interface ClsStmt    { kind: "Cls"; mode: Expr | null; }
export interface ScreenStmt { kind: "Screen"; mode: Expr; }
export interface ColorStmt  { kind: "Color"; fg: Expr | null; bg: Expr | null; }
export interface LocateStmt { kind: "Locate"; row: Expr | null; col: Expr | null; }
export interface PsetStmt   { kind: "Pset"; coord: Coord; color: Expr | null; }
export interface PresetStmt { kind: "Preset"; coord: Coord; color: Expr | null; }
export interface LineStmt   { kind: "Line"; from: Coord|null; to: Coord; color: Expr|null; mode: "B"|"BF"|null; }
export interface CircleStmt { kind: "Circle"; center: Coord; radius: Expr;
                              color: Expr|null; start: Expr|null; end: Expr|null; aspect: Expr|null; }
export interface PaintStmt  { kind: "Paint"; point: Coord; fill: Expr|null; border: Expr|null; }
export interface SoundStmt  { kind: "Sound"; freq: Expr; dur: Expr; }
export interface PlayStmt   { kind: "Play"; mml: Expr; }
export interface BeepStmt   { kind: "Beep"; }
export interface UnimplementedStmt { kind: "Unimplemented"; name: string; }

export type Stmt =
  | AssignStmt | PrintStmt | InputStmt
  | IfStmt | ForStmt | NextStmt | WhileStmt | WendStmt
  | GotoStmt | GosubStmt | ReturnStmt | OnGotoStmt
  | EndStmt | StopStmt | RemStmt | RunStmt | NewStmt | ListStmt
  | DimStmt | DataStmt | ReadStmt | RestoreStmt | DefFnStmt
  | ClearStmt | SwapStmt | RandomizeStmt
  | ClsStmt | ScreenStmt | ColorStmt | LocateStmt
  | PsetStmt | PresetStmt | LineStmt | CircleStmt | PaintStmt
  | SoundStmt | PlayStmt | BeepStmt | UnimplementedStmt;

export interface ProgramLine {
  number: number | null;
  statements: Stmt[];
  sourceLine: number;
}
export interface Program {
  lines: ProgramLine[];
}
```

### 13.1 디스크리미네이티드 유니온 활용

각 노드의 `kind` 필드를 디스크리미네이터로 두면 TypeScript의 *exhaustive switch* 가 빛을 발합니다.

```ts
function visit(s: Stmt): void {
  switch (s.kind) {
    case "Print": ...; break;
    case "Assign": ...; break;
    // ...
    default: {
      const _: never = s;  // 컴파일 시 모든 케이스 강제
      throw new Error("unreachable");
    }
  }
}
```

새 문장을 추가할 때마다 컴파일러가 *처리 누락*을 잡아 줍니다.

### 13.2 AST 시각화 도구

디버깅을 위해 간단한 prettyPrint 함수를 두면 좋습니다.

```ts
// src/ast/print.ts
import * as A from "./nodes.js";

export function dumpExpr(e: A.Expr): string {
  switch (e.kind) {
    case "NumLit": return String(e.value);
    case "StrLit": return JSON.stringify(e.value);
    case "VarRef": return e.name;
    case "ArrayRef": return `${e.name}(${e.indices.map(dumpExpr).join(",")})`;
    case "FnCall": return `${e.target}(${e.args.map(dumpExpr).join(",")})`;
    case "Unary": return `(${e.op} ${dumpExpr(e.operand)})`;
    case "Binary": return `(${dumpExpr(e.lhs)} ${e.op} ${dumpExpr(e.rhs)})`;
  }
}
```

---

> 3부 끝. 이제 우리는 GW-BASIC 소스를 받아 AST로 만드는 *완전한 프론트엔드*를 가졌습니다. 4부에서 이 AST를 바이트코드로 컴파일하고, 가상 머신을 만들어 실행시킵니다.
# 제4부 · 백엔드 (1) — 바이트코드와 컴파일러

## 14장. 바이트코드 명령어 집합 (ISA) 설계

### 14.1 설계 철학

좋은 ISA의 조건:

- **수가 적을 것** — 디코더 단순, 디스패치 빠름
- **표현력이 풍부할 것** — 하나의 명령에 너무 많은 일을 시키지 않음
- **고정폭 또는 단순한 가변폭** — VM 실행이 빠름
- **디버깅이 쉬울 것** — 사람이 읽을 수 있는 형태로 덤프 가능

본 구현은 **태그된 객체 배열** 방식을 택합니다. 이진 인코딩이 아니라 `{ op, ... }` 형태의 객체로 명령을 저장합니다. 이진 인코딩은 빠르지만 디버깅이 어렵고, V8은 작은 객체 배열도 충분히 잘 최적화합니다.

### 14.2 명령어 카테고리

| 분류 | 예시 | 설명 |
|------|------|------|
| 스택 조작 | `PUSH`, `POP`, `DUP`, `SWAP_TOP` | 피연산자 스택 직접 조작 |
| 산술 | `ADD`, `SUB`, `MUL`, `DIV`, `IDIV`, `MOD`, `POW`, `NEG` | 이항/단항 산술 |
| 비교 | `EQ`, `NE`, `LT`, `LE`, `GT`, `GE` | -1/0 결과 |
| 논리 | `AND`, `OR`, `XOR`, `NOT` | 비트/논리 |
| 변수 | `LOAD`, `STORE`, `LOAD_ARR`, `STORE_ARR`, `DIM` | 변수 환경 |
| 분기 | `JMP`, `JMP_IF_FALSE`, `JMP_IF_TRUE`, `CALL`, `RET` | 제어 흐름 |
| FOR | `FOR_INIT`, `FOR_NEXT` | FOR 루프 전용 |
| 입출력 | `PRINT_VAL`, `PRINT_SEP`, `PRINT_NL`, `INPUT` | 콘솔 |
| 그래픽 | `CLS`, `PSET`, `LINE`, `CIRCLE`, `COLOR`, `SCREEN`, `LOCATE` | Host 위임 |
| 사운드 | `SOUND`, `PLAY`, `BEEP` | Host 위임 |
| 함수 | `CALL_FN`, `CALL_BUILTIN` | 사용자/내장 함수 |
| 데이터 | `READ`, `RESTORE` | DATA 풀 접근 |
| 종료 | `END`, `STOP`, `HALT` | 프로그램 종료 |

### 14.3 명령어 타입 정의

```ts
// src/vm/opcodes.ts
import { BasicValue } from "../runtime/value.js";

export type Op =
  // 스택
  | { op: "PUSH"; value: BasicValue }
  | { op: "POP" }
  | { op: "DUP" }
  | { op: "SWAP_TOP" }
  // 산술
  | { op: "ADD" } | { op: "SUB" } | { op: "MUL" } | { op: "DIV" }
  | { op: "IDIV" } | { op: "MOD" } | { op: "POW" } | { op: "NEG" }
  // 비교
  | { op: "EQ" } | { op: "NE" } | { op: "LT" } | { op: "LE" }
  | { op: "GT" } | { op: "GE" }
  // 논리
  | { op: "AND" } | { op: "OR" } | { op: "XOR" } | { op: "NOT" }
  // 변수
  | { op: "LOAD";  name: string }
  | { op: "STORE"; name: string }
  | { op: "LOAD_ARR";  name: string; n: number }
  | { op: "STORE_ARR"; name: string; n: number }
  | { op: "DIM"; name: string; n: number }
  // 분기
  | { op: "JMP"; target: number }
  | { op: "JMP_IF_FALSE"; target: number }
  | { op: "JMP_IF_TRUE";  target: number }
  | { op: "CALL"; target: number }
  | { op: "RET" }
  | { op: "RET_TO"; target: number }
  // FOR
  | { op: "FOR_INIT"; varName: string; loopEnd: number }
  | { op: "FOR_NEXT"; varName: string; loopStart: number }
  // WHILE
  | { op: "WHILE_TEST"; loopEnd: number }
  | { op: "WEND"; loopStart: number }
  // 입출력
  | { op: "PRINT_VAL" }
  | { op: "PRINT_SEP"; sep: ";" | "," }
  | { op: "PRINT_TAB" }
  | { op: "PRINT_SPC" }
  | { op: "PRINT_USING"; nargs: number }
  | { op: "PRINT_NL" }
  | { op: "INPUT"; prompt: string; promptSep: ";" | ","; vars: { name: string; isArray: boolean; nIdx: number }[]; suppressQuestion: boolean }
  // 그래픽
  | { op: "CLS"; mode: number }
  | { op: "SCREEN" }
  | { op: "COLOR"; hasFg: boolean; hasBg: boolean }
  | { op: "LOCATE"; hasRow: boolean; hasCol: boolean }
  | { op: "PSET"; isStep: boolean; hasColor: boolean }
  | { op: "PRESET"; isStep: boolean; hasColor: boolean }
  | { op: "LINE"; hasFrom: boolean; fromStep: boolean; toStep: boolean; hasColor: boolean; mode: "B"|"BF"|null }
  | { op: "CIRCLE"; isStep: boolean; hasColor: boolean; hasStart: boolean; hasEnd: boolean; hasAspect: boolean }
  | { op: "PAINT"; isStep: boolean; hasFill: boolean; hasBorder: boolean }
  // 사운드
  | { op: "SOUND" }
  | { op: "PLAY" }
  | { op: "BEEP" }
  // 함수
  | { op: "CALL_BUILTIN"; name: string; nargs: number }
  | { op: "CALL_FN"; name: string; nargs: number }
  | { op: "DEF_FN"; name: string; params: string[]; body: Op[] }
  // 데이터
  | { op: "READ"; name: string; isArray: boolean; nIdx: number }
  | { op: "RESTORE"; line: number | null }
  // 기타
  | { op: "RANDOMIZE"; hasSeed: boolean }
  | { op: "CLEAR" }
  | { op: "SWAP"; a: { name: string; isArray: boolean; nIdx: number }; b: { name: string; isArray: boolean; nIdx: number } }
  // 종료
  | { op: "END" }
  | { op: "STOP" }
  | { op: "HALT" };
```

### 14.4 컴파일된 프로그램 구조

```ts
// src/vm/program.ts
import { Op } from "./opcodes.js";

export interface CompiledProgram {
  code: Op[];
  // BASIC 라인 번호 → code 인덱스
  lineMap: Map<number, number>;
  // DATA 풀: 모든 DATA 항목을 순서대로 모은 배열
  dataPool: { kind: "num"|"str"; value: number|string; sourceLine: number }[];
  // 라인 번호 → DATA 풀 인덱스 (RESTORE n 용)
  dataLineMap: Map<number, number>;
  // 사용자 정의 함수 테이블
  defFns: Map<string, { params: string[]; body: Op[] }>;
}
```

### 14.5 명령 디코딩 비용

객체 배열 디스패치는 다음과 같이 됩니다.

```ts
const ins = code[pc++];
switch (ins.op) { ... }
```

V8은 `op` 필드를 hidden class로 인식하고 인라인 캐시(IC)를 통해 빠르게 디스패치합니다. 1억 명령 / 초 수준의 throughput은 어렵지만, *수천만 명령 / 초* 는 무리 없이 나옵니다. GW-BASIC의 원래 속도(8086 4.77MHz로 수만 명령/초)에 비하면 수백 배 빠릅니다.

---

## 15장. AST → 바이트코드 컴파일러

### 15.1 컴파일러 골격

```ts
// src/compiler/compiler.ts
import * as A from "../ast/nodes.js";
import { Op } from "../vm/opcodes.js";
import { CompiledProgram } from "../vm/program.js";
import { BasicError, ERR } from "../common/types.js";
import { INT, SNG, DBL, STR } from "../runtime/value.js";

class Frame {
  forStack: { varName: string; loopEndPatch: number; loopStart: number }[] = [];
  whileStack: { testStart: number; loopEndPatch: number }[] = [];
}

export class Compiler {
  code: Op[] = [];
  lineMap = new Map<number, number>();
  dataPool: CompiledProgram["dataPool"] = [];
  dataLineMap = new Map<number, number>();
  defFns: CompiledProgram["defFns"] = new Map();
  frame = new Frame();

  compile(prog: A.Program): CompiledProgram {
    // 1패스: DATA 수집 + 라인 인덱스 예약
    this.collectData(prog);

    // 2패스: 코드 발생
    for (const line of prog.lines) {
      if (line.number !== null) {
        this.lineMap.set(line.number, this.code.length);
      }
      for (const s of line.statements) {
        this.emitStmt(s, line);
      }
    }
    this.emit({ op: "END" });

    // FOR / WHILE 짝 검사
    if (this.frame.forStack.length > 0) {
      throw new BasicError(ERR.FOR_WITHOUT_NEXT, "FOR without NEXT");
    }

    return {
      code: this.code,
      lineMap: this.lineMap,
      dataPool: this.dataPool,
      dataLineMap: this.dataLineMap,
      defFns: this.defFns,
    };
  }

  private emit(op: Op): number {
    this.code.push(op);
    return this.code.length - 1;
  }

  private patch(idx: number, target: number): void {
    const ins = this.code[idx]!;
    (ins as any).target = target;
  }

  private collectData(prog: A.Program): void {
    for (const line of prog.lines) {
      for (const s of line.statements) {
        if (s.kind === "Data") {
          if (line.number !== null && !this.dataLineMap.has(line.number)) {
            this.dataLineMap.set(line.number, this.dataPool.length);
          }
          for (const item of s.items) {
            this.dataPool.push({
              kind: item.kind, value: item.value as any,
              sourceLine: line.number ?? 0,
            });
          }
        }
      }
    }
  }
}
```

### 15.2 표현식 컴파일

```ts
// 클래스 메서드로 추가
private emitExpr(e: A.Expr): void {
  switch (e.kind) {
    case "NumLit": {
      const v = e.numType === "INT" ? INT(e.value)
              : e.numType === "DBL" ? DBL(e.value) : SNG(e.value);
      this.emit({ op: "PUSH", value: v });
      return;
    }
    case "StrLit": {
      this.emit({ op: "PUSH", value: STR(e.value) });
      return;
    }
    case "VarRef": {
      this.emit({ op: "LOAD", name: normName(e.name) });
      return;
    }
    case "ArrayRef": {
      for (const i of e.indices) this.emitExpr(i);
      this.emit({ op: "LOAD_ARR", name: normName(e.name), n: e.indices.length });
      return;
    }
    case "Unary": {
      this.emitExpr(e.operand);
      if (e.op === "-") this.emit({ op: "NEG" });
      else if (e.op === "+") {} // no-op
      else if (e.op === "NOT") this.emit({ op: "NOT" });
      return;
    }
    case "Binary": {
      this.emitExpr(e.lhs);
      this.emitExpr(e.rhs);
      this.emit({ op: BINOP[e.op] });
      return;
    }
    case "FnCall": {
      for (const a of e.args) this.emitExpr(a);
      if (e.target.startsWith("FN_")) {
        this.emit({ op: "CALL_FN", name: e.target, nargs: e.args.length });
      } else {
        this.emit({ op: "CALL_BUILTIN", name: e.target, nargs: e.args.length });
      }
      return;
    }
  }
}

const BINOP: Record<string, Op["op"]> = {
  "+":  "ADD",  "-":  "SUB",  "*":  "MUL",  "/":  "DIV",
  "\\": "IDIV", "MOD":"MOD",  "^":  "POW",
  "=":  "EQ",   "<>": "NE",   "<":  "LT",   "<=": "LE",
  ">":  "GT",   ">=": "GE",
  "AND":"AND",  "OR": "OR",   "XOR":"XOR",
};

function normName(name: string): string {
  return name.toUpperCase();
}
```

### 15.3 문장 컴파일

```ts
private emitStmt(s: A.Stmt, line: A.ProgramLine): void {
  switch (s.kind) {
    case "Rem":
    case "Data":
      return; // 코드 생성 없음

    case "Assign": {
      if (s.target.kind === "VarRef") {
        this.emitExpr(s.value);
        this.emit({ op: "STORE", name: normName(s.target.name) });
      } else {
        // ⚠️ 인덱스 먼저, 값은 마지막 — STORE_ARR(16장)가 스택 *최상위*에서
        // 값을 pop하므로 순서가 어긋나면 값이 인덱스로 쓰인다
        for (const i of s.target.indices) this.emitExpr(i);
        this.emitExpr(s.value);
        this.emit({ op: "STORE_ARR", name: normName(s.target.name), n: s.target.indices.length });
      }
      return;
    }

    case "Print": {
      for (const item of s.items) {
        if (item.kind === "expr") {
          this.emitExpr(item.value);
          this.emit({ op: "PRINT_VAL" });
        } else if (item.kind === "sep") {
          this.emit({ op: "PRINT_SEP", sep: item.value });
        } else if (item.kind === "func") {
          this.emitExpr(item.arg);
          this.emit({ op: item.name === "TAB" ? "PRINT_TAB" : "PRINT_SPC" });
        } else if (item.kind === "using") {
          this.emitExpr(item.fmt);
          for (const a of item.args) this.emitExpr(a);
          this.emit({ op: "PRINT_USING", nargs: item.args.length });
        }
      }
      if (!s.suppressNewline) this.emit({ op: "PRINT_NL" });
      return;
    }

    case "Input": {
      this.emit({
        op: "INPUT",
        prompt: s.prompt,
        promptSep: s.promptSep,
        vars: s.targets.map(t => ({
          name: normName(t.kind === "VarRef" ? t.name : (t as A.ArrayRef).name),
          isArray: t.kind === "ArrayRef",
          nIdx: t.kind === "ArrayRef" ? (t as A.ArrayRef).indices.length : 0,
        })),
        suppressQuestion: s.suppressQuestion,
      });
      // 배열 인덱스는 INPUT 직전에 미리 스택에 올린다
      // (단순화를 위해 본 구현은 배열 INPUT을 LET으로 emit)
      return;
    }

    case "If": {
      this.emitExpr(s.cond);
      const jmpToElse = this.emit({ op: "JMP_IF_FALSE", target: -1 });
      // THEN
      this.emitThenOrElse(s.thenBranch, line);
      const jmpToEnd = this.emit({ op: "JMP", target: -1 });
      this.patch(jmpToElse, this.code.length);
      // ELSE
      if (s.elseBranch) this.emitThenOrElse(s.elseBranch, line);
      this.patch(jmpToEnd, this.code.length);
      return;
    }

    case "Goto": {
      this.emit({ op: "JMP", target: this.lineRef(s.target) });
      return;
    }
    case "Gosub": {
      this.emit({ op: "CALL", target: this.lineRef(s.target) });
      return;
    }
    case "Return": {
      if (s.target !== null) {
        this.emit({ op: "RET_TO", target: this.lineRef(s.target) });
      } else {
        this.emit({ op: "RET" });
      }
      return;
    }
    case "OnGoto": {
      // 인덱스(1-based)에 따라 점프. 0 또는 범위 초과면 다음 문장으로 진행
      this.emitExpr(s.expr);
      // 후보마다: dup, push i, eq → 매치면 트램폴린(POP 후 점프/호출),
      // 불일치면 skip 점프로 다음 후보로. lineRef는 반드시 JMP/CALL을
      // emit하는 그 자리에서 호출해야 forward 참조 patch가 올바른 명령에 걸린다.
      const endJumps: number[] = [];
      for (let i = 0; i < s.targets.length; i++) {
        this.emit({ op: "DUP" });
        this.emit({ op: "PUSH", value: INT(i + 1) });
        this.emit({ op: "EQ" });
        const jt = this.emit({ op: "JMP_IF_TRUE", target: -1 });   // 매치 → 트램폴린
        const skip = this.emit({ op: "JMP", target: -1 });          // 불일치 → 다음 후보
        this.patch(jt, this.code.length);
        this.emit({ op: "POP" });                                   // ON-식 결과 제거
        if (s.mode === "GOTO") {
          this.emit({ op: "JMP", target: this.lineRef(s.targets[i]!) });
        } else {
          this.emit({ op: "CALL", target: this.lineRef(s.targets[i]!) });
          // GOSUB는 RETURN 후 CALL 다음 명령으로 돌아오므로 체인 밖으로 탈출
          endJumps.push(this.emit({ op: "JMP", target: -1 }));
        }
        this.patch(skip, this.code.length);
      }
      // 매치 안 되면 식 결과 POP하고 통과
      this.emit({ op: "POP" });
      for (const j of endJumps) this.patch(j, this.code.length);
      return;
    }

    case "For": {
      // 표준 BASIC FOR/NEXT는: var = start; do { ... ; var += step; } while ((step>0 ? var<=end : var>=end))
      // 우리 ISA는 FOR_INIT / FOR_NEXT 두 명령으로 처리
      // 스택에 start, end, step을 올린 뒤 FOR_INIT
      this.emitExpr(s.start);
      this.emitExpr(s.end);
      if (s.step) this.emitExpr(s.step);
      else this.emit({ op: "PUSH", value: INT(1) });
      const initIdx = this.emit({ op: "FOR_INIT", varName: normName(s.varName), loopEnd: -1 });
      const loopStart = this.code.length;
      this.frame.forStack.push({
        varName: normName(s.varName),
        loopEndPatch: initIdx,
        loopStart,
      });
      return;
    }

    case "Next": {
      const names = s.vars.length === 0 ? [null] : s.vars.map(normName);
      for (const name of names) {
        const top = this.frame.forStack.pop();
        if (!top) throw new BasicError(ERR.NEXT_WITHOUT_FOR, "NEXT without FOR");
        if (name !== null && name !== top.varName) {
          throw new BasicError(ERR.NEXT_WITHOUT_FOR, `NEXT ${name} doesn't match FOR ${top.varName}`);
        }
        this.emit({ op: "FOR_NEXT", varName: top.varName, loopStart: top.loopStart });
        // FOR_INIT의 loopEnd를 현재 위치로 patch (NEXT 다음 명령)
        (this.code[top.loopEndPatch] as any).loopEnd = this.code.length;
      }
      return;
    }

    case "While": {
      const testStart = this.code.length;
      this.emitExpr(s.cond);
      const exitPatch = this.emit({ op: "WHILE_TEST", loopEnd: -1 });
      this.frame.whileStack.push({ testStart, loopEndPatch: exitPatch });
      return;
    }
    case "Wend": {
      const top = this.frame.whileStack.pop();
      if (!top) throw new BasicError(ERR.SYNTAX, "WEND without WHILE");
      this.emit({ op: "WEND", loopStart: top.testStart });
      (this.code[top.loopEndPatch] as any).loopEnd = this.code.length;
      return;
    }

    case "Dim": {
      for (const d of s.decls) {
        for (const dim of d.dims) this.emitExpr(dim);
        this.emit({ op: "DIM", name: normName(d.name), n: d.dims.length });
      }
      return;
    }
    case "Read": {
      for (const t of s.targets) {
        if (t.kind === "ArrayRef") {
          for (const i of t.indices) this.emitExpr(i);
          this.emit({ op: "READ", name: normName(t.name), isArray: true, nIdx: t.indices.length });
        } else {
          this.emit({ op: "READ", name: normName(t.name), isArray: false, nIdx: 0 });
        }
      }
      return;
    }
    case "Restore": {
      this.emit({ op: "RESTORE", line: s.line });
      return;
    }

    case "DefFn": {
      // 함수 본문을 별도 컴파일
      const sub = new Compiler();
      sub.emitExpr(s.body);
      sub.emit({ op: "RET" });
      this.defFns.set(s.name, { params: s.params.map(normName), body: sub.code });
      return;
    }

    case "End": this.emit({ op: "END" }); return;
    case "Stop": this.emit({ op: "STOP" }); return;
    case "Run": this.emit({ op: "JMP", target: 0 }); return;
    case "Clear": this.emit({ op: "CLEAR" }); return;
    case "Randomize": {
      if (s.seed) this.emitExpr(s.seed);
      this.emit({ op: "RANDOMIZE", hasSeed: !!s.seed });
      return;
    }
    case "Swap": {
      const desc = (l: A.Lvalue) => ({
        name: normName(l.kind === "VarRef" ? l.name : l.name),
        isArray: l.kind === "ArrayRef",
        nIdx: l.kind === "ArrayRef" ? l.indices.length : 0,
      });
      if (s.a.kind === "ArrayRef") for (const i of s.a.indices) this.emitExpr(i);
      if (s.b.kind === "ArrayRef") for (const i of s.b.indices) this.emitExpr(i);
      this.emit({ op: "SWAP", a: desc(s.a), b: desc(s.b) });
      return;
    }

    // 그래픽
    case "Cls": {
      if (s.mode) this.emitExpr(s.mode);
      this.emit({ op: "CLS", mode: s.mode ? -1 : 0 }); // mode -1: 스택에 값 있음
      return;
    }
    case "Screen": { this.emitExpr(s.mode); this.emit({ op: "SCREEN" }); return; }
    case "Color": {
      if (s.fg) this.emitExpr(s.fg);
      if (s.bg) this.emitExpr(s.bg);
      this.emit({ op: "COLOR", hasFg: !!s.fg, hasBg: !!s.bg });
      return;
    }
    case "Locate": {
      if (s.row) this.emitExpr(s.row);
      if (s.col) this.emitExpr(s.col);
      this.emit({ op: "LOCATE", hasRow: !!s.row, hasCol: !!s.col });
      return;
    }
    case "Pset": case "Preset": {
      this.emitExpr(s.coord.x); this.emitExpr(s.coord.y);
      if (s.color) this.emitExpr(s.color);
      this.emit({ op: s.kind === "Pset" ? "PSET" : "PRESET",
                  isStep: s.coord.isStep, hasColor: !!s.color });
      return;
    }
    case "Line": {
      if (s.from) { this.emitExpr(s.from.x); this.emitExpr(s.from.y); }
      this.emitExpr(s.to.x); this.emitExpr(s.to.y);
      if (s.color) this.emitExpr(s.color);
      this.emit({
        op: "LINE",
        hasFrom: !!s.from,
        fromStep: s.from?.isStep ?? false,
        toStep: s.to.isStep,
        hasColor: !!s.color,
        mode: s.mode,
      });
      return;
    }
    case "Circle": {
      this.emitExpr(s.center.x); this.emitExpr(s.center.y);
      this.emitExpr(s.radius);
      if (s.color) this.emitExpr(s.color);
      if (s.start) this.emitExpr(s.start);
      if (s.end)   this.emitExpr(s.end);
      if (s.aspect)this.emitExpr(s.aspect);
      this.emit({
        op: "CIRCLE",
        isStep: s.center.isStep,
        hasColor: !!s.color, hasStart: !!s.start,
        hasEnd: !!s.end, hasAspect: !!s.aspect,
      });
      return;
    }
    case "Paint": {
      this.emitExpr(s.point.x); this.emitExpr(s.point.y);
      if (s.fill) this.emitExpr(s.fill);
      if (s.border) this.emitExpr(s.border);
      this.emit({ op: "PAINT", isStep: s.point.isStep, hasFill: !!s.fill, hasBorder: !!s.border });
      return;
    }
    case "Sound": {
      this.emitExpr(s.freq); this.emitExpr(s.dur);
      this.emit({ op: "SOUND" }); return;
    }
    case "Play": { this.emitExpr(s.mml); this.emit({ op: "PLAY" }); return; }
    case "Beep": this.emit({ op: "BEEP" }); return;

    case "List": case "New":
      // REPL 명령은 컴파일 단계에서 NOOP
      return;

    case "Unimplemented":
      throw new BasicError(ERR.SYNTAX, `Unimplemented: ${s.name}`);

    default: {
      const _: never = s;
      throw new Error("compile: missed case");
    }
  }
}

private emitThenOrElse(b: A.Stmt[] | { goto: number }, line: A.ProgramLine): void {
  if ("goto" in b) {
    this.emit({ op: "JMP", target: this.lineRef(b.goto) });
  } else {
    for (const s of b) this.emitStmt(s, line);
  }
}

private lineRef(n: number): number {
  // 컴파일 1패스에서는 lineMap이 비어 있을 수 있음
  // 우리는 2패스 구조라 이미 채워져 있음 (lineMap이 미리 만들어짐)
  // 그러나 forward reference는 발생할 수 있으므로 sentinel 후 patch
  const idx = this.lineMap.get(n);
  if (idx !== undefined) return idx;
  // forward: 임시 -1, 후처리 단계에서 일괄 patch
  this.unresolved.push({ line: n, opIndex: this.code.length });
  return -1;
}
```

⚠️ `lineRef`의 forward reference 처리는 단순화를 위해 두 단계 컴파일로 바꾸는 것이 깔끔합니다. 1패스에서 모든 라인 위치를 미리 계산하고(빈 노드로 길이만 카운팅) 2패스에서 실제 코드 발생을 합니다. 본 책은 다음과 같이 변형합니다.

```ts
// 더 깔끔한 방법: 컴파일을 1패스로 하되, 모든 JMP/CALL을 라인 번호 그대로 저장하고
// 마지막에 lineMap을 참고해 일괄 변환
```

### 15.4 라인 위치 사전 계산 패턴

```ts
compile(prog: A.Program): CompiledProgram {
  this.collectData(prog);
  for (const line of prog.lines) {
    if (line.number !== null) this.lineMap.set(line.number, this.code.length);
    for (const s of line.statements) this.emitStmt(s, line);
  }
  // 라인 참조가 -1 인 명령들은 lineMap을 보고 일괄 변환
  this.resolveUnresolved();
  this.emit({ op: "END" });

  // FOR / WHILE 짝 검사
  if (this.frame.forStack.length > 0) {
    throw new BasicError(ERR.FOR_WITHOUT_NEXT, "FOR without NEXT");
  }
  if (this.frame.whileStack.length > 0) {
    throw new BasicError(ERR.SYNTAX, "WHILE without WEND");
  }

  return {
    code: this.code,
    lineMap: this.lineMap,
    dataPool: this.dataPool,
    dataLineMap: this.dataLineMap,
    defFns: this.defFns,
  };
}

private unresolved: { line: number; opIndex: number }[] = [];

private resolveUnresolved(): void {
  for (const u of this.unresolved) {
    const target = this.lineMap.get(u.line);
    if (target === undefined) {
      throw new BasicError(ERR.UNDEFINED_LINE_NUMBER, `Undefined line: ${u.line}`);
    }
    (this.code[u.opIndex] as any).target = target;
  }
}
```

💡 라인 번호 참조 명령은 `JMP`, `JMP_IF_*`, `CALL`, `RET_TO`, `RESTORE`(line 필드)입니다. 한 곳에서 일괄 처리하면 안전합니다.

### 15.5 디스어셈블러

디버깅을 위해 컴파일 결과를 텍스트로 보는 유틸리티.

```ts
// src/compiler/disasm.ts
import { CompiledProgram } from "../vm/program.js";

export function disassemble(p: CompiledProgram): string {
  const lines: string[] = [];
  const reverseLineMap = new Map<number, number>();
  for (const [n, i] of p.lineMap) reverseLineMap.set(i, n);

  for (let i = 0; i < p.code.length; i++) {
    const ln = reverseLineMap.get(i);
    if (ln !== undefined) lines.push(`; line ${ln}`);
    const op = p.code[i]!;
    let extras = "";
    for (const k of Object.keys(op)) {
      if (k === "op") continue;
      extras += ` ${k}=${JSON.stringify((op as any)[k])}`;
    }
    lines.push(`${String(i).padStart(4," ")}: ${op.op}${extras}`);
  }
  return lines.join("\n");
}
```

```basic
10 FOR I=1 TO 3
20 PRINT I
30 NEXT I
40 END
```

위 프로그램의 디스어셈블 결과:

```
; line 10
   0: PUSH value={"tag":"INT","v":1}
   1: PUSH value={"tag":"INT","v":3}
   2: PUSH value={"tag":"INT","v":1}
   3: FOR_INIT varName="I" loopEnd=8
; line 20
   4: LOAD name="I"
   5: PRINT_VAL
   6: PRINT_NL
; line 30
   7: FOR_NEXT varName="I" loopStart=4
; line 40
   8: END
   9: END
```

(마지막 두 END는 사용자 END + 컴파일러가 끼우는 가드용 END입니다.)

### 15.6 컴파일러 테스트

```ts
import { describe, it, expect } from "vitest";
import { Lexer } from "../src/lexer/lexer.js";
import { Parser } from "../src/parser/parser.js";
import { Compiler } from "../src/compiler/compiler.js";

function compile(src: string) {
  const ast = new Parser(Lexer.tokenize(src)).parseProgram();
  return new Compiler().compile(ast);
}

describe("Compiler", () => {
  it("PRINT 1+2", () => {
    const p = compile("10 PRINT 1+2");
    const ops = p.code.map(o => o.op);
    expect(ops).toEqual(["PUSH","PUSH","ADD","PRINT_VAL","PRINT_NL","END"]);
  });
  it("FOR 루프 점프 패치", () => {
    const p = compile("10 FOR I=1 TO 3\n20 PRINT I\n30 NEXT I");
    const init = p.code.find(o => o.op === "FOR_INIT") as any;
    const next = p.code.find(o => o.op === "FOR_NEXT") as any;
    expect(init.loopEnd).toBeGreaterThan(0);
    expect(next.loopStart).toBeLessThan(init.loopEnd);
  });
  it("GOTO 라인 해상", () => {
    const p = compile("10 GOTO 30\n20 PRINT 1\n30 PRINT 2");
    const jmp = p.code[0] as any;
    expect(jmp.op).toBe("JMP");
    expect(p.code[jmp.target].op).toBe("PUSH");
  });
});
```

이로써 컴파일러까지 완성. 다음 장에서는 이 바이트코드를 실행할 VM을 만듭니다.

---

> 14-15장 끝.
# 제4부 · 백엔드 (2) — 가상 머신과 메모리

## 16장. 스택 기반 가상 머신

### 16.1 VM의 큰 그림

```ts
// src/vm/vm.ts
import { CompiledProgram } from "./program.js";
import { Op } from "./opcodes.js";
import { BasicValue, INT, SNG, DBL, STR } from "../runtime/value.js";
import { Env } from "../runtime/env.js";
import { Host } from "../host/host.js";
import { BasicError, ERR } from "../common/types.js";
import { callBuiltin } from "../runtime/builtins.js";
import {
  add, sub, mul, div, idiv, mod, pow, neg,
  cmp, andOp, orOp, xorOp, notOp, toBool, fromBool,
  toNum, toStr,
} from "../runtime/ops.js";
import { formatPrintValue, formatSep, splitInput } from "../runtime/print-format.js";
import { formatUsing } from "../runtime/print-using.js";   // 19장의 확장판

interface ForRecord {
  varName: string;
  end: number;
  step: number;
  loopEnd: number;     // 종료 시 점프할 PC
}

export class VM {
  private pc = 0;
  private stack: BasicValue[] = [];
  private callStack: number[] = [];
  private forStack: ForRecord[] = [];
  private dataPtr = 0;
  private env = new Env();
  private halted = false;

  constructor(public program: CompiledProgram, public host: Host) {}

  async run(): Promise<void> {
    this.pc = 0;
    this.halted = false;
    while (!this.halted && this.pc < this.program.code.length) {
      const ins = this.program.code[this.pc++]!;
      await this.dispatch(ins);
    }
  }

  // ─── 스택 도우미 ────────────────────────────────
  private push(v: BasicValue): void { this.stack.push(v); }
  private pop(): BasicValue {
    const v = this.stack.pop();
    if (v === undefined) throw new BasicError(ERR.SYNTAX, "Stack underflow");
    return v;
  }
  private peek(off = 0): BasicValue {
    const v = this.stack[this.stack.length - 1 - off];
    if (v === undefined) throw new BasicError(ERR.SYNTAX, "Stack underflow");
    return v;
  }
}
```

### 16.2 명령 디스패치

```ts
// 동기 명령은 void를, 비동기 명령(INPUT/SOUND/PLAY/BEEP)은 Promise를 반환한다.
// async 함수로 만들면 동기 명령의 예외까지 rejected Promise로 감싸져
// 동기 호출 경로(16.5의 dispatchSync)에서 조용히 사라지므로 일반 메서드로 둔다.
private dispatch(ins: Op): void | Promise<void> {
  switch (ins.op) {
    case "PUSH": this.push(ins.value); return;
    case "POP":  this.pop(); return;
    case "DUP":  this.push(this.peek()); return;
    case "SWAP_TOP": {
      const a = this.pop(), b = this.pop();
      this.push(a); this.push(b); return;
    }

    // 산술
    case "ADD": { const b = this.pop(), a = this.pop(); this.push(add(a,b)); return; }
    case "SUB": { const b = this.pop(), a = this.pop(); this.push(sub(a,b)); return; }
    case "MUL": { const b = this.pop(), a = this.pop(); this.push(mul(a,b)); return; }
    case "DIV": { const b = this.pop(), a = this.pop(); this.push(div(a,b)); return; }
    case "IDIV":{ const b = this.pop(), a = this.pop(); this.push(idiv(a,b)); return; }
    case "MOD": { const b = this.pop(), a = this.pop(); this.push(mod(a,b)); return; }
    case "POW": { const b = this.pop(), a = this.pop(); this.push(pow(a,b)); return; }
    case "NEG": { this.push(neg(this.pop())); return; }

    // 비교
    case "EQ": case "NE": case "LT": case "LE": case "GT": case "GE": {
      const b = this.pop(), a = this.pop();
      this.push(fromBool(cmp(a, b, ins.op)));
      return;
    }

    // 논리
    case "AND": { const b = this.pop(), a = this.pop(); this.push(andOp(a,b)); return; }
    case "OR":  { const b = this.pop(), a = this.pop(); this.push(orOp(a,b)); return; }
    case "XOR": { const b = this.pop(), a = this.pop(); this.push(xorOp(a,b)); return; }
    case "NOT": { this.push(notOp(this.pop())); return; }

    // 변수
    case "LOAD":  this.push(this.env.get(ins.name)); return;
    case "STORE": this.env.set(ins.name, this.pop()); return;
    case "LOAD_ARR": {
      const idx: number[] = [];
      for (let i = 0; i < ins.n; i++) idx.unshift(toNum(this.pop()) | 0);
      this.push(this.env.getArr(ins.name, idx));
      return;
    }
    case "STORE_ARR": {
      const v = this.pop();
      const idx: number[] = [];
      for (let i = 0; i < ins.n; i++) idx.unshift(toNum(this.pop()) | 0);
      this.env.setArr(ins.name, idx, v);
      return;
    }
    case "DIM": {
      const dims: number[] = [];
      for (let i = 0; i < ins.n; i++) dims.unshift(toNum(this.pop()) | 0);
      this.env.dim(ins.name, dims);
      return;
    }

    // 분기
    case "JMP": this.pc = ins.target; return;
    case "JMP_IF_FALSE": if (!toBool(this.pop())) this.pc = ins.target; return;
    case "JMP_IF_TRUE":  if ( toBool(this.pop())) this.pc = ins.target; return;
    case "CALL": this.callStack.push(this.pc); this.pc = ins.target; return;
    case "RET": {
      const ret = this.callStack.pop();
      if (ret === undefined) {
        throw new BasicError(ERR.RETURN_WITHOUT_GOSUB, "RETURN without GOSUB");
      }
      this.pc = ret; return;
    }
    case "RET_TO": {
      if (this.callStack.length === 0) {
        throw new BasicError(ERR.RETURN_WITHOUT_GOSUB, "RETURN without GOSUB");
      }
      this.callStack.pop();
      this.pc = ins.target;
      return;
    }

    // FOR / NEXT
    case "FOR_INIT": {
      const step = toNum(this.pop());
      const end  = toNum(this.pop());
      const start= toNum(this.pop());
      this.env.set(ins.varName, SNG(start));
      this.forStack.push({
        varName: ins.varName, end, step, loopEnd: ins.loopEnd,
      });
      // 즉시 종료 조건 검사 (start가 이미 end를 넘었으면 루프 스킵)
      if ((step > 0 && start > end) || (step < 0 && start < end)) {
        this.forStack.pop();
        this.pc = ins.loopEnd;
      }
      return;
    }
    case "FOR_NEXT": {
      const top = this.forStack[this.forStack.length - 1];
      if (!top || top.varName !== ins.varName) {
        throw new BasicError(ERR.NEXT_WITHOUT_FOR, `NEXT without matching FOR (${ins.varName})`);
      }
      const cur = toNum(this.env.get(ins.varName));
      const next = cur + top.step;
      this.env.set(ins.varName, SNG(next));
      const done = top.step > 0 ? next > top.end : next < top.end;
      if (done) {
        this.forStack.pop();
        // pc는 자연스럽게 다음 명령으로
      } else {
        this.pc = ins.loopStart;
      }
      return;
    }

    // WHILE / WEND
    case "WHILE_TEST": {
      if (!toBool(this.pop())) this.pc = ins.loopEnd;
      return;
    }
    case "WEND": this.pc = ins.loopStart; return;

    // 입출력
    case "PRINT_VAL": {
      const v = this.pop();
      this.host.printAt(formatPrintValue(v));
      return;
    }
    case "PRINT_SEP": {
      this.host.printAt(formatSep(ins.sep, this.host.column()));
      return;
    }
    case "PRINT_TAB": {
      const col = (toNum(this.pop()) | 0);
      const cur = this.host.column();
      const need = col - cur;
      if (need > 0) this.host.printAt(" ".repeat(need));
      else if (need < 0) { this.host.println(""); this.host.printAt(" ".repeat(col - 1)); }
      return;
    }
    case "PRINT_SPC": {
      const n = (toNum(this.pop()) | 0);
      this.host.printAt(" ".repeat(Math.max(0, n)));
      return;
    }
    case "PRINT_USING": {
      const args: BasicValue[] = [];
      for (let i = 0; i < ins.nargs; i++) args.unshift(this.pop());
      const fmt = toStr(this.pop());
      this.host.printAt(formatUsing(fmt, args));
      return;
    }
    case "PRINT_NL": this.host.println(""); return;

    case "INPUT": return this.doInput(ins);   // 아래 doInput 참고

    // 그래픽 (Host로 위임)
    case "CLS": {
      let mode = 0;
      if (ins.mode === -1) mode = toNum(this.pop()) | 0;
      this.host.cls(mode);
      return;
    }
    case "SCREEN": this.host.setScreen(toNum(this.pop()) | 0); return;
    case "COLOR": {
      let bg: number | null = null, fg: number | null = null;
      if (ins.hasBg) bg = toNum(this.pop()) | 0;
      if (ins.hasFg) fg = toNum(this.pop()) | 0;
      this.host.setColor(fg, bg);
      return;
    }
    case "LOCATE": {
      let col: number | null = null, row: number | null = null;
      if (ins.hasCol) col = toNum(this.pop()) | 0;
      if (ins.hasRow) row = toNum(this.pop()) | 0;
      this.host.locate(row, col);
      return;
    }
    case "PSET": case "PRESET": {
      let color: number | null = null;
      if (ins.hasColor) color = toNum(this.pop()) | 0;
      const y = toNum(this.pop()) | 0;
      const x = toNum(this.pop()) | 0;
      this.host.pset(x, y, color, ins.isStep, ins.op === "PRESET");
      return;
    }
    case "LINE": {
      let color: number | null = null;
      if (ins.hasColor) color = toNum(this.pop()) | 0;
      const y2 = toNum(this.pop()) | 0;
      const x2 = toNum(this.pop()) | 0;
      let x1 = NaN, y1 = NaN;
      if (ins.hasFrom) { y1 = toNum(this.pop()) | 0; x1 = toNum(this.pop()) | 0; }
      this.host.drawLine(
        ins.hasFrom ? x1 : null, ins.hasFrom ? y1 : null,
        x2, y2, color, ins.fromStep, ins.toStep, ins.mode,
      );
      return;
    }
    case "CIRCLE": {
      let aspect: number | null = null, end: number | null = null;
      let start: number | null = null, color: number | null = null;
      if (ins.hasAspect) aspect = toNum(this.pop());
      if (ins.hasEnd)    end    = toNum(this.pop());
      if (ins.hasStart)  start  = toNum(this.pop());
      if (ins.hasColor)  color  = toNum(this.pop()) | 0;
      const r = toNum(this.pop());
      const y = toNum(this.pop()) | 0;
      const x = toNum(this.pop()) | 0;
      this.host.drawCircle(x, y, r, color, start, end, aspect, ins.isStep);
      return;
    }
    case "PAINT": {
      let border: number | null = null, fill: number | null = null;
      if (ins.hasBorder) border = toNum(this.pop()) | 0;
      if (ins.hasFill)   fill   = toNum(this.pop()) | 0;
      const y = toNum(this.pop()) | 0;
      const x = toNum(this.pop()) | 0;
      this.host.paint(x, y, fill, border, ins.isStep);
      return;
    }

    // 사운드 (pop은 동기적으로 끝내고 Promise만 반환)
    case "SOUND": {
      const dur = toNum(this.pop());
      const freq = toNum(this.pop());
      return this.host.sound(freq, dur);
    }
    case "PLAY": {
      const mml = toStr(this.pop());
      return this.host.play(mml);
    }
    case "BEEP": return this.host.sound(800, 200);

    // 함수
    case "CALL_BUILTIN": {
      const args: BasicValue[] = [];
      for (let i = 0; i < ins.nargs; i++) args.unshift(this.pop());
      this.push(callBuiltin(ins.name, args, this));
      return;
    }
    case "CALL_FN":
      // 사용자 정의 함수 호출. sub-VM을 따로 만들면 결과(그쪽 스택의 최상위)를
      // 돌려받는 경로가 복잡해지므로, 매개변수 스코프(frame)와 함께
      // DEF FN을 다루는 26장에서 *동기 평가*로 구현한다 (26.3절 코드로 채움).
      throw new BasicError(ERR.SYNTAX, `FN not yet implemented (26장 참고)`);

    case "DEF_FN":
      this.program.defFns.set(ins.name, { params: ins.params, body: ins.body });
      return;

    // 데이터
    case "READ": {
      const item = this.program.dataPool[this.dataPtr++];
      if (!item) throw new BasicError(ERR.OUT_OF_DATA, "Out of DATA");
      const isStr = ins.name.endsWith("$");
      let v: BasicValue;
      if (isStr) {
        v = STR(typeof item.value === "string" ? item.value : String(item.value));
      } else {
        const n = typeof item.value === "number" ? item.value : parseFloat(item.value as string);
        if (!Number.isFinite(n)) {
          // 숫자 변수에 숫자가 아닌 DATA — GW-BASIC은 해당 DATA 라인의 Syntax error
          throw new BasicError(ERR.SYNTAX, `Syntax error in DATA (line ${item.sourceLine})`);
        }
        v = SNG(n);
      }
      if (ins.isArray) {
        const idx: number[] = [];
        for (let i = 0; i < ins.nIdx; i++) idx.unshift(toNum(this.pop()) | 0);
        this.env.setArr(ins.name, idx, v);
      } else {
        this.env.set(ins.name, v);
      }
      return;
    }
    case "RESTORE": {
      if (ins.line === null) this.dataPtr = 0;
      else {
        const p = this.program.dataLineMap.get(ins.line);
        if (p === undefined) {
          throw new BasicError(ERR.UNDEFINED_LINE_NUMBER, `RESTORE: line ${ins.line} not found`);
        }
        this.dataPtr = p;
      }
      return;
    }

    case "RANDOMIZE": {
      if (ins.hasSeed) this.host.seedRandom(toNum(this.pop()));
      else this.host.seedRandom(Date.now());
      return;
    }
    case "CLEAR":
      this.env.clear();
      this.forStack.length = 0;
      this.callStack.length = 0;
      this.stack.length = 0;
      return;

    case "SWAP": {
      const get = (d: typeof ins.a, idx: number[]): BasicValue =>
        d.isArray ? this.env.getArr(d.name, idx) : this.env.get(d.name);
      const set = (d: typeof ins.a, idx: number[], v: BasicValue): void => {
        if (d.isArray) this.env.setArr(d.name, idx, v); else this.env.set(d.name, v);
      };
      const popIdx = (n: number): number[] => {
        const r: number[] = [];
        for (let i = 0; i < n; i++) r.unshift(toNum(this.pop()) | 0);
        return r;
      };
      const bIdx = popIdx(ins.b.nIdx);
      const aIdx = popIdx(ins.a.nIdx);
      const va = get(ins.a, aIdx);
      const vb = get(ins.b, bIdx);
      if (va.tag !== vb.tag) {
        // GW-BASIC: SWAP requires same type
        throw new BasicError(ERR.TYPE_MISMATCH, "SWAP type mismatch");
      }
      set(ins.a, aIdx, vb);
      set(ins.b, bIdx, va);
      return;
    }

    case "END":
    case "STOP":
    case "HALT":
      this.halted = true;
      return;
  }
}

// INPUT의 실제 처리 (유일하게 await가 필요한 부분이라 별도 async 메서드)
private async doInput(ins: Op & { op: "INPUT" }): Promise<void> {
  // 프롬프트 뒤가 콤마면 물음표 억제: INPUT "p", V
  const q = (ins.suppressQuestion || ins.promptSep === ",") ? "" : "? ";
  const text = (await this.host.inputLine(ins.prompt + q)) ?? "";
  const parts = splitInput(text, ins.vars.length);
  for (let i = 0; i < ins.vars.length; i++) {
    const v = ins.vars[i]!;
    const raw = parts[i] ?? "";
    const isStr = v.name.endsWith("$");
    const val: BasicValue = isStr ? STR(raw) : SNG(parseFloat(raw) || 0);
    if (v.isArray) {
      // 배열 INPUT은 본 구현에서 비지원 (단순 설계)
      throw new BasicError(ERR.SYNTAX, "Array INPUT not supported");
    }
    this.env.set(v.name, val);
  }
}
```

### 16.3 PRINT 포매팅 도우미

```ts
// src/runtime/print-format.ts
import { BasicValue } from "./value.js";

const TAB_WIDTH = 14;

export function formatPrintValue(v: BasicValue): string {
  if (v.tag === "STR") return v.v;
  // 양수는 앞 공백, 모두 끝에 공백 한 칸
  const s = formatNumber(v.v, v.tag);
  return (v.v >= 0 ? " " : "") + s + " ";
}

function formatNumber(n: number, tag: "INT" | "SNG" | "DBL"): string {
  if (tag === "INT") return Math.trunc(n).toString();
  if (Number.isInteger(n) && Math.abs(n) < 1e15) return n.toString();
  // 부동소수: 7자리(SNG) / 16자리(DBL) 정밀도로 trim
  const prec = tag === "DBL" ? 16 : 7;
  let s = n.toPrecision(prec);
  // 후행 0 제거
  if (s.includes(".") && !s.includes("E") && !s.includes("e")) {
    s = s.replace(/0+$/, "").replace(/\.$/, "");
  }
  return s;
}

export function formatSep(sep: ";" | ",", curCol: number): string {
  if (sep === ";") return "";
  // 콤마: 다음 인쇄 구역으로 이동 (폭 14, 시작 컬럼 1, 15, 29, …)
  const next = Math.floor((curCol - 1) / TAB_WIDTH + 1) * TAB_WIDTH + 1;
  return " ".repeat(next - curCol);
}

export function formatUsing(fmt: string, args: import("./value.js").BasicValue[]): string {
  // PRINT USING의 단순 구현: # 자리수, . 소수점, $ 통화 정도만
  // (자세한 사양은 19장에서 확장)
  let out = "";
  let aIdx = 0;
  let i = 0;
  while (i < fmt.length) {
    const c = fmt[i]!;
    if (c === "#" || c === ".") {
      // 한 필드 추출
      let field = "";
      while (i < fmt.length && (fmt[i] === "#" || fmt[i] === ".")) field += fmt[i++];
      const arg = args[aIdx++];
      out += formatNumericField(field, arg ? Number((arg as any).v) : 0);
    } else {
      out += c; i++;
    }
  }
  return out;
}

function formatNumericField(field: string, n: number): string {
  const dot = field.indexOf(".");
  const intDigits = dot < 0 ? field.length : dot;
  const fracDigits = dot < 0 ? 0 : field.length - dot - 1;
  let s = n.toFixed(fracDigits);
  // 정수 부분 패딩
  const dot2 = s.indexOf(".");
  const intPart = dot2 < 0 ? s : s.slice(0, dot2);
  const padLen = Math.max(0, intDigits - intPart.length);
  s = " ".repeat(padLen) + s;
  // 정수부가 너무 크면 % 부호 (오버플로 표시)
  if (intPart.length > intDigits) s = "%" + s.trimStart();
  return s;
}

export function splitInput(text: string, n: number): string[] {
  // INPUT은 콤마로 구분, 따옴표로 묶을 수 있음
  const parts: string[] = [];
  let cur = "", inQ = false;
  for (const ch of text) {
    if (ch === '"') { inQ = !inQ; continue; }
    if (ch === "," && !inQ) { parts.push(cur.trim()); cur = ""; continue; }
    cur += ch;
  }
  if (cur.length > 0 || parts.length < n) parts.push(cur.trim());
  return parts;
}
```

### 16.4 비동기 실행 (Async/await)

VM의 `run`이 `async`인 이유는 **INPUT, SOUND, PLAY, BEEP** 이 비동기 호스트 호출을 하기 때문입니다. 주의할 점은 `dispatch` 자체를 `async` 함수로 만들면 안 된다는 것입니다 — async 함수는 예외를 *동기적으로 던지지 않고* rejected Promise로 감싸므로, 동기 호출 경로에서 에러가 조용히 사라집니다. 그래서 `dispatch`는 일반 메서드로 두고, 비동기 명령에서만 Promise를 반환합니다. `await`는 Promise가 아닌 값에도 쓸 수 있으므로 `await this.dispatch(ins)`는 그대로 동작하지만, 매 명령에 await를 거는 것은 느립니다. 다음 절에서 최적화를 다룹니다.

### 16.5 동기 / 비동기 분리

성능을 위해 명령을 *비동기 명령* 과 *동기 명령*으로 나눕니다.

```ts
private isAsyncOp(op: string): boolean {
  return op === "INPUT" || op === "SOUND" || op === "PLAY" || op === "BEEP";
}

private dispatchSync(ins: Op): void {
  const r = this.dispatch(ins);   // 동기 명령은 즉시 완료, 예외도 동기로 던져진다
  if (r !== undefined) {
    throw new BasicError(ERR.SYNTAX, `Async op in sync context: ${ins.op}`);
  }
}

async run(): Promise<void> {
  while (!this.halted && this.pc < this.program.code.length) {
    const ins = this.program.code[this.pc++]!;
    if (this.isAsyncOp(ins.op)) {
      await this.dispatch(ins);
    } else {
      this.dispatchSync(ins);
    }
    // 주기적으로 yield (긴 루프에서 UI 블로킹 방지)
    if ((this.pc & 0xFFF) === 0) await Promise.resolve();
  }
}
```

`dispatchSync`는 비동기 명령을 만나면 throw 합니다 (BEEP도 비동기임에 주의). 이렇게 하면 99%의 명령이 마이크로태스크 비용 없이 실행됩니다.

### 16.6 인터럽트와 STOP

GW-BASIC은 Ctrl+Break로 중단할 수 있었습니다. 우리는 이를 다음과 같이 흉내 냅니다.

```ts
public requestStop(): void { this.stopRequested = true; }
private stopRequested = false;

// run() 내부, 매 4096명령마다:
if (this.stopRequested) {
  this.halted = true;
  this.host.println("Break");
  return;
}
```

브라우저에서는 Esc 키를 잡아 `vm.requestStop()`을 호출하면 됩니다.

---

## 17장. 메모리 모델과 값 표현

### 17.1 BasicValue 구조 재검토

```ts
export type BasicValue =
  | { tag: "INT"; v: number }
  | { tag: "SNG"; v: number }
  | { tag: "DBL"; v: number }
  | { tag: "STR"; v: string };
```

JavaScript 엔진(V8)에서 작은 객체는 hidden class로 인라이닝되어 빠릅니다. `tag` 필드 검사는 분기 예측이 잘 들어맞는 단순 비교라 수십 사이클 안에 끝납니다.

### 17.2 NaN-boxing은 필요할까?

루아처럼 64비트 NaN-boxing을 쓰면 박싱 비용이 사라집니다. 그러나 JavaScript는 이미 number를 IEEE 754 doublet로 다루고, 박스 객체도 SMI/HeapNumber 최적화를 받습니다. 우리 정도 규모에서는 *오히려* 직접 객체가 빠르고 디버깅도 쉽습니다.

### 17.3 산술 연산 구현

```ts
// src/runtime/ops.ts
import { BasicValue, INT, SNG, DBL, STR } from "./value.js";
import { BasicError, ERR } from "../common/types.js";

export function toNum(v: BasicValue): number {
  if (v.tag === "STR") throw new BasicError(ERR.TYPE_MISMATCH, "Type mismatch");
  return v.v;
}
export function toStr(v: BasicValue): string {
  if (v.tag !== "STR") throw new BasicError(ERR.TYPE_MISMATCH, "Type mismatch");
  return v.v;
}
export function toBool(v: BasicValue): boolean {
  return toNum(v) !== 0;
}
export function fromBool(b: boolean): BasicValue {
  return INT(b ? -1 : 0);
}

function promote(a: BasicValue, b: BasicValue): "INT"|"SNG"|"DBL" {
  if (a.tag === "STR" || b.tag === "STR") {
    throw new BasicError(ERR.TYPE_MISMATCH, "Type mismatch");
  }
  if (a.tag === "DBL" || b.tag === "DBL") return "DBL";
  if (a.tag === "SNG" || b.tag === "SNG") return "SNG";
  return "INT";
}

function makeNum(tag: "INT"|"SNG"|"DBL", v: number): BasicValue {
  if (tag === "INT") {
    if (v > 32767 || v < -32768) {
      // 자동 승격 (오버플로 회피)
      return SNG(v);
    }
    return INT(v | 0);
  }
  return tag === "DBL" ? DBL(v) : SNG(v);
}

export function add(a: BasicValue, b: BasicValue): BasicValue {
  if (a.tag === "STR" && b.tag === "STR") {
    const s = a.v + b.v;
    if (s.length > 255) throw new BasicError(ERR.STRING_TOO_LONG, "String too long");
    return STR(s);
  }
  return makeNum(promote(a,b), toNum(a) + toNum(b));
}
export function sub(a: BasicValue, b: BasicValue): BasicValue { return makeNum(promote(a,b), toNum(a) - toNum(b)); }
export function mul(a: BasicValue, b: BasicValue): BasicValue { return makeNum(promote(a,b), toNum(a) * toNum(b)); }
export function div(a: BasicValue, b: BasicValue): BasicValue {
  const bv = toNum(b);
  if (bv === 0) throw new BasicError(ERR.DIVISION_BY_ZERO, "Division by zero");
  // /는 항상 부동소수 (최소 SNG)
  const tag = promote(a,b);
  return makeNum(tag === "INT" ? "SNG" : tag, toNum(a) / bv);
}
export function idiv(a: BasicValue, b: BasicValue): BasicValue {
  const av = toNum(a) | 0;
  const bv = toNum(b) | 0;
  if (bv === 0) throw new BasicError(ERR.DIVISION_BY_ZERO, "Division by zero");
  const r = (av / bv) | 0;        // 0 방향 trunc
  return INT(r);
}
export function mod(a: BasicValue, b: BasicValue): BasicValue {
  const av = toNum(a) | 0;
  const bv = toNum(b) | 0;
  if (bv === 0) throw new BasicError(ERR.DIVISION_BY_ZERO, "Division by zero");
  const r = av - ((av / bv) | 0) * bv;
  return INT(r);
}
export function pow(a: BasicValue, b: BasicValue): BasicValue {
  return makeNum("DBL", Math.pow(toNum(a), toNum(b)));
}
export function neg(a: BasicValue): BasicValue {
  if (a.tag === "STR") throw new BasicError(ERR.TYPE_MISMATCH, "Type mismatch");
  return makeNum(a.tag, -a.v);
}

export function cmp(a: BasicValue, b: BasicValue, op: string): boolean {
  let r: number;
  if (a.tag === "STR" && b.tag === "STR") {
    r = a.v < b.v ? -1 : a.v > b.v ? 1 : 0;
  } else {
    const av = toNum(a), bv = toNum(b);
    r = av < bv ? -1 : av > bv ? 1 : 0;
  }
  switch (op) {
    case "EQ": return r === 0;
    case "NE": return r !== 0;
    case "LT": return r < 0;
    case "LE": return r <= 0;
    case "GT": return r > 0;
    case "GE": return r >= 0;
  }
  return false;
}

export function andOp(a: BasicValue, b: BasicValue): BasicValue {
  return INT((toNum(a) | 0) & (toNum(b) | 0));
}
export function orOp(a: BasicValue, b: BasicValue): BasicValue {
  return INT((toNum(a) | 0) | (toNum(b) | 0));
}
export function xorOp(a: BasicValue, b: BasicValue): BasicValue {
  return INT((toNum(a) | 0) ^ (toNum(b) | 0));
}
export function notOp(a: BasicValue): BasicValue {
  return INT(~(toNum(a) | 0));
}
```

### 17.4 메모리 한계

GW-BASIC은 64KB 데이터 영역, 64KB 문자열 영역이라는 제한이 있었습니다. 본 구현에서는 JavaScript의 자연스러운 한계(GB 단위)를 그대로 두지만, 다음 두 검사는 명시적으로 합니다.

- 단일 문자열 길이 ≤ 255
- 배열 총 원소 수가 너무 크면 경고 (GW-BASIC은 32767개 제한)

### 17.5 가비지 컬렉션

JavaScript의 GC를 그대로 활용합니다. BasicValue는 모두 **불변(immutable)** 으로 다루므로, 사용한 값은 즉시 GC 대상이 됩니다. Hot path에서 객체 생성을 줄이려면 *작은 정수에 대한 캐시* 가 도움이 됩니다.

```ts
const SMALL_INT_CACHE: BasicValue[] = [];
for (let i = -128; i <= 127; i++) SMALL_INT_CACHE[i + 128] = { tag: "INT", v: i };
export function INT(v: number): BasicValue {
  const i = v | 0;
  if (i >= -128 && i <= 127) return SMALL_INT_CACHE[i + 128]!;
  return { tag: "INT", v: i };
}
```

이 한 가지로 FOR 루프, 카운터 등에서 발생하는 INT 객체 할당이 거의 사라집니다.

---

## 18장. 변수 환경과 스코프

### 18.1 Env 클래스

```ts
// src/runtime/env.ts
import { BasicValue, INT, SNG, DBL, STR } from "./value.js";
import { BasicError, ERR } from "../common/types.js";

interface ArrayBox {
  dims: number[];        // 각 차원의 *상한* (포함)  → 길이 = dim+1
  data: BasicValue[];
  baseIsOne: boolean;    // OPTION BASE 1이면 true (기본 false)
}

export class Env {
  private scalar = new Map<string, BasicValue>();
  private arrays = new Map<string, ArrayBox>();
  private defaultTypeMap = new Map<string, "INT"|"SNG"|"DBL"|"STR">();
  // DEFINT/DEFSNG/DEFDBL/DEFSTR로 채워짐
  private frameStack: Map<string, BasicValue>[] = [];

  optionBase = 0;

  defaultType(name: string): "INT"|"SNG"|"DBL"|"STR" {
    const last = name[name.length - 1];
    if (last === "$") return "STR";
    if (last === "%") return "INT";
    if (last === "!") return "SNG";
    if (last === "#") return "DBL";
    const first = name[0]!.toUpperCase();
    return this.defaultTypeMap.get(first) ?? "SNG";
  }

  setDefaultRange(range: string, type: "INT"|"SNG"|"DBL"|"STR"): void {
    // "A-Z" 또는 "I-N" 형태
    const [a, b] = range.split("-");
    const lo = a!.charCodeAt(0), hi = (b ?? a)!.charCodeAt(0);
    for (let c = lo; c <= hi; c++) {
      this.defaultTypeMap.set(String.fromCharCode(c), type);
    }
  }

  get(name: string): BasicValue {
    // frame이 있고 그곳에 있으면 우선
    for (let i = this.frameStack.length - 1; i >= 0; i--) {
      const f = this.frameStack[i]!;
      if (f.has(name)) return f.get(name)!;
    }
    if (this.scalar.has(name)) return this.scalar.get(name)!;
    // 미정의: 기본값
    return this.defaultValue(name);
  }

  set(name: string, v: BasicValue): void {
    for (let i = this.frameStack.length - 1; i >= 0; i--) {
      const f = this.frameStack[i]!;
      if (f.has(name)) { f.set(name, this.coerce(name, v)); return; }
    }
    this.scalar.set(name, this.coerce(name, v));
  }

  private defaultValue(name: string): BasicValue {
    const t = this.defaultType(name);
    if (t === "STR") return STR("");
    if (t === "INT") return INT(0);
    if (t === "DBL") return DBL(0);
    return SNG(0);
  }

  private coerce(name: string, v: BasicValue): BasicValue {
    const t = this.defaultType(name);
    if (t === "STR") {
      if (v.tag !== "STR") throw new BasicError(ERR.TYPE_MISMATCH, `Type mismatch: ${name}`);
      if (v.v.length > 255) throw new BasicError(ERR.STRING_TOO_LONG, "String too long");
      return v;
    }
    if (v.tag === "STR") throw new BasicError(ERR.TYPE_MISMATCH, `Type mismatch: ${name}`);
    if (t === "INT") {
      const r = Math.round(v.v);
      if (r > 32767 || r < -32768) throw new BasicError(ERR.OVERFLOW, "Overflow");
      return INT(r);
    }
    if (t === "DBL") return DBL(v.v);
    return SNG(v.v);
  }

  // ── 배열 ──────────────────────────────────────
  dim(name: string, upperBounds: number[]): void {
    if (this.arrays.has(name)) {
      throw new BasicError(ERR.DUPLICATE_DEFINITION, `Duplicate definition: ${name}`);
    }
    const dims = upperBounds.map(b => b + 1 - this.optionBase);
    let total = 1;
    for (const d of dims) {
      if (d <= 0) throw new BasicError(ERR.SUBSCRIPT_OUT_OF_RANGE, "Bad DIM");
      total *= d;
    }
    const init = this.defaultValue(name);
    const data = new Array<BasicValue>(total).fill(init);
    this.arrays.set(name, { dims, data, baseIsOne: this.optionBase === 1 });
  }

  private idxFlat(box: ArrayBox, idx: number[]): number {
    if (idx.length !== box.dims.length) {
      throw new BasicError(ERR.SUBSCRIPT_OUT_OF_RANGE, "Wrong number of subscripts");
    }
    let flat = 0;
    for (let i = 0; i < idx.length; i++) {
      const k = idx[i]! - (box.baseIsOne ? 1 : 0);
      if (k < 0 || k >= box.dims[i]!) {
        throw new BasicError(ERR.SUBSCRIPT_OUT_OF_RANGE, `Subscript out of range`);
      }
      flat = flat * box.dims[i]! + k;
    }
    return flat;
  }

  getArr(name: string, idx: number[]): BasicValue {
    let box = this.arrays.get(name);
    if (!box) {
      // 묵시적 DIM (10까지)
      this.dim(name, idx.map(_ => 10));
      box = this.arrays.get(name)!;
    }
    return box.data[this.idxFlat(box, idx)]!;
  }

  setArr(name: string, idx: number[], v: BasicValue): void {
    let box = this.arrays.get(name);
    if (!box) {
      this.dim(name, idx.map(_ => 10));
      box = this.arrays.get(name)!;
    }
    box.data[this.idxFlat(box, idx)] = this.coerce(name, v);
  }

  pushFrame(): void { this.frameStack.push(new Map()); }
  popFrame(): void  { this.frameStack.pop(); }

  // 최상위 frame에 *새 이름*을 만든다 (DEF FN 매개변수 바인딩 전용).
  // set()은 frame에 이미 있는 이름만 갱신하므로,
  // 이것 없이 매개변수를 set으로 바인딩하면 전역 변수를 영구히 덮어쓴다.
  setLocal(name: string, v: BasicValue): void {
    const f = this.frameStack[this.frameStack.length - 1];
    if (f) f.set(name, this.coerce(name, v));
    else this.set(name, v);
  }

  clear(): void {
    this.scalar.clear();
    this.arrays.clear();
    this.frameStack.length = 0;
  }
}
```

### 18.2 OPTION BASE

```basic
OPTION BASE 1
DIM A(5)        ' 인덱스 1..5
```

본 구현에서는 `Env.optionBase`를 둬 처리합니다. AST/컴파일러에 추가 명령을 만들지 않고 환경 차원에서 다룹니다.

### 18.3 DEFxxx 처리

```basic
10 DEFINT I-N
20 I = 3.7
30 PRINT I        ' 4
```

`DEFINT` 같은 문은 본 구현에서 *직접 컴파일하지 않고* REPL 진입 시점에 환경에 반영합니다. 또는 별도 statement로 추가할 수 있습니다. 본 책에서는 단순화를 위해 DEFxxx를 인식만 하고 환경에 즉시 반영하는 형태로 다룹니다.

```ts
// stmt.ts에 추가
function parseDefRange(cur: Cursor, type: "INT"|"SNG"|"DBL"|"STR"): A.Stmt {
  const ranges: string[] = [];
  ranges.push(consumeRange(cur));
  while (cur.match("COMMA")) ranges.push(consumeRange(cur));
  return { kind: "DefType", type, ranges };
}
```

(AST에 `DefType` 노드를 추가하고 컴파일러에서 즉시 환경에 반영하는 식으로 구현)

### 18.4 프레임 스택 (DEF FN)

DEF FN의 매개변수만 별도의 스코프를 갖습니다. `Env.pushFrame` / `popFrame`이 그 역할을 합니다. 일반 변수와 같은 이름의 매개변수는 함수 내부에서만 매개변수를 가리킵니다(섀도잉).

⚠️ 매개변수 바인딩에는 `set`이 아니라 반드시 `setLocal`을 씁니다. `set`은 frame에 이미 존재하는 이름만 갱신하고 없으면 전역에 쓰기 때문에, `set`으로 바인딩하면 새 frame이 비어 있어 매개변수 값이 그대로 전역 변수를 덮어써 버립니다.

### 18.5 환경 테스트

```ts
import { describe, it, expect } from "vitest";
import { Env } from "../src/runtime/env.js";
import { INT, STR, SNG } from "../src/runtime/value.js";

describe("Env", () => {
  it("기본 타입 결정", () => {
    const e = new Env();
    expect(e.defaultType("A")).toBe("SNG");
    expect(e.defaultType("A%")).toBe("INT");
    expect(e.defaultType("S$")).toBe("STR");
  });

  it("DEFINT 영역", () => {
    const e = new Env();
    e.setDefaultRange("I-N", "INT");
    expect(e.defaultType("INDEX")).toBe("INT");
    expect(e.defaultType("ALPHA")).toBe("SNG");
  });

  it("배열 묵시 DIM", () => {
    const e = new Env();
    e.setArr("A", [3], SNG(7));
    expect((e.getArr("A", [3]) as any).v).toBe(7);
  });

  it("배열 범위 초과", () => {
    const e = new Env();
    e.dim("A", [5]);
    expect(() => e.getArr("A", [10])).toThrow();
  });

  it("타입 강제 변환", () => {
    const e = new Env();
    e.set("X%", SNG(3.7));
    expect((e.get("X%") as any).v).toBe(4); // 반올림
  });
});
```

---

> 4부 끝. 이제 우리는 GW-BASIC 소스를 받아 **실제 결과를 만드는** 완전한 처리기를 가졌습니다. 5부는 PRINT/INPUT 같은 실용 명령어들의 *동작 디테일*과 *런타임 라이브러리*를 다룹니다.
# 제5부 · 런타임 (1) — 입출력과 제어 흐름

## 19장. PRINT와 INPUT — 입출력의 모든 것

### 19.1 PRINT 동작의 8가지 규칙

GW-BASIC의 PRINT는 단순해 보이지만 의외로 규칙이 많습니다.

1. **숫자 양쪽에 공백** — 양수면 부호 자리에 공백, 항상 끝에 공백 한 칸
2. **콤마는 14컬럼 인쇄 구역** — 다음 구역 시작 컬럼(1, 15, 29, …)으로 이동
3. **세미콜론은 공백 없음** — 즉시 이어 출력
4. **줄 끝 `;` 또는 `,`** — 줄바꿈 억제
5. **TAB(n)** — n 컬럼으로 절대 이동 (현재 위치보다 앞이면 다음 줄)
6. **SPC(n)** — 공백 n개
7. **PRINT USING** — 포맷 문자열 사용
8. **? = PRINT** — 단축 표기

### 19.2 컬럼 추적

Host는 *현재 커서 컬럼* 을 기억해야 합니다.

```ts
// src/host/console.ts
import * as readline from "node:readline";
import { Host } from "./host.js";
import { Rng } from "./rng.js";

export class ConsoleHost implements Host {
  private col = 1;        // 1-based
  private curRow = 1;
  private rng = new Rng(Date.now() & 0xFFFF);
  private rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  printAt(s: string): void {
    process.stdout.write(s);
    for (const ch of s) {
      if (ch === "\n") { this.curRow++; this.col = 1; }
      else if (ch === "\r") { this.col = 1; }
      else this.col++;
    }
  }
  println(s: string): void { this.printAt(s + "\n"); }
  column(): number { return this.col; }
  row(): number { return this.curRow; }

  inputLine(prompt: string): Promise<string | null> {
    return new Promise((resolve) => {
      this.rl.question(prompt, (ans) => { this.curRow++; this.col = 1; resolve(ans); });
    });
  }
  inkey(): string { return ""; }   // 콘솔 비차단 키 입력은 raw mode 필요 — 본 구현 생략

  cls(_mode: number): void { console.clear(); this.col = 1; this.curRow = 1; }
  setScreen(_mode: number): void {}
  setColor(_fg: number | null, _bg: number | null): void {}
  locate(row: number | null, col: number | null): void {
    if (row !== null) this.curRow = row;
    if (col !== null) this.col = col;
  }

  // 콘솔은 그래픽 미지원 — no-op (브라우저의 CanvasHost가 담당)
  pset(): void {}
  drawLine(): void {}
  drawCircle(): void {}
  paint(): void {}

  async sound(_freq: number, durMs: number): Promise<void> {
    await new Promise(r => setTimeout(r, durMs));
  }
  async play(_mml: string): Promise<void> {}

  now(): number { return Date.now(); }
  random(): number { return this.rng.next(); }
  lastRandom(): number { return this.rng.lastValue(); }
  seedRandom(s: number): void { this.rng.seed(s); }
}
```

### 19.3 PRINT USING 자세히

GW-BASIC의 PRINT USING은 별도의 미니 언어입니다. 구현해야 할 주요 토큰:

| 토큰 | 의미 |
|------|------|
| `#` | 숫자 자리 |
| `.` | 소수점 위치 |
| `,` | 천 단위 콤마 |
| `+` `-` | 부호 자리 (앞/뒤) |
| `**` | 빈 자리에 별표 채움 |
| `$$` | 빈 자리에 $ 채움 |
| `**$` | 별표 + $ |
| `^^^^` | 지수 표기 (E±NN) |
| `\ ... \` | 문자열 필드 (사이 공백 수만큼 길이) |
| `&` | 가변 길이 문자열 |
| `!` | 첫 글자만 |
| `_` | 다음 문자를 리터럴로 |

**예제**:

```basic
PRINT USING "##.##"; 3.14159     ' " 3.14" (필드 폭 5, 오른쪽 정렬)
PRINT USING "$$#,###.##"; 1234.5 ' " $1,234.50"
PRINT USING "\   \"; "Hello"     ' "Hello" (5자리 필드)
```

### 19.4 PRINT USING 구현 (확장판)

```ts
// src/runtime/print-using.ts
import { BasicValue } from "./value.js";

export function formatUsing(fmt: string, args: BasicValue[]): string {
  let out = "";
  let aIdx = 0;
  let i = 0;

  while (i < fmt.length) {
    const ch = fmt[i]!;

    // 리터럴 이스케이프
    if (ch === "_" && i + 1 < fmt.length) {
      out += fmt[i+1];
      i += 2;
      continue;
    }

    // 문자열 필드 \..\
    if (ch === "\\") {
      let j = i + 1;
      while (j < fmt.length && fmt[j] === " ") j++;
      if (fmt[j] === "\\") {
        const width = j - i + 1;   // \, 공백들, \
        const arg = args[aIdx++];
        const s = arg && arg.tag === "STR" ? arg.v : "";
        out += s.padEnd(width).slice(0, width);
        i = j + 1;
        continue;
      }
    }
    if (ch === "&") {
      const arg = args[aIdx++];
      out += arg && arg.tag === "STR" ? arg.v : "";
      i++;
      continue;
    }
    if (ch === "!") {
      const arg = args[aIdx++];
      out += arg && arg.tag === "STR" ? (arg.v[0] ?? "") : "";
      i++;
      continue;
    }

    // 숫자 필드: 시작 토큰 모음
    if (ch === "#" || ch === "+" || ch === "-" || ch === "$" || ch === "*" || ch === ".") {
      const start = i;
      // $$ ** **$ 같은 prefix 흡수
      while (i < fmt.length && /[#+\-,.$*]/.test(fmt[i]!)) i++;
      // 지수 표기 ^^^^
      let exp = "";
      while (i < fmt.length && fmt[i] === "^") { exp += fmt[i++]; }
      const fld = fmt.slice(start, i);
      const arg = args[aIdx++];
      out += formatNumberField(fld, exp.length, arg ? toNumSafe(arg) : 0);
      continue;
    }

    out += ch;
    i++;
  }
  return out;
}

function toNumSafe(v: BasicValue): number {
  return v.tag === "STR" ? 0 : v.v;
}

function formatNumberField(fld: string, expCount: number, n: number): string {
  // 옵션 추출
  const dollarPrefix = fld.startsWith("$$") || fld.startsWith("**$");
  const starFill = fld.startsWith("**") || fld.startsWith("**$");
  const leadingPlus  = fld.startsWith("+");
  const leadingMinus = fld.startsWith("-");
  const trailingPlus  = fld.endsWith("+");
  const trailingMinus = fld.endsWith("-");
  const useComma = fld.includes(",");

  // # 자리 수 (정수부, 소수부)
  const dot = fld.indexOf(".");
  const intDigits = countHash(dot < 0 ? fld : fld.slice(0, dot));
  const fracDigits = dot < 0 ? 0 : countHash(fld.slice(dot + 1));

  let abs = Math.abs(n);
  let s: string;
  if (expCount > 0) {
    // 지수 표기: ^^^^ 는 E±NN — E와 부호를 빼면 지수 자릿수는 expCount - 2
    const expSign = n === 0 ? 0 : Math.floor(Math.log10(abs));
    const mantissa = abs / Math.pow(10, expSign);
    s = mantissa.toFixed(fracDigits) + "E" + (expSign >= 0 ? "+" : "-")
        + Math.abs(expSign).toString().padStart(expCount - 2, "0");
  } else {
    s = abs.toFixed(fracDigits);
  }
  // 천 단위 콤마
  if (useComma) {
    const [ip, fp] = s.split(".");
    s = ip!.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (fp !== undefined ? "." + fp : "");
  }
  // 부호
  const sign = n < 0 ? "-" : (leadingPlus || trailingPlus ? "+" : "");
  // 채움: 필드 문자 하나가 출력 한 칸 — 필드 리터럴 전체 길이가 곧 출력 폭이다
  // (# 개수만 세면 콤마와 $$ 자리가 빠져 "$$#,###.##" 같은 필드의 폭이 어긋난다)
  const fieldWidth = fld.length + expCount;
  const fill = starFill ? "*" : " ";
  const dollar = dollarPrefix ? "$" : "";
  const need = fieldWidth - s.length - sign.length - dollar.length;

  if (need < 0) {
    // 오버플로 → % 부호
    return "%" + sign + dollar + s;
  }
  let pad = fill.repeat(need);
  if (trailingPlus || trailingMinus) {
    return pad + dollar + s + (sign || (trailingPlus ? "+" : " "));
  }
  return pad + sign + dollar + s;
}

function countHash(s: string): number {
  let c = 0;
  for (const ch of s) if (ch === "#") c++;
  return c;
}
```

### 19.5 INPUT의 동작

`INPUT "Name? "; A$`의 동작:

1. 프롬프트 `"Name? "` 출력
2. 사용자가 한 줄을 입력하고 엔터
3. 콤마로 분리해 변수에 할당
4. 따옴표가 있으면 따옴표 내용을 그대로 (콤마 포함)
5. 숫자 변수에 비숫자 입력 → "Redo from start" 출력 후 재시도

```ts
async function inputWithRetry(host: Host, prompt: string, vars: VarDesc[]): Promise<void> {
  while (true) {
    const text = await host.inputLine(prompt);
    const parts = splitInput(text, vars.length);
    try {
      for (let i = 0; i < vars.length; i++) {
        const v = vars[i]!;
        const raw = parts[i] ?? "";
        const isStr = v.name.endsWith("$");
        if (isStr) v.assign(STR(raw));
        else {
          const n = parseFloat(raw);
          if (!Number.isFinite(n) || raw.trim() === "") {
            throw new Error("redo");
          }
          v.assign(SNG(n));
        }
      }
      return;
    } catch {
      host.println("?Redo from start");
    }
  }
}
```

### 19.6 LINE INPUT

콤마 분리 없이 한 줄을 통째로 받습니다.

```basic
LINE INPUT "Title: "; T$
```

본 구현에서 LINE INPUT은 INPUT의 `suppressQuestion` + 단일 변수 + raw 모드로 다룹니다.

### 19.7 INKEY$

비차단 키 입력. 누른 키가 없으면 빈 문자열 반환.

```ts
// Host
inkey(): string {
  return this.keyBuffer.shift() ?? "";
}
```

브라우저에서는 keydown 이벤트로 buffer를 채우고, Node에서는 raw mode로 stdin에서 읽습니다.

### 19.8 LPRINT

라인 프린터로 보내는 출력. 본 구현에서는 콘솔과 동일하게 동작시키되, 별도 핸들러를 둘 수 있는 여지를 남깁니다.

---

## 20장. 제어 흐름 — GOTO, IF/THEN/ELSE, FOR/NEXT, WHILE/WEND

### 20.1 GOTO와 GOSUB의 본질적 차이

- GOTO: 그냥 점프. 돌아오지 않음.
- GOSUB: 점프 + 호출 스택에 복귀 주소 push.
- RETURN: 호출 스택 pop. 비어 있으면 `Return without GOSUB`.
- RETURN n: pop + 라인 n으로 점프 (드물게 쓰는 형태).

호출 스택 깊이는 GW-BASIC에서 약 12 이내였으나, 우리는 1000 정도로 넉넉하게 둡니다.

### 20.2 IF의 두 형태

**한 줄 IF (Single-line IF)**:

```basic
IF X > 0 THEN PRINT "POS" : Y = X ELSE Y = -X
```

THEN/ELSE 뒤가 *문장 리스트*입니다. 콜론으로 이어집니다.

**다중 라인 IF는 GW-BASIC에 없음**. (QuickBASIC부터 도입). 본 구현은 한 줄 IF만 지원합니다.

### 20.3 THEN 라인 번호

`IF X = 1 THEN 100`은 `IF X = 1 THEN GOTO 100`과 동일.

### 20.4 ELSE 매칭의 모호성

```basic
IF A THEN IF B THEN C ELSE D
```

`ELSE D`는 *가까운* IF에 매칭됩니다 (`IF B THEN C ELSE D`). 우리 파서는 재귀적으로 IF 안의 IF를 처리하므로 자연스럽게 해결됩니다.

### 20.5 FOR/NEXT의 정확한 의미

```basic
FOR I = start TO end STEP step
   ... body ...
NEXT I
```

의미는 다음과 같습니다.

```
I = start
while (step > 0 ? I <= end : I >= end):
   body
   I = I + step
```

⚠️ **중요**: `start > end` (step > 0)이면 본문이 *한 번도* 실행되지 않습니다. GW-BASIC도 그렇게 동작합니다.

⚠️ STEP 0은 무한 루프. GW-BASIC은 검사하지 않으므로 우리도 그대로 둡니다.

### 20.6 NEXT의 변수 생략

```basic
FOR I=1 TO 10
  FOR J=1 TO 5
    PRINT I, J
  NEXT
NEXT
```

`NEXT` 단독은 가장 안쪽 FOR를 닫습니다. `NEXT J, I`는 J → I 순서로 두 FOR를 닫습니다.

### 20.7 WHILE/WEND

```basic
WHILE cond
  body
WEND
```

FOR보다 단순합니다. cond가 거짓이면 WEND 다음으로 점프, 참이면 본문 실행 후 WEND가 다시 WHILE로 점프.

### 20.8 ON ... GOTO / GOSUB

```basic
ON X GOTO 100, 200, 300
```

X가 1이면 100, 2이면 200, 3이면 300. X가 0이거나 4 이상이면 다음 문장으로 통과(에러 아님).

X가 음수거나 255 초과면 `Illegal function call`.

### 20.9 STOP과 END

- `END`: 정상 종료
- `STOP`: 중단 (CONT로 재개 가능, 본 구현은 재개 미지원)

### 20.10 종합 예제

```basic
10 INPUT "How many"; N
20 IF N <= 0 THEN END
30 FOR I = 1 TO N
40   FOR J = 1 TO I
50     PRINT "*";
60   NEXT J
70   PRINT
80 NEXT I
90 GOTO 10
```

이 프로그램은 위 모든 기능을 사용합니다. 우리 VM에서 정상 동작합니다.

---

## 21장. 서브루틴 — GOSUB / RETURN

### 21.1 호출 스택 구현

`VM.callStack: number[]`. push/pop만 하면 됩니다. 깊이 제한은 다음과 같이.

```ts
case "CALL": {
  if (this.callStack.length >= 1000) {
    throw new BasicError(ERR.OUT_OF_MEMORY, "Too many GOSUBs");
  }
  this.callStack.push(this.pc);
  this.pc = ins.target;
  return;
}
```

### 21.2 재귀

GW-BASIC은 *원리적으로* GOSUB 재귀가 됩니다. 단, 매개변수 전달이 없으니 전역 변수로만 해야 합니다. 다음 팩토리얼:

```basic
10 N = 5
20 R = 1
30 GOSUB 100
40 PRINT R : END
100 IF N <= 1 THEN RETURN
110 R = R * N
120 N = N - 1
130 GOSUB 100
140 N = N + 1
150 RETURN
```

이런 재귀는 변수 보존이 없어 실수하기 쉽습니다. DEF FN이나 별도 *수동 스택*을 써야 합니다.

### 21.3 RETURN n (드문 형태)

```basic
500 GOSUB 1000
510 PRINT "이쪽으로 돌아오지 않을 수 있음"
1000 RETURN 2000
```

`RETURN 2000`은 호출 스택을 pop하지만 *복귀 주소를 무시* 하고 라인 2000으로 점프합니다. 본 구현에서 `RET_TO` 명령으로 처리.

### 21.4 호출 스택 디버깅

VM에 `getCallStack()` 메서드를 두면 디버거가 활용할 수 있습니다.

```ts
public getCallStack(): number[] {
  return [...this.callStack];
}
```

---

## 22장. 배열 — DIM과 다차원 인덱싱

### 22.1 묵시적 DIM

선언 없이 배열을 사용하면 GW-BASIC은 자동으로 0..10 범위(11개)로 DIM 합니다. 우리는 18장에서 이를 이미 구현했습니다.

### 22.2 다차원 평탄화

```ts
// 내부 표현은 1차원 배열
private idxFlat(box: ArrayBox, idx: number[]): number {
  let flat = 0;
  for (let i = 0; i < idx.length; i++) {
    flat = flat * box.dims[i]! + (idx[i]! - (box.baseIsOne ? 1 : 0));
  }
  return flat;
}
```

이는 **row-major** 순서입니다. C와 같습니다 (Fortran은 column-major).

### 22.3 ERASE

배열을 해제합니다.

```basic
ERASE A, B
```

본 구현 추가:

```ts
case "ERASE": {
  for (const n of ins.names) this.env.erase(n);
  return;
}
```

`Env.erase(name): void { this.arrays.delete(name); }`.

### 22.4 OPTION BASE

프로그램 시작 부분에 한 번 쓸 수 있습니다. 본 구현은 `OPTION BASE 1`을 만나면 즉시 `env.optionBase = 1`로 설정합니다. ⚠️ 이미 DIM된 배열이 있으면 에러.

### 22.5 큰 배열 성능

`Array<BasicValue>`를 쓰면 객체 참조 배열이 되어 캐시 친화도가 떨어집니다. 100만 원소 이상 다루는 경우 `Float64Array` / `Int32Array` 같은 typed array로 백엔드를 바꾸는 것이 좋습니다.

본 구현은 단순함을 위해 `Array<BasicValue>`를 유지하지만, 다음과 같이 *전문화 가능* 한 구조를 둘 수 있습니다.

```ts
type ArrayBox =
  | { kind: "REF"; data: BasicValue[]; dims: number[] }
  | { kind: "F64"; data: Float64Array; dims: number[] }
  | { kind: "I32"; data: Int32Array; dims: number[] };
```

이는 27-31장에서 *최적화* 주제로 다룹니다.

### 22.6 LBOUND / UBOUND

```basic
PRINT LBOUND(A), UBOUND(A)      ' 보통 0, 10
PRINT LBOUND(A, 2)              ' 2번째 차원의 하한
```

내장 함수로 추가. `Env.bounds(name, dim)`로.

---

> 5부 (1) 끝.
# 제5부 · 런타임 (2) — 표준 함수 라이브러리

## 23장. 문자열 함수

### 23.1 함수 디스패치 테이블

```ts
// src/runtime/builtins.ts
import { BasicValue, INT, SNG, DBL, STR } from "./value.js";
import { BasicError, ERR } from "../common/types.js";
import { toNum, toStr } from "./ops.js";
import type { VM } from "../vm/vm.js";

type Builtin = (args: BasicValue[], vm: VM) => BasicValue;

export const BUILTINS: Record<string, Builtin> = {
  // 문자열
  "LEN":     (a) => INT(toStr(a[0]!).length),
  "LEFT$":   (a) => leftStr(a),
  "RIGHT$":  (a) => rightStr(a),
  "MID$":    (a) => midStr(a),
  "INSTR":   (a) => instrFn(a),
  "STR$":    (a) => STR(formatStr(a[0]!)),
  "VAL":     (a) => valFn(a[0]!),
  "CHR$":    (a) => STR(String.fromCharCode(toNum(a[0]!) | 0)),
  "ASC":     (a) => INT((toStr(a[0]!).charCodeAt(0) || 0)),
  "STRING$": (a) => stringRepeat(a),
  "SPACE$":  (a) => STR(" ".repeat(Math.max(0, toNum(a[0]!) | 0))),
  "HEX$":    (a) => STR((toNum(a[0]!) | 0).toString(16).toUpperCase()),
  "OCT$":    (a) => STR((toNum(a[0]!) | 0).toString(8)),

  // 수학
  "ABS": (a) => SNG(Math.abs(toNum(a[0]!))),
  "SGN": (a) => INT(Math.sign(toNum(a[0]!))),
  // INT/FIX 결과가 16비트를 넘으면 INT 태그로 넣을 수 없으므로 DBL로
  "INT": (a) => { const f = Math.floor(toNum(a[0]!));
                  return (f >= -32768 && f <= 32767) ? INT(f) : DBL(f); },
  "FIX": (a) => { const t = Math.trunc(toNum(a[0]!));
                  return (t >= -32768 && t <= 32767) ? INT(t) : DBL(t); },
  "SQR": (a) => DBL(Math.sqrt(toNum(a[0]!))),
  "SIN": (a) => DBL(Math.sin(toNum(a[0]!))),
  "COS": (a) => DBL(Math.cos(toNum(a[0]!))),
  "TAN": (a) => DBL(Math.tan(toNum(a[0]!))),
  "ATN": (a) => DBL(Math.atan(toNum(a[0]!))),
  "LOG": (a) => DBL(Math.log(toNum(a[0]!))),
  "EXP": (a) => DBL(Math.exp(toNum(a[0]!))),

  // 변환
  "CINT": (a) => { const n = Math.round(toNum(a[0]!));
                   if (n < -32768 || n > 32767) throw new BasicError(ERR.OVERFLOW, "Overflow");
                   return INT(n); },
  "CSNG": (a) => SNG(toNum(a[0]!)),
  "CDBL": (a) => DBL(toNum(a[0]!)),

  // 환경
  "RND":    (a, vm) => SNG(rndFn(a, vm)),
  "TIMER":  (_a, vm) => SNG(vm.host.now() / 1000),
  "INKEY$": (_a, vm) => STR(vm.host.inkey()),

  // 화면
  "POS":    (_a, vm) => INT(vm.host.column()),
  "CSRLIN": (_a, vm) => INT(vm.host.row()),
};

export function callBuiltin(name: string, args: BasicValue[], vm: VM): BasicValue {
  const fn = BUILTINS[name];
  if (!fn) throw new BasicError(ERR.SYNTAX, `Unknown builtin ${name}`);
  return fn(args, vm);
}
```

### 23.2 LEFT$ / RIGHT$ / MID$

```ts
function leftStr(args: BasicValue[]): BasicValue {
  const s = toStr(args[0]!);
  const n = Math.max(0, toNum(args[1]!) | 0);
  return STR(s.slice(0, n));
}
function rightStr(args: BasicValue[]): BasicValue {
  const s = toStr(args[0]!);
  const n = Math.max(0, toNum(args[1]!) | 0);
  return STR(n === 0 ? "" : s.slice(-n));
}
function midStr(args: BasicValue[]): BasicValue {
  const s = toStr(args[0]!);
  const start = (toNum(args[1]!) | 0);    // 1-based
  if (start < 1) throw new BasicError(ERR.ILLEGAL_FUNCTION_CALL, "MID$ start");
  if (args.length >= 3) {
    const len = Math.max(0, toNum(args[2]!) | 0);
    return STR(s.substr(start - 1, len));
  }
  return STR(s.substr(start - 1));
}
```

⚠️ **주의**: `MID$`는 *문장*으로도 쓸 수 있습니다 (`MID$(A$, 3, 2) = "XX"`). 본 구현은 함수 형태만 지원하지만, *MID$ 문* 을 추가하려면 파서에 특수 케이스가 필요합니다 (좌변 lvalue로 인정).

### 23.3 INSTR

```basic
INSTR(haystack$, needle$)
INSTR(start, haystack$, needle$)
```

```ts
function instrFn(args: BasicValue[]): BasicValue {
  let start = 1, hi = 0;
  if (args.length === 3) {
    start = Math.max(1, toNum(args[0]!) | 0);
    hi = 1;
  }
  const hay = toStr(args[hi]!);
  const needle = toStr(args[hi + 1]!);
  if (needle === "") return INT(start);   // 빈 문자열은 항상 start
  const idx = hay.indexOf(needle, start - 1);
  return INT(idx < 0 ? 0 : idx + 1);
}
```

### 23.4 STRING$

```basic
STRING$(n, char_or_code)
```

```ts
function stringRepeat(args: BasicValue[]): BasicValue {
  const n = Math.max(0, toNum(args[0]!) | 0);
  const ch = args[1]!;
  const code = ch.tag === "STR" ? (ch.v.charCodeAt(0) || 0) : (toNum(ch) | 0);
  return STR(String.fromCharCode(code).repeat(n));
}
```

### 23.5 STR$ 의 공백 규칙

```ts
function formatStr(v: BasicValue): string {
  const n = toNum(v);
  const s = formatNumberPlain(n, v.tag as "INT"|"SNG"|"DBL");
  return n >= 0 ? " " + s : s;
}

// 16장 print-format.ts의 숫자 형식과 동일하되 *끝 공백 없이* 반환
function formatNumberPlain(n: number, tag: "INT" | "SNG" | "DBL"): string {
  if (tag === "INT") return Math.trunc(n).toString();
  if (Number.isInteger(n) && Math.abs(n) < 1e15) return n.toString();
  const prec = tag === "DBL" ? 16 : 7;
  let s = n.toPrecision(prec);
  if (s.includes(".") && !s.includes("E") && !s.includes("e")) {
    s = s.replace(/0+$/, "").replace(/\.$/, "");
  }
  return s;
}
```

### 23.6 VAL

문자열을 숫자로 변환. 앞에서부터 *유효한 숫자 부분만* 읽고 나머지는 무시.

```ts
function valFn(v: BasicValue): BasicValue {
  const s = toStr(v).trim();
  const m = s.match(/^[+-]?(\d+\.?\d*|\.\d+)([eEdD][+-]?\d+)?/);
  if (!m) return SNG(0);
  return SNG(parseFloat(m[0].replace(/d/i, "e")));
}
```

⚠️ 16진수 / 8진수 (`&H`, `&O`)도 인식하려면 추가 분기가 필요합니다. 본 구현에서는 생략.

---

## 24장. 수학 함수

### 24.1 RND의 미묘함

GW-BASIC의 `RND`는 *유사 난수*입니다. 인자에 따라 동작이 다릅니다.

| 호출 | 동작 |
|------|------|
| `RND` 또는 `RND(1)` | 새 난수 (0 이상 1 미만) |
| `RND(0)` | 마지막에 반환한 난수 |
| `RND(-n)` | n으로 시드 후 새 난수 |

```ts
function rndFn(args: BasicValue[], vm: VM): number {
  if (args.length === 0) return vm.host.random();
  const x = toNum(args[0]!);
  if (x < 0) { vm.host.seedRandom(x); return vm.host.random(); }
  if (x === 0) return vm.host.lastRandom();
  return vm.host.random();
}
```

### 24.2 시드 가능한 난수

`Math.random()`은 시드를 줄 수 없으므로 우리는 자체 PRNG를 구현합니다. 간단한 *Linear Congruential* 또는 *Mulberry32*를 씁니다.

```ts
// src/host/rng.ts
export class Rng {
  private state: number;
  private last = 0;
  constructor(seed = 1) { this.state = seed | 0 || 1; }

  seed(s: number): void { this.state = (s | 0) || 1; }

  next(): number {
    // Mulberry32
    let t = (this.state + 0x6D2B79F5) | 0;
    this.state = t;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    const r = ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    this.last = r;
    return r;
  }

  lastValue(): number { return this.last; }
}
```

Host 구현에 이를 사용:

```ts
random() { return this.rng.next(); }
lastRandom() { return this.rng.lastValue(); }
seedRandom(s: number) { this.rng.seed(s); }
```

### 24.3 RANDOMIZE

```basic
RANDOMIZE TIMER     ' 시드를 현재 시각으로
```

본 구현에서 인자 없이 `RANDOMIZE`만 쓰면 GW-BASIC은 사용자에게 시드를 물었습니다. 우리는 단순화를 위해 `Date.now()`를 시드로 씁니다.

### 24.4 삼각함수와 라디안

GW-BASIC의 `SIN/COS/TAN`은 *라디안*을 받습니다. JavaScript와 같습니다.

### 24.5 LOG와 EXP

`LOG(x)`는 자연로그. 인자 ≤ 0이면 `Illegal function call`.

```ts
"LOG": (a) => {
  const x = toNum(a[0]!);
  if (x <= 0) throw new BasicError(ERR.ILLEGAL_FUNCTION_CALL, "LOG of non-positive");
  return DBL(Math.log(x));
},
```

### 24.6 ABS / SGN / INT / FIX 정리

- ABS(-3.7) = 3.7
- SGN(-3) = -1, SGN(0) = 0, SGN(3) = 1
- INT(-3.7) = -4 (floor)
- FIX(-3.7) = -3 (trunc)

---

## 25장. DATA / READ / RESTORE

### 25.1 동작 모델

DATA는 *프로그램 어디에나* 둘 수 있습니다. 컴파일러가 **DATA 풀** 을 모아 둡니다(15장).

```basic
10 DATA 1, 2, "hello"
20 DATA 3.14
30 READ A, B, S$, X
40 PRINT A; B; S$; X
```

읽기 순서는 *소스 라인 순*입니다. 콜론으로 이어진 DATA도 같은 순서.

### 25.2 RESTORE

```basic
RESTORE        ' 데이터 포인터를 처음으로
RESTORE 100    ' 라인 100의 첫 DATA로
```

### 25.3 타입 매칭

READ 대상이 숫자 변수인데 DATA 항목이 숫자로 해석되지 않으면 GW-BASIC은 해당 DATA 라인을 가리키는 `Syntax error`를 냅니다 (본 구현도 동일 — 16장 READ 참고). DATA의 *bare string* 이 숫자처럼 보이면(예: `DATA -5`) 숫자로 파싱됩니다. 본 구현은 컴파일 단계에서 `kind: "num" | "str"`로 분류하고, 숫자 READ 시점에 다시 검사합니다.

### 25.4 OUT OF DATA

DATA를 모두 읽고 또 READ하면 `Out of DATA`. 

### 25.5 테스트

```ts
it("DATA / READ / RESTORE", async () => {
  const out: string[] = [];
  const host = makeMockHost(out);
  await runSrc(`
    10 DATA 1, 2, 3
    20 FOR I=1 TO 3 : READ X : PRINT X; : NEXT
    30 RESTORE
    40 READ Y : PRINT Y
  `, host);
  expect(out.join("")).toContain(" 1  2  3");
  expect(out.join("")).toContain("1");  // RESTORE 후 다시 1
});
```

---

## 26장. 사용자 정의 함수 DEF FN

### 26.1 단일식 함수

```basic
10 DEF FN SQUARE(X) = X * X
20 PRINT FN SQUARE(5)
```

GW-BASIC의 DEF FN은 *한 줄짜리 표현식 함수* 입니다. 다중 라인 함수는 QuickBASIC의 `FUNCTION`이 도입된 후입니다.

### 26.2 매개변수 스코프

매개변수는 함수 내부에서만 의미를 가집니다. 같은 이름의 전역 변수가 있으면 *섀도잉*. 함수 끝나면 원래 값 복원.

⚠️ GW-BASIC 실제 동작은 매개변수가 *전역 변수를 임시로 덮어씌움*. 함수 호출 후 다시 복원되는 식. 본 구현은 frame stack을 써서 더 깔끔하게 처리합니다.

### 26.3 컴파일과 호출

15장에서 이미 `DEF_FN` / `CALL_FN` 명령을 만들었습니다. 16장에서 자리만 잡아 둔 `CALL_FN` 디스패치를 여기서 채웁니다. sub-VM을 따로 만들지 않고, 본문(단일 표현식)을 현재 VM에서 *동기 평가*합니다.

```ts
case "CALL_FN": {
  const fn = this.program.defFns.get(ins.name);
  if (!fn) throw new BasicError(ERR.SYNTAX, `Undefined FN ${ins.name}`);
  if (fn.params.length !== ins.nargs) {
    throw new BasicError(ERR.SYNTAX, `FN ${ins.name} arity mismatch`);
  }
  const args: BasicValue[] = [];
  for (let i = 0; i < ins.nargs; i++) args.unshift(this.pop());
  // 매개변수를 frame에 *새 바인딩*으로 push (setLocal — 18.4절 참고.
  // set을 쓰면 빈 frame을 지나쳐 전역 변수를 덮어써 섀도잉이 깨진다)
  this.env.pushFrame();
  for (let i = 0; i < fn.params.length; i++) this.env.setLocal(fn.params[i]!, args[i]!);
  // 본문은 단일 표현식이므로 여기서 동기 실행 (sub-VM 없이 직접)
  const savedStack = this.stack;
  this.stack = [];
  this.evalExprBody(fn.body);
  const result = this.pop();
  this.stack = savedStack;
  this.env.popFrame();
  this.push(result);
  return;
}

private evalExprBody(body: Op[]): void {
  // body는 동기 명령들로만 이루어졌다고 가정 (표현식에는 비동기 명령이 없다)
  let p = 0;
  while (p < body.length) {
    const ins = body[p++]!;
    if (ins.op === "RET") break;
    this.dispatchSync(ins);
  }
}
```

### 26.4 재귀 DEF FN?

GW-BASIC의 DEF FN은 재귀를 지원하지 않습니다 (정의에 자기 자신 호출 금지). 우리도 그대로 둡니다 — 단, 매개변수를 frame으로 처리했기 때문에 *기술적으로* 동작은 합니다. 의도된 사용은 아닙니다.

### 26.5 종합 예제

```basic
10 DEF FN SQ(X) = X * X
20 DEF FN HYP(A, B) = SQR(FN SQ(A) + FN SQ(B))
30 PRINT FN HYP(3, 4)
```

출력: `5`. 함수 안에서 다른 함수를 호출하는 것도 됩니다.

---

> 5부 끝. 표준 라이브러리까지 완성. 다음은 그래픽과 사운드입니다.
# 제6부 · 그래픽과 사운드

## 27장. SCREEN 모드와 그래픽 명령

### 27.1 SCREEN 모드 개요

GW-BASIC의 SCREEN 모드는 IBM 그래픽 어댑터에 의존합니다. 본 구현은 *현대 캔버스*에 맞춰 단순화합니다.

| 모드 | 원본 해상도 | 색상 | 본 구현 매핑 |
|------|------------|------|--------------|
| 0 | 텍스트 80×25 | 16색 | 텍스트만 (그리기 무시) |
| 1 | 320×200 | 4색 (팔레트) | 320×200 캔버스, 16색 팔레트 사용 |
| 2 | 640×200 | 2색 | 640×200 캔버스, 흑백 |
| 7 | 320×200 | 16색 (EGA) | 동일 |
| 8 | 640×200 | 16색 | 동일 |
| 9 | 640×350 | 16색 | 동일 |
| 12 | 640×480 | 16색 | 본 구현 추가 |
| 13 | 320×200 | 256색 | 본 구현 추가 |

본 구현 기본은 *모드 12* (640×480, 16색).

### 27.2 16색 팔레트 (CGA/EGA 표준)

```ts
// src/host/palette.ts
export const PALETTE_16: [number, number, number][] = [
  [0x00, 0x00, 0x00],   // 0 BLACK
  [0x00, 0x00, 0xAA],   // 1 BLUE
  [0x00, 0xAA, 0x00],   // 2 GREEN
  [0x00, 0xAA, 0xAA],   // 3 CYAN
  [0xAA, 0x00, 0x00],   // 4 RED
  [0xAA, 0x00, 0xAA],   // 5 MAGENTA
  [0xAA, 0x55, 0x00],   // 6 BROWN
  [0xAA, 0xAA, 0xAA],   // 7 LIGHT GRAY
  [0x55, 0x55, 0x55],   // 8 DARK GRAY
  [0x55, 0x55, 0xFF],   // 9 LIGHT BLUE
  [0x55, 0xFF, 0x55],   // 10 LIGHT GREEN
  [0x55, 0xFF, 0xFF],   // 11 LIGHT CYAN
  [0xFF, 0x55, 0x55],   // 12 LIGHT RED
  [0xFF, 0x55, 0xFF],   // 13 LIGHT MAGENTA
  [0xFF, 0xFF, 0x55],   // 14 YELLOW
  [0xFF, 0xFF, 0xFF],   // 15 WHITE
];
```

### 27.3 CanvasHost 구현

```ts
// src/host/canvas-host.ts
import { Host } from "./host.js";
import { PALETTE_16 } from "./palette.js";
import { Rng } from "./rng.js";
import { playMml } from "../runtime/mml.js";   // 28장 — 이 import가 없으면 play()가 컴파일되지 않는다

export class CanvasHost implements Host {
  private ctx: CanvasRenderingContext2D;
  private width = 640;
  private height = 480;
  private fg = 15;
  private bg = 0;
  private cursorX = 0;
  private cursorY = 0;
  private textCol = 1;
  private textRow = 1;
  private cellW = 8;
  private cellH = 16;
  private rng = new Rng(Date.now() & 0xFFFF);
  private inputResolver: ((s:string)=>void) | null = null;
  private keyBuffer: string[] = [];

  constructor(private canvas: HTMLCanvasElement) {
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.ctx = canvas.getContext("2d")!;
    this.cls(0);
    canvas.tabIndex = 0;
    canvas.addEventListener("keydown", (e) => this.onKey(e));
  }

  // ── 텍스트 ────────────────────────────────────
  printAt(s: string): void {
    for (const ch of s) {
      if (ch === "\n") { this.cursorY += this.cellH; this.cursorX = 0; this.textRow++; this.textCol = 1; continue; }
      if (ch === "\r") { this.cursorX = 0; this.textCol = 1; continue; }
      this.drawChar(ch);
      this.cursorX += this.cellW;
      this.textCol++;
      if (this.cursorX >= this.width) {
        this.cursorX = 0;
        this.cursorY += this.cellH;
        this.textRow++; this.textCol = 1;
      }
    }
  }
  println(s: string): void { this.printAt(s + "\n"); }
  column(): number { return this.textCol; }
  row(): number { return this.textRow; }

  private drawChar(ch: string): void {
    this.ctx.fillStyle = this.colorRGB(this.bg);
    this.ctx.fillRect(this.cursorX, this.cursorY, this.cellW, this.cellH);
    this.ctx.fillStyle = this.colorRGB(this.fg);
    this.ctx.font = `${this.cellH - 2}px monospace`;
    this.ctx.textBaseline = "top";
    this.ctx.fillText(ch, this.cursorX, this.cursorY);
  }

  // ── 입력 ─────────────────────────────────────
  inputLine(prompt: string): Promise<string> {
    this.printAt(prompt);
    return new Promise<string>((resolve) => {
      this.inputResolver = resolve;
      this.lineBuffer = "";
    });
  }
  private lineBuffer = "";
  private onKey(e: KeyboardEvent): void {
    if (this.inputResolver) {
      if (e.key === "Enter") {
        this.println("");
        const line = this.lineBuffer;
        this.lineBuffer = "";
        const r = this.inputResolver;
        this.inputResolver = null;
        r(line);
      } else if (e.key === "Backspace") {
        if (this.lineBuffer.length > 0) {
          this.lineBuffer = this.lineBuffer.slice(0, -1);
          this.cursorX -= this.cellW;
          this.ctx.fillStyle = this.colorRGB(this.bg);
          this.ctx.fillRect(this.cursorX, this.cursorY, this.cellW, this.cellH);
        }
      } else if (e.key.length === 1) {
        this.lineBuffer += e.key;
        this.printAt(e.key);
      }
      e.preventDefault();
      return;
    }
    if (e.key.length === 1) this.keyBuffer.push(e.key);
    else if (e.key === "Enter") this.keyBuffer.push("\r");
  }
  inkey(): string { return this.keyBuffer.shift() ?? ""; }

  // ── 화면 제어 ─────────────────────────────────
  cls(_mode: number): void {
    this.ctx.fillStyle = this.colorRGB(this.bg);
    this.ctx.fillRect(0, 0, this.width, this.height);
    this.cursorX = 0; this.cursorY = 0;
    this.textRow = 1; this.textCol = 1;
  }
  setScreen(_mode: number): void { this.cls(0); }
  setColor(fg: number | null, bg: number | null): void {
    if (fg !== null) this.fg = fg & 15;
    if (bg !== null) this.bg = bg & 15;
  }
  locate(row: number | null, col: number | null): void {
    if (row !== null) { this.textRow = row; this.cursorY = (row - 1) * this.cellH; }
    if (col !== null) { this.textCol = col; this.cursorX = (col - 1) * this.cellW; }
  }

  // ── 픽셀/도형 ─────────────────────────────────
  pset(x: number, y: number, color: number | null, _step: boolean, preset: boolean): void {
    const c = color !== null ? color : (preset ? this.bg : this.fg);
    const img = this.ctx.createImageData(1, 1);
    const [r, g, b] = PALETTE_16[c & 15]!;
    img.data[0] = r; img.data[1] = g; img.data[2] = b; img.data[3] = 255;
    this.ctx.putImageData(img, x, y);
  }
  drawLine(x1: number|null, y1: number|null, x2: number, y2: number,
           color: number | null, _fromStep: boolean, _toStep: boolean,
           mode: "B"|"BF"|null): void {
    const c = color !== null ? color : this.fg;
    this.ctx.strokeStyle = this.colorRGB(c);
    this.ctx.fillStyle = this.colorRGB(c);
    if (x1 === null) { x1 = this.cursorX; y1 = this.cursorY; }
    if (mode === "B") {
      this.ctx.strokeRect(Math.min(x1, x2), Math.min(y1!, y2),
                          Math.abs(x2 - x1), Math.abs(y2 - y1!));
    } else if (mode === "BF") {
      this.ctx.fillRect(Math.min(x1, x2), Math.min(y1!, y2),
                        Math.abs(x2 - x1), Math.abs(y2 - y1!));
    } else {
      this.ctx.beginPath();
      this.ctx.moveTo(x1 + 0.5, y1! + 0.5);
      this.ctx.lineTo(x2 + 0.5, y2 + 0.5);
      this.ctx.stroke();
    }
  }
  drawCircle(x: number, y: number, r: number,
             color: number | null,
             start: number | null, end: number | null,
             aspect: number | null, _step: boolean): void {
    const c = color !== null ? color : this.fg;
    this.ctx.strokeStyle = this.colorRGB(c);
    this.ctx.beginPath();
    const sa = start ?? 0;
    const ea = end ?? Math.PI * 2;
    const a = aspect ?? (this.width === 320 ? 0.83 : 1.0);
    this.ctx.ellipse(x, y, r, r * a, 0, sa, ea);
    this.ctx.stroke();
  }
  paint(x: number, y: number, fill: number | null, _border: number | null, _step: boolean): void {
    // 단순 flood fill (성능 무시 버전)
    const c = fill !== null ? fill : this.fg;
    const targetRGBA = (() => {
      const [r, g, b] = PALETTE_16[c & 15]!;
      return (255 << 24) | (b << 16) | (g << 8) | r;
    })();
    const img = this.ctx.getImageData(0, 0, this.width, this.height);
    const data = new Uint32Array(img.data.buffer);
    const startIdx = y * this.width + x;
    const startCol = data[startIdx];
    if (startCol === targetRGBA) return;
    const queue: number[] = [startIdx];
    while (queue.length > 0) {
      const idx = queue.pop()!;
      if (data[idx] !== startCol) continue;
      data[idx] = targetRGBA;
      const xx = idx % this.width;
      if (xx > 0) queue.push(idx - 1);
      if (xx < this.width - 1) queue.push(idx + 1);
      if (idx >= this.width) queue.push(idx - this.width);
      if (idx < data.length - this.width) queue.push(idx + this.width);
    }
    this.ctx.putImageData(img, 0, 0);
  }

  private colorRGB(c: number): string {
    const [r, g, b] = PALETTE_16[c & 15]!;
    return `rgb(${r},${g},${b})`;
  }

  // ── 시간 / 난수 ───────────────────────────────
  now(): number { return performance.now(); }
  random(): number { return this.rng.next(); }
  lastRandom(): number { return this.rng.lastValue(); }
  seedRandom(s: number): void { this.rng.seed(s); }

  // ── 사운드 ────────────────────────────────────
  private audioCtx?: AudioContext;
  async sound(freq: number, durMs: number): Promise<void> {
    if (typeof AudioContext === "undefined") return;
    if (!this.audioCtx) this.audioCtx = new AudioContext();
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.frequency.value = freq;
    osc.type = "square";
    gain.gain.value = 0.1;
    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    osc.start();
    await new Promise(r => setTimeout(r, durMs));
    osc.stop();
  }

  // PLAY는 28장에서
  async play(mml: string): Promise<void> {
    await playMml(this, mml);
  }
}
```

⚠️ 위 paint의 flood fill은 *큰 영역*에서는 매우 느립니다. 실용 구현은 scanline flood fill이 필요합니다.

### 27.4 STEP 좌표

```basic
PSET (10, 10)
PSET STEP (5, 0)    ' 현재 위치에서 (+5, 0)
```

본 구현 단순화: STEP 모드에서는 *마지막 그래픽 위치*를 host가 기억하고 더해 줍니다 (생략 코드). 실제 GW-BASIC은 픽셀 좌표 (x, y)를 항상 갱신합니다.

### 27.5 종합 예제 — 만델브로

```basic
10 SCREEN 12 : CLS
20 FOR PY = 0 TO 479
30   FOR PX = 0 TO 639
40     CR = (PX - 320) / 200 - 0.5
50     CI = (PY - 240) / 200
60     ZR = 0 : ZI = 0 : N = 0
70     WHILE (ZR*ZR + ZI*ZI < 4) AND (N < 32)
80       T = ZR*ZR - ZI*ZI + CR
90       ZI = 2*ZR*ZI + CI
100      ZR = T
110      N = N + 1
120    WEND
130    PSET (PX, PY), N MOD 16
140  NEXT PX
150 NEXT PY
160 END
```

이 프로그램이 우리 VM에서 (조금 느리지만) 동작합니다. 스크린 12 모드는 640×480, 16색.

---

## 28장. 사운드 — SOUND와 PLAY (MML)

### 28.1 SOUND 명령

```basic
SOUND 440, 18.2     ' 라음 1초 (18.2 클럭 = 1초)
```

GW-BASIC에서 길이 단위는 *18.2 ticks/sec* (PIT 타이머). 본 구현에서는 *밀리초*로 단순화하거나 변환합니다.

### 28.2 PLAY와 MML

PLAY는 *Music Macro Language*를 받습니다. 다음과 같은 명령들로 구성:

| 명령 | 의미 |
|------|------|
| `A`-`G` | 음표 (현재 옥타브) |
| `+`, `#` | 반음 올림 |
| `-` | 반음 내림 |
| `O` n | 옥타브 (0-6) |
| `>` `<` | 옥타브 ±1 |
| `L` n | 기본 음 길이 (1=온음표, 4=4분음표, 8=8분음표 ...) |
| `T` n | 템포 (32-255 BPM) |
| `P` n | 쉼표 (길이 n) |
| `MN` `ML` `MS` | 노트 길이 모드 (Normal/Legato/Staccato) |
| `MF` `MB` | Foreground/Background (큐 동기) |

### 28.3 MML 파서/플레이어

```ts
// src/runtime/mml.ts
import type { CanvasHost } from "../host/canvas-host.js";

const NOTE_FREQ_C0 = 16.351;       // C0
const NOTE_OFFSET: Record<string, number> = {
  C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11,
};

interface MmlState {
  octave: number;
  length: number;        // 분모 (4 = 4분음표)
  tempo: number;         // BPM
  mode: "N" | "L" | "S"; // Normal / Legato / Staccato
}

export async function playMml(host: CanvasHost, mml: string): Promise<void> {
  const s: MmlState = { octave: 4, length: 4, tempo: 120, mode: "N" };
  let i = 0;
  const u = mml.toUpperCase();

  const wholeNoteMs = (): number => 60000 / s.tempo * 4;

  const noteMs = (len: number, dotted: boolean): number => {
    let ms = wholeNoteMs() / len;
    if (dotted) ms *= 1.5;
    if (s.mode === "L") return ms;
    if (s.mode === "S") return ms * 0.75;
    return ms * 0.875;     // Normal: 음과 음 사이 약간의 공백
  };

  // noUncheckedIndexedAccess 대응: 범위 밖 인덱스는 빈 문자열로
  const at = (k: number): string => u[k] ?? "";

  const readNum = (): number => {
    let n = "";
    while (i < u.length && at(i) >= "0" && at(i) <= "9") n += u[i++];
    return parseInt(n, 10);
  };

  while (i < u.length) {
    const ch = u[i++]!;
    if (ch === " " || ch === "\t") continue;

    if (ch >= "A" && ch <= "G") {
      let semi = NOTE_OFFSET[ch]!;
      if (at(i) === "+" || at(i) === "#") { semi++; i++; }
      else if (at(i) === "-") { semi--; i++; }
      let len = s.length;
      if (at(i) >= "0" && at(i) <= "9") len = readNum();
      let dotted = false;
      if (at(i) === ".") { dotted = true; i++; }
      const freq = NOTE_FREQ_C0 * Math.pow(2, s.octave + semi / 12);
      const ms = noteMs(len, dotted);
      await host.sound(freq, ms);
      continue;
    }

    if (ch === "O") { s.octave = readNum(); continue; }
    if (ch === ">") { s.octave++; continue; }
    if (ch === "<") { s.octave--; continue; }
    if (ch === "L") { s.length = readNum(); continue; }
    if (ch === "T") { s.tempo = readNum(); continue; }
    if (ch === "P" || ch === "R") {
      let len = s.length;
      if (at(i) >= "0" && at(i) <= "9") len = readNum();
      await new Promise(r => setTimeout(r, wholeNoteMs() / len));
      continue;
    }
    if (ch === "M") {
      const m = u[i++];
      if (m === "N") s.mode = "N";
      else if (m === "L") s.mode = "L";
      else if (m === "S") s.mode = "S";
      // MF/MB는 본 구현에서 무시
      continue;
    }
    if (ch === "N") {
      const n = readNum();
      if (n === 0) {
        await new Promise(r => setTimeout(r, wholeNoteMs() / s.length));
      } else {
        const freq = 440 * Math.pow(2, (n - 33) / 12);
        await host.sound(freq, noteMs(s.length, false));
      }
      continue;
    }
    // 알 수 없는 문자는 무시
  }
}
```

### 28.4 PLAY로 곡 연주

```basic
10 PLAY "T120 O5 L4 CDEFGAB>C"
20 PLAY "L8 CC GG AA G2"          ' 작은별 부분
```

### 28.5 BEEP

`BEEP`은 본 구현에서 800Hz로 200ms 사운드를 냅니다 (CPU 스피커 흉내).

### 28.6 동시 발음?

GW-BASIC은 한 번에 한 음만 가능합니다 (단음 기기). 본 구현도 단음만 지원. 다성음을 원하면 별도 채널(WebAudio 노드 분리) 도입이 필요합니다.

---

> 6부 끝. 이제 멀티미디어 BASIC이 동작합니다.
# 제7부 · 도구와 통합

## 29장. REPL — 즉시 실행 환경

### 29.1 REPL의 두 모드

GW-BASIC의 REPL은 *직접 모드*와 *프로그램 모드*를 동시에 지원합니다.

- 라인 번호 없는 입력 → 즉시 실행
- 라인 번호 있는 입력 → 프로그램 저장소에 저장/대체
- 같은 라인 번호 + 빈 본문 → 해당 라인 삭제

### 29.2 ProgramStore

```ts
// src/repl/store.ts
export class ProgramStore {
  private lines = new Map<number, string>();   // 라인 번호 → 원본 텍스트

  insert(line: number, text: string): void {
    if (text.trim() === "") this.lines.delete(line);
    else this.lines.set(line, text);
  }
  remove(line: number): void { this.lines.delete(line); }
  clear(): void { this.lines.clear(); }
  list(from = 0, to = Number.MAX_SAFE_INTEGER): string[] {
    const out: string[] = [];
    for (const n of [...this.lines.keys()].sort((a,b) => a-b)) {
      if (n >= from && n <= to) out.push(`${n} ${this.lines.get(n)}`);
    }
    return out;
  }
  toSource(): string {
    return this.list().join("\n");
  }
}
```

### 29.3 REPL 메인 루프

```ts
// src/repl/repl.ts
import { Lexer } from "../lexer/lexer.js";
import { Parser } from "../parser/parser.js";
import { Compiler } from "../compiler/compiler.js";
import { VM } from "../vm/vm.js";
import { ProgramStore } from "./store.js";
import type { Host } from "../host/host.js";

export class Repl {
  store = new ProgramStore();

  constructor(private host: Host) {}

  async run(): Promise<void> {
    this.host.println("GW-BASIC TS 0.1");
    this.host.println("Ok");
    while (true) {
      const line = await this.host.inputLine("");
      if (line === null) break;
      try {
        await this.handle(line);
      } catch (e: any) {
        if (e.message === "EXIT") break;   // BYE / SYSTEM — 삼키면 종료가 안 된다
        this.host.println(`?${e.message}`);
      }
      this.host.println("Ok");
    }
  }

  async handle(input: string): Promise<void> {
    const trimmed = input.trim();
    if (trimmed === "") return;

    // 라인 번호로 시작하면 저장
    const m = trimmed.match(/^(\d+)\s*(.*)$/);
    if (m) {
      const lineNum = parseInt(m[1]!, 10);
      this.store.insert(lineNum, m[2]!);
      return;
    }

    // 메타 명령
    const upper = trimmed.toUpperCase();
    if (upper === "RUN") return this.runProgram();
    if (upper === "NEW") { this.store.clear(); return; }
    if (upper.startsWith("LIST")) {
      for (const l of this.store.list()) this.host.println(l);
      return;
    }
    if (upper === "BYE" || upper === "SYSTEM") {
      throw new Error("EXIT");
    }
    if (upper.startsWith("LOAD")) {
      const name = trimmed.slice(4).trim().replace(/^"|"$/g, "");
      await this.load(name);
      return;
    }
    if (upper.startsWith("SAVE")) {
      const name = trimmed.slice(4).trim().replace(/^"|"$/g, "");
      await this.save(name);
      return;
    }

    // 즉시 실행
    await this.runImmediate(trimmed);
  }

  private async runProgram(): Promise<void> {
    const src = this.store.toSource();
    if (src === "") return;
    const tokens = Lexer.tokenize(src + "\n");
    const ast = new Parser(tokens).parseProgram();
    const program = new Compiler().compile(ast);
    const vm = new VM(program, this.host);
    await vm.run();
  }

  private async runImmediate(line: string): Promise<void> {
    const tokens = Lexer.tokenize(line + "\n");
    const ast = new Parser(tokens).parseProgram();
    const program = new Compiler().compile(ast);
    const vm = new VM(program, this.host);
    await vm.run();
  }

  private async load(_name: string): Promise<void> {
    // 브라우저 IndexedDB 또는 Node fs
    // ... CLAUDE.md의 IndexedDB 요구를 따름
  }
  private async save(_name: string): Promise<void> { /* ... */ }
}
```

### 29.4 IndexedDB 저장소 (브라우저)

```ts
// src/repl/idb-store.ts
const DB_NAME = "gwbasic_ts";
const STORE = "programs";

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE, { keyPath: "name" });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function saveProgram(name: string, source: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put({ name, source, savedAt: Date.now() });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function loadProgram(name: string): Promise<string | null> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get(name);
    req.onsuccess = () => resolve(req.result?.source ?? null);
    req.onerror = () => reject(req.error);
  });
}
```

### 29.5 자동 실행과 이어하기

CLAUDE.md 요구사항 *이어하기*는 다음과 같이 구현합니다.

- 프로그램 실행 중 5초마다 (또는 INPUT 시점에) 변수 상태 + PC를 IndexedDB에 저장
- 다음 실행 시 "이어하시겠습니까?" 프롬프트 → 'Y'면 상태 복원 후 재시작

본 책에서는 인터페이스만 보여 줍니다.

```ts
interface SavePoint {
  source: string;
  pc: number;
  stack: BasicValue[];
  callStack: number[];
  forStack: ForRecord[];
  scalars: [string, BasicValue][];
  arrays: [string, ArrayBox][];
  dataPtr: number;
}
```

VM에 `dump(): SavePoint` 와 `restore(sp: SavePoint): void`를 추가합니다.

⚠️ DB 손상 시에도 동작해야 한다는 요구가 있으므로, restore 단계에서 *모든 필드의 존재* 를 검증하고, 실패하면 빈 상태로 시작합니다.

---

## 30장. 디버거 — 단계 실행과 브레이크포인트

### 30.1 디버거의 인터페이스

```ts
interface Debugger {
  setBreakpoint(line: number): void;
  removeBreakpoint(line: number): void;
  step(): Promise<void>;
  continue(): Promise<void>;
  pause(): void;
  state(): { pc: number; line: number | null; stack: BasicValue[]; vars: Map<string, BasicValue> };
}
```

### 30.2 VM의 훅

```ts
// vm.ts에 추가
public onBeforeInstruction: ((pc: number, op: Op) => Promise<void> | void) | null = null;

async run(): Promise<void> {
  while (!this.halted && this.pc < this.program.code.length) {
    if (this.onBeforeInstruction) await this.onBeforeInstruction(this.pc, this.program.code[this.pc]!);
    if (this.halted) return;
    const ins = this.program.code[this.pc++]!;
    if (this.isAsyncOp(ins.op)) await this.dispatch(ins);
    else this.dispatchSync(ins);
  }
}
```

### 30.3 라인 단위 매핑

PC → BASIC 라인 번호의 역매핑이 필요합니다.

```ts
// CompiledProgram에 추가 (옵셔널로 — 필수로 하면 15장의 compile() 반환 객체가
// 이 필드를 만들지 않아 컴파일이 깨진다)
pcToLine?: number[];   // 인덱스 = pc, 값 = BASIC line (없으면 0)
```

컴파일러에서 라인 시작마다 채웁니다.

```ts
private currentLine = 0;
// emitStmt 진입 시 currentLine 업데이트, emit 시 pcToLine[코드 인덱스] = currentLine
```

### 30.4 단계 실행 구현

```ts
class StepDebugger implements Debugger {
  private breaks = new Set<number>();
  private resumeFn: (() => void) | null = null;
  private mode: "run" | "step" = "run";

  attach(vm: VM): void {
    vm.onBeforeInstruction = async (pc) => {
      const line = vm.program.pcToLine?.[pc] ?? 0;
      if (this.mode === "step" || this.breaks.has(line)) {
        await new Promise<void>(r => { this.resumeFn = r; });
      }
    };
  }
  setBreakpoint(line: number): void { this.breaks.add(line); }
  removeBreakpoint(line: number): void { this.breaks.delete(line); }
  step(): Promise<void> { this.mode = "step"; return this.continueOnce(); }
  continue(): Promise<void> { this.mode = "run"; return this.continueOnce(); }
  pause(): void { this.mode = "step"; }
  private continueOnce(): Promise<void> {
    if (this.resumeFn) { this.resumeFn(); this.resumeFn = null; }
    return Promise.resolve();
  }
  state() { /* ... */ }
}
```

### 30.5 디버거 UI 스케치

브라우저에서는 다음과 같은 패널을 보여 줍니다.

```
┌─────────── Source ───────────┐  ┌── Variables ──┐
│ 10 FOR I=1 TO 10            │  │ I = 5         │
│ 20 ▶ PRINT I                │  │ N = 0         │
│ 30 NEXT I                   │  └───────────────┘
│ 40 END                      │
└─────────────────────────────┘  ┌── Stack ──────┐
[Step] [Continue] [Pause]       │ (empty)        │
                                  └───────────────┘
```

본 책 범위 밖이지만, 위 인터페이스만 있으면 React/Vue 등으로 쉽게 만들 수 있습니다.

---

## 31장. 테스트 전략과 회귀 검증

### 31.1 테스트 피라미드

- **단위 테스트**: Lexer, Parser, Compiler, 각 op
- **통합 테스트**: src → run → stdout 비교
- **회귀 테스트**: examples/ 폴더의 전체 예제

### 31.2 통합 테스트 헬퍼

```ts
// tests/helpers.ts
import { Lexer } from "../src/lexer/lexer.js";
import { Parser } from "../src/parser/parser.js";
import { Compiler } from "../src/compiler/compiler.js";
import { VM } from "../src/vm/vm.js";
import type { Host } from "../src/host/host.js";

export function makeMockHost(captureOut: string[], inputs: string[] = []): Host {
  let col = 1, row = 1;
  return {
    printAt(s) { captureOut.push(s); for (const c of s) { if (c === "\n") { row++; col = 1; } else col++; } },
    println(s) { captureOut.push(s + "\n"); row++; col = 1; },
    column: () => col,
    row: () => row,
    inputLine: async () => inputs.shift() ?? "",
    inkey: () => "",
    cls: () => { col = 1; row = 1; },
    setScreen: () => {},
    setColor: () => {},
    locate: (r, c) => { if (r) row = r; if (c) col = c; },
    pset: () => {},
    drawLine: () => {},
    drawCircle: () => {},
    paint: () => {},
    sound: async () => {},
    play: async () => {},
    now: () => Date.now(),
    random: () => 0.5,
    lastRandom: () => 0.5,
    seedRandom: () => {},
  };
}

export async function runSrc(src: string, host: Host): Promise<void> {
  const tokens = Lexer.tokenize(src + "\n");
  const ast = new Parser(tokens).parseProgram();
  const prog = new Compiler().compile(ast);
  const vm = new VM(prog, host);
  await vm.run();
}
```

### 31.3 회귀 테스트 — 예제 폴더

```ts
// tests/examples.test.ts
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { runSrc, makeMockHost } from "./helpers.js";

const dir = "examples";
const cases = readdirSync(dir).filter(f => f.endsWith(".bas"));

describe("Examples", () => {
  for (const f of cases) {
    it(f, async () => {
      const src = readFileSync(`${dir}/${f}`, "utf8");
      const expected = readFileSync(`${dir}/${f.replace(/\.bas$/, ".out")}`, "utf8");
      const out: string[] = [];
      await runSrc(src, makeMockHost(out));
      expect(out.join("")).toBe(expected);
    });
  }
});
```

### 31.4 황금 출력 (Golden output) 갱신 정책

`UPDATE_GOLDEN=1 npm test` 같은 환경변수로 *기대 출력 파일을 새로 쓰는* 모드를 두면 편리합니다.

```ts
if (process.env.UPDATE_GOLDEN) {
  writeFileSync(`${dir}/${f.replace(/\.bas$/, ".out")}`, out.join(""));
}
```

### 31.5 퍼지 (Fuzz) 테스트

랜덤 BASIC 프로그램을 생성해 *크래시 없음*만 확인합니다.

```ts
import { generate } from "./fuzz/generator.js";

describe("Fuzz", () => {
  for (let i = 0; i < 100; i++) {
    it(`random program ${i}`, async () => {
      const src = generate(/*seed=*/i);
      const out: string[] = [];
      try { await runSrc(src, makeMockHost(out)); }
      catch (e: any) {
        // BasicError는 OK, 그 외 (TypeError, RangeError) 만 실패
        expect(e.code).toBeDefined();
      }
    });
  }
});
```

생성기는 BNF를 따라 무작위 트리를 만든 후 직렬화합니다.

### 31.6 성능 벤치

```ts
import { performance } from "node:perf_hooks";

it("성능: 100만 카운터", async () => {
  const t0 = performance.now();
  await runSrc("10 FOR I=1 TO 1000000 : NEXT", makeMockHost([]));
  const dt = performance.now() - t0;
  console.log(`100만 NEXT: ${dt.toFixed(1)}ms`);
  expect(dt).toBeLessThan(2000);   // 2초 이내
});
```

---

## 32장. 빌드, 패키징, 배포

### 32.1 esbuild 설정

```json
{
  "scripts": {
    "build": "esbuild src/main.ts --bundle --outfile=dist/dist.js --format=esm --target=es2022 --minify",
    "build:web": "esbuild src/web.ts --bundle --outfile=public/dist.js --format=iife --target=es2022 --minify",
    "build:all": "npm run build && npm run build:web"
  }
}
```

CLAUDE.md 요구대로 `dist.js` 단일 산출물.

### 32.2 release 폴더 (Linux/Mac)

```bash
#!/usr/bin/env bash
# build.sh
set -e
mkdir -p release
npm run build:web
cp public/dist.js release/dist.js
cp public/index.html release/index.html
[ -d examples ] && cp -r examples release/
[ -d data ]     && cp -r data release/
echo "release/ 폴더가 준비되었습니다."
```

### 32.3 release 폴더 (Windows)

```bat
@echo off
chcp 949 > nul
setlocal
mkdir release 2>nul
call npm run build:web
copy /Y public\dist.js  release\dist.js
copy /Y public\index.html release\index.html
xcopy /E /I /Y examples release\examples
xcopy /E /I /Y data release\data
echo release 폴더가 준비되었습니다.
endlocal
```

⚠️ Windows는 cp949(EUC-KR)로 한글이 깨지지 않게 `chcp 949` 선언.

### 32.4 정적 호스팅

`release/` 폴더를 그대로 정적 서버에 올리면 됩니다.

```bash
cd release && python -m http.server 8001
```

브라우저로 `http://localhost:8001` 접속.

### 32.5 index.html 골격

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>GW-BASIC TS</title>
  <style>
    body { background: #000; color: #ccc; font-family: monospace; margin: 0; }
    canvas { display: block; margin: 0 auto; image-rendering: pixelated; }
  </style>
</head>
<body>
  <canvas id="screen"></canvas>
  <script src="dist.js"></script>
</body>
</html>
```

### 32.6 web.ts 진입점

```ts
// src/web.ts
import { CanvasHost } from "./host/canvas-host.js";
import { Repl } from "./repl/repl.js";

window.addEventListener("DOMContentLoaded", () => {
  const cv = document.getElementById("screen") as HTMLCanvasElement;
  const host = new CanvasHost(cv);
  const repl = new Repl(host);
  repl.run().catch(e => host.println(`Fatal: ${e.message}`));
  cv.focus();
});
```

### 32.7 CI 파이프라인 예 (GitHub Actions)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm test
      - run: npm run build:all
      - uses: actions/upload-artifact@v4
        with: { name: dist, path: release }
```

### 32.8 버전과 변경 이력

CLAUDE.md 요구대로 `history.md`에 한글로 이력을 남깁니다.

```markdown
# 변경 이력

## 0.1.0 (2026-05-02)
- 첫 릴리스
- Lexer, Parser, Compiler, VM 완성
- PRINT/INPUT/IF/FOR/WHILE/GOSUB 지원
- DEF FN, DATA/READ/RESTORE 지원
- SCREEN, LINE, CIRCLE, PSET 지원
- SOUND, PLAY (MML) 지원
- IndexedDB 저장 / 이어하기 미완

## 0.2.0 (예정)
- 이어하기 완성
- PRINT USING 확장
- LBOUND/UBOUND
- ERASE
```

---

> 7부 끝. 가이드북의 본문이 끝났습니다. 다음은 부록입니다.
# 부록

## 부록 A — GW-BASIC BNF 전체

```ebnf
(* === 프로그램 구조 === *)
<program>        ::= { <line> }
<line>           ::= [ <line-number> ] <statement-list> <eol>
<line-number>    ::= /[0-9]{1,5}/
<statement-list> ::= <statement> { ":" <statement> }
<eol>            ::= "\n" | EOF

(* === 문장 === *)
<statement> ::=
    <assign> | <print> | <input> | <line-input>
  | <if> | <for> | <next> | <while> | <wend>
  | <goto> | <gosub> | <return> | <on-goto>
  | <end> | <stop> | <rem>
  | <dim> | <data> | <read> | <restore>
  | <def-fn> | <def-type>
  | <cls> | <screen> | <color> | <locate>
  | <pset> | <preset> | <line-stmt> | <circle> | <paint>
  | <sound> | <play> | <beep>
  | <randomize> | <clear> | <swap> | <erase>
  | <run> | <new> | <list> | <load> | <save> | <system>
  | (* empty *)

<assign>     ::= [ "LET" ] <lvalue> "=" <expression>
<lvalue>     ::= <ident-with-suffix> | <array-ref>
<array-ref>  ::= <ident-with-suffix> "(" <expression> { "," <expression> } ")"

<print>      ::= ( "PRINT" | "?" ) [ <print-list> ]
<print-list> ::= <print-item> { <print-sep> [ <print-item> ] }
<print-item> ::= <expression>
               | "TAB" "(" <expression> ")"
               | "SPC" "(" <expression> ")"
               | "USING" <expression> ";" <expression> { ";" <expression> }
<print-sep>  ::= ";" | ","

<input>      ::= "INPUT" [ ";" ] [ <string-literal> ( ";" | "," ) ] <lvalue> { "," <lvalue> }
<line-input> ::= "LINE" "INPUT" [ ";" ] [ <string-literal> ";" ] <lvalue>

<if>         ::= "IF" <expression> ( "THEN" | "GOTO" ) <then-clause>
                 [ "ELSE" <else-clause> ]
<then-clause>::= <line-number> | <statement-list>
<else-clause>::= <line-number> | <statement-list>

<for>        ::= "FOR" <ident-with-suffix> "=" <expression> "TO" <expression>
                 [ "STEP" <expression> ]
<next>       ::= "NEXT" [ <ident-with-suffix> { "," <ident-with-suffix> } ]
<while>      ::= "WHILE" <expression>
<wend>       ::= "WEND"

<goto>       ::= "GOTO" <line-number>
<gosub>      ::= "GOSUB" <line-number>
<return>     ::= "RETURN" [ <line-number> ]
<on-goto>    ::= "ON" <expression> ( "GOTO" | "GOSUB" ) <line-number> { "," <line-number> }

<end>        ::= "END"
<stop>       ::= "STOP"
<rem>        ::= "REM" /.*/ | "'" /.*/

<dim>        ::= "DIM" <dim-decl> { "," <dim-decl> }
<dim-decl>   ::= <ident-with-suffix> "(" <expression> { "," <expression> } ")"
<data>       ::= "DATA" <data-item> { "," <data-item> }
<data-item>  ::= <number> | <string-literal> | <bare-string>
<read>       ::= "READ" <lvalue> { "," <lvalue> }
<restore>    ::= "RESTORE" [ <line-number> ]

<def-fn>     ::= "DEF" "FN" <ident> [ "(" <ident> { "," <ident> } ")" ] "=" <expression>
<def-type>   ::= ( "DEFINT" | "DEFSNG" | "DEFDBL" | "DEFSTR" )
                 <range> { "," <range> }
<range>      ::= <letter> [ "-" <letter> ]

<cls>        ::= "CLS" [ <expression> ]
<screen>     ::= "SCREEN" <expression> [ "," <expression> [ "," <expression> [ "," <expression> ] ] ]
<color>      ::= "COLOR" [ <expression> ] [ "," <expression> [ "," <expression> ] ]
<locate>     ::= "LOCATE" [ <expression> ] [ "," [ <expression> ] [ "," <expression> ] ]
<pset>       ::= "PSET"   <coord> [ "," <expression> ]
<preset>     ::= "PRESET" <coord> [ "," <expression> ]
<line-stmt>  ::= "LINE" [ <coord> ] "-" <coord>
                 [ "," <expression> ]
                 [ "," ( "B" | "BF" ) ]
                 [ "," <expression> ]            (* style *)
<circle>     ::= "CIRCLE" <coord> "," <expression>
                 [ "," <expression> ]            (* color *)
                 [ "," <expression> "," <expression> ]   (* start, end *)
                 [ "," <expression> ]            (* aspect *)
<paint>      ::= "PAINT" <coord> [ "," <expression> [ "," <expression> [ "," <expression> ] ] ]
<coord>      ::= [ "STEP" ] "(" <expression> "," <expression> ")"

<sound>      ::= "SOUND" <expression> "," <expression>
<play>       ::= "PLAY" <expression>
<beep>       ::= "BEEP"

<randomize>  ::= "RANDOMIZE" [ <expression> ]
<clear>      ::= "CLEAR" [ "," <expression> [ "," <expression> ] ]
<swap>       ::= "SWAP" <lvalue> "," <lvalue>
<erase>      ::= "ERASE" <ident-with-suffix> { "," <ident-with-suffix> }

<run>        ::= "RUN" [ <line-number> | <string-literal> ]
<new>        ::= "NEW"
<list>       ::= "LIST" [ <line-number> ] [ "-" [ <line-number> ] ]
<load>       ::= "LOAD" <expression> [ "," "R" ]
<save>       ::= "SAVE" <expression> [ "," ( "A" | "P" ) ]
<system>     ::= "SYSTEM"

(* === 표현식 (우선순위 낮은 → 높은) === *)
<expression>  ::= <or-expr>
<or-expr>     ::= <xor-expr> { "OR" <xor-expr> }
<xor-expr>    ::= <eqv-expr> { "XOR" <eqv-expr> }
<eqv-expr>    ::= <imp-expr> { "EQV" <imp-expr> }
<imp-expr>    ::= <and-expr> { "IMP" <and-expr> }
<and-expr>    ::= <not-expr> { "AND" <not-expr> }
<not-expr>    ::= [ "NOT" ] <rel-expr>
<rel-expr>    ::= <add-expr> [ <rel-op> <add-expr> ]
<rel-op>      ::= "=" | "<>" | "<" | "<=" | ">" | ">="
<add-expr>    ::= <mod-expr> { ("+" | "-") <mod-expr> }
<mod-expr>    ::= <intdiv-expr> { "MOD" <intdiv-expr> }
<intdiv-expr> ::= <mul-expr> { "\\" <mul-expr> }
<mul-expr>    ::= <unary-expr> { ("*" | "/") <unary-expr> }
<unary-expr>  ::= ( "+" | "-" ) <unary-expr> | <pow-expr>
<pow-expr>    ::= <primary> { "^" <unary-expr> }
<primary>     ::= <number> | <string-literal>
                | <ident-with-suffix>
                | <array-ref>
                | <func-call>
                | "(" <expression> ")"

<func-call>   ::= <builtin-name> "(" [ <expression> { "," <expression> } ] ")"
                | "FN" <ident> "(" [ <expression> { "," <expression> } ] ")"
                | "FN" <ident>

(* === 어휘 단위 === *)
<number>            ::= <int-lit> | <float-lit> | <hex-lit> | <oct-lit>
<int-lit>           ::= /[0-9]+/  [ "%" ]
<float-lit>         ::= /[0-9]+ "." [0-9]* ([ED][+-]?[0-9]+)?/
                      | /\. [0-9]+ ([ED][+-]?[0-9]+)?/
                      | /[0-9]+ [ED] [+-]? [0-9]+/
                      | /[0-9]+ "!"/                     (* SNG 강제 *)
                      | /[0-9]+ "#"/                     (* DBL 강제 *)
<hex-lit>           ::= /& "H" [0-9A-Fa-f]+/
<oct-lit>           ::= /& "O"? [0-7]+/
<string-literal>    ::= /" [^"\n]* "/
<ident>             ::= /[A-Za-z][A-Za-z0-9]{0,39}/
<ident-with-suffix> ::= <ident> [ "%" | "!" | "#" | "$" ]
<letter>            ::= /[A-Za-z]/
<bare-string>       ::= /[^,:\n]+/                       (* DATA 안에서만 *)
```

---

## 부록 B — 명령어 / 함수 레퍼런스 카드

### B.1 제어 흐름

| 명령 | 형식 | 비고 |
|------|------|------|
| GOTO | `GOTO line` | 무조건 분기 |
| GOSUB | `GOSUB line` | 호출 (RETURN으로 복귀) |
| RETURN | `RETURN [line]` | 복귀 (line 지정 시 그곳으로) |
| IF | `IF cond THEN ... [ELSE ...]` | 한 줄 조건문 |
| FOR | `FOR v=a TO b [STEP s]` | 카운터 루프 |
| NEXT | `NEXT [v[, v...]]` | FOR 종료 |
| WHILE | `WHILE cond` | 조건 루프 |
| WEND | `WEND` | WHILE 종료 |
| ON | `ON expr GOTO l1, l2, ...` | 다중 분기 |
| END | `END` | 정상 종료 |
| STOP | `STOP` | 중단 |

### B.2 변수 / 데이터

| 명령 | 형식 |
|------|------|
| LET | `[LET] var = expr` |
| DIM | `DIM v(d1[,d2,...])[, ...]` |
| ERASE | `ERASE v[, v...]` |
| DATA | `DATA item[, item...]` |
| READ | `READ v[, v...]` |
| RESTORE | `RESTORE [line]` |
| DEF | `DEF FN name[(params)] = expr` |
| DEFINT/SNG/DBL/STR | `DEFINT A-Z` |
| SWAP | `SWAP a, b` |
| CLEAR | `CLEAR` |

### B.3 입출력

| 명령 | 형식 |
|------|------|
| PRINT | `PRINT items` |
| PRINT USING | `PRINT USING fmt; args` |
| INPUT | `INPUT ["prompt";] vars` |
| LINE INPUT | `LINE INPUT ["prompt";] var$` |
| LPRINT | `LPRINT items` |

### B.4 그래픽

| 명령 | 형식 |
|------|------|
| SCREEN | `SCREEN mode` |
| CLS | `CLS [mode]` |
| COLOR | `COLOR [fg][, bg]` |
| LOCATE | `LOCATE [r][, c]` |
| PSET | `PSET (x, y) [, c]` |
| PRESET | `PRESET (x, y) [, c]` |
| LINE | `LINE [(x1,y1)]-(x2,y2) [,c [,B|BF]]` |
| CIRCLE | `CIRCLE (x,y), r [,c [,start,end [,asp]]]` |
| PAINT | `PAINT (x,y) [,fill [,border]]` |

### B.5 사운드

| 명령 | 형식 |
|------|------|
| SOUND | `SOUND freq, dur` |
| PLAY | `PLAY mml$` |
| BEEP | `BEEP` |

### B.6 문자열 함수

| 함수 | 반환 | 설명 |
|------|------|------|
| LEN(s$) | INT | 길이 |
| LEFT$(s$, n) | STR | 왼쪽 n자 |
| RIGHT$(s$, n) | STR | 오른쪽 n자 |
| MID$(s$, p[, n]) | STR | p부터 n자 |
| INSTR([start,] s$, t$) | INT | t$의 위치 (없으면 0) |
| CHR$(n) | STR | ASCII n의 문자 |
| ASC(s$) | INT | 첫 글자의 ASCII |
| STR$(n) | STR | 숫자 → 문자열 |
| VAL(s$) | SNG | 문자열 → 숫자 |
| STRING$(n, c) | STR | c를 n번 반복 |
| SPACE$(n) | STR | 공백 n개 |
| HEX$(n) | STR | 16진수 표현 |
| OCT$(n) | STR | 8진수 표현 |

### B.7 수학 함수

| 함수 | 설명 |
|------|------|
| ABS(x) | 절댓값 |
| SGN(x) | 부호 (-1, 0, 1) |
| INT(x) | floor |
| FIX(x) | trunc |
| SQR(x) | √x |
| SIN/COS/TAN(x) | 삼각함수 (라디안) |
| ATN(x) | arctan |
| LOG(x) | ln |
| EXP(x) | e^x |
| RND[(x)] | 난수 |
| CINT/CSNG/CDBL(x) | 타입 변환 |

### B.8 기타

| 함수 / 명령 | 설명 |
|------------|------|
| TIMER | 자정 이후 초 |
| INKEY$ | 비차단 키 입력 |
| POS(0) | 커서 컬럼 |
| CSRLIN | 커서 행 |
| RANDOMIZE [seed] | 난수 시드 |
| RUN [line] | 처음부터 (또는 line부터) 실행 |
| NEW | 프로그램 삭제 |
| LIST [from][-to] | 소스 출력 |
| LOAD/SAVE "name" | 디스크 입출력 |
| SYSTEM | OS로 복귀 |

---

## 부록 C — 에러 코드표

| 번호 | 메시지 | 의미 |
|------|--------|------|
| 1 | NEXT without FOR | NEXT가 짝 잃음 |
| 2 | Syntax error | 일반 문법 오류 |
| 3 | RETURN without GOSUB | 호출 스택 비었음 |
| 4 | Out of DATA | READ 초과 |
| 5 | Illegal function call | 잘못된 인자 |
| 6 | Overflow | 수치 범위 초과 |
| 7 | Out of memory | 메모리 부족 |
| 8 | Undefined line number | 분기 대상 라인 없음 |
| 9 | Subscript out of range | 배열 인덱스 초과 |
| 10 | Duplicate definition | 이미 DIM된 배열 |
| 11 | Division by zero | 0으로 나눔 |
| 12 | Illegal direct | 직접 모드 금지 명령 |
| 13 | Type mismatch | 타입 불일치 |
| 14 | Out of string space | 문자열 공간 부족 |
| 15 | String too long | 문자열 255자 초과 |
| 16 | String formula too complex | 식이 너무 복잡 |
| 17 | Can't continue | CONT 불가 |
| 18 | Undefined user function | DEF FN 안 됨 |
| 19 | No RESUME | ON ERROR 후 RESUME 없음 |
| 20 | RESUME without error | 에러 없이 RESUME |
| 21 | Unprintable error | 알 수 없음 |
| 22 | Missing operand | 피연산자 부족 |
| 23 | Line buffer overflow | 라인 버퍼 초과 |
| 24 | Device timeout | 장치 시간초과 |
| 25 | Device fault | 장치 오류 |
| 26 | FOR without NEXT | FOR 짝 잃음 |
| 27 | Out of paper | 프린터 |
| 29 | WHILE without WEND | |
| 30 | WEND without WHILE | |
| 50 | Field overflow | 파일 |
| 51 | Internal error | |
| 52 | Bad file number | |
| 53 | File not found | |
| 54 | Bad file mode | |
| 55 | File already open | |
| 57 | Device I/O error | |
| 58 | File already exists | |
| 61 | Disk full | |
| 62 | Input past end | |
| 63 | Bad record number | |
| 64 | Bad file name | |
| 66 | Direct statement in file | |
| 67 | Too many files | |
| 68 | Device unavailable | |
| 69 | Communication buffer overflow | |
| 70 | Permission denied | |
| 71 | Disk not ready | |
| 72 | Disk-media error | |
| 73 | Advanced feature | 본 구현에서 미지원 |
| 74 | Rename across disks | |
| 75 | Path/File access error | |
| 76 | Path not found | |

---

## 부록 D — 예제 프로그램 모음 (10선)

### D.1 Hello, World

```basic
10 PRINT "HELLO, WORLD!"
20 END
```

### D.2 99 병의 맥주

```basic
10 FOR N = 99 TO 1 STEP -1
20   PRINT N; "bottles of beer on the wall,"; N; "bottles of beer."
30   PRINT "Take one down, pass it around,"; N-1; "bottles of beer on the wall."
40 NEXT N
50 END
```

### D.3 피보나치

```basic
10 INPUT "How many fibs"; N
20 A = 0 : B = 1
30 FOR I = 1 TO N
40   PRINT A;
50   T = A + B : A = B : B = T
60 NEXT I
70 PRINT
80 END
```

### D.4 소수 (에라토스테네스)

```basic
10 N = 100
20 DIM S(N)
30 FOR I = 2 TO N : S(I) = 1 : NEXT
40 FOR I = 2 TO INT(SQR(N))
50   IF S(I) = 0 THEN GOTO 90
60   FOR J = I*I TO N STEP I
70     S(J) = 0
80   NEXT J
90 NEXT I
100 FOR I = 2 TO N
110  IF S(I) = 1 THEN PRINT I;
120 NEXT I
130 PRINT
140 END
```

### D.5 숫자 맞히기

```basic
10 RANDOMIZE TIMER
20 N = INT(RND * 100) + 1
30 G = 0
40 PRINT "1과 100 사이의 수를 맞춰 봐!"
50 G = G + 1
60 INPUT "추측"; X
70 IF X < N THEN PRINT "더 큰 수" : GOTO 50
80 IF X > N THEN PRINT "더 작은 수" : GOTO 50
90 PRINT "정답!"; G; "회 만에 맞췄음."
100 END
```

### D.6 도형 — 동심원

```basic
10 SCREEN 12 : CLS
20 FOR R = 10 TO 200 STEP 10
30   CIRCLE (320, 240), R, R MOD 16
40 NEXT R
50 LOCATE 28, 30 : PRINT "Press any key"
60 IF INKEY$ = "" THEN GOTO 60
70 END
```

### D.7 나선

```basic
10 SCREEN 12 : CLS : COLOR 14
20 FOR T = 0 TO 1000
30   X = 320 + (T / 5) * COS(T / 10)
40   Y = 240 + (T / 5) * SIN(T / 10)
50   PSET (X, Y), 14
60 NEXT T
70 IF INKEY$ = "" THEN 70
80 END
```

### D.8 작은별 연주

```basic
10 PLAY "T120 O4 L4 CCGG AAG2 FFEE DDC2"
20 PLAY "GGFF EED2 GGFF EED2"
30 PLAY "CCGG AAG2 FFEE DDC2"
40 END
```

### D.9 사용자 함수

```basic
10 DEF FN F2C(F) = (F - 32) * 5 / 9
20 INPUT "화씨 온도"; F
30 PRINT F; "F ="; FN F2C(F); "C"
40 GOTO 20
```

### D.10 행렬 곱

```basic
10 N = 3
20 DIM A(N,N), B(N,N), C(N,N)
30 FOR I=1 TO N : FOR J=1 TO N
40   A(I,J) = I*N + J
50   B(I,J) = (I+J) MOD 5
60 NEXT J : NEXT I
70 FOR I=1 TO N : FOR J=1 TO N
80   C(I,J) = 0
90   FOR K=1 TO N
100    C(I,J) = C(I,J) + A(I,K) * B(K,J)
110  NEXT K
120 NEXT J : NEXT I
130 FOR I=1 TO N
140  FOR J=1 TO N : PRINT C(I,J);
150  NEXT J : PRINT
160 NEXT I
170 END
```

---

## 부록 E — 추가 학습 자료

### 책

- Bob Nystrom, *Crafting Interpreters*. https://craftinginterpreters.com/
- Thorsten Ball, *Writing An Interpreter In Go*.
- Aho/Lam/Sethi/Ullman, *Compilers: Principles, Techniques, and Tools* (드래곤 북).
- Andrew W. Appel, *Modern Compiler Implementation in ML / Java / C*.

### 온라인

- 위키북스 *Compiler Construction* (영문)
- *Pratt Parsers: Expression Parsing Made Easy* — Bob Nystrom 블로그
- *Build Your Own Lisp* — orange book

### GW-BASIC 원본 자료

- *Microsoft GW-BASIC User's Guide and User's Reference* (1987)
- *IBM PC BASIC Reference Manual*
- Microsoft에서 2020년 공개한 GW-BASIC 어셈블리 소스: `https://github.com/microsoft/GW-BASIC`

### 참고할 만한 BASIC 구현

- **Vintage BASIC** (Haskell): https://www.vintage-basic.net/
- **PC-BASIC** (Python): https://github.com/robhagemans/pcbasic
- **MonsterBASIC**, **mBasic**, **bwBASIC**

### 본 책의 코드

본 가이드북의 모든 코드는 다음 디렉터리 구조로 구성됩니다.

```
ts_gwbasic/
├── src/
│   ├── common/types.ts
│   ├── lexer/{lexer,token}.ts
│   ├── parser/{cursor,expr,stmt,parser}.ts
│   ├── ast/{nodes,print}.ts
│   ├── compiler/{compiler,disasm}.ts
│   ├── vm/{opcodes,program,vm}.ts
│   ├── runtime/{value,ops,builtins,env,print-format,print-using,mml}.ts
│   ├── host/{host,console-host,canvas-host,palette,rng}.ts
│   ├── repl/{repl,store,idb-store}.ts
│   ├── main.ts
│   └── web.ts
├── tests/
├── examples/
├── public/index.html
├── data/
├── build.sh
├── build.bat
├── package.json
├── tsconfig.json
├── readme.md
└── history.md
```

각 장에서 보여 준 코드를 그대로 합치면 동작합니다.

---

## 맺음말

여기까지 따라오셨다면, 여러분은 이미 *언어 처리기 작성자* 입니다. 몇 천 줄의 TypeScript 코드로 1980년대 마이크로컴퓨터의 영혼을 다시 살려 냈습니다. 이 경험은 다음과 같이 확장됩니다.

- **DSL 만들기**: 회사 내부 스크립트, 게임 스크립트, 설정 언어
- **다른 레거시 언어 부활**: Logo, 6502 어셈블러, Forth
- **자체 언어 설계**: 작은 함수형 언어, 작은 객체 지향 언어
- **JIT 도전**: 본 VM의 hot loop를 WASM이나 네이티브 코드로 컴파일

언어를 만든다는 것은 *생각의 도구를 만드는 것* 이고, 그 도구는 다시 더 큰 생각을 가능하게 합니다. 즐거운 해킹을 기원합니다.

— 끝.
