# Lua로 배우는 알고리즘

> 실행 가능한 예제로 익히는 알고리즘 입문서
> 약 100페이지 분량 / Lua 5.4 기준

---

## 목차

1. [서문](#1-서문)
2. [환경 준비와 측정 도구](#2-환경-준비와-측정-도구)
3. [복잡도 분석 — Big-O 입문](#3-복잡도-분석--big-o-입문)
4. [정렬 알고리즘](#4-정렬-알고리즘)
5. [탐색 알고리즘](#5-탐색-알고리즘)
6. [재귀와 분할정복](#6-재귀와-분할정복)
7. [동적 계획법 (Dynamic Programming)](#7-동적-계획법-dynamic-programming)
8. [그리디 알고리즘](#8-그리디-알고리즘)
9. [백트래킹](#9-백트래킹)
10. [그래프 알고리즘](#10-그래프-알고리즘)
11. [문자열 알고리즘](#11-문자열-알고리즘)
12. [수학과 정수론 알고리즘](#12-수학과-정수론-알고리즘)
13. [비트 조작](#13-비트-조작)
14. [기하 알고리즘](#14-기하-알고리즘)
15. [근사와 휴리스틱](#15-근사와-휴리스틱)
16. [실전 문제 풀이](#16-실전-문제-풀이)
17. [부록 — 알고리즘 치트시트](#17-부록--알고리즘-치트시트)

---

# 1. 서문

## 1.1 알고리즘이란

알고리즘은 **문제를 풀기 위한 단계별 절차**다. 같은 문제도 어떤 알고리즘으로 푸느냐에 따라 1초가 걸릴 수도, 1년이 걸릴 수도 있다. 좋은 프로그래머는 새로운 알고리즘을 발명하기보다, **기존 알고리즘을 알맞은 자리에 갖다 쓰는 사람**에 가깝다.

이 책은 그 "갖다 쓸 수 있는 알고리즘"의 카탈로그를 만든다. 동시에, 알고리즘이 왜 그렇게 동작하는지를 코드로 직접 확인하면서 이해한다.

## 1.2 왜 Lua인가

- **문법이 짧다.** 알고리즘의 본질에 집중할 수 있다.
- **인터프리터가 가볍다.** 어디서든 빠르게 실험한다.
- **테이블 하나로 모든 자료구조가 가능하다.** 알고리즘만 보면 된다.
- **C와 비슷한 직관.** 인덱스가 1부터 시작하는 점만 빼면 의사코드를 거의 그대로 옮길 수 있다.

이 책의 자매서 *Lua로 배우는 자료구조* 를 먼저 읽었다면, 이번 책은 그 자료구조들을 **어떻게 활용하는가** 의 답이 된다. 두 권을 같이 보는 것을 권한다.

## 1.3 학습 방법

1. **예제는 모두 실행해본다.** `lua file.lua` 한 줄이면 된다.
2. **출력이 왜 그렇게 나오는지 추적한다.** print 한두 개를 추가해서 중간 상태를 본다.
3. **입력을 바꿔본다.** 가장 작은 입력, 비어있는 입력, 1개짜리 입력, 정렬된 입력, 거꾸로 정렬된 입력으로 한 번씩 돌려본다.
4. **외워서 다시 짜본다.** 외우지 말고 **흐름을 이해한 채로** 다시 짜본다.

자, 시작하자.

---

# 2. 환경 준비와 측정 도구

## 2.1 Lua 설치

```bash
# Ubuntu/Debian
sudo apt install lua5.4

# macOS
brew install lua

# 버전 확인
lua -v
```

## 2.2 시간 측정 헬퍼

알고리즘 책에서 시간 측정은 매우 중요하다. 책 전체에서 다음 헬퍼를 사용한다.

```lua
-- bench.lua
local M = {}

function M.measure(label, fn, ...)
    local t0 = os.clock()
    local result = {fn(...)}
    local elapsed = os.clock() - t0
    print(string.format("[%s] %.6fs", label, elapsed))
    return table.unpack(result)
end

function M.compare(items)
    -- items = { {label, fn}, ... }
    for _, it in ipairs(items) do
        M.measure(it[1], it[2])
    end
end

return M
```

사용 예:

```lua
local bench = require("bench")
bench.measure("sum 1..1e6", function()
    local s = 0
    for i = 1, 1e6 do s = s + i end
    return s
end)
-- [sum 1..1e6] 0.012345s
```

## 2.3 무작위 데이터 생성기

알고리즘 비교에 쓸 데이터셋을 만든다.

```lua
local M = {}

math.randomseed(os.time())

function M.random_array(n, lo, hi)
    lo, hi = lo or 1, hi or 1e6
    local t = {}
    for i = 1, n do t[i] = math.random(lo, hi) end
    return t
end

function M.sorted_array(n)
    local t = {}
    for i = 1, n do t[i] = i end
    return t
end

function M.reversed_array(n)
    local t = {}
    for i = 1, n do t[i] = n - i + 1 end
    return t
end

function M.nearly_sorted(n, swaps)
    local t = M.sorted_array(n)
    for _ = 1, (swaps or n / 100) do
        local i, j = math.random(1, n), math.random(1, n)
        t[i], t[j] = t[j], t[i]
    end
    return t
end

return M
```

## 2.4 정확성 검증 헬퍼

```lua
local function assert_equal(actual, expected, msg)
    if type(actual) == "table" and type(expected) == "table" then
        if #actual ~= #expected then
            error(string.format("[%s] length mismatch: %d vs %d",
                  msg or "?", #actual, #expected))
        end
        for i = 1, #actual do
            if actual[i] ~= expected[i] then
                error(string.format("[%s] index %d: %s vs %s",
                      msg or "?", i, tostring(actual[i]), tostring(expected[i])))
            end
        end
    elseif actual ~= expected then
        error(string.format("[%s] %s vs %s", msg or "?",
              tostring(actual), tostring(expected)))
    end
end

assert_equal({1, 2, 3}, {1, 2, 3}, "test1")  -- OK
-- assert_equal({1, 2}, {1, 3}, "test2")     -- 에러
```

이 책의 모든 알고리즘은 위 헬퍼들을 활용해 검증된다고 가정한다.

---

# 3. 복잡도 분석 — Big-O 입문

## 3.1 왜 Big-O인가

같은 문제를 푸는 알고리즘이 둘 있다고 하자.
- A: 입력이 두 배가 되면 시간도 두 배
- B: 입력이 두 배가 되면 시간이 네 배

작은 입력에선 B가 더 빠를 수도 있다. 하지만 입력이 충분히 커지면 **A가 압도적으로 빠르다.** Big-O는 이 "충분히 큰 입력에서의 성장률"을 표현한다.

## 3.2 흔한 복잡도 클래스

| 표기      | 이름     | n=10  | n=1,000   | n=1,000,000     |
|---------|--------|-------|-----------|-----------------|
| O(1)    | 상수     | 1     | 1         | 1               |
| O(log n)| 로그     | 3     | 10        | 20              |
| O(n)    | 선형     | 10    | 1,000     | 1,000,000       |
| O(n log n) | 선형로그 | 33  | 10,000    | 20,000,000      |
| O(n²)   | 이차     | 100   | 1,000,000 | 10¹²            |
| O(2ⁿ)   | 지수     | 1,024 | 천문학적     | 우주가 끝날 때까지     |

**감 잡기:**
- 1억(10⁸)번 연산 ≈ 1초 (Lua는 좀 더 느려서 1천만이 현실적)
- O(n²)으로는 n=10,000이 한계
- O(n log n)이면 n=10,000,000도 다룰 수 있다

## 3.3 측정으로 확인

```lua
local function timed(n, fn)
    local t0 = os.clock()
    fn(n)
    return os.clock() - t0
end

local function linear(n)
    local s = 0
    for i = 1, n do s = s + i end
end

local function quadratic(n)
    local s = 0
    for i = 1, n do
        for j = 1, n do s = s + 1 end
    end
end

for _, n in ipairs({1000, 2000, 4000, 8000}) do
    print(string.format("n=%d  linear=%.4fs  quadratic=%.4fs",
        n, timed(n, linear), timed(n, quadratic)))
end
```

전형적인 출력:

```
n=1000  linear=0.0001s  quadratic=0.0086s
n=2000  linear=0.0001s  quadratic=0.0349s   ← 4배
n=4000  linear=0.0002s  quadratic=0.1396s   ← 4배
n=8000  linear=0.0004s  quadratic=0.5587s   ← 4배
```

n이 두 배가 될 때 선형은 두 배, 이차는 네 배. Big-O가 실측에서 확인된다.

## 3.4 평균/최악/최선

알고리즘은 입력에 따라 성능이 다르다.
- **최선(best):** 가장 운 좋은 경우 (이미 정렬된 배열)
- **평균(average):** 기대값
- **최악(worst):** 가장 운 나쁜 경우

예: 퀵정렬은 평균 O(n log n)이지만, 최악(이미 정렬된 입력 + 나쁜 피벗)에 O(n²).

## 3.5 공간 복잡도

시간만이 자원이 아니다. 메모리도 한정되어 있다.

```lua
-- O(n) 공간: 새 배열 만듦
local function reversed_copy(arr)
    local t = {}
    for i = #arr, 1, -1 do table.insert(t, arr[i]) end
    return t
end

-- O(1) 공간: 같은 배열 안에서 처리
local function reverse_in_place(arr)
    local i, j = 1, #arr
    while i < j do
        arr[i], arr[j] = arr[j], arr[i]
        i, j = i+1, j-1
    end
end
```

## 3.6 점근적 vs 실제 성능

이론과 실제는 다를 수 있다.
- 작은 n에서는 상수가 큰 차이를 만든다
- 캐시 친화도, 분기 예측이 영향
- 메모리 할당/GC 비용

그래서 Lua의 `table.sort`(C 구현)는 이론상 같은 O(n log n)인 직접 만든 병합 정렬보다 훨씬 빠르다. **알고리즘 선택과 구현 선택은 별개의 문제**임을 기억하자.

---

# 4. 정렬 알고리즘

정렬은 알고리즘의 "Hello World"다. 거의 모든 알고리즘 기법을 정렬에서 만난다.

## 4.1 버블 정렬 — O(n²)

가장 단순한 정렬. 인접한 두 원소를 비교해서 큰 것을 뒤로 보낸다.

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
        if not swapped then break end  -- 최적화: 한 번도 교환 없으면 끝
    end
    return arr
end

local t = {64, 34, 25, 12, 22, 11, 90}
bubble_sort(t)
print(table.concat(t, " "))  -- 11 12 22 25 34 64 90
```

- 시간: 평균/최악 O(n²), 최선 O(n)
- 공간: O(1)
- **안정 정렬**: 같은 값의 상대 순서가 보존됨

## 4.2 선택 정렬 — O(n²)

매 단계마다 최솟값을 찾아서 앞쪽에 놓는다.

```lua
local function selection_sort(arr)
    local n = #arr
    for i = 1, n - 1 do
        local min_idx = i
        for j = i + 1, n do
            if arr[j] < arr[min_idx] then min_idx = j end
        end
        if min_idx ~= i then
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
        end
    end
    return arr
end

print(table.concat(selection_sort({5, 2, 8, 1, 9, 3}), " "))
-- 1 2 3 5 8 9
```

교환 횟수가 적어서 쓰기가 비싼 환경에서 유리할 수 있다. 단, 안정적이지 않다.

## 4.3 삽입 정렬 — O(n²)

한 원소씩 보면서 이미 정렬된 앞부분의 적절한 위치에 끼워 넣는다.

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

거의 정렬된 데이터에서 O(n)에 가깝다. 작은 배열이나 부분 배열에 자주 쓰인다.

## 4.4 병합 정렬 — O(n log n)

분할정복의 정석. 반으로 나누고, 각각 정렬한 뒤, 병합한다.

```lua
local function merge(left, right)
    local result, i, j = {}, 1, 1
    while i <= #left and j <= #right do
        if left[i] <= right[j] then
            result[#result + 1] = left[i]; i = i + 1
        else
            result[#result + 1] = right[j]; j = j + 1
        end
    end
    while i <= #left do result[#result + 1] = left[i]; i = i + 1 end
    while j <= #right do result[#result + 1] = right[j]; j = j + 1 end
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

local t = merge_sort({5, 2, 8, 1, 9, 3, 7, 4, 6})
print(table.concat(t, " "))  -- 1 2 3 4 5 6 7 8 9
```

- 시간: 항상 O(n log n)
- 공간: O(n) (병합 임시 배열)
- **안정 정렬**: ✓

## 4.5 퀵 정렬 — 평균 O(n log n)

피벗을 정해 작은 것은 왼쪽, 큰 것은 오른쪽으로 분할하고, 각 부분을 재귀적으로 정렬.

```lua
local function partition(arr, lo, hi)
    local pivot = arr[hi]
    local i = lo - 1
    for j = lo, hi - 1 do
        if arr[j] <= pivot then
            i = i + 1
            arr[i], arr[j] = arr[j], arr[i]
        end
    end
    arr[i+1], arr[hi] = arr[hi], arr[i+1]
    return i + 1
end

local function quicksort(arr, lo, hi)
    lo, hi = lo or 1, hi or #arr
    if lo < hi then
        local p = partition(arr, lo, hi)
        quicksort(arr, lo, p - 1)
        quicksort(arr, p + 1, hi)
    end
end

local t = {5, 2, 8, 1, 9, 3, 7, 4, 6}
quicksort(t)
print(table.concat(t, " "))  -- 1 2 3 4 5 6 7 8 9
```

피벗 선택이 핵심. 마지막 원소를 그대로 쓰면 정렬된 입력에서 최악(O(n²)). 무작위 피벗으로 회피:

```lua
local function quicksort_random(arr, lo, hi)
    lo, hi = lo or 1, hi or #arr
    if lo < hi then
        local r = math.random(lo, hi)
        arr[r], arr[hi] = arr[hi], arr[r]
        local p = partition(arr, lo, hi)
        quicksort_random(arr, lo, p - 1)
        quicksort_random(arr, p + 1, hi)
    end
end
```

3-way 분할 (Dutch National Flag)로 중복 많은 데이터에 강해진다:

```lua
local function quicksort_3way(arr, lo, hi)
    lo, hi = lo or 1, hi or #arr
    if lo >= hi then return end
    local lt, gt, i = lo, hi, lo
    local pivot = arr[lo]
    while i <= gt do
        if arr[i] < pivot then
            arr[i], arr[lt] = arr[lt], arr[i]
            lt, i = lt + 1, i + 1
        elseif arr[i] > pivot then
            arr[i], arr[gt] = arr[gt], arr[i]
            gt = gt - 1
        else
            i = i + 1
        end
    end
    quicksort_3way(arr, lo, lt - 1)
    quicksort_3way(arr, gt + 1, hi)
end
```

## 4.6 힙 정렬 — O(n log n)

배열을 힙으로 만들고 한 개씩 빼낸다. 공간 O(1).

```lua
local function sift_down(arr, start, n)
    local root = start
    while 2*root <= n do
        local child = 2*root
        if child < n and arr[child] < arr[child+1] then
            child = child + 1
        end
        if arr[root] < arr[child] then
            arr[root], arr[child] = arr[child], arr[root]
            root = child
        else break end
    end
end

local function heap_sort(arr)
    local n = #arr
    -- heapify
    for i = n // 2, 1, -1 do sift_down(arr, i, n) end
    -- 한 개씩 추출
    for i = n, 2, -1 do
        arr[1], arr[i] = arr[i], arr[1]
        sift_down(arr, 1, i - 1)
    end
    return arr
end

print(table.concat(heap_sort({5, 2, 8, 1, 9, 3, 7, 4, 6}), " "))
-- 1 2 3 4 5 6 7 8 9
```

## 4.7 카운팅 정렬 — O(n + k)

값의 범위가 작을 때 압도적으로 빠르다.

```lua
local function counting_sort(arr, max_val)
    local count = {}
    for i = 0, max_val do count[i] = 0 end
    for _, v in ipairs(arr) do count[v] = count[v] + 1 end
    local idx = 1
    for v = 0, max_val do
        for _ = 1, count[v] do
            arr[idx] = v
            idx = idx + 1
        end
    end
    return arr
end

print(table.concat(counting_sort({4, 2, 2, 8, 3, 3, 1}, 8), " "))
-- 1 2 2 3 3 4 8
```

- 시간: O(n + k) (k = 값의 범위)
- 비교 없이 정렬한다는 점이 특별하다
- 음수, 부동소수, 큰 범위엔 부적합

## 4.8 기수 정렬 (Radix Sort) — O(n × d)

정수를 자릿수별로 정렬.

```lua
local function radix_sort(arr)
    local max_val = 0
    for _, v in ipairs(arr) do
        if v > max_val then max_val = v end
    end
    local exp = 1
    while max_val // exp > 0 do
        -- 자릿수 exp에 대해 카운팅 정렬
        local count = {}
        for i = 0, 9 do count[i] = 0 end
        for _, v in ipairs(arr) do
            local d = (v // exp) % 10
            count[d] = count[d] + 1
        end
        for i = 1, 9 do count[i] = count[i] + count[i-1] end

        local output = {}
        for i = #arr, 1, -1 do
            local d = (arr[i] // exp) % 10
            output[count[d]] = arr[i]
            count[d] = count[d] - 1
        end
        for i = 1, #arr do arr[i] = output[i] end
        exp = exp * 10
    end
    return arr
end

print(table.concat(radix_sort({170, 45, 75, 90, 802, 24, 2, 66}), " "))
-- 2 24 45 66 75 90 170 802
```

## 4.9 정렬 비교 벤치마크

```lua
local function bench_sort(name, fn, n)
    local arr = {}
    for i = 1, n do arr[i] = math.random(1, 1e9) end
    local t0 = os.clock()
    fn(arr)
    print(string.format("%-20s n=%d  %.4fs", name, n, os.clock() - t0))
end

local n = 5000
bench_sort("bubble_sort", bubble_sort, n)
bench_sort("insertion_sort", insertion_sort, n)
bench_sort("merge_sort_wrap", function(a)
    local s = merge_sort(a)
    for i, v in ipairs(s) do a[i] = v end
end, n)
bench_sort("quicksort", quicksort, n)
bench_sort("heap_sort", heap_sort, n)
bench_sort("table.sort (C)", function(a) table.sort(a) end, n)
```

전형적 결과 (Lua 5.4, n=5000):

```
bubble_sort         n=5000  0.5421s
insertion_sort      n=5000  0.2845s
merge_sort_wrap     n=5000  0.0102s
quicksort           n=5000  0.0061s
heap_sort           n=5000  0.0094s
table.sort (C)      n=5000  0.0008s
```

C로 짠 `table.sort`가 압도적이다. 거의 모든 실무 상황에서는 `table.sort`로 충분하다.

## 4.10 안정성과 in-place 표

| 알고리즘    | 시간 (평균)     | 시간 (최악)      | 공간       | 안정 |
|---------|------------|-------------|----------|----|
| 버블      | O(n²)      | O(n²)       | O(1)     | ✓  |
| 선택      | O(n²)      | O(n²)       | O(1)     | ✗  |
| 삽입      | O(n²)      | O(n²)       | O(1)     | ✓  |
| 병합      | O(n log n) | O(n log n)  | O(n)     | ✓  |
| 퀵       | O(n log n) | O(n²)       | O(log n) | ✗  |
| 힙       | O(n log n) | O(n log n)  | O(1)     | ✗  |
| 카운팅     | O(n + k)   | O(n + k)    | O(k)     | ✓  |
| 기수      | O(n × d)   | O(n × d)    | O(n + k) | ✓  |

---

# 5. 탐색 알고리즘

## 5.1 선형 탐색 — O(n)

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

정렬되지 않은 데이터에선 이게 한계.

## 5.2 이진 탐색 — O(log n)

정렬된 배열에서. 매번 후보 범위를 절반으로 줄인다.

```lua
local function binary_search(arr, target)
    local lo, hi = 1, #arr
    while lo <= hi do
        local mid = (lo + hi) // 2
        if arr[mid] == target then return mid
        elseif arr[mid] < target then lo = mid + 1
        else hi = mid - 1 end
    end
    return -1
end

local sorted = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
print(binary_search(sorted, 11))  -- 6
print(binary_search(sorted, 4))   -- -1
```

오버플로우 안전 버전 (Lua는 64비트 정수라 문제 없지만 습관):

```lua
local mid = lo + (hi - lo) // 2
```

## 5.3 lower_bound / upper_bound

이진 탐색의 변형. STL과 동일한 의미.

- `lower_bound(arr, x)`: x **이상**이 처음 나타나는 위치
- `upper_bound(arr, x)`: x **초과**가 처음 나타나는 위치

```lua
local function lower_bound(arr, x)
    local lo, hi = 1, #arr + 1
    while lo < hi do
        local mid = (lo + hi) // 2
        if arr[mid] < x then lo = mid + 1
        else hi = mid end
    end
    return lo
end

local function upper_bound(arr, x)
    local lo, hi = 1, #arr + 1
    while lo < hi do
        local mid = (lo + hi) // 2
        if arr[mid] <= x then lo = mid + 1
        else hi = mid end
    end
    return lo
end

local t = {1, 2, 2, 2, 3, 5, 8}
print(lower_bound(t, 2))  -- 2
print(upper_bound(t, 2))  -- 5
print(upper_bound(t, 2) - lower_bound(t, 2))  -- 3 (개수)
```

## 5.4 답을 이진 탐색

"몇 명을 데려올까?", "최소 시간은?" 같은 답이 단조성을 가질 때.

**예제: 코코 바나나 먹기 (LeetCode 875).** 시간 H시간 안에 모든 바나나를 먹기 위한 시간당 최소 먹는 양.

```lua
local function min_eating_speed(piles, H)
    local function hours(k)
        local h = 0
        for _, p in ipairs(piles) do
            h = h + math.ceil(p / k)
        end
        return h
    end

    local lo, hi = 1, 0
    for _, p in ipairs(piles) do if p > hi then hi = p end end

    while lo < hi do
        local mid = (lo + hi) // 2
        if hours(mid) <= H then hi = mid
        else lo = mid + 1 end
    end
    return lo
end

print(min_eating_speed({3, 6, 7, 11}, 8))      -- 4
print(min_eating_speed({30, 11, 23, 4, 20}, 5)) -- 30
```

이 패턴이 익으면 "답을 이진탐색" 류 문제는 보자마자 풀린다.

## 5.5 삼분 탐색 — O(log n)

단봉 함수(unimodal function)에서 극값을 찾는다.

```lua
local function ternary_search(f, lo, hi, eps)
    eps = eps or 1e-7
    while hi - lo > eps do
        local m1 = lo + (hi - lo) / 3
        local m2 = hi - (hi - lo) / 3
        if f(m1) < f(m2) then lo = m1
        else hi = m2 end
    end
    return (lo + hi) / 2
end

-- 예: f(x) = -(x-3)^2 + 5 의 최댓값
local function f(x) return -(x - 3)^2 + 5 end
print(ternary_search(f, 0, 10))  -- 약 3.0
```

## 5.6 보간 탐색 — 평균 O(log log n)

키가 균등 분포일 때 이진보다 빠르다.

```lua
local function interpolation_search(arr, target)
    local lo, hi = 1, #arr
    while lo <= hi and target >= arr[lo] and target <= arr[hi] do
        if lo == hi then
            return arr[lo] == target and lo or -1
        end
        local pos = lo + ((target - arr[lo]) * (hi - lo)) // (arr[hi] - arr[lo])
        if arr[pos] == target then return pos
        elseif arr[pos] < target then lo = pos + 1
        else hi = pos - 1 end
    end
    return -1
end
```

## 5.7 점프 탐색

이진 탐색과 선형 탐색의 절충. O(√n).

```lua
local function jump_search(arr, target)
    local n = #arr
    local step = math.floor(math.sqrt(n))
    local prev = 1
    while prev <= n and arr[math.min(step, n)] < target do
        prev = step + 1
        step = step + math.floor(math.sqrt(n))
    end
    for i = prev, math.min(step, n) do
        if arr[i] == target then return i end
    end
    return -1
end
```

블록 단위로만 접근 가능한 자료(테이프 등)에서 의의가 있다.

---

# 6. 재귀와 분할정복

## 6.1 재귀의 두 부분

모든 재귀는 **종료 조건**과 **재귀 단계**로 구성된다.

```lua
local function factorial(n)
    if n <= 1 then return 1 end           -- 종료 조건
    return n * factorial(n - 1)           -- 재귀 단계
end

print(factorial(10))  -- 3628800
```

## 6.2 분할정복의 패턴

**문제 → 작은 문제로 분할 → 각각 풀기 → 합치기**

```
T(n) = a × T(n/b) + f(n)
```

전형적인 예: 병합 정렬, 퀵 정렬, 이진 탐색, 빠른 거듭제곱, Karatsuba.

## 6.3 빠른 거듭제곱 — O(log n)

```lua
local function fast_pow(base, exp)
    if exp == 0 then return 1 end
    local half = fast_pow(base, exp // 2)
    if exp % 2 == 0 then return half * half
    else return half * half * base end
end

print(fast_pow(2, 10))  -- 1024
print(fast_pow(3, 20))  -- 3486784401
```

반복 버전:

```lua
local function fast_pow_iter(base, exp)
    local result = 1
    while exp > 0 do
        if exp & 1 == 1 then result = result * base end
        base = base * base
        exp = exp >> 1
    end
    return result
end
```

## 6.4 모듈러 거듭제곱

암호학에서 핵심.

```lua
local function pow_mod(base, exp, mod)
    local result = 1
    base = base % mod
    while exp > 0 do
        if exp & 1 == 1 then
            result = (result * base) % mod
        end
        base = (base * base) % mod
        exp = exp >> 1
    end
    return result
end

print(pow_mod(2, 100, 1000000007))  -- 976371285
```

## 6.5 최대 부분합 — Kadane의 O(n) vs 분할정복 O(n log n)

**분할정복 버전:**

```lua
local function max_subarray_dc(arr, lo, hi)
    lo, hi = lo or 1, hi or #arr
    if lo == hi then return arr[lo] end
    local mid = (lo + hi) // 2
    local left = max_subarray_dc(arr, lo, mid)
    local right = max_subarray_dc(arr, mid + 1, hi)

    -- 가운데를 가로지르는 최대합
    local left_sum, sum = -math.huge, 0
    for i = mid, lo, -1 do
        sum = sum + arr[i]
        if sum > left_sum then left_sum = sum end
    end
    local right_sum
    sum, right_sum = 0, -math.huge
    for i = mid + 1, hi do
        sum = sum + arr[i]
        if sum > right_sum then right_sum = sum end
    end

    return math.max(left, right, left_sum + right_sum)
end

print(max_subarray_dc({-2, 1, -3, 4, -1, 2, 1, -5, 4}))  -- 6
```

**Kadane (DP의 일종):**

```lua
local function max_subarray_kadane(arr)
    local best, cur = arr[1], arr[1]
    for i = 2, #arr do
        cur = math.max(arr[i], cur + arr[i])
        best = math.max(best, cur)
    end
    return best
end

print(max_subarray_kadane({-2, 1, -3, 4, -1, 2, 1, -5, 4}))  -- 6
```

같은 답, O(n)이 압도적으로 빠르다. 같은 문제를 여러 시각으로 보는 훈련이 중요하다.

## 6.6 하노이의 탑

```lua
local function hanoi(n, from, to, via)
    if n == 1 then
        print(string.format("Move disk 1 from %s to %s", from, to))
        return
    end
    hanoi(n - 1, from, via, to)
    print(string.format("Move disk %d from %s to %s", n, from, to))
    hanoi(n - 1, via, to, from)
end

hanoi(3, "A", "C", "B")
-- Move disk 1 from A to C
-- Move disk 2 from A to B
-- Move disk 1 from C to B
-- Move disk 3 from A to C
-- Move disk 1 from B to A
-- Move disk 2 from B to C
-- Move disk 1 from A to C
```

총 이동 횟수는 2ⁿ - 1.

## 6.7 재귀 → 반복 변환

깊은 재귀는 스택 오버플로우 위험. 명시적 스택으로 변환:

```lua
-- 재귀 트리 순회
local function traverse_recursive(node)
    if not node then return end
    print(node.value)
    traverse_recursive(node.left)
    traverse_recursive(node.right)
end

-- 반복 (명시적 스택)
local function traverse_iter(node)
    local stack = {node}
    while #stack > 0 do
        local n = stack[#stack]; stack[#stack] = nil
        if n then
            print(n.value)
            stack[#stack + 1] = n.right
            stack[#stack + 1] = n.left
        end
    end
end
```

## 6.8 꼬리 재귀

Lua는 꼬리 호출 최적화(TCO)를 지원한다. `return f(...)` 형태면 스택 안 쌓인다.

```lua
local function sum_tail(n, acc)
    acc = acc or 0
    if n == 0 then return acc end
    return sum_tail(n - 1, acc + n)  -- 꼬리 호출
end

print(sum_tail(1000000))  -- 스택 오버플로우 없음
```

비교: TCO 안 되는 형태

```lua
local function sum_naive(n)
    if n == 0 then return 0 end
    return n + sum_naive(n - 1)  -- 꼬리 호출 아님 (덧셈이 마지막)
end

-- sum_naive(1000000)  -- stack overflow
```

---

# 7. 동적 계획법 (Dynamic Programming)

## 7.1 DP는 무엇이고 언제 쓰나

DP의 핵심은 두 가지:
1. **중복 부분문제 (overlapping subproblems):** 같은 작은 문제가 여러 번 나타난다.
2. **최적 부분구조 (optimal substructure):** 큰 문제의 답을 작은 문제의 답으로 만들 수 있다.

해법:
- **Top-down + Memoization:** 재귀 + 캐시
- **Bottom-up:** 표(table)를 채워나감

## 7.2 피보나치 수열

### Naive — O(2ⁿ)

```lua
local function fib_naive(n)
    if n < 2 then return n end
    return fib_naive(n - 1) + fib_naive(n - 2)
end

-- print(fib_naive(40))  -- 수십 초
```

`fib(40)`은 수십억 번의 재귀를 만든다. `fib(38)`이 두 번 계산되고, 그 안에서 `fib(36)`이 네 번 계산되고... 지수적 폭발.

### Top-down 메모화 — O(n)

```lua
local function fib_memo()
    local cache = {}
    local function f(n)
        if n < 2 then return n end
        if cache[n] then return cache[n] end
        cache[n] = f(n - 1) + f(n - 2)
        return cache[n]
    end
    return f
end

local fib = fib_memo()
print(fib(50))   -- 12586269025
print(fib(100))  -- 354224848179261915075
```

### Bottom-up — O(n), O(1) 공간

```lua
local function fib_iter(n)
    if n < 2 then return n end
    local a, b = 0, 1
    for _ = 2, n do
        a, b = b, a + b
    end
    return b
end

print(fib_iter(50))
```

DP의 진수: **상태**(n)를 정의하고 **점화식**(f(n) = f(n-1) + f(n-2))을 찾는 것.

## 7.3 계단 오르기

한 번에 1칸 또는 2칸씩 오를 때, n 계단을 오르는 방법 수.

```lua
local function climb(n)
    if n <= 2 then return n end
    local dp = {1, 2}
    for i = 3, n do
        dp[i] = dp[i-1] + dp[i-2]
    end
    return dp[n]
end

print(climb(10))  -- 89
```

피보나치와 점화식이 같다.

## 7.4 동전 거스름돈

목표 금액 amount를 만드는 데 필요한 최소 동전 수. coins = {1, 2, 5}일 때 11원 → 3개 (5+5+1).

```lua
local function coin_change(coins, amount)
    local dp = {}
    for i = 0, amount do dp[i] = math.huge end
    dp[0] = 0
    for a = 1, amount do
        for _, c in ipairs(coins) do
            if a - c >= 0 and dp[a - c] + 1 < dp[a] then
                dp[a] = dp[a - c] + 1
            end
        end
    end
    return dp[amount] == math.huge and -1 or dp[amount]
end

print(coin_change({1, 2, 5}, 11))  -- 3
print(coin_change({2}, 3))         -- -1
```

## 7.5 0/1 배낭 문제

n개의 물건 (무게 w, 가치 v)와 배낭 용량 W가 주어질 때, 가치를 최대로.

```lua
local function knapsack(weights, values, W)
    local n = #weights
    local dp = {}
    for i = 0, n do
        dp[i] = {}
        for w = 0, W do dp[i][w] = 0 end
    end

    for i = 1, n do
        for w = 0, W do
            dp[i][w] = dp[i-1][w]  -- 안 넣는 경우
            if weights[i] <= w then
                local taken = dp[i-1][w - weights[i]] + values[i]
                if taken > dp[i][w] then dp[i][w] = taken end
            end
        end
    end
    return dp[n][W]
end

-- 무게 [2, 3, 4, 5], 가치 [3, 4, 5, 6], 용량 5
print(knapsack({2, 3, 4, 5}, {3, 4, 5, 6}, 5))  -- 7 (= 3 + 4)
```

공간 O(n×W) → 1차원으로 압축 가능 (단, 안쪽 루프를 역순으로!):

```lua
local function knapsack_compact(weights, values, W)
    local dp = {}
    for w = 0, W do dp[w] = 0 end
    for i = 1, #weights do
        for w = W, weights[i], -1 do
            local v = dp[w - weights[i]] + values[i]
            if v > dp[w] then dp[w] = v end
        end
    end
    return dp[W]
end
```

## 7.6 최장 공통 부분 수열 (LCS)

`"abcde"`와 `"ace"`의 LCS는 `"ace"` (길이 3).

```lua
local function lcs(a, b)
    local m, n = #a, #b
    local dp = {}
    for i = 0, m do
        dp[i] = {}
        for j = 0, n do dp[i][j] = 0 end
    end

    for i = 1, m do
        for j = 1, n do
            if a:sub(i, i) == b:sub(j, j) then
                dp[i][j] = dp[i-1][j-1] + 1
            else
                dp[i][j] = math.max(dp[i-1][j], dp[i][j-1])
            end
        end
    end

    -- 실제 부분수열 복원
    local result, i, j = {}, m, n
    while i > 0 and j > 0 do
        if a:sub(i, i) == b:sub(j, j) then
            table.insert(result, 1, a:sub(i, i))
            i, j = i - 1, j - 1
        elseif dp[i-1][j] > dp[i][j-1] then
            i = i - 1
        else
            j = j - 1
        end
    end
    return dp[m][n], table.concat(result)
end

local len, seq = lcs("abcde", "ace")
print(len, seq)  -- 3  ace
```

git diff, DNA 비교, 텍스트 유사도의 기본.

## 7.7 편집 거리 (Edit Distance, Levenshtein)

문자열 a를 b로 바꾸는 데 필요한 최소 연산 수 (삽입/삭제/치환).

```lua
local function edit_distance(a, b)
    local m, n = #a, #b
    local dp = {}
    for i = 0, m do dp[i] = {[0] = i} end
    for j = 0, n do dp[0][j] = j end

    for i = 1, m do
        for j = 1, n do
            if a:sub(i, i) == b:sub(j, j) then
                dp[i][j] = dp[i-1][j-1]
            else
                dp[i][j] = 1 + math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
            end
        end
    end
    return dp[m][n]
end

print(edit_distance("kitten", "sitting"))  -- 3
print(edit_distance("hello", "yellow"))    -- 2
```

스펠 체커, 자동 정정의 핵심.

## 7.8 최장 증가 부분 수열 (LIS)

`{10, 9, 2, 5, 3, 7, 101, 18}`의 LIS 길이는 4 (`2, 3, 7, 101`).

### O(n²) DP

```lua
local function lis_n2(arr)
    local n = #arr
    local dp = {}
    for i = 1, n do dp[i] = 1 end
    for i = 2, n do
        for j = 1, i - 1 do
            if arr[j] < arr[i] and dp[j] + 1 > dp[i] then
                dp[i] = dp[j] + 1
            end
        end
    end
    local best = 0
    for _, v in ipairs(dp) do if v > best then best = v end end
    return best
end

print(lis_n2({10, 9, 2, 5, 3, 7, 101, 18}))  -- 4
```

### O(n log n) — 이진 탐색 활용

```lua
local function lis_nlogn(arr)
    local tails = {}  -- tails[i]: 길이 i+1인 LIS의 마지막 값 중 최솟값
    for _, x in ipairs(arr) do
        -- tails에서 x 이상이 처음 나오는 위치
        local lo, hi = 1, #tails + 1
        while lo < hi do
            local mid = (lo + hi) // 2
            if tails[mid] < x then lo = mid + 1
            else hi = mid end
        end
        tails[lo] = x
    end
    return #tails
end

print(lis_nlogn({10, 9, 2, 5, 3, 7, 101, 18}))  -- 4
```

## 7.9 행렬 체인 곱셈

행렬 곱은 결합 법칙이 성립하지만, 곱셈 횟수는 묶는 방식에 따라 달라진다.

```lua
local function matrix_chain(p)
    -- p[i] = i번째 행렬의 행 수, p[i+1] = 열 수
    local n = #p - 1
    local dp = {}
    for i = 1, n do
        dp[i] = {}
        for j = 1, n do dp[i][j] = 0 end
    end

    for L = 2, n do
        for i = 1, n - L + 1 do
            local j = i + L - 1
            dp[i][j] = math.huge
            for k = i, j - 1 do
                local cost = dp[i][k] + dp[k+1][j] + p[i] * p[k+1] * p[j+1]
                if cost < dp[i][j] then dp[i][j] = cost end
            end
        end
    end
    return dp[1][n]
end

-- 행렬 4개: 10x30, 30x5, 5x60
print(matrix_chain({10, 30, 5, 60}))  -- 4500
```

## 7.10 메모이제이션 데코레이터

DP를 위한 범용 도구.

```lua
local function memoize(fn)
    local cache = {}
    return function(...)
        local args = {...}
        local key = table.concat(args, "|")
        if cache[key] == nil then
            cache[key] = fn(...)
        end
        return cache[key]
    end
end

local function _fib(n)
    if n < 2 then return n end
    return fib(n - 1) + fib(n - 2)
end

fib = memoize(_fib)  -- 주의: _fib가 fib를 호출하므로 글로벌이 필요한 패턴
print(fib(50))
```

> Lua의 글로벌 변수를 안 쓰려면 클로저로 감싸자:
>
> ```lua
> local function make_fib()
>     local cache = {}
>     local function f(n)
>         if n < 2 then return n end
>         if cache[n] then return cache[n] end
>         cache[n] = f(n - 1) + f(n - 2)
>         return cache[n]
>     end
>     return f
> end
> local fib = make_fib()
> ```

---

# 8. 그리디 알고리즘

## 8.1 그리디는 무엇인가

매 단계에서 **국소적으로 최선의 선택**을 한다. 이게 전역 최적이 되는 문제에서만 통한다.

DP가 모든 가능성을 보고 결정한다면, 그리디는 **현재만 보고 결정**한다.

## 8.2 동전 거스름돈 (그리디가 통할 때)

`{1, 5, 10, 50, 100, 500}` 같은 한국 화폐는 큰 동전부터 쓰면 항상 최적.

```lua
local function greedy_coins(amount, coins)
    table.sort(coins, function(a, b) return a > b end)
    local result = {}
    for _, c in ipairs(coins) do
        local n = amount // c
        if n > 0 then
            for _ = 1, n do table.insert(result, c) end
            amount = amount - n * c
        end
    end
    if amount ~= 0 then return nil end
    return result
end

local r = greedy_coins(763, {1, 5, 10, 50, 100, 500})
print(table.concat(r, " "))   -- 500 100 100 50 10 1 1 1
```

**경고:** `{1, 3, 4}` 동전으로 6원을 만들 때 그리디는 `4 + 1 + 1 = 3개`라 답하지만 최적은 `3 + 3 = 2개`. 화폐 체계가 "canonical"한 경우에만 통한다. DP가 안전하다.

## 8.3 활동 선택 문제

겹치지 않게 최대 몇 개의 활동을 할 수 있는가? **종료 시간**으로 정렬하는 것이 정답.

```lua
local function activity_selection(activities)
    -- activities = { {start, end}, ... }
    table.sort(activities, function(a, b) return a[2] < b[2] end)
    local result = {activities[1]}
    local last_end = activities[1][2]
    for i = 2, #activities do
        if activities[i][1] >= last_end then
            table.insert(result, activities[i])
            last_end = activities[i][2]
        end
    end
    return result
end

local acts = {{1,4}, {3,5}, {0,6}, {5,7}, {3,9}, {5,9}, {6,10}, {8,11}, {8,12}, {2,14}, {12,16}}
local chosen = activity_selection(acts)
for _, a in ipairs(chosen) do io.write(string.format("(%d,%d) ", a[1], a[2])) end
print()
-- (1,4) (5,7) (8,11) (12,16)
```

## 8.4 회의실 분배 (Meeting Rooms II)

겹치는 회의들을 위해 필요한 최소 회의실 수.

```lua
local function min_rooms(meetings)
    local starts, ends = {}, {}
    for _, m in ipairs(meetings) do
        table.insert(starts, m[1])
        table.insert(ends, m[2])
    end
    table.sort(starts)
    table.sort(ends)

    local rooms, max_rooms = 0, 0
    local i, j = 1, 1
    while i <= #starts do
        if starts[i] < ends[j] then
            rooms = rooms + 1
            if rooms > max_rooms then max_rooms = rooms end
            i = i + 1
        else
            rooms = rooms - 1
            j = j + 1
        end
    end
    return max_rooms
end

print(min_rooms({{0,30}, {5,10}, {15,20}}))  -- 2
print(min_rooms({{7,10}, {2,4}}))            -- 1
```

## 8.5 허프만 코딩

문자별 빈도가 다를 때, 평균 비트 수가 최소인 가변 길이 코드.

```lua
-- 우선순위 큐 (min-heap)
local PQ = {}
PQ.__index = PQ
function PQ.new() return setmetatable({n = 0, items = {}}, PQ) end
function PQ:push(v)
    self.n = self.n + 1
    self.items[self.n] = v
    local i = self.n
    while i > 1 do
        local p = i // 2
        if self.items[i].freq < self.items[p].freq then
            self.items[i], self.items[p] = self.items[p], self.items[i]
            i = p
        else break end
    end
end
function PQ:pop()
    local top = self.items[1]
    self.items[1] = self.items[self.n]
    self.items[self.n] = nil
    self.n = self.n - 1
    local i = 1
    while 2*i <= self.n do
        local c = 2*i
        if c < self.n and self.items[c+1].freq < self.items[c].freq then c = c + 1 end
        if self.items[i].freq <= self.items[c].freq then break end
        self.items[i], self.items[c] = self.items[c], self.items[i]
        i = c
    end
    return top
end

local function huffman(freq)
    local pq = PQ.new()
    for ch, f in pairs(freq) do
        pq:push({char = ch, freq = f, left = nil, right = nil})
    end
    while pq.n > 1 do
        local a = pq:pop()
        local b = pq:pop()
        pq:push({char = nil, freq = a.freq + b.freq, left = a, right = b})
    end
    local root = pq:pop()

    local codes = {}
    local function walk(node, code)
        if node.char then
            codes[node.char] = code == "" and "0" or code
            return
        end
        walk(node.left, code .. "0")
        walk(node.right, code .. "1")
    end
    walk(root, "")
    return codes
end

local freq = {a = 5, b = 9, c = 12, d = 13, e = 16, f = 45}
for ch, code in pairs(huffman(freq)) do
    print(ch, code)
end
```

자주 나오는 문자엔 짧은 코드, 드문 문자엔 긴 코드. ZIP, JPEG의 압축 핵심.

## 8.6 분할 가능 배낭 (Fractional Knapsack)

0/1 배낭과 달리 물건을 쪼갤 수 있다. **단위 가치**가 큰 것부터 담는 그리디로 최적.

```lua
local function fractional_knapsack(weights, values, W)
    local items = {}
    for i = 1, #weights do
        items[i] = {w = weights[i], v = values[i], unit = values[i] / weights[i]}
    end
    table.sort(items, function(a, b) return a.unit > b.unit end)

    local total = 0
    for _, it in ipairs(items) do
        if W == 0 then break end
        local take = math.min(it.w, W)
        total = total + take * it.unit
        W = W - take
    end
    return total
end

print(fractional_knapsack({10, 20, 30}, {60, 100, 120}, 50))  -- 240.0
```

## 8.7 그리디가 통할까? 검증법

1. **반례를 찾아본다.** 작은 입력으로 손으로 풀어보고 그리디가 틀린 답을 내면 즉시 폐기.
2. **교환 논증.** 그리디 선택을 하지 않은 임의의 최적해를 가져와, 그리디 선택으로 바꿔도 여전히 최적이라는 걸 증명.
3. **DP로 비교한다.** 작은 입력에서 두 알고리즘의 답이 같은지 확인.

```lua
-- 작은 입력 자동 검증
local function verify_greedy(n)
    for _ = 1, 100 do
        local coins = {1, math.random(2, 5), math.random(6, 10)}
        local amount = math.random(10, 30)
        local g = greedy_coins(amount, coins) or {}
        local d = coin_change(coins, amount)  -- DP
        if d > 0 and #g ~= d then
            print("반례:", amount, "동전:", table.concat(coins, ","))
            return false
        end
    end
    return true
end
```

---

# 9. 백트래킹

## 9.1 백트래킹이란

DFS로 가능성의 트리를 탐색하면서, 조건을 만족 못하면 즉시 **되돌아가는(backtrack)** 기법.

뼈대:
```
function backtrack(상태):
    if 종료조건: 결과 저장; return
    for 선택 in 후보들:
        if 유효한가?(선택):
            상태에 적용
            backtrack(다음 상태)
            상태 되돌리기
```

## 9.2 순열 생성

```lua
local function permutations(arr)
    local result = {}
    local n = #arr

    local function backtrack(start)
        if start == n then
            local copy = {}
            for i = 1, n do copy[i] = arr[i] end
            table.insert(result, copy)
            return
        end
        for i = start + 1, n do
            arr[start + 1], arr[i] = arr[i], arr[start + 1]
            backtrack(start + 1)
            arr[start + 1], arr[i] = arr[i], arr[start + 1]
        end
    end

    backtrack(0)
    return result
end

for _, p in ipairs(permutations({1, 2, 3})) do
    print(table.concat(p, " "))
end
-- 1 2 3
-- 1 3 2
-- 2 1 3
-- 2 3 1
-- 3 2 1
-- 3 1 2
```

## 9.3 부분집합 (멱집합)

```lua
local function subsets(arr)
    local result = {}
    local cur = {}

    local function backtrack(start)
        local copy = {}
        for i = 1, #cur do copy[i] = cur[i] end
        table.insert(result, copy)

        for i = start, #arr do
            table.insert(cur, arr[i])
            backtrack(i + 1)
            cur[#cur] = nil
        end
    end

    backtrack(1)
    return result
end

for _, s in ipairs(subsets({1, 2, 3})) do
    print("{" .. table.concat(s, ",") .. "}")
end
-- {} {1} {1,2} {1,2,3} {1,3} {2} {2,3} {3}
```

2ⁿ개의 부분집합. n=20 정도까지 실용적.

## 9.4 조합

n개에서 k개를 고르는 모든 방법.

```lua
local function combinations(n, k)
    local result = {}
    local cur = {}

    local function backtrack(start)
        if #cur == k then
            local c = {}
            for i = 1, k do c[i] = cur[i] end
            table.insert(result, c)
            return
        end
        for i = start, n do
            table.insert(cur, i)
            backtrack(i + 1)
            cur[#cur] = nil
        end
    end

    backtrack(1)
    return result
end

for _, c in ipairs(combinations(4, 2)) do
    print(table.concat(c, " "))
end
-- 1 2
-- 1 3
-- 1 4
-- 2 3
-- 2 4
-- 3 4
```

## 9.5 N-Queens 문제

n×n 체스판에 n개의 퀸을 서로 공격하지 않게 배치.

```lua
local function n_queens(n)
    local solutions = {}
    local board = {}
    for i = 1, n do board[i] = 0 end  -- board[행] = 열

    local function safe(row, col)
        for r = 1, row - 1 do
            if board[r] == col or
               math.abs(board[r] - col) == math.abs(r - row) then
                return false
            end
        end
        return true
    end

    local function backtrack(row)
        if row > n then
            local copy = {}
            for i = 1, n do copy[i] = board[i] end
            table.insert(solutions, copy)
            return
        end
        for col = 1, n do
            if safe(row, col) then
                board[row] = col
                backtrack(row + 1)
            end
        end
    end

    backtrack(1)
    return solutions
end

local sols = n_queens(8)
print("8-queens solutions:", #sols)  -- 92

-- 첫 해 출력
local function print_board(sol)
    for r = 1, #sol do
        for c = 1, #sol do
            io.write(sol[r] == c and "Q " or ". ")
        end
        print()
    end
end
print_board(sols[1])
```

## 9.6 스도쿠 풀이

```lua
local function solve_sudoku(board)
    local function valid(row, col, num)
        for i = 1, 9 do
            if board[row][i] == num or board[i][col] == num then return false end
        end
        local br = ((row - 1) // 3) * 3 + 1
        local bc = ((col - 1) // 3) * 3 + 1
        for r = br, br + 2 do
            for c = bc, bc + 2 do
                if board[r][c] == num then return false end
            end
        end
        return true
    end

    local function backtrack()
        for row = 1, 9 do
            for col = 1, 9 do
                if board[row][col] == 0 then
                    for num = 1, 9 do
                        if valid(row, col, num) then
                            board[row][col] = num
                            if backtrack() then return true end
                            board[row][col] = 0
                        end
                    end
                    return false
                end
            end
        end
        return true
    end

    return backtrack() and board or nil
end

local puzzle = {
    {5,3,0, 0,7,0, 0,0,0},
    {6,0,0, 1,9,5, 0,0,0},
    {0,9,8, 0,0,0, 0,6,0},
    {8,0,0, 0,6,0, 0,0,3},
    {4,0,0, 8,0,3, 0,0,1},
    {7,0,0, 0,2,0, 0,0,6},
    {0,6,0, 0,0,0, 2,8,0},
    {0,0,0, 4,1,9, 0,0,5},
    {0,0,0, 0,8,0, 0,7,9}
}

if solve_sudoku(puzzle) then
    for i = 1, 9 do print(table.concat(puzzle[i], " ")) end
end
```

## 9.7 미로 모든 경로

```lua
local function find_all_paths(maze, start, goal)
    local rows, cols = #maze, #maze[1]
    local visited = {}
    for i = 1, rows do
        visited[i] = {}
        for j = 1, cols do visited[i][j] = false end
    end
    local paths = {}
    local cur_path = {}
    local dirs = {{0,1}, {1,0}, {0,-1}, {-1,0}}

    local function backtrack(r, c)
        if r < 1 or r > rows or c < 1 or c > cols then return end
        if maze[r][c] == 1 or visited[r][c] then return end

        visited[r][c] = true
        table.insert(cur_path, {r, c})

        if r == goal[1] and c == goal[2] then
            local copy = {}
            for i, p in ipairs(cur_path) do copy[i] = {p[1], p[2]} end
            table.insert(paths, copy)
        else
            for _, d in ipairs(dirs) do
                backtrack(r + d[1], c + d[2])
            end
        end

        cur_path[#cur_path] = nil
        visited[r][c] = false
    end

    backtrack(start[1], start[2])
    return paths
end

local maze = {
    {0,0,0,0},
    {0,1,1,0},
    {0,0,0,0},
    {1,0,1,0}
}
local paths = find_all_paths(maze, {1,1}, {4,4})
print("Total paths:", #paths)
for _, p in ipairs(paths) do
    local s = ""
    for _, c in ipairs(p) do s = s .. string.format("(%d,%d)", c[1], c[2]) end
    print(s)
end
```

## 9.8 가지치기 (Pruning)

탐색 공간을 줄이는 것이 백트래킹의 성능 핵심.

```lua
-- N-Queens 가지치기 강화: 비트마스크 사용
local function n_queens_fast(n)
    local count = 0
    local function solve(row, cols, diag1, diag2)
        if row == n then count = count + 1; return end
        local available = ~(cols | diag1 | diag2) & ((1 << n) - 1)
        while available ~= 0 do
            local p = available & -available  -- lowest set bit
            available = available ~ p
            solve(row + 1, cols | p, (diag1 | p) << 1, (diag2 | p) >> 1)
        end
    end
    solve(0, 0, 0, 0)
    return count
end

print(n_queens_fast(12))  -- 14200 (수 초 내)
```

비트 트릭으로 N-Queens가 압도적으로 빨라진다. 13장 참조.

---

# 10. 그래프 알고리즘

자료구조 책에서 다룬 그래프 표현을 가정한다. 여기선 알고리즘에 집중.

## 10.1 그래프 표현 (복습)

```lua
-- 인접 리스트 (가중치)
local graph = {
    A = {{"B", 4}, {"C", 2}},
    B = {{"A", 4}, {"C", 1}, {"D", 5}},
    C = {{"A", 2}, {"B", 1}, {"D", 8}, {"E", 10}},
    D = {{"B", 5}, {"C", 8}, {"E", 2}},
    E = {{"C", 10}, {"D", 2}}
}

local nodes = {"A", "B", "C", "D", "E"}
```

## 10.2 BFS — 너비 우선 탐색

큐로 구현. 무가중치 그래프의 최단 거리를 준다.

```lua
local function bfs(graph, start)
    local visited = {[start] = true}
    local queue = {start}
    local order, head = {}, 1
    while head <= #queue do
        local node = queue[head]; head = head + 1
        table.insert(order, node)
        for _, e in ipairs(graph[node] or {}) do
            local nb = e[1]
            if not visited[nb] then
                visited[nb] = true
                table.insert(queue, nb)
            end
        end
    end
    return order
end

print(table.concat(bfs(graph, "A"), " "))
```

### 무가중치 최단 거리

```lua
local function bfs_distances(graph, start)
    local dist = {[start] = 0}
    local prev = {[start] = nil}
    local queue, head = {start}, 1
    while head <= #queue do
        local u = queue[head]; head = head + 1
        for _, e in ipairs(graph[u] or {}) do
            if dist[e[1]] == nil then
                dist[e[1]] = dist[u] + 1
                prev[e[1]] = u
                table.insert(queue, e[1])
            end
        end
    end
    return dist, prev
end
```

## 10.3 DFS — 깊이 우선 탐색

```lua
-- 재귀
local function dfs(graph, start)
    local visited, order = {}, {}
    local function visit(u)
        if visited[u] then return end
        visited[u] = true
        table.insert(order, u)
        for _, e in ipairs(graph[u] or {}) do visit(e[1]) end
    end
    visit(start)
    return order
end

-- 명시적 스택 (재귀 깊이 우려 시)
local function dfs_iter(graph, start)
    local visited, order = {}, {}
    local stack = {start}
    while #stack > 0 do
        local u = stack[#stack]; stack[#stack] = nil
        if not visited[u] then
            visited[u] = true
            table.insert(order, u)
            for _, e in ipairs(graph[u] or {}) do
                if not visited[e[1]] then table.insert(stack, e[1]) end
            end
        end
    end
    return order
end
```

## 10.4 Dijkstra — 비음수 가중치 최단 경로

```lua
-- Min-heap 우선순위 큐
local function pq_new() return {n = 0, items = {}} end
local function pq_push(pq, v)
    pq.n = pq.n + 1
    pq.items[pq.n] = v
    local i = pq.n
    while i > 1 do
        local p = i // 2
        if pq.items[i][2] < pq.items[p][2] then
            pq.items[i], pq.items[p] = pq.items[p], pq.items[i]; i = p
        else break end
    end
end
local function pq_pop(pq)
    local top = pq.items[1]
    pq.items[1] = pq.items[pq.n]; pq.items[pq.n] = nil; pq.n = pq.n - 1
    local i = 1
    while 2 * i <= pq.n do
        local c = 2 * i
        if c < pq.n and pq.items[c+1][2] < pq.items[c][2] then c = c + 1 end
        if pq.items[i][2] <= pq.items[c][2] then break end
        pq.items[i], pq.items[c] = pq.items[c], pq.items[i]; i = c
    end
    return top
end

local function dijkstra(graph, start)
    local dist, prev = {}, {}
    for k in pairs(graph) do dist[k] = math.huge end
    dist[start] = 0
    local pq = pq_new()
    pq_push(pq, {start, 0})

    while pq.n > 0 do
        local top = pq_pop(pq)
        local u, d = top[1], top[2]
        if d <= dist[u] then
            for _, e in ipairs(graph[u]) do
                local v, w = e[1], e[2]
                local alt = d + w
                if alt < dist[v] then
                    dist[v] = alt
                    prev[v] = u
                    pq_push(pq, {v, alt})
                end
            end
        end
    end
    return dist, prev
end

local d, p = dijkstra(graph, "A")
for _, n in ipairs(nodes) do
    print(n, d[n])
end
```

## 10.5 Bellman-Ford — 음수 간선 허용

```lua
local function bellman_ford(graph, start)
    local dist = {}
    for k in pairs(graph) do dist[k] = math.huge end
    dist[start] = 0

    local edges = {}
    for u, neigh in pairs(graph) do
        for _, e in ipairs(neigh) do
            table.insert(edges, {u, e[1], e[2]})
        end
    end

    local n = 0
    for _ in pairs(graph) do n = n + 1 end

    for _ = 1, n - 1 do
        for _, e in ipairs(edges) do
            if dist[e[1]] + e[3] < dist[e[2]] then
                dist[e[2]] = dist[e[1]] + e[3]
            end
        end
    end

    -- 음수 사이클 검출
    for _, e in ipairs(edges) do
        if dist[e[1]] + e[3] < dist[e[2]] then
            return nil, "negative cycle"
        end
    end
    return dist
end
```

## 10.6 Floyd-Warshall — 모든 쌍 최단 경로

```lua
local function floyd_warshall(nodes, edges)
    local dist = {}
    for _, u in ipairs(nodes) do
        dist[u] = {}
        for _, v in ipairs(nodes) do
            dist[u][v] = (u == v) and 0 or math.huge
        end
    end
    for _, e in ipairs(edges) do
        dist[e[1]][e[2]] = e[3]
    end

    for _, k in ipairs(nodes) do
        for _, i in ipairs(nodes) do
            for _, j in ipairs(nodes) do
                if dist[i][k] + dist[k][j] < dist[i][j] then
                    dist[i][j] = dist[i][k] + dist[k][j]
                end
            end
        end
    end
    return dist
end

local nodes = {"A", "B", "C", "D"}
local edges = {{"A","B",3}, {"A","C",6}, {"B","C",2},
               {"B","D",1}, {"C","D",2}}
local d = floyd_warshall(nodes, edges)
for _, u in ipairs(nodes) do
    for _, v in ipairs(nodes) do
        io.write(string.format("%4s ", d[u][v] == math.huge and "∞" or tostring(d[u][v])))
    end
    print()
end
```

O(V³). V가 작을 때 좋다.

## 10.7 위상 정렬 — Kahn 알고리즘

```lua
local function topological_sort(graph, nodes)
    local indeg = {}
    for _, n in ipairs(nodes) do indeg[n] = 0 end
    for _, neigh in pairs(graph) do
        for _, e in ipairs(neigh) do
            indeg[e[1]] = indeg[e[1]] + 1
        end
    end

    local queue, head = {}, 1
    for _, n in ipairs(nodes) do
        if indeg[n] == 0 then table.insert(queue, n) end
    end

    local order = {}
    while head <= #queue do
        local u = queue[head]; head = head + 1
        table.insert(order, u)
        for _, e in ipairs(graph[u] or {}) do
            indeg[e[1]] = indeg[e[1]] - 1
            if indeg[e[1]] == 0 then table.insert(queue, e[1]) end
        end
    end

    if #order ~= #nodes then return nil, "cycle" end
    return order
end

local dag = {
    ["코드"] = {{"테스트", 0}, {"문서", 0}},
    ["테스트"] = {{"리뷰", 0}},
    ["문서"] = {{"리뷰", 0}},
    ["리뷰"] = {{"배포", 0}},
    ["배포"] = {}
}
local nodes = {"코드", "테스트", "문서", "리뷰", "배포"}
print(table.concat(topological_sort(dag, nodes), " -> "))
```

## 10.8 강결합 요소 (SCC) — Tarjan 알고리즘

```lua
local function tarjan_scc(graph, nodes)
    local idx, low, on_stack = {}, {}, {}
    local stack, sccs = {}, {}
    local index = 0

    local function strongconnect(v)
        index = index + 1
        idx[v] = index
        low[v] = index
        table.insert(stack, v)
        on_stack[v] = true

        for _, e in ipairs(graph[v] or {}) do
            local w = e[1]
            if idx[w] == nil then
                strongconnect(w)
                low[v] = math.min(low[v], low[w])
            elseif on_stack[w] then
                low[v] = math.min(low[v], idx[w])
            end
        end

        if low[v] == idx[v] then
            local component = {}
            while true do
                local w = table.remove(stack)
                on_stack[w] = false
                table.insert(component, w)
                if w == v then break end
            end
            table.insert(sccs, component)
        end
    end

    for _, v in ipairs(nodes) do
        if idx[v] == nil then strongconnect(v) end
    end
    return sccs
end
```

## 10.9 최소 신장 트리 — Kruskal

```lua
-- Union-Find
local function uf_new(items)
    local p, r = {}, {}
    for _, x in ipairs(items) do p[x] = x; r[x] = 0 end
    return {parent = p, rank = r}
end
local function uf_find(uf, x)
    if uf.parent[x] ~= x then uf.parent[x] = uf_find(uf, uf.parent[x]) end
    return uf.parent[x]
end
local function uf_union(uf, x, y)
    local rx, ry = uf_find(uf, x), uf_find(uf, y)
    if rx == ry then return false end
    if uf.rank[rx] < uf.rank[ry] then uf.parent[rx] = ry
    elseif uf.rank[rx] > uf.rank[ry] then uf.parent[ry] = rx
    else uf.parent[ry] = rx; uf.rank[rx] = uf.rank[rx] + 1 end
    return true
end

local function kruskal(nodes, edges)
    local sorted = {}
    for i, e in ipairs(edges) do sorted[i] = e end
    table.sort(sorted, function(a, b) return a[3] < b[3] end)

    local uf = uf_new(nodes)
    local mst, total = {}, 0
    for _, e in ipairs(sorted) do
        if uf_union(uf, e[1], e[2]) then
            table.insert(mst, e)
            total = total + e[3]
        end
    end
    return mst, total
end

local edges = {
    {"A","B",4}, {"A","C",1}, {"B","C",2},
    {"B","D",5}, {"C","D",8}, {"C","E",10}, {"D","E",2}
}
local mst, total = kruskal({"A","B","C","D","E"}, edges)
for _, e in ipairs(mst) do print(e[1], e[2], e[3]) end
print("Total:", total)
```

## 10.10 MST — Prim

```lua
local function prim(graph, start)
    local in_mst = {}
    local pq = pq_new()
    pq_push(pq, {start, nil, 0})
    local total, edges = 0, {}

    while pq.n > 0 do
        local top = pq_pop(pq)
        local u, parent, w = top[1], top[2], top[3]
        if not in_mst[u] then
            in_mst[u] = true
            total = total + w
            if parent then table.insert(edges, {parent, u, w}) end
            for _, e in ipairs(graph[u] or {}) do
                if not in_mst[e[1]] then
                    pq_push(pq, {e[1], u, e[2]})
                end
            end
        end
    end
    return edges, total
end
```

## 10.11 A* 알고리즘

휴리스틱을 활용한 최단 경로. Dijkstra의 일반화.

```lua
local function manhattan(a, b)
    return math.abs(a[1] - b[1]) + math.abs(a[2] - b[2])
end

local function a_star(grid, start, goal)
    local rows, cols = #grid, #grid[1]
    local function key(p) return p[1] * 10000 + p[2] end
    local g = {[key(start)] = 0}
    local came = {}

    local pq = pq_new()
    pq_push(pq, {start, manhattan(start, goal)})

    while pq.n > 0 do
        local top = pq_pop(pq)
        local cur = top[1]
        if cur[1] == goal[1] and cur[2] == goal[2] then
            local path = {cur}
            local k = key(cur)
            while came[k] do
                local p = came[k]
                table.insert(path, 1, p)
                k = key(p)
            end
            return path
        end
        for _, d in ipairs({{0,1},{1,0},{0,-1},{-1,0}}) do
            local n = {cur[1] + d[1], cur[2] + d[2]}
            if n[1] >= 1 and n[1] <= rows and n[2] >= 1 and n[2] <= cols
               and grid[n[1]][n[2]] == 0 then
                local tentative = (g[key(cur)] or math.huge) + 1
                if tentative < (g[key(n)] or math.huge) then
                    came[key(n)] = cur
                    g[key(n)] = tentative
                    pq_push(pq, {n, tentative + manhattan(n, goal)})
                end
            end
        end
    end
    return nil
end

local grid = {
    {0,0,0,0,0},
    {0,1,1,0,0},
    {0,0,0,0,0},
    {0,1,1,1,0},
    {0,0,0,0,0}
}
local path = a_star(grid, {1,1}, {5,5})
for _, p in ipairs(path) do io.write(string.format("(%d,%d) ", p[1], p[2])) end
print()
```

게임 길찾기의 표준.

---

# 11. 문자열 알고리즘

## 11.1 단순 패턴 매칭 — O(n×m)

```lua
local function naive_match(text, pattern)
    local n, m = #text, #pattern
    local positions = {}
    for i = 1, n - m + 1 do
        local j = 1
        while j <= m and text:sub(i + j - 1, i + j - 1) == pattern:sub(j, j) do
            j = j + 1
        end
        if j > m then table.insert(positions, i) end
    end
    return positions
end

print(table.concat(naive_match("ababcabab", "abab"), " "))  -- 1 6
```

## 11.2 KMP 알고리즘 — O(n + m)

실패 함수(failure function)를 미리 계산해 패턴을 한 칸씩 미는 게 아니라 더 효율적으로 민다.

```lua
local function kmp_table(pattern)
    local m = #pattern
    local pi = {0}
    local k = 0
    for i = 2, m do
        while k > 0 and pattern:sub(k+1, k+1) ~= pattern:sub(i, i) do
            k = pi[k]
        end
        if pattern:sub(k+1, k+1) == pattern:sub(i, i) then
            k = k + 1
        end
        pi[i] = k
    end
    return pi
end

local function kmp_search(text, pattern)
    local pi = kmp_table(pattern)
    local n, m = #text, #pattern
    local positions = {}
    local q = 0
    for i = 1, n do
        while q > 0 and pattern:sub(q+1, q+1) ~= text:sub(i, i) do
            q = pi[q]
        end
        if pattern:sub(q+1, q+1) == text:sub(i, i) then
            q = q + 1
        end
        if q == m then
            table.insert(positions, i - m + 1)
            q = pi[q]
        end
    end
    return positions
end

print(table.concat(kmp_search("ababababcababab", "abab"), " "))
-- 1 3 5 9 11 13
```

## 11.3 Rabin-Karp — 해시 기반 매칭

```lua
local function rabin_karp(text, pattern)
    local d = 256
    local q = 101  -- 소수
    local n, m = #text, #pattern
    if m > n then return {} end

    local h = 1
    for _ = 1, m - 1 do h = (h * d) % q end

    local p, t = 0, 0
    for i = 1, m do
        p = (d * p + pattern:byte(i)) % q
        t = (d * t + text:byte(i)) % q
    end

    local positions = {}
    for i = 1, n - m + 1 do
        if p == t then
            local match = true
            for j = 1, m do
                if text:sub(i + j - 1, i + j - 1) ~= pattern:sub(j, j) then
                    match = false; break
                end
            end
            if match then table.insert(positions, i) end
        end
        if i < n - m + 1 then
            t = (d * (t - text:byte(i) * h) + text:byte(i + m)) % q
            if t < 0 then t = t + q end
        end
    end
    return positions
end

print(table.concat(rabin_karp("AABAACAADAABAABA", "AABA"), " "))
-- 1 9 13
```

여러 패턴을 동시에 검색할 때 강점이 있다.

## 11.4 Z 알고리즘

각 위치 i에서 시작하는 부분문자열이 원래 문자열의 접두사와 얼마나 일치하는지를 계산.

```lua
local function z_function(s)
    local n = #s
    local z = {0}
    for i = 1, n do z[i + 1] = 0 end
    local l, r = 0, 0
    for i = 2, n do
        if i <= r then
            z[i] = math.min(r - i + 1, z[i - l + 1])
        end
        while i + z[i] <= n and s:sub(z[i] + 1, z[i] + 1) == s:sub(i + z[i], i + z[i]) do
            z[i] = z[i] + 1
        end
        if i + z[i] - 1 > r then
            l, r = i, i + z[i] - 1
        end
    end
    return z
end

-- 패턴 매칭: pattern + "$" + text 의 z 함수에서 z[i] == #pattern인 곳
local function z_search(text, pattern)
    local combined = pattern .. "$" .. text
    local z = z_function(combined)
    local m = #pattern
    local result = {}
    for i = m + 2, #combined do
        if z[i] == m then
            table.insert(result, i - m - 1)
        end
    end
    return result
end

print(table.concat(z_search("ababcababd", "ab"), " "))  -- 1 3 6 8
```

## 11.5 Manacher — 최장 회문 부분문자열 O(n)

```lua
local function longest_palindrome(s)
    -- 짝/홀 케이스 통합: a#b#a#b → ^#a#b#a#b#$
    local t = "^"
    for i = 1, #s do t = t .. "#" .. s:sub(i, i) end
    t = t .. "#$"

    local n = #t
    local p = {}
    for i = 1, n do p[i] = 0 end
    local center, right = 1, 1

    for i = 2, n - 1 do
        if i < right then
            p[i] = math.min(right - i, p[2 * center - i])
        end
        while t:sub(i + 1 + p[i], i + 1 + p[i]) == t:sub(i - 1 - p[i], i - 1 - p[i]) do
            p[i] = p[i] + 1
        end
        if i + p[i] > right then
            center, right = i, i + p[i]
        end
    end

    local max_len, max_center = 0, 0
    for i = 1, n do
        if p[i] > max_len then
            max_len = p[i]; max_center = i
        end
    end
    local start = (max_center - max_len) // 2
    return s:sub(start + 1, start + max_len)
end

print(longest_palindrome("babad"))      -- "bab" or "aba"
print(longest_palindrome("cbbd"))       -- "bb"
print(longest_palindrome("forgeeksskeegfor")) -- "geeksskeeg"
```

## 11.6 트라이로 멀티 패턴 검색

```lua
local function trie_new() return {children = {}, end_of = false} end

local function trie_insert(t, word)
    local n = t
    for i = 1, #word do
        local c = word:sub(i, i)
        if not n.children[c] then n.children[c] = trie_new() end
        n = n.children[c]
    end
    n.end_of = true
end

local function multi_search(text, patterns)
    local t = trie_new()
    for _, p in ipairs(patterns) do trie_insert(t, p) end

    local hits = {}
    for i = 1, #text do
        local n = t
        local j = i
        while j <= #text do
            local c = text:sub(j, j)
            if not n.children[c] then break end
            n = n.children[c]
            if n.end_of then
                table.insert(hits, {i, j})
            end
            j = j + 1
        end
    end
    return hits
end

local hits = multi_search("hellohehey", {"he", "hello", "hey"})
for _, h in ipairs(hits) do print(h[1], h[2]) end
```

Aho-Corasick으로 진화시키면 O(n + m + 매칭수).

## 11.7 문자열 거꾸로 / 회전

```lua
local function reverse_string(s)
    local r = {}
    for i = #s, 1, -1 do r[#r + 1] = s:sub(i, i) end
    return table.concat(r)
end

print(reverse_string("hello"))  -- "olleh"

-- 단어 단위 뒤집기 (in-place느낌으로 효율적)
local function reverse_words(s)
    local words = {}
    for w in s:gmatch("%S+") do table.insert(words, 1, w) end
    return table.concat(words, " ")
end

print(reverse_words("the quick brown fox"))  -- "fox brown quick the"
```

## 11.8 애너그램

```lua
local function are_anagrams(a, b)
    if #a ~= #b then return false end
    local count = {}
    for i = 1, #a do
        local c = a:sub(i, i)
        count[c] = (count[c] or 0) + 1
    end
    for i = 1, #b do
        local c = b:sub(i, i)
        if not count[c] or count[c] == 0 then return false end
        count[c] = count[c] - 1
    end
    return true
end

print(are_anagrams("listen", "silent"))  -- true
print(are_anagrams("hello", "world"))    -- false
```

## 11.9 문자열 압축 (Run-length encoding)

```lua
local function rle_encode(s)
    if #s == 0 then return "" end
    local result, count = {}, 1
    for i = 2, #s do
        if s:sub(i, i) == s:sub(i-1, i-1) then
            count = count + 1
        else
            table.insert(result, s:sub(i-1, i-1))
            table.insert(result, tostring(count))
            count = 1
        end
    end
    table.insert(result, s:sub(#s, #s))
    table.insert(result, tostring(count))
    return table.concat(result)
end

local function rle_decode(s)
    local result = {}
    for c, n in s:gmatch("(%a)(%d+)") do
        table.insert(result, c:rep(tonumber(n)))
    end
    return table.concat(result)
end

print(rle_encode("aaabbbcccccd"))   -- "a3b3c5d1"
print(rle_decode("a3b3c5d1"))       -- "aaabbbcccccd"
```

---

# 12. 수학과 정수론 알고리즘

## 12.1 최대공약수 — 유클리드

```lua
local function gcd(a, b)
    while b ~= 0 do
        a, b = b, a % b
    end
    return a
end

print(gcd(48, 18))   -- 6
print(gcd(100, 75))  -- 25
```

재귀 버전:

```lua
local function gcd_rec(a, b)
    if b == 0 then return a end
    return gcd_rec(b, a % b)
end
```

최소공배수:

```lua
local function lcm(a, b) return a // gcd(a, b) * b end
print(lcm(4, 6))  -- 12
```

## 12.2 확장 유클리드

ax + by = gcd(a, b)의 정수해 (x, y)를 함께 찾는다.

```lua
local function ext_gcd(a, b)
    if b == 0 then return a, 1, 0 end
    local g, x1, y1 = ext_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1
end

local g, x, y = ext_gcd(35, 15)
print(g, x, y)              -- 5  1  -2
print(35 * x + 15 * y)      -- 5
```

모듈러 역원의 기초.

## 12.3 모듈러 역원

`a × x ≡ 1 (mod m)`을 만족하는 x.

```lua
local function mod_inverse(a, m)
    local g, x, _ = ext_gcd(a, m)
    if g ~= 1 then return nil end
    return (x % m + m) % m
end

print(mod_inverse(3, 11))  -- 4 (3 * 4 = 12 ≡ 1 mod 11)
```

페르마의 소정리로 m이 소수일 때:

```lua
local function pow_mod(base, exp, mod)
    local r = 1
    base = base % mod
    while exp > 0 do
        if exp & 1 == 1 then r = (r * base) % mod end
        base = (base * base) % mod
        exp = exp >> 1
    end
    return r
end

local function mod_inverse_fermat(a, p)
    return pow_mod(a, p - 2, p)
end

print(mod_inverse_fermat(3, 11))  -- 4
```

## 12.4 에라토스테네스의 체

n까지의 모든 소수.

```lua
local function sieve(n)
    local is_prime = {}
    for i = 2, n do is_prime[i] = true end
    for i = 2, math.floor(math.sqrt(n)) do
        if is_prime[i] then
            for j = i*i, n, i do is_prime[j] = false end
        end
    end
    local primes = {}
    for i = 2, n do
        if is_prime[i] then table.insert(primes, i) end
    end
    return primes
end

local p = sieve(50)
print(table.concat(p, " "))
-- 2 3 5 7 11 13 17 19 23 29 31 37 41 43 47
```

## 12.5 선형 시간 체

각 합성수가 정확히 한 번씩 걸러진다.

```lua
local function linear_sieve(n)
    local primes, smallest = {}, {}
    for i = 2, n do
        if not smallest[i] then
            smallest[i] = i
            table.insert(primes, i)
        end
        for _, p in ipairs(primes) do
            if p > smallest[i] or i * p > n then break end
            smallest[i * p] = p
        end
    end
    return primes, smallest
end
```

소인수분해와 결합하면 빠르다.

## 12.6 소인수분해

```lua
local function factorize(n)
    local factors = {}
    local d = 2
    while d * d <= n do
        while n % d == 0 do
            table.insert(factors, d)
            n = n // d
        end
        d = d + 1
    end
    if n > 1 then table.insert(factors, n) end
    return factors
end

print(table.concat(factorize(360), " "))  -- 2 2 2 3 3 5
```

## 12.7 빠른 소수 판정 — Miller-Rabin

```lua
local function miller_rabin(n, witnesses)
    if n < 2 then return false end
    for _, w in ipairs({2, 3, 5, 7, 11, 13}) do
        if n == w then return true end
        if n % w == 0 then return false end
    end

    local d, r = n - 1, 0
    while d % 2 == 0 do d = d // 2; r = r + 1 end

    witnesses = witnesses or {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37}
    for _, a in ipairs(witnesses) do
        if a >= n then break end
        local x = pow_mod(a, d, n)
        if x ~= 1 and x ~= n - 1 then
            local prime = false
            for _ = 1, r - 1 do
                x = (x * x) % n
                if x == n - 1 then prime = true; break end
            end
            if not prime then return false end
        end
    end
    return true
end

print(miller_rabin(1000000007))  -- true
print(miller_rabin(1000000009))  -- true
print(miller_rabin(1000000011))  -- false
```

## 12.8 조합 (nCk)

```lua
-- 파스칼의 삼각형
local function binomial_table(n)
    local C = {}
    for i = 0, n do C[i] = {} end
    for i = 0, n do
        C[i][0] = 1
        for j = 1, i do
            C[i][j] = (i == j) and 1 or (C[i-1][j-1] + (C[i-1][j] or 0))
        end
    end
    return C
end

local C = binomial_table(10)
print(C[10][3])  -- 120

-- 모듈러 환경에서 nCk
local function nCk_mod(n, k, p)
    if k < 0 or k > n then return 0 end
    local num, den = 1, 1
    for i = 1, k do
        num = (num * ((n - i + 1) % p)) % p
        den = (den * i) % p
    end
    return (num * mod_inverse_fermat(den, p)) % p
end
```

## 12.9 카탈란 수

`Cn = (2n)!/((n+1)!n!)`. 괄호 짝, 이진 트리 개수, 다각형 분할 등.

```lua
local function catalan(n)
    local c = {1}
    for i = 1, n do
        c[i + 1] = 0
        for j = 0, i - 1 do
            c[i + 1] = c[i + 1] + c[j + 1] * c[i - j]
        end
    end
    return c[n + 1]
end

for i = 0, 10 do print(i, catalan(i)) end
-- 0 1
-- 1 1
-- 2 2
-- 3 5
-- 4 14
-- 5 42
-- ...
```

## 12.10 행렬 거듭제곱과 피보나치

```lua
local function mat_mul(a, b)
    return {
        {a[1][1]*b[1][1] + a[1][2]*b[2][1], a[1][1]*b[1][2] + a[1][2]*b[2][2]},
        {a[2][1]*b[1][1] + a[2][2]*b[2][1], a[2][1]*b[1][2] + a[2][2]*b[2][2]}
    }
end

local function mat_pow(m, p)
    local result = {{1, 0}, {0, 1}}
    while p > 0 do
        if p & 1 == 1 then result = mat_mul(result, m) end
        m = mat_mul(m, m)
        p = p >> 1
    end
    return result
end

local function fib(n)
    if n == 0 then return 0 end
    local m = mat_pow({{1, 1}, {1, 0}}, n)
    return m[1][2]
end

print(fib(10))   -- 55
print(fib(50))   -- 12586269025
```

O(log n)에 피보나치를 구한다.

## 12.11 중국인의 나머지 정리

```lua
local function crt(r, m)
    local M = 1
    for _, x in ipairs(m) do M = M * x end
    local result = 0
    for i, ri in ipairs(r) do
        local Mi = M // m[i]
        local _, _, _ = ext_gcd(Mi, m[i])
        local inv = mod_inverse(Mi, m[i])
        result = (result + ri * Mi * inv) % M
    end
    return result, M
end

-- x ≡ 2 (mod 3), x ≡ 3 (mod 5), x ≡ 2 (mod 7)
local x, M = crt({2, 3, 2}, {3, 5, 7})
print(x, M)  -- 23  105
```

---

# 13. 비트 조작

## 13.1 Lua의 비트 연산자 (5.3+)

```lua
local a, b = 0xFF, 0x0F
print(a & b)   -- 15  (AND)
print(a | b)   -- 255 (OR)
print(a ~ b)   -- 240 (XOR)
print(~a)      -- -256 (NOT, 부호 있는 64비트)
print(a << 4)  -- 4080 (왼쪽 시프트)
print(a >> 4)  -- 15   (오른쪽 시프트)
```

## 13.2 흔한 비트 트릭

### 짝수/홀수 판정

```lua
local function is_even(n) return n & 1 == 0 end
```

### 2의 거듭제곱?

```lua
local function is_power_of_two(n)
    return n > 0 and (n & (n - 1)) == 0
end

print(is_power_of_two(16))   -- true
print(is_power_of_two(15))   -- false
```

`n - 1`은 가장 낮은 1 비트 아래를 모두 1로 만든다. AND가 0이면 그 한 비트가 유일.

### i번째 비트 설정/해제/토글

```lua
local function set_bit(n, i)    return n | (1 << i) end
local function clear_bit(n, i)  return n & ~(1 << i) end
local function toggle_bit(n, i) return n ~ (1 << i) end
local function get_bit(n, i)    return (n >> i) & 1 end
```

### 가장 낮은 1 비트 추출

```lua
local function lowest_bit(n) return n & -n end
print(lowest_bit(12))  -- 4 (1100 → 100)
```

펜윅 트리의 핵심.

### 비트 개수 (popcount)

```lua
local function popcount(n)
    local count = 0
    while n > 0 do
        count = count + (n & 1)
        n = n >> 1
    end
    return count
end

-- Brian Kernighan: 1인 비트 수만큼만 도는 빠른 버전
local function popcount_fast(n)
    local count = 0
    while n > 0 do
        n = n & (n - 1)
        count = count + 1
    end
    return count
end

print(popcount_fast(0xFF))  -- 8
print(popcount_fast(0x0F0F))  -- 8
```

## 13.3 비트마스크로 부분집합

n개 원소의 부분집합을 정수의 비트로 표현.

```lua
local items = {"apple", "banana", "cherry", "date"}
local n = #items

for mask = 0, (1 << n) - 1 do
    local subset = {}
    for i = 0, n - 1 do
        if mask & (1 << i) ~= 0 then
            table.insert(subset, items[i + 1])
        end
    end
    print("{" .. table.concat(subset, ",") .. "}")
end
```

## 13.4 비트마스크 DP — 외판원 문제 (TSP)

n이 작을 때 (n ≤ 20).

```lua
local function tsp(dist)
    local n = #dist
    local INF = math.huge
    local dp = {}
    for mask = 0, (1 << n) - 1 do
        dp[mask] = {}
        for i = 1, n do dp[mask][i] = INF end
    end
    dp[1][1] = 0  -- 시작: 도시 1만 방문, 현재 1번에

    for mask = 1, (1 << n) - 1 do
        for u = 1, n do
            if mask & (1 << (u-1)) ~= 0 and dp[mask][u] < INF then
                for v = 1, n do
                    if mask & (1 << (v-1)) == 0 then
                        local new_mask = mask | (1 << (v-1))
                        local cost = dp[mask][u] + dist[u][v]
                        if cost < dp[new_mask][v] then
                            dp[new_mask][v] = cost
                        end
                    end
                end
            end
        end
    end

    local full = (1 << n) - 1
    local best = INF
    for u = 2, n do
        local total = dp[full][u] + dist[u][1]
        if total < best then best = total end
    end
    return best
end

local d = {
    {0, 10, 15, 20},
    {10, 0, 35, 25},
    {15, 35, 0, 30},
    {20, 25, 30, 0}
}
print(tsp(d))  -- 80
```

O(n²·2ⁿ)이지만 n=20에서도 동작.

## 13.5 XOR 트릭

### 한 번만 나타난 수 찾기

배열에서 모든 수가 두 번씩 나타나는데 하나만 한 번. XOR의 자기소거 성질로 O(n), O(1).

```lua
local function single_number(arr)
    local x = 0
    for _, v in ipairs(arr) do x = x ~ v end
    return x
end

print(single_number({2, 3, 5, 4, 5, 3, 4}))  -- 2
```

### 두 수 교환 without temp

```lua
local a, b = 5, 7
a = a ~ b
b = a ~ b
a = a ~ b
print(a, b)  -- 7  5
```

### 두 변수의 차이 비트만 1로

```lua
local function diff_bits(a, b)
    return popcount_fast(a ~ b)
end
print(diff_bits(0b1010, 0b1101))  -- 4
```

## 13.6 그레이 코드

연속한 두 수의 비트가 정확히 하나만 다른 인코딩.

```lua
local function gray_code(n)
    local result = {}
    for i = 0, (1 << n) - 1 do
        result[i + 1] = i ~ (i >> 1)
    end
    return result
end

for _, g in ipairs(gray_code(3)) do
    print(string.format("%d (%03d)", g, tonumber(string.format("%o", g))))
end
```

## 13.7 비트보드

체스, 오목 등의 보드 게임을 비트로 표현하면 매우 빠르다.

```lua
-- 4x4 보드
local function print_board(board)
    for r = 0, 3 do
        for c = 0, 3 do
            local bit = 1 << (r * 4 + c)
            io.write(board & bit ~= 0 and "X " or ". ")
        end
        print()
    end
end

local board = 0
board = board | (1 << 5)   -- (1, 1)
board = board | (1 << 10)  -- (2, 2)
print_board(board)
-- . . . .
-- . X . .
-- . . X .
-- . . . .
```

---

# 14. 기하 알고리즘

## 14.1 점, 벡터, 거리

```lua
local function dist(p, q)
    return math.sqrt((p[1] - q[1])^2 + (p[2] - q[2])^2)
end

local function dist_sq(p, q)
    return (p[1] - q[1])^2 + (p[2] - q[2])^2
end

print(dist({0, 0}, {3, 4}))  -- 5.0
```

비교만 한다면 `dist_sq`로 sqrt를 피하자.

## 14.2 외적과 시계/반시계

```lua
local function cross(o, a, b)
    return (a[1] - o[1]) * (b[2] - o[2]) - (a[2] - o[2]) * (b[1] - o[1])
end

-- > 0: 반시계 / < 0: 시계 / 0: 일직선
print(cross({0,0}, {1,0}, {0,1}))   -- 1 (반시계)
print(cross({0,0}, {1,0}, {0,-1}))  -- -1 (시계)
print(cross({0,0}, {1,0}, {2,0}))   -- 0 (일직선)
```

## 14.3 두 선분 교차 판정

```lua
local function on_segment(p, q, r)
    return q[1] <= math.max(p[1], r[1]) and q[1] >= math.min(p[1], r[1])
       and q[2] <= math.max(p[2], r[2]) and q[2] >= math.min(p[2], r[2])
end

local function segments_intersect(p1, q1, p2, q2)
    local function ori(a, b, c)
        local v = cross(a, b, c)
        if v > 0 then return 1 end
        if v < 0 then return -1 end
        return 0
    end

    local o1 = ori(p1, q1, p2)
    local o2 = ori(p1, q1, q2)
    local o3 = ori(p2, q2, p1)
    local o4 = ori(p2, q2, q1)

    if o1 ~= o2 and o3 ~= o4 then return true end

    if o1 == 0 and on_segment(p1, p2, q1) then return true end
    if o2 == 0 and on_segment(p1, q2, q1) then return true end
    if o3 == 0 and on_segment(p2, p1, q2) then return true end
    if o4 == 0 and on_segment(p2, q1, q2) then return true end
    return false
end

print(segments_intersect({1,1}, {10,1}, {1,2}, {10,2}))  -- false
print(segments_intersect({10,0}, {0,10}, {0,0}, {10,10}))  -- true
```

## 14.4 다각형 면적 — Shoelace

```lua
local function polygon_area(pts)
    local n = #pts
    local area = 0
    for i = 1, n do
        local j = (i % n) + 1
        area = area + pts[i][1] * pts[j][2]
        area = area - pts[j][1] * pts[i][2]
    end
    return math.abs(area) / 2
end

print(polygon_area({{0,0}, {4,0}, {4,3}, {0,3}}))  -- 12.0
print(polygon_area({{0,0}, {4,0}, {2,3}}))         -- 6.0
```

## 14.5 점이 다각형 안에 있는가? (Ray Casting)

```lua
local function point_in_polygon(p, polygon)
    local n = #polygon
    local inside = false
    local j = n
    for i = 1, n do
        local pi, pj = polygon[i], polygon[j]
        if ((pi[2] > p[2]) ~= (pj[2] > p[2])) and
           (p[1] < (pj[1] - pi[1]) * (p[2] - pi[2]) / (pj[2] - pi[2]) + pi[1]) then
            inside = not inside
        end
        j = i
    end
    return inside
end

local poly = {{0,0}, {4,0}, {4,4}, {0,4}}
print(point_in_polygon({2, 2}, poly))   -- true
print(point_in_polygon({5, 5}, poly))   -- false
```

## 14.6 볼록 껍질 (Convex Hull) — Andrew의 단조 체인

```lua
local function convex_hull(points)
    table.sort(points, function(a, b)
        if a[1] ~= b[1] then return a[1] < b[1] end
        return a[2] < b[2]
    end)

    local n = #points
    if n < 3 then return points end

    local hull = {}

    -- 아래 껍질
    for i = 1, n do
        while #hull >= 2 and cross(hull[#hull-1], hull[#hull], points[i]) <= 0 do
            hull[#hull] = nil
        end
        hull[#hull + 1] = points[i]
    end

    -- 위 껍질
    local lower = #hull + 1
    for i = n - 1, 1, -1 do
        while #hull >= lower and cross(hull[#hull-1], hull[#hull], points[i]) <= 0 do
            hull[#hull] = nil
        end
        hull[#hull + 1] = points[i]
    end

    hull[#hull] = nil  -- 시작점 중복 제거
    return hull
end

local pts = {{0,0}, {1,1}, {2,2}, {3,1}, {3,0}, {0,3}, {3,3}}
for _, p in ipairs(convex_hull(pts)) do
    print(p[1], p[2])
end
```

O(n log n).

## 14.7 가까운 두 점 — 분할정복 O(n log n)

```lua
local function closest_pair(points)
    local n = #points
    local sorted = {}
    for i, p in ipairs(points) do sorted[i] = p end
    table.sort(sorted, function(a, b) return a[1] < b[1] end)

    local function rec(lo, hi)
        if hi - lo + 1 <= 3 then
            local best = math.huge
            for i = lo, hi do
                for j = i + 1, hi do
                    best = math.min(best, dist(sorted[i], sorted[j]))
                end
            end
            return best
        end
        local mid = (lo + hi) // 2
        local mx = sorted[mid][1]
        local d = math.min(rec(lo, mid), rec(mid + 1, hi))

        local strip = {}
        for i = lo, hi do
            if math.abs(sorted[i][1] - mx) < d then
                table.insert(strip, sorted[i])
            end
        end
        table.sort(strip, function(a, b) return a[2] < b[2] end)
        for i = 1, #strip do
            local j = i + 1
            while j <= #strip and (strip[j][2] - strip[i][2]) < d do
                d = math.min(d, dist(strip[i], strip[j]))
                j = j + 1
            end
        end
        return d
    end

    return rec(1, n)
end

local pts = {{2,3}, {12,30}, {40,50}, {5,1}, {12,10}, {3,4}}
print(closest_pair(pts))  -- 1.414...
```

---

# 15. 근사와 휴리스틱

## 15.1 정확한 답이 너무 비쌀 때

NP-hard 문제(외판원, 배낭, 그래프 색칠 등)는 작은 입력엔 정확한 알고리즘이 가능하지만 큰 입력엔 근사/휴리스틱이 필요하다.

## 15.2 외판원 — 가장 가까운 이웃 휴리스틱

```lua
local function tsp_nearest(dist)
    local n = #dist
    local visited = {[1] = true}
    local route = {1}
    local cur = 1
    local total = 0

    for _ = 2, n do
        local next_city, min_d = nil, math.huge
        for v = 1, n do
            if not visited[v] and dist[cur][v] < min_d then
                min_d = dist[cur][v]
                next_city = v
            end
        end
        visited[next_city] = true
        table.insert(route, next_city)
        total = total + min_d
        cur = next_city
    end
    total = total + dist[cur][1]
    table.insert(route, 1)
    return route, total
end

local d = {
    {0, 10, 15, 20},
    {10, 0, 35, 25},
    {15, 35, 0, 30},
    {20, 25, 30, 0}
}
local route, total = tsp_nearest(d)
print(table.concat(route, "->"), total)
-- 1->2->4->3->1   95   (정답 80에 비해 약간 큼)
```

가장 가까운 이웃은 빠르지만 보통 25% 정도 손해. 출발점만 바꾸어도 결과가 달라진다.

## 15.3 2-opt 개선

기존 경로에서 두 간선을 끊고 뒤집어보면서 개선.

```lua
local function tsp_2opt(dist, route)
    local n = #route - 1
    local function tour_cost(r)
        local s = 0
        for i = 1, #r - 1 do s = s + dist[r[i]][r[i+1]] end
        return s
    end

    local improved = true
    while improved do
        improved = false
        for i = 2, n - 1 do
            for j = i + 1, n do
                local new_route = {}
                for k = 1, i - 1 do new_route[k] = route[k] end
                for k = j, i, -1 do table.insert(new_route, route[k]) end
                for k = j + 1, #route do table.insert(new_route, route[k]) end
                if tour_cost(new_route) < tour_cost(route) then
                    route = new_route
                    improved = true
                end
            end
        end
    end
    return route, tour_cost(route)
end
```

## 15.4 시뮬레이티드 어닐링

물리학 비유. 무작위 이동을 받아들이되, 시간이 갈수록 보수적이 된다.

```lua
local function sa_tsp(dist, start_route, max_iter, T0)
    local function tour_cost(r)
        local s = 0
        for i = 1, #r - 1 do s = s + dist[r[i]][r[i+1]] end
        return s
    end

    local cur = start_route
    local cur_cost = tour_cost(cur)
    local best, best_cost = cur, cur_cost
    local T = T0 or 100

    for iter = 1, max_iter do
        local i = math.random(2, #cur - 2)
        local j = math.random(i + 1, #cur - 1)

        local new_route = {}
        for k = 1, i - 1 do new_route[k] = cur[k] end
        for k = j, i, -1 do table.insert(new_route, cur[k]) end
        for k = j + 1, #cur do table.insert(new_route, cur[k]) end

        local new_cost = tour_cost(new_route)
        local delta = new_cost - cur_cost

        if delta < 0 or math.random() < math.exp(-delta / T) then
            cur, cur_cost = new_route, new_cost
            if new_cost < best_cost then
                best, best_cost = new_route, new_cost
            end
        end
        T = T * 0.999
    end
    return best, best_cost
end
```

## 15.5 유전 알고리즘 — 부분집합 합

n개 숫자에서 합이 목표에 가까운 부분집합 찾기.

```lua
local function ga_subset_sum(nums, target, pop_size, generations)
    local n = #nums
    pop_size = pop_size or 50
    generations = generations or 200

    local function fitness(individual)
        local s = 0
        for i, b in ipairs(individual) do
            if b == 1 then s = s + nums[i] end
        end
        return -math.abs(target - s)  -- 0이 최적
    end

    local function random_individual()
        local ind = {}
        for i = 1, n do ind[i] = math.random(0, 1) end
        return ind
    end

    local population = {}
    for i = 1, pop_size do population[i] = random_individual() end

    for gen = 1, generations do
        table.sort(population, function(a, b) return fitness(a) > fitness(b) end)
        local new_pop = {population[1], population[2]}  -- 엘리트
        while #new_pop < pop_size do
            -- 부모 선택
            local p1 = population[math.random(1, pop_size // 2)]
            local p2 = population[math.random(1, pop_size // 2)]
            -- 교배
            local child = {}
            for i = 1, n do
                child[i] = math.random() < 0.5 and p1[i] or p2[i]
            end
            -- 변이
            for i = 1, n do
                if math.random() < 0.05 then child[i] = 1 - child[i] end
            end
            table.insert(new_pop, child)
        end
        population = new_pop
    end

    table.sort(population, function(a, b) return fitness(a) > fitness(b) end)
    return population[1], -fitness(population[1])
end

local nums = {15, 22, 8, 33, 7, 12, 19, 25, 41, 11}
local sol, err = ga_subset_sum(nums, 70)
local s = 0
for i, b in ipairs(sol) do if b == 1 then io.write(nums[i], " "); s = s + nums[i] end end
print()
print("Sum:", s, "(target 70, error", err, ")")
```

## 15.6 몬테카를로 — 원주율 추정

```lua
local function estimate_pi(n)
    local inside = 0
    for _ = 1, n do
        local x, y = math.random(), math.random()
        if x*x + y*y <= 1 then inside = inside + 1 end
    end
    return 4 * inside / n
end

print(estimate_pi(1000))      -- ≈ 3.13
print(estimate_pi(100000))    -- ≈ 3.142
print(estimate_pi(10000000))  -- ≈ 3.1416
```

오차는 √n 에 비례. 확률적이지만 수렴은 느리다.

---

# 16. 실전 문제 풀이

## 16.1 두 수의 합 (Two Sum)

```lua
local function two_sum(nums, target)
    local seen = {}
    for i, n in ipairs(nums) do
        local need = target - n
        if seen[need] then return {seen[need], i} end
        seen[n] = i
    end
    return nil
end

local r = two_sum({2, 7, 11, 15}, 9)
print(r[1], r[2])  -- 1  2
```

## 16.2 세 수의 합 (Three Sum)

```lua
local function three_sum(nums)
    table.sort(nums)
    local n = #nums
    local result = {}
    for i = 1, n - 2 do
        if i > 1 and nums[i] == nums[i-1] then goto continue end
        local lo, hi = i + 1, n
        while lo < hi do
            local s = nums[i] + nums[lo] + nums[hi]
            if s == 0 then
                table.insert(result, {nums[i], nums[lo], nums[hi]})
                while lo < hi and nums[lo] == nums[lo+1] do lo = lo + 1 end
                while lo < hi and nums[hi] == nums[hi-1] do hi = hi - 1 end
                lo, hi = lo + 1, hi - 1
            elseif s < 0 then lo = lo + 1
            else hi = hi - 1 end
        end
        ::continue::
    end
    return result
end

for _, t in ipairs(three_sum({-1, 0, 1, 2, -1, -4})) do
    print(t[1], t[2], t[3])
end
-- -1 -1 2
-- -1 0 1
```

## 16.3 가장 긴 부분 회문 ("Manacher 없이" 단순 O(n²))

```lua
local function longest_palindrome_simple(s)
    local function expand(l, r)
        while l >= 1 and r <= #s and s:sub(l, l) == s:sub(r, r) do
            l, r = l - 1, r + 1
        end
        return l + 1, r - 1
    end

    local best_l, best_r = 1, 1
    for i = 1, #s do
        local l1, r1 = expand(i, i)
        local l2, r2 = expand(i, i + 1)
        if r1 - l1 > best_r - best_l then best_l, best_r = l1, r1 end
        if r2 - l2 > best_r - best_l then best_l, best_r = l2, r2 end
    end
    return s:sub(best_l, best_r)
end

print(longest_palindrome_simple("babad"))   -- "bab"
print(longest_palindrome_simple("cbbd"))    -- "bb"
```

## 16.4 빗물 가두기 (Trapping Rain Water)

```lua
local function trap(height)
    local n = #height
    if n == 0 then return 0 end
    local left, right = {height[1]}, {}
    for i = 2, n do
        left[i] = math.max(left[i-1], height[i])
    end
    right[n] = height[n]
    for i = n - 1, 1, -1 do
        right[i] = math.max(right[i+1], height[i])
    end
    local total = 0
    for i = 1, n do
        total = total + math.min(left[i], right[i]) - height[i]
    end
    return total
end

print(trap({0,1,0,2,1,0,1,3,2,1,2,1}))  -- 6
```

## 16.5 주식 매매 (한 번)

```lua
local function max_profit(prices)
    local min_price, profit = math.huge, 0
    for _, p in ipairs(prices) do
        if p < min_price then min_price = p end
        if p - min_price > profit then profit = p - min_price end
    end
    return profit
end

print(max_profit({7, 1, 5, 3, 6, 4}))  -- 5
print(max_profit({7, 6, 4, 3, 1}))     -- 0
```

## 16.6 슬라이딩 윈도우 — 최대 K개 다른 문자

```lua
local function longest_k_distinct(s, k)
    local count, distinct = {}, 0
    local best, l = 0, 1
    for r = 1, #s do
        local c = s:sub(r, r)
        if (count[c] or 0) == 0 then distinct = distinct + 1 end
        count[c] = (count[c] or 0) + 1
        while distinct > k do
            local c2 = s:sub(l, l)
            count[c2] = count[c2] - 1
            if count[c2] == 0 then distinct = distinct - 1 end
            l = l + 1
        end
        if r - l + 1 > best then best = r - l + 1 end
    end
    return best
end

print(longest_k_distinct("eceba", 2))   -- 3 ("ece")
print(longest_k_distinct("aa", 1))      -- 2
```

## 16.7 단어 사다리 (Word Ladder)

```lua
local function word_ladder(begin_word, end_word, word_list)
    local dict = {}
    for _, w in ipairs(word_list) do dict[w] = true end
    if not dict[end_word] then return 0 end

    local q = {{begin_word, 1}}
    local head = 1
    local visited = {[begin_word] = true}

    while head <= #q do
        local cur, level = q[head][1], q[head][2]; head = head + 1
        if cur == end_word then return level end
        for i = 1, #cur do
            for c = string.byte('a'), string.byte('z') do
                local nw = cur:sub(1, i-1) .. string.char(c) .. cur:sub(i+1)
                if dict[nw] and not visited[nw] then
                    visited[nw] = true
                    table.insert(q, {nw, level + 1})
                end
            end
        end
    end
    return 0
end

local r = word_ladder("hit", "cog", {"hot","dot","dog","lot","log","cog"})
print(r)  -- 5  (hit->hot->dot->dog->cog)
```

## 16.8 LRU 캐시 (16장 응용)

자료구조 책의 LRU를 그대로 가져와 알고리즘 실전 문제에 활용.

```lua
local LRU = {}
LRU.__index = LRU

function LRU.new(cap)
    local self = setmetatable({
        cap = cap, size = 0, map = {},
        head = {prev=nil,next=nil}, tail = {prev=nil,next=nil}
    }, LRU)
    self.head.next, self.tail.prev = self.tail, self.head
    return self
end

function LRU:_remove(n)
    n.prev.next, n.next.prev = n.next, n.prev
end
function LRU:_add_front(n)
    n.next = self.head.next; n.prev = self.head
    self.head.next.prev = n; self.head.next = n
end
function LRU:get(k)
    local n = self.map[k]
    if not n then return -1 end
    self:_remove(n); self:_add_front(n)
    return n.value
end
function LRU:put(k, v)
    local n = self.map[k]
    if n then
        n.value = v; self:_remove(n); self:_add_front(n); return
    end
    n = {key=k, value=v}
    self.map[k] = n
    self:_add_front(n)
    self.size = self.size + 1
    if self.size > self.cap then
        local victim = self.tail.prev
        self:_remove(victim); self.map[victim.key] = nil
        self.size = self.size - 1
    end
end

local c = LRU.new(2)
c:put(1, 1); c:put(2, 2)
print(c:get(1))   -- 1
c:put(3, 3)       -- 2 evict
print(c:get(2))   -- -1
c:put(4, 4)       -- 1 evict
print(c:get(1))   -- -1
print(c:get(3))   -- 3
print(c:get(4))   -- 4
```

## 16.9 최대 비트 XOR

```lua
local function trie_max_xor(nums)
    local root = {}
    local function insert(n)
        local node = root
        for i = 31, 0, -1 do
            local b = (n >> i) & 1
            if not node[b] then node[b] = {} end
            node = node[b]
        end
    end
    for _, n in ipairs(nums) do insert(n) end

    local best = 0
    for _, n in ipairs(nums) do
        local node = root
        local xor = 0
        for i = 31, 0, -1 do
            local b = (n >> i) & 1
            if node[1 - b] then
                xor = xor | (1 << i)
                node = node[1 - b]
            else
                node = node[b]
            end
        end
        if xor > best then best = xor end
    end
    return best
end

print(trie_max_xor({3, 10, 5, 25, 2, 8}))  -- 28 (5 XOR 25)
```

## 16.10 정렬된 두 배열의 중앙값 — O(log min(m,n))

```lua
local function median_two_sorted(a, b)
    if #a > #b then a, b = b, a end
    local m, n = #a, #b
    local lo, hi = 0, m
    while lo <= hi do
        local i = (lo + hi) // 2
        local j = (m + n + 1) // 2 - i
        local a_left  = i == 0 and -math.huge or a[i]
        local a_right = i == m and  math.huge or a[i+1]
        local b_left  = j == 0 and -math.huge or b[j]
        local b_right = j == n and  math.huge or b[j+1]
        if a_left <= b_right and b_left <= a_right then
            if (m + n) % 2 == 1 then
                return math.max(a_left, b_left)
            end
            return (math.max(a_left, b_left) + math.min(a_right, b_right)) / 2
        elseif a_left > b_right then
            hi = i - 1
        else
            lo = i + 1
        end
    end
end

print(median_two_sorted({1, 3}, {2}))         -- 2
print(median_two_sorted({1, 2}, {3, 4}))      -- 2.5
```

---

# 17. 부록 — 알고리즘 치트시트

## 17.1 시간 복잡도별 알고리즘 분류

| 복잡도          | 대표 알고리즘                              |
|--------------|--------------------------------------|
| O(1)         | 해시 테이블 평균 조회, 스택 push/pop          |
| O(log n)     | 이진 탐색, 힙 push/pop, BST 균형 트리        |
| O(n)         | 선형 탐색, Kadane, KMP 매칭, popcount    |
| O(n log n)   | merge/quick/heap sort, LIS-DP+이진, MST |
| O(n²)        | bubble/insertion/selection sort, LCS |
| O(n³)        | Floyd-Warshall, 행렬 곱셈                |
| O(2ⁿ)        | 부분집합 brute force, naive TSP          |
| O(n!)        | 모든 순열 탐색 (백트래킹 미적용)               |

## 17.2 입력 크기별 가능한 알고리즘

| n              | 가능한 복잡도    |
|----------------|------------|
| n ≤ 10         | O(n!)      |
| n ≤ 20         | O(2ⁿ)      |
| n ≤ 1,000      | O(n²)      |
| n ≤ 100,000    | O(n log n) |
| n ≤ 1,000,000  | O(n)       |
| n ≤ 10⁹        | O(log n) 또는 O(1) |

## 17.3 어떤 알고리즘을 쓸까

| 문제 유형            | 첫 후보              |
|------------------|-------------------|
| 정렬               | `table.sort` (Lua 내장) |
| 정렬된 데이터에서 검색     | 이진 탐색             |
| 답 자체를 이진 탐색      | "최소 X 만족하는 답" 형태   |
| 그래프 최단 (가중치 없음)  | BFS               |
| 그래프 최단 (가중치 양수)  | Dijkstra          |
| 그래프 최단 (음수 가능)   | Bellman-Ford      |
| 모든 쌍 최단          | Floyd-Warshall    |
| MST              | Kruskal / Prim    |
| 의존성 순서           | 위상 정렬             |
| 부분 문제 + 중복       | DP                |
| 그리디가 통할 듯        | 종료 시간/단위 가치 정렬   |
| 모든 가능성 탐색        | 백트래킹             |
| 부분집합 합/배낭        | DP (knapsack)     |
| 문자열 패턴 매칭        | KMP / Rabin-Karp  |
| 자동 완성, 사전        | 트라이               |
| 슬라이딩 윈도우         | 양방향 인덱스, 단조 큐    |

## 17.4 디버깅 팁

1. **작은 입력으로 손으로 풀어본다.** 코드 결과와 비교.
2. **경계 케이스:** 빈 배열, 1개 원소, 모두 같은 값, 정렬됨/역정렬됨.
3. **랜덤 테스트:** brute force로 비교 가능한 작은 입력에 대해 검증.
4. **범위 검사:** 인덱스 1부터 시작, off-by-one에 주의.
5. **`print` 디버깅:** 의심되는 변수의 모든 변화를 찍어보고 패턴을 본다.

## 17.5 Lua 알고리즘 패턴 코드

### 표준 입력 받기

```lua
for line in io.lines() do
    -- 처리
end

-- 한 줄에 공백 구분 정수
local nums = {}
for n in io.read():gmatch("%-?%d+") do
    table.insert(nums, tonumber(n))
end
```

### 빠른 출력

```lua
local out = {}
for i = 1, n do
    out[i] = tostring(result[i])
end
io.write(table.concat(out, "\n"), "\n")
```

`print`는 매번 flush해서 느리다. 대량 출력은 위처럼.

### 안전한 정수 나눗셈

```lua
-- Lua 5.3+ 권장: //
local q = a // b

-- 5.1/5.2 호환:
local q = math.floor(a / b)
```

### 큰 수 mod

```lua
local MOD = 1000000007
local function add(a, b) return (a + b) % MOD end
local function mul(a, b) return (a * b) % MOD end
```

## 17.6 마치며

알고리즘은 **외우는 것이 아니라 만나는 것**이다. 문제와 알고리즘의 만남이 잦아질수록, 새 문제를 봐도 어떤 도구를 꺼낼지 자연스레 떠오른다.

이 책의 모든 예제를 직접 돌려봤다면, 당신은 이미 다음 단계로 넘어갈 준비가 되었다.

- 알고리즘 문제 사이트(LeetCode, 백준, Codeforces)에서 실전 풀이
- 같은 문제를 다른 알고리즘으로 풀어보고 시간 비교
- 문제를 풀 때마다 **이 책의 어떤 도구를 썼는지** 기록하기

실력은 아는 알고리즘의 가짓수가 아니라, **올바른 자리에 올바른 알고리즘을 쓰는 직관**이다. 그 직관은 손이 만든다. 행운을 빈다.

— 끝 —

```lua
-- 끝까지 읽으셨다면, 이 줄을 실행해보세요.
print("당신은 이제 Lua 알고리즘의 기초를 마쳤습니다 🎉")
```
