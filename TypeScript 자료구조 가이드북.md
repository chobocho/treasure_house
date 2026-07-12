# TypeScript 자료구조 가이드북
## 동작하는 코드로 배우는 자료구조: 배열부터 그래프, 트라이, 유니온-파인드까지

### 대상 독자
- TypeScript 기본 문법은 익혔지만 자료구조는 처음 공부하는 개발자
- JavaScript로 자료구조를 짜다가 타입 안전한 구현으로 옮겨가고 싶은 독자
- 코딩 테스트, 사이드 프로젝트, 게임 개발에서 즉시 가져다 쓸 수 있는 자료구조 코드를 원하는 독자
- "이 자료구조가 왜 필요한지"부터 차근차근 이해하고 싶은 독자

---

# 저자 서문

자료구조는 "데이터를 어떻게 담을 것인가"에 대한 답을 모아 놓은 도구 상자입니다.

같은 데이터라도 어떤 구조에 담느냐에 따라 검색은 1000배 빨라지고, 메모리는 절반으로 줄고, 코드는 두 배로 짧아질 수 있습니다. 반대로 잘못된 구조를 고르면 동작은 하지만 사용자 수가 늘어나는 순간 서비스가 멈춥니다.

자료구조 책은 많지만, 대부분은 다음 중 하나의 함정에 빠집니다.

1. C/C++ 위주 — 포인터/메모리 관리에 절반의 분량을 쓰고, 정작 우리가 매일 쓰는 언어와 거리가 있습니다.
2. 의사코드(pseudo code) 중심 — 책을 다 읽고도 "내 프로젝트에 어떻게 붙이지?"라는 질문이 남습니다.
3. JavaScript 예제 — 타입이 없어 코드 의도가 흐려지고, 큰 프로젝트에 그대로 붙이면 런타임 오류가 나기 쉽습니다.

이 책은 **TypeScript로 동작하는 코드**를 처음부터 끝까지 직접 구현하면서 자료구조를 배우는 책입니다. 모든 구현체는 다음 세 가지 원칙을 지킵니다.

1. **타입 안전** — 제네릭으로 어떤 타입이든 담을 수 있게
2. **즉시 실행 가능** — `tsc` 한 번으로 컴파일되고, `node` 또는 브라우저에서 그대로 동작
3. **시간복잡도 명시** — 각 연산이 왜 빠르고 왜 느린지 설명

이 책을 끝까지 따라오면, 여러분은 자료구조 14종의 내부 동작을 손으로 구현해 보고, 어떤 상황에 어떤 구조를 골라야 하는지 판단할 수 있게 됩니다. 그리고 무엇보다, 코딩 테스트나 실무 프로젝트에서 바로 가져다 쓸 수 있는 자료구조 코드 모음을 손에 쥐게 됩니다.

---

# 이 책의 구성

이 책은 총 **14장**으로 구성됩니다.

1. 자료구조와 시간복잡도
2. TypeScript 제네릭 복습
3. 배열과 동적 배열(Dynamic Array)
4. 연결 리스트(Linked List)
5. 이중 연결 리스트(Doubly Linked List)
6. 스택(Stack)
7. 큐(Queue)와 덱(Deque)
8. 해시 테이블(Hash Table)
9. 이진 트리와 순회
10. 이진 탐색 트리(BST)
11. 힙(Heap)과 우선순위 큐
12. 그래프(Graph)와 BFS / DFS
13. 트라이(Trie)와 유니온-파인드(Disjoint Set)
14. 종합 실습 — LRU 캐시, 다익스트라, 자동완성 엔진

각 장은 다음 구조를 따릅니다.

- 학습 목표
- 자료구조의 의미와 쓰임
- TypeScript 구현 (동작하는 전체 코드)
- 사용 예제 (`console.log`로 결과 확인)
- 시간복잡도 표
- 핵심 정리
- 연습문제

---

# 1장. 자료구조와 시간복잡도

## 학습 목표
- "자료구조"라는 단어가 가리키는 범위를 이해한다.
- Big-O 표기법으로 알고리즘 속도를 비교할 수 있다.
- 배열 / 연결 리스트 / 해시 테이블의 차이를 한 줄로 설명할 수 있다.

## 1.1 자료구조란

자료구조(Data Structure)는 **데이터를 메모리 위에 어떻게 배치하고, 어떤 연산을 어떤 비용으로 제공할지**를 정해 놓은 약속입니다.

같은 100만 개의 숫자라도

- 한 줄로 늘어놓으면(배열) → "n번째 값" 접근이 빠름
- 다음 칸을 가리키는 화살표로 잇으면(연결 리스트) → 중간 삽입이 빠름
- 해시 함수를 통과시켜 정해진 자리에 넣으면(해시 테이블) → "이 값이 들어 있나?" 검사가 빠름

연산마다 잘하는 구조와 못하는 구조가 다르고, 우리는 상황에 맞는 구조를 골라야 합니다.

## 1.2 Big-O 표기법

알고리즘이 데이터 개수 n에 대해 얼마나 느려지는지 표시합니다.

| 표기 | 이름 | 예시 |
|------|------|------|
| O(1) | 상수 | 배열의 i번째 접근 |
| O(log n) | 로그 | 정렬된 배열의 이진 탐색 |
| O(n) | 선형 | 배열 전체 순회 |
| O(n log n) | 선형 로그 | 효율적 정렬(병합/퀵) |
| O(n²) | 이차 | 이중 반복문 |
| O(2ⁿ) | 지수 | 부분집합 전부 만들기 |

n이 100만일 때 대략적인 연산 횟수는 다음과 같습니다.

- O(log n) ≈ 20
- O(n) ≈ 1,000,000
- O(n log n) ≈ 20,000,000
- O(n²) ≈ 1,000,000,000,000 ← 사실상 불가능

## 1.3 측정 도구를 만들어 보자

이론도 좋지만 직접 시간을 재 봅시다. 이 책 전체에서 쓸 작은 유틸리티입니다.

```ts
// src/util/measure.ts
export function measure<T>(label: string, fn: () => T): T {
  const start = performance.now();
  const result = fn();
  const elapsed = performance.now() - start;
  console.log(`[${label}] ${elapsed.toFixed(3)} ms`);
  return result;
}

export function buildArray(n: number): number[] {
  const arr = new Array<number>(n);
  for (let i = 0; i < n; i++) arr[i] = i;
  return arr;
}
```

사용 예시:

```ts
import { measure, buildArray } from "./util/measure";

const arr = buildArray(1_000_000);

measure("index access", () => arr[500_000]);     // O(1)
measure("includes", () => arr.includes(999_999)); // O(n)
```

## 핵심 정리
- 자료구조는 **연산별 비용 표**다. 연산을 무엇을 자주 할지 먼저 정한 뒤 구조를 고른다.
- Big-O는 데이터가 커질 때의 **증가 추세**를 본다. 작은 n에서는 상수가 더 중요할 수도 있다.
- 측정은 거짓말하지 않는다. 의심스러우면 직접 시간을 재 본다.

## 연습문제
1. O(n)과 O(n log n)이 n=10에서는 차이가 얼마나 되는가? n=10⁶에서는?
2. 위 `measure` 함수를 이용해 길이 100만 배열의 `includes`와 `indexOf` 속도를 비교해 보라.

---

# 2장. TypeScript 제네릭 복습

## 학습 목표
- 자료구조 구현에 꼭 필요한 제네릭 문법만 빠르게 정리한다.
- `T`, `K extends string`, `Comparator<T>` 같은 패턴을 읽을 수 있다.

## 2.1 왜 제네릭이 필요한가

자료구조는 "어떤 타입이 들어와도" 동작해야 합니다. `Stack`이 `number`만 받는다면 쓸모가 절반입니다.

```ts
// 좋지 않은 예 — 타입을 잃어버림
class AnyStack {
  private items: any[] = [];
  push(item: any): void { this.items.push(item); }
  pop(): any { return this.items.pop(); }
}

// 제네릭으로 타입 보존
class Stack<T> {
  private items: T[] = [];
  push(item: T): void { this.items.push(item); }
  pop(): T | undefined { return this.items.pop(); }
}

const s = new Stack<number>();
s.push(1);
// s.push("hello"); // ← 컴파일 에러: 정확히 우리가 원하던 안전망
```

## 2.2 자주 쓰는 제네릭 패턴

### 비교 함수 타입

정렬, 힙, 트리에서 반복적으로 쓰입니다.

```ts
export type Comparator<T> = (a: T, b: T) => number;

// 양수: a가 뒤로 / 음수: a가 앞으로 / 0: 같음
export const numAsc: Comparator<number> = (a, b) => a - b;
export const numDesc: Comparator<number> = (a, b) => b - a;
```

### 키 제약

```ts
function pluck<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { id: 1, name: "Lee" };
const name = pluck(user, "name"); // string으로 추론
```

### 옵션 객체

```ts
interface MapOptions<K> {
  capacity?: number;
  hash?: (key: K) => number;
}
```

이 정도면 책을 끝까지 따라오는 데 부족함이 없습니다. 모르는 문법이 나오면 그때그때 짧게 짚겠습니다.

## 핵심 정리
- 자료구조는 **제네릭 클래스**로 만든다. 타입을 잃지 말라.
- 정렬 가능한 자료구조는 **`Comparator<T>` 주입**으로 다양한 정렬 기준을 지원한다.

---

# 3장. 배열과 동적 배열

## 학습 목표
- JavaScript 배열의 내부 동작과 한계를 이해한다.
- 동적 배열(Dynamic Array)을 처음부터 직접 구현해 본다.
- amortized O(1) 개념을 이해한다.

## 3.1 JavaScript 배열의 정체

JavaScript의 `Array`는 스펙상으로는 **키-값 객체**입니다. 다행히 실제 엔진(V8 등)은 빈틈 없이 채워진 배열을 연속 메모리로 최적화하지만, 아래처럼 구멍(hole)을 만들면 이 최적화가 약해지고 빈 슬롯도 메모리를 차지하게 됩니다.

```ts
const a: number[] = [];
a[1000] = 1;
console.log(a.length); // 1001 — 1000개의 빈 슬롯이 생김
```

성능을 정말 따져야 한다면 `Int32Array` 같은 **타입드 배열(TypedArray)** 을 씁니다. 일반 객체 배열은 다음에 만들 동적 배열의 기반으로 이미 충분히 빠릅니다.

## 3.2 동적 배열을 직접 만들기

직접 구현해야 동작 원리가 머리에 남습니다. 고정 크기 버퍼로 시작해서, 가득 차면 두 배로 늘립니다.

```ts
// src/ds/DynamicArray.ts
export class DynamicArray<T> {
  private buffer: (T | undefined)[];
  private size = 0;

  constructor(capacity = 4) {
    this.buffer = new Array<T | undefined>(capacity);
  }

  get length(): number { return this.size; }
  get capacity(): number { return this.buffer.length; }

  get(index: number): T {
    if (index < 0 || index >= this.size) throw new RangeError(`index ${index}`);
    return this.buffer[index] as T;
  }

  set(index: number, value: T): void {
    if (index < 0 || index >= this.size) throw new RangeError(`index ${index}`);
    this.buffer[index] = value;
  }

  push(value: T): void {
    if (this.size === this.buffer.length) this.grow();
    this.buffer[this.size++] = value;
  }

  pop(): T | undefined {
    if (this.size === 0) return undefined;
    const value = this.buffer[--this.size];
    this.buffer[this.size] = undefined; // 참조 해제
    return value;
  }

  insert(index: number, value: T): void {
    if (index < 0 || index > this.size) throw new RangeError(`index ${index}`);
    if (this.size === this.buffer.length) this.grow();
    for (let i = this.size; i > index; i--) {
      this.buffer[i] = this.buffer[i - 1];
    }
    this.buffer[index] = value;
    this.size++;
  }

  remove(index: number): T {
    if (index < 0 || index >= this.size) throw new RangeError(`index ${index}`);
    const value = this.buffer[index] as T;
    for (let i = index; i < this.size - 1; i++) {
      this.buffer[i] = this.buffer[i + 1];
    }
    this.size--;
    this.buffer[this.size] = undefined;
    return value;
  }

  private grow(): void {
    const next = new Array<T | undefined>(this.buffer.length * 2);
    for (let i = 0; i < this.size; i++) next[i] = this.buffer[i];
    this.buffer = next;
  }

  *[Symbol.iterator](): IterableIterator<T> {
    for (let i = 0; i < this.size; i++) yield this.buffer[i] as T;
  }

  toArray(): T[] { return [...this]; }
}
```

## 3.3 동작 확인

```ts
import { DynamicArray } from "./ds/DynamicArray";

const arr = new DynamicArray<string>(2);
arr.push("a");
arr.push("b");
arr.push("c"); // 여기서 자동으로 capacity가 4로 grow
arr.insert(1, "X");
console.log(arr.toArray()); // ["a", "X", "b", "c"]
console.log(arr.remove(0)); // "a"
console.log(arr.toArray()); // ["X", "b", "c"]
console.log(arr.length, arr.capacity); // 3 4
```

## 3.4 amortized O(1)이란

`push`는 가끔 `grow`를 부르고, `grow`는 O(n)입니다. 그런데 두 배씩 늘리면 평균적으로는 한 번의 `push`당 비용이 상수입니다.

직관: n번 push할 때 grow는 log₂n번만 일어나고, 매 grow의 비용은 마지막 grow가 가장 큰 등비급수로 합산되어 총 O(n)입니다. 따라서 **push 한 번당 평균 O(1)**.

## 시간복잡도

| 연산 | 평균 | 최악 |
|------|------|------|
| `get`/`set` | O(1) | O(1) |
| `push`/`pop` | amortized O(1) | O(n) (grow 시점) |
| `insert`/`remove` (중간) | O(n) | O(n) |

## 핵심 정리
- 배열은 "인덱스 접근"이 가장 빠른 자료구조다.
- 동적 배열은 **2배 grow** 전략으로 push 비용을 평균 상수로 만든다.
- 중간 삽입/삭제가 잦다면 다음 장의 연결 리스트를 보라.

## 연습문제
1. `grow`에서 2배가 아니라 1.5배를 쓰면 어떤 트레이드오프가 생기는가?
2. `pop` 후 capacity가 size의 4배 이상이면 절반으로 shrink하도록 개선해 보라.

---

# 4장. 연결 리스트

## 학습 목표
- 노드 + 포인터로 데이터를 잇는다는 개념을 이해한다.
- 단일 연결 리스트(Singly Linked List)를 직접 구현한다.
- 배열과의 트레이드오프를 설명할 수 있다.

## 4.1 왜 연결 리스트인가

배열은 중간 삽입/삭제가 비쌉니다. 길이 100만짜리 배열의 0번 인덱스에 값을 넣으면 99만 9999개를 한 칸씩 밀어야 합니다.

연결 리스트는 각 노드가 다음 노드를 **포인터로 가리킵니다**. 중간 삽입은 화살표 두 개만 바꾸면 끝나기 때문에 O(1)입니다(단, 그 위치를 찾는 데 O(n)이 듭니다).

```
[a] → [b] → [c] → null
```

## 4.2 단일 연결 리스트 구현

```ts
// src/ds/LinkedList.ts
class ListNode<T> {
  constructor(public value: T, public next: ListNode<T> | null = null) {}
}

export class LinkedList<T> {
  private head: ListNode<T> | null = null;
  private tail: ListNode<T> | null = null;
  private size = 0;

  get length(): number { return this.size; }
  isEmpty(): boolean { return this.size === 0; }

  /** 끝에 추가 — O(1) */
  pushBack(value: T): void {
    const node = new ListNode(value);
    if (!this.tail) {
      this.head = this.tail = node;
    } else {
      this.tail.next = node;
      this.tail = node;
    }
    this.size++;
  }

  /** 앞에 추가 — O(1) */
  pushFront(value: T): void {
    this.head = new ListNode(value, this.head);
    if (!this.tail) this.tail = this.head;
    this.size++;
  }

  /** 앞에서 제거 — O(1) */
  popFront(): T | undefined {
    if (!this.head) return undefined;
    const value = this.head.value;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.size--;
    return value;
  }

  /** index로 접근 — O(n) */
  at(index: number): T {
    if (index < 0 || index >= this.size) throw new RangeError(`index ${index}`);
    let cur = this.head!;
    for (let i = 0; i < index; i++) cur = cur.next!;
    return cur.value;
  }

  /** 첫 일치 노드 제거 — O(n) */
  remove(predicate: (value: T) => boolean): boolean {
    let prev: ListNode<T> | null = null;
    let cur = this.head;
    while (cur) {
      if (predicate(cur.value)) {
        if (prev) prev.next = cur.next;
        else this.head = cur.next;
        if (cur === this.tail) this.tail = prev;
        this.size--;
        return true;
      }
      prev = cur;
      cur = cur.next;
    }
    return false;
  }

  /** 리스트 뒤집기 — O(n), 추가 메모리 O(1) */
  reverse(): void {
    let prev: ListNode<T> | null = null;
    let cur = this.head;
    this.tail = this.head;
    while (cur) {
      const next = cur.next;
      cur.next = prev;
      prev = cur;
      cur = next;
    }
    this.head = prev;
  }

  *[Symbol.iterator](): IterableIterator<T> {
    let cur = this.head;
    while (cur) {
      yield cur.value;
      cur = cur.next;
    }
  }

  toArray(): T[] { return [...this]; }
}
```

## 4.3 동작 확인

```ts
import { LinkedList } from "./ds/LinkedList";

const list = new LinkedList<number>();
list.pushBack(1);
list.pushBack(2);
list.pushBack(3);
list.pushFront(0);
console.log(list.toArray()); // [0, 1, 2, 3]

list.remove(v => v === 2);
console.log(list.toArray()); // [0, 1, 3]

list.reverse();
console.log(list.toArray()); // [3, 1, 0]

console.log(list.at(0)); // 3
```

## 4.4 배열 vs 연결 리스트

| 연산 | 동적 배열 | 연결 리스트 |
|------|-----------|-------------|
| 인덱스 접근 | O(1) | O(n) |
| 끝 추가 | amortized O(1) | O(1) |
| 앞 추가 | O(n) | O(1) |
| 중간 삽입(위치 알 때) | O(n) | O(1) |
| 메모리 | 연속, 캐시 친화적 | 흩어짐, 포인터 오버헤드 |

실무 팁: 90%의 경우 **그냥 배열을 써도 됩니다**. JS 엔진의 메모리 캐시 효과가 강력해서 실제 측정해 보면 배열의 중간 삽입이 더 빠른 경우도 흔합니다. 연결 리스트는 다음 장의 LRU 캐시처럼 "양 끝에서 빠른 삽입/삭제가 모두 필요할 때" 빛납니다.

## 핵심 정리
- 연결 리스트는 **노드 + next 포인터**로 잇는 구조다.
- 양 끝 연산이 O(1), 인덱스 접근은 O(n).
- 화살표만 바꾸므로 중간 삽입/삭제 비용은 노드를 찾는 비용과 같다.

## 연습문제
1. 두 정렬된 연결 리스트를 합쳐 정렬된 하나의 리스트로 만드는 함수 `merge(a, b)`를 구현하라.
2. 사이클이 있는지 검사하는 `hasCycle()`을 두 포인터(거북이/토끼) 기법으로 구현하라.

---

# 5장. 이중 연결 리스트

## 학습 목표
- 양방향 포인터의 효과를 이해한다.
- 이중 연결 리스트(DLL)를 직접 구현한다.
- 다음 장의 덱(Deque)과 12장의 LRU 캐시 기반을 만든다.

## 5.1 왜 prev가 필요한가

단일 연결 리스트는 **뒤로 갈 수 없습니다**. 끝 노드를 알아도 그 앞 노드를 모르니, 끝에서 제거할 때 다시 처음부터 훑어야 합니다.

이중 연결 리스트는 각 노드가 `prev`와 `next` 둘 다 가집니다.

```
null ← [a] ⇄ [b] ⇄ [c] → null
```

이러면 양 끝 모두에서 O(1) 삭제가 가능합니다.

## 5.2 더미 헤드/테일 트릭

구현이 까다로운 이유는 "head가 null일 때", "tail이 null일 때" 같은 경계 조건입니다. **더미(sentinel) 노드** 두 개를 양 끝에 두면 모든 실제 노드는 항상 prev와 next를 가지게 되어 코드가 깔끔해집니다.

```ts
// src/ds/DoublyLinkedList.ts
class DLLNode<T> {
  prev: DLLNode<T> | null = null;
  next: DLLNode<T> | null = null;
  constructor(public value: T | null) {}
}

export class DoublyLinkedList<T> {
  private head = new DLLNode<T>(null); // sentinel
  private tail = new DLLNode<T>(null); // sentinel
  private size = 0;

  constructor() {
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  get length(): number { return this.size; }

  /** node를 ref 앞에 넣음 */
  private insertBefore(ref: DLLNode<T>, node: DLLNode<T>): void {
    node.prev = ref.prev;
    node.next = ref;
    ref.prev!.next = node;
    ref.prev = node;
    this.size++;
  }

  /** 임의의 노드를 떼어냄 */
  private detach(node: DLLNode<T>): void {
    node.prev!.next = node.next;
    node.next!.prev = node.prev;
    node.prev = node.next = null;
    this.size--;
  }

  pushBack(value: T): DLLNode<T> {
    const node = new DLLNode(value);
    this.insertBefore(this.tail, node);
    return node; // 반환값을 LRU 캐시에서 활용
  }

  pushFront(value: T): DLLNode<T> {
    const node = new DLLNode(value);
    this.insertBefore(this.head.next!, node);
    return node;
  }

  popBack(): T | undefined {
    if (this.size === 0) return undefined;
    const node = this.tail.prev!;
    this.detach(node);
    return node.value!;
  }

  popFront(): T | undefined {
    if (this.size === 0) return undefined;
    const node = this.head.next!;
    this.detach(node);
    return node.value!;
  }

  /** O(1)로 임의 노드 제거 — 외부에서 노드 참조를 들고 있을 때 */
  removeNode(node: DLLNode<T>): T {
    const value = node.value!;
    this.detach(node);
    return value;
  }

  /** 노드를 맨 앞으로 옮김 — LRU 캐시에서 핵심 */
  moveToFront(node: DLLNode<T>): void {
    this.detach(node);
    this.insertBefore(this.head.next!, node);
  }

  *[Symbol.iterator](): IterableIterator<T> {
    let cur = this.head.next!;
    while (cur !== this.tail) {
      yield cur.value!;
      cur = cur.next!;
    }
  }

  toArray(): T[] { return [...this]; }
}
```

## 5.3 동작 확인

```ts
import { DoublyLinkedList } from "./ds/DoublyLinkedList";

const dll = new DoublyLinkedList<string>();
const a = dll.pushBack("a");
dll.pushBack("b");
const c = dll.pushBack("c");
console.log(dll.toArray()); // ["a", "b", "c"]

dll.moveToFront(c);
console.log(dll.toArray()); // ["c", "a", "b"]

dll.removeNode(a);
console.log(dll.toArray()); // ["c", "b"]

console.log(dll.popBack(), dll.popFront()); // b c
console.log(dll.length); // 0
```

## 핵심 정리
- 이중 연결 리스트는 양 끝 + 임의 노드 제거가 모두 O(1).
- **더미 헤드/테일**을 두면 경계 조건이 사라진다.
- 외부에서 노드 참조를 들고 있으면 O(1) 이동이 가능해 LRU 캐시의 핵심이 된다.

## 연습문제
1. `moveToBack(node)`를 추가하라.
2. 인덱스 i의 노드를 반환하는 `nodeAt(i)`를 구현하되, 길이의 절반보다 크면 tail부터 거슬러 올라가도록 최적화하라.

---

# 6장. 스택

## 학습 목표
- LIFO(Last In First Out) 개념을 이해한다.
- 배열 기반과 연결 리스트 기반 스택을 모두 만들 수 있다.
- 괄호 검사, 식 계산 같은 고전 응용을 직접 푼다.

## 6.1 스택의 의미

가장 늦게 들어온 것이 가장 먼저 나옵니다. 책을 쌓는 것과 같습니다.

응용:
- 함수 호출 스택(콜 스택)
- undo / redo
- 깊이 우선 탐색(DFS)
- 괄호/태그 매칭
- 후위표기식 계산

## 6.2 구현

배열 기반이 가장 단순합니다.

```ts
// src/ds/Stack.ts
export class Stack<T> {
  private items: T[] = [];

  push(value: T): void { this.items.push(value); }
  pop(): T | undefined { return this.items.pop(); }
  peek(): T | undefined { return this.items[this.items.length - 1]; }
  get size(): number { return this.items.length; }
  isEmpty(): boolean { return this.items.length === 0; }

  toArray(): T[] { return [...this.items]; }
}
```

모든 연산이 amortized O(1).

## 6.3 응용 1 — 괄호 검사

```ts
// src/app/balanced.ts
import { Stack } from "../ds/Stack";

const PAIRS: Record<string, string> = { ")": "(", "]": "[", "}": "{" };

export function isBalanced(input: string): boolean {
  const stack = new Stack<string>();
  for (const ch of input) {
    if (ch === "(" || ch === "[" || ch === "{") {
      stack.push(ch);
    } else if (ch in PAIRS) {
      if (stack.pop() !== PAIRS[ch]) return false;
    }
  }
  return stack.isEmpty();
}

console.log(isBalanced("({[a+b]*c})")); // true
console.log(isBalanced("({[a+b]*c)"));  // false
console.log(isBalanced(""));            // true
```

## 6.4 응용 2 — 후위표기식(Reverse Polish) 계산

후위표기식은 `3 4 + 2 *`처럼 연산자가 뒤에 오는 식입니다. 스택만으로 계산할 수 있습니다.

```ts
// src/app/rpn.ts
import { Stack } from "../ds/Stack";

type Op = "+" | "-" | "*" | "/";
const OPS: Record<Op, (a: number, b: number) => number> = {
  "+": (a, b) => a + b,
  "-": (a, b) => a - b,
  "*": (a, b) => a * b,
  "/": (a, b) => a / b,
};

function isOp(token: string): token is Op { return token in OPS; }

export function evalRpn(expr: string): number {
  const stack = new Stack<number>();
  for (const token of expr.split(/\s+/).filter(Boolean)) {
    if (isOp(token)) {
      const b = stack.pop()!;
      const a = stack.pop()!;
      stack.push(OPS[token](a, b));
    } else {
      stack.push(Number(token));
    }
  }
  return stack.pop()!;
}

console.log(evalRpn("3 4 + 2 *"));     // 14
console.log(evalRpn("5 1 2 + 4 * + 3 -")); // 14
```

## 핵심 정리
- 스택은 **꼭대기에서만** 일하는 구조. 그래서 단순하고 빠르다.
- 배열의 `push`/`pop`이 이미 스택이다. 굳이 클래스로 감싸는 이유는 **불변 인터페이스 강제** 와 가독성.

## 연습문제
1. `min()` 메서드가 O(1)인 스택을 만들어라(보조 스택을 함께 운영).
2. 중위표기식 → 후위표기식 변환기를 구현하라(샨팅 야드 알고리즘).

---

# 7장. 큐와 덱

## 학습 목표
- FIFO(First In First Out)와 양방향 큐(Deque)를 이해한다.
- 단순 큐 / 원형 큐(Circular Queue) / 덱을 모두 직접 구현한다.
- BFS, 작업 스케줄링에 어떻게 쓰이는지 본다.

## 7.1 가장 단순한 큐 (그리고 함정)

```ts
class NaiveQueue<T> {
  private items: T[] = [];
  enqueue(v: T) { this.items.push(v); }
  dequeue(): T | undefined { return this.items.shift(); }
}
```

이 코드는 동작하지만 느립니다. `Array.shift()`는 모든 원소를 한 칸씩 당기므로 **O(n)** 입니다. 큐가 커지면 치명적입니다.

## 7.2 원형 큐

고정 크기 버퍼에서 head/tail 인덱스를 회전시켜 양 끝 연산을 O(1)로 만듭니다.

```ts
// src/ds/CircularQueue.ts
export class CircularQueue<T> {
  private buffer: (T | undefined)[];
  private head = 0;
  private tail = 0;
  private size = 0;

  constructor(capacity: number) {
    if (capacity <= 0) throw new RangeError("capacity must be > 0");
    this.buffer = new Array<T | undefined>(capacity);
  }

  get length(): number { return this.size; }
  get capacity(): number { return this.buffer.length; }
  isFull(): boolean { return this.size === this.buffer.length; }
  isEmpty(): boolean { return this.size === 0; }

  enqueue(value: T): void {
    if (this.isFull()) this.grow();
    this.buffer[this.tail] = value;
    this.tail = (this.tail + 1) % this.buffer.length;
    this.size++;
  }

  dequeue(): T | undefined {
    if (this.isEmpty()) return undefined;
    const value = this.buffer[this.head] as T;
    this.buffer[this.head] = undefined;
    this.head = (this.head + 1) % this.buffer.length;
    this.size--;
    return value;
  }

  peek(): T | undefined {
    return this.isEmpty() ? undefined : (this.buffer[this.head] as T);
  }

  private grow(): void {
    const next = new Array<T | undefined>(this.buffer.length * 2);
    for (let i = 0; i < this.size; i++) {
      next[i] = this.buffer[(this.head + i) % this.buffer.length];
    }
    this.buffer = next;
    this.head = 0;
    this.tail = this.size;
  }

  *[Symbol.iterator](): IterableIterator<T> {
    for (let i = 0; i < this.size; i++) {
      yield this.buffer[(this.head + i) % this.buffer.length] as T;
    }
  }

  toArray(): T[] { return [...this]; }
}
```

```ts
import { CircularQueue } from "./ds/CircularQueue";

const q = new CircularQueue<number>(3);
q.enqueue(1);
q.enqueue(2);
q.enqueue(3);
console.log(q.dequeue()); // 1
q.enqueue(4);
q.enqueue(5); // grow
console.log(q.toArray()); // [2, 3, 4, 5]
```

## 7.3 덱(Deque)

양 끝 모두에서 enqueue/dequeue가 가능한 큐. 5장의 이중 연결 리스트가 그대로 덱입니다. 인덱스 기반이 필요하다면 원형 큐를 양방향으로 확장해도 됩니다.

```ts
// src/ds/Deque.ts
import { DoublyLinkedList } from "./DoublyLinkedList";

export class Deque<T> {
  private list = new DoublyLinkedList<T>();

  pushFront(v: T) { this.list.pushFront(v); }
  pushBack(v: T) { this.list.pushBack(v); }
  popFront(): T | undefined { return this.list.popFront(); }
  popBack(): T | undefined { return this.list.popBack(); }

  get length(): number { return this.list.length; }
  toArray(): T[] { return this.list.toArray(); }
}
```

## 7.4 큐의 응용 — 슬라이딩 윈도우 최댓값

길이 n 배열에서 크기 k 윈도우의 최댓값들을 O(n)에 구합니다. 덱에 **인덱스**를 담고, 새 원소가 들어올 때 더 작은 인덱스를 뒤에서 빼는 단조 덱 기법입니다.

```ts
// src/app/slidingMax.ts
import { Deque } from "../ds/Deque";

export function slidingMax(nums: number[], k: number): number[] {
  const dq = new Deque<number>();
  const result: number[] = [];
  for (let i = 0; i < nums.length; i++) {
    // 윈도우 밖이면 앞에서 제거
    while (dq.length > 0 && dq.toArray()[0] <= i - k) dq.popFront();
    // 끝에서 더 작은 값들 제거
    while (dq.length > 0 && nums[dq.toArray().slice(-1)[0]] < nums[i]) dq.popBack();
    dq.pushBack(i);
    if (i >= k - 1) result.push(nums[dq.toArray()[0]]);
  }
  return result;
}

console.log(slidingMax([1, 3, -1, -3, 5, 3, 6, 7], 3));
// [3, 3, 5, 5, 6, 7]
```

> 위 구현은 가독성을 위해 `toArray()`를 호출했지만 매번 O(n)이라 큰 입력에서 느려집니다. 실무에서는 인덱스를 직접 다루는 원형 덱을 따로 만드는 편이 좋습니다.

## 핵심 정리
- `Array.shift()`는 O(n)이다. 큐가 필요하면 **원형 큐 또는 이중 연결 리스트**를 써라.
- BFS, 작업 큐, 메시지 큐 등 "들어온 순서대로 처리"가 등장하면 큐를 떠올려라.

## 연습문제
1. 원형 큐에 `pushFront`, `popBack`을 추가해 인덱스 기반 덱으로 확장하라.
2. 두 스택으로 큐를 구현하라.

---

# 8장. 해시 테이블

## 학습 목표
- 해시 함수와 충돌(collision)을 이해한다.
- 체이닝(chaining) 방식 해시 테이블을 직접 만든다.
- JavaScript의 `Map`/`Object`와 비교한다.

## 8.1 핵심 아이디어

키를 정수로 변환(해시)해서 배열의 인덱스로 쓰면, 평균 O(1)에 접근할 수 있습니다.

```
key "name" → hash 7382 → 7382 % 16 = 6 → buffer[6]
```

문제는 **두 키가 같은 자리에 떨어지는 충돌**입니다. 가장 단순한 해결책은 각 칸을 **버킷(작은 리스트)** 으로 만드는 체이닝입니다.

## 8.2 직접 만들기

```ts
// src/ds/HashMap.ts
type Entry<K, V> = { key: K; value: V };

export class HashMap<K, V> {
  private buckets: Entry<K, V>[][];
  private size = 0;
  private readonly LOAD_FACTOR = 0.75;

  constructor(initialCapacity = 16) {
    this.buckets = Array.from({ length: initialCapacity }, () => []);
  }

  get length(): number { return this.size; }

  set(key: K, value: V): void {
    const i = this.indexOf(key);
    const bucket = this.buckets[i];
    const entry = bucket.find(e => this.equal(e.key, key));
    if (entry) {
      entry.value = value;
      return;
    }
    bucket.push({ key, value });
    this.size++;
    if (this.size > this.buckets.length * this.LOAD_FACTOR) this.rehash();
  }

  get(key: K): V | undefined {
    const i = this.indexOf(key);
    const entry = this.buckets[i].find(e => this.equal(e.key, key));
    return entry?.value;
  }

  has(key: K): boolean {
    const i = this.indexOf(key);
    return this.buckets[i].some(e => this.equal(e.key, key));
  }

  delete(key: K): boolean {
    const i = this.indexOf(key);
    const bucket = this.buckets[i];
    const idx = bucket.findIndex(e => this.equal(e.key, key));
    if (idx === -1) return false;
    bucket.splice(idx, 1);
    this.size--;
    return true;
  }

  *entries(): IterableIterator<[K, V]> {
    for (const bucket of this.buckets) {
      for (const e of bucket) yield [e.key, e.value];
    }
  }

  private indexOf(key: K): number {
    return Math.abs(this.hash(key)) % this.buckets.length;
  }

  /** 단순 문자열 해시 (djb2). 객체 키는 JSON으로 직렬화. */
  private hash(key: K): number {
    const s = typeof key === "string" ? key : JSON.stringify(key);
    let h = 5381;
    for (let i = 0; i < s.length; i++) h = ((h << 5) + h) ^ s.charCodeAt(i);
    return h | 0;
  }

  private equal(a: K, b: K): boolean {
    if (a === b) return true;
    return JSON.stringify(a) === JSON.stringify(b);
  }

  private rehash(): void {
    const oldBuckets = this.buckets;
    this.buckets = Array.from({ length: oldBuckets.length * 2 }, () => []);
    this.size = 0;
    for (const bucket of oldBuckets) {
      for (const e of bucket) this.set(e.key, e.value);
    }
  }
}
```

## 8.3 동작 확인

```ts
import { HashMap } from "./ds/HashMap";

const m = new HashMap<string, number>();
m.set("apple", 1);
m.set("banana", 2);
m.set("apple", 10); // 덮어쓰기
console.log(m.get("apple"));  // 10
console.log(m.has("grape"));  // false
console.log(m.length);        // 2

for (const [k, v] of m.entries()) console.log(k, v);
m.delete("banana");
console.log(m.length); // 1
```

## 8.4 부하율(Load Factor)과 리해시

엔트리 수 / 버킷 수를 부하율이라 하고, 이게 0.75를 넘으면 충돌이 잦아져 O(1)이 무너집니다. 그래서 **버킷을 두 배로 키우고 모든 키를 다시 분배(rehash)** 합니다. rehash 자체는 O(n)이지만, 동적 배열의 grow와 같은 논리로 amortized O(1)입니다.

## 8.5 JavaScript의 Map vs Object

- `Object`는 키가 항상 문자열/심볼로 변환됩니다. `obj[1]`과 `obj["1"]`이 같습니다.
- `Map`은 임의의 객체를 키로 쓸 수 있고, 삽입 순서가 보존됩니다. 자료구조 의도가 명확하다면 `Map`을 권장합니다.

성능 측정 한 번 해 봅시다.

```ts
import { measure } from "./util/measure";

const N = 100_000;
const map = new Map<number, number>();
const obj: Record<string, number> = {};

measure("Map set", () => {
  for (let i = 0; i < N; i++) map.set(i, i);
});
measure("Object set", () => {
  for (let i = 0; i < N; i++) obj[i] = i;
});
```

정수 키를 쓰는 이 벤치마크에서는 대부분의 엔진에서 오히려 `Object` 쪽이 몇 배 빠릅니다. 엔진이 정수 키를 배열처럼 최적화하기 때문입니다. 문자열 키에서는 둘이 엎치락뒤치락하고, 키 추가/삭제가 잦은 워크로드에서는 `Map`이 유리해지는 경우가 많습니다. 요컨대 `Map`을 고르는 기준은 미세 성능이 아니라 **의도의 명확함**입니다.

## 시간복잡도

| 연산 | 평균 | 최악 |
|------|------|------|
| `set`/`get`/`has`/`delete` | O(1) | O(n) (모두 한 버킷에 몰림) |
| 순회 | O(n + 버킷수) | 같음 |

## 핵심 정리
- 해시 테이블의 평균 O(1)은 **좋은 해시 함수 + 적절한 부하율** 두 조건이 함께 충족될 때.
- 체이닝 외에 오픈 어드레싱(linear probing)도 있으나 구현이 까다롭다.
- 키가 문자열이고 단순한 캐시라면 그냥 `Map`을 써라.

## 연습문제
1. 위 `HashMap`에서 `delete` 후 size가 capacity의 1/4 미만이면 절반으로 shrink하도록 수정하라.
2. 객체 키 비교를 `JSON.stringify` 대신 **참조 동등성**(`===`)으로 바꾸면 어떤 차이가 생기는가?

---

# 9장. 이진 트리와 순회

## 학습 목표
- 트리/이진 트리/노드/높이 같은 용어를 정확히 안다.
- 전위(preorder)/중위(inorder)/후위(postorder)/레벨(BFS) 순회를 모두 구현한다.

## 9.1 용어 정리

- **트리(Tree)**: 사이클 없는 연결 그래프. 한 노드를 루트로 정해 방향을 부여.
- **이진 트리(Binary Tree)**: 자식이 최대 두 개.
- **잎(Leaf)**: 자식이 없는 노드.
- **높이(height)**: 루트에서 가장 먼 잎까지의 간선 수.

```
        1
       / \
      2   3
     / \   \
    4   5   6
```

이 트리의 높이는 2.

## 9.2 노드 정의와 빌드

```ts
// src/ds/BinaryTree.ts
export class TreeNode<T> {
  constructor(
    public value: T,
    public left: TreeNode<T> | null = null,
    public right: TreeNode<T> | null = null,
  ) {}
}

/** 배열로 표현된 레벨 순서를 트리로 변환 — null은 빈 자리 */
export function buildTree<T>(values: (T | null)[]): TreeNode<T> | null {
  if (values.length === 0 || values[0] === null) return null;
  const root = new TreeNode<T>(values[0] as T);
  const queue: TreeNode<T>[] = [root];
  let i = 1;
  while (queue.length > 0 && i < values.length) {
    const node = queue.shift()!;
    if (i < values.length && values[i] !== null) {
      node.left = new TreeNode(values[i] as T);
      queue.push(node.left);
    }
    i++;
    if (i < values.length && values[i] !== null) {
      node.right = new TreeNode(values[i] as T);
      queue.push(node.right);
    }
    i++;
  }
  return root;
}
```

## 9.3 네 가지 순회

```ts
// src/ds/BinaryTreeTraversal.ts
import { TreeNode } from "./BinaryTree";

export function preorder<T>(root: TreeNode<T> | null): T[] {
  const result: T[] = [];
  function dfs(node: TreeNode<T> | null) {
    if (!node) return;
    result.push(node.value);
    dfs(node.left);
    dfs(node.right);
  }
  dfs(root);
  return result;
}

export function inorder<T>(root: TreeNode<T> | null): T[] {
  const result: T[] = [];
  function dfs(node: TreeNode<T> | null) {
    if (!node) return;
    dfs(node.left);
    result.push(node.value);
    dfs(node.right);
  }
  dfs(root);
  return result;
}

export function postorder<T>(root: TreeNode<T> | null): T[] {
  const result: T[] = [];
  function dfs(node: TreeNode<T> | null) {
    if (!node) return;
    dfs(node.left);
    dfs(node.right);
    result.push(node.value);
  }
  dfs(root);
  return result;
}

export function bfs<T>(root: TreeNode<T> | null): T[] {
  if (!root) return [];
  const result: T[] = [];
  const queue: TreeNode<T>[] = [root];
  while (queue.length > 0) {
    const node = queue.shift()!;
    result.push(node.value);
    if (node.left) queue.push(node.left);
    if (node.right) queue.push(node.right);
  }
  return result;
}
```

## 9.4 동작 확인

```ts
import { buildTree } from "./ds/BinaryTree";
import { preorder, inorder, postorder, bfs } from "./ds/BinaryTreeTraversal";

const root = buildTree([1, 2, 3, 4, 5, null, 6]);
console.log(preorder(root));  // [1, 2, 4, 5, 3, 6]
console.log(inorder(root));   // [4, 2, 5, 1, 3, 6]
console.log(postorder(root)); // [4, 5, 2, 6, 3, 1]
console.log(bfs(root));       // [1, 2, 3, 4, 5, 6]
```

## 9.5 재귀 vs 반복

재귀는 짧고 직관적이지만 깊이가 수만이 넘으면 스택 오버플로가 납니다. 반복으로 바꾸려면 직접 스택을 둡니다.

```ts
export function inorderIter<T>(root: TreeNode<T> | null): T[] {
  const result: T[] = [];
  const stack: TreeNode<T>[] = [];
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

## 핵심 정리
- 전위/중위/후위는 "현재 노드를 언제 방문하는가"의 차이일 뿐, 좌→우 순서는 항상 같다.
- BFS는 큐, DFS는 (암시적) 스택.
- 깊이가 매우 깊은 트리에선 반복형으로 바꿔라.

## 연습문제
1. 트리의 높이를 구하는 `height(root)`를 재귀로 구현하라.
2. 트리의 좌/우를 거울처럼 뒤집는 `invert(root)`를 구현하라.

---

# 10장. 이진 탐색 트리(BST)

## 학습 목표
- BST의 정렬 불변식을 이해한다.
- 삽입/검색/삭제를 구현한다.
- 균형이 깨졌을 때 어떤 일이 일어나는지 본다.

## 10.1 정의

이진 탐색 트리는 다음을 만족하는 이진 트리입니다.

> 모든 노드에 대해, **왼쪽 부분 트리의 모든 값 < 노드 값 < 오른쪽 부분 트리의 모든 값**

이러면 중위 순회가 정렬된 순서로 나옵니다.

## 10.2 구현

```ts
// src/ds/BST.ts
import { Comparator } from "../util/types";

class BSTNode<T> {
  left: BSTNode<T> | null = null;
  right: BSTNode<T> | null = null;
  constructor(public value: T) {}
}

export class BST<T> {
  private root: BSTNode<T> | null = null;
  private size = 0;

  constructor(private cmp: Comparator<T>) {}

  get length(): number { return this.size; }

  insert(value: T): void {
    this.root = this.insertNode(this.root, value);
  }

  private insertNode(node: BSTNode<T> | null, value: T): BSTNode<T> {
    if (!node) {
      this.size++;
      return new BSTNode(value);
    }
    const c = this.cmp(value, node.value);
    if (c < 0) node.left = this.insertNode(node.left, value);
    else if (c > 0) node.right = this.insertNode(node.right, value);
    // c === 0 이면 중복 — 무시
    return node;
  }

  has(value: T): boolean {
    let cur = this.root;
    while (cur) {
      const c = this.cmp(value, cur.value);
      if (c === 0) return true;
      cur = c < 0 ? cur.left : cur.right;
    }
    return false;
  }

  min(): T | undefined {
    if (!this.root) return undefined;
    let cur = this.root;
    while (cur.left) cur = cur.left;
    return cur.value;
  }

  max(): T | undefined {
    if (!this.root) return undefined;
    let cur = this.root;
    while (cur.right) cur = cur.right;
    return cur.value;
  }

  delete(value: T): boolean {
    const before = this.size;
    this.root = this.deleteNode(this.root, value);
    return this.size < before;
  }

  private deleteNode(node: BSTNode<T> | null, value: T): BSTNode<T> | null {
    if (!node) return null;
    const c = this.cmp(value, node.value);
    if (c < 0) { node.left = this.deleteNode(node.left, value); return node; }
    if (c > 0) { node.right = this.deleteNode(node.right, value); return node; }
    // 일치 — 세 가지 케이스
    this.size--;
    if (!node.left) return node.right;
    if (!node.right) return node.left;
    // 둘 다 있을 때: 오른쪽 부분 트리의 최솟값으로 대체
    let succ = node.right;
    while (succ.left) succ = succ.left;
    node.value = succ.value;
    this.size++; // deleteNode 재귀에서 다시 감소시킬 것이므로 보정
    node.right = this.deleteNode(node.right, succ.value);
    return node;
  }

  /** 정렬된 순서로 순회 */
  *[Symbol.iterator](): IterableIterator<T> {
    function* dfs(node: BSTNode<T> | null): IterableIterator<T> {
      if (!node) return;
      yield* dfs(node.left);
      yield node.value;
      yield* dfs(node.right);
    }
    yield* dfs(this.root);
  }

  toArray(): T[] { return [...this]; }
}
```

```ts
// src/util/types.ts
export type Comparator<T> = (a: T, b: T) => number;
export const numAsc: Comparator<number> = (a, b) => a - b;
```

## 10.3 동작 확인

```ts
import { BST } from "./ds/BST";
import { numAsc } from "./util/types";

const bst = new BST<number>(numAsc);
[5, 2, 8, 1, 3, 7, 9].forEach(v => bst.insert(v));
console.log(bst.toArray()); // [1, 2, 3, 5, 7, 8, 9]
console.log(bst.has(7));    // true
console.log(bst.min(), bst.max()); // 1 9

bst.delete(5);
console.log(bst.toArray()); // [1, 2, 3, 7, 8, 9]
```

## 10.4 균형 문제

이미 정렬된 데이터를 차례로 넣으면 BST는 한쪽으로만 뻗어 사실상 연결 리스트가 됩니다.

```ts
const bad = new BST<number>(numAsc);
[1, 2, 3, 4, 5].forEach(v => bad.insert(v));
// 트리:
// 1
//  \
//   2
//    \
//     3
//      \
//       4
//        \
//         5
```

이런 경우 `has`가 O(n)이 됩니다. 해결책은 **자동 균형 트리** — AVL, Red-Black, B-Tree 등. 이 책은 입문용이라 균형 트리는 다음 책으로 넘기지만, JavaScript의 `Set`/`Map`이 내부적으로 해시 테이블을 쓴다는 점, 정렬된 순회가 필요하면 `Array.sort`나 11장 힙을 고려한다는 점만 기억해 둡시다.

## 시간복잡도

| 연산 | 균형 잡힘 | 최악(편향) |
|------|-----------|-----------|
| 검색/삽입/삭제 | O(log n) | O(n) |

## 핵심 정리
- BST의 중위 순회는 자동 정렬이다.
- 균형이 깨지면 모든 보장이 사라진다. 데이터가 무작위로 들어오지 않는다면 균형 트리를 써라.

## 연습문제
1. BST에서 두 값 사이의 모든 원소를 반환하는 `range(lo, hi)`를 구현하라.
2. BST를 정렬된 배열로부터 만들 때, 항상 균형이 잡히도록 하는 `fromSortedArray`를 구현하라.

---

# 11장. 힙과 우선순위 큐

## 학습 목표
- 이진 힙(Binary Heap)의 배열 표현을 이해한다.
- 최소 힙을 직접 구현한다.
- 우선순위 큐로 작업 스케줄링을 구현해 본다.

## 11.1 힙이란

힙은 **부모가 자식보다 항상 작거나 같은**(최소 힙) 또는 **크거나 같은**(최대 힙) 완전 이진 트리입니다.

완전 이진 트리는 빈틈이 없으므로 **배열로 표현**할 수 있습니다.

```
인덱스:    0   1   2   3   4   5   6
값:        1   3   2   7   5   4   6

부모(i) = floor((i-1)/2)
왼자식(i) = 2i + 1
오른자식(i) = 2i + 2
```

## 11.2 구현

```ts
// src/ds/MinHeap.ts
import { Comparator, numAsc } from "../util/types";

export class MinHeap<T> {
  private data: T[] = [];

  constructor(private cmp: Comparator<T> = numAsc as Comparator<T>) {}

  get length(): number { return this.data.length; }
  isEmpty(): boolean { return this.data.length === 0; }
  peek(): T | undefined { return this.data[0]; }

  push(value: T): void {
    this.data.push(value);
    this.siftUp(this.data.length - 1);
  }

  pop(): T | undefined {
    if (this.data.length === 0) return undefined;
    const top = this.data[0];
    const last = this.data.pop()!;
    if (this.data.length > 0) {
      this.data[0] = last;
      this.siftDown(0);
    }
    return top;
  }

  /** 배열로부터 O(n)에 힙 빌드 */
  static from<U>(values: U[], cmp: Comparator<U>): MinHeap<U> {
    const h = new MinHeap<U>(cmp);
    h.data = values.slice();
    for (let i = Math.floor(h.data.length / 2) - 1; i >= 0; i--) h.siftDown(i);
    return h;
  }

  private siftUp(i: number): void {
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (this.cmp(this.data[i], this.data[p]) >= 0) break;
      [this.data[i], this.data[p]] = [this.data[p], this.data[i]];
      i = p;
    }
  }

  private siftDown(i: number): void {
    const n = this.data.length;
    while (true) {
      const l = 2 * i + 1, r = 2 * i + 2;
      let smallest = i;
      if (l < n && this.cmp(this.data[l], this.data[smallest]) < 0) smallest = l;
      if (r < n && this.cmp(this.data[r], this.data[smallest]) < 0) smallest = r;
      if (smallest === i) break;
      [this.data[i], this.data[smallest]] = [this.data[smallest], this.data[i]];
      i = smallest;
    }
  }

  toArray(): T[] { return this.data.slice(); }
}
```

## 11.3 동작 확인

```ts
import { MinHeap } from "./ds/MinHeap";

const h = new MinHeap<number>();
[5, 1, 4, 2, 8, 3].forEach(v => h.push(v));

const sorted: number[] = [];
while (!h.isEmpty()) sorted.push(h.pop()!);
console.log(sorted); // [1, 2, 3, 4, 5, 8]  — 힙 정렬
```

## 11.4 우선순위 큐로 변신

우선순위 큐(Priority Queue)는 "우선순위가 가장 높은 작업"을 꺼내는 큐입니다. 비교자만 바꾸면 됩니다.

```ts
type Task = { id: string; priority: number };

const pq = new MinHeap<Task>((a, b) => a.priority - b.priority); // 작은 priority가 먼저
pq.push({ id: "T1", priority: 5 });
pq.push({ id: "T2", priority: 1 });
pq.push({ id: "T3", priority: 3 });

while (!pq.isEmpty()) console.log(pq.pop()!.id);
// T2, T3, T1
```

## 11.5 K번째 큰 수 (실전 응용)

크기 K짜리 최소 힙을 유지하면 메모리 O(K)에 K번째 큰 수를 구할 수 있습니다.

```ts
// src/app/kthLargest.ts
import { MinHeap } from "../ds/MinHeap";

export function kthLargest(nums: number[], k: number): number {
  const h = new MinHeap<number>();
  for (const n of nums) {
    h.push(n);
    if (h.length > k) h.pop();
  }
  return h.peek()!;
}

console.log(kthLargest([3, 2, 1, 5, 6, 4], 2)); // 5
```

## 시간복잡도

| 연산 | 비용 |
|------|------|
| `push`/`pop` | O(log n) |
| `peek` | O(1) |
| 배열로부터 빌드 | O(n) — 직관적이지 않지만 사실 |

## 핵심 정리
- 힙은 트리지만 배열로 구현한다. 부모-자식 인덱스 공식이 핵심.
- 정렬 전체가 필요 없을 때 — "가장 작은(또는 큰) 몇 개" — 힙이 가장 효율적이다.

## 연습문제
1. 최대 힙으로 바꾸려면 무엇만 바꾸면 되는가?
2. 두 정렬된 배열을 합치는 데 힙을 써 보라(K-way merge로 확장 가능).

---

# 12장. 그래프와 BFS / DFS

## 학습 목표
- 그래프와 그 표현 방식(인접 리스트 vs 인접 행렬)을 안다.
- BFS와 DFS를 모두 구현한다.
- 위상 정렬을 직접 만든다.

## 12.1 그래프란

노드(정점)들과 그것들을 잇는 간선의 모음입니다. 방향이 있을 수도, 없을 수도, 가중치가 있을 수도 있습니다.

도로망, 친구 관계, 의존성 그래프, 미로, 게임 맵 — 거의 모든 "관계"는 그래프입니다.

## 12.2 인접 리스트

각 노드마다 "내가 연결된 노드들의 목록"을 저장합니다. 노드 V개, 간선 E개일 때 메모리 O(V+E).

```ts
// src/ds/Graph.ts
export class Graph<T> {
  private adj = new Map<T, Map<T, number>>(); // 노드 → (이웃 → 가중치)

  addNode(node: T): void {
    if (!this.adj.has(node)) this.adj.set(node, new Map());
  }

  addEdge(from: T, to: T, weight = 1, undirected = true): void {
    this.addNode(from);
    this.addNode(to);
    this.adj.get(from)!.set(to, weight);
    if (undirected) this.adj.get(to)!.set(from, weight);
  }

  neighbors(node: T): Map<T, number> {
    return this.adj.get(node) ?? new Map();
  }

  nodes(): IterableIterator<T> { return this.adj.keys(); }

  get size(): number { return this.adj.size; }
}
```

## 12.3 BFS — 최단 거리(가중치 없을 때)

```ts
// src/algo/bfs.ts
import { Graph } from "../ds/Graph";

export function bfs<T>(graph: Graph<T>, start: T): Map<T, number> {
  const dist = new Map<T, number>();
  dist.set(start, 0);
  const queue: T[] = [start];
  while (queue.length > 0) {
    const cur = queue.shift()!;
    for (const next of graph.neighbors(cur).keys()) {
      if (!dist.has(next)) {
        dist.set(next, dist.get(cur)! + 1);
        queue.push(next);
      }
    }
  }
  return dist;
}
```

```ts
import { Graph } from "./ds/Graph";
import { bfs } from "./algo/bfs";

const g = new Graph<string>();
g.addEdge("A", "B");
g.addEdge("A", "C");
g.addEdge("B", "D");
g.addEdge("C", "D");
g.addEdge("D", "E");

console.log([...bfs(g, "A")]);
// [["A", 0], ["B", 1], ["C", 1], ["D", 2], ["E", 3]]
```

## 12.4 DFS — 재귀와 반복

```ts
// src/algo/dfs.ts
import { Graph } from "../ds/Graph";

export function dfsRecursive<T>(graph: Graph<T>, start: T): T[] {
  const visited = new Set<T>();
  const order: T[] = [];
  function visit(node: T) {
    if (visited.has(node)) return;
    visited.add(node);
    order.push(node);
    for (const next of graph.neighbors(node).keys()) visit(next);
  }
  visit(start);
  return order;
}

export function dfsIterative<T>(graph: Graph<T>, start: T): T[] {
  const visited = new Set<T>();
  const order: T[] = [];
  const stack: T[] = [start];
  while (stack.length > 0) {
    const node = stack.pop()!;
    if (visited.has(node)) continue;
    visited.add(node);
    order.push(node);
    for (const next of graph.neighbors(node).keys()) {
      if (!visited.has(next)) stack.push(next);
    }
  }
  return order;
}
```

## 12.5 위상 정렬 (Topological Sort)

방향 그래프에서 "선행 관계"가 깨지지 않게 노드를 일렬로 줄세우는 것. 빌드 시스템, 작업 의존성 해결의 기본입니다.

진입 차수(in-degree)가 0인 노드부터 큐에서 꺼내며 처리합니다(Kahn 알고리즘).

```ts
// src/algo/topo.ts
import { Graph } from "../ds/Graph";

export function topologicalSort<T>(graph: Graph<T>): T[] {
  const inDegree = new Map<T, number>();
  for (const node of graph.nodes()) inDegree.set(node, 0);
  for (const node of graph.nodes()) {
    for (const next of graph.neighbors(node).keys()) {
      inDegree.set(next, (inDegree.get(next) ?? 0) + 1);
    }
  }

  const queue: T[] = [];
  for (const [n, d] of inDegree) if (d === 0) queue.push(n);

  const order: T[] = [];
  while (queue.length > 0) {
    const cur = queue.shift()!;
    order.push(cur);
    for (const next of graph.neighbors(cur).keys()) {
      inDegree.set(next, inDegree.get(next)! - 1);
      if (inDegree.get(next) === 0) queue.push(next);
    }
  }

  if (order.length !== inDegree.size) throw new Error("cycle detected");
  return order;
}
```

```ts
const deps = new Graph<string>();
deps.addEdge("compile", "test", 1, false); // false = directed
deps.addEdge("test", "package", 1, false);
deps.addEdge("compile", "lint", 1, false);
deps.addEdge("lint", "package", 1, false);

console.log(topologicalSort(deps));
// 예: [ "compile", "test", "lint", "package" ]
```

## 핵심 정리
- 그래프 표현은 거의 항상 **인접 리스트(`Map`)** 가 정답이다. 인접 행렬은 노드 수가 적고 밀집할 때만.
- BFS = 최단 거리(간선 가중치가 모두 1일 때).
- 가중치가 있으면 14장의 다익스트라.
- 사이클이 없는 방향 그래프에선 위상 정렬이 가능.

## 연습문제
1. BFS로 미로 최단 경로를 구하는 함수를 만들어라.
2. DFS로 사이클을 검출하는 함수를 만들어라.

---

# 13장. 트라이와 유니온-파인드

## 학습 목표
- 문자열 검색에 특화된 트라이(Trie) 구조를 만든다.
- 분리집합을 빠르게 합치고 비교하는 유니온-파인드(Disjoint Set)를 만든다.

## 13.1 트라이

자동완성, 사전, 접두사 검색에 쓰는 트리. 각 노드가 한 글자를 나타내고, 루트에서 잎까지의 경로가 단어입니다.

```
        root
       /  |  \
      a   c   d
      |   |   |
      p   a   o
      |   |   |
      p   t   g
      |
      l
      |
      e
```

문자열 N개의 평균 길이가 L일 때, 검색은 **단어 길이만큼만** O(L) — N과 무관!

```ts
// src/ds/Trie.ts
class TrieNode {
  children = new Map<string, TrieNode>();
  isWord = false;
}

export class Trie {
  private root = new TrieNode();

  insert(word: string): void {
    let cur = this.root;
    for (const ch of word) {
      let next = cur.children.get(ch);
      if (!next) {
        next = new TrieNode();
        cur.children.set(ch, next);
      }
      cur = next;
    }
    cur.isWord = true;
  }

  has(word: string): boolean {
    const node = this.findNode(word);
    return node !== null && node.isWord;
  }

  startsWith(prefix: string): boolean {
    return this.findNode(prefix) !== null;
  }

  /** 접두사로 시작하는 모든 단어 반환 — 자동완성의 핵심 */
  autocomplete(prefix: string, limit = 10): string[] {
    const node = this.findNode(prefix);
    if (!node) return [];
    const result: string[] = [];
    function dfs(n: TrieNode, path: string) {
      if (result.length >= limit) return;
      if (n.isWord) result.push(path);
      for (const [ch, child] of n.children) {
        if (result.length >= limit) return;
        dfs(child, path + ch);
      }
    }
    dfs(node, prefix);
    return result;
  }

  private findNode(s: string): TrieNode | null {
    let cur = this.root;
    for (const ch of s) {
      const next = cur.children.get(ch);
      if (!next) return null;
      cur = next;
    }
    return cur;
  }
}
```

```ts
import { Trie } from "./ds/Trie";

const trie = new Trie();
["apple", "app", "apply", "apt", "bat", "battle"].forEach(w => trie.insert(w));

console.log(trie.has("app"));        // true
console.log(trie.has("appl"));       // false
console.log(trie.startsWith("ap"));  // true
console.log(trie.autocomplete("ap"));// ["app", "apple", "apply", "apt"]
console.log(trie.autocomplete("bat"));// ["bat", "battle"]
```

## 13.2 유니온-파인드 (Disjoint Set Union)

"이 둘이 같은 그룹인가?" + "이 둘을 같은 그룹으로 묶어라"를 거의 O(1)에 처리하는 구조. 최소 신장 트리(크루스칼), 네트워크 연결 판정 등에 쓰입니다.

핵심 두 최적화:
- **경로 압축(path compression)**: `find`할 때 부모를 루트로 직접 이어버림.
- **랭크/사이즈 합치기(union by rank)**: 작은 트리를 큰 트리에 붙임.

```ts
// src/ds/DisjointSet.ts
export class DisjointSet {
  private parent: number[];
  private rank: number[];

  constructor(size: number) {
    this.parent = Array.from({ length: size }, (_, i) => i);
    this.rank = new Array(size).fill(0);
  }

  find(x: number): number {
    if (this.parent[x] !== x) {
      this.parent[x] = this.find(this.parent[x]); // 경로 압축
    }
    return this.parent[x];
  }

  /** 합쳤으면 true, 이미 같은 그룹이면 false */
  union(a: number, b: number): boolean {
    const ra = this.find(a), rb = this.find(b);
    if (ra === rb) return false;
    if (this.rank[ra] < this.rank[rb]) {
      this.parent[ra] = rb;
    } else if (this.rank[ra] > this.rank[rb]) {
      this.parent[rb] = ra;
    } else {
      this.parent[rb] = ra;
      this.rank[ra]++;
    }
    return true;
  }

  connected(a: number, b: number): boolean {
    return this.find(a) === this.find(b);
  }
}
```

```ts
import { DisjointSet } from "./ds/DisjointSet";

const ds = new DisjointSet(6);
ds.union(0, 1);
ds.union(1, 2);
ds.union(3, 4);

console.log(ds.connected(0, 2)); // true
console.log(ds.connected(0, 3)); // false

ds.union(2, 3);
console.log(ds.connected(0, 4)); // true
```

두 최적화를 모두 적용하면 한 연산의 비용이 **사실상 O(1)** 입니다. 정확히는 O(α(n))인데, α(아커만 함수의 역함수)는 우주의 모든 원자 수보다 큰 n에서도 4를 넘지 않습니다.

## 핵심 정리
- 트라이는 "접두사가 같은 단어 묶음"을 자연스럽게 표현한다. 자동완성/스펠 체크의 정공법.
- 유니온-파인드는 "그룹화"가 등장하면 무조건 떠올려야 하는 카드. 경로 압축 + 랭크 합치기 잊지 말기.

## 연습문제
1. 트라이에 `delete(word)`를 구현하라(쓰이지 않게 된 노드는 정리).
2. 유니온-파인드로 친구 관계가 들어올 때마다 "지금까지의 그룹 수"를 출력하라.

---

# 14장. 종합 실습

지금까지 만든 자료구조를 묶어 세 가지 실전 프로그램을 만듭니다.

1. **LRU 캐시** — 해시 테이블 + 이중 연결 리스트
2. **다익스트라 최단 경로** — 그래프 + 우선순위 큐
3. **자동완성 엔진** — 트라이 + 사용 빈도 정렬

## 14.1 LRU 캐시

LRU = Least Recently Used. 용량을 초과하면 **가장 오래 안 쓴 항목을 제거**하는 캐시.

핵심: get/put이 **모두 O(1)** 이어야 합니다. 이걸 만족하려면

- "키 → 노드" 빠른 조회 → **해시 테이블**
- "방금 쓴 항목을 맨 앞으로" 빠른 이동 → **이중 연결 리스트**

```ts
// src/app/LRUCache.ts
import { DoublyLinkedList } from "../ds/DoublyLinkedList";

type Entry<K, V> = { key: K; value: V };

export class LRUCache<K, V> {
  private list = new DoublyLinkedList<Entry<K, V>>();
  // DLLNode 타입을 외부로 export하지 않은 상태이므로 any로 단순화
  private map = new Map<K, any>();

  constructor(private capacity: number) {
    if (capacity <= 0) throw new RangeError("capacity must be > 0");
  }

  get(key: K): V | undefined {
    const node = this.map.get(key);
    if (!node) return undefined;
    this.list.moveToFront(node);
    return (node.value as Entry<K, V>).value;
  }

  put(key: K, value: V): void {
    const existing = this.map.get(key);
    if (existing) {
      existing.value = { key, value };
      this.list.moveToFront(existing);
      return;
    }
    if (this.map.size >= this.capacity) {
      // 가장 오래된 항목 제거 (꼬리)
      const evicted = this.list.popBack()!;
      this.map.delete(evicted.key);
    }
    const node = this.list.pushFront({ key, value });
    this.map.set(key, node);
  }

  get size(): number { return this.map.size; }
}
```

```ts
import { LRUCache } from "./app/LRUCache";

const cache = new LRUCache<string, number>(3);
cache.put("a", 1);
cache.put("b", 2);
cache.put("c", 3);
console.log(cache.get("a")); // 1 — a를 최신으로 끌어올림
cache.put("d", 4);            // b가 가장 오래됨 → 제거
console.log(cache.get("b")); // undefined
console.log(cache.get("c")); // 3
```

> 참고: 위 구현은 5장의 `DoublyLinkedList`가 노드 참조를 외부에 반환하는 구조여야 동작합니다. 실제 프로덕션 코드에서는 노드 타입을 함께 export하는 것이 좋습니다.

## 14.2 다익스트라 최단 경로

가중치가 있는 그래프에서 한 출발점으로부터 모든 노드까지의 최단 거리를 구합니다. 음수 가중치는 없다고 가정.

핵심: "현재까지 알려진 최단 거리가 가장 짧은 노드"를 빠르게 꺼내야 함 → **우선순위 큐(11장 힙)**.

```ts
// src/algo/dijkstra.ts
import { Graph } from "../ds/Graph";
import { MinHeap } from "../ds/MinHeap";

export function dijkstra<T>(graph: Graph<T>, start: T): Map<T, number> {
  const dist = new Map<T, number>();
  for (const n of graph.nodes()) dist.set(n, Infinity);
  dist.set(start, 0);

  const pq = new MinHeap<[number, T]>((a, b) => a[0] - b[0]);
  pq.push([0, start]);

  while (!pq.isEmpty()) {
    const [d, cur] = pq.pop()!;
    if (d > dist.get(cur)!) continue; // 이미 더 짧은 경로로 처리됨
    for (const [next, w] of graph.neighbors(cur)) {
      const nd = d + w;
      if (nd < (dist.get(next) ?? Infinity)) {
        dist.set(next, nd);
        pq.push([nd, next]);
      }
    }
  }

  return dist;
}
```

```ts
import { Graph } from "./ds/Graph";
import { dijkstra } from "./algo/dijkstra";

const g = new Graph<string>();
g.addEdge("A", "B", 7);
g.addEdge("A", "C", 9);
g.addEdge("A", "F", 14);
g.addEdge("B", "C", 10);
g.addEdge("B", "D", 15);
g.addEdge("C", "D", 11);
g.addEdge("C", "F", 2);
g.addEdge("D", "E", 6);
g.addEdge("E", "F", 9);

console.log([...dijkstra(g, "A")]);
// A=0, B=7, C=9, D=20, E=20, F=11
```

시간복잡도: O((V+E) log V).

## 14.3 자동완성 엔진

13장의 트라이에 **사용 빈도**를 더해, 인기 있는 단어부터 보여주는 자동완성을 만듭니다.

```ts
// src/app/Autocomplete.ts
class TrieNode {
  children = new Map<string, TrieNode>();
  word: string | null = null;
  freq = 0;
}

export class Autocomplete {
  private root = new TrieNode();

  /** 단어 등록 — 같은 단어 다시 등록하면 빈도 증가 */
  add(word: string, weight = 1): void {
    let cur = this.root;
    for (const ch of word) {
      let next = cur.children.get(ch);
      if (!next) { next = new TrieNode(); cur.children.set(ch, next); }
      cur = next;
    }
    cur.word = word;
    cur.freq += weight;
  }

  /** 사용 시 호출 — 빈도 증가로 우선순위 높임 */
  hit(word: string): void {
    let cur = this.root;
    for (const ch of word) {
      const next = cur.children.get(ch);
      if (!next) return;
      cur = next;
    }
    if (cur.word === word) cur.freq++;
  }

  suggest(prefix: string, limit = 5): string[] {
    let cur = this.root;
    for (const ch of prefix) {
      const next = cur.children.get(ch);
      if (!next) return [];
      cur = next;
    }
    const results: { word: string; freq: number }[] = [];
    function dfs(n: TrieNode) {
      if (n.word) results.push({ word: n.word, freq: n.freq });
      for (const child of n.children.values()) dfs(child);
    }
    dfs(cur);
    results.sort((a, b) => b.freq - a.freq);
    return results.slice(0, limit).map(r => r.word);
  }
}
```

```ts
import { Autocomplete } from "./app/Autocomplete";

const ac = new Autocomplete();
["apple", "application", "apply", "apricot", "appliance"].forEach(w => ac.add(w));

ac.hit("apple");
ac.hit("apple");
ac.hit("application");

console.log(ac.suggest("app", 3));
// ["apple", "application", "appliance"] — 빈도 1 동률(apply·appliance)은 트라이 탐색 순서를 따른다
```

## 14.4 다음 단계

이 책에서 만든 14가지 자료구조는 코딩 테스트와 일반적인 웹/앱 개발에서 90% 이상의 상황을 덮습니다. 더 깊이 공부하고 싶다면 다음 주제를 권합니다.

- **자기 균형 트리** — AVL, Red-Black, B-Tree
- **고급 그래프 알고리즘** — 벨만-포드, 플로이드-워셜, 최소 신장 트리(크루스칼/프림), 강결합 요소(타잔)
- **고급 문자열 알고리즘** — KMP, 라빈-카프, 접미사 배열
- **비결정적 자료구조** — 블룸 필터(Bloom Filter), 카운트-민 스케치, 스킵 리스트
- **함수형 영구 자료구조** — 한 번 만든 후 변경되지 않는 트리/리스트

또한, 이 책의 모든 구현체를 한 폴더에 모아 npm 패키지로 만들어 두면 다음 프로젝트에서 곧장 가져다 쓸 수 있습니다. **자기 자료구조 라이브러리를 갖는 것**, 그것이 자료구조 공부의 진짜 보상입니다.

---

# 부록 A. 자료구조 선택 치트시트

| 상황 | 추천 |
|------|------|
| 인덱스로 빠른 접근 | 배열 |
| 양 끝 빠른 추가/제거 | 이중 연결 리스트 / 덱 |
| LIFO | 스택 |
| FIFO | 원형 큐 |
| "이게 있나?" 빠른 검사 | 해시 셋(Set) |
| 키-값 저장 | `Map` 또는 해시 테이블 |
| 정렬 상태 유지 | (균형) BST 또는 정렬 배열 + 이진 탐색 |
| 우선순위 처리 | 힙(우선순위 큐) |
| 관계/네트워크 | 그래프 |
| 접두사 검색 | 트라이 |
| 그룹 합치기/판정 | 유니온-파인드 |
| 캐시 | LRU(해시 + DLL) |

# 부록 B. 시간복잡도 종합 표

| 자료구조 | 접근 | 검색 | 삽입 | 삭제 |
|----------|------|------|------|------|
| 배열 | O(1) | O(n) | O(n) | O(n) |
| 동적 배열 | O(1) | O(n) | amortized O(1) (끝) | O(n) |
| 연결 리스트 | O(n) | O(n) | O(1) (앞) | O(1) (앞) |
| 이중 연결 리스트 | O(n) | O(n) | O(1) (양 끝) | O(1) (양 끝) |
| 스택 | O(n) | O(n) | O(1) | O(1) |
| 원형 큐 | O(n) | O(n) | O(1) | O(1) |
| 해시 테이블 | — | O(1) avg | O(1) avg | O(1) avg |
| BST (균형) | O(log n) | O(log n) | O(log n) | O(log n) |
| BST (편향) | O(n) | O(n) | O(n) | O(n) |
| 이진 힙 | O(1) (최상) | O(n) | O(log n) | O(log n) |
| 트라이 | — | O(L) | O(L) | O(L) |
| 유니온-파인드 | — | O(α(n)) | — | — |

# 부록 C. tsconfig와 실행

이 책의 모든 코드는 다음 `tsconfig.json`에서 컴파일됩니다.

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
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
tsc

# 즉시 실행 (권장) — 컴파일 없이 바로 실행
npx tsx src/index.ts

# 컴파일 결과물을 node로 직접 실행하려면 package.json에 "type": "module"을 넣고,
# 소스의 상대 임포트에 .js 확장자를 붙여야 합니다.
#   예: import { measure } from "./util/measure.js";
# (확장자를 생략하게 해 주던 --experimental-specifier-resolution 플래그는
#  Node 20에서 제거되었습니다)
node dist/index.js
```

---

## 🔗 관련 문서
- [[TypeScript 기초 가이드북]] — 문법 입문
- [[TypeScript]] — 인덱스
- [[Go 패턴]] · [[Lua 기초]] · [[Pandas 가이드북]] — 다른 언어 가이드
- [[프로그래밍 언어]]
