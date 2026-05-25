# Lua로 배우는 자료구조

> 실행 가능한 예제로 익히는 자료구조 입문서
> 약 100페이지 분량 / Lua 5.4 기준

---

## 목차

1. [서문](#1-서문)
2. [Lua 시작하기](#2-lua-시작하기)
3. [테이블 — Lua의 만능 자료구조](#3-테이블--lua의-만능-자료구조)
4. [배열 (Array)](#4-배열-array)
5. [연결 리스트 (Linked List)](#5-연결-리스트-linked-list)
6. [스택 (Stack)](#6-스택-stack)
7. [큐와 덱 (Queue & Deque)](#7-큐와-덱-queue--deque)
8. [해시 테이블 (Hash Table)](#8-해시-테이블-hash-table)
9. [집합 (Set)](#9-집합-set)
10. [트리와 이진 탐색 트리](#10-트리와-이진-탐색-트리)
11. [힙과 우선순위 큐](#11-힙과-우선순위-큐)
12. [그래프 (Graph)](#12-그래프-graph)
13. [트라이 (Trie)](#13-트라이-trie)
14. [유니온 파인드 (Union-Find)](#14-유니온-파인드-union-find)
15. [고급 자료구조](#15-고급-자료구조)
16. [실전 응용](#16-실전-응용)
17. [부록 — 자료구조 치트시트](#17-부록--자료구조-치트시트)

---

# 1. 서문

## 1.1 이 책의 목적

자료구조는 프로그래밍의 골격이다. 어떤 언어를 쓰든, 데이터를 어떻게 저장하고 꺼내느냐가 프로그램의 성능과 가독성을 결정짓는다. 이 책은 **Lua**라는 작고 우아한 언어로 자료구조를 배운다.

왜 Lua인가? 첫째, 문법이 단순해서 자료구조의 본질에 집중할 수 있다. 둘째, Lua의 핵심 자료구조인 `table` 하나만 잘 이해하면 거의 모든 자료구조를 만들 수 있다. 셋째, 인터프리터가 가벼워서 어디서든 빠르게 실험해볼 수 있다.

이 책의 모든 예제는 **실행 가능**하다. 복사해서 `lua filename.lua` 로 바로 돌려볼 수 있다. 글을 읽기만 하지 말고, 한 줄씩 직접 타이핑하고 출력 결과를 눈으로 확인하길 권한다.

## 1.2 누구를 위한 책인가

- 다른 언어로 프로그래밍을 해봤지만 자료구조를 체계적으로 배우지 못한 사람
- C, Java, Python으로 자료구조를 배웠지만 더 본질적인 이해를 원하는 사람
- 게임 스크립팅, 임베디드, Redis, OpenResty 등에서 Lua를 만나 깊이 들어가려는 사람
- 코딩 테스트 준비를 Lua로 하고 싶은 호기심 많은 학생

## 1.3 학습 방법

1. **읽기 전 코드 먼저 돌려보기.** 출력이 어떤지 추측하고 맞춰보자.
2. **수정하기.** 입력 값을 바꿔보고, 일부러 망가뜨려보고, 어떻게 깨지는지 본다.
3. **다시 만들기.** 책을 덮고 빈 화면에서 직접 구현해본다. 두 번째 만들 때 비로소 이해된다.

자, 시작하자.

---

# 2. Lua 시작하기

## 2.1 설치와 실행

### 리눅스 / macOS

```bash
# Ubuntu/Debian
sudo apt install lua5.4

# macOS
brew install lua

# 버전 확인
lua -v
```

### Windows

[lua.org](http://www.lua.org)에서 바이너리를 받거나, [Scoop](https://scoop.sh) 사용:

```powershell
scoop install lua
```

### 첫 실행

```lua
-- hello.lua
print("Hello, Lua!")
```

```bash
$ lua hello.lua
Hello, Lua!
```

대화형 모드(REPL)로도 실험 가능하다.

```bash
$ lua
Lua 5.4.6  Copyright (C) 1994-2023 Lua.org, PUC-Rio
> print(1 + 2)
3
> = 1 + 2     -- Lua 5.4에서 = 으로 시작하면 print 생략
3
```

## 2.2 Lua 기본 문법 5분 요약

자료구조에 들어가기 전, 책 전체에서 쓰일 문법만 빠르게 짚고 가자.

### 변수와 타입

```lua
local n = 42              -- number
local s = "hello"         -- string
local b = true            -- boolean
local t = {1, 2, 3}       -- table (이 책의 주인공)
local f = function() end  -- function
local nothing = nil       -- nil (값 없음)

print(type(n), type(s), type(b), type(t))
-- 출력: number  string  boolean  table
```

> **중요:** `local` 키워드를 빼면 전역 변수가 된다. 이 책에서는 항상 `local`을 쓴다 (CLAUDE 가이드라인의 "global 금지"와 일맥상통).

### 제어문

```lua
-- if
local x = 10
if x > 0 then
    print("양수")
elseif x == 0 then
    print("영")
else
    print("음수")
end

-- while
local i = 1
while i <= 3 do
    print(i)
    i = i + 1
end

-- for (수치)
for i = 1, 5 do print(i) end       -- 1 2 3 4 5
for i = 10, 1, -2 do print(i) end  -- 10 8 6 4 2

-- for (제네릭)
for k, v in pairs({a=1, b=2}) do
    print(k, v)
end
```

### 함수

```lua
local function add(a, b)
    return a + b
end

-- 다중 반환
local function divmod(a, b)
    return a // b, a % b
end

local q, r = divmod(17, 5)
print(q, r)  -- 3  2

-- 가변 인자
local function sum(...)
    local args = {...}
    local s = 0
    for _, v in ipairs(args) do s = s + v end
    return s
end

print(sum(1, 2, 3, 4, 5))  -- 15
```

### 문자열

```lua
local s = "Lua"
print(#s)              -- 길이: 3
print(s .. " 5.4")     -- 연결: "Lua 5.4"
print(string.upper(s)) -- "LUA"
print(s:upper())       -- 같은 결과 (메서드 호출)
print(string.format("%d + %d = %d", 1, 2, 3))
```

## 2.3 알아둘 함정

Lua 초심자가 자주 놓치는 부분:

**1) 인덱스는 1부터 시작한다.**

```lua
local t = {"a", "b", "c"}
print(t[1])  -- "a"  (0이 아님!)
print(t[0])  -- nil
```

**2) `nil`과 `false`만 거짓이다. 0과 ""은 참이다.**

```lua
if 0 then print("참") end   -- 출력: 참
if "" then print("참") end  -- 출력: 참
```

**3) 비교 연산자는 `~=` (`!=` 아님).**

```lua
if a ~= b then ... end
```

**4) `and`/`or`는 단락 평가 + 값 반환.**

```lua
local x = nil
local y = x or "default"
print(y)  -- "default"
```

**5) `#` 연산자는 시퀀스에만 안전하다.**

```lua
local t = {1, 2, nil, 4}
print(#t)  -- 4 또는 2일 수 있음. 정의되지 않은 동작!
```

이 다섯 가지만 기억하면 자료구조 구현 중에 만나는 의문의 80%는 풀린다.

---

# 3. 테이블 — Lua의 만능 자료구조

## 3.1 테이블이 전부다

다른 언어들은 배열, 해시맵, 객체, 리스트를 별도의 타입으로 제공한다. Lua는 단 하나의 합성 자료구조 — **테이블** — 만 제공한다. 그리고 이 하나로 위의 모든 것을 만든다.

```lua
-- 배열처럼
local arr = {10, 20, 30}
print(arr[1], arr[2], arr[3])  -- 10  20  30

-- 해시맵처럼
local map = {name="홍길동", age=30}
print(map.name, map.age)        -- 홍길동  30
print(map["name"])              -- 같은 결과

-- 둘 다 섞어서
local mixed = {1, 2, 3, kind="numbers"}
print(mixed[1], mixed.kind)     -- 1  numbers

-- 객체처럼 (메서드 포함)
local point = {
    x = 10, y = 20,
    distance = function(self)
        return math.sqrt(self.x^2 + self.y^2)
    end
}
print(point:distance())         -- 22.36...
```

## 3.2 테이블의 내부 구조

Lua 테이블은 내부적으로 두 부분으로 나뉜다:

- **배열 부분 (array part)**: 1, 2, 3, ... 같은 양의 정수 키
- **해시 부분 (hash part)**: 그 외 모든 키 (문자열, 음수, 실수, 객체 등)

이는 성능 최적화다. `t[1], t[2], t[3]` 같은 정수 인덱스 접근은 C 배열만큼 빠르다. `t.name`은 해시 테이블 조회로 처리된다.

```lua
local t = {}
t[1] = "first"     -- 배열 부분
t[2] = "second"    -- 배열 부분
t.name = "test"    -- 해시 부분
t[100] = "far"     -- 보통 해시 부분 (배열이 너무 듬성)
```

이 구조를 이해하면 왜 "1부터 시작하는 연속된 정수 키"가 시퀀스(sequence)로 특별 취급되는지 알 수 있다.

## 3.3 테이블 기본 연산

```lua
local t = {10, 20, 30}

-- 길이
print(#t)                    -- 3

-- 끝에 추가
table.insert(t, 40)
print(t[4])                  -- 40

-- 특정 위치에 삽입
table.insert(t, 1, 5)        -- 맨 앞에 삽입
print(t[1], t[2])            -- 5  10

-- 제거
table.remove(t)              -- 끝에서 제거
table.remove(t, 1)           -- 첫 번째 제거

-- 정렬
local nums = {3, 1, 4, 1, 5, 9, 2, 6}
table.sort(nums)
for _, v in ipairs(nums) do io.write(v, " ") end
-- 출력: 1 1 2 3 4 5 6 9
print()

-- 역정렬
table.sort(nums, function(a, b) return a > b end)

-- 연결 (concat)
local words = {"hello", "world", "lua"}
print(table.concat(words, ", "))  -- "hello, world, lua"
```

## 3.4 순회 (iteration)

```lua
local t = {10, 20, 30, name="alice"}

-- 1) ipairs: 시퀀스(1..n) 순회. 중간에 nil 만나면 멈춤
for i, v in ipairs(t) do
    print(i, v)
end
-- 출력:
-- 1  10
-- 2  20
-- 3  30

-- 2) pairs: 모든 키-값 순회 (순서 보장 안 됨)
for k, v in pairs(t) do
    print(k, v)
end
-- 출력 (순서 다를 수 있음):
-- 1     10
-- 2     20
-- 3     30
-- name  alice
```

**언제 무엇을 쓸까?**

- 배열 시퀀스를 순서대로 처리: `ipairs`
- 해시맵 전체를 훑을 때: `pairs`
- 정해진 순서가 필요하면 키를 정렬해서 순회

```lua
local scores = {alice=90, bob=85, carol=78}
local keys = {}
for k in pairs(scores) do table.insert(keys, k) end
table.sort(keys)

for _, k in ipairs(keys) do
    print(k, scores[k])
end
-- 출력:
-- alice  90
-- bob    85
-- carol  78
```

## 3.5 깊은 복사 / 얕은 복사

테이블은 **참조 타입**이다. 대입은 복사가 아니다.

```lua
local a = {1, 2, 3}
local b = a
b[1] = 999
print(a[1])  -- 999  (a도 바뀜!)
```

얕은 복사:

```lua
local function shallow_copy(t)
    local copy = {}
    for k, v in pairs(t) do
        copy[k] = v
    end
    return copy
end
```

깊은 복사:

```lua
local function deep_copy(t, seen)
    if type(t) ~= "table" then return t end
    seen = seen or {}
    if seen[t] then return seen[t] end  -- 순환 참조 방지

    local copy = {}
    seen[t] = copy
    for k, v in pairs(t) do
        copy[deep_copy(k, seen)] = deep_copy(v, seen)
    end
    return copy
end

-- 테스트
local original = {1, {2, 3}, {a = {b = 4}}}
local clone = deep_copy(original)
clone[2][1] = 999
print(original[2][1])  -- 2 (원본 안전)
print(clone[2][1])     -- 999
```

## 3.6 메타테이블 한 입 맛보기

테이블의 동작을 커스터마이징하는 메커니즘이 **메타테이블**이다. 자료구조 구현에서 자주 쓰니 짚고 가자.

```lua
local Vector = {}
Vector.__index = Vector  -- 메서드 검색용

function Vector.new(x, y)
    return setmetatable({x=x, y=y}, Vector)
end

function Vector:length()
    return math.sqrt(self.x^2 + self.y^2)
end

-- 연산자 오버로딩
Vector.__add = function(a, b)
    return Vector.new(a.x + b.x, a.y + b.y)
end

Vector.__tostring = function(v)
    return string.format("(%g, %g)", v.x, v.y)
end

local v1 = Vector.new(3, 4)
local v2 = Vector.new(1, 2)
local v3 = v1 + v2

print(v1:length())  -- 5.0
print(tostring(v3)) -- (4, 6)
```

이 패턴을 익혀두면 7장 이후로 등장하는 모든 자료구조 클래스가 자연스럽게 읽힐 것이다.

---

# 4. 배열 (Array)

## 4.1 배열이란

배열은 **같은 타입의 원소를 일렬로 늘어놓은 자료구조**다. 인덱스로 즉시 접근(O(1))할 수 있다는 점이 가장 큰 강점.

Lua에서 배열은 시퀀스 형태의 테이블이다.

```lua
local arr = {10, 20, 30, 40, 50}
print(arr[3])  -- 30 (O(1) 접근)
```

## 4.2 동적 배열 직접 만들기

`table.insert`/`table.remove`로 충분하지만, 학습을 위해 직접 만들어보자.

```lua
-- dynamic_array.lua
local DynamicArray = {}
DynamicArray.__index = DynamicArray

function DynamicArray.new()
    return setmetatable({size = 0, data = {}}, DynamicArray)
end

function DynamicArray:push(value)
    self.size = self.size + 1
    self.data[self.size] = value
end

function DynamicArray:pop()
    if self.size == 0 then return nil end
    local v = self.data[self.size]
    self.data[self.size] = nil
    self.size = self.size - 1
    return v
end

function DynamicArray:get(i)
    assert(i >= 1 and i <= self.size, "out of range")
    return self.data[i]
end

function DynamicArray:set(i, v)
    assert(i >= 1 and i <= self.size, "out of range")
    self.data[i] = v
end

function DynamicArray:length()
    return self.size
end

function DynamicArray:print()
    io.write("[")
    for i = 1, self.size do
        io.write(tostring(self.data[i]))
        if i < self.size then io.write(", ") end
    end
    print("]")
end

-- 테스트
local a = DynamicArray.new()
for i = 1, 5 do a:push(i * 10) end
a:print()                -- [10, 20, 30, 40, 50]
print(a:get(3))          -- 30
a:set(3, 999)
a:print()                -- [10, 20, 999, 40, 50]
print(a:pop())           -- 50
a:print()                -- [10, 20, 999, 40]
```

## 4.3 배열 알고리즘 모음

### 선형 탐색

```lua
local function linear_search(arr, target)
    for i = 1, #arr do
        if arr[i] == target then return i end
    end
    return -1
end

print(linear_search({3, 5, 7, 9, 11}, 7))  -- 3
print(linear_search({3, 5, 7, 9, 11}, 4))  -- -1
```

시간복잡도 O(n).

### 이진 탐색

```lua
local function binary_search(arr, target)
    local lo, hi = 1, #arr
    while lo <= hi do
        local mid = (lo + hi) // 2
        if arr[mid] == target then
            return mid
        elseif arr[mid] < target then
            lo = mid + 1
        else
            hi = mid - 1
        end
    end
    return -1
end

local sorted = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
print(binary_search(sorted, 11))  -- 6
print(binary_search(sorted, 4))   -- -1
```

시간복잡도 O(log n). **단, 정렬된 배열에서만!**

### 뒤집기

```lua
local function reverse(arr)
    local lo, hi = 1, #arr
    while lo < hi do
        arr[lo], arr[hi] = arr[hi], arr[lo]
        lo = lo + 1
        hi = hi - 1
    end
    return arr
end

local t = {1, 2, 3, 4, 5}
reverse(t)
print(table.concat(t, " "))  -- 5 4 3 2 1
```

### 회전

```lua
-- 오른쪽으로 k칸 회전: [1,2,3,4,5], k=2 → [4,5,1,2,3]
local function rotate(arr, k)
    local n = #arr
    k = k % n
    -- 3단계 뒤집기 트릭
    reverse_range(arr, 1, n)
    reverse_range(arr, 1, k)
    reverse_range(arr, k+1, n)
end

function reverse_range(arr, lo, hi)
    while lo < hi do
        arr[lo], arr[hi] = arr[hi], arr[lo]
        lo, hi = lo+1, hi-1
    end
end

local t = {1, 2, 3, 4, 5}
rotate(t, 2)
print(table.concat(t, " "))  -- 4 5 1 2 3
```

### 중복 제거

```lua
local function dedupe_sorted(arr)
    if #arr == 0 then return arr end
    local w = 1
    for r = 2, #arr do
        if arr[r] ~= arr[w] then
            w = w + 1
            arr[w] = arr[r]
        end
    end
    -- 뒤쪽 잘라내기
    for i = w+1, #arr do arr[i] = nil end
    return arr
end

local t = {1, 1, 2, 2, 2, 3, 4, 4, 5}
dedupe_sorted(t)
print(table.concat(t, " "))  -- 1 2 3 4 5
```

## 4.4 정렬 알고리즘 직접 만들기

`table.sort`는 내부적으로 quicksort를 쓴다. 여기서는 학습용으로 직접 구현해본다.

### 버블 정렬 — O(n²)

```lua
local function bubble_sort(arr)
    local n = #arr
    for i = 1, n - 1 do
        local swapped = false
        for j = 1, n - i do
            if arr[j] > arr[j+1] then
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = true
            end
        end
        if not swapped then break end
    end
    return arr
end

print(table.concat(bubble_sort({5, 2, 8, 1, 9, 3}), " "))
-- 1 2 3 5 8 9
```

### 삽입 정렬 — O(n²)

```lua
local function insertion_sort(arr)
    for i = 2, #arr do
        local key = arr[i]
        local j = i - 1
        while j >= 1 and arr[j] > key do
            arr[j+1] = arr[j]
            j = j - 1
        end
        arr[j+1] = key
    end
    return arr
end

print(table.concat(insertion_sort({5, 2, 8, 1, 9, 3}), " "))
```

거의 정렬된 데이터엔 O(n)에 가깝다.

### 병합 정렬 — O(n log n)

```lua
local function merge(left, right)
    local result, i, j = {}, 1, 1
    while i <= #left and j <= #right do
        if left[i] <= right[j] then
            table.insert(result, left[i]); i = i + 1
        else
            table.insert(result, right[j]); j = j + 1
        end
    end
    while i <= #left do table.insert(result, left[i]); i = i + 1 end
    while j <= #right do table.insert(result, right[j]); j = j + 1 end
    return result
end

local function merge_sort(arr)
    if #arr <= 1 then return arr end
    local mid = #arr // 2
    local left, right = {}, {}
    for i = 1, mid do left[i] = arr[i] end
    for i = mid + 1, #arr do right[i - mid] = arr[i] end
    return merge(merge_sort(left), merge_sort(right))
end

local sorted = merge_sort({5, 2, 8, 1, 9, 3, 7, 4, 6})
print(table.concat(sorted, " "))  -- 1 2 3 4 5 6 7 8 9
```

### 퀵 정렬 — 평균 O(n log n)

```lua
local function quicksort(arr, lo, hi)
    lo = lo or 1
    hi = hi or #arr
    if lo >= hi then return end

    local pivot = arr[hi]
    local i = lo - 1
    for j = lo, hi - 1 do
        if arr[j] <= pivot then
            i = i + 1
            arr[i], arr[j] = arr[j], arr[i]
        end
    end
    arr[i+1], arr[hi] = arr[hi], arr[i+1]

    quicksort(arr, lo, i)
    quicksort(arr, i + 2, hi)
end

local t = {5, 2, 8, 1, 9, 3, 7, 4, 6}
quicksort(t)
print(table.concat(t, " "))
```

## 4.5 다차원 배열

Lua엔 진짜 다차원 배열이 없다. 테이블의 테이블로 흉내낸다.

```lua
-- 3x3 행렬
local function new_matrix(rows, cols, fill)
    fill = fill or 0
    local m = {}
    for i = 1, rows do
        m[i] = {}
        for j = 1, cols do
            m[i][j] = fill
        end
    end
    return m
end

local mat = new_matrix(3, 3, 0)
mat[1][1] = 1
mat[2][2] = 2
mat[3][3] = 3

for i = 1, 3 do
    for j = 1, 3 do
        io.write(mat[i][j], " ")
    end
    print()
end
-- 출력:
-- 1 0 0
-- 0 2 0
-- 0 0 3
```

### 행렬 곱셈

```lua
local function matmul(a, b)
    local rows_a, cols_a = #a, #a[1]
    local rows_b, cols_b = #b, #b[1]
    assert(cols_a == rows_b, "shape mismatch")

    local c = new_matrix(rows_a, cols_b, 0)
    for i = 1, rows_a do
        for j = 1, cols_b do
            local sum = 0
            for k = 1, cols_a do
                sum = sum + a[i][k] * b[k][j]
            end
            c[i][j] = sum
        end
    end
    return c
end

local A = {{1, 2}, {3, 4}}
local B = {{5, 6}, {7, 8}}
local C = matmul(A, B)
for i = 1, #C do print(table.concat(C[i], " ")) end
-- 19 22
-- 43 50
```

## 4.6 배열 성능 요약

| 연산        | 시간복잡도 |
|-----------|-------|
| 인덱스 접근    | O(1)  |
| 끝에 추가/제거  | O(1) (분할상환) |
| 중간에 삽입/제거 | O(n)  |
| 선형 탐색     | O(n)  |
| 이진 탐색(정렬됨) | O(log n) |

**언제 쓸까:** 임의 접근이 잦고, 크기가 안정적이며, 끝쪽에서만 변경이 일어날 때.
**언제 피할까:** 중간 삽입/삭제가 잦을 때 → 연결 리스트가 유리할 수 있다.

---

# 5. 연결 리스트 (Linked List)

## 5.1 연결 리스트란

배열은 메모리에 연속으로 늘어놓는다. 연결 리스트는 **노드들이 포인터로 연결되어 있는** 자료구조다. 각 노드는 값과 다음 노드의 참조를 갖는다.

```
[10|*]→[20|*]→[30|*]→[40|*]→nil
```

장점: 중간 삽입/삭제가 O(1) (해당 노드를 알고 있다면).
단점: 인덱스 접근이 O(n).

## 5.2 단일 연결 리스트

```lua
-- linked_list.lua
local LinkedList = {}
LinkedList.__index = LinkedList

function LinkedList.new()
    return setmetatable({head = nil, size = 0}, LinkedList)
end

function LinkedList:push_front(value)
    self.head = {value = value, next = self.head}
    self.size = self.size + 1
end

function LinkedList:push_back(value)
    local node = {value = value, next = nil}
    if not self.head then
        self.head = node
    else
        local cur = self.head
        while cur.next do cur = cur.next end
        cur.next = node
    end
    self.size = self.size + 1
end

function LinkedList:pop_front()
    if not self.head then return nil end
    local v = self.head.value
    self.head = self.head.next
    self.size = self.size - 1
    return v
end

function LinkedList:find(value)
    local cur, idx = self.head, 1
    while cur do
        if cur.value == value then return idx end
        cur = cur.next
        idx = idx + 1
    end
    return -1
end

function LinkedList:remove(value)
    if not self.head then return false end
    if self.head.value == value then
        self.head = self.head.next
        self.size = self.size - 1
        return true
    end
    local cur = self.head
    while cur.next do
        if cur.next.value == value then
            cur.next = cur.next.next
            self.size = self.size - 1
            return true
        end
        cur = cur.next
    end
    return false
end

function LinkedList:print()
    local cur = self.head
    local parts = {}
    while cur do
        table.insert(parts, tostring(cur.value))
        cur = cur.next
    end
    print(table.concat(parts, " -> ") .. " -> nil")
end

-- 테스트
local list = LinkedList.new()
list:push_back(10)
list:push_back(20)
list:push_back(30)
list:push_front(5)
list:print()                  -- 5 -> 10 -> 20 -> 30 -> nil
print(list:find(20))          -- 3
list:remove(20)
list:print()                  -- 5 -> 10 -> 30 -> nil
print(list:pop_front())       -- 5
list:print()                  -- 10 -> 30 -> nil
```

## 5.3 이중 연결 리스트

각 노드가 `prev`와 `next` 둘 다 가진다. 양쪽으로 순회하고, 노드 위치에서 즉시 삭제할 수 있다.

```lua
-- doubly_linked_list.lua
local DLL = {}
DLL.__index = DLL

function DLL.new()
    return setmetatable({head = nil, tail = nil, size = 0}, DLL)
end

function DLL:push_back(v)
    local node = {value = v, prev = self.tail, next = nil}
    if self.tail then self.tail.next = node else self.head = node end
    self.tail = node
    self.size = self.size + 1
    return node
end

function DLL:push_front(v)
    local node = {value = v, prev = nil, next = self.head}
    if self.head then self.head.prev = node else self.tail = node end
    self.head = node
    self.size = self.size + 1
    return node
end

function DLL:remove_node(node)
    if node.prev then node.prev.next = node.next
    else self.head = node.next end

    if node.next then node.next.prev = node.prev
    else self.tail = node.prev end

    self.size = self.size - 1
end

function DLL:print_forward()
    local cur, parts = self.head, {}
    while cur do
        table.insert(parts, tostring(cur.value))
        cur = cur.next
    end
    print(table.concat(parts, " <-> "))
end

function DLL:print_backward()
    local cur, parts = self.tail, {}
    while cur do
        table.insert(parts, tostring(cur.value))
        cur = cur.prev
    end
    print(table.concat(parts, " <-> "))
end

local d = DLL.new()
d:push_back(1)
d:push_back(2)
d:push_back(3)
d:push_front(0)
d:print_forward()   -- 0 <-> 1 <-> 2 <-> 3
d:print_backward()  -- 3 <-> 2 <-> 1 <-> 0
```

이중 연결 리스트는 **LRU 캐시** 같은 자료구조의 핵심 부품이다 (15장 참조).

## 5.4 연결 리스트 알고리즘

### 뒤집기

```lua
function LinkedList:reverse()
    local prev, cur = nil, self.head
    while cur do
        local nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    end
    self.head = prev
end

local list = LinkedList.new()
for i = 1, 5 do list:push_back(i) end
list:print()                  -- 1 -> 2 -> 3 -> 4 -> 5 -> nil
list:reverse()
list:print()                  -- 5 -> 4 -> 3 -> 2 -> 1 -> nil
```

이 패턴은 코딩 테스트의 단골이다.

### 사이클 탐지 (Floyd의 토끼와 거북이)

```lua
local function has_cycle(head)
    local slow, fast = head, head
    while fast and fast.next do
        slow = slow.next
        fast = fast.next.next
        if slow == fast then return true end
    end
    return false
end

-- 인위적 사이클 만들기
local list = LinkedList.new()
for i = 1, 5 do list:push_back(i) end
local last = list.head
while last.next do last = last.next end
last.next = list.head.next  -- 사이클!

print(has_cycle(list.head))  -- true
```

### 두 정렬된 리스트 병합

```lua
local function merge_sorted(a, b)
    local dummy = {next = nil}
    local tail = dummy
    while a and b do
        if a.value <= b.value then
            tail.next, a = a, a.next
        else
            tail.next, b = b, b.next
        end
        tail = tail.next
    end
    tail.next = a or b
    return dummy.next
end
```

## 5.5 배열 vs 연결 리스트

| 연산        | 배열     | 연결 리스트 |
|-----------|--------|--------|
| 인덱스 접근    | O(1)   | O(n)   |
| 앞쪽 삽입     | O(n)   | O(1)   |
| 뒤쪽 삽입     | O(1)*  | O(1)** |
| 중간 삽입(노드 알 때) | O(n) | O(1) |
| 메모리 지역성   | 좋음     | 나쁨     |
| 캐시 친화도    | 높음     | 낮음     |

\* 분할상환 / \*\* `tail` 포인터 있을 때

**현실 조언:** 현대 CPU에선 캐시 효율 때문에 배열이 거의 항상 빠르다. 연결 리스트가 진짜 필요한 곳은 **노드 자체를 외부에서 참조하면서 O(1)에 떼어내야 하는 경우** (LRU 캐시, 자유 리스트 등)다.

---

# 6. 스택 (Stack)

## 6.1 LIFO

스택은 **후입선출(Last In First Out)** 자료구조다. 책상 위에 책을 쌓고, 위에서부터 빼는 모습.

세 가지 연산:
- `push(x)`: 위에 올림
- `pop()`: 위에서 뺌
- `top()` 또는 `peek()`: 위에 무엇이 있는지 보기 (제거 X)

## 6.2 배열 기반 스택

```lua
-- stack.lua
local Stack = {}
Stack.__index = Stack

function Stack.new()
    return setmetatable({items = {}, n = 0}, Stack)
end

function Stack:push(v)
    self.n = self.n + 1
    self.items[self.n] = v
end

function Stack:pop()
    if self.n == 0 then return nil end
    local v = self.items[self.n]
    self.items[self.n] = nil
    self.n = self.n - 1
    return v
end

function Stack:peek()
    return self.items[self.n]
end

function Stack:empty()
    return self.n == 0
end

function Stack:size()
    return self.n
end

-- 테스트
local s = Stack.new()
s:push(1); s:push(2); s:push(3)
print(s:peek())  -- 3
print(s:pop())   -- 3
print(s:pop())   -- 2
print(s:size())  -- 1
```

모든 연산이 O(1).

## 6.3 응용 1: 괄호 짝 검사

```lua
local function is_balanced(expr)
    local pairs_map = {[")"] = "(", ["]"] = "[", ["}"] = "{"}
    local stack = Stack.new()

    for i = 1, #expr do
        local c = expr:sub(i, i)
        if c == "(" or c == "[" or c == "{" then
            stack:push(c)
        elseif c == ")" or c == "]" or c == "}" then
            if stack:pop() ~= pairs_map[c] then
                return false
            end
        end
    end
    return stack:empty()
end

print(is_balanced("(a+b)*[c-d]"))      -- true
print(is_balanced("([)]"))             -- false
print(is_balanced("{[()]}"))            -- true
print(is_balanced("("))                 -- false
```

## 6.4 응용 2: 중위 → 후위 변환 (Shunting-yard)

```lua
local function to_postfix(expr)
    local prec = {["+"]=1, ["-"]=1, ["*"]=2, ["/"]=2, ["^"]=3}
    local right_assoc = {["^"]=true}
    local output, ops = {}, Stack.new()

    -- 토큰화 (간단 버전: 공백 기준)
    for token in expr:gmatch("%S+") do
        if tonumber(token) then
            table.insert(output, token)
        elseif token == "(" then
            ops:push(token)
        elseif token == ")" then
            while not ops:empty() and ops:peek() ~= "(" do
                table.insert(output, ops:pop())
            end
            ops:pop()  -- "(" 버림
        else  -- 연산자
            while not ops:empty() and ops:peek() ~= "(" do
                local top = ops:peek()
                if (right_assoc[token] and prec[top] > prec[token]) or
                   (not right_assoc[token] and prec[top] >= prec[token]) then
                    table.insert(output, ops:pop())
                else
                    break
                end
            end
            ops:push(token)
        end
    end
    while not ops:empty() do
        table.insert(output, ops:pop())
    end
    return table.concat(output, " ")
end

print(to_postfix("3 + 4 * 2"))         -- 3 4 2 * +
print(to_postfix("( 1 + 2 ) * 3"))     -- 1 2 + 3 *
print(to_postfix("2 ^ 3 ^ 2"))         -- 2 3 2 ^ ^  (오른쪽 결합)
```

## 6.5 응용 3: 후위식 평가

```lua
local function eval_postfix(expr)
    local stack = Stack.new()
    for token in expr:gmatch("%S+") do
        local n = tonumber(token)
        if n then
            stack:push(n)
        else
            local b = stack:pop()
            local a = stack:pop()
            if token == "+" then stack:push(a + b)
            elseif token == "-" then stack:push(a - b)
            elseif token == "*" then stack:push(a * b)
            elseif token == "/" then stack:push(a / b)
            elseif token == "^" then stack:push(a ^ b)
            end
        end
    end
    return stack:pop()
end

print(eval_postfix("3 4 2 * +"))   -- 11
print(eval_postfix("1 2 + 3 *"))   -- 9
```

이 두 함수를 합치면 간단한 계산기가 된다.

```lua
local function calc(expr)
    return eval_postfix(to_postfix(expr))
end
print(calc("( 3 + 5 ) * 2 - 4"))   -- 12
```

## 6.6 응용 4: DFS의 명시적 스택

재귀 대신 스택을 써서 DFS를 짤 수 있다 (12장에서 본격 사용).

```lua
local graph = {
    A = {"B", "C"},
    B = {"D", "E"},
    C = {"F"},
    D = {}, E = {}, F = {}
}

local function dfs(start)
    local stack = Stack.new()
    local visited = {}
    stack:push(start)
    while not stack:empty() do
        local node = stack:pop()
        if not visited[node] then
            visited[node] = true
            io.write(node, " ")
            for _, n in ipairs(graph[node]) do
                stack:push(n)
            end
        end
    end
    print()
end

dfs("A")  -- A C F B E D  (스택 특성상 역순)
```

## 6.7 함수 호출 스택

CPU도 함수 호출을 스택으로 관리한다. Lua의 `debug.traceback`이 그 흔적이다.

```lua
local function foo()
    print(debug.traceback("at foo"))
end
local function bar() foo() end
local function baz() bar() end
baz()
```

재귀 깊이가 깊어지면 스택 오버플로우가 난다. 깊이가 우려되면 **반복문 + 명시적 스택**으로 바꿔야 한다.

---

# 7. 큐와 덱 (Queue & Deque)

## 7.1 FIFO

큐는 **선입선출(First In First Out)**. 줄서기.

- `enqueue(x)` (push back): 뒤에 추가
- `dequeue()` (pop front): 앞에서 빼기

## 7.2 단순 큐 — 안티패턴

가장 단순한 구현:

```lua
local q = {}
table.insert(q, 1)        -- enqueue
table.insert(q, 2)
local v = table.remove(q, 1)  -- dequeue (앞에서)
```

문제: `table.remove(q, 1)`은 모든 원소를 한 칸씩 당겨오므로 **O(n)**. 큐의 핵심인 dequeue가 느린 건 치명적.

## 7.3 두 인덱스 기반 큐

`first`, `last` 인덱스를 두고 양 끝만 움직이면 둘 다 O(1).

```lua
-- queue.lua
local Queue = {}
Queue.__index = Queue

function Queue.new()
    return setmetatable({first = 1, last = 0, items = {}}, Queue)
end

function Queue:enqueue(v)
    self.last = self.last + 1
    self.items[self.last] = v
end

function Queue:dequeue()
    if self.first > self.last then return nil end
    local v = self.items[self.first]
    self.items[self.first] = nil
    self.first = self.first + 1
    return v
end

function Queue:peek()
    return self.items[self.first]
end

function Queue:size()
    return self.last - self.first + 1
end

function Queue:empty()
    return self.first > self.last
end

-- 테스트
local q = Queue.new()
q:enqueue("a"); q:enqueue("b"); q:enqueue("c")
print(q:dequeue())  -- a
print(q:dequeue())  -- b
q:enqueue("d")
while not q:empty() do io.write(q:dequeue(), " ") end
-- 출력: c d
print()
```

`first`/`last`가 무한히 증가한다는 약점은 있지만, Lua의 number는 64비트라 실용적으로 문제 없다.

## 7.4 원형 버퍼 (Circular Buffer)

크기가 고정인 큐엔 원형 버퍼가 좋다. 메모리 재사용 + 캐시 친화적.

```lua
local CircularQueue = {}
CircularQueue.__index = CircularQueue

function CircularQueue.new(capacity)
    return setmetatable({
        buf = {},
        cap = capacity,
        head = 1, tail = 1, size = 0
    }, CircularQueue)
end

function CircularQueue:enqueue(v)
    if self.size == self.cap then return false, "full" end
    self.buf[self.tail] = v
    self.tail = (self.tail % self.cap) + 1
    self.size = self.size + 1
    return true
end

function CircularQueue:dequeue()
    if self.size == 0 then return nil end
    local v = self.buf[self.head]
    self.buf[self.head] = nil
    self.head = (self.head % self.cap) + 1
    self.size = self.size - 1
    return v
end

local cq = CircularQueue.new(3)
cq:enqueue(1); cq:enqueue(2); cq:enqueue(3)
print(cq:enqueue(4))  -- false   full
print(cq:dequeue())   -- 1
cq:enqueue(4)         -- 이제 자리 있음
print(cq:dequeue(), cq:dequeue(), cq:dequeue())  -- 2 3 4
```

## 7.5 덱 (Deque, 양방향 큐)

양 끝에서 모두 push/pop이 가능한 자료구조.

```lua
local Deque = {}
Deque.__index = Deque

function Deque.new()
    return setmetatable({first = 0, last = -1, items = {}}, Deque)
end

function Deque:push_front(v)
    self.items[self.first] = v
    self.first = self.first - 1
end

function Deque:push_back(v)
    self.last = self.last + 1
    self.items[self.last] = v
end

function Deque:pop_front()
    if self.first >= self.last then return nil end
    self.first = self.first + 1
    local v = self.items[self.first]
    self.items[self.first] = nil
    return v
end

function Deque:pop_back()
    if self.first >= self.last then return nil end
    local v = self.items[self.last]
    self.items[self.last] = nil
    self.last = self.last - 1
    return v
end

function Deque:size()
    return self.last - self.first
end

local d = Deque.new()
d:push_back(1); d:push_back(2)
d:push_front(0); d:push_front(-1)
print(d:pop_front(), d:pop_front())  -- -1  0
print(d:pop_back(), d:pop_back())    -- 2  1
```

## 7.6 응용: BFS

큐의 가장 유명한 응용은 **너비 우선 탐색**.

```lua
local graph = {
    A = {"B", "C"},
    B = {"A", "D", "E"},
    C = {"A", "F"},
    D = {"B"}, E = {"B", "F"},
    F = {"C", "E"}
}

local function bfs(start)
    local q = Queue.new()
    local visited = {[start] = true}
    q:enqueue(start)
    while not q:empty() do
        local node = q:dequeue()
        io.write(node, " ")
        for _, neighbor in ipairs(graph[node]) do
            if not visited[neighbor] then
                visited[neighbor] = true
                q:enqueue(neighbor)
            end
        end
    end
    print()
end

bfs("A")  -- A B C D E F
```

## 7.7 응용: 슬라이딩 윈도우 최댓값

덱의 대표적 응용. 시간복잡도 O(n).

```lua
local function sliding_max(arr, k)
    local d = Deque.new()  -- 인덱스를 저장
    local result = {}

    for i = 1, #arr do
        -- 윈도우 밖 인덱스 제거
        if d:size() > 0 and d.items[d.first + 1] <= i - k then
            d:pop_front()
        end
        -- 뒤에서 작은 값들 제거 (단조 감소)
        while d:size() > 0 and arr[d.items[d.last]] < arr[i] do
            d:pop_back()
        end
        d:push_back(i)
        if i >= k then
            table.insert(result, arr[d.items[d.first + 1]])
        end
    end
    return result
end

local arr = {1, 3, -1, -3, 5, 3, 6, 7}
local r = sliding_max(arr, 3)
print(table.concat(r, " "))  -- 3 3 5 5 6 7
```

> 단조 덱 패턴은 한 번 익혀두면 시계열, 주식 차트, 시뮬레이션 등에서 두고두고 쓰인다.

---

# 8. 해시 테이블 (Hash Table)

## 8.1 키-값 매핑

해시 테이블은 키를 통해 값을 즉시 찾을 수 있는 자료구조. 평균 O(1).

Lua의 테이블은 사실 이미 해시 테이블이다.

```lua
local phonebook = {
    ["홍길동"] = "010-1234-5678",
    ["이몽룡"] = "010-2345-6789",
    ["성춘향"] = "010-3456-7890"
}

print(phonebook["홍길동"])  -- 010-1234-5678
phonebook["홍길동"] = nil   -- 삭제
print(phonebook["홍길동"])  -- nil
```

이 장에서는 **밑바닥부터 직접 만들어보며** 동작 원리를 이해한다.

## 8.2 해시 함수

키를 정수 배열 인덱스로 바꾸는 함수. 좋은 해시는:

1. **빠르다** — O(1)에 가깝게
2. **균등하다** — 비슷한 입력도 다른 출력
3. **결정적** — 같은 입력엔 항상 같은 출력

문자열용 간단한 해시 (FNV-1a):

```lua
local FNV_OFFSET = 2166136261
local FNV_PRIME = 16777619

local function hash_string(s, capacity)
    local h = FNV_OFFSET
    for i = 1, #s do
        h = (h ~ s:byte(i)) * FNV_PRIME
        h = h & 0xFFFFFFFF
    end
    return (h % capacity) + 1
end

print(hash_string("hello", 16))  -- 16개 버킷 중 하나
print(hash_string("world", 16))
```

> Lua 5.3+ 의 비트 연산자 `~`(XOR), `&`(AND)를 사용한다. Lua 5.1/5.2에선 `bit32` 라이브러리 필요.

## 8.3 체이닝 방식 해시 테이블

각 버킷이 연결 리스트를 가져 충돌을 처리.

```lua
-- hash_table.lua
local HashTable = {}
HashTable.__index = HashTable

function HashTable.new(capacity)
    capacity = capacity or 16
    local buckets = {}
    for i = 1, capacity do buckets[i] = {} end
    return setmetatable({
        buckets = buckets,
        capacity = capacity,
        size = 0
    }, HashTable)
end

function HashTable:_hash(key)
    return hash_string(tostring(key), self.capacity)
end

function HashTable:set(key, value)
    local idx = self:_hash(key)
    local bucket = self.buckets[idx]
    for _, pair in ipairs(bucket) do
        if pair[1] == key then
            pair[2] = value
            return
        end
    end
    table.insert(bucket, {key, value})
    self.size = self.size + 1

    if self.size > self.capacity * 0.75 then
        self:_resize(self.capacity * 2)
    end
end

function HashTable:get(key)
    local idx = self:_hash(key)
    for _, pair in ipairs(self.buckets[idx]) do
        if pair[1] == key then return pair[2] end
    end
    return nil
end

function HashTable:remove(key)
    local idx = self:_hash(key)
    local bucket = self.buckets[idx]
    for i, pair in ipairs(bucket) do
        if pair[1] == key then
            table.remove(bucket, i)
            self.size = self.size - 1
            return true
        end
    end
    return false
end

function HashTable:_resize(new_capacity)
    local old = self.buckets
    local new_buckets = {}
    for i = 1, new_capacity do new_buckets[i] = {} end
    self.buckets = new_buckets
    self.capacity = new_capacity
    self.size = 0
    for _, bucket in ipairs(old) do
        for _, pair in ipairs(bucket) do
            self:set(pair[1], pair[2])
        end
    end
end

-- 테스트
local h = HashTable.new(4)
h:set("apple", 1)
h:set("banana", 2)
h:set("cherry", 3)
h:set("date", 4)
h:set("elderberry", 5)  -- 리사이즈 트리거

print(h:get("banana"))      -- 2
print(h:get("missing"))     -- nil
h:remove("apple")
print(h:get("apple"))       -- nil
print(h.capacity)           -- 8
```

## 8.4 개방 주소법 (선형 탐사)

체이닝 대신, 충돌 시 다음 빈 자리로 이동하는 방식.

```lua
local OpenHash = {}
OpenHash.__index = OpenHash

function OpenHash.new(cap)
    cap = cap or 16
    return setmetatable({
        keys = {}, values = {},
        capacity = cap, size = 0
    }, OpenHash)
end

function OpenHash:_probe(key)
    local idx = hash_string(tostring(key), self.capacity)
    while self.keys[idx] and self.keys[idx] ~= key do
        idx = (idx % self.capacity) + 1
    end
    return idx
end

function OpenHash:set(key, value)
    if self.size >= self.capacity * 0.5 then
        self:_resize(self.capacity * 2)
    end
    local idx = self:_probe(key)
    if not self.keys[idx] then
        self.size = self.size + 1
    end
    self.keys[idx] = key
    self.values[idx] = value
end

function OpenHash:get(key)
    local idx = self:_probe(key)
    return self.values[idx]
end

function OpenHash:_resize(new_cap)
    local old_keys, old_vals = self.keys, self.values
    self.keys, self.values = {}, {}
    self.capacity, self.size = new_cap, 0
    for i, k in pairs(old_keys) do
        self:set(k, old_vals[i])
    end
end

local oh = OpenHash.new(8)
oh:set("a", 1); oh:set("b", 2); oh:set("c", 3)
print(oh:get("b"))  -- 2
```

> 개방 주소법은 캐시 친화적이고 메모리 할당이 적지만, **삭제가 까다롭다** (tombstone 필요). 학습용으로는 체이닝이 직관적이다.

## 8.5 해시 테이블 응용

### 두 수의 합 (Two Sum)

```lua
local function two_sum(nums, target)
    local seen = {}
    for i, n in ipairs(nums) do
        local need = target - n
        if seen[need] then
            return {seen[need], i}
        end
        seen[n] = i
    end
    return nil
end

local r = two_sum({2, 7, 11, 15}, 9)
print(r[1], r[2])  -- 1  2
```

O(n)으로 풀린다. 정렬 없이 한 번만 훑어도 되는 강력한 패턴.

### 빈도수 세기

```lua
local function counter(arr)
    local c = {}
    for _, v in ipairs(arr) do
        c[v] = (c[v] or 0) + 1
    end
    return c
end

local c = counter({"a", "b", "a", "c", "b", "a"})
for k, v in pairs(c) do print(k, v) end
-- a 3
-- b 2
-- c 1
```

### 그룹화

```lua
local people = {
    {name="alice", team="A"},
    {name="bob", team="B"},
    {name="carol", team="A"},
    {name="dave", team="B"}
}

local function group_by(arr, keyfn)
    local g = {}
    for _, item in ipairs(arr) do
        local k = keyfn(item)
        g[k] = g[k] or {}
        table.insert(g[k], item)
    end
    return g
end

local by_team = group_by(people, function(p) return p.team end)
for team, members in pairs(by_team) do
    io.write(team, ": ")
    for _, m in ipairs(members) do io.write(m.name, " ") end
    print()
end
```

## 8.6 해시 테이블 함정

**1) 해시 충돌 공격:** 신뢰할 수 없는 입력으로 해시 키를 만들면 모두 같은 버킷에 몰릴 수 있다(O(n²) 공격). 외부 입력엔 randomized seed 사용.

**2) 부동소수점 키:** `0.1 + 0.2 ~= 0.3` 같은 문제로 키 검색이 실패할 수 있다. 부동소수는 키로 쓰지 말자.

**3) 변경 가능한 키:** 키로 쓴 테이블의 내용을 바꾸면 해시가 어긋난다. 사실상 잃어버린다.

**4) 순서 가정:** Lua 테이블의 `pairs` 순서는 **정의되지 않는다.** 순서가 필요하면 별도로 정렬하거나 LinkedHashMap을 만들어야 한다.

---

# 9. 집합 (Set)

## 9.1 중복 없는 컬렉션

집합은 **중복 없는 원소들의 모음**. 순서는 없다.

핵심 연산: 추가, 제거, 포함 여부 확인. 모두 평균 O(1).

## 9.2 Lua에서 Set은 테이블 한 줄

```lua
local s = {}
s["apple"] = true
s["banana"] = true
s["apple"] = true  -- 이미 있음. 그래도 OK

-- 포함?
if s["apple"] then print("있음") end

-- 제거
s["apple"] = nil

-- 순회
for k in pairs(s) do print(k) end
```

이게 끝이다. 하지만 학습용으로 정리된 클래스를 만들어보자.

## 9.3 Set 클래스

```lua
-- set.lua
local Set = {}
Set.__index = Set

function Set.new(items)
    local s = setmetatable({_data = {}, _size = 0}, Set)
    if items then
        for _, v in ipairs(items) do s:add(v) end
    end
    return s
end

function Set:add(v)
    if not self._data[v] then
        self._data[v] = true
        self._size = self._size + 1
    end
end

function Set:remove(v)
    if self._data[v] then
        self._data[v] = nil
        self._size = self._size - 1
    end
end

function Set:contains(v)
    return self._data[v] == true
end

function Set:size()
    return self._size
end

function Set:items()
    local arr = {}
    for k in pairs(self._data) do table.insert(arr, k) end
    return arr
end

function Set:union(other)
    local r = Set.new()
    for k in pairs(self._data) do r:add(k) end
    for k in pairs(other._data) do r:add(k) end
    return r
end

function Set:intersect(other)
    local r = Set.new()
    for k in pairs(self._data) do
        if other:contains(k) then r:add(k) end
    end
    return r
end

function Set:difference(other)
    local r = Set.new()
    for k in pairs(self._data) do
        if not other:contains(k) then r:add(k) end
    end
    return r
end

function Set:is_subset(other)
    for k in pairs(self._data) do
        if not other:contains(k) then return false end
    end
    return true
end

function Set:__tostring()
    local arr = self:items()
    table.sort(arr, function(a, b) return tostring(a) < tostring(b) end)
    return "{" .. table.concat(arr, ", ") .. "}"
end

-- 테스트
local A = Set.new({1, 2, 3, 4})
local B = Set.new({3, 4, 5, 6})

print("A =", tostring(A))
print("B =", tostring(B))
print("A ∪ B =", tostring(A:union(B)))         -- {1, 2, 3, 4, 5, 6}
print("A ∩ B =", tostring(A:intersect(B)))     -- {3, 4}
print("A - B =", tostring(A:difference(B)))    -- {1, 2}
print(Set.new({1, 2}):is_subset(A))            -- true
```

## 9.4 응용: 중복 제거

```lua
local function dedupe(arr)
    local s, result = {}, {}
    for _, v in ipairs(arr) do
        if not s[v] then
            s[v] = true
            table.insert(result, v)
        end
    end
    return result
end

local r = dedupe({1, 2, 2, 3, 1, 4, 3, 5})
print(table.concat(r, " "))  -- 1 2 3 4 5
```

## 9.5 응용: 두 리스트의 공통 원소

```lua
local function common(a, b)
    local sa = {}
    for _, v in ipairs(a) do sa[v] = true end
    local r = {}
    for _, v in ipairs(b) do
        if sa[v] then table.insert(r, v) end
    end
    return r
end

print(table.concat(common({1,2,3,4}, {3,4,5,6}), " "))  -- 3 4
```

## 9.6 다중집합 (Multiset / Bag)

같은 원소가 여러 개 있을 수 있는 변형.

```lua
local Multiset = {}
Multiset.__index = Multiset

function Multiset.new()
    return setmetatable({_data = {}}, Multiset)
end

function Multiset:add(v, count)
    count = count or 1
    self._data[v] = (self._data[v] or 0) + count
end

function Multiset:remove(v)
    local c = self._data[v]
    if not c then return false end
    if c <= 1 then self._data[v] = nil
    else self._data[v] = c - 1 end
    return true
end

function Multiset:count(v)
    return self._data[v] or 0
end

local m = Multiset.new()
m:add("apple", 3); m:add("banana"); m:add("apple")
print(m:count("apple"))   -- 4
m:remove("apple")
print(m:count("apple"))   -- 3
```

---

# 10. 트리와 이진 탐색 트리

## 10.1 트리란

트리는 **계층적 자료구조**. 노드들이 부모-자식 관계로 연결된다. 사이클 없는 그래프의 특수형.

용어:
- **루트(root):** 최상위 노드
- **리프(leaf):** 자식이 없는 노드
- **자식/부모/형제(child/parent/sibling):** 인접 관계
- **깊이(depth):** 루트로부터의 거리
- **높이(height):** 가장 깊은 리프까지의 거리

## 10.2 일반 트리

```lua
local function node(value, ...)
    return {value = value, children = {...}}
end

local tree = node("root",
    node("A",
        node("A1"),
        node("A2")),
    node("B",
        node("B1",
            node("B1a"))),
    node("C"))

-- 전위 순회 (preorder)
local function preorder(t, depth)
    depth = depth or 0
    print(string.rep("  ", depth) .. t.value)
    for _, c in ipairs(t.children) do
        preorder(c, depth + 1)
    end
end

preorder(tree)
-- root
--   A
--     A1
--     A2
--   B
--     B1
--       B1a
--   C
```

## 10.3 이진 트리 (Binary Tree)

각 노드가 **최대 2개의 자식** (left/right)을 가지는 트리.

```lua
local function bnode(v, l, r)
    return {value = v, left = l, right = r}
end

--          1
--         / \
--        2   3
--       / \   \
--      4   5   6
local tree = bnode(1,
    bnode(2, bnode(4), bnode(5)),
    bnode(3, nil, bnode(6)))
```

### 세 가지 순회

```lua
-- 전위 (Preorder): 노드 → 왼쪽 → 오른쪽
local function pre(t)
    if not t then return end
    io.write(t.value, " ")
    pre(t.left); pre(t.right)
end

-- 중위 (Inorder): 왼쪽 → 노드 → 오른쪽
local function ino(t)
    if not t then return end
    ino(t.left)
    io.write(t.value, " ")
    ino(t.right)
end

-- 후위 (Postorder): 왼쪽 → 오른쪽 → 노드
local function post(t)
    if not t then return end
    post(t.left); post(t.right)
    io.write(t.value, " ")
end

io.write("Pre:  "); pre(tree); print()    -- 1 2 4 5 3 6
io.write("In:   "); ino(tree); print()    -- 4 2 5 1 3 6
io.write("Post: "); post(tree); print()   -- 4 5 2 6 3 1
```

### 레벨 순회 (BFS)

```lua
local function level_order(t)
    if not t then return end
    local q = Queue.new()
    q:enqueue(t)
    while not q:empty() do
        local n = q:dequeue()
        io.write(n.value, " ")
        if n.left then q:enqueue(n.left) end
        if n.right then q:enqueue(n.right) end
    end
    print()
end

level_order(tree)  -- 1 2 3 4 5 6
```

## 10.4 이진 탐색 트리 (BST)

이진 트리에 **순서 제약**을 추가:
- 왼쪽 서브트리의 모든 값 < 노드 < 오른쪽 서브트리의 모든 값

이 규칙 덕에 검색이 O(log n) (균형 잡혔을 때).

```lua
-- bst.lua
local BST = {}
BST.__index = BST

function BST.new()
    return setmetatable({root = nil, size = 0}, BST)
end

local function insert_node(node, v)
    if not node then return {value = v, left = nil, right = nil} end
    if v < node.value then
        node.left = insert_node(node.left, v)
    elseif v > node.value then
        node.right = insert_node(node.right, v)
    end
    return node
end

function BST:insert(v)
    self.root = insert_node(self.root, v)
    self.size = self.size + 1
end

function BST:contains(v)
    local cur = self.root
    while cur do
        if v == cur.value then return true
        elseif v < cur.value then cur = cur.left
        else cur = cur.right end
    end
    return false
end

function BST:min()
    local cur = self.root
    if not cur then return nil end
    while cur.left do cur = cur.left end
    return cur.value
end

function BST:max()
    local cur = self.root
    if not cur then return nil end
    while cur.right do cur = cur.right end
    return cur.value
end

local function remove_node(node, v)
    if not node then return nil end
    if v < node.value then
        node.left = remove_node(node.left, v)
    elseif v > node.value then
        node.right = remove_node(node.right, v)
    else
        -- 자식 0/1개
        if not node.left then return node.right end
        if not node.right then return node.left end
        -- 자식 2개: 오른쪽 서브트리의 최솟값으로 대체
        local succ = node.right
        while succ.left do succ = succ.left end
        node.value = succ.value
        node.right = remove_node(node.right, succ.value)
    end
    return node
end

function BST:remove(v)
    self.root = remove_node(self.root, v)
end

function BST:inorder()
    local result = {}
    local function walk(n)
        if not n then return end
        walk(n.left)
        table.insert(result, n.value)
        walk(n.right)
    end
    walk(self.root)
    return result
end

-- 테스트
local b = BST.new()
for _, v in ipairs({5, 3, 8, 1, 4, 7, 9, 2}) do b:insert(v) end
print(table.concat(b:inorder(), " "))  -- 1 2 3 4 5 7 8 9 (자동 정렬!)
print(b:contains(7))                    -- true
print(b:min(), b:max())                 -- 1  9
b:remove(5)
print(table.concat(b:inorder(), " "))  -- 1 2 3 4 7 8 9
```

## 10.5 BST의 함정: 균형

데이터가 정렬되어 들어오면 BST는 연결 리스트가 된다.

```lua
local b = BST.new()
for i = 1, 10 do b:insert(i) end
-- 트리 모양: 1 → 2 → 3 → ... → 10
-- 검색이 O(n)이 되어버린다.
```

해결: **자가 균형 트리** (AVL, Red-Black, Treap 등). 다음 절은 그중 가장 단순한 AVL.

## 10.6 AVL 트리

각 노드의 왼쪽/오른쪽 서브트리 높이 차가 최대 1이 되도록 회전(rotation)으로 자동 조정.

```lua
-- avl.lua
local AVL = {}
AVL.__index = AVL

function AVL.new()
    return setmetatable({root = nil}, AVL)
end

local function height(n) return n and n.height or 0 end
local function update(n) n.height = 1 + math.max(height(n.left), height(n.right)) end
local function balance_factor(n) return height(n.left) - height(n.right) end

local function rotate_right(y)
    local x = y.left
    y.left = x.right
    x.right = y
    update(y); update(x)
    return x
end

local function rotate_left(x)
    local y = x.right
    x.right = y.left
    y.left = x
    update(x); update(y)
    return y
end

local function balance(n)
    update(n)
    local bf = balance_factor(n)
    if bf > 1 then
        if balance_factor(n.left) < 0 then
            n.left = rotate_left(n.left)
        end
        return rotate_right(n)
    end
    if bf < -1 then
        if balance_factor(n.right) > 0 then
            n.right = rotate_right(n.right)
        end
        return rotate_left(n)
    end
    return n
end

local function avl_insert(n, v)
    if not n then return {value = v, left = nil, right = nil, height = 1} end
    if v < n.value then n.left = avl_insert(n.left, v)
    elseif v > n.value then n.right = avl_insert(n.right, v)
    else return n end
    return balance(n)
end

function AVL:insert(v) self.root = avl_insert(self.root, v) end

function AVL:height() return height(self.root) end

function AVL:inorder()
    local r = {}
    local function w(n)
        if not n then return end
        w(n.left); table.insert(r, n.value); w(n.right)
    end
    w(self.root)
    return r
end

-- 테스트: 정렬된 데이터에도 균형 잡힘
local a = AVL.new()
for i = 1, 15 do a:insert(i) end
print("AVL height:", a:height())  -- 4 (log2 15 ≈ 4)

local b = BST.new()
for i = 1, 15 do b:insert(i) end
-- BST는 일반 BST라 한 줄짜리 트리... 높이 15
```

## 10.7 트리 알고리즘 모음

### 트리 높이

```lua
local function tree_height(n)
    if not n then return 0 end
    return 1 + math.max(tree_height(n.left), tree_height(n.right))
end
```

### 노드 개수

```lua
local function count_nodes(n)
    if not n then return 0 end
    return 1 + count_nodes(n.left) + count_nodes(n.right)
end
```

### 대칭 여부 (거울 트리)

```lua
local function is_symmetric(n)
    local function mirror(a, b)
        if not a and not b then return true end
        if not a or not b then return false end
        return a.value == b.value
            and mirror(a.left, b.right)
            and mirror(a.right, b.left)
        end
    if not n then return true end
    return mirror(n.left, n.right)
end
```

### 최저 공통 조상 (LCA)

```lua
local function lca(n, p, q)
    if not n or n.value == p or n.value == q then return n end
    local l = lca(n.left, p, q)
    local r = lca(n.right, p, q)
    if l and r then return n end
    return l or r
end
```

### 직렬화 / 역직렬화

```lua
local function serialize(n)
    if not n then return "#" end
    return n.value .. "," .. serialize(n.left) .. "," .. serialize(n.right)
end

local function deserialize(s)
    local tokens = {}
    for t in s:gmatch("[^,]+") do table.insert(tokens, t) end
    local i = 0
    local function build()
        i = i + 1
        if tokens[i] == "#" then return nil end
        return {
            value = tonumber(tokens[i]) or tokens[i],
            left = build(),
            right = build()
        }
    end
    return build()
end

local s = serialize(tree)
print(s)
local rebuilt = deserialize(s)
io.write("Pre rebuilt: "); pre(rebuilt); print()
```

---

# 11. 힙과 우선순위 큐

## 11.1 힙이란

힙은 **완전 이진 트리** + **힙 속성**:
- **최소 힙(min-heap):** 부모 ≤ 자식
- **최대 힙(max-heap):** 부모 ≥ 자식

루트엔 항상 최소(또는 최대)값. 우선순위 큐 구현의 표준.

## 11.2 배열로 표현하기

완전 이진 트리는 배열로 표현하면 포인터가 필요 없다.

```
인덱스(1-based):
부모(i)   = i / 2
왼쪽(i)  = 2i
오른쪽(i) = 2i + 1
```

```lua
-- min_heap.lua
local MinHeap = {}
MinHeap.__index = MinHeap

function MinHeap.new()
    return setmetatable({items = {}, n = 0}, MinHeap)
end

function MinHeap:_swap(i, j)
    self.items[i], self.items[j] = self.items[j], self.items[i]
end

function MinHeap:_sift_up(i)
    while i > 1 do
        local p = i // 2
        if self.items[i] < self.items[p] then
            self:_swap(i, p)
            i = p
        else
            break
        end
    end
end

function MinHeap:_sift_down(i)
    while true do
        local l, r = 2*i, 2*i+1
        local smallest = i
        if l <= self.n and self.items[l] < self.items[smallest] then smallest = l end
        if r <= self.n and self.items[r] < self.items[smallest] then smallest = r end
        if smallest == i then break end
        self:_swap(i, smallest)
        i = smallest
    end
end

function MinHeap:push(v)
    self.n = self.n + 1
    self.items[self.n] = v
    self:_sift_up(self.n)
end

function MinHeap:pop()
    if self.n == 0 then return nil end
    local top = self.items[1]
    self.items[1] = self.items[self.n]
    self.items[self.n] = nil
    self.n = self.n - 1
    if self.n > 0 then self:_sift_down(1) end
    return top
end

function MinHeap:peek()
    return self.items[1]
end

function MinHeap:size() return self.n end

-- 테스트
local h = MinHeap.new()
for _, v in ipairs({5, 3, 8, 1, 9, 2, 7}) do h:push(v) end
local sorted = {}
while h:size() > 0 do table.insert(sorted, h:pop()) end
print(table.concat(sorted, " "))  -- 1 2 3 5 7 8 9
```

push/pop 모두 O(log n).

## 11.3 일반화: 비교 함수와 우선순위 큐

```lua
local PQ = {}
PQ.__index = PQ

function PQ.new(cmp)
    return setmetatable({
        items = {}, n = 0,
        cmp = cmp or function(a, b) return a < b end
    }, PQ)
end

function PQ:_sift_up(i)
    while i > 1 do
        local p = i // 2
        if self.cmp(self.items[i], self.items[p]) then
            self.items[i], self.items[p] = self.items[p], self.items[i]
            i = p
        else break end
    end
end

function PQ:_sift_down(i)
    while true do
        local l, r = 2*i, 2*i+1
        local best = i
        if l <= self.n and self.cmp(self.items[l], self.items[best]) then best = l end
        if r <= self.n and self.cmp(self.items[r], self.items[best]) then best = r end
        if best == i then break end
        self.items[i], self.items[best] = self.items[best], self.items[i]
        i = best
    end
end

function PQ:push(v)
    self.n = self.n + 1
    self.items[self.n] = v
    self:_sift_up(self.n)
end

function PQ:pop()
    if self.n == 0 then return nil end
    local top = self.items[1]
    self.items[1] = self.items[self.n]
    self.items[self.n] = nil
    self.n = self.n - 1
    if self.n > 0 then self:_sift_down(1) end
    return top
end

function PQ:size() return self.n end

-- 작업 우선순위 큐 (낮은 priority가 먼저)
local jobs = PQ.new(function(a, b) return a.priority < b.priority end)
jobs:push({name = "report", priority = 3})
jobs:push({name = "deploy", priority = 1})
jobs:push({name = "lunch", priority = 5})
jobs:push({name = "fix bug", priority = 2})

while jobs:size() > 0 do
    local j = jobs:pop()
    print(j.priority, j.name)
end
-- 1   deploy
-- 2   fix bug
-- 3   report
-- 5   lunch
```

## 11.4 힙 정렬

힙으로 정렬하기.

```lua
local function heap_sort(arr)
    local h = MinHeap.new()
    for _, v in ipairs(arr) do h:push(v) end
    for i = 1, #arr do arr[i] = h:pop() end
    return arr
end

print(table.concat(heap_sort({5, 2, 8, 1, 9, 3}), " "))  -- 1 2 3 5 8 9
```

시간복잡도 O(n log n), 공간 O(n).

> in-place 힙 정렬도 가능하지만 코드가 길다. 학습용으론 위 버전이 명확하다.

## 11.5 응용: 상위 K개

```lua
-- 가장 큰 K개를 효율적으로
local function top_k(arr, k)
    local h = PQ.new(function(a, b) return a < b end)  -- min-heap
    for _, v in ipairs(arr) do
        if h:size() < k then
            h:push(v)
        elseif v > h.items[1] then
            h:pop()
            h:push(v)
        end
    end
    local r = {}
    while h:size() > 0 do table.insert(r, 1, h:pop()) end
    return r
end

print(table.concat(top_k({3, 1, 4, 1, 5, 9, 2, 6, 5, 3}, 3), " "))
-- 5 6 9
```

힙 크기를 k로 유지하면서 작은 값을 버린다. O(n log k).

## 11.6 응용: K개 정렬된 리스트 병합

```lua
local function merge_k(lists)
    local pq = PQ.new(function(a, b) return a.value < b.value end)
    for i, list in ipairs(lists) do
        if #list > 0 then
            pq:push({value = list[1], list = list, idx = 1})
        end
    end
    local result = {}
    while pq:size() > 0 do
        local top = pq:pop()
        table.insert(result, top.value)
        if top.idx < #top.list then
            pq:push({value = top.list[top.idx+1], list = top.list, idx = top.idx+1})
        end
    end
    return result
end

local r = merge_k({{1,4,7}, {2,5,8}, {3,6,9}})
print(table.concat(r, " "))  -- 1 2 3 4 5 6 7 8 9
```

K개 리스트를 O(n log k)에 병합.

## 11.7 응용: 작업 스케줄러

```lua
local function scheduler()
    local s = {time = 0, pq = PQ.new(function(a, b) return a.deadline < b.deadline end)}

    function s:schedule(name, delay)
        self.pq:push({name = name, deadline = self.time + delay})
    end

    function s:tick()
        self.time = self.time + 1
        while self.pq:size() > 0 and self.pq.items[1].deadline <= self.time do
            local job = self.pq:pop()
            print(string.format("[t=%d] running %s", self.time, job.name))
        end
    end

    return s
end

local s = scheduler()
s:schedule("backup", 3)
s:schedule("report", 1)
s:schedule("ping", 2)
for _ = 1, 5 do s:tick() end
-- [t=1] running report
-- [t=2] running ping
-- [t=3] running backup
```

---

# 12. 그래프 (Graph)

## 12.1 그래프란

노드(vertex)와 간선(edge)으로 이뤄진 자료구조. 트리는 사이클 없는 연결 그래프의 특수형이다.

분류:
- **방향(directed) / 무방향(undirected)**
- **가중치(weighted) / 무가중치(unweighted)**
- **연결(connected) / 비연결**

## 12.2 그래프 표현

### 인접 리스트 (Adjacency List)

가장 흔하다. 각 노드가 인접한 노드 목록을 가진다.

```lua
local graph = {
    A = {"B", "C"},
    B = {"A", "D"},
    C = {"A", "D", "E"},
    D = {"B", "C"},
    E = {"C"}
}
```

가중치 있을 때:

```lua
local wgraph = {
    A = {{"B", 4}, {"C", 2}},
    B = {{"A", 4}, {"D", 5}},
    C = {{"A", 2}, {"D", 8}, {"E", 10}},
    D = {{"B", 5}, {"C", 8}, {"E", 2}},
    E = {{"C", 10}, {"D", 2}}
}
```

### 인접 행렬 (Adjacency Matrix)

|V|×|V| 크기의 2차원 배열. 간선 존재 여부를 O(1)에 확인.

```lua
local nodes = {"A", "B", "C", "D"}
local idx = {A=1, B=2, C=3, D=4}
local matrix = {
    {0, 1, 1, 0},
    {1, 0, 0, 1},
    {1, 0, 0, 1},
    {0, 1, 1, 0}
}
print(matrix[idx.A][idx.B])  -- 1 (연결됨)
```

희소 그래프는 인접 리스트가, 조밀한 그래프는 인접 행렬이 유리.

## 12.3 Graph 클래스

```lua
-- graph.lua
local Graph = {}
Graph.__index = Graph

function Graph.new(directed)
    return setmetatable({
        adj = {},
        directed = directed or false,
        nodes = {}
    }, Graph)
end

function Graph:add_node(n)
    if not self.adj[n] then
        self.adj[n] = {}
        table.insert(self.nodes, n)
    end
end

function Graph:add_edge(u, v, w)
    w = w or 1
    self:add_node(u); self:add_node(v)
    table.insert(self.adj[u], {v, w})
    if not self.directed then
        table.insert(self.adj[v], {u, w})
    end
end

function Graph:neighbors(n)
    return self.adj[n] or {}
end

function Graph:print()
    for _, n in ipairs(self.nodes) do
        io.write(n, ": ")
        for _, e in ipairs(self.adj[n]) do
            io.write(string.format("(%s,%s) ", e[1], e[2]))
        end
        print()
    end
end

local g = Graph.new(false)
g:add_edge("A", "B", 1)
g:add_edge("A", "C", 4)
g:add_edge("B", "C", 2)
g:add_edge("B", "D", 5)
g:add_edge("C", "D", 1)
g:print()
```

## 12.4 BFS (너비 우선 탐색)

```lua
function Graph:bfs(start)
    local q = Queue.new()
    local visited = {[start] = true}
    local order = {}
    q:enqueue(start)
    while not q:empty() do
        local n = q:dequeue()
        table.insert(order, n)
        for _, e in ipairs(self.adj[n]) do
            local nb = e[1]
            if not visited[nb] then
                visited[nb] = true
                q:enqueue(nb)
            end
        end
    end
    return order
end

print(table.concat(g:bfs("A"), " "))
```

## 12.5 DFS (깊이 우선 탐색)

재귀 버전:

```lua
function Graph:dfs(start)
    local visited, order = {}, {}
    local function visit(n)
        if visited[n] then return end
        visited[n] = true
        table.insert(order, n)
        for _, e in ipairs(self.adj[n]) do visit(e[1]) end
    end
    visit(start)
    return order
end
```

스택 버전 (재귀 깊이 우려가 있을 때):

```lua
function Graph:dfs_iter(start)
    local stack = Stack.new()
    local visited, order = {}, {}
    stack:push(start)
    while not stack:empty() do
        local n = stack:pop()
        if not visited[n] then
            visited[n] = true
            table.insert(order, n)
            for _, e in ipairs(self.adj[n]) do
                if not visited[e[1]] then stack:push(e[1]) end
            end
        end
    end
    return order
end
```

## 12.6 최단 경로 — Dijkstra

비음수 가중치 그래프의 단일 출발점 최단 경로. O((V+E) log V).

```lua
function Graph:dijkstra(start)
    local dist, prev = {}, {}
    for _, n in ipairs(self.nodes) do dist[n] = math.huge end
    dist[start] = 0

    local pq = PQ.new(function(a, b) return a[2] < b[2] end)
    pq:push({start, 0})

    while pq:size() > 0 do
        local top = pq:pop()
        local u, d = top[1], top[2]
        if d <= dist[u] then
            for _, e in ipairs(self.adj[u]) do
                local v, w = e[1], e[2]
                local alt = d + w
                if alt < dist[v] then
                    dist[v] = alt
                    prev[v] = u
                    pq:push({v, alt})
                end
            end
        end
    end
    return dist, prev
end

local function path(prev, target)
    local p = {}
    while target do
        table.insert(p, 1, target)
        target = prev[target]
    end
    return p
end

local g2 = Graph.new(false)
g2:add_edge("A", "B", 4)
g2:add_edge("A", "C", 2)
g2:add_edge("B", "C", 1)
g2:add_edge("B", "D", 5)
g2:add_edge("C", "D", 8)
g2:add_edge("C", "E", 10)
g2:add_edge("D", "E", 2)

local dist, prev = g2:dijkstra("A")
for _, n in ipairs(g2.nodes) do
    print(n, dist[n], table.concat(path(prev, n), "->"))
end
-- A   0    A
-- B   3    A->C->B
-- C   2    A->C
-- D   8    A->C->B->D
-- E   10   A->C->B->D->E
```

## 12.7 Bellman-Ford (음수 가중치 허용)

음수 간선까지 처리. O(VE). 음수 사이클도 검출.

```lua
function Graph:bellman_ford(start)
    local dist, prev = {}, {}
    for _, n in ipairs(self.nodes) do dist[n] = math.huge end
    dist[start] = 0

    -- 모든 간선 수집
    local edges = {}
    for u, neigh in pairs(self.adj) do
        for _, e in ipairs(neigh) do
            table.insert(edges, {u, e[1], e[2]})
        end
    end

    for _ = 1, #self.nodes - 1 do
        for _, e in ipairs(edges) do
            local u, v, w = e[1], e[2], e[3]
            if dist[u] + w < dist[v] then
                dist[v] = dist[u] + w
                prev[v] = u
            end
        end
    end

    -- 음수 사이클 검사
    for _, e in ipairs(edges) do
        if dist[e[1]] + e[3] < dist[e[2]] then
            return nil, nil, "negative cycle"
        end
    end
    return dist, prev
end
```

## 12.8 위상 정렬 (Topological Sort)

DAG에서 선행 관계를 만족하는 순서. 의존성 해결, 빌드 시스템에 쓰임.

```lua
function Graph:topological_sort()
    local indegree = {}
    for _, n in ipairs(self.nodes) do indegree[n] = 0 end
    for u, neigh in pairs(self.adj) do
        for _, e in ipairs(neigh) do
            indegree[e[1]] = indegree[e[1]] + 1
        end
    end

    local q = Queue.new()
    for _, n in ipairs(self.nodes) do
        if indegree[n] == 0 then q:enqueue(n) end
    end

    local order = {}
    while not q:empty() do
        local u = q:dequeue()
        table.insert(order, u)
        for _, e in ipairs(self.adj[u]) do
            indegree[e[1]] = indegree[e[1]] - 1
            if indegree[e[1]] == 0 then q:enqueue(e[1]) end
        end
    end

    if #order ~= #self.nodes then return nil, "cycle detected" end
    return order
end

local dag = Graph.new(true)
dag:add_edge("코드작성", "테스트")
dag:add_edge("테스트", "리뷰")
dag:add_edge("리뷰", "배포")
dag:add_edge("문서작성", "리뷰")
dag:add_edge("코드작성", "문서작성")

local order = dag:topological_sort()
print(table.concat(order, " -> "))
-- 코드작성 -> 문서작성 -> 테스트 -> 리뷰 -> 배포
-- (출력 순서는 큐 동작에 따라 다를 수 있음)
```

## 12.9 사이클 검출

```lua
function Graph:has_cycle_undirected()
    local visited = {}
    local function dfs(u, parent)
        visited[u] = true
        for _, e in ipairs(self.adj[u]) do
            local v = e[1]
            if not visited[v] then
                if dfs(v, u) then return true end
            elseif v ~= parent then
                return true
            end
        end
        return false
    end
    for _, n in ipairs(self.nodes) do
        if not visited[n] then
            if dfs(n, nil) then return true end
        end
    end
    return false
end
```

## 12.10 연결 요소 (Connected Components)

```lua
function Graph:connected_components()
    local visited, comps = {}, {}
    local function dfs(start)
        local comp = {}
        local stack = Stack.new()
        stack:push(start)
        while not stack:empty() do
            local u = stack:pop()
            if not visited[u] then
                visited[u] = true
                table.insert(comp, u)
                for _, e in ipairs(self.adj[u]) do
                    if not visited[e[1]] then stack:push(e[1]) end
                end
            end
        end
        return comp
    end
    for _, n in ipairs(self.nodes) do
        if not visited[n] then
            table.insert(comps, dfs(n))
        end
    end
    return comps
end

local g3 = Graph.new(false)
g3:add_edge(1, 2); g3:add_edge(2, 3)
g3:add_edge(4, 5)
g3:add_node(6)

for i, comp in ipairs(g3:connected_components()) do
    print("Component "..i..": "..table.concat(comp, ","))
end
-- Component 1: 1,2,3
-- Component 2: 4,5
-- Component 3: 6
```

## 12.11 최소 신장 트리 (MST) — Kruskal

모든 노드를 잇는 최소 비용 간선 집합. Kruskal은 유니온 파인드를 쓴다 (14장).

```lua
-- 간단 버전 (UnionFind는 14장에서)
function Graph:kruskal_mst()
    local edges = {}
    local seen = {}
    for u, neigh in pairs(self.adj) do
        for _, e in ipairs(neigh) do
            local key = u < e[1] and (u..","..e[1]) or (e[1]..","..u)
            if not seen[key] then
                seen[key] = true
                table.insert(edges, {u, e[1], e[2]})
            end
        end
    end
    table.sort(edges, function(a, b) return a[3] < b[3] end)

    local uf = UnionFind.new(self.nodes)
    local mst, cost = {}, 0
    for _, e in ipairs(edges) do
        if uf:find(e[1]) ~= uf:find(e[2]) then
            uf:union(e[1], e[2])
            table.insert(mst, e)
            cost = cost + e[3]
        end
    end
    return mst, cost
end
```

UnionFind는 14장에서 정의한다.

---

# 13. 트라이 (Trie)

## 13.1 트라이란

문자열 검색용 트리. 각 노드가 한 글자를 표현하고, 루트→리프 경로가 하나의 단어가 된다.

장점: 접두사 검색이 매우 빠름 — O(접두사 길이).

응용: 자동완성, 사전, IP 라우팅 테이블, 스펠 체커.

## 13.2 구현

```lua
-- trie.lua
local Trie = {}
Trie.__index = Trie

function Trie.new()
    return setmetatable({root = {children = {}, is_end = false}}, Trie)
end

function Trie:insert(word)
    local node = self.root
    for i = 1, #word do
        local c = word:sub(i, i)
        if not node.children[c] then
            node.children[c] = {children = {}, is_end = false}
        end
        node = node.children[c]
    end
    node.is_end = true
end

function Trie:contains(word)
    local node = self.root
    for i = 1, #word do
        local c = word:sub(i, i)
        node = node.children[c]
        if not node then return false end
    end
    return node.is_end
end

function Trie:starts_with(prefix)
    local node = self.root
    for i = 1, #prefix do
        local c = prefix:sub(i, i)
        node = node.children[c]
        if not node then return false end
    end
    return true
end

function Trie:autocomplete(prefix)
    local node = self.root
    for i = 1, #prefix do
        local c = prefix:sub(i, i)
        node = node.children[c]
        if not node then return {} end
    end
    local result = {}
    local function dfs(n, path)
        if n.is_end then table.insert(result, path) end
        for c, child in pairs(n.children) do
            dfs(child, path .. c)
        end
    end
    dfs(node, prefix)
    return result
end

-- 테스트
local t = Trie.new()
for _, w in ipairs({"apple", "app", "application", "apt", "ape", "banana"}) do
    t:insert(w)
end

print(t:contains("app"))         -- true
print(t:contains("ap"))          -- false
print(t:starts_with("ap"))       -- true

local list = t:autocomplete("ap")
table.sort(list)
for _, w in ipairs(list) do print(w) end
-- ape
-- app
-- apple
-- application
-- apt
```

## 13.3 응용: 단어 빈도

```lua
function Trie:insert_with_count(word, cnt)
    cnt = cnt or 1
    local node = self.root
    for i = 1, #word do
        local c = word:sub(i, i)
        node.children[c] = node.children[c] or {children = {}, is_end = false, count = 0}
        node = node.children[c]
    end
    node.is_end = true
    node.count = (node.count or 0) + cnt
end

function Trie:count_of(word)
    local node = self.root
    for i = 1, #word do
        local c = word:sub(i, i)
        node = node.children[c]
        if not node then return 0 end
    end
    return node.is_end and (node.count or 0) or 0
end
```

## 13.4 응용: 가장 긴 공통 접두사

```lua
local function lcp(words)
    if #words == 0 then return "" end
    local t = Trie.new()
    for _, w in ipairs(words) do t:insert(w) end

    local prefix, node = "", t.root
    while true do
        local cnt, only_child = 0, nil
        for c, child in pairs(node.children) do
            cnt = cnt + 1; only_child = {c, child}
        end
        if cnt ~= 1 or node.is_end then break end
        prefix = prefix .. only_child[1]
        node = only_child[2]
    end
    return prefix
end

print(lcp({"flower", "flow", "flight"}))   -- "fl"
print(lcp({"dog", "racecar", "car"}))      -- ""
```

## 13.5 메모리 vs 속도

트라이는 문자별 노드가 필요해 메모리를 많이 쓴다. 메모리 절약 변형으로 **Radix Tree(경로 압축)** 가 있다.

---

# 14. 유니온 파인드 (Union-Find)

## 14.1 서로소 집합

여러 원소를 그룹으로 관리하면서:
- `find(x)`: x가 속한 그룹의 대표(루트)
- `union(x, y)`: x와 y의 그룹을 합침

응용: Kruskal MST, 친구 관계, 네트워크 연결성 판정.

## 14.2 기본 구현

```lua
-- union_find.lua
UnionFind = {}
UnionFind.__index = UnionFind

function UnionFind.new(items)
    local parent, rank = {}, {}
    if items then
        for _, x in ipairs(items) do
            parent[x] = x
            rank[x] = 0
        end
    end
    return setmetatable({parent = parent, rank = rank}, UnionFind)
end

function UnionFind:make(x)
    if self.parent[x] == nil then
        self.parent[x] = x
        self.rank[x] = 0
    end
end

-- 경로 압축 적용
function UnionFind:find(x)
    if self.parent[x] ~= x then
        self.parent[x] = self:find(self.parent[x])
    end
    return self.parent[x]
end

-- 랭크 기반 합치기
function UnionFind:union(x, y)
    local rx, ry = self:find(x), self:find(y)
    if rx == ry then return false end
    if self.rank[rx] < self.rank[ry] then
        self.parent[rx] = ry
    elseif self.rank[rx] > self.rank[ry] then
        self.parent[ry] = rx
    else
        self.parent[ry] = rx
        self.rank[rx] = self.rank[rx] + 1
    end
    return true
end

function UnionFind:connected(x, y)
    return self:find(x) == self:find(y)
end

-- 테스트
local uf = UnionFind.new({1, 2, 3, 4, 5, 6, 7, 8})
uf:union(1, 2)
uf:union(2, 3)
uf:union(4, 5)
uf:union(6, 7)
uf:union(5, 6)

print(uf:connected(1, 3))   -- true
print(uf:connected(4, 7))   -- true
print(uf:connected(1, 4))   -- false
print(uf:connected(8, 1))   -- false
```

경로 압축 + 랭크 합치기를 모두 적용하면 거의 O(1) (실제로는 inverse Ackermann).

## 14.3 응용: 네트워크 연결 쿼리

```lua
local function process_queries(n, queries)
    local uf = UnionFind.new()
    for i = 1, n do uf:make(i) end
    local results = {}
    for _, q in ipairs(queries) do
        if q[1] == "union" then
            uf:union(q[2], q[3])
        else
            table.insert(results, uf:connected(q[2], q[3]))
        end
    end
    return results
end

local r = process_queries(5, {
    {"union", 1, 2},
    {"union", 3, 4},
    {"query", 1, 4},  -- false
    {"union", 2, 3},
    {"query", 1, 4},  -- true
    {"query", 1, 5},  -- false
})
for _, v in ipairs(r) do print(v) end
```

## 14.4 응용: 격자에서 섬의 개수

```lua
local function count_islands(grid)
    local rows, cols = #grid, #grid[1]
    local uf = UnionFind.new()
    for i = 1, rows do
        for j = 1, cols do
            if grid[i][j] == 1 then
                uf:make(i * cols + j)
            end
        end
    end
    local function id(i, j) return i * cols + j end
    for i = 1, rows do
        for j = 1, cols do
            if grid[i][j] == 1 then
                if i+1 <= rows and grid[i+1][j] == 1 then uf:union(id(i,j), id(i+1,j)) end
                if j+1 <= cols and grid[i][j+1] == 1 then uf:union(id(i,j), id(i,j+1)) end
            end
        end
    end
    local roots = {}
    for i = 1, rows do
        for j = 1, cols do
            if grid[i][j] == 1 then
                roots[uf:find(id(i,j))] = true
            end
        end
    end
    local cnt = 0
    for _ in pairs(roots) do cnt = cnt + 1 end
    return cnt
end

local grid = {
    {1,1,0,0,0},
    {1,0,0,1,1},
    {0,0,1,1,0},
    {0,0,0,0,1}
}
print(count_islands(grid))  -- 3
```

---

# 15. 고급 자료구조

## 15.1 LRU 캐시

가장 오래 안 쓴 항목부터 버리는 캐시. 해시 + 이중 연결 리스트 조합으로 O(1) get/put.

```lua
-- lru.lua
local LRU = {}
LRU.__index = LRU

function LRU.new(capacity)
    local self = setmetatable({
        capacity = capacity,
        size = 0,
        map = {},
        head = {prev = nil, next = nil},  -- sentinel
        tail = {prev = nil, next = nil}
    }, LRU)
    self.head.next = self.tail
    self.tail.prev = self.head
    return self
end

function LRU:_remove(node)
    node.prev.next = node.next
    node.next.prev = node.prev
end

function LRU:_add_front(node)
    node.prev = self.head
    node.next = self.head.next
    self.head.next.prev = node
    self.head.next = node
end

function LRU:get(key)
    local node = self.map[key]
    if not node then return nil end
    self:_remove(node)
    self:_add_front(node)
    return node.value
end

function LRU:put(key, value)
    local node = self.map[key]
    if node then
        node.value = value
        self:_remove(node)
        self:_add_front(node)
        return
    end
    node = {key = key, value = value}
    self.map[key] = node
    self:_add_front(node)
    self.size = self.size + 1
    if self.size > self.capacity then
        local victim = self.tail.prev
        self:_remove(victim)
        self.map[victim.key] = nil
        self.size = self.size - 1
    end
end

local cache = LRU.new(3)
cache:put("a", 1); cache:put("b", 2); cache:put("c", 3)
print(cache:get("a"))   -- 1 (a를 최근 사용으로 이동)
cache:put("d", 4)       -- b가 가장 오래됨 → 버려짐
print(cache:get("b"))   -- nil
print(cache:get("c"))   -- 3
print(cache:get("d"))   -- 4
```

웹 캐시, 페이지 교체, 데이터베이스 버퍼풀의 표준 알고리즘.

## 15.2 스킵 리스트 (Skip List)

확률적 자료구조. 정렬된 데이터에서 검색/삽입/삭제가 평균 O(log n).

```lua
-- skiplist.lua
math.randomseed(os.time())

local SkipList = {}
SkipList.__index = SkipList

local MAX_LEVEL = 16
local P = 0.5

local function random_level()
    local lvl = 1
    while math.random() < P and lvl < MAX_LEVEL do
        lvl = lvl + 1
    end
    return lvl
end

function SkipList.new()
    local head = {value = -math.huge, forward = {}}
    for i = 1, MAX_LEVEL do head.forward[i] = nil end
    return setmetatable({head = head, level = 1}, SkipList)
end

function SkipList:insert(v)
    local update = {}
    local x = self.head
    for i = self.level, 1, -1 do
        while x.forward[i] and x.forward[i].value < v do
            x = x.forward[i]
        end
        update[i] = x
    end
    local lvl = random_level()
    if lvl > self.level then
        for i = self.level + 1, lvl do update[i] = self.head end
        self.level = lvl
    end
    local node = {value = v, forward = {}}
    for i = 1, lvl do
        node.forward[i] = update[i].forward[i]
        update[i].forward[i] = node
    end
end

function SkipList:contains(v)
    local x = self.head
    for i = self.level, 1, -1 do
        while x.forward[i] and x.forward[i].value < v do
            x = x.forward[i]
        end
    end
    x = x.forward[1]
    return x and x.value == v
end

function SkipList:print_layer()
    local cur, t = self.head.forward[1], {}
    while cur do
        table.insert(t, tostring(cur.value))
        cur = cur.forward[1]
    end
    print(table.concat(t, " -> "))
end

local sl = SkipList.new()
for _, v in ipairs({3, 6, 7, 9, 12, 19, 17, 26, 21, 25}) do sl:insert(v) end
sl:print_layer()
print(sl:contains(19))   -- true
print(sl:contains(100))  -- false
```

Redis의 sorted set이 스킵 리스트로 만들어졌다.

## 15.3 블룸 필터 (Bloom Filter)

확률적 멤버십 자료구조. **거짓 양성은 가능, 거짓 음성은 불가능.**
공간 효율이 매우 높다.

```lua
-- bloom.lua
local BloomFilter = {}
BloomFilter.__index = BloomFilter

local function hash1(s, m)
    local h = 0
    for i = 1, #s do h = (h * 31 + s:byte(i)) & 0xFFFFFFFF end
    return (h % m) + 1
end

local function hash2(s, m)
    local h = 5381
    for i = 1, #s do h = ((h * 33) + s:byte(i)) & 0xFFFFFFFF end
    return (h % m) + 1
end

local function hash3(s, m)
    local h = 0
    for i = 1, #s do h = ((h * 17) ~ s:byte(i)) & 0xFFFFFFFF end
    return (h % m) + 1
end

function BloomFilter.new(m)
    local bits = {}
    for i = 1, m do bits[i] = 0 end
    return setmetatable({bits = bits, m = m}, BloomFilter)
end

function BloomFilter:add(s)
    self.bits[hash1(s, self.m)] = 1
    self.bits[hash2(s, self.m)] = 1
    self.bits[hash3(s, self.m)] = 1
end

function BloomFilter:contains(s)
    return self.bits[hash1(s, self.m)] == 1
       and self.bits[hash2(s, self.m)] == 1
       and self.bits[hash3(s, self.m)] == 1
end

local bf = BloomFilter.new(100)
for _, w in ipairs({"apple", "banana", "cherry"}) do bf:add(w) end
print(bf:contains("apple"))   -- true
print(bf:contains("banana"))  -- true
print(bf:contains("grape"))   -- false (대부분)
print(bf:contains("xyz123"))  -- false (대부분)
```

스팸 필터, 캐시 효율화, 데이터베이스의 디스크 접근 회피에 활용.

## 15.4 펜윅 트리 (Fenwick Tree / BIT)

배열의 부분합을 O(log n)에 갱신/조회.

```lua
local Fenwick = {}
Fenwick.__index = Fenwick

function Fenwick.new(n)
    local t = {}
    for i = 1, n do t[i] = 0 end
    return setmetatable({tree = t, n = n}, Fenwick)
end

function Fenwick:update(i, delta)
    while i <= self.n do
        self.tree[i] = self.tree[i] + delta
        i = i + (i & -i)
    end
end

function Fenwick:prefix_sum(i)
    local s = 0
    while i > 0 do
        s = s + self.tree[i]
        i = i - (i & -i)
    end
    return s
end

function Fenwick:range_sum(l, r)
    return self:prefix_sum(r) - self:prefix_sum(l - 1)
end

local f = Fenwick.new(10)
for i = 1, 10 do f:update(i, i) end  -- [1,2,...,10]
print(f:prefix_sum(5))    -- 1+2+3+4+5 = 15
print(f:range_sum(3, 7))  -- 3+4+5+6+7 = 25
f:update(5, 100)          -- 5번 인덱스 +100
print(f:range_sum(3, 7))  -- 125
```

## 15.5 세그먼트 트리

펜윅보다 더 일반적이고, 구간 갱신/조회까지 가능.

```lua
local SegTree = {}
SegTree.__index = SegTree

function SegTree.new(arr)
    local n = #arr
    local self = setmetatable({n = n, tree = {}}, SegTree)
    for i = 1, 4*n do self.tree[i] = 0 end
    self:_build(arr, 1, 1, n)
    return self
end

function SegTree:_build(arr, node, l, r)
    if l == r then
        self.tree[node] = arr[l]
        return
    end
    local mid = (l + r) // 2
    self:_build(arr, 2*node, l, mid)
    self:_build(arr, 2*node+1, mid+1, r)
    self.tree[node] = self.tree[2*node] + self.tree[2*node+1]
end

function SegTree:update(i, val)
    self:_update(1, 1, self.n, i, val)
end

function SegTree:_update(node, l, r, i, val)
    if l == r then self.tree[node] = val; return end
    local mid = (l + r) // 2
    if i <= mid then self:_update(2*node, l, mid, i, val)
    else self:_update(2*node+1, mid+1, r, i, val) end
    self.tree[node] = self.tree[2*node] + self.tree[2*node+1]
end

function SegTree:query(ql, qr)
    return self:_query(1, 1, self.n, ql, qr)
end

function SegTree:_query(node, l, r, ql, qr)
    if qr < l or r < ql then return 0 end
    if ql <= l and r <= qr then return self.tree[node] end
    local mid = (l + r) // 2
    return self:_query(2*node, l, mid, ql, qr)
         + self:_query(2*node+1, mid+1, r, ql, qr)
end

local st = SegTree.new({1, 3, 5, 7, 9, 11})
print(st:query(2, 5))  -- 3+5+7+9 = 24
st:update(3, 100)
print(st:query(2, 5))  -- 3+100+7+9 = 119
```

## 15.6 원형 큐 캐시 (Ring Buffer)

7장에서 다뤘지만 다시 한 번, 메시지 큐와 로깅에서의 응용.

```lua
local function ring_logger(capacity)
    local buf, idx, count = {}, 1, 0
    return {
        log = function(msg)
            buf[idx] = string.format("[%d] %s", os.time(), msg)
            idx = (idx % capacity) + 1
            count = math.min(count + 1, capacity)
        end,
        dump = function()
            local start = (count == capacity) and idx or 1
            for i = 0, count - 1 do
                local k = ((start + i - 1) % capacity) + 1
                print(buf[k])
            end
        end
    }
end

local lg = ring_logger(3)
for i = 1, 5 do lg.log("message " .. i) end
lg.dump()
-- 마지막 3개만 남음
```

---

# 16. 실전 응용

## 16.1 단어 횟수 세기 (CountVectorizer 흉내)

```lua
local function tokenize(text)
    local tokens = {}
    for w in text:lower():gmatch("[%w']+") do
        table.insert(tokens, w)
    end
    return tokens
end

local function count_words(docs)
    local counts = {}
    for _, doc in ipairs(docs) do
        for _, w in ipairs(tokenize(doc)) do
            counts[w] = (counts[w] or 0) + 1
        end
    end
    return counts
end

local function top_n(counts, n)
    local arr = {}
    for w, c in pairs(counts) do table.insert(arr, {w, c}) end
    table.sort(arr, function(a, b) return a[2] > b[2] end)
    local r = {}
    for i = 1, math.min(n, #arr) do r[i] = arr[i] end
    return r
end

local docs = {
    "the cat sat on the mat",
    "the dog chased the cat",
    "the dog and the cat played"
}

for _, p in ipairs(top_n(count_words(docs), 5)) do
    print(p[1], p[2])
end
-- the   6
-- cat   3
-- dog   2
-- sat   1
-- on    1
```

## 16.2 미니 데이터베이스 인덱스

해시맵 인덱스로 즉시 조회.

```lua
local DB = {}
DB.__index = DB

function DB.new()
    return setmetatable({rows = {}, indices = {}}, DB)
end

function DB:create_index(field)
    self.indices[field] = {}
    for id, row in pairs(self.rows) do
        local v = row[field]
        self.indices[field][v] = self.indices[field][v] or {}
        table.insert(self.indices[field][v], id)
    end
end

function DB:insert(row)
    local id = #self.rows + 1
    row.id = id
    self.rows[id] = row
    for field, idx in pairs(self.indices) do
        local v = row[field]
        idx[v] = idx[v] or {}
        table.insert(idx[v], id)
    end
    return id
end

function DB:find_by(field, value)
    if self.indices[field] then
        local ids = self.indices[field][value] or {}
        local r = {}
        for _, id in ipairs(ids) do table.insert(r, self.rows[id]) end
        return r
    end
    -- full scan
    local r = {}
    for _, row in pairs(self.rows) do
        if row[field] == value then table.insert(r, row) end
    end
    return r
end

local db = DB.new()
db:create_index("city")
db:insert({name="Alice", city="Seoul", age=30})
db:insert({name="Bob", city="Busan", age=25})
db:insert({name="Carol", city="Seoul", age=35})

for _, row in ipairs(db:find_by("city", "Seoul")) do
    print(row.name, row.age)
end
-- Alice  30
-- Carol  35
```

## 16.3 미로 풀이 (BFS)

```lua
local function solve_maze(maze, start, goal)
    local rows, cols = #maze, #maze[1]
    local q = Queue.new()
    local prev = {}
    local key = function(r, c) return r * 1000 + c end
    q:enqueue(start)
    prev[key(start[1], start[2])] = false
    local dirs = {{0,1},{1,0},{0,-1},{-1,0}}
    while not q:empty() do
        local cur = q:dequeue()
        local r, c = cur[1], cur[2]
        if r == goal[1] and c == goal[2] then
            local path = {{r,c}}
            local k = key(r,c)
            while prev[k] do
                table.insert(path, 1, prev[k])
                k = key(prev[k][1], prev[k][2])
            end
            return path
        end
        for _, d in ipairs(dirs) do
            local nr, nc = r+d[1], c+d[2]
            if nr >= 1 and nr <= rows and nc >= 1 and nc <= cols
               and maze[nr][nc] == 0 and prev[key(nr,nc)] == nil then
                prev[key(nr,nc)] = {r, c}
                q:enqueue({nr, nc})
            end
        end
    end
    return nil
end

local maze = {
    {0,0,1,0,0},
    {0,1,0,0,1},
    {0,0,0,1,0},
    {1,1,0,0,0},
    {0,0,0,1,0}
}

local path = solve_maze(maze, {1,1}, {5,5})
for _, p in ipairs(path) do io.write("("..p[1]..","..p[2]..") ") end
print()
```

## 16.4 자동완성 사전

```lua
local Dict = {}
Dict.__index = Dict

function Dict.new(words)
    local self = setmetatable({trie = Trie.new(), freq = {}}, Dict)
    for _, w in ipairs(words or {}) do self:add(w) end
    return self
end

function Dict:add(word, n)
    n = n or 1
    self.trie:insert(word)
    self.freq[word] = (self.freq[word] or 0) + n
end

function Dict:suggest(prefix, k)
    k = k or 5
    local matches = self.trie:autocomplete(prefix)
    table.sort(matches, function(a, b)
        return (self.freq[a] or 0) > (self.freq[b] or 0)
    end)
    local r = {}
    for i = 1, math.min(k, #matches) do r[i] = matches[i] end
    return r
end

local d = Dict.new()
d:add("apple", 100); d:add("apply", 50); d:add("app", 200)
d:add("application", 30); d:add("ape", 5)

for _, w in ipairs(d:suggest("ap", 3)) do print(w) end
-- app
-- apple
-- apply
```

## 16.5 이벤트 디스패처 (관찰자 패턴)

```lua
local EventBus = {}
EventBus.__index = EventBus

function EventBus.new()
    return setmetatable({listeners = {}}, EventBus)
end

function EventBus:on(event, callback)
    self.listeners[event] = self.listeners[event] or {}
    table.insert(self.listeners[event], callback)
end

function EventBus:emit(event, ...)
    for _, cb in ipairs(self.listeners[event] or {}) do cb(...) end
end

local bus = EventBus.new()
bus:on("login", function(user) print("welcome,", user) end)
bus:on("login", function(user) print("logging:", user) end)
bus:emit("login", "alice")
-- welcome, alice
-- logging: alice
```

## 16.6 메모이제이션과 DP

해시맵으로 함수 결과를 캐시.

```lua
local function memoize(f)
    local cache = {}
    return function(n)
        if cache[n] == nil then
            cache[n] = f(n)
        end
        return cache[n]
    end
end

local fib
fib = memoize(function(n)
    if n < 2 then return n end
    return fib(n-1) + fib(n-2)
end)

print(fib(50))  -- 12586269025  (메모 없으면 영원히)
```

---

# 17. 부록 — 자료구조 치트시트

## 17.1 시간복잡도 비교

| 자료구조       | 접근       | 검색      | 삽입       | 삭제       | 비고             |
|------------|----------|---------|----------|----------|----------------|
| 배열         | O(1)     | O(n)    | O(n)     | O(n)     | 끝쪽은 O(1)       |
| 동적 배열      | O(1)     | O(n)    | O(1)*    | O(n)     |                |
| 단일 연결 리스트  | O(n)     | O(n)    | O(1)**   | O(1)**   | 위치 알 때         |
| 이중 연결 리스트  | O(n)     | O(n)    | O(1)**   | O(1)**   |                |
| 스택         | O(n)     | O(n)    | O(1)     | O(1)     | 맨 위만           |
| 큐          | O(n)     | O(n)    | O(1)     | O(1)     | 양 끝만           |
| 해시 테이블     | N/A      | O(1)~   | O(1)~    | O(1)~    | 최악 O(n)        |
| 이진 탐색 트리   | O(log n)~ | O(log n)~ | O(log n)~ | O(log n)~ | 최악 O(n)        |
| 균형 트리(AVL) | O(log n) | O(log n) | O(log n) | O(log n) |                |
| 힙          | O(1)peek | O(n)    | O(log n) | O(log n) | top만 O(1)      |
| 트라이        | O(L)     | O(L)    | O(L)     | O(L)     | L = 키 길이       |
| 펜윅 트리      | -        | O(log n) | O(log n) | -        | 부분합 전용         |
| 유니온 파인드    | -        | O(α(n)) | O(α(n))  | -        | α: inverse Ackermann |

\* 분할상환  \*\* 위치를 알고 있을 때

## 17.2 어떤 자료구조를 쓸까

| 상황                     | 추천          |
|------------------------|-------------|
| 인덱스 접근 + 끝쪽 변경         | 배열          |
| 양 끝에서만 추가/삭제           | 큐 / 덱       |
| 키-값 매핑, 빈도수            | 해시 테이블      |
| 중복 없는 컬렉션              | 집합          |
| 순서 유지 + 빠른 검색          | 균형 트리       |
| 최솟값/최댓값 반복 추출          | 힙           |
| 정렬된 데이터의 부분합           | 펜윅/세그먼트 트리  |
| 문자열 접두사 검색             | 트라이         |
| 그룹 합치기/소속 판정           | 유니온 파인드     |
| 그래프 탐색 (최단/연결성)        | BFS / DFS   |
| 가중치 최단 경로 (양수)         | Dijkstra    |
| 캐시 (최근 사용 우선)          | LRU         |
| 멤버십 빠른 확인 (오탐 허용)      | 블룸 필터       |

## 17.3 Lua 자료구조 코드 패턴 모음

### 클래스 만들기

```lua
local Foo = {}
Foo.__index = Foo
function Foo.new()
    return setmetatable({}, Foo)
end
function Foo:method() ... end
```

### 배열 길이

```lua
#arr  -- nil이 없는 시퀀스에서만 안전
```

### 안전한 길이 추적

```lua
self.size = self.size + 1  -- 직접 관리
```

### 끝 추가/제거

```lua
table.insert(t, v)        -- O(1)
table.remove(t)           -- O(1) (끝)
```

### 정렬

```lua
table.sort(t, cmp)
```

### 깊은 복사

```lua
local function deep(t, seen)
    if type(t) ~= "table" then return t end
    seen = seen or {}
    if seen[t] then return seen[t] end
    local c = {}; seen[t] = c
    for k, v in pairs(t) do c[deep(k, seen)] = deep(v, seen) end
    return c
end
```

### 메모이제이션

```lua
local function memoize(f)
    local cache = {}
    return function(...)
        local key = table.concat({...}, "|")
        if cache[key] == nil then cache[key] = f(...) end
        return cache[key]
    end
end
```

## 17.4 마치며

자료구조는 **문제와 데이터를 보고 자연스럽게 떠올라야** 진짜 자기 것이 된다. 책을 덮은 뒤엔, 이런 식으로 연습해보자:

1. 알고리즘 사이트(LeetCode, Codeforces, 백준)에서 문제를 골라 Lua로 풀어본다.
2. 같은 문제를 다른 자료구조로 한 번씩 풀어본다. 시간/메모리를 비교한다.
3. 라이브러리에 의존하지 말고, 처음 한 번은 직접 만든다.
4. 그 후엔 Lua의 `table`/`table.sort`처럼 잘 만들어진 도구를 적극 활용한다.

자료구조는 결국 **사고의 도구**다. 도구가 많아질수록 같은 문제를 다른 각도에서 볼 수 있게 된다. 좋은 코드를 위한 여정에서 이 책이 첫 발판이 되길 바란다.

— 끝 —

```lua
-- 끝까지 읽으셨다면, 이 줄을 실행해보세요.
print("당신은 이제 Lua 자료구조의 기초를 마쳤습니다 🎉")
```
