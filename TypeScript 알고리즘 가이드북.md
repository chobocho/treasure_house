# TypeScript 알고리즘 가이드북
## 동작하는 코드로 배우는 알고리즘: 정렬·탐색·DP·그래프·문자열·기하까지

### 대상 독자
- TypeScript 문법과 기본 자료구조는 익혔지만, 알고리즘은 체계적으로 배운 적이 없는 개발자
- 코딩 테스트, 사이드 프로젝트, 게임 개발에서 알고리즘을 즉시 가져다 쓰고 싶은 독자
- C/Java 의사코드를 보면 머리가 굳어버리는 사람
- "왜 이 알고리즘이 빠른가"부터 차근차근 이해하고 싶은 독자

### 함께 보면 좋은 책
- [[TypeScript 기초 가이드북]] — 문법 입문
- [[TypeScript 자료구조 가이드북]] — 이 책에서 사용하는 자료구조의 직접 구현

---

# 저자 서문

알고리즘은 "문제를 푸는 절차"입니다. 단순한 정의지만 그 안에는 수십 년에 걸쳐 다듬어진 지혜가 담겨 있습니다.

같은 문제라도 알고리즘에 따라 1초가 걸릴 수도, 10년이 걸릴 수도 있습니다. 검색 엔진, 추천 시스템, 라우팅, 그래픽 엔진, 컴파일러, 게임 AI — 우리가 매일 쓰는 모든 소프트웨어의 핵심에는 잘 선택된 알고리즘이 있습니다.

알고리즘 책은 시중에 많지만 대부분은 한 가지 함정에 빠집니다.

1. **수학적 증명 위주** — 점화식, 마스터 정리, 평균 분석 — 1장만 읽고 책장에 꽂아두게 됩니다.
2. **C/Java 코드** — 우리가 매일 쓰는 환경과 너무 멀어서, "이걸 어떻게 내 프로젝트에 붙이지?"라는 질문이 끝까지 남습니다.
3. **의사코드만 가득** — 책을 다 읽어도 손이 코드를 기억하지 못합니다.

이 책은 다릅니다.

- 모든 알고리즘은 **TypeScript로 처음부터 구현**합니다.
- 모든 코드는 **`tsc`로 컴파일되고, Node나 브라우저에서 그대로 실행**됩니다.
- 모든 코드에는 **시간/공간 복잡도와 한 줄짜리 직관**이 함께 붙어 있습니다.
- 모든 장 끝에는 **연습문제**가 붙어 있고, 정답이 명시적으로 적혀 있지 않은 곳이라도 **이 장의 코드를 그대로 쓰면 풀리도록** 설계되어 있습니다.

이 책을 끝까지 따라오면, 여러분은 50가지가 넘는 알고리즘을 손으로 짜 본 사람이 됩니다. 그리고 무엇보다, 새로운 문제를 만났을 때 "이건 어떤 카테고리의 문제고, 어떤 알고리즘의 변형으로 풀 수 있겠다"는 **분류 감각**을 갖게 됩니다. 그것이 알고리즘 공부의 진짜 보상입니다.

---

# 이 책의 구성

이 책은 총 **20장 + 부록 3편**으로 구성됩니다.

1. 알고리즘과 복잡도 분석
2. 측정과 검증 — 우리가 쓸 도구
3. 기본 정렬 — 버블·선택·삽입
4. 효율적 정렬 — 병합·퀵·힙
5. 비교 없는 정렬 — 계수·기수·버킷
6. 탐색 — 선형·이진·삼분
7. 재귀와 분할정복
8. 백트래킹
9. 동적 계획법(DP) 입문
10. DP 심화 — 패턴별 분류
11. 그리디 알고리즘
12. 그래프 — BFS/DFS와 응용
13. 그래프 최단경로
14. 최소 신장 트리(MST)
15. 문자열 알고리즘
16. 비트마스킹
17. 수학 알고리즘 — 정수론·조합론
18. 기하 알고리즘
19. 보조 자료구조 — 세그먼트 트리·펜윅 트리
20. 종합 실습 — 코딩 테스트 풀이 패턴 모음

각 장은 다음 구조를 따릅니다.

- 학습 목표
- 직관과 핵심 아이디어
- TypeScript 구현 (동작하는 전체 코드)
- 사용 예제 (`console.log`로 결과 확인)
- 시간/공간 복잡도
- 흔한 함정
- 핵심 정리
- 연습문제

---

# 1장. 알고리즘과 복잡도 분석

## 학습 목표
- "알고리즘"의 정의를 자기 말로 설명할 수 있다.
- Big-O / Big-Ω / Big-Θ 표기를 구분한다.
- 시간 복잡도와 공간 복잡도를 모두 분석할 수 있다.

## 1.1 알고리즘이란

알고리즘(Algorithm)은 **유한한 절차로 문제의 입력을 출력으로 바꾸는 방법**입니다. 다음 다섯 가지 조건을 만족해야 합니다.

1. **입력**이 0개 이상 정의되어 있다.
2. **출력**이 1개 이상 정의되어 있다.
3. 각 단계가 **명확**하다(애매하지 않다).
4. 절차가 **유한** 시간에 끝난다.
5. 모든 단계가 **실행 가능**하다.

요리 레시피와 비슷합니다. "맛있게 잘 끓이세요"는 알고리즘이 아니지만, "물 200ml에 라면을 넣고 4분 30초 끓인다"는 알고리즘입니다.

## 1.2 좋은 알고리즘의 기준

같은 결과를 내는 알고리즘이 여러 개라면, 우리는 다음 기준으로 비교합니다.

- **정확성(correctness)** — 모든 입력에 대해 올바른 출력을 내는가?
- **효율성(efficiency)** — 얼마나 빠른가? 메모리는 얼마나 쓰는가?
- **단순성(simplicity)** — 짧고 읽기 쉬운가?
- **일반성(generality)** — 비슷한 문제에 재사용할 수 있는가?

"빠르면 장땡"이 아닙니다. 한 줄로 끝나는 정렬을 50줄짜리 빠른 정렬로 바꿔서 버그를 만들고, 결국 다시 한 줄짜리로 되돌리는 일이 실무에서 흔합니다.

## 1.3 Big-O 다시 보기

Big-O는 **입력 크기 n이 무한히 커질 때 알고리즘의 비용 상한**을 나타냅니다.

```
T(n) = O(g(n))   ⇔   어떤 상수 c, n0이 있어 모든 n ≥ n0에서 T(n) ≤ c·g(n)
```

직관적으로 풀어쓰면:

- O(1): n이 아무리 커져도 같은 시간
- O(log n): n이 두 배가 돼도 1만 더 걸림
- O(n): n이 두 배가 되면 시간도 두 배
- O(n²): n이 두 배가 되면 시간은 네 배

n=10⁶일 때 대략적인 연산 횟수:

| Big-O | 횟수 | 1초 안에 가능? |
|-------|------|----------------|
| O(1) | 1 | 예 |
| O(log n) | 20 | 예 |
| O(n) | 10⁶ | 예 |
| O(n log n) | 2×10⁷ | 예 |
| O(n²) | 10¹² | 아니오 (~20분) |
| O(n³) | 10¹⁸ | 아니오 (~30년) |
| O(2ⁿ) | 천문학적 | 아니오 |

## 1.4 Big-Ω, Big-Θ

- **Big-O**: 상한 (이보다 빨리 끝난다)
- **Big-Ω**: 하한 (이보다 빨리 끝나지는 않는다)
- **Big-Θ**: 정확한 추정 (양쪽 모두)

실무에서는 거의 항상 Big-O만 씁니다. "최악의 경우 얼마나 느린가"가 가장 궁금하기 때문입니다.

## 1.5 공간 복잡도

시간만 비싼 게 아닙니다. 메모리도 자원입니다.

```ts
// 공간 O(1) — 입력 배열 외에 상수 개 변수만 사용
function sumInPlace(arr: number[]): number {
  let total = 0;
  for (const x of arr) total += x;
  return total;
}

// 공간 O(n) — 새 배열을 만듦
function doubled(arr: number[]): number[] {
  return arr.map(x => x * 2);
}

// 공간 O(n) — 재귀 콜 스택이 n 깊이
function sumRecursive(arr: number[], i = 0): number {
  if (i === arr.length) return 0;
  return arr[i] + sumRecursive(arr, i + 1);
}
```

## 1.6 평균/최선/최악

같은 알고리즘이라도 입력에 따라 비용이 달라집니다.

| 알고리즘 | 최선 | 평균 | 최악 |
|---------|------|------|------|
| 선형 탐색 | O(1) | O(n) | O(n) |
| 이진 탐색 | O(1) | O(log n) | O(log n) |
| 퀵 정렬 | O(n log n) | O(n log n) | O(n²) |
| 삽입 정렬 | O(n) | O(n²) | O(n²) |

"평균 O(n log n)"인 퀵 정렬이 "최악 O(n log n)"인 병합 정렬보다 실무에서 더 자주 쓰이는 이유는, 평균 케이스가 압도적으로 더 자주 나타나며 상수항이 작기 때문입니다.

## 1.7 amortized — 분할 상환 분석

가끔 비싼 연산이 섞여 있어도, 여러 번에 걸쳐 평균을 내면 싸게 보일 수 있습니다.

대표 예: 동적 배열의 `push`. 가끔(크기가 두 배 될 때) O(n)이 들지만, n번 push할 때 총비용이 O(n)이라 한 번당 amortized O(1)입니다.

이걸 분석하는 정식 기법은 **회계 분석법(accounting method)**, **포텐셜 함수법(potential method)** 등이 있지만, 이 책에서는 직관적으로 "n번 연산 총비용 ÷ n"으로 갈음하겠습니다.

## 핵심 정리
- 알고리즘은 **유한한 절차**다. 각 단계가 명확해야 한다.
- Big-O는 **입력이 커질 때의 증가 추세**를 본다. 작은 n에서는 상수가 더 중요할 수 있다.
- 시간 복잡도뿐 아니라 **공간 복잡도**도 챙겨라.

## 연습문제
1. O(n)과 O(n²)이 n=10에서는 차이가 얼마나 되는가? n=10⁶에서는?
2. `Array.prototype.includes`는 O(n)이다. n=10⁸이면 1초 안에 끝나는가?

---

# 2장. 측정과 검증 — 우리가 쓸 도구

## 학습 목표
- 알고리즘의 실제 실행 시간을 정확히 측정하는 함수를 만든다.
- 무작위 입력 생성기로 알고리즘 정확성을 검증한다.
- 두 알고리즘을 공정하게 비교하는 벤치마크 패턴을 익힌다.

## 2.1 왜 직접 측정해야 하는가

복잡도 분석은 강력하지만, 다음 경우에는 거짓말을 합니다.

- n이 작을 때 (상수가 더 큰 영향)
- 캐시 효과 (메모리 지역성)
- 입력 분포 (이미 정렬된 입력 vs 무작위)
- 언어/엔진 특성 (V8의 JIT 최적화)

그래서 실무에서는 **이론으로 후보를 좁힌 뒤 측정으로 결정**합니다.

## 2.2 측정 유틸리티

이 책 전체에서 쓸 도구입니다.

```ts
// src/util/measure.ts
export function measure<T>(label: string, fn: () => T): T {
  const start = performance.now();
  const result = fn();
  const elapsed = performance.now() - start;
  console.log(`[${label}] ${elapsed.toFixed(3)} ms`);
  return result;
}

/** N번 반복해 평균 시간 측정 — 한 번 측정의 노이즈 제거 */
export function bench(label: string, fn: () => void, runs = 5): void {
  // JIT warmup
  fn();
  const times: number[] = [];
  for (let i = 0; i < runs; i++) {
    const start = performance.now();
    fn();
    times.push(performance.now() - start);
  }
  const avg = times.reduce((a, b) => a + b, 0) / runs;
  const min = Math.min(...times);
  console.log(`[${label}] avg ${avg.toFixed(3)} ms, min ${min.toFixed(3)} ms`);
}
```

JIT 워밍업은 V8/SpiderMonkey가 첫 호출 후 코드를 최적화하기 때문에 필요합니다. 첫 번째 측정만 보면 항상 가장 느린 결과를 얻게 됩니다.

## 2.3 무작위 입력 생성기

```ts
// src/util/random.ts
/** seed로 재현 가능한 PRNG (mulberry32) */
export function makeRng(seed = 42): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function randomArray(n: number, min = 0, max = 1000, seed = 42): number[] {
  const rng = makeRng(seed);
  const arr = new Array<number>(n);
  for (let i = 0; i < n; i++) arr[i] = min + Math.floor(rng() * (max - min));
  return arr;
}

export function shuffled(arr: number[], seed = 42): number[] {
  const rng = makeRng(seed);
  const copy = arr.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}
```

`Math.random`을 쓰지 않는 이유는 **재현 가능성** 때문입니다. 버그를 잡을 때 같은 입력을 다시 만들 수 있어야 합니다.

## 2.4 검증 헬퍼

```ts
// src/util/verify.ts
export function assertEqual<T>(actual: T, expected: T, label = "assertEqual"): void {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) {
    throw new Error(`[${label}] expected ${e}, got ${a}`);
  }
}

export function isSorted(arr: number[], asc = true): boolean {
  for (let i = 1; i < arr.length; i++) {
    if (asc ? arr[i] < arr[i - 1] : arr[i] > arr[i - 1]) return false;
  }
  return true;
}

/** 두 배열이 원소 다중집합으로 같은가 */
export function sameMultiset(a: number[], b: number[]): boolean {
  if (a.length !== b.length) return false;
  const sa = a.slice().sort((x, y) => x - y);
  const sb = b.slice().sort((x, y) => x - y);
  return sa.every((v, i) => v === sb[i]);
}
```

## 2.5 정렬 검증 예시

```ts
import { randomArray } from "./util/random";
import { isSorted, sameMultiset } from "./util/verify";

function mySort(arr: number[]): number[] {
  return arr.slice().sort((a, b) => a - b);
}

const input = randomArray(1000);
const sorted = mySort(input);

console.log("정렬됨?", isSorted(sorted));
console.log("같은 다중집합?", sameMultiset(input, sorted));
```

이 책의 모든 정렬 알고리즘은 위 두 검증을 통과합니다.

## 핵심 정리
- 이론 분석은 후보 선정, 실측은 최종 결정.
- **워밍업 → 반복 측정 → 평균/최소** 가 신뢰할 수 있는 측정 패턴.
- 재현 가능한 시드 PRNG를 써라.

## 연습문제
1. 위 `bench` 함수에 표준편차 출력을 추가하라.
2. `randomArray`로 100만 개 정수를 만들어 `Array.prototype.sort` 시간을 재 보라.

---

# 3장. 기본 정렬 — 버블·선택·삽입

## 학습 목표
- O(n²) 정렬 세 가지의 동작 원리를 안다.
- 안정 정렬(stable sort)과 in-place 개념을 안다.
- 작은 n에서 삽입 정렬이 왜 자주 쓰이는지 이해한다.

## 3.1 정렬이란

배열의 원소를 **비교 함수가 정한 순서대로** 재배열하는 것. 정렬 자체보다 정렬 후 가능해지는 일들 — 이진 탐색, 중복 제거, 그룹화 — 이 더 중요합니다.

## 3.2 버블 정렬

인접한 두 원소를 비교해 잘못된 순서면 교환. n-1번 반복하면 정렬됩니다.

```ts
// src/sort/bubble.ts
export function bubbleSort(arr: number[]): number[] {
  const a = arr.slice();
  for (let i = 0; i < a.length - 1; i++) {
    let swapped = false;
    for (let j = 0; j < a.length - 1 - i; j++) {
      if (a[j] > a[j + 1]) {
        [a[j], a[j + 1]] = [a[j + 1], a[j]];
        swapped = true;
      }
    }
    if (!swapped) break; // 이미 정렬됨 → early exit
  }
  return a;
}
```

```ts
console.log(bubbleSort([5, 2, 8, 1, 9, 3])); // [1, 2, 3, 5, 8, 9]
```

복잡도: 시간 O(n²), 공간 O(1). 안정.

## 3.3 선택 정렬

매 단계에서 남은 부분의 최솟값을 찾아 맨 앞으로 옮김.

```ts
// src/sort/selection.ts
export function selectionSort(arr: number[]): number[] {
  const a = arr.slice();
  for (let i = 0; i < a.length - 1; i++) {
    let minIdx = i;
    for (let j = i + 1; j < a.length; j++) {
      if (a[j] < a[minIdx]) minIdx = j;
    }
    if (minIdx !== i) [a[i], a[minIdx]] = [a[minIdx], a[i]];
  }
  return a;
}
```

복잡도: 시간 O(n²) (입력에 무관). 공간 O(1). **불안정**.

장점: 교환 횟수가 최대 n-1번뿐입니다. 디스크 같은 비싼 쓰기 매체에서 의미가 있습니다.

## 3.4 삽입 정렬

이미 정렬된 부분에 새 원소를 한 칸씩 거꾸로 밀어 넣음. 카드 게임에서 카드를 정리하는 방식과 같습니다.

```ts
// src/sort/insertion.ts
export function insertionSort(arr: number[]): number[] {
  const a = arr.slice();
  for (let i = 1; i < a.length; i++) {
    const key = a[i];
    let j = i - 1;
    while (j >= 0 && a[j] > key) {
      a[j + 1] = a[j];
      j--;
    }
    a[j + 1] = key;
  }
  return a;
}
```

```ts
console.log(insertionSort([5, 2, 8, 1, 9, 3])); // [1, 2, 3, 5, 8, 9]
console.log(insertionSort([1, 2, 3, 4, 5]));    // O(n) — 이미 정렬됨
```

복잡도: 최선 O(n) (이미 정렬), 최악 O(n²). 공간 O(1). 안정.

## 3.5 왜 작은 n에선 삽입 정렬?

V8의 `Array.prototype.sort`는 내부적으로 **TimSort**를 쓰는데, 그 안에서 일정 크기(보통 n ≤ 32) 미만 부분 배열은 **삽입 정렬**로 처리합니다. 이유:

- 상수항이 매우 작음 (간단한 루프 + 비교)
- 캐시 친화적 (데이터 한 줄에 다 들어옴)
- 거의 정렬된 입력에 매우 빠름

이론적 복잡도가 작은 n에서는 거짓말을 한다는 살아있는 증거입니다.

## 3.6 셸 정렬 (보너스)

삽입 정렬의 일반화. "거리 g 떨어진 원소들끼리 먼저 정렬"을 거리를 줄여가며 반복.

```ts
// src/sort/shell.ts
export function shellSort(arr: number[]): number[] {
  const a = arr.slice();
  for (let gap = a.length >> 1; gap > 0; gap >>= 1) {
    for (let i = gap; i < a.length; i++) {
      const tmp = a[i];
      let j = i;
      while (j >= gap && a[j - gap] > tmp) {
        a[j] = a[j - gap];
        j -= gap;
      }
      a[j] = tmp;
    }
  }
  return a;
}
```

복잡도는 갭 시퀀스에 따라 달라집니다. 위처럼 절반씩 줄이는 갭은 최악 O(n²)이고, Hibbard 갭(1, 3, 7, 15, …)은 O(n^1.5), 더 정교한 갭은 O(n log² n)까지 내려갑니다.

## 시간복잡도 정리

| 알고리즘 | 최선 | 평균 | 최악 | 공간 | 안정 |
|---------|------|------|------|------|------|
| 버블 | O(n) | O(n²) | O(n²) | O(1) | ✓ |
| 선택 | O(n²) | O(n²) | O(n²) | O(1) | ✗ |
| 삽입 | O(n) | O(n²) | O(n²) | O(1) | ✓ |
| 셸 | O(n log n) | ~ | O(n²) (절반 갭) | O(1) | ✗ |

## 핵심 정리
- O(n²) 정렬 셋은 **n ≤ 수백** 또는 거의 정렬된 입력에서 빛난다.
- **거의 정렬됨**이 입력 특성이라면 삽입 정렬이 효율적 정렬보다 빠를 수 있다.
- 안정성이 필요하면 버블/삽입을, 교환을 줄이려면 선택을.

## 연습문제
1. 삽입 정렬에서 "이미 정렬된 부분"을 이진 탐색으로 위치를 찾도록 바꿔라(이진 삽입 정렬).
2. 측정으로 n=20에서 삽입 정렬과 `Array.prototype.sort`를 비교하라.

---

# 4장. 효율적 정렬 — 병합·퀵·힙

## 학습 목표
- 분할정복(divide and conquer) 원리를 이해한다.
- 병합/퀵/힙 정렬을 직접 구현한다.
- 각 알고리즘의 함정을 알고 피한다.

## 4.1 병합 정렬

배열을 절반으로 쪼개고, 각 절반을 정렬한 뒤, 두 정렬된 배열을 합칩니다.

```ts
// src/sort/merge.ts
export function mergeSort(arr: number[]): number[] {
  if (arr.length <= 1) return arr.slice();
  const mid = arr.length >> 1;
  const left = mergeSort(arr.slice(0, mid));
  const right = mergeSort(arr.slice(mid));
  return merge(left, right);
}

function merge(left: number[], right: number[]): number[] {
  const result = new Array<number>(left.length + right.length);
  let i = 0, j = 0, k = 0;
  while (i < left.length && j < right.length) {
    if (left[i] <= right[j]) result[k++] = left[i++];
    else result[k++] = right[j++];
  }
  while (i < left.length) result[k++] = left[i++];
  while (j < right.length) result[k++] = right[j++];
  return result;
}
```

```ts
console.log(mergeSort([5, 2, 8, 1, 9, 3, 7, 4]));
// [1, 2, 3, 4, 5, 7, 8, 9]
```

복잡도: **항상 O(n log n)**. 공간 O(n). **안정**.

장점: 최악 보장. 단점: 추가 메모리.

## 4.2 퀵 정렬

피벗(pivot)을 하나 골라, 피벗보다 작은 것은 왼쪽, 큰 것은 오른쪽으로 나눕니다. 양쪽을 재귀적으로 정렬.

```ts
// src/sort/quick.ts
export function quickSort(arr: number[]): number[] {
  const a = arr.slice();
  qs(a, 0, a.length - 1);
  return a;
}

function qs(a: number[], lo: number, hi: number): void {
  if (lo >= hi) return;
  const p = partition(a, lo, hi);
  qs(a, lo, p - 1);
  qs(a, p + 1, hi);
}

/** Lomuto partition */
function partition(a: number[], lo: number, hi: number): number {
  // 피벗으로 가운데 값을 끝으로 보냄 (이미 정렬된 입력 대비)
  const mid = (lo + hi) >> 1;
  [a[mid], a[hi]] = [a[hi], a[mid]];
  const pivot = a[hi];
  let i = lo;
  for (let j = lo; j < hi; j++) {
    if (a[j] < pivot) {
      [a[i], a[j]] = [a[j], a[i]];
      i++;
    }
  }
  [a[i], a[hi]] = [a[hi], a[i]];
  return i;
}
```

복잡도: 평균 O(n log n), 최악 O(n²). 공간 O(log n) (재귀 스택). **불안정**.

### 함정과 해결
- **이미 정렬된 입력 + 피벗을 끝으로 고정** → O(n²). 위처럼 **중앙값 또는 무작위 피벗**을 써라.
- **중복이 많은 입력** → 3-way 파티션이 빠르다.

### 3-way 퀵 정렬 (중복에 강함)

```ts
// src/sort/quick3.ts
export function quickSort3(arr: number[]): number[] {
  const a = arr.slice();
  qs3(a, 0, a.length - 1);
  return a;
}

function qs3(a: number[], lo: number, hi: number): void {
  if (lo >= hi) return;
  const pivot = a[(lo + hi) >> 1];
  let lt = lo, gt = hi, i = lo;
  while (i <= gt) {
    if (a[i] < pivot) { [a[lt], a[i]] = [a[i], a[lt]]; lt++; i++; }
    else if (a[i] > pivot) { [a[i], a[gt]] = [a[gt], a[i]]; gt--; }
    else i++;
  }
  qs3(a, lo, lt - 1);
  qs3(a, gt + 1, hi);
}

console.log(quickSort3([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9]));
```

## 4.3 힙 정렬

[[TypeScript 자료구조 가이드북]] 11장의 힙을 그대로 활용합니다. 모든 원소를 힙에 넣고 하나씩 꺼내면 정렬된 순서가 나옵니다.

```ts
// src/sort/heap.ts
/** in-place 힙 정렬 — 추가 메모리 O(1) */
export function heapSort(arr: number[]): number[] {
  const a = arr.slice();
  const n = a.length;
  // 최대 힙 빌드
  for (let i = (n >> 1) - 1; i >= 0; i--) siftDown(a, i, n);
  // 끝에 최댓값을 보내고 힙 크기 줄이기
  for (let end = n - 1; end > 0; end--) {
    [a[0], a[end]] = [a[end], a[0]];
    siftDown(a, 0, end);
  }
  return a;
}

function siftDown(a: number[], i: number, n: number): void {
  while (true) {
    const l = 2 * i + 1, r = 2 * i + 2;
    let largest = i;
    if (l < n && a[l] > a[largest]) largest = l;
    if (r < n && a[r] > a[largest]) largest = r;
    if (largest === i) return;
    [a[i], a[largest]] = [a[largest], a[i]];
    i = largest;
  }
}
```

복잡도: **항상 O(n log n)**. 공간 O(1). **불안정**.

장점: 최악 보장 + 추가 메모리 없음. 단점: 캐시 친화적이지 않아 실측 속도는 퀵 정렬보다 보통 느림.

## 4.4 비교 — 언제 무엇을?

| 알고리즘 | 평균 | 최악 | 공간 | 안정 | 캐시 친화 |
|---------|------|------|------|------|-----------|
| 병합 | O(n log n) | O(n log n) | O(n) | ✓ | ✓ |
| 퀵 | O(n log n) | O(n²) | O(log n) | ✗ | ✓ |
| 힙 | O(n log n) | O(n log n) | O(1) | ✗ | ✗ |

실무 선택:
- 일반적: **퀵 정렬** (보통 가장 빠름)
- 안정성 필요: **병합 정렬** 또는 TimSort
- 메모리 빠듯: **힙 정렬**

V8의 `Array.prototype.sort`는 TimSort. 작은 부분은 삽입, 큰 부분은 병합.

## 4.5 안정성이 왜 중요한가

다중 키 정렬에서 결정적입니다. 학생을 "성적 → 이름" 순으로 정렬하고 싶으면:

1. 이름으로 먼저 정렬
2. 성적으로 다시 정렬 (안정 정렬이어야 같은 성적 안에서 이름 순서가 보존됨)

```ts
type Student = { name: string; score: number };
const students: Student[] = [
  { name: "Lee", score: 90 },
  { name: "Kim", score: 85 },
  { name: "Park", score: 90 },
];

const sorted = students
  .slice()
  .sort((a, b) => a.name.localeCompare(b.name)) // 이름 순
  .sort((a, b) => b.score - a.score);            // 성적 내림차순 (안정)

console.log(sorted);
// [{Lee,90},{Park,90},{Kim,85}]
```

## 핵심 정리
- 분할정복으로 O(n log n)을 달성할 수 있다.
- 퀵은 평균 빠르지만 최악이 위험. 피벗을 잘 골라라.
- 힙은 보장된 O(n log n) + O(1) 메모리.

## 연습문제
1. 병합 정렬을 in-place로 만들 수 있는가? (힌트: 매우 어렵다. 시도만 해보고 왜 어려운지 정리)
2. 퀵 정렬에 "n ≤ 16이면 삽입 정렬로 전환"을 추가해 측정해 보라.

---

# 5장. 비교 없는 정렬 — 계수·기수·버킷

## 학습 목표
- 비교 정렬의 하한 Ω(n log n)을 이해한다.
- 정수에 특화된 O(n) 정렬을 구현한다.

## 5.1 비교 정렬의 하한

n개의 원소를 비교만으로 정렬하려면 **최소 Ω(n log n)번의 비교**가 필요하다는 것이 증명되어 있습니다.

직관: 가능한 순열은 n!개. 한 번 비교로 절반을 줄이면 log₂(n!) ≈ n log n번 비교가 필요.

비교를 안 하면? 더 빠를 수도 있습니다. 단, 입력에 제약이 필요합니다.

## 5.2 계수 정렬 (Counting Sort)

값의 범위가 작은 정수에 대해 O(n + k) — k는 범위.

```ts
// src/sort/counting.ts
export function countingSort(arr: number[]): number[] {
  if (arr.length === 0) return [];
  let min = arr[0], max = arr[0];
  for (const x of arr) {
    if (x < min) min = x;
    if (x > max) max = x;
  }
  const k = max - min + 1;
  const count = new Array<number>(k).fill(0);
  for (const x of arr) count[x - min]++;

  // 누적합 → 안정 정렬을 위해
  for (let i = 1; i < k; i++) count[i] += count[i - 1];

  const result = new Array<number>(arr.length);
  for (let i = arr.length - 1; i >= 0; i--) {
    const idx = --count[arr[i] - min];
    result[idx] = arr[i];
  }
  return result;
}
```

```ts
console.log(countingSort([4, 2, 2, 8, 3, 3, 1])); // [1, 2, 2, 3, 3, 4, 8]
```

복잡도: O(n + k). k가 너무 크면(예: 0~10⁹) 비효율. 범위가 좁은 정수일 때만.

## 5.3 기수 정렬 (Radix Sort)

자릿수 별로 안정 정렬을 반복. LSD(Least Significant Digit)부터.

```ts
// src/sort/radix.ts
export function radixSort(arr: number[]): number[] {
  if (arr.length === 0) return [];
  // 음수 처리: 최솟값으로 평행이동
  const min = Math.min(...arr);
  let a = arr.map(x => x - min);
  const max = Math.max(...a);
  for (let exp = 1; Math.floor(max / exp) > 0; exp *= 10) {
    a = countingByDigit(a, exp);
  }
  return a.map(x => x + min);
}

function countingByDigit(arr: number[], exp: number): number[] {
  const count = new Array<number>(10).fill(0);
  for (const x of arr) count[Math.floor(x / exp) % 10]++;
  for (let i = 1; i < 10; i++) count[i] += count[i - 1];
  const result = new Array<number>(arr.length);
  for (let i = arr.length - 1; i >= 0; i--) {
    const d = Math.floor(arr[i] / exp) % 10;
    result[--count[d]] = arr[i];
  }
  return result;
}

console.log(radixSort([170, 45, 75, 90, 802, 24, 2, 66]));
// [2, 24, 45, 66, 75, 90, 170, 802]
```

복잡도: O(d × (n + b)) — d는 자릿수, b는 진수.

## 5.4 버킷 정렬 (Bucket Sort)

값이 [0, 1) 같은 균등 분포 실수에 잘 맞습니다.

```ts
// src/sort/bucket.ts
import { insertionSort } from "./insertion";

/** values in [0, 1) */
export function bucketSort(arr: number[], bucketCount = 10): number[] {
  if (arr.length === 0) return [];
  const buckets: number[][] = Array.from({ length: bucketCount }, () => []);
  for (const x of arr) {
    const idx = Math.min(Math.floor(x * bucketCount), bucketCount - 1);
    buckets[idx].push(x);
  }
  const result: number[] = [];
  for (const b of buckets) {
    const sorted = insertionSort(b);
    for (const v of sorted) result.push(v);
  }
  return result;
}

console.log(bucketSort([0.42, 0.32, 0.23, 0.52, 0.25, 0.47, 0.51]));
```

복잡도: 평균 O(n + n²/k + k) = O(n) (k ≈ n).

## 핵심 정리
- 입력에 제약이 있으면 비교 정렬보다 빠른 O(n) 정렬이 가능하다.
- 계수: 범위가 좁은 정수.
- 기수: 큰 정수 (자릿수 기반).
- 버킷: 균등 분포 실수.

## 연습문제
1. 문자열 길이가 모두 같은 입력을 기수 정렬로 정렬하는 코드를 만들어라.
2. 계수 정렬로 음수가 포함된 입력도 처리하라(이미 위 코드는 가능 — min을 빼는 트릭).

---

# 6장. 탐색 — 선형·이진·삼분

## 학습 목표
- 선형/이진/삼분 탐색의 동작과 적용 조건을 안다.
- 이진 탐색의 두 가지 변형(lower_bound / upper_bound)을 익힌다.
- 삼분 탐색이 어떤 함수에 적용 가능한지 이해한다.

## 6.1 선형 탐색

처음부터 끝까지 보기. 정렬되지 않은 배열에선 이게 최선.

```ts
// src/search/linear.ts
export function linearSearch<T>(arr: T[], target: T): number {
  for (let i = 0; i < arr.length; i++) {
    if (arr[i] === target) return i;
  }
  return -1;
}
```

복잡도: O(n). 메모리 O(1).

## 6.2 이진 탐색

**정렬된** 배열에서 매번 절반을 버립니다.

```ts
// src/search/binary.ts
export function binarySearch(arr: number[], target: number): number {
  let lo = 0, hi = arr.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] === target) return mid;
    if (arr[mid] < target) lo = mid + 1;
    else hi = mid - 1;
  }
  return -1;
}
```

```ts
const a = [1, 3, 5, 7, 9, 11, 13];
console.log(binarySearch(a, 7));  // 3
console.log(binarySearch(a, 4));  // -1
```

복잡도: O(log n).

### 함정 — 오버플로
다른 언어에선 `lo + hi`가 정수 오버플로를 일으킬 수 있어 `lo + ((hi - lo) >> 1)`을 씁니다. JavaScript는 수 범위가 넓어 덧셈 자체는 안전하지만, `>>`가 피연산자를 32비트 정수로 잘라 계산하므로 길이가 2³⁰을 넘는 배열이라면 `Math.floor((lo + hi) / 2)`를 써야 합니다.

## 6.3 lower_bound / upper_bound

C++ STL의 두 함수. **target 이상이 처음 나오는 위치 / target 초과가 처음 나오는 위치**.

```ts
// src/search/bound.ts
/** target 이상이 처음 등장하는 인덱스 */
export function lowerBound(arr: number[], target: number): number {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] < target) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

/** target 초과가 처음 등장하는 인덱스 */
export function upperBound(arr: number[], target: number): number {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] <= target) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

const a = [1, 2, 2, 2, 3, 4, 5];
console.log(lowerBound(a, 2)); // 1
console.log(upperBound(a, 2)); // 4
console.log(upperBound(a, 2) - lowerBound(a, 2)); // 3 (2의 개수)
```

활용: 정렬된 배열에서 **특정 값의 개수**, **삽입 위치**, **범위 내 원소 수**.

## 6.4 답을 이진 탐색

문제의 정답이 단조성을 가지면, 답 자체를 이진 탐색할 수 있습니다.

**문제**: 매일 일정한 양 K씩 책을 읽을 수 있다. n일 안에 모든 페이지를 읽으려면 K는 최소 얼마여야 하는가?

```ts
// src/search/answerBinary.ts
export function minDailyPages(pages: number[], days: number): number {
  let lo = 1, hi = pages.reduce((a, b) => a + b, 0);
  while (lo < hi) {
    const k = (lo + hi) >> 1;
    if (canFinish(pages, days, k)) hi = k;
    else lo = k + 1;
  }
  return lo;
}

function canFinish(pages: number[], days: number, k: number): boolean {
  let used = 1, remain = k;
  for (const p of pages) {
    if (p > k) return false;
    if (p > remain) { used++; remain = k; }
    remain -= p;
  }
  return used <= days;
}

console.log(minDailyPages([7, 2, 5, 10, 8], 2)); // 18
```

핵심: `canFinish(k)`가 단조 — k가 커지면 더 잘 끝남 → 이진 탐색.

## 6.5 삼분 탐색

볼록(convex) 또는 오목(concave) 함수의 극값 찾기.

```ts
// src/search/ternary.ts
/** [lo, hi]에서 단봉 함수 f의 최댓값 위치 — 정수 도메인 */
export function ternarySearchMax(
  f: (x: number) => number,
  lo: number,
  hi: number,
): number {
  while (hi - lo > 2) {
    const m1 = lo + Math.floor((hi - lo) / 3);
    const m2 = hi - Math.floor((hi - lo) / 3);
    if (f(m1) < f(m2)) lo = m1 + 1;
    else hi = m2 - 1;
  }
  let best = lo;
  for (let i = lo + 1; i <= hi; i++) if (f(i) > f(best)) best = i;
  return best;
}

// 예: f(x) = -(x-7)^2 + 50의 최댓값
const f = (x: number) => -((x - 7) ** 2) + 50;
console.log(ternarySearchMax(f, 0, 20)); // 7
```

복잡도: O(log n).

## 핵심 정리
- 정렬되어 있으면 이진 탐색.
- "이 답이 가능한가?"가 단조면 답을 이진 탐색.
- 단봉 함수의 극값은 삼분 탐색.

## 연습문제
1. 회전된 정렬 배열(예: [4,5,6,7,0,1,2])에서 이진 탐색으로 값을 찾아라.
2. 두 정렬 배열의 중앙값을 O(log(min(m,n)))에 구하라.

---

# 7장. 재귀와 분할정복

## 학습 목표
- 재귀의 정의와 베이스 케이스의 중요성을 안다.
- 분할정복 패턴을 식별하고 적용한다.
- 재귀를 반복문으로 옮길 줄 안다.

## 7.1 재귀의 두 조건

1. **베이스 케이스(base case)** — 더 이상 재귀하지 않는 종료 조건
2. **재귀 케이스(recursive case)** — 자신을 더 작은 입력으로 호출

베이스 케이스를 빠뜨리면 무한 루프 → 스택 오버플로.

## 7.2 고전 예 — 팩토리얼, 피보나치

```ts
// src/recursion/factorial.ts
export function factorial(n: number): number {
  if (n <= 1) return 1;            // 베이스
  return n * factorial(n - 1);     // 재귀
}

export function fib(n: number): number {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}
```

`fib(40)`은 동작하지만 `fib(50)`은 매우 느립니다. 같은 부분 문제를 지수적으로 반복하기 때문. **메모이제이션**으로 O(n)으로 줄일 수 있는데, 이건 9장에서 다룹니다.

## 7.3 분할정복 패턴

```
1. 문제를 작은 부분 문제로 나눈다.
2. 각 부분 문제를 재귀적으로 푼다.
3. 부분 해를 합친다.
```

병합 정렬, 퀵 정렬, 이진 탐색 모두 이 패턴.

## 7.4 거듭제곱 — O(log n)

```ts
// src/recursion/power.ts
export function power(base: number, exp: number): number {
  if (exp === 0) return 1;
  if (exp % 2 === 0) {
    const half = power(base, exp / 2);
    return half * half;
  }
  return base * power(base, exp - 1);
}

console.log(power(2, 10)); // 1024
console.log(power(3, 20)); // 3486784401
```

같은 결과를 `base ** exp`로도 얻을 수 있지만, **모듈러 거듭제곱**(17장)에선 이 분할정복이 필수입니다.

## 7.5 최대공약수 — 유클리드

```ts
// src/recursion/gcd.ts
export function gcd(a: number, b: number): number {
  return b === 0 ? a : gcd(b, a % b);
}

console.log(gcd(48, 18)); // 6
```

복잡도: O(log min(a, b)).

## 7.6 하노이 탑

```ts
// src/recursion/hanoi.ts
export function hanoi(n: number, from = "A", to = "C", via = "B"): string[] {
  if (n === 0) return [];
  const moves: string[] = [];
  moves.push(...hanoi(n - 1, from, via, to));
  moves.push(`${from} → ${to}`);
  moves.push(...hanoi(n - 1, via, to, from));
  return moves;
}

console.log(hanoi(3));
// ['A → C', 'A → B', 'C → B', 'A → C', 'B → A', 'B → C', 'A → C']
```

이동 횟수 = 2ⁿ − 1.

## 7.7 재귀를 반복으로

깊이가 크면 스택 오버플로가 납니다. JavaScript는 꼬리 호출 최적화(TCO)가 표준엔 있으나 V8은 미지원.

### 명시적 스택으로 변환

```ts
// src/recursion/inorderIter.ts
type Node = { value: number; left: Node | null; right: Node | null };

export function inorder(root: Node | null): number[] {
  const result: number[] = [];
  const stack: Node[] = [];
  let cur = root;
  while (cur || stack.length > 0) {
    while (cur) { stack.push(cur); cur = cur.left; }
    const node = stack.pop()!;
    result.push(node.value);
    cur = node.right;
  }
  return result;
}
```

같은 결과를 내지만 스택 깊이는 우리가 통제할 수 있습니다.

## 핵심 정리
- 재귀는 **베이스 + 자기 호출**의 조합.
- 분할정복은 재귀의 가장 강력한 패턴.
- 깊이가 깊어질 수 있으면 명시적 스택으로 옮겨라.

## 연습문제
1. 정수 n을 2진수 문자열로 변환하는 재귀 함수.
2. 배열을 거꾸로 만드는 재귀 함수 (in-place).

---

# 8장. 백트래킹

## 학습 목표
- 백트래킹의 본질이 "후보를 시도하고, 안 되면 되돌리기"임을 안다.
- 순열·조합·부분집합·N-Queens·스도쿠를 푼다.

## 8.1 백트래킹이란

탐색 공간을 트리처럼 펼치며, **유망하지 않은 가지를 일찍 잘라내는** 방법. DFS의 일종.

```
모든 후보 시도
  → 가지가 유망하지 않으면 즉시 되돌림(가지치기)
  → 해를 찾으면 기록
```

## 8.2 부분집합 — 모든 부분집합

```ts
// src/backtrack/subsets.ts
export function subsets<T>(arr: T[]): T[][] {
  const result: T[][] = [];
  const path: T[] = [];

  function dfs(start: number) {
    result.push(path.slice());
    for (let i = start; i < arr.length; i++) {
      path.push(arr[i]);
      dfs(i + 1);
      path.pop();
    }
  }

  dfs(0);
  return result;
}

console.log(subsets([1, 2, 3]));
// [[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]]
```

## 8.3 순열

```ts
// src/backtrack/permutations.ts
export function permutations<T>(arr: T[]): T[][] {
  const result: T[][] = [];
  const used = new Array<boolean>(arr.length).fill(false);
  const path: T[] = [];

  function dfs() {
    if (path.length === arr.length) {
      result.push(path.slice());
      return;
    }
    for (let i = 0; i < arr.length; i++) {
      if (used[i]) continue;
      used[i] = true;
      path.push(arr[i]);
      dfs();
      path.pop();
      used[i] = false;
    }
  }

  dfs();
  return result;
}

console.log(permutations([1, 2, 3]));
// 6가지
```

## 8.4 조합 — n개에서 r개 고르기

```ts
// src/backtrack/combinations.ts
export function combinations<T>(arr: T[], r: number): T[][] {
  const result: T[][] = [];
  const path: T[] = [];

  function dfs(start: number) {
    if (path.length === r) {
      result.push(path.slice());
      return;
    }
    // 가지치기: 남은 원소가 부족하면 종료
    if (path.length + (arr.length - start) < r) return;
    for (let i = start; i < arr.length; i++) {
      path.push(arr[i]);
      dfs(i + 1);
      path.pop();
    }
  }

  dfs(0);
  return result;
}

console.log(combinations([1, 2, 3, 4], 2));
// [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
```

## 8.5 N-Queens

n×n 체스판에 n개의 퀸을 서로 공격하지 않게 놓기.

```ts
// src/backtrack/nqueens.ts
export function solveNQueens(n: number): number[][] {
  const result: number[][] = [];
  const cols: number[] = []; // cols[r] = 행 r의 퀸의 열
  const usedCol = new Set<number>();
  const usedDiag1 = new Set<number>(); // r - c
  const usedDiag2 = new Set<number>(); // r + c

  function dfs(r: number) {
    if (r === n) { result.push(cols.slice()); return; }
    for (let c = 0; c < n; c++) {
      if (usedCol.has(c) || usedDiag1.has(r - c) || usedDiag2.has(r + c)) continue;
      cols.push(c);
      usedCol.add(c); usedDiag1.add(r - c); usedDiag2.add(r + c);
      dfs(r + 1);
      cols.pop();
      usedCol.delete(c); usedDiag1.delete(r - c); usedDiag2.delete(r + c);
    }
  }

  dfs(0);
  return result;
}

console.log(solveNQueens(4));   // 2가지
console.log(solveNQueens(8).length); // 92
```

## 8.6 스도쿠 풀이

```ts
// src/backtrack/sudoku.ts
type Board = number[][]; // 9x9, 0 = 빈칸

export function solveSudoku(board: Board): boolean {
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      if (board[r][c] !== 0) continue;
      for (let n = 1; n <= 9; n++) {
        if (canPlace(board, r, c, n)) {
          board[r][c] = n;
          if (solveSudoku(board)) return true;
          board[r][c] = 0;
        }
      }
      return false; // 1~9 다 안 되면 백트랙
    }
  }
  return true; // 빈칸 없음
}

function canPlace(board: Board, r: number, c: number, n: number): boolean {
  for (let i = 0; i < 9; i++) {
    if (board[r][i] === n || board[i][c] === n) return false;
  }
  const br = Math.floor(r / 3) * 3;
  const bc = Math.floor(c / 3) * 3;
  for (let i = br; i < br + 3; i++) {
    for (let j = bc; j < bc + 3; j++) {
      if (board[i][j] === n) return false;
    }
  }
  return true;
}

const puzzle: Board = [
  [5,3,0,0,7,0,0,0,0],
  [6,0,0,1,9,5,0,0,0],
  [0,9,8,0,0,0,0,6,0],
  [8,0,0,0,6,0,0,0,3],
  [4,0,0,8,0,3,0,0,1],
  [7,0,0,0,2,0,0,0,6],
  [0,6,0,0,0,0,2,8,0],
  [0,0,0,4,1,9,0,0,5],
  [0,0,0,0,8,0,0,7,9],
];

solveSudoku(puzzle);
console.log(puzzle.map(row => row.join("")).join("\n"));
```

## 핵심 정리
- 백트래킹 = DFS + 가지치기.
- 입력이 작아도(n=20 정도) 가능한 후보가 너무 많으면 가지치기를 잘 설계해야 한다.
- 일반 패턴: `path` 배열, `used` 집합, 정해진 순서대로 시도, 끝나면 되돌리기.

## 연습문제
1. 단어 게임: 격자에서 인접 칸을 따라 단어를 만들 수 있는지 검사.
2. 동전을 골라 합 N을 만드는 모든 방법을 출력.

---

# 9장. 동적 계획법(DP) 입문

## 학습 목표
- DP의 두 조건(중복 부분 문제, 최적 부분 구조)을 안다.
- 메모이제이션과 타뷸레이션을 모두 구현한다.
- 1차원 DP의 고전 문제 5개를 푼다.

## 9.1 DP의 두 조건

1. **중복 부분 문제(overlapping subproblems)** — 같은 부분 문제가 여러 번 나옴
2. **최적 부분 구조(optimal substructure)** — 부분 해의 조합으로 전체 해가 만들어짐

피보나치는 둘 다 만족 → DP로 풀 수 있음.

## 9.2 메모이제이션 vs 타뷸레이션

| 방식 | 특징 | 단점 |
|------|------|------|
| 메모이제이션 (top-down) | 재귀 + 캐시. 자연스러운 코드. | 콜 스택 깊이, 함수 호출 오버헤드 |
| 타뷸레이션 (bottom-up) | 반복문으로 작은 문제부터 채움. 빠름. | 의존 순서를 직접 정해야 함 |

## 9.3 피보나치 세 버전

```ts
// src/dp/fib.ts

// 1. 순수 재귀 — O(2^n)
export function fibRec(n: number): number {
  if (n < 2) return n;
  return fibRec(n - 1) + fibRec(n - 2);
}

// 2. 메모이제이션 — O(n)
export function fibMemo(n: number, memo = new Map<number, number>()): number {
  if (n < 2) return n;
  if (memo.has(n)) return memo.get(n)!;
  const v = fibMemo(n - 1, memo) + fibMemo(n - 2, memo);
  memo.set(n, v);
  return v;
}

// 3. 타뷸레이션 — O(n) 시간, O(1) 공간
export function fibIter(n: number): number {
  if (n < 2) return n;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) { [a, b] = [b, a + b]; }
  return b;
}
```

## 9.4 계단 오르기

n칸 계단을 한 번에 1칸 또는 2칸씩. 가능한 경로 수.

```ts
// src/dp/stairs.ts
export function climbStairs(n: number): number {
  if (n <= 2) return n;
  let a = 1, b = 2;
  for (let i = 3; i <= n; i++) { [a, b] = [b, a + b]; }
  return b;
}

console.log(climbStairs(5)); // 8
```

점화식: `f(n) = f(n-1) + f(n-2)`. 사실 피보나치.

## 9.5 도둑 — 인접 집 못 털기

```ts
// src/dp/houseRobber.ts
export function houseRobber(money: number[]): number {
  let prev = 0, curr = 0;
  for (const m of money) {
    [prev, curr] = [curr, Math.max(curr, prev + m)];
  }
  return curr;
}

console.log(houseRobber([2, 7, 9, 3, 1])); // 12
```

점화식: `f(i) = max(f(i-1), f(i-2) + money[i])`.

## 9.6 동전 거스름 — 최소 동전 수

```ts
// src/dp/coinChange.ts
export function coinChange(coins: number[], amount: number): number {
  const dp = new Array<number>(amount + 1).fill(Infinity);
  dp[0] = 0;
  for (let a = 1; a <= amount; a++) {
    for (const c of coins) {
      if (c <= a && dp[a - c] + 1 < dp[a]) dp[a] = dp[a - c] + 1;
    }
  }
  return dp[amount] === Infinity ? -1 : dp[amount];
}

console.log(coinChange([1, 2, 5], 11)); // 3 (5+5+1)
```

복잡도: O(amount × coins).

## 9.7 LIS — 가장 긴 증가 부분 수열

```ts
// src/dp/lis.ts

// O(n²)
export function lis(arr: number[]): number {
  const dp = new Array<number>(arr.length).fill(1);
  for (let i = 1; i < arr.length; i++) {
    for (let j = 0; j < i; j++) {
      if (arr[j] < arr[i]) dp[i] = Math.max(dp[i], dp[j] + 1);
    }
  }
  return Math.max(0, ...dp);
}

// O(n log n) — 이진 탐색 활용
export function lisFast(arr: number[]): number {
  const tails: number[] = [];
  for (const x of arr) {
    let lo = 0, hi = tails.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (tails[mid] < x) lo = mid + 1;
      else hi = mid;
    }
    tails[lo] = x;
  }
  return tails.length;
}

console.log(lisFast([10, 9, 2, 5, 3, 7, 101, 18])); // 4
```

`tails[i]`는 길이 i+1짜리 증가 부분수열의 마지막 원소 중 최솟값.

## 9.8 최대 부분합 (카데인)

연속 부분배열 합 최댓값.

```ts
// src/dp/kadane.ts
export function maxSubArray(nums: number[]): number {
  let best = nums[0], curr = nums[0];
  for (let i = 1; i < nums.length; i++) {
    curr = Math.max(nums[i], curr + nums[i]);
    best = Math.max(best, curr);
  }
  return best;
}

console.log(maxSubArray([-2, 1, -3, 4, -1, 2, 1, -5, 4])); // 6
```

복잡도: O(n).

## 핵심 정리
- DP는 **점화식 → 캐시**의 구조다. 점화식을 못 세우면 코드도 안 나온다.
- 1차원 DP는 보통 두 변수만으로 공간 O(1)로 줄일 수 있다.
- 의심나면 메모이제이션부터, 검증되면 타뷸레이션으로 옮겨라.

## 연습문제
1. 1, 2, 3을 더해 n을 만드는 방법의 수.
2. 가운데 한 글자를 추가/삭제/교체할 수 있을 때, 두 문자열 a → b 변환 최소 비용 (편집 거리, 다음 장 미리보기).

---

# 10장. DP 심화 — 패턴별 분류

## 학습 목표
- 2차원 DP 패턴(LCS, 편집 거리, 격자 경로)에 익숙해진다.
- 0-1 배낭과 무한 배낭의 차이를 안다.
- 비트마스크 DP를 맛본다.

## 10.1 LCS — 최장 공통 부분수열

```ts
// src/dp/lcs.ts
export function lcs(a: string, b: string): number {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
      else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  return dp[m][n];
}

console.log(lcs("ABCBDAB", "BDCAB")); // 4 (BDAB 또는 BCAB)
```

복잡도: O(mn).

### LCS 자체 복원

```ts
export function lcsString(a: string, b: string): string {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
      else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  let i = m, j = n;
  let s = "";
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) { s = a[i - 1] + s; i--; j--; }
    else if (dp[i - 1][j] >= dp[i][j - 1]) i--;
    else j--;
  }
  return s;
}

console.log(lcsString("ABCBDAB", "BDCAB")); // "BCAB"
```

## 10.2 편집 거리(Edit Distance / Levenshtein)

a → b로 만드는 데 필요한 삽입/삭제/교체 최소 횟수.

```ts
// src/dp/editDistance.ts
export function editDistance(a: string, b: string): number {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) dp[i][j] = dp[i - 1][j - 1];
      else dp[i][j] = 1 + Math.min(
        dp[i - 1][j],     // 삭제
        dp[i][j - 1],     // 삽입
        dp[i - 1][j - 1], // 교체
      );
    }
  }
  return dp[m][n];
}

console.log(editDistance("kitten", "sitting")); // 3
```

활용: 자동 교정, DNA 서열 비교, fuzzy 검색.

## 10.3 격자 경로의 수

m×n 격자에서 (0,0)에서 (m-1, n-1)까지, 오른쪽/아래로만 갈 때 경로 수.

```ts
// src/dp/uniquePaths.ts
export function uniquePaths(m: number, n: number): number {
  const dp = new Array<number>(n).fill(1);
  for (let i = 1; i < m; i++) {
    for (let j = 1; j < n; j++) dp[j] += dp[j - 1];
  }
  return dp[n - 1];
}

console.log(uniquePaths(3, 7)); // 28
```

공간 O(n) — 한 행만 유지.

## 10.4 0-1 배낭

각 아이템을 **한 번씩만** 담을 수 있을 때, 무게 W 안에서 가치 최대화.

```ts
// src/dp/knapsack01.ts
export function knapsack01(weights: number[], values: number[], W: number): number {
  const n = weights.length;
  // dp[w] = 무게 ≤ w일 때 최대 가치
  const dp = new Array<number>(W + 1).fill(0);
  for (let i = 0; i < n; i++) {
    // 뒤에서부터 — 한 번씩만 쓰도록
    for (let w = W; w >= weights[i]; w--) {
      dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
    }
  }
  return dp[W];
}

console.log(knapsack01([2, 3, 4, 5], [3, 4, 5, 6], 5)); // 7 (무게2+3, 가치3+4)
```

## 10.5 무한 배낭 (Unbounded Knapsack)

같은 아이템을 여러 번 담을 수 있을 때.

```ts
// src/dp/knapsackUnbounded.ts
export function knapsackUnbounded(weights: number[], values: number[], W: number): number {
  const dp = new Array<number>(W + 1).fill(0);
  for (let w = 1; w <= W; w++) {
    for (let i = 0; i < weights.length; i++) {
      if (weights[i] <= w) dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
    }
  }
  return dp[W];
}
```

차이점: 0-1은 안쪽 루프를 **뒤에서 앞으로**, 무한은 **앞에서 뒤로**. 이 한 줄 차이가 전부입니다.

## 10.6 행렬 체인 곱셈

행렬을 곱하는 순서에 따라 곱셈 횟수가 다릅니다. 최소 횟수.

```ts
// src/dp/matrixChain.ts
export function matrixChain(dims: number[]): number {
  const n = dims.length - 1; // 행렬 개수
  const dp: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let len = 2; len <= n; len++) {
    for (let i = 0; i <= n - len; i++) {
      const j = i + len - 1;
      dp[i][j] = Infinity;
      for (let k = i; k < j; k++) {
        const cost = dp[i][k] + dp[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1];
        if (cost < dp[i][j]) dp[i][j] = cost;
      }
    }
  }
  return dp[0][n - 1];
}

console.log(matrixChain([10, 30, 5, 60])); // 4500
```

복잡도: O(n³).

## 10.7 비트마스크 DP — 외판원 문제(TSP) 작은 n

n개 도시를 모두 방문하고 출발지로 돌아오는 최소 비용. n ≤ 20 정도면 O(n² · 2ⁿ).

```ts
// src/dp/tsp.ts
export function tsp(dist: number[][]): number {
  const n = dist.length;
  const FULL = (1 << n) - 1;
  const dp: number[][] = Array.from({ length: 1 << n }, () => new Array(n).fill(Infinity));
  dp[1][0] = 0; // 시작: 도시 0만 방문

  for (let mask = 1; mask <= FULL; mask++) {
    for (let u = 0; u < n; u++) {
      if (!(mask & (1 << u))) continue;
      if (dp[mask][u] === Infinity) continue;
      for (let v = 0; v < n; v++) {
        if (mask & (1 << v)) continue;
        const next = mask | (1 << v);
        const cost = dp[mask][u] + dist[u][v];
        if (cost < dp[next][v]) dp[next][v] = cost;
      }
    }
  }

  let best = Infinity;
  for (let u = 1; u < n; u++) {
    best = Math.min(best, dp[FULL][u] + dist[u][0]);
  }
  return best;
}

const distMatrix = [
  [0, 10, 15, 20],
  [10, 0, 35, 25],
  [15, 35, 0, 30],
  [20, 25, 30, 0],
];
console.log(tsp(distMatrix)); // 80
```

## 핵심 정리
- 2차원 DP: 두 인덱스가 등장하면 자연스럽게 2D 테이블.
- 배낭: 한 번 쓰면 역방향, 여러 번 쓰면 정방향.
- 비트마스크 DP는 n ≤ 20에서만. 그 이상은 다른 접근.

## 연습문제
1. 회문 개수 — 문자열 s의 모든 부분 회문의 개수를 O(n²)에 구하라.
2. LCS의 공간을 O(min(m, n))으로 줄여라.

---

# 11장. 그리디 알고리즘

## 학습 목표
- 그리디의 직관과 한계를 안다.
- 그리디로 풀리는 고전 문제들을 실제로 푼다.
- 그리디가 안 되는 경우를 식별한다.

## 11.1 그리디의 본질

매 단계에서 **지금 가장 좋아 보이는 선택**을 한다. 이게 전체적으로 최선이 되려면 두 조건이 필요합니다.

1. **그리디 선택 속성** — 매 단계의 지역 최적이 전역 최적을 만든다.
2. **최적 부분 구조** — 부분 해를 그대로 쓸 수 있다.

DP와 다른 점: DP는 모든 부분 문제를 풀고 비교, 그리디는 그 자리에서 결정.

## 11.2 활동 선택

겹치지 않게 가장 많은 활동 고르기. 끝나는 시간이 빠른 순으로 정렬 후 그리디.

```ts
// src/greedy/activitySelection.ts
type Activity = { start: number; end: number };

export function activitySelection(activities: Activity[]): Activity[] {
  const sorted = activities.slice().sort((a, b) => a.end - b.end);
  const result: Activity[] = [];
  let lastEnd = -Infinity;
  for (const act of sorted) {
    if (act.start >= lastEnd) {
      result.push(act);
      lastEnd = act.end;
    }
  }
  return result;
}

console.log(activitySelection([
  { start: 1, end: 4 },
  { start: 3, end: 5 },
  { start: 0, end: 6 },
  { start: 5, end: 7 },
  { start: 8, end: 9 },
  { start: 5, end: 9 },
]));
// 3개: (1,4) (5,7) (8,9)
```

증명 스케치: 가장 빨리 끝나는 활동을 골라 미래 자원을 최대화.

## 11.3 분수 배낭(Fractional Knapsack)

조각을 낼 수 있는 배낭. 단위 무게당 가치 큰 순으로.

```ts
// src/greedy/fractionalKnapsack.ts
export function fractionalKnapsack(weights: number[], values: number[], W: number): number {
  const items = weights.map((w, i) => ({ w, v: values[i], r: values[i] / w }));
  items.sort((a, b) => b.r - a.r);
  let total = 0, remaining = W;
  for (const it of items) {
    if (remaining === 0) break;
    if (it.w <= remaining) { total += it.v; remaining -= it.w; }
    else { total += it.r * remaining; remaining = 0; }
  }
  return total;
}

console.log(fractionalKnapsack([10, 20, 30], [60, 100, 120], 50)); // 240
```

0-1 배낭은 그리디로 안 풀립니다. **분수 가능 여부**가 핵심.

## 11.4 동전 거스름 (그리디 가능 케이스)

동전 단위가 1, 5, 10, 50, 100, 500처럼 "큰 단위가 작은 단위의 정수배"이면 그리디가 통합니다. {1, 3, 4}처럼 비표준이면 안 됩니다.

```ts
// src/greedy/coinChangeGreedy.ts
export function coinChangeGreedy(coins: number[], amount: number): number {
  const sorted = coins.slice().sort((a, b) => b - a);
  let count = 0, remain = amount;
  for (const c of sorted) {
    count += Math.floor(remain / c);
    remain %= c;
  }
  return remain === 0 ? count : -1;
}

console.log(coinChangeGreedy([1, 5, 10, 50, 100, 500], 1280));
```

확신이 없으면 9장의 DP로.

## 11.5 회의실 배정 (최소 회의실 수)

여러 회의를 모두 진행하려면 최소 몇 개의 방이 필요한가?

```ts
// src/greedy/meetingRooms.ts
type Meeting = { start: number; end: number };

export function minMeetingRooms(meetings: Meeting[]): number {
  const starts = meetings.map(m => m.start).sort((a, b) => a - b);
  const ends = meetings.map(m => m.end).sort((a, b) => a - b);
  let rooms = 0, i = 0, j = 0;
  while (i < starts.length) {
    if (starts[i] < ends[j]) { rooms++; i++; }
    else { j++; i++; }
  }
  return rooms;
}

console.log(minMeetingRooms([
  { start: 0, end: 30 },
  { start: 5, end: 10 },
  { start: 15, end: 20 },
])); // 2
```

## 11.6 허프만 코딩 (압축의 기초)

빈도 높은 글자에 짧은 코드 부여. 우선순위 큐 기반.

```ts
// src/greedy/huffman.ts
import { MinHeap } from "../ds/MinHeap"; // 자료구조 가이드북 11장

class HNode {
  constructor(
    public freq: number,
    public char: string | null = null,
    public left: HNode | null = null,
    public right: HNode | null = null,
  ) {}
}

export function huffmanCodes(text: string): Map<string, string> {
  const freq = new Map<string, number>();
  for (const ch of text) freq.set(ch, (freq.get(ch) ?? 0) + 1);

  const heap = new MinHeap<HNode>((a, b) => a.freq - b.freq);
  for (const [ch, f] of freq) heap.push(new HNode(f, ch));

  while (heap.length > 1) {
    const a = heap.pop()!;
    const b = heap.pop()!;
    heap.push(new HNode(a.freq + b.freq, null, a, b));
  }

  const root = heap.pop()!;
  const codes = new Map<string, string>();
  function dfs(node: HNode, path: string) {
    if (node.char !== null) { codes.set(node.char, path || "0"); return; }
    if (node.left) dfs(node.left, path + "0");
    if (node.right) dfs(node.right, path + "1");
  }
  dfs(root, "");
  return codes;
}

console.log(huffmanCodes("aabbccccdddd"));
```

## 핵심 정리
- 그리디는 **증명 가능할 때만** 신뢰하라.
- 활동 선택, 분수 배낭, 회의실, 허프만 — 잘 알려진 그리디.
- 의심나면 DP로 정답을 구하고 비교하라.

## 연습문제
1. 정수 배열에서 인접 두 수를 골라 곱하지 못한다는 제약 아래 합 최대 (도둑 문제 변형).
2. 1차원 좌표에서 모든 집을 덮는 최소 안테나 수.

---

# 12장. 그래프 — BFS/DFS와 응용

## 학습 목표
- 그래프 표현(인접 리스트/행렬)을 안다.
- BFS/DFS의 동작과 메모리 차이를 안다.
- 사이클 검출, 위상 정렬, 강결합 요소를 구현한다.

## 12.1 그래프 표현

인접 리스트 — 노드 V, 간선 E일 때 메모리 O(V + E).

```ts
// src/graph/Graph.ts
export class Graph {
  adj = new Map<number, [number, number][]>(); // 노드 → [이웃, 가중치]

  addNode(u: number): void {
    if (!this.adj.has(u)) this.adj.set(u, []);
  }

  addEdge(u: number, v: number, w = 1, undirected = true): void {
    this.addNode(u); this.addNode(v);
    this.adj.get(u)!.push([v, w]);
    if (undirected) this.adj.get(v)!.push([u, w]);
  }

  neighbors(u: number): [number, number][] { return this.adj.get(u) ?? []; }
  nodes(): IterableIterator<number> { return this.adj.keys(); }
  size(): number { return this.adj.size; }
}
```

## 12.2 BFS

큐 기반 — 가까운 노드부터.

```ts
// src/graph/bfs.ts
import { Graph } from "./Graph";

export function bfs(g: Graph, start: number): Map<number, number> {
  const dist = new Map<number, number>();
  dist.set(start, 0);
  const queue: number[] = [start];
  let head = 0;
  while (head < queue.length) {
    const u = queue[head++];
    for (const [v] of g.neighbors(u)) {
      if (!dist.has(v)) {
        dist.set(v, dist.get(u)! + 1);
        queue.push(v);
      }
    }
  }
  return dist;
}
```

`queue.shift()` 대신 인덱스 `head`를 쓰는 이유는 `shift()`가 O(n)이기 때문.

## 12.3 DFS — 재귀와 반복

```ts
// src/graph/dfs.ts
import { Graph } from "./Graph";

export function dfsRecursive(g: Graph, start: number): number[] {
  const order: number[] = [];
  const visited = new Set<number>();
  function visit(u: number) {
    if (visited.has(u)) return;
    visited.add(u);
    order.push(u);
    for (const [v] of g.neighbors(u)) visit(v);
  }
  visit(start);
  return order;
}

export function dfsIterative(g: Graph, start: number): number[] {
  const order: number[] = [];
  const visited = new Set<number>();
  const stack = [start];
  while (stack.length > 0) {
    const u = stack.pop()!;
    if (visited.has(u)) continue;
    visited.add(u);
    order.push(u);
    for (const [v] of g.neighbors(u)) {
      if (!visited.has(v)) stack.push(v);
    }
  }
  return order;
}
```

## 12.4 연결 요소(Connected Components)

```ts
// src/graph/connectedComponents.ts
import { Graph } from "./Graph";

export function connectedComponents(g: Graph): number[][] {
  const visited = new Set<number>();
  const result: number[][] = [];
  for (const u of g.nodes()) {
    if (visited.has(u)) continue;
    const comp: number[] = [];
    const stack = [u];
    while (stack.length > 0) {
      const x = stack.pop()!;
      if (visited.has(x)) continue;
      visited.add(x);
      comp.push(x);
      for (const [y] of g.neighbors(x)) if (!visited.has(y)) stack.push(y);
    }
    result.push(comp);
  }
  return result;
}
```

## 12.5 사이클 검출 — 무방향

```ts
// src/graph/hasCycleUndirected.ts
import { Graph } from "./Graph";

export function hasCycleUndirected(g: Graph): boolean {
  const visited = new Set<number>();
  function dfs(u: number, parent: number): boolean {
    visited.add(u);
    for (const [v] of g.neighbors(u)) {
      if (!visited.has(v)) {
        if (dfs(v, u)) return true;
      } else if (v !== parent) {
        return true;
      }
    }
    return false;
  }
  for (const u of g.nodes()) {
    if (!visited.has(u) && dfs(u, -1)) return true;
  }
  return false;
}
```

## 12.6 사이클 검출 — 방향

세 가지 색깔(흰=미방문, 회=현재 경로, 검=완료) 트릭.

```ts
// src/graph/hasCycleDirected.ts
import { Graph } from "./Graph";

export function hasCycleDirected(g: Graph): boolean {
  const color = new Map<number, 0 | 1 | 2>();
  for (const u of g.nodes()) color.set(u, 0);
  function dfs(u: number): boolean {
    color.set(u, 1);
    for (const [v] of g.neighbors(u)) {
      const c = color.get(v) ?? 0;
      if (c === 1) return true;        // 회색 만남 → 사이클
      if (c === 0 && dfs(v)) return true;
    }
    color.set(u, 2);
    return false;
  }
  for (const u of g.nodes()) {
    if (color.get(u) === 0 && dfs(u)) return true;
  }
  return false;
}
```

## 12.7 위상 정렬 (DFS 기반)

```ts
// src/graph/topoDfs.ts
import { Graph } from "./Graph";

export function topoSortDfs(g: Graph): number[] {
  const visited = new Set<number>();
  const order: number[] = [];
  function dfs(u: number) {
    if (visited.has(u)) return;
    visited.add(u);
    for (const [v] of g.neighbors(u)) dfs(v);
    order.push(u);
  }
  for (const u of g.nodes()) dfs(u);
  return order.reverse();
}
```

## 12.8 강결합 요소(SCC) — 코사라주

```ts
// src/graph/scc.ts
import { Graph } from "./Graph";

export function kosaraju(g: Graph): number[][] {
  const order: number[] = [];
  const visited = new Set<number>();

  // 1단계: 종료 시간 순 스택
  function dfs1(u: number) {
    if (visited.has(u)) return;
    visited.add(u);
    for (const [v] of g.neighbors(u)) dfs1(v);
    order.push(u);
  }
  for (const u of g.nodes()) dfs1(u);

  // 2단계: 역방향 그래프
  const rev = new Graph();
  for (const u of g.nodes()) rev.addNode(u);
  for (const u of g.nodes()) for (const [v, w] of g.neighbors(u)) {
    rev.addEdge(v, u, w, false);
  }

  // 3단계: 역순으로 DFS
  visited.clear();
  const sccs: number[][] = [];
  function dfs2(u: number, comp: number[]) {
    if (visited.has(u)) return;
    visited.add(u);
    comp.push(u);
    for (const [v] of rev.neighbors(u)) dfs2(v, comp);
  }
  for (let i = order.length - 1; i >= 0; i--) {
    const u = order[i];
    if (visited.has(u)) continue;
    const comp: number[] = [];
    dfs2(u, comp);
    sccs.push(comp);
  }
  return sccs;
}
```

## 12.9 이분 그래프 판정

BFS로 색칠해 가며 같은 색이 인접하면 거짓.

```ts
// src/graph/isBipartite.ts
import { Graph } from "./Graph";

export function isBipartite(g: Graph): boolean {
  const color = new Map<number, 0 | 1>();
  for (const start of g.nodes()) {
    if (color.has(start)) continue;
    color.set(start, 0);
    const queue = [start];
    let head = 0;
    while (head < queue.length) {
      const u = queue[head++];
      for (const [v] of g.neighbors(u)) {
        if (!color.has(v)) {
          color.set(v, color.get(u) === 0 ? 1 : 0);
          queue.push(v);
        } else if (color.get(v) === color.get(u)) {
          return false;
        }
      }
    }
  }
  return true;
}
```

## 핵심 정리
- BFS = 가까운 곳부터 (큐), DFS = 깊은 곳부터 (스택/재귀).
- 무방향 사이클 검출은 부모 체크. 방향은 3색 DFS.
- 위상 정렬, SCC, 이분 그래프는 모두 DFS/BFS의 변주.

## 연습문제
1. BFS로 미로(2D 격자) 최단 경로 + 경로 자체 복원.
2. DFS로 다리(bridge) 찾기 — 끊으면 그래프가 분리되는 간선.

---

# 13장. 그래프 최단경로

## 학습 목표
- 다익스트라(Dijkstra)를 우선순위 큐로 구현한다.
- 음수 가중치엔 벨만-포드(Bellman-Ford), 모든 쌍은 플로이드-워셜(Floyd-Warshall).
- 어떤 경우에 어떤 알고리즘인지 구분한다.

## 13.1 가중치 그래프

12장의 `Graph`를 그대로 씁니다. 간선 가중치 w가 함께 저장되어 있습니다.

## 13.2 다익스트라

**음수 가중치 없음** 보장. 한 출발점에서 모든 노드까지의 최단 거리.

```ts
// src/graph/dijkstra.ts
import { Graph } from "./Graph";
import { MinHeap } from "../ds/MinHeap";

export function dijkstra(g: Graph, start: number): {
  dist: Map<number, number>;
  prev: Map<number, number | null>;
} {
  const dist = new Map<number, number>();
  const prev = new Map<number, number | null>();
  for (const u of g.nodes()) { dist.set(u, Infinity); prev.set(u, null); }
  dist.set(start, 0);

  const pq = new MinHeap<[number, number]>((a, b) => a[0] - b[0]);
  pq.push([0, start]);

  while (!pq.isEmpty()) {
    const [d, u] = pq.pop()!;
    if (d > dist.get(u)!) continue;
    for (const [v, w] of g.neighbors(u)) {
      const nd = d + w;
      if (nd < dist.get(v)!) {
        dist.set(v, nd);
        prev.set(v, u);
        pq.push([nd, v]);
      }
    }
  }
  return { dist, prev };
}

export function pathTo(prev: Map<number, number | null>, target: number): number[] {
  const path: number[] = [];
  let cur: number | null = target;
  while (cur !== null) {
    path.push(cur);
    cur = prev.get(cur) ?? null;
  }
  return path.reverse();
}
```

```ts
import { Graph } from "./graph/Graph";
import { dijkstra, pathTo } from "./graph/dijkstra";

const g = new Graph();
g.addEdge(1, 2, 7);
g.addEdge(1, 3, 9);
g.addEdge(1, 6, 14);
g.addEdge(2, 3, 10);
g.addEdge(2, 4, 15);
g.addEdge(3, 4, 11);
g.addEdge(3, 6, 2);
g.addEdge(4, 5, 6);
g.addEdge(5, 6, 9);

const { dist, prev } = dijkstra(g, 1);
console.log([...dist]); // [[1,0],[2,7],[3,9],[6,11],[4,20],[5,20]]
console.log(pathTo(prev, 5)); // [1, 3, 6, 5]
```

복잡도: O((V + E) log V).

## 13.3 다익스트라가 음수에서 깨지는 이유

음수 간선이 있으면 "확정된" 거리에 더 짧은 경로가 나중에 등장할 수 있어 최적성이 깨집니다. 이런 경우는 벨만-포드.

## 13.4 벨만-포드

음수 가중치 OK. 음수 사이클도 검출.

```ts
// src/graph/bellmanFord.ts
import { Graph } from "./Graph";

export function bellmanFord(g: Graph, start: number): {
  dist: Map<number, number>;
  hasNegCycle: boolean;
} {
  const dist = new Map<number, number>();
  for (const u of g.nodes()) dist.set(u, Infinity);
  dist.set(start, 0);

  const V = g.size();

  // 모든 간선을 V-1번 완화
  for (let i = 0; i < V - 1; i++) {
    let updated = false;
    for (const u of g.nodes()) {
      if (dist.get(u) === Infinity) continue;
      for (const [v, w] of g.neighbors(u)) {
        if (dist.get(u)! + w < dist.get(v)!) {
          dist.set(v, dist.get(u)! + w);
          updated = true;
        }
      }
    }
    if (!updated) break;
  }

  // 한 번 더 완화되면 음수 사이클
  let hasNegCycle = false;
  for (const u of g.nodes()) {
    if (dist.get(u) === Infinity) continue;
    for (const [v, w] of g.neighbors(u)) {
      if (dist.get(u)! + w < dist.get(v)!) { hasNegCycle = true; break; }
    }
    if (hasNegCycle) break;
  }

  return { dist, hasNegCycle };
}
```

복잡도: O(VE).

## 13.5 플로이드-워셜 — 모든 쌍

```ts
// src/graph/floydWarshall.ts
export function floydWarshall(n: number, edges: [number, number, number][]): number[][] {
  const dp: number[][] = Array.from({ length: n }, () => new Array(n).fill(Infinity));
  for (let i = 0; i < n; i++) dp[i][i] = 0;
  for (const [u, v, w] of edges) dp[u][v] = Math.min(dp[u][v], w);

  for (let k = 0; k < n; k++) {
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (dp[i][k] + dp[k][j] < dp[i][j]) dp[i][j] = dp[i][k] + dp[k][j];
      }
    }
  }
  return dp;
}

const result = floydWarshall(4, [
  [0, 1, 5], [0, 3, 10],
  [1, 2, 3], [2, 3, 1],
]);
console.log(result[0][3]); // 9 (0→1→2→3)
```

복잡도: O(V³). 작은 그래프(V ≤ 400)에서 강력.

## 13.6 알고리즘 선택

| 상황 | 추천 |
|------|------|
| 단일 출발, 음수 없음 | 다익스트라 |
| 단일 출발, 음수 가능 | 벨만-포드 |
| 모든 쌍, 작은 V | 플로이드-워셜 |
| 모든 쌍, V 큰데 희소 | 다익스트라 V번 |
| 가중치 모두 1 | BFS |

## 핵심 정리
- 다익스트라는 **음수 안 됨**, 그러나 가장 빠름.
- 벨만-포드는 음수 + 사이클 검출.
- 플로이드-워셜은 작은 그래프 + 모든 쌍.

## 연습문제
1. 다익스트라로 K번째 최단 경로 구하기 (힌트: 노드별 방문 횟수 K번까지).
2. 가장 비용이 큰 간선의 비용을 최소화하는 경로 (병목 최단경로).

---

# 14장. 최소 신장 트리(MST)

## 학습 목표
- 신장 트리와 MST의 정의를 안다.
- 크루스칼과 프림을 모두 구현한다.
- 어떤 상황에 어떤 알고리즘이 유리한지 안다.

## 14.1 MST란

연결된 무방향 가중치 그래프에서, 모든 노드를 포함하면서 사이클이 없는 부분 그래프 중 **간선 가중치 합이 최소**인 것.

응용: 네트워크 연결 비용 최소화, 클러스터링.

## 14.2 크루스칼 — 간선 정렬 + 유니온-파인드

```ts
// src/graph/kruskal.ts
import { DisjointSet } from "../ds/DisjointSet"; // 자료구조 가이드북 13장

export function kruskal(n: number, edges: [number, number, number][]): {
  total: number;
  picked: [number, number, number][];
} {
  const sorted = edges.slice().sort((a, b) => a[2] - b[2]);
  const ds = new DisjointSet(n);
  const picked: [number, number, number][] = [];
  let total = 0;
  for (const [u, v, w] of sorted) {
    if (ds.union(u, v)) {
      picked.push([u, v, w]);
      total += w;
      if (picked.length === n - 1) break;
    }
  }
  return { total, picked };
}

const result = kruskal(7, [
  [0, 1, 7], [0, 3, 5], [1, 2, 8], [1, 3, 9],
  [1, 4, 7], [2, 4, 5], [3, 4, 15], [3, 5, 6],
  [4, 5, 8], [4, 6, 9], [5, 6, 11],
]);
console.log(result.total); // 39
```

복잡도: O(E log E). 간선 정렬이 병목.

## 14.3 프림 — 우선순위 큐

크루스칼이 간선 중심이라면, 프림은 노드 중심.

```ts
// src/graph/prim.ts
import { Graph } from "./Graph";
import { MinHeap } from "../ds/MinHeap";

export function prim(g: Graph, start: number): {
  total: number;
  parent: Map<number, number>;
} {
  const visited = new Set<number>();
  const parent = new Map<number, number>();
  const pq = new MinHeap<[number, number, number]>((a, b) => a[0] - b[0]); // [w, u, v]
  pq.push([0, start, start]);

  let total = 0;
  while (!pq.isEmpty()) {
    const [w, u, v] = pq.pop()!;
    if (visited.has(v)) continue;
    visited.add(v);
    if (u !== v) parent.set(v, u);
    total += w;
    for (const [next, weight] of g.neighbors(v)) {
      if (!visited.has(next)) pq.push([weight, v, next]);
    }
  }
  return { total, parent };
}
```

복잡도: O(E log V). 희소 그래프에서 크루스칼과 비슷, 밀집 그래프에선 더 유리.

## 14.4 비교

| 알고리즘 | 시간 | 적합 |
|----------|------|------|
| 크루스칼 | O(E log E) | 희소 그래프, 분산 환경 |
| 프림 | O(E log V) | 밀집 그래프 |

## 핵심 정리
- MST는 그리디 + (유니온-파인드 또는 우선순위 큐).
- 답은 유일하지 않을 수 있다(같은 가중치).

## 연습문제
1. 크루스칼로 두 번째로 작은 MST를 구하라.
2. 노드 추가 시 MST를 갱신하는 동적 MST를 설계하라.

---

# 15장. 문자열 알고리즘

## 학습 목표
- KMP, 라빈-카프, Z 알고리즘으로 부분 문자열 검색을 구현한다.
- 회문 처리(Manacher)와 접미사 배열을 안다.

## 15.1 부분 문자열 검색 — 단순법

```ts
// src/string/naiveSearch.ts
export function naiveSearch(text: string, pattern: string): number[] {
  const result: number[] = [];
  for (let i = 0; i <= text.length - pattern.length; i++) {
    let match = true;
    for (let j = 0; j < pattern.length; j++) {
      if (text[i + j] !== pattern[j]) { match = false; break; }
    }
    if (match) result.push(i);
  }
  return result;
}
```

복잡도: O(nm). 짧은 패턴이라면 충분.

## 15.2 KMP — Knuth-Morris-Pratt

실패 함수(failure function, π 또는 LPS)를 미리 계산해 일치 실패 시 패턴을 똑똑히 건너뜁니다.

```ts
// src/string/kmp.ts
export function kmpSearch(text: string, pattern: string): number[] {
  if (pattern.length === 0) return [];
  const lps = computeLPS(pattern);
  const result: number[] = [];
  let i = 0, j = 0;
  while (i < text.length) {
    if (text[i] === pattern[j]) { i++; j++; }
    if (j === pattern.length) {
      result.push(i - j);
      j = lps[j - 1];
    } else if (i < text.length && text[i] !== pattern[j]) {
      if (j > 0) j = lps[j - 1];
      else i++;
    }
  }
  return result;
}

function computeLPS(p: string): number[] {
  const lps = new Array<number>(p.length).fill(0);
  let len = 0, i = 1;
  while (i < p.length) {
    if (p[i] === p[len]) { len++; lps[i] = len; i++; }
    else if (len > 0) len = lps[len - 1];
    else { lps[i] = 0; i++; }
  }
  return lps;
}

console.log(kmpSearch("abxabcabcaby", "abcaby")); // [6]
```

복잡도: O(n + m).

## 15.3 라빈-카프 — 해시 기반

해시값을 굴리며(rolling hash) O(1)로 윈도우를 옮깁니다.

```ts
// src/string/rabinKarp.ts
export function rabinKarp(text: string, pattern: string): number[] {
  const m = pattern.length, n = text.length;
  if (m > n) return [];
  const BASE = 256, MOD = 1_000_000_007;
  let pHash = 0, tHash = 0, h = 1;
  for (let i = 0; i < m - 1; i++) h = (h * BASE) % MOD;
  for (let i = 0; i < m; i++) {
    pHash = (pHash * BASE + pattern.charCodeAt(i)) % MOD;
    tHash = (tHash * BASE + text.charCodeAt(i)) % MOD;
  }
  const result: number[] = [];
  for (let i = 0; i <= n - m; i++) {
    if (pHash === tHash) {
      let match = true;
      for (let j = 0; j < m; j++) {
        if (text[i + j] !== pattern[j]) { match = false; break; }
      }
      if (match) result.push(i);
    }
    if (i < n - m) {
      tHash = (BASE * (tHash - text.charCodeAt(i) * h) + text.charCodeAt(i + m)) % MOD;
      if (tHash < 0) tHash += MOD;
    }
  }
  return result;
}

console.log(rabinKarp("abracadabra", "abra")); // [0, 7]
```

복잡도: 평균 O(n + m), 최악 O(nm) (해시 충돌 시).

## 15.4 Z 알고리즘

각 위치 i에서 "그 위치부터 시작해 원본 접두사와 몇 글자 일치하는가" 배열.

```ts
// src/string/z.ts
export function zArray(s: string): number[] {
  const n = s.length;
  const z = new Array<number>(n).fill(0);
  z[0] = n;
  let l = 0, r = 0;
  for (let i = 1; i < n; i++) {
    if (i < r) z[i] = Math.min(r - i, z[i - l]);
    while (i + z[i] < n && s[z[i]] === s[i + z[i]]) z[i]++;
    if (i + z[i] > r) { l = i; r = i + z[i]; }
  }
  return z;
}

export function zSearch(text: string, pattern: string): number[] {
  const sep = "\u0000";
  const z = zArray(pattern + sep + text);
  const result: number[] = [];
  for (let i = pattern.length + 1; i < z.length; i++) {
    if (z[i] === pattern.length) result.push(i - pattern.length - 1);
  }
  return result;
}

console.log(zSearch("abxabcabcaby", "abcaby")); // [6]
```

복잡도: O(n + m).

## 15.5 Manacher — 모든 회문 부분 문자열

가장 긴 회문 부분 문자열을 O(n).

```ts
// src/string/manacher.ts
export function longestPalindrome(s: string): string {
  if (s.length === 0) return "";
  // 짝수/홀수 통합을 위해 # 삽입
  const t = "^#" + s.split("").join("#") + "#$";
  const p = new Array<number>(t.length).fill(0);
  let center = 0, right = 0;
  for (let i = 1; i < t.length - 1; i++) {
    const mirror = 2 * center - i;
    if (i < right) p[i] = Math.min(right - i, p[mirror]);
    while (t[i + 1 + p[i]] === t[i - 1 - p[i]]) p[i]++;
    if (i + p[i] > right) { center = i; right = i + p[i]; }
  }
  let maxLen = 0, maxCenter = 0;
  for (let i = 0; i < t.length; i++) {
    if (p[i] > maxLen) { maxLen = p[i]; maxCenter = i; }
  }
  const start = (maxCenter - maxLen) >> 1;
  return s.slice(start, start + maxLen);
}

console.log(longestPalindrome("babad"));   // "bab" 또는 "aba"
console.log(longestPalindrome("cbbd"));    // "bb"
```

복잡도: O(n).

## 15.6 접미사 배열 (Suffix Array) — 단순 구현

문자열의 모든 접미사를 사전순으로 정렬한 인덱스 배열.

```ts
// src/string/suffixArray.ts
export function suffixArray(s: string): number[] {
  const indices = Array.from({ length: s.length }, (_, i) => i);
  indices.sort((a, b) => {
    const sa = s.slice(a), sb = s.slice(b);
    return sa < sb ? -1 : sa > sb ? 1 : 0;
  });
  return indices;
}

console.log(suffixArray("banana"));
// [5, 3, 1, 0, 4, 2] — a, ana, anana, banana, na, nana
```

복잡도: 단순 구현 O(n² log n), 효율적 구현(SA-IS, DC3) O(n).

## 15.7 LCP — 최장 공통 접두사 배열

```ts
// src/string/lcp.ts
export function lcpArray(s: string, sa: number[]): number[] {
  const n = s.length;
  const rank = new Array<number>(n).fill(0);
  for (let i = 0; i < n; i++) rank[sa[i]] = i;
  const lcp = new Array<number>(n).fill(0);
  let h = 0;
  for (let i = 0; i < n; i++) {
    if (rank[i] > 0) {
      const j = sa[rank[i] - 1];
      while (i + h < n && j + h < n && s[i + h] === s[j + h]) h++;
      lcp[rank[i]] = h;
      if (h > 0) h--;
    } else {
      h = 0;
    }
  }
  return lcp;
}
```

활용: 가장 긴 반복 부분 문자열, 서로 다른 부분 문자열의 개수.

## 핵심 정리
- 짧은 패턴: 단순법.
- 일반: KMP 또는 Z.
- 다중 패턴: Aho-Corasick (트라이 + 실패 링크, 본 책 범위 외).
- 회문 모두: Manacher.

## 연습문제
1. KMP의 LPS 배열로 패턴의 가장 긴 반복 접두사를 구하라.
2. 두 문자열의 최장 공통 부분 문자열을 접미사 배열로 구하라.

---

# 16장. 비트마스킹

## 학습 목표
- 비트 연산자(`&`, `|`, `^`, `~`, `<<`, `>>`)를 자유롭게 쓴다.
- 부분집합을 비트마스크로 다룬다.
- DP에서 비트마스크를 활용한다.

## 16.1 기본 비트 연산

```ts
// src/bit/basics.ts
export const setBit = (mask: number, i: number): number => mask | (1 << i);
export const clearBit = (mask: number, i: number): number => mask & ~(1 << i);
export const toggleBit = (mask: number, i: number): number => mask ^ (1 << i);
export const checkBit = (mask: number, i: number): boolean => (mask & (1 << i)) !== 0;

/** 1의 개수 — Brian Kernighan */
export function popcount(mask: number): number {
  let count = 0;
  while (mask !== 0) {
    mask &= mask - 1;
    count++;
  }
  return count;
}

/** 가장 낮은 1의 위치 — log */
export const lowestBit = (mask: number): number => Math.log2(mask & -mask) | 0;

console.log(popcount(0b10110101));  // 5
console.log(checkBit(0b1010, 1));   // true
console.log(setBit(0b1010, 0));     // 11 (0b1011)
```

## 16.2 부분집합 순회

n개 원소의 모든 부분집합은 0 ~ 2ⁿ-1.

```ts
// src/bit/subsets.ts
export function allSubsets<T>(arr: T[]): T[][] {
  const n = arr.length;
  const result: T[][] = [];
  for (let mask = 0; mask < 1 << n; mask++) {
    const subset: T[] = [];
    for (let i = 0; i < n; i++) {
      if (mask & (1 << i)) subset.push(arr[i]);
    }
    result.push(subset);
  }
  return result;
}

console.log(allSubsets([1, 2, 3]));
```

## 16.3 부분집합의 부분집합

특정 마스크의 부분집합만 순회. DP에서 자주 쓰임.

```ts
export function subsetsOf(mask: number): number[] {
  const result: number[] = [];
  let s = mask;
  while (true) {
    result.push(s);
    if (s === 0) break;
    s = (s - 1) & mask;
  }
  return result;
}

console.log(subsetsOf(0b1011));
// [11, 10, 9, 8, 3, 2, 1, 0]
```

## 16.4 비트마스크 DP — 다른 시각으로 보기

10장에서 본 TSP는 `dp[mask][u]`. 마스크는 "지금까지 방문한 도시들의 집합".

```ts
// src/bit/assignment.ts
/** N명에게 N개의 작업 할당 — 각 작업의 비용 행렬, 총비용 최소 */
export function minAssignmentCost(cost: number[][]): number {
  const n = cost.length;
  const FULL = (1 << n) - 1;
  // dp[mask] = mask에 속한 작업들이 i번째 사람들에게 할당됐을 때 최소 비용
  const dp = new Array<number>(1 << n).fill(Infinity);
  dp[0] = 0;
  for (let mask = 0; mask < FULL; mask++) {
    if (dp[mask] === Infinity) continue;
    const i = popcount(mask); // 다음 사람
    for (let j = 0; j < n; j++) {
      if (mask & (1 << j)) continue;
      const next = mask | (1 << j);
      const v = dp[mask] + cost[i][j];
      if (v < dp[next]) dp[next] = v;
    }
  }
  return dp[FULL];
}

function popcount(m: number) {
  let c = 0; while (m !== 0) { m &= m - 1; c++; } return c;
}

console.log(minAssignmentCost([
  [9, 2, 7, 8],
  [6, 4, 3, 7],
  [5, 8, 1, 8],
  [7, 6, 9, 4],
])); // 13
```

## 16.5 32비트 한계와 BigInt

JavaScript 비트 연산은 32비트 정수만 다룹니다. 33비트 이상이 필요하면 `BigInt`로 옮기세요.

```ts
const big = (1n << 50n) | (1n << 40n);
console.log(big); // 큰 수
```

## 핵심 정리
- 비트마스크는 **작은 집합**(원소 ≤ 30개 정도)을 빠르게 다루는 도구.
- 부분집합 DP, 작업 할당, TSP 같은 NP-hard 문제의 작은 인스턴스에 강력.

## 연습문제
1. n비트 정수 두 개의 해밍 거리(다른 비트 수)를 구하라.
2. 그레이 코드 — 인접 두 수가 1비트만 차이나는 수열을 생성하라.

---

# 17장. 수학 알고리즘

## 학습 목표
- 정수론 기본기(GCD, LCM, 모듈러, 소수)를 안다.
- 빠른 거듭제곱과 모듈러 역원을 구한다.
- 조합론 기본 공식을 코드로 옮긴다.

## 17.1 GCD/LCM

```ts
// src/math/gcd.ts
export function gcd(a: number, b: number): number {
  a = Math.abs(a); b = Math.abs(b);
  while (b !== 0) [a, b] = [b, a % b];
  return a;
}

export function lcm(a: number, b: number): number {
  return (a / gcd(a, b)) * b;
}

console.log(gcd(48, 18));  // 6
console.log(lcm(12, 18));  // 36
```

## 17.2 확장 유클리드 — 베주 항등식

ax + by = gcd(a, b)인 x, y를 함께 구함.

```ts
// src/math/extGcd.ts
export function extGcd(a: number, b: number): [number, number, number] {
  if (b === 0) return [a, 1, 0];
  const [g, x1, y1] = extGcd(b, a % b);
  return [g, y1, x1 - Math.floor(a / b) * y1];
}

console.log(extGcd(30, 18)); // [6, -1, 2] → 30×(-1) + 18×2 = 6
```

활용: 모듈러 역원.

## 17.3 빠른 거듭제곱 (모듈러 포함)

```ts
// src/math/power.ts
export function power(base: bigint, exp: bigint, mod: bigint): bigint {
  let result = 1n;
  base = base % mod;
  while (exp > 0n) {
    if (exp % 2n === 1n) result = (result * base) % mod;
    exp /= 2n;
    base = (base * base) % mod;
  }
  return result;
}

console.log(power(2n, 100n, 1_000_000_007n)); // 모듈러 거듭제곱
```

복잡도: O(log exp).

## 17.4 모듈러 역원

페르마의 소정리: p가 소수이면 a^(p-2) ≡ a^(-1) (mod p).

```ts
// src/math/modInverse.ts
import { power } from "./power";

export function modInverse(a: bigint, p: bigint): bigint {
  return power(a, p - 2n, p);
}

const P = 1_000_000_007n;
console.log(modInverse(3n, P));
```

활용: 조합 nCr 모듈러 계산.

## 17.5 에라토스테네스의 체 — 소수 찾기

```ts
// src/math/sieve.ts
export function sieve(n: number): boolean[] {
  const isPrime = new Array<boolean>(n + 1).fill(true);
  isPrime[0] = isPrime[1] = false;
  for (let i = 2; i * i <= n; i++) {
    if (!isPrime[i]) continue;
    for (let j = i * i; j <= n; j += i) isPrime[j] = false;
  }
  return isPrime;
}

export function primesUpTo(n: number): number[] {
  const sv = sieve(n);
  const result: number[] = [];
  for (let i = 2; i <= n; i++) if (sv[i]) result.push(i);
  return result;
}

console.log(primesUpTo(30)); // [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

복잡도: O(n log log n).

## 17.6 단일 소수 판정 — 밀러-라빈

큰 수에 대해서. 결정적 + 작은 시드로 안전.

```ts
// src/math/millerRabin.ts
import { power } from "./power";

function isComposite(n: bigint, a: bigint, d: bigint, s: bigint): boolean {
  let x = power(a, d, n);
  if (x === 1n || x === n - 1n) return false;
  for (let r = 0n; r < s - 1n; r++) {
    x = (x * x) % n;
    if (x === n - 1n) return false;
  }
  return true;
}

export function isPrime(n: bigint): boolean {
  if (n < 2n) return false;
  for (const p of [2n, 3n, 5n, 7n, 11n, 13n, 17n, 19n, 23n, 29n, 31n, 37n]) {
    if (n === p) return true;
    if (n % p === 0n) return false;
  }
  let d = n - 1n;
  let s = 0n;
  while (d % 2n === 0n) { d /= 2n; s++; }
  for (const a of [2n, 3n, 5n, 7n, 11n, 13n, 17n, 19n, 23n, 29n, 31n, 37n]) {
    if (isComposite(n, a, d, s)) return false;
  }
  return true;
}

console.log(isPrime(1_000_000_007n)); // true
console.log(isPrime(1_000_000_009n)); // true
```

위 시드 셋은 64비트 정수까지 결정적입니다.

## 17.7 조합 nCr 모듈러

```ts
// src/math/comb.ts
import { power } from "./power";

const MOD = 1_000_000_007n;

export class Comb {
  private fact: bigint[] = [1n];
  private invFact: bigint[] = [1n];

  constructor(maxN: number) {
    for (let i = 1; i <= maxN; i++) {
      this.fact.push((this.fact[i - 1] * BigInt(i)) % MOD);
    }
    this.invFact[maxN] = power(this.fact[maxN], MOD - 2n, MOD);
    for (let i = maxN - 1; i >= 0; i--) {
      this.invFact[i] = (this.invFact[i + 1] * BigInt(i + 1)) % MOD;
    }
  }

  nCr(n: number, r: number): bigint {
    if (r < 0 || r > n) return 0n;
    return (this.fact[n] * this.invFact[r] % MOD) * this.invFact[n - r] % MOD;
  }
}

const c = new Comb(100);
console.log(c.nCr(10, 3));  // 120n
console.log(c.nCr(50, 25)); // 모듈러 결과
```

## 17.8 카탈란 수

이진 트리 개수, 괄호 짝짓기, ...

```ts
// src/math/catalan.ts
import { Comb } from "./comb";

const MOD = 1_000_000_007n;

export function catalan(n: number, comb: Comb): bigint {
  return comb.nCr(2 * n, n) * power(BigInt(n + 1), MOD - 2n, MOD) % MOD;
}

function power(base: bigint, exp: bigint, mod: bigint): bigint {
  let r = 1n; base = base % mod;
  while (exp > 0n) {
    if (exp % 2n === 1n) r = (r * base) % mod;
    exp /= 2n; base = (base * base) % mod;
  }
  return r;
}
```

## 핵심 정리
- 모듈러 거듭제곱은 정수론 알고리즘의 기본기.
- 큰 수는 항상 BigInt.
- 조합 모듈러는 fact/invFact 전처리 + O(1) 쿼리.

## 연습문제
1. 두 수의 GCD를 BigInt로 구현하라.
2. 1부터 N까지 각 수의 약수 개수를 O(N log N)에 구하라.

---

# 18장. 기하 알고리즘

## 학습 목표
- 점·선분·다각형 기본 연산을 구현한다.
- 외적(cross product) 한 줄로 좌/우/공선 판정.
- 볼록 껍질(Convex Hull)을 그래엄 스캔으로 만든다.

## 18.1 점과 외적

```ts
// src/geom/basics.ts
export type Point = { x: number; y: number };

export function cross(o: Point, a: Point, b: Point): number {
  return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
}

/** 양수: 반시계, 음수: 시계, 0: 공선 */
export function ccw(o: Point, a: Point, b: Point): -1 | 0 | 1 {
  const v = cross(o, a, b);
  return v > 0 ? 1 : v < 0 ? -1 : 0;
}

export function dist(a: Point, b: Point): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}
```

## 18.2 선분 교차 판정

```ts
// src/geom/segmentIntersect.ts
import { Point, ccw } from "./basics";

export function segmentsIntersect(p1: Point, p2: Point, p3: Point, p4: Point): boolean {
  const d1 = ccw(p3, p4, p1);
  const d2 = ccw(p3, p4, p2);
  const d3 = ccw(p1, p2, p3);
  const d4 = ccw(p1, p2, p4);
  if (d1 !== d2 && d3 !== d4) return true;
  // 공선 케이스
  if (d1 === 0 && onSegment(p3, p4, p1)) return true;
  if (d2 === 0 && onSegment(p3, p4, p2)) return true;
  if (d3 === 0 && onSegment(p1, p2, p3)) return true;
  if (d4 === 0 && onSegment(p1, p2, p4)) return true;
  return false;
}

function onSegment(a: Point, b: Point, p: Point): boolean {
  return Math.min(a.x, b.x) <= p.x && p.x <= Math.max(a.x, b.x)
      && Math.min(a.y, b.y) <= p.y && p.y <= Math.max(a.y, b.y);
}
```

## 18.3 다각형 면적 — 신발끈 공식

```ts
// src/geom/polygonArea.ts
import { Point } from "./basics";

export function polygonArea(pts: Point[]): number {
  let area = 0;
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length];
    area += a.x * b.y - a.y * b.x;
  }
  return Math.abs(area) / 2;
}

console.log(polygonArea([{x:0,y:0},{x:4,y:0},{x:4,y:3},{x:0,y:3}])); // 12
```

## 18.4 점이 다각형 안에 있는가 — 광선 캐스팅

```ts
// src/geom/pointInPolygon.ts
import { Point } from "./basics";

export function pointInPolygon(p: Point, polygon: Point[]): boolean {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x, yi = polygon[i].y;
    const xj = polygon[j].x, yj = polygon[j].y;
    const intersect = (yi > p.y) !== (yj > p.y)
      && p.x < ((xj - xi) * (p.y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}
```

## 18.5 볼록 껍질 — 그래엄 스캔

```ts
// src/geom/convexHull.ts
import { Point, ccw } from "./basics";

export function convexHull(pts: Point[]): Point[] {
  if (pts.length < 3) return pts.slice();
  // 가장 아래/왼쪽 점을 시작점
  let p0 = pts[0];
  for (const p of pts) {
    if (p.y < p0.y || (p.y === p0.y && p.x < p0.x)) p0 = p;
  }
  const sorted = pts.filter(p => p !== p0).sort((a, b) => {
    const c = ccw(p0, a, b);
    if (c !== 0) return -c;
    return ((a.x - p0.x) ** 2 + (a.y - p0.y) ** 2)
         - ((b.x - p0.x) ** 2 + (b.y - p0.y) ** 2);
  });
  const hull: Point[] = [p0];
  for (const p of sorted) {
    while (hull.length >= 2 && ccw(hull[hull.length - 2], hull[hull.length - 1], p) <= 0) {
      hull.pop();
    }
    hull.push(p);
  }
  return hull;
}

console.log(convexHull([
  {x:0,y:3},{x:2,y:2},{x:1,y:1},{x:2,y:1},{x:3,y:0},{x:0,y:0},{x:3,y:3}
]));
```

복잡도: O(n log n).

## 18.6 두 점 거리 최솟값 (분할정복)

```ts
// src/geom/closestPair.ts
import { Point, dist } from "./basics";

export function closestPair(pts: Point[]): number {
  const sortedX = pts.slice().sort((a, b) => a.x - b.x);
  const sortedY = pts.slice().sort((a, b) => a.y - b.y);
  return solve(sortedX, sortedY);
}

function solve(px: Point[], py: Point[]): number {
  const n = px.length;
  if (n <= 3) {
    let best = Infinity;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
      best = Math.min(best, dist(px[i], px[j]));
    }
    return best;
  }
  const mid = n >> 1;
  const midX = px[mid].x;
  const pxLeft = px.slice(0, mid);
  const pxRight = px.slice(mid);
  const pyLeft: Point[] = [], pyRight: Point[] = [];
  const set = new Set(pxLeft);
  for (const p of py) (set.has(p) ? pyLeft : pyRight).push(p);

  const dl = solve(pxLeft, pyLeft);
  const dr = solve(pxRight, pyRight);
  let d = Math.min(dl, dr);

  const strip = py.filter(p => Math.abs(p.x - midX) < d);
  for (let i = 0; i < strip.length; i++) {
    for (let j = i + 1; j < strip.length && strip[j].y - strip[i].y < d; j++) {
      d = Math.min(d, dist(strip[i], strip[j]));
    }
  }
  return d;
}
```

복잡도: O(n log n).

## 핵심 정리
- 외적 ccw는 기하 알고리즘의 만능 도구.
- 부동소수점 오차에 주의 — eps 비교 필요할 때 많음.

## 연습문제
1. 두 직선의 교점을 구하라.
2. n개의 점 중 어떤 점이 볼록 껍질의 꼭짓점인지 표시하라.

---

# 19장. 보조 자료구조 — 세그먼트 트리·펜윅 트리

## 학습 목표
- 구간 합/최솟값 같은 구간 쿼리 + 점 갱신을 O(log n)에 처리한다.
- 펜윅 트리(BIT)와 세그먼트 트리의 차이를 안다.

## 19.1 펜윅 트리 — 구간 합

```ts
// src/ds/Fenwick.ts
export class Fenwick {
  private tree: number[];

  constructor(size: number) {
    this.tree = new Array<number>(size + 1).fill(0);
  }

  /** index에 delta를 더함 (1-indexed 내부) */
  update(i: number, delta: number): void {
    for (i = i + 1; i < this.tree.length; i += i & -i) {
      this.tree[i] += delta;
    }
  }

  /** [0, i] 누적합 */
  prefix(i: number): number {
    let sum = 0;
    for (i = i + 1; i > 0; i -= i & -i) sum += this.tree[i];
    return sum;
  }

  /** [l, r] 구간합 */
  range(l: number, r: number): number {
    if (l === 0) return this.prefix(r);
    return this.prefix(r) - this.prefix(l - 1);
  }
}

const f = new Fenwick(10);
[3, 2, -1, 6, 5, 4, -3, 3, 7, 2].forEach((v, i) => f.update(i, v));
console.log(f.range(0, 9));  // 28
console.log(f.range(2, 5));  // 14
f.update(3, -6); // arr[3] 6 -> 0
console.log(f.range(2, 5));  // 8
```

복잡도: 갱신 O(log n), 쿼리 O(log n).

## 19.2 세그먼트 트리 — 더 일반적

구간 합뿐 아니라 min/max/gcd 등 결합법칙을 만족하는 모든 연산.

```ts
// src/ds/SegmentTree.ts
export class SegmentTree<T> {
  private tree: T[];
  private n: number;

  constructor(
    arr: T[],
    private identity: T,
    private op: (a: T, b: T) => T,
  ) {
    this.n = arr.length;
    this.tree = new Array<T>(4 * this.n).fill(identity);
    if (this.n > 0) this.build(arr, 1, 0, this.n - 1);
  }

  private build(arr: T[], node: number, l: number, r: number): void {
    if (l === r) { this.tree[node] = arr[l]; return; }
    const mid = (l + r) >> 1;
    this.build(arr, node * 2, l, mid);
    this.build(arr, node * 2 + 1, mid + 1, r);
    this.tree[node] = this.op(this.tree[node * 2], this.tree[node * 2 + 1]);
  }

  update(i: number, value: T): void {
    this.upd(1, 0, this.n - 1, i, value);
  }

  private upd(node: number, l: number, r: number, i: number, value: T): void {
    if (l === r) { this.tree[node] = value; return; }
    const mid = (l + r) >> 1;
    if (i <= mid) this.upd(node * 2, l, mid, i, value);
    else this.upd(node * 2 + 1, mid + 1, r, i, value);
    this.tree[node] = this.op(this.tree[node * 2], this.tree[node * 2 + 1]);
  }

  query(l: number, r: number): T {
    return this.q(1, 0, this.n - 1, l, r);
  }

  private q(node: number, nl: number, nr: number, l: number, r: number): T {
    if (r < nl || nr < l) return this.identity;
    if (l <= nl && nr <= r) return this.tree[node];
    const mid = (nl + nr) >> 1;
    return this.op(
      this.q(node * 2, nl, mid, l, r),
      this.q(node * 2 + 1, mid + 1, nr, l, r),
    );
  }
}
```

```ts
import { SegmentTree } from "./ds/SegmentTree";

const minTree = new SegmentTree<number>(
  [3, 1, 4, 1, 5, 9, 2, 6, 5, 3],
  Infinity,
  (a, b) => Math.min(a, b),
);
console.log(minTree.query(0, 4)); // 1
console.log(minTree.query(5, 9)); // 2
minTree.update(5, 0);
console.log(minTree.query(0, 9)); // 0
```

복잡도: 빌드 O(n), 갱신/쿼리 O(log n).

## 19.3 구간 갱신 — 지연 전파 (Lazy Propagation)

세그먼트 트리에 "[l, r]에 모두 +x"를 O(log n)에 가능하게.

```ts
// src/ds/LazySegmentTree.ts
export class LazySumSegTree {
  private tree: number[];
  private lazy: number[];
  private n: number;

  constructor(arr: number[]) {
    this.n = arr.length;
    this.tree = new Array(4 * this.n).fill(0);
    this.lazy = new Array(4 * this.n).fill(0);
    if (this.n > 0) this.build(arr, 1, 0, this.n - 1);
  }

  private build(arr: number[], node: number, l: number, r: number): void {
    if (l === r) { this.tree[node] = arr[l]; return; }
    const mid = (l + r) >> 1;
    this.build(arr, node * 2, l, mid);
    this.build(arr, node * 2 + 1, mid + 1, r);
    this.tree[node] = this.tree[node * 2] + this.tree[node * 2 + 1];
  }

  private push(node: number, l: number, r: number): void {
    if (this.lazy[node] !== 0) {
      const mid = (l + r) >> 1;
      this.apply(node * 2, l, mid, this.lazy[node]);
      this.apply(node * 2 + 1, mid + 1, r, this.lazy[node]);
      this.lazy[node] = 0;
    }
  }

  private apply(node: number, l: number, r: number, value: number): void {
    this.tree[node] += (r - l + 1) * value;
    this.lazy[node] += value;
  }

  update(l: number, r: number, value: number): void {
    this.upd(1, 0, this.n - 1, l, r, value);
  }

  private upd(node: number, nl: number, nr: number, l: number, r: number, value: number): void {
    if (r < nl || nr < l) return;
    if (l <= nl && nr <= r) { this.apply(node, nl, nr, value); return; }
    this.push(node, nl, nr);
    const mid = (nl + nr) >> 1;
    this.upd(node * 2, nl, mid, l, r, value);
    this.upd(node * 2 + 1, mid + 1, nr, l, r, value);
    this.tree[node] = this.tree[node * 2] + this.tree[node * 2 + 1];
  }

  query(l: number, r: number): number {
    return this.q(1, 0, this.n - 1, l, r);
  }

  private q(node: number, nl: number, nr: number, l: number, r: number): number {
    if (r < nl || nr < l) return 0;
    if (l <= nl && nr <= r) return this.tree[node];
    this.push(node, nl, nr);
    const mid = (nl + nr) >> 1;
    return this.q(node * 2, nl, mid, l, r) + this.q(node * 2 + 1, mid + 1, nr, l, r);
  }
}

const t = new LazySumSegTree([1, 2, 3, 4, 5]);
t.update(1, 3, 10);
console.log(t.query(0, 4)); // 1 + 12 + 13 + 14 + 5 = 45
```

## 핵심 정리
- 펜윅: 구간 합 전용. 코드가 짧고 빠름.
- 세그먼트: 일반적. 결합법칙만 만족하면 됨.
- 구간 갱신은 지연 전파.

## 연습문제
1. 펜윅으로 점 갱신 + 구간 합 외에, 좌표 압축을 곁들여 인버전(역순쌍) 개수를 구하라.
2. 세그먼트 트리에 "구간 최댓값과 그 개수"를 동시에 저장하라.

---

# 20장. 종합 실습 — 코딩 테스트 풀이 패턴 모음

## 학습 목표
- 자주 등장하는 문제 유형의 풀이 템플릿을 익힌다.
- 한 문제에 여러 알고리즘을 결합하는 감각을 기른다.

## 20.1 두 포인터

정렬된 배열에서 합이 target인 두 수 찾기.

```ts
// src/pattern/twoSum.ts
export function twoSumSorted(arr: number[], target: number): [number, number] | null {
  let l = 0, r = arr.length - 1;
  while (l < r) {
    const s = arr[l] + arr[r];
    if (s === target) return [l, r];
    if (s < target) l++;
    else r--;
  }
  return null;
}

console.log(twoSumSorted([1, 3, 5, 7, 9], 12)); // [1, 4] (3 + 9 = 12)
```

## 20.2 슬라이딩 윈도우

연속 부분 배열의 합이 target 이상인 가장 짧은 길이.

```ts
// src/pattern/minSubarrayLen.ts
export function minSubarrayLen(target: number, nums: number[]): number {
  let l = 0, sum = 0, best = Infinity;
  for (let r = 0; r < nums.length; r++) {
    sum += nums[r];
    while (sum >= target) {
      best = Math.min(best, r - l + 1);
      sum -= nums[l++];
    }
  }
  return best === Infinity ? 0 : best;
}

console.log(minSubarrayLen(7, [2, 3, 1, 2, 4, 3])); // 2
```

## 20.3 단조 스택 — 다음 큰 수

각 인덱스에서 오른쪽으로 처음 만나는 더 큰 수.

```ts
// src/pattern/nextGreater.ts
export function nextGreater(nums: number[]): number[] {
  const result = new Array<number>(nums.length).fill(-1);
  const stack: number[] = []; // index
  for (let i = 0; i < nums.length; i++) {
    while (stack.length > 0 && nums[stack[stack.length - 1]] < nums[i]) {
      result[stack.pop()!] = nums[i];
    }
    stack.push(i);
  }
  return result;
}

console.log(nextGreater([2, 1, 2, 4, 3])); // [4, 2, 4, -1, -1]
```

## 20.4 누적합 + 해시맵 — 합이 K인 부분배열 개수

```ts
// src/pattern/subarraySum.ts
export function subarraySum(nums: number[], k: number): number {
  const count = new Map<number, number>();
  count.set(0, 1);
  let sum = 0, total = 0;
  for (const n of nums) {
    sum += n;
    total += count.get(sum - k) ?? 0;
    count.set(sum, (count.get(sum) ?? 0) + 1);
  }
  return total;
}

console.log(subarraySum([1, 1, 1], 2)); // 2
```

## 20.5 BFS로 단어 사다리

`hit → hot → dot → dog → cog`

```ts
// src/pattern/wordLadder.ts
export function wordLadder(begin: string, end: string, list: string[]): number {
  const set = new Set(list);
  if (!set.has(end)) return 0;
  const queue: [string, number][] = [[begin, 1]];
  const visited = new Set<string>([begin]);
  while (queue.length > 0) {
    const [word, dist] = queue.shift()!;
    if (word === end) return dist;
    for (let i = 0; i < word.length; i++) {
      for (let c = 97; c <= 122; c++) {
        const next = word.slice(0, i) + String.fromCharCode(c) + word.slice(i + 1);
        if (set.has(next) && !visited.has(next)) {
          visited.add(next);
          queue.push([next, dist + 1]);
        }
      }
    }
  }
  return 0;
}

console.log(wordLadder("hit", "cog", ["hot","dot","dog","lot","log","cog"])); // 5
```

## 20.6 DP + 비트마스크 — 단어 깨기

문장을 사전 단어로 나눌 수 있는가?

```ts
// src/pattern/wordBreak.ts
export function wordBreak(s: string, wordDict: string[]): boolean {
  const set = new Set(wordDict);
  const dp = new Array(s.length + 1).fill(false);
  dp[0] = true;
  for (let i = 1; i <= s.length; i++) {
    for (let j = 0; j < i; j++) {
      if (dp[j] && set.has(s.slice(j, i))) { dp[i] = true; break; }
    }
  }
  return dp[s.length];
}

console.log(wordBreak("leetcode", ["leet", "code"])); // true
console.log(wordBreak("applepenapple", ["apple", "pen"])); // true
```

## 20.7 그리디 + 정렬 — 회의실 K개에서 최대 활동

끝나는 시간이 빠른 순으로 정렬한 뒤, 각 회의를 "가장 늦게 끝났으면서도 겹치지 않는 방"에 배정합니다(best-fit). 빈 방이 없으면 그 회의는 포기합니다.

```ts
// src/pattern/maxActivities.ts
type Meeting = { start: number; end: number };

/** 회의실이 rooms개일 때 진행할 수 있는 최대 회의 수 */
export function maxActivities(meetings: Meeting[], rooms: number): number {
  const sorted = meetings.slice().sort((a, b) => a.end - b.end);
  const roomEnds: number[] = []; // 사용 중인 각 방의 종료 시각 (오름차순 유지)
  let count = 0;
  for (const m of sorted) {
    // m.start 이전에 끝난 방 중 가장 늦게 끝난 방을 재사용 (best-fit)
    let idx = -1;
    for (let i = roomEnds.length - 1; i >= 0; i--) {
      if (roomEnds[i] <= m.start) { idx = i; break; }
    }
    if (idx >= 0) roomEnds.splice(idx, 1);        // 그 방을 재사용
    else if (roomEnds.length >= rooms) continue;  // 빈 방 없음 → 이 회의는 포기
    let pos = roomEnds.length;                    // 정렬 유지하며 종료 시각 삽입
    while (pos > 0 && roomEnds[pos - 1] > m.end) pos--;
    roomEnds.splice(pos, 0, m.end);
    count++;
  }
  return count;
}

console.log(maxActivities([
  { start: 1, end: 4 },
  { start: 2, end: 5 },
  { start: 3, end: 6 },
  { start: 5, end: 7 },
], 2)); // 3 — 방1: (1,4)→(5,7), 방2: (2,5). (3,6)은 포기
```

## 20.8 LRU 캐시 — 자료구조 합치기

자료구조 가이드북 14장과 동일하지만 단독 실행 가능 버전.

```ts
// src/pattern/LRU.ts
export class LRU<K, V> {
  private map = new Map<K, V>(); // Map은 삽입 순서 유지
  constructor(private cap: number) {}
  get(key: K): V | undefined {
    if (!this.map.has(key)) return undefined;
    const value = this.map.get(key)!;
    this.map.delete(key);
    this.map.set(key, value);
    return value;
  }
  put(key: K, value: V): void {
    if (this.map.has(key)) this.map.delete(key);
    else if (this.map.size >= this.cap) {
      const oldest = this.map.keys().next().value as K;
      this.map.delete(oldest);
    }
    this.map.set(key, value);
  }
}

const c = new LRU<string, number>(2);
c.put("a", 1); c.put("b", 2);
console.log(c.get("a")); // 1
c.put("c", 3);           // b 제거
console.log(c.get("b")); // undefined
```

JavaScript `Map`이 삽입 순서를 유지하기 때문에 이 트릭이 가능합니다.

## 20.9 백트래킹 + 가지치기 — Word Search II

여러 단어를 한 번의 DFS로 찾기. 트라이와 결합.

```ts
// src/pattern/wordSearchII.ts
class TrieNode {
  children = new Map<string, TrieNode>();
  word: string | null = null;
}

export function findWords(board: string[][], words: string[]): string[] {
  const root = new TrieNode();
  for (const w of words) {
    let cur = root;
    for (const ch of w) {
      let next = cur.children.get(ch);
      if (!next) { next = new TrieNode(); cur.children.set(ch, next); }
      cur = next;
    }
    cur.word = w;
  }

  const result = new Set<string>();
  const m = board.length, n = board[0].length;
  function dfs(r: number, c: number, node: TrieNode) {
    if (r < 0 || r >= m || c < 0 || c >= n) return;
    const ch = board[r][c];
    if (ch === "#") return;
    const next = node.children.get(ch);
    if (!next) return;
    if (next.word) { result.add(next.word); next.word = null; } // 중복 방지
    board[r][c] = "#";
    dfs(r + 1, c, next); dfs(r - 1, c, next);
    dfs(r, c + 1, next); dfs(r, c - 1, next);
    board[r][c] = ch;
  }
  for (let r = 0; r < m; r++) for (let c = 0; c < n; c++) dfs(r, c, root);
  return [...result];
}
```

## 20.10 마무리 — 알고리즘 학습 로드맵

이 책에서 다룬 카테고리:

1. 정렬 → 비교/비비교
2. 탐색 → 단조성을 이진 탐색
3. 분할정복 → 재귀
4. DP → 점화식 + 캐시
5. 그리디 → 증명 가능한 지역 최적
6. 그래프 → BFS/DFS + 가중치
7. 문자열 → 해시/실패 함수
8. 비트 → 작은 집합
9. 수학 → 모듈러
10. 기하 → 외적

다음 단계로 가고 싶다면:

- **고급 그래프**: 최대 유량(Ford-Fulkerson, Dinic), 이분 매칭(Hopcroft-Karp)
- **고급 문자열**: Aho-Corasick, 접미사 자동자(Suffix Automaton)
- **고급 DP**: 분할 DP, 트리 DP, Knuth 최적화, CHT(Convex Hull Trick)
- **계산 기하 심화**: 회전 캘리퍼스, 보로노이 다이어그램
- **고급 자료구조**: 스플레이 트리, Link-Cut 트리, Persistent 자료구조

그리고 마지막으로, **문제를 많이 풀어보세요**. 알고리즘은 이론을 안다고 끝나는 게 아닙니다. LeetCode, Codeforces, BOJ에서 한 주에 5~10문제씩 꾸준히 풀면, 6개월 후 다른 사람이 됩니다.

---

# 부록 A. 알고리즘 선택 치트시트

| 문제 유형 | 추천 알고리즘 |
|----------|---------------|
| 정렬 | 일반: `Array.sort` (TimSort) / 안정성 필요: 병합 |
| 정렬된 배열에서 검색 | 이진 탐색 |
| 단조성 갖는 답 찾기 | 답 자체를 이진 탐색 |
| 모든 부분집합 탐색 | 백트래킹 또는 비트마스크 (n ≤ 20) |
| 중복 부분 문제 | DP |
| 매 단계 최적 선택으로 충분 | 그리디 (증명 후) |
| 단일 출발 최단경로 | 다익스트라 / 음수면 벨만-포드 |
| 모든 쌍 최단경로 | 플로이드-워셜 |
| 연결 / 그룹화 | 유니온-파인드 |
| 우선순위 처리 | 우선순위 큐(힙) |
| 부분 문자열 검색 | KMP / 라빈-카프 |
| 자동완성, 사전 | 트라이 |
| 구간 쿼리 + 점 갱신 | 펜윅 / 세그먼트 트리 |
| 구간 갱신 + 구간 쿼리 | 지연 전파 세그먼트 트리 |

# 부록 B. 시간복잡도 한눈에

| 알고리즘 | 시간 | 공간 |
|----------|------|------|
| 버블/선택/삽입 정렬 | O(n²) | O(1) |
| 병합 정렬 | O(n log n) | O(n) |
| 퀵 정렬 | O(n log n) avg / O(n²) worst | O(log n) |
| 힙 정렬 | O(n log n) | O(1) |
| 계수 정렬 | O(n + k) | O(n + k) |
| 기수 정렬 | O(d(n + b)) | O(n + b) |
| 이진 탐색 | O(log n) | O(1) |
| BFS / DFS | O(V + E) | O(V) |
| 다익스트라 | O((V+E) log V) | O(V) |
| 벨만-포드 | O(VE) | O(V) |
| 플로이드-워셜 | O(V³) | O(V²) |
| 크루스칼 | O(E log E) | O(V) |
| 프림 | O(E log V) | O(V) |
| KMP | O(n + m) | O(m) |
| 라빈-카프 | O(n + m) avg | O(1) |
| Manacher | O(n) | O(n) |
| 펜윅 트리 | O(log n)/op | O(n) |
| 세그먼트 트리 | O(log n)/op | O(n) |

# 부록 C. tsconfig와 실행 환경

이 책의 모든 코드는 다음 환경에서 검증되었습니다.

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "node",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}
```

실행:

```bash
# 컴파일
npx tsc

# Node 18 이상에서 실행
node --experimental-specifier-resolution=node dist/index.js

# 또는 즉시 실행
npx tsx src/index.ts

# BigInt가 등장하는 17장 코드는 Node 10.4 이상 필요
```

이 책의 모든 자료구조(`MinHeap`, `Graph`, `DisjointSet` 등)는 [[TypeScript 자료구조 가이드북]]에서 그대로 가져온 것입니다. 두 책을 함께 묶어 자기만의 알고리즘 라이브러리로 만들어 두면, 다음 코딩 테스트나 사이드 프로젝트에서 곧장 가져다 쓸 수 있습니다.

좋은 알고리즘 여행 되시길.

---

## 🔗 관련 문서
- [[TypeScript 기초 가이드북]] — 문법 입문
- [[TypeScript 자료구조 가이드북]] — 이 책에서 사용하는 자료구조
- [[TypeScript]] — 인덱스
- [[Go 패턴]] · [[Lua 기초]] · [[Pandas 가이드북]] — 다른 언어 가이드
- [[프로그래밍 언어]]
