# Lua 심화 — 어드밴스 가이드

> 메타테이블 · OOP · 코루틴 · 메타프로그래밍 · 디자인 패턴
> Lua 5.4 기준. 모든 코드는 `lua main.lua` 로 그대로 실행됩니다.

---

## 이 책이 다루지 않는 것

자료구조와 알고리즘은 별도 가이드에 충분히 정리되어 있어, 이 책에서는 같은 내용을 다시 쓰지 않습니다. 다음 문서를 함께 펼쳐 두고 읽으세요.

- [[Lua 기초]] — 기초 문법집 (변수, 조건문, for, table 입문)
- [[Lua 자료구조]] — 배열, 연결 리스트, 해시, 트리, 그래프, 트라이, 유니온 파인드, 힙
- [[Lua 알고리즘]] — 정렬/탐색/DP/그래프 알고리즘과 복잡도 분석

이 책은 **언어 자체의 깊이**에 집중합니다. 메타테이블이 어떻게 동작하는지, OOP를 어떻게 직접 만드는지, 코루틴으로 비동기를 어떻게 다루는지, 디자인 패턴을 어떻게 Lua답게 표현하는지를 다룹니다.

---

## 목차

1. 서문과 학습 환경
2. Lua 모델 다시 보기
3. 테이블 심화
4. 메타테이블 완전 정복
5. 객체 지향 프로그래밍
6. 함수와 클로저
7. 이터레이터
8. 코루틴
9. 모듈과 패키지
10. 에러 처리
11. 문자열과 패턴
12. 디버그와 성찰(introspection)
13. 가비지 컬렉션과 메모리
14. I/O · OS · 비트 연산
15. 디자인 패턴 카탈로그
16. 함수형 패턴
17. 동시성과 비동기 패턴
18. 테스트와 품질
19. LuaJIT과 최적화
20. 부록

---

# 1. 서문과 학습 환경

## 1.1 이 책의 목적

기초 문법집은 입문자에게 "무엇이 있는지"를 보여줍니다. 이 책은 같은 도구로 "무엇을 만들 수 있는지", 그리고 "왜 그렇게 동작하는지"를 다룹니다.

세 가지 축으로 구성됩니다.

1. **언어의 핵심 메커니즘** — 메타테이블, 환경, 클로저, 코루틴.
2. **재사용 가능한 패턴** — 직접 만든 클래스, 옵저버, 액터, 메모이저.
3. **생산성** — 디버깅, 테스트, 모듈 분할, 핫 리로드.

읽고 끝나는 책이 아닙니다. 모든 예제를 그대로 입력하고 한 줄씩 변형해 보세요. Lua는 작은 언어라 변형의 비용이 매우 낮습니다.

## 1.2 누구를 위한 책인가

- 기초 문법집을 한 번 통과한 사람
- 게임 스크립트(LÖVE2D, Roblox, Defold)에서 더 큰 모듈을 짜고 싶은 사람
- Redis, Nginx, WoW Addon, Neovim 등에 임베드된 Lua를 다루는 사람
- 임베디드/도구용 미니 인터프리터를 만드는 사람
- C에서 Lua를 호출하거나, 반대로 Lua에서 C 라이브러리를 부르는 사람

## 1.3 개발 환경

이 책의 모든 코드는 **Lua 5.4** 기준입니다. 5.1과의 차이는 본문에 그때마다 표시합니다.

```bash
# Ubuntu / Debian
sudo apt install lua5.4

# macOS
brew install lua

# Termux (Android)
pkg install lua54

lua -v
# Lua 5.4.x  Copyright (C) 1994-2023 Lua.org, PUC-Rio
```

### LuaJIT

게임이나 고성능 임베딩에서는 LuaJIT이 더 흔합니다. LuaJIT은 Lua 5.1 문법 + 일부 5.2 확장입니다. 호환성 차이가 나는 부분은 19장에서 정리합니다.

```bash
sudo apt install luajit
luajit -v
```

### 권장 도구

- **stylua** — 포매터
- **luacheck** — 린터
- **busted** — 테스트 러너 (18장에서 자체 미니 버전을 만듭니다)
- **luarocks** — 패키지 매니저

## 1.4 코드 실행 규칙

본문 코드는 두 가지 형태입니다.

```lua
-- 단독 실행 가능한 스크립트
print("hello")
```

```lua
-- 모듈로 분리되는 코드 (파일명을 주석으로 표시)
-- file: utils.lua
local M = {}
function M.greet(name) return "hi, " .. name end
return M
```

모듈 예제는 같은 디렉터리에서 `lua main.lua` 로 묶어 실행합니다.

## 1.5 책에서 자주 쓰는 헬퍼

이 책 전체에서 다음 두 함수를 자주 씁니다. 한 번 익혀 두세요.

```lua
-- 깊은 출력 (테이블을 보기 좋게)
local function dump(v, indent)
    indent = indent or ""
    if type(v) ~= "table" then
        io.write(tostring(v))
        return
    end
    io.write("{\n")
    for k, val in pairs(v) do
        io.write(indent .. "  ")
        io.write(tostring(k) .. " = ")
        dump(val, indent .. "  ")
        io.write(",\n")
    end
    io.write(indent .. "}")
end

local function p(...)
    local n = select("#", ...)
    for i = 1, n do
        dump((select(i, ...)))
        io.write(i < n and "\t" or "\n")
    end
end

p({a=1, b={c=2}})
-- {
--   a = 1,
--   b = {
--     c = 2,
--   },
-- }
```

이 헬퍼는 부록 20.4에도 모아 두었습니다.

---

# 2. Lua 모델 다시 보기

문법은 이미 알고 있다고 가정합니다. 이 장은 **값(value)이 어떻게 동작하는지**, 즉 Lua의 의미 모델을 정확히 잡아 두는 장입니다. 이걸 빨리 깔끔히 정리하지 않으면 메타테이블, OOP, 코루틴이 전부 모래 위 집이 됩니다.

## 2.1 8가지 타입

```lua
print(type(nil))       --> nil
print(type(true))      --> boolean
print(type(3.14))      --> number
print(type("x"))       --> string
print(type(print))     --> function
print(type({}))        --> table
print(type(io.stdout)) --> userdata
print(type(coroutine.create(function() end))) --> thread
```

이 8개가 전부입니다. **클래스는 타입이 아니라 메타테이블의 결과**입니다(5장).

### number의 두 얼굴 — integer / float

Lua 5.3부터 number는 내부적으로 **정수 서브타입**과 **부동소수 서브타입**으로 나뉩니다.

```lua
print(math.type(1))     --> integer
print(math.type(1.0))   --> float
print(math.type(1/2))   --> float   -- 나눗셈은 float
print(math.type(7 // 2))--> integer -- 정수 나눗셈
```

같은 값이지만 표현이 다르면 동작이 살짝 다릅니다.

```lua
print(1 == 1.0)         --> true   -- == 는 값 비교
print(string.format("%d", 1.0))  -- 5.4: 정확히 정수일 때만 OK
```

게임 좌표처럼 정수만 다루고 싶다면 `//` 와 `math.tointeger` 를 의식해서 쓰세요.

```lua
local function ix(n) return math.tointeger(n) or error("not int") end
```

## 2.2 값과 참조

Lua 값은 두 부류로 갈립니다.

| 분류 | 타입 |
|---|---|
| 값(by value) | nil, boolean, number, string |
| 참조(by reference) | table, function, userdata, thread |

```lua
local a = "hi"
local b = a
b = b .. "!"
print(a, b)   --> hi   hi!   -- 문자열은 불변

local t1 = {1, 2, 3}
local t2 = t1
t2[1] = 99
print(t1[1])  --> 99            -- 같은 테이블을 가리킴
```

### 깊은 복사

테이블을 진짜 복제하려면 직접 복사해야 합니다.

```lua
local function deepcopy(o, seen)
    if type(o) ~= "table" then return o end
    seen = seen or {}
    if seen[o] then return seen[o] end
    local r = {}
    seen[o] = r
    for k, v in pairs(o) do
        r[deepcopy(k, seen)] = deepcopy(v, seen)
    end
    return setmetatable(r, getmetatable(o))
}
```

순환 참조를 처리하려면 위처럼 `seen` 테이블이 필요합니다. 자료구조 가이드의 깊은 복사 절도 함께 참조하세요. → [[Lua 자료구조#3.5 깊은 복사 / 얕은 복사]]

## 2.3 truthy / falsy

Lua에서 거짓은 `false` 와 `nil` 단 둘뿐입니다. **0도, 빈 문자열도 참**입니다.

```lua
if 0 then print("0 is truthy") end       -- 출력됨
if "" then print("'' is truthy") end     -- 출력됨
if {} then print("{} is truthy") end     -- 출력됨

if nil then print("never") end
if false then print("never") end
```

C/Python 출신이 가장 자주 잘못 짜는 부분입니다.

### and / or 의 단축평가 패턴

`and` 와 `or` 는 boolean이 아니라 **마지막으로 평가한 값**을 돌려줍니다. 이 성질로 삼항 연산자를 흉내 냅니다.

```lua
local sign = (x >= 0) and "+" or "-"
local name = user and user.name or "anonymous"
```

함정: 가운데 값이 false/nil 이면 깨집니다.

```lua
local v = cond and false or "fallback"  -- cond=true 여도 "fallback"
```

이런 경우는 그냥 if 로 쓰세요.

## 2.4 다중 할당과 다중 반환

Lua는 다중 할당과 다중 반환이 일급 시민입니다.

```lua
local a, b, c = 1, 2, 3
local x, y = y, x   -- 스왑 (임시 변수 없이)

local function minmax(t)
    local lo, hi = math.huge, -math.huge
    for _, v in ipairs(t) do
        if v < lo then lo = v end
        if v > hi then hi = v end
    end
    return lo, hi
end

local lo, hi = minmax({3, 1, 4, 1, 5, 9, 2, 6})
print(lo, hi)  --> 1   9
```

### 다중 반환의 절단 규칙

식의 끝에 있을 때만 모든 반환값이 펼쳐집니다.

```lua
local function two() return 1, 2 end

print(two())            --> 1   2     -- 끝이라 모두 사용
print(two(), 9)         --> 1   9     -- 끝이 아니라서 첫 값만
local a, b, c = two(), 9
print(a, b, c)          --> 1   9   nil

local t = {two(), 9}
print(#t)               --> 2

local t = {9, two()}
print(#t)               --> 3   -- 끝이라 펼쳐짐
```

이 규칙은 메타프로그래밍에서 함정으로 자주 등장합니다.

### 가변 인자와 select

```lua
local function f(...)
    local n = select("#", ...)   -- nil 포함 인자 개수
    for i = 1, n do
        print(i, (select(i, ...)))
    end
end

f("a", nil, "c")
-- 1   a
-- 2   nil
-- 3   c
```

`{...}` 으로 받으면 중간에 nil이 있을 때 길이가 어긋날 수 있습니다. nil 가능성이 있으면 `select("#", ...)` 가 정답입니다.

`table.pack` / `table.unpack` 도 함께:

```lua
local function f(...)
    local args = table.pack(...)  -- {n = N, [1]=..., [2]=...}
    return args.n, table.unpack(args, 1, args.n)
end
```

## 2.5 식과 문 — 모두 식이 아님

Lua에서 모든 게 식인 건 아닙니다.

```lua
local x = if a then 1 else 2 end   -- 에러: if 는 문(statement)
```

대안:

```lua
local x = a and 1 or 2

-- 또는 즉시 호출 함수
local x = (function()
    if a then return 1 else return 2 end
end)()
```

## 2.6 변수 스코프 한 줄 정리

- `local` 없이 쓰면 **전역**.
- `local` 은 그것이 선언된 **블록**(if, for, do…end, function 본문) 안에서만 유효.
- 함수는 자신을 둘러싼 모든 블록의 local을 **상향 참조(upvalue)** 한다 → 7장과 8장의 핵심.

```lua
local x = 1
do
    local x = 2
    print(x)  --> 2
end
print(x)      --> 1
```

## 2.7 do ... end 의 두 쓰임

블록을 묶어 스코프를 만들거나, 의도적으로 변수의 수명을 제한할 때 씁니다.

```lua
do
    local big = load_big_resource()
    process(big)
end  -- big 의 참조가 여기서 끊김 → GC 가능
```

13장에서 가비지 컬렉션 시점을 제어할 때 이 패턴을 다시 봅니다.

## 2.8 동등성 — `==` 와 rawequal

```lua
print({} == {})              --> false  (다른 테이블)
local t = {}
print(t == t)                --> true
print(rawequal(t, t))        --> true
```

`==` 는 메타테이블의 `__eq` 를 부를 수 있고, `rawequal` 은 절대 부르지 않습니다.

## 2.9 길이 연산자 `#` 의 정의

```lua
print(#"hello")          --> 5
print(#{10, 20, 30})     --> 3
```

테이블에서는 **시퀀스**(1..n 까지 nil 없는 정수 키)일 때만 의미 있는 값을 줍니다. 구멍이 있으면 결과가 정의되지 않습니다.

```lua
local t = {1, nil, 3}
print(#t)   -- 1 또는 3, 구현 정의
```

테이블의 길이는 직접 추적하는 편이 안전합니다(3장).

## 2.10 string 의 메서드 호출 가능성

문자열은 값 타입이지만, `string` 라이브러리가 문자열의 메타테이블의 `__index` 로 등록돼 있어 콜론 호출이 가능합니다.

```lua
local s = "hello"
print(s:upper())          --> HELLO
print(s:sub(1, 3))        --> hel
print(("world"):len())    --> 5
```

이건 4장(메타테이블)의 작은 예고편입니다.

---

# 3. 테이블 심화

테이블은 Lua의 유일한 복합 자료구조입니다. 배열이고, 해시 맵이고, 객체이고, 모듈이고, 환경이고, 클래스입니다. 이 장은 **순수 테이블의 동작과 라이브러리**에 집중하고, 메타테이블은 4장에서 다룹니다.

## 3.1 두 개의 부분

내부적으로 모든 테이블은 두 개의 저장소로 구성됩니다.

- **배열 부분(array part)** — 1, 2, 3, ... 정수 키
- **해시 부분(hash part)** — 그 외 모든 키 (문자열, 음수, 실수, 테이블, 함수…)

```lua
local t = {}
t[1] = "a"        -- 배열부
t[2] = "b"        -- 배열부
t.name = "x"      -- 해시부
t[1.5] = true     -- 해시부
t[-1] = "neg"     -- 해시부
```

이걸 알면 두 가지가 명확해집니다.

1. 배열 부분에 키 0 을 쓰면 손해. 1부터 시작해야 라이브러리가 잘 돕습니다.
2. 큰 정수 인덱스를 띄엄띄엄 쓰면 배열부가 비대해지거나 해시부로 떨어집니다.

## 3.2 시퀀스(sequence)의 정의

Lua 매뉴얼은 "시퀀스"를 정확히 정의합니다.

> 키가 1, 2, ..., n 인 양의 정수이고 그 외의 양의 정수 키가 없는 테이블.

이 조건을 만족할 때만 `#t`, `ipairs`, `table.insert`, `table.sort`, `table.concat` 등이 안전합니다.

```lua
local good = {10, 20, 30}
local bad  = {10, nil, 30}      -- 시퀀스 아님

for i, v in ipairs(good) do print(i, v) end
-- 1 10
-- 2 20
-- 3 30

for i, v in ipairs(bad) do print(i, v) end
-- 1 10        -- nil 만나면 거기서 중단
```

### 안전한 길이 추적

구멍이 생길 가능성이 있으면 길이를 직접 들고 다니세요.

```lua
local List = {}
List.__index = List

function List.new() return setmetatable({n = 0}, List) end
function List:push(v) self.n = self.n + 1; self[self.n] = v end
function List:pop()
    local v = self[self.n]
    self[self.n] = nil
    self.n = self.n - 1
    return v
end
function List:len() return self.n end
```

자료구조 가이드의 동적 배열도 같은 패턴입니다 → [[Lua 자료구조#4.2 동적 배열 직접 만들기]].

## 3.3 table 라이브러리

```lua
local t = {30, 10, 20}

table.insert(t, 40)        -- 끝에 추가 → {30,10,20,40}
table.insert(t, 1, 0)      -- 1번 위치에 삽입 → {0,30,10,20,40}
table.remove(t)            -- 끝에서 제거
table.remove(t, 1)         -- 1번 제거 → {30,10,20}

table.sort(t)              -- 오름차순 정렬 → {10,20,30}
table.sort(t, function(a,b) return a > b end)  -- 내림차순

print(table.concat(t, ", ")) -- "30, 20, 10"

local copy = table.move(t, 1, #t, 1, {})
```

`table.move(a1, f, e, t, a2)` — `a1[f..e]` 을 `a2[t..]` 로 복사. **얕은 복사용으로 가장 빠른 도구**입니다.

```lua
-- 배열 복제
local function clone_array(t) return table.move(t, 1, #t, 1, {}) end

-- 끼워 넣기 (a 의 i 위치에 b 삽입)
local function splice(a, i, b)
    table.move(a, i, #a, i + #b)        -- 뒤로 밀기
    table.move(b, 1, #b, i, a)          -- b 복사
    return a
end
```

## 3.4 정렬과 안정성

`table.sort` 는 **불안정 정렬**입니다. 안정성이 필요하면 보조 키를 쓰세요.

```lua
local items = {{n=1,k=2},{n=2,k=1},{n=3,k=2},{n=4,k=1}}
for i, v in ipairs(items) do v._i = i end
table.sort(items, function(a, b)
    if a.k ~= b.k then return a.k < b.k end
    return a._i < b._i      -- 동률은 원래 순서
end)
```

알고리즘 가이드에서 정렬 알고리즘 자체를 직접 구현하는 절을 참조하세요 → [[Lua 알고리즘#4. 정렬 알고리즘]].

## 3.5 pairs vs ipairs vs next

```lua
local t = {10, 20, "x", name="A"}

for i, v in ipairs(t) do print(i, v) end
-- 1 10
-- 2 20
-- 3 x
-- (name 은 나오지 않음)

for k, v in pairs(t) do print(k, v) end
-- 1 10
-- 2 20
-- 3 x
-- name A
```

- `ipairs` — 1부터 시작, **첫 nil에서 멈춤**, 정수 키만.
- `pairs` — 모든 키. 순서는 **정의되지 않음**(특히 해시부).
- `next(t, k)` — 직접 호출 가능한 저수준 이터레이터.

```lua
local k, v = nil
while true do
    k, v = next(t, k)
    if k == nil then break end
    print(k, v)
end
```

순서 있는 순회가 필요하면 키를 모아 정렬해서 돌리세요.

```lua
local function sortedpairs(t, cmp)
    local keys = {}
    for k in pairs(t) do keys[#keys+1] = k end
    table.sort(keys, cmp)
    local i = 0
    return function()
        i = i + 1
        local k = keys[i]
        if k == nil then return nil end
        return k, t[k]
    end
end

for k, v in sortedpairs({c=3, a=1, b=2}) do print(k, v) end
-- a 1
-- b 2
-- c 3
```

7장에서 이런 이터레이터를 직접 만드는 법을 본격적으로 다룹니다.

## 3.6 keys / values / entries

대부분의 모던 언어가 갖춘 함수가 Lua 표준엔 없습니다. 직접 만드세요.

```lua
local M = {}

function M.keys(t)
    local r, n = {}, 0
    for k in pairs(t) do n = n + 1; r[n] = k end
    return r
end

function M.values(t)
    local r, n = {}, 0
    for _, v in pairs(t) do n = n + 1; r[n] = v end
    return r
end

function M.entries(t)
    local r, n = {}, 0
    for k, v in pairs(t) do n = n + 1; r[n] = {k, v} end
    return r
end

function M.size(t)
    local n = 0
    for _ in pairs(t) do n = n + 1 end
    return n
end

return M
```

`#t` 는 시퀀스 전용이므로 해시부 크기는 `M.size` 처럼 직접 세야 합니다.

## 3.7 병합과 분할

```lua
-- 얕은 병합 (b가 a를 덮어씀)
local function merge(a, b)
    local r = {}
    for k, v in pairs(a) do r[k] = v end
    for k, v in pairs(b) do r[k] = v end
    return r
end

-- in-place 확장
local function extend(a, b)
    for k, v in pairs(b) do a[k] = v end
    return a
end

-- 깊은 병합
local function deepmerge(a, b)
    local r = {}
    for k, v in pairs(a) do r[k] = v end
    for k, v in pairs(b) do
        if type(v) == "table" and type(r[k]) == "table" then
            r[k] = deepmerge(r[k], v)
        else
            r[k] = v
        end
    end
    return r
end
```

## 3.8 변경 불가 테이블 (read-only)

표준 Lua에는 없습니다. 메타테이블 한 줄로 만듭니다.

```lua
local function readonly(t)
    return setmetatable({}, {
        __index = t,
        __newindex = function(_, k)
            error("read-only: cannot set " .. tostring(k), 2)
        end,
        __metatable = false,   -- getmetatable 차단
    })
end

local cfg = readonly({port=8080, host="localhost"})
print(cfg.port)        --> 8080
cfg.port = 9000        -- 에러: read-only: cannot set port
```

`__metatable = false` 로 메타테이블 자체도 숨겨서 우회를 막습니다. 4장에서 다시 봅니다.

## 3.9 키로서의 테이블/함수

키는 nil 이 아닌 어떤 값이든 가능합니다. 이걸 활용하면 **정체성 키**(identity key)를 만들 수 있습니다.

```lua
local SECRET = {}            -- 빈 테이블 = 유일한 키
local cache = setmetatable({}, {__mode = "k"})

cache[SECRET] = "only I can read this"
print(cache[SECRET])
```

토큰 기반 권한, 비공개 슬롯, 약한 키 캐시 등에 자주 씁니다. 13장의 약한 테이블 절에서 다시 다룹니다.

## 3.10 테이블의 함정 모음

| 함정 | 증상 | 해결 |
|---|---|---|
| `#t` 가 nil 만나면 미정의 | 길이 -- 1 | 별도 카운트 |
| `pairs` 순서 의존 | 환경마다 다름 | 정렬해서 순회 |
| `t == t2` 는 동일성 | 내용 같아도 false | `deepequal` 직접 |
| 해시부에 큰 정수 키 | 메모리 비대 | 키를 다른 형태로 |
| `local t={}` 두 번 | 같은 줄 비교 false | 한 번만 만들기 |

깊은 등치(deepequal)도 자주 필요합니다.

```lua
local function deepequal(a, b)
    if a == b then return true end
    if type(a) ~= "table" or type(b) ~= "table" then return false end
    for k, v in pairs(a) do
        if not deepequal(v, b[k]) then return false end
    end
    for k in pairs(b) do
        if a[k] == nil then return false end
    end
    return true
end
```

순환 참조까지 안전하게 만들려면 `seen` 인자를 추가하세요(2.2절 deepcopy 참고).

---

# 4. 메타테이블 완전 정복

메타테이블은 Lua가 작은 언어로 큰 일을 하는 비결입니다. **모든 OOP, 연산자 오버로딩, 가상 인덱스, 약한 참조, 프록시, 샌드박스가 메타테이블 위에서 만들어집니다.**

## 4.1 한 문장 정의

> 메타테이블은 어떤 테이블에 "기본 동작에서 벗어나는 일이 일어났을 때 호출되는 훅 함수들"을 모아 둔 또 다른 테이블이다.

```lua
local t = {}
local mt = {}
setmetatable(t, mt)
print(getmetatable(t) == mt)   --> true
```

훅의 이름은 모두 **두 개의 밑줄**로 시작합니다. 이를 메타메서드라고 부릅니다.

## 4.2 메타메서드 일람

| 메타메서드 | 트리거 |
|---|---|
| `__index` | `t[k]` 의 키가 없을 때 |
| `__newindex` | `t[k] = v` 의 키가 없을 때 |
| `__call` | `t(...)` 함수 호출 |
| `__tostring` | `tostring(t)`, `print(t)` |
| `__len` | `#t` |
| `__eq` | `t == u` (둘 다 같은 메타테이블 또는 같은 `__eq`) |
| `__lt` | `t < u` |
| `__le` | `t <= u` |
| `__add`, `__sub`, `__mul`, `__div`, `__mod`, `__pow`, `__unm` | 산술 |
| `__idiv` | `//` |
| `__band`, `__bor`, `__bxor`, `__bnot`, `__shl`, `__shr` | 비트 (5.3+) |
| `__concat` | `..` |
| `__metatable` | `getmetatable` 결과를 가짜로, `setmetatable`을 차단 |
| `__mode` | 약한 테이블 키/값 (13장) |
| `__gc` | 가비지 컬렉션 시 (13장) |
| `__close` | `<close>` 변수 종료 (5.4+) |
| `__pairs` | (5.2 한정) |
| `__name` | 사용자 데이터 식별자(에러 메시지) |

## 4.3 가장 중요한 셋: __index, __newindex, __call

### __index — 폴백 조회

```lua
local defaults = {host = "localhost", port = 8080, timeout = 30}

local cfg = setmetatable({port = 9000}, {__index = defaults})

print(cfg.host)     --> localhost  (fallback)
print(cfg.port)     --> 9000       (own)
print(cfg.timeout)  --> 30         (fallback)
```

`__index` 는 **테이블이거나 함수**일 수 있습니다.

```lua
-- 함수 형태: 동적으로 계산
local lazy = setmetatable({}, {
    __index = function(t, k)
        local v = string.upper(k)
        rawset(t, k, v)         -- 캐시
        return v
    end,
})
print(lazy.hello)   --> HELLO   (계산되어 저장됨)
print(lazy.hello)   --> HELLO   (이번엔 캐시에서)
```

### __newindex — 쓰기 가로채기

```lua
local logged = setmetatable({}, {
    __newindex = function(t, k, v)
        print(("set %s = %s"):format(k, tostring(v)))
        rawset(t, k, v)
    end,
})

logged.x = 10   -- "set x = 10"
logged.y = 20   -- "set y = 20"
print(logged.x) -- 10
```

핵심 함정: `__newindex` 는 **키가 아직 없을 때만** 호출됩니다. 한 번 `rawset` 으로 저장한 뒤에는 다시 안 불립니다.

쓰기 자체를 강제로 가로채려면 데이터를 **다른 테이블에 보관**합니다.

```lua
local function observed(initial, on_set)
    local data = initial or {}
    return setmetatable({}, {
        __index = data,
        __newindex = function(_, k, v)
            on_set(k, data[k], v)
            data[k] = v
        end,
    })
end

local p = observed({hp=100}, function(k, old, new)
    print(("%s: %s -> %s"):format(k, tostring(old), tostring(new)))
end)
p.hp = 80     -- hp: 100 -> 80
p.hp = 60     -- hp: 80 -> 60
print(p.hp)   -- 60
```

15장의 옵저버 패턴 절에서 이 구조를 정식 패턴으로 다시 봅니다.

### __call — 테이블을 함수처럼

```lua
local Counter = setmetatable({n = 0}, {
    __call = function(self)
        self.n = self.n + 1
        return self.n
    end,
})

print(Counter())  --> 1
print(Counter())  --> 2
print(Counter())  --> 3
```

OOP에서 클래스 자체를 호출 가능하게 만드는 데도 씁니다(5장의 `Class(args)` 패턴).

## 4.4 산술과 비교 메타메서드

벡터를 만들어 봅시다. 메타테이블 학습용 단골 예제입니다.

```lua
local Vec = {}
Vec.__index = Vec

function Vec.new(x, y) return setmetatable({x=x, y=y}, Vec) end

function Vec.__add(a, b) return Vec.new(a.x + b.x, a.y + b.y) end
function Vec.__sub(a, b) return Vec.new(a.x - b.x, a.y - b.y) end
function Vec.__mul(a, k)
    if type(k) == "number" then
        return Vec.new(a.x * k, a.y * k)
    end
    -- k 가 Vec 이면 내적
    return a.x * k.x + a.y * k.y
end
function Vec.__unm(a) return Vec.new(-a.x, -a.y) end
function Vec.__eq(a, b) return a.x == b.x and a.y == b.y end
function Vec.__lt(a, b) return a:len2() < b:len2() end
function Vec.__tostring(v) return ("(%g, %g)"):format(v.x, v.y) end
function Vec:len2() return self.x*self.x + self.y*self.y end
function Vec:len()  return math.sqrt(self:len2()) end

local a, b = Vec.new(1, 2), Vec.new(3, 4)
print(a + b)        --> (4, 6)
print(b - a)        --> (2, 2)
print(a * 3)        --> (3, 6)
print(a * b)        --> 11      -- 내적
print(-a)           --> (-1, -2)
print(a == Vec.new(1,2))  --> true
print(a < b)              --> true   (길이 비교)
```

`__lt` 만 정의하면 `>` 도 자동으로 동작합니다(`a > b` 는 `b < a` 로 변환).

### __eq 의 함정

`__eq` 는 두 객체의 메타테이블이 **둘 다 정의되어 있고, 같거나 같은 `__eq`** 일 때만 호출됩니다. 서로 다른 클래스 간 == 는 항상 false.

```lua
local A = setmetatable({}, {__eq = function() return true end})
local B = setmetatable({}, {__eq = function() return true end})
print(A == B)       -- 5.4: A 의 __eq 호출 → true
                    -- 5.1: false (같은 메타테이블 아님)
```

버전 차이가 있어 객체 평등은 명시적 메서드(`a:equals(b)`)를 권장합니다.

## 4.5 __tostring, __concat, __len

```lua
local M = setmetatable({}, {
    __tostring = function() return "<MyObj>" end,
    __concat   = function(a, b) return tostring(a) .. tostring(b) end,
    __len      = function() return 42 end,
})

print(M)            --> <MyObj>
print("=" .. M)     --> =<MyObj>
print(#M)           --> 42
```

`io.write` 는 `__tostring` 을 호출하지 **않습니다**. `print` 와 `tostring` 만 호출합니다. 헷갈리면 직접 `tostring(x)` 로 감싸세요.

## 4.6 __index 체인 — 다중 레벨

```lua
local Animal = {kind="animal"}
function Animal:speak() return "some sound" end

local Dog = setmetatable({}, {__index = Animal})
function Dog:speak() return "woof" end

local Puppy = setmetatable({}, {__index = Dog})

local p = setmetatable({name="Buddy"}, {__index = Puppy})
print(p.kind)       --> animal   (3단계 폴백)
print(p:speak())    --> woof     (Dog 에서 발견)
print(p.name)       --> Buddy    (자기 자신)
```

이 폴백 체인이 그대로 5장의 상속이 됩니다.

## 4.7 rawget / rawset / rawequal / rawlen

메타메서드를 **건너뛰는** 원시 접근자입니다. 메타메서드 안에서 무한 재귀를 피할 때 필수.

```lua
local mt = {}
mt.__index = function(t, k)
    if k:sub(1,1) == "_" then return nil end
    return rawget(t, "real_" .. k)    -- 메타메서드 우회
end

mt.__newindex = function(t, k, v)
    rawset(t, "real_" .. k, v)
end

local p = setmetatable({}, mt)
p.name = "Lua"
print(p.name)       --> Lua    (real_name 에 저장)
```

## 4.8 __metatable — 메타테이블 잠그기

```lua
local protected = setmetatable({}, {
    __index = {greet=function() return "hi" end},
    __metatable = "locked",   -- 어떤 truthy 값이든 OK
})

print(getmetatable(protected))   --> locked    (가짜를 보여줌)
setmetatable(protected, {})      -- 에러: cannot change a protected metatable
```

read-only 객체, 라이브러리 보호용으로 자주 씁니다.

## 4.9 __close (Lua 5.4) — to-be-closed 변수

Python 의 with, Go 의 defer 와 비슷한 자원 관리 기능입니다.

```lua
local function file_open(path)
    local f = assert(io.open(path, "r"))
    return setmetatable({f=f}, {
        __close = function(self)
            print("closing " .. path)
            self.f:close()
        end,
        __index = {
            read = function(self, ...) return self.f:read(...) end,
        },
    })
end

do
    local f <close> = file_open("/etc/hostname")
    print(f:read("l"))
end  -- 블록을 벗어나는 순간 __close 자동 호출
```

`<close>` 어노테이션은 Lua 5.4 신기능입니다. LuaJIT에서는 동작하지 않습니다.

## 4.10 메타테이블이 부르는 메타메서드 — 우선순위

산술 `a + b` 에서 두 피연산자의 메타테이블이 둘 다 `__add` 를 갖고 있으면 **a 쪽 먼저** 시도합니다.

```lua
local A = setmetatable({}, {__add = function() return "A" end})
local B = setmetatable({}, {__add = function() return "B" end})
print(A + B)   --> A
```

이 규칙으로 좌측 우선의 연산자를 의식해 두세요.

## 4.11 메타테이블 디버깅 트릭

```lua
-- 어떤 객체의 메타테이블이 갖고 있는 메타메서드 목록
local function metainfo(t)
    local mt = getmetatable(t)
    if not mt then return "no metatable" end
    local r = {}
    for k in pairs(mt) do
        if k:sub(1, 2) == "__" then r[#r+1] = k end
    end
    table.sort(r)
    return table.concat(r, ", ")
end

print(metainfo(Vec.new(1,2)))
-- __add, __eq, __index, __lt, __mul, __sub, __tostring, __unm
```

## 4.12 메타테이블 설계 가이드

1. **공유** — 같은 클래스의 인스턴스는 메타테이블을 **공유**해야 합니다. 인스턴스마다 새로 만들면 메모리와 캐시가 무너집니다.
2. **`__index` 우선** — 메서드 디스패치는 `__index` 한 군데로 통일.
3. **`rawset/rawget` 으로 무한 재귀 방지** — 특히 `__newindex` 안에서.
4. **`__metatable` 로 보호** — 라이브러리 객체의 메타테이블을 외부에서 바꾸지 못하게.
5. **간결하게** — 메타메서드를 너무 많이 정의하면 디버깅 추적이 어려워집니다.

---

# 5. 객체 지향 프로그래밍

Lua에는 `class` 키워드가 없습니다. 대신 메타테이블로 OOP를 직접 만듭니다. 이 장은 표준이 된 패턴들을 빌드업 형식으로 보여줍니다.

## 5.1 가장 단순한 객체

```lua
local cat = {name = "Tom"}

function cat:meow()
    print(self.name .. ": meow")
end

cat:meow()    -- Tom: meow
```

`cat:meow()` 는 `cat.meow(cat)` 의 설탕(syntactic sugar)입니다. **콜론은 첫 인자로 self를 자동 전달**.

선언도 마찬가지입니다.

```lua
function obj:method(x) ... end
-- 같은 의미
function obj.method(self, x) ... end
```

## 5.2 클래스 패턴 — 1단계

```lua
local Dog = {}
Dog.__index = Dog          -- 인스턴스가 Dog 의 메서드를 찾도록

function Dog.new(name)
    local self = setmetatable({}, Dog)
    self.name = name
    return self
end

function Dog:bark()
    print(self.name .. ": woof")
end

local d = Dog.new("Rex")
d:bark()  -- Rex: woof
```

핵심은 두 줄입니다.

1. `Dog.__index = Dog` — "메서드 찾을 때 Dog 자기 자신을 보라"
2. `setmetatable(self, Dog)` — "이 인스턴스의 메타테이블이 Dog"

이렇게 하면 인스턴스에 `bark` 가 없을 때 메타테이블 → `__index` → `Dog` 에서 발견됩니다.

## 5.3 클래스 패턴 — 2단계 (`Class()` 로 생성)

생성자 이름을 매번 정하기 귀찮으니 클래스를 함수처럼 호출하게 만듭니다.

```lua
local function class()
    local cls = {}
    cls.__index = cls
    setmetatable(cls, {
        __call = function(_, ...)
            local self = setmetatable({}, cls)
            if cls.init then cls.init(self, ...) end
            return self
        end,
    })
    return cls
end

local Dog = class()
function Dog:init(name) self.name = name end
function Dog:bark() print(self.name .. ": woof") end

local d = Dog("Rex")
d:bark()
```

`Dog("Rex")` 가 `Dog.new("Rex")` 처럼 보이게 됩니다. 이게 우리가 이 책 전체에서 쓸 베이스입니다.

## 5.4 단일 상속

```lua
local function class(base)
    local cls = setmetatable({}, {
        __index = base,
        __call = function(c, ...)
            local self = setmetatable({}, c)
            if c.init then c.init(self, ...) end
            return self
        end,
    })
    cls.__index = cls
    cls.super = base
    return cls
end

local Animal = class()
function Animal:init(name) self.name = name end
function Animal:speak() return "..." end
function Animal:describe() return self.name .. " says " .. self:speak() end

local Dog = class(Animal)
function Dog:speak() return "woof" end

local Cat = class(Animal)
function Cat:init(name, color)
    Animal.init(self, name)         -- super 호출
    self.color = color
end
function Cat:speak() return "meow" end

local d = Dog("Rex")
local c = Cat("Tom", "black")

print(d:describe())   -- Rex says woof
print(c:describe())   -- Tom says meow
print(c.color)        -- black
```

핵심:

- `class(base)` 에서 `__index = base` 로 설정하면 `Dog.foo` 가 없을 때 `Animal.foo` 에서 찾습니다.
- 인스턴스 → `Dog` (`__index=Dog`) → `Animal` 의 2단 체인.
- 자식이 부모 init을 호출하려면 `Animal.init(self, ...)` 처럼 직접 부릅니다.

## 5.5 super 호출 헬퍼

매번 부모 클래스를 이름으로 부르긴 번거롭습니다. 헬퍼를 둡니다.

```lua
function Cat:init(name, color)
    self.super.init(self, name)
    self.color = color
end
```

`self.super` 는 `class()` 가 만들어 둔 부모 참조입니다. 다이아몬드(다중 상속) 상황엔 이걸로 부족하므로, 다중 상속에서는 다른 패턴을 씁니다(다음 절).

## 5.6 다중 상속과 믹스인

Lua는 단일 `__index` 만 가지므로 다중 상속을 흉내내려면 직접 lookup 함수를 씁니다.

```lua
local function multiclass(...)
    local parents = {...}
    local cls = {}
    cls.__index = function(t, k)
        for _, p in ipairs(parents) do
            local v = p[k]
            if v ~= nil then return v end
        end
        return nil
    end
    setmetatable(cls, {
        __call = function(c, ...)
            local self = setmetatable({}, cls)
            if cls.init then cls.init(self, ...) end
            return self
        end,
    })
    return cls
end

local Walker = {}
function Walker:walk() return self.name .. " walks" end

local Swimmer = {}
function Swimmer:swim() return self.name .. " swims" end

local Duck = multiclass(Walker, Swimmer)
function Duck:init(name) self.name = name end

local d = Duck("Donald")
print(d:walk())   -- Donald walks
print(d:swim())   -- Donald swims
```

다중 상속은 충돌(같은 메서드 이름)이 위험합니다. 가능하면 **믹스인**(mixin)으로 분리해서 명시적으로 합치는 패턴을 권장합니다.

```lua
local function mixin(target, ...)
    for _, src in ipairs({...}) do
        for k, v in pairs(src) do
            target[k] = v
        end
    end
    return target
end

local Logger = {}
function Logger:log(msg) print("[" .. self.name .. "] " .. msg) end

local Cache = {}
function Cache:cache_get(k) return (self._cache or {})[k] end
function Cache:cache_set(k, v)
    self._cache = self._cache or {}
    self._cache[k] = v
end

local Service = class()
mixin(Service, Logger, Cache)
function Service:init(name) self.name = name end

local s = Service("svc1")
s:log("started")
s:cache_set("user", "Alice")
print(s:cache_get("user"))
```

명시적이고 충돌이 보입니다.

## 5.7 private / protected — 관례와 클로저

Lua에는 접근 제어자가 없습니다. 두 가지 관례를 씁니다.

### A. 언더스코어 관례

```lua
function Account:init(balance)
    self._balance = balance       -- 외부에서 만지지 마세요
end
function Account:balance() return self._balance end
function Account:deposit(n) self._balance = self._balance + n end
```

빠르고 가볍지만 강제력은 없습니다.

### B. 클로저로 진짜 비공개

```lua
local function newAccount(initial)
    local balance = initial
    return {
        balance = function() return balance end,
        deposit = function(n) balance = balance + n end,
        withdraw = function(n)
            if n > balance then error("insufficient") end
            balance = balance - n
        end,
    }
end

local a = newAccount(100)
print(a.balance())    -- 100
a.deposit(50)
print(a.balance())    -- 150
print(a.balance)      -- function: 0x..  (값에 직접 접근 불가)
```

진짜 비공개를 만들지만 메타테이블/상속을 못 씁니다. 두 패턴을 섞기도 합니다.

### C. 약한 키 비공개 슬롯

```lua
local Account = class()
local private = setmetatable({}, {__mode = "k"})

function Account:init(b) private[self] = {balance = b} end
function Account:balance()  return private[self].balance end
function Account:deposit(n) private[self].balance = private[self].balance + n end
```

인스턴스가 GC 되면 비공개 데이터도 같이 사라집니다. 13장에서 약한 테이블을 자세히 다룹니다.

## 5.8 추상 메서드와 인터페이스

```lua
local Shape = class()
function Shape:area()
    error("Shape:area() is abstract", 2)
end
function Shape:describe()
    return ("area = %.2f"):format(self:area())
end

local Circle = class(Shape)
function Circle:init(r) self.r = r end
function Circle:area() return math.pi * self.r * self.r end

print(Circle(2):describe())   -- area = 12.57
```

추상 메서드 검사를 더 강하게 만들고 싶으면 인터페이스를 명시적으로 검증합니다.

```lua
local function implements(obj, iface)
    for _, m in ipairs(iface) do
        if type(obj[m]) ~= "function" then
            error("does not implement: " .. m, 2)
        end
    end
end

local Drawable = {"draw", "bounds"}

local Sprite = class()
function Sprite:init() implements(self, Drawable) end  -- 인스턴스 시점 검증
function Sprite:draw() end
function Sprite:bounds() return 0,0,1,1 end

Sprite()   -- OK
```

## 5.9 정적 메서드와 클래스 변수

`self` 가 필요 없는 메서드는 점(`.`)으로 정의합니다.

```lua
local Counter = class()
Counter.total = 0     -- 클래스 변수

function Counter:init()
    Counter.total = Counter.total + 1
    self.id = Counter.total
end

function Counter.count()    -- 정적 메서드
    return Counter.total
end

Counter(); Counter(); Counter()
print(Counter.count())   -- 3
```

## 5.10 == 와 tostring 갖춘 깔끔한 클래스

```lua
local Money = class()
function Money:init(amount, ccy)
    self.amount = amount
    self.ccy = ccy
end
function Money.__eq(a, b)
    return a.amount == b.amount and a.ccy == b.ccy
end
function Money.__add(a, b)
    assert(a.ccy == b.ccy, "currency mismatch")
    return Money(a.amount + b.amount, a.ccy)
end
function Money.__tostring(m)
    return ("%s %.2f"):format(m.ccy, m.amount)
end

local m1 = Money(100, "USD")
local m2 = Money(50, "USD")
print(m1 + m2)                -- USD 150.00
print(m1 == Money(100,"USD")) -- true
```

## 5.11 객체 직렬화

OOP를 쓰면 직렬화가 필요해집니다. 가장 단순한 형태는 다음과 같습니다.

```lua
local function serialize(o, indent)
    indent = indent or ""
    local t = type(o)
    if t == "nil" or t == "boolean" or t == "number" then
        return tostring(o)
    elseif t == "string" then
        return string.format("%q", o)
    elseif t == "table" then
        local parts = {}
        local next_i = indent .. "  "
        for k, v in pairs(o) do
            local key
            if type(k) == "string" and k:match("^[%a_][%w_]*$") then
                key = k
            else
                key = "[" .. serialize(k, next_i) .. "]"
            end
            parts[#parts+1] = next_i .. key .. " = " .. serialize(v, next_i)
        end
        return "{\n" .. table.concat(parts, ",\n") .. "\n" .. indent .. "}"
    end
    error("cannot serialize " .. t)
end

print(serialize({a=1, b={2,3,"x"}}))
```

함수, 메타테이블, 순환 참조까지 포함하면 일이 커집니다. 18장의 테스트 절에서 보조용 deepequal을 쓰는 쪽이 자주 더 실용적입니다.

## 5.12 OOP 안티패턴

| 안티패턴 | 왜 나쁜가 |
|---|---|
| 인스턴스마다 메타테이블 새로 생성 | 메모리 폭발, JIT 캐시 무효 |
| `__index = function` 으로 깊은 폴백 | 디버깅 어려움, 성능 저하 |
| 점/콜론 혼용 (`obj.foo()` vs `obj:foo()`) | self 가 nil 인 채 실행 |
| 부모 init 호출 누락 | 인스턴스 상태 미초기화 |
| 다중 상속 남용 | 다이아몬드 충돌 |
| 모든 메서드를 클래스에 박기 | 모듈로 분리하면 더 깔끔 |

---

# 6. 함수와 클로저

Lua의 함수는 **퍼스트 클래스 값**입니다. 변수에 담고, 인자로 넘기고, 반환하고, 테이블에 저장할 수 있습니다. 더 나아가 Lua의 함수는 자동으로 **클로저**입니다.

## 6.1 익명 함수와 식 위치

```lua
local f = function(x) return x * 2 end
print(f(3))   -- 6

table.sort(arr, function(a, b) return a > b end)

-- 즉시 호출 함수 (IIFE)
local config = (function()
    local t = {}
    t.host = os.getenv("HOST") or "localhost"
    return t
end)()
```

## 6.2 다중 반환과 select 다시 보기

이미 2.4 에서 봤지만, 함수 설계 관점에서 한 번 더 강조합니다.

```lua
-- 결과 + 에러 패턴 (Go 스타일)
local function parseInt(s)
    local n = tonumber(s)
    if not n then return nil, "not a number: " .. s end
    return n
end

local n, err = parseInt("abc")
if not n then print("error: " .. err) end
```

이 패턴은 10장의 에러 처리에서 더 다듬습니다.

## 6.3 가변 인자

```lua
local function log(level, ...)
    local n = select("#", ...)
    local parts = {}
    for i = 1, n do
        parts[i] = tostring(select(i, ...))
    end
    print(("[%s] %s"):format(level, table.concat(parts, " ")))
end

log("INFO", "user", 42, "logged in")
-- [INFO] user 42 logged in
```

`{...}` 와 `select` 의 차이를 다시 강조합니다.

```lua
local function f(...)
    local t = {...}
    print(#t)                   -- nil 만나면 끊김
    print(select("#", ...))     -- 진짜 개수
end
f(1, 2, nil, 4)
-- 2
-- 4
```

## 6.4 표현식 조각으로서의 함수 호출

함수의 **여러 반환값은 마지막 위치에서만 펼쳐진다**(2.4) — 가변 인자 전달도 같은 규칙입니다.

```lua
local function pass(...)
    return ...
end

print(pass(1, 2, 3))      -- 1 2 3
print(pass(1, 2, 3), 99)  -- 1 99   (끝이 아니라서 첫 값만)
```

이 규칙을 알면 함수 합성이 자연스럽습니다.

```lua
local function compose(f, g)
    return function(...) return f(g(...)) end
end
```

## 6.5 클로저

Lua 함수는 **렉시컬 스코프**입니다. 함수가 만들어진 곳의 local 변수를 캡처합니다.

```lua
local function makeCounter()
    local n = 0
    return function()
        n = n + 1
        return n
    end
end

local c = makeCounter()
print(c())   -- 1
print(c())   -- 2
print(c())   -- 3
```

`n` 은 외부 변수처럼 보이지만 `c` 의 **업밸류(upvalue)** 입니다. 다른 카운터를 만들면 별도의 `n`.

```lua
local a = makeCounter()
local b = makeCounter()
print(a(), a(), b())  -- 1   2   1
```

### 같은 업밸류 공유

같은 closure block에서 만든 함수 둘은 같은 업밸류를 공유합니다.

```lua
local function pair()
    local n = 0
    local function inc() n = n + 1 end
    local function get() return n end
    return inc, get
end

local inc, get = pair()
inc(); inc(); inc()
print(get())   -- 3
```

이게 OOP의 캡슐화를 클로저로 만드는 기반(5.7 B)입니다.

### 클로저로 만든 메모이저

```lua
local function memoize(f)
    local cache = {}
    return function(x)
        local v = cache[x]
        if v == nil then
            v = f(x)
            cache[x] = v
        end
        return v
    end
end

local function slow(x)
    local s = 0
    for i = 1, x do s = s + i end
    return s
end

local fast = memoize(slow)
print(fast(1000000))   -- 첫 호출은 느림
print(fast(1000000))   -- 두 번째는 캐시
```

다중 인자 메모이저, 약한 캐시 메모이저는 16장에서 다룹니다. 알고리즘 가이드의 메모이제이션 절도 참조 → [[Lua 알고리즘#7. 동적 계획법]].

## 6.6 부분 적용과 커링

```lua
local function partial(f, ...)
    local fixed = table.pack(...)
    return function(...)
        local args = table.move(fixed, 1, fixed.n, 1, {})
        local extra = table.pack(...)
        for i = 1, extra.n do args[fixed.n + i] = extra[i] end
        return f(table.unpack(args, 1, fixed.n + extra.n))
    end
end

local function add(a, b, c) return a + b + c end
local addOne = partial(add, 1)
local addOneTwo = partial(add, 1, 2)

print(addOne(2, 3))      -- 6
print(addOneTwo(10))     -- 13
```

진짜 커링 (한 번에 한 인자):

```lua
local function curry(f, n)
    local function rec(args)
        if #args >= n then return f(table.unpack(args, 1, n)) end
        return function(x)
            local na = table.move(args, 1, #args, 1, {})
            na[#na+1] = x
            return rec(na)
        end
    end
    return rec({})
end

local add3 = curry(function(a,b,c) return a+b+c end, 3)
print(add3(1)(2)(3))   -- 6
```

## 6.7 고차 함수와 컬렉션 헬퍼

표준 라이브러리에는 없습니다. 자주 쓰는 셋입니다.

```lua
local function map(t, f)
    local r = {}
    for i = 1, #t do r[i] = f(t[i], i) end
    return r
end

local function filter(t, pred)
    local r, n = {}, 0
    for i = 1, #t do
        if pred(t[i], i) then n = n + 1; r[n] = t[i] end
    end
    return r
end

local function reduce(t, f, init)
    local acc = init
    local i = 1
    if acc == nil then acc = t[1]; i = 2 end
    for j = i, #t do acc = f(acc, t[j]) end
    return acc
end

local xs = {1, 2, 3, 4, 5}
print(reduce(xs, function(a,b) return a+b end))   -- 15
print(table.concat(map(xs, function(x) return x*x end), ","))  -- 1,4,9,16,25
print(table.concat(filter(xs, function(x) return x%2==1 end), ","))  -- 1,3,5
```

16장에서 lazy seq 와 트랜스듀서를 다룹니다.

## 6.8 파이프 (pipe / chain)

```lua
local function pipe(...)
    local fns = {...}
    return function(x)
        for _, f in ipairs(fns) do x = f(x) end
        return x
    end
end

local trim = function(s) return s:match("^%s*(.-)%s*$") end
local upper = string.upper
local exclaim = function(s) return s .. "!" end

local shout = pipe(trim, upper, exclaim)
print(shout("  hello  "))   -- HELLO!
```

UNIX 파이프 같은 코드 작성이 가능합니다.

## 6.9 재귀와 꼬리 호출

Lua는 **꼬리 호출 최적화(TCO)** 를 보장합니다. 꼬리 호출은 스택을 늘리지 않습니다.

```lua
local function loop(n)
    if n <= 0 then return "done" end
    return loop(n - 1)        -- 꼬리 호출
end

print(loop(1000000))   -- 스택 오버플로 없이 동작
```

주의: `return loop(n-1) + 1` 은 꼬리 호출이 **아닙니다**. 반환 후 + 1 을 해야 하므로 스택 프레임이 남습니다.

```lua
-- 비꼬리 (스택 사용)
local function fact(n) return n <= 1 and 1 or n * fact(n-1) end

-- 꼬리화
local function fact_iter(n, acc)
    acc = acc or 1
    if n <= 1 then return acc end
    return fact_iter(n - 1, acc * n)
end
```

알고리즘 가이드의 재귀→반복 변환 절도 참조 → [[Lua 알고리즘#6.7 재귀 → 반복 변환]].

## 6.10 함수 식별과 일급성

함수도 **참조** 타입입니다. 두 함수 정의가 글자가 같아도 다른 객체입니다.

```lua
local f = function() end
local g = function() end
print(f == g)   -- false
print(f == f)   -- true
```

테이블의 키로도 쓸 수 있습니다.

```lua
local handlers = {}
handlers[print]  = "is print"
handlers[ipairs] = "is ipairs"

print(handlers[print])  -- is print
```

## 6.11 함수 호출 비용 의식

함수 호출 자체가 가장 빠른 연산은 아닙니다. 핫 루프에서는:

- 메서드 디스패치(`obj:m()`)는 일반 함수 호출보다 약간 느립니다(메타테이블 lookup).
- 클로저 호출은 일반 함수 호출과 거의 같지만, 만들어질 때(매 루프 안에서 생성)는 비쌉니다.

```lua
-- 나쁜 예: 매 반복마다 함수 객체 생성
for i = 1, 1e6 do
    table.sort(t, function(a,b) return a < b end)
end

-- 좋은 예: 한 번만 만들고 재사용
local cmp = function(a, b) return a < b end
for i = 1, 1e6 do table.sort(t, cmp) end
```

19장 LuaJIT 절에서 더 구체적으로 다룹니다.

---

# 7. 이터레이터

`for k, v in pairs(t) do ... end` 의 **`in`** 뒤에 무엇이 와도 되는지 정확히 이해하면, Lua의 모든 컬렉션을 동일한 문법으로 다룰 수 있습니다.

## 7.1 제네릭 for 의 정확한 정의

```lua
for var_1, ..., var_n in <ITER>, <STATE>, <INITIAL> do ... end
```

`<ITER>`, `<STATE>`, `<INITIAL>` 세 값이 필요합니다. 매 반복마다 Lua는 다음을 합니다.

```lua
local var_1, ..., var_n = ITER(STATE, var_1)
if var_1 == nil then break end
```

즉 이터레이터 함수는 `(state, control) → next_control, ...` 시그니처입니다.

대부분의 경우 첫 번째 식 하나만 씁니다(`pairs(t)`). 그건 그 함수가 세 값을 반환해 주기 때문입니다.

```lua
local function pairs_demo(t)
    return next, t, nil    -- iter, state, init
end

for k, v in pairs_demo({a=1, b=2}) do print(k, v) end
```

`next` 함수가 이터레이터, `t` 가 상태, `nil` 이 초기 키입니다.

## 7.2 Stateless 이터레이터 — `ipairs` 풀어 쓰기

```lua
local function iter(t, i)
    i = i + 1
    local v = t[i]
    if v == nil then return nil end
    return i, v
end

local function my_ipairs(t)
    return iter, t, 0
end

for i, v in my_ipairs({"a","b","c"}) do print(i, v) end
```

이런 형태를 **stateless iterator** 라고 합니다. 상태가 인자로만 흐르고, 함수 자체는 상태가 없습니다. 작고 빠릅니다.

## 7.3 Stateful 이터레이터 — 클로저로

```lua
local function range(a, b, step)
    step = step or 1
    local i = a - step
    return function()
        i = i + step
        if (step > 0 and i > b) or (step < 0 and i < b) then return nil end
        return i
    end
end

for i in range(1, 5) do io.write(i, " ") end       -- 1 2 3 4 5
print()
for i in range(10, 1, -2) do io.write(i, " ") end  -- 10 8 6 4 2
```

값을 반환하는 함수 하나만 있으면 됩니다 (state, init 은 무시됩니다). 가독성이 더 좋고, 여러 번 돌릴 수 없습니다(함수 호출이 한 번 쓰면 끝).

여러 번 돌리고 싶다면 stateless 형태를 쓰세요.

## 7.4 표준 이터레이터 모음

```lua
local M = {}

function M.range(a, b, step)
    step = step or 1
    if not b then a, b = 1, a end       -- range(n) → 1..n
    local i = a - step
    return function()
        i = i + step
        if (step > 0 and i > b) or (step < 0 and i < b) then return nil end
        return i
    end
end

function M.enumerate(t)
    local i = 0
    return function()
        i = i + 1
        if t[i] == nil then return nil end
        return i, t[i]
    end
end

function M.zip(a, b)
    local i = 0
    return function()
        i = i + 1
        if a[i] == nil or b[i] == nil then return nil end
        return a[i], b[i]
    end
end

function M.chain(...)
    local lists = {...}
    local li, i = 1, 0
    return function()
        while li <= #lists do
            i = i + 1
            local v = lists[li][i]
            if v ~= nil then return v end
            li = li + 1; i = 0
        end
    end
end

function M.take(n, gen)
    local i = 0
    return function()
        if i >= n then return nil end
        i = i + 1
        return gen()
    end
end

function M.filter(gen, pred)
    return function()
        while true do
            local v = gen()
            if v == nil then return nil end
            if pred(v) then return v end
        end
    end
end

function M.map(gen, f)
    return function()
        local v = gen()
        if v == nil then return nil end
        return f(v)
    end
end

return M
```

사용 예:

```lua
local I = require "iter"

for i, v in I.enumerate({"a","b","c"}) do
    print(i, v)
end

for a, b in I.zip({1,2,3}, {"x","y","z"}) do
    print(a, b)
end

for v in I.take(5, I.map(I.range(1, 1000), function(x) return x*x end)) do
    print(v)   -- 1, 4, 9, 16, 25
end
```

`pairs` 와 같은 인터페이스라 모든 for-루프와 자연스럽게 어울립니다.

## 7.5 무한 시퀀스

```lua
local function naturals()
    local n = 0
    return function() n = n + 1; return n end
end

local function fibs()
    local a, b = 0, 1
    return function() a, b = b, a+b; return a end
end

for v in I.take(10, fibs()) do io.write(v, " ") end
-- 1 1 2 3 5 8 13 21 34 55
```

8장의 코루틴으로 같은 구조를 더 우아하게 만들 수 있습니다.

## 7.6 트리 순회 이터레이터

자료구조 가이드에서 정의한 이진 트리(→ [[Lua 자료구조#10.3 이진 트리]])를 순회하는 외부 이터레이터를 코루틴 없이 만들면 다음과 같습니다.

```lua
local function inorder(root)
    local stack = {}
    local node = root
    return function()
        while node or #stack > 0 do
            while node do
                stack[#stack+1] = node
                node = node.left
            end
            node = stack[#stack]
            stack[#stack] = nil
            local out = node
            node = node.right
            return out
        end
        return nil
    end
end
```

같은 일을 코루틴으로는 한결 직관적으로 쓸 수 있습니다(8장의 8.6).

## 7.7 이터레이터 디자인 가이드

1. **stateful은 짧게 끝나는 흐름** — 한 번만 돌릴 거라면 클로저 이터레이터.
2. **stateless는 여러 번 돌리는 데이터** — 컬렉션 자체를 상태로.
3. **`for` 가 끊어지는 조건은 `nil`** — false 가 아니라.
4. **이터레이터가 자원을 잡고 있다면 보호** — 8.7 의 `for` + `coroutine.wrap` + `<close>` 조합.

---

# 8. 코루틴

코루틴은 Lua가 큰 동사적 무기입니다. 비선점형 멀티태스킹, 제너레이터, 비동기, 상태 머신, 외부 DSL 파서까지 한 도구로 표현할 수 있습니다.

## 8.1 코루틴이란

스레드와 다릅니다. 코루틴은 **명시적으로** 자신을 일시 중단(yield)하고 자원이 한 번에 한 코루틴만 실행됩니다. 그래서 OS 스레드 비용이 없고, 동기화 문제가 적습니다.

```lua
local co = coroutine.create(function(x)
    print("a:", x)
    local y = coroutine.yield(x + 1)
    print("b:", y)
    return "done"
end)

print(coroutine.resume(co, 10))   -- a: 10  →  true   11
print(coroutine.resume(co, 99))   -- b: 99  →  true   done
print(coroutine.resume(co))       -- false  cannot resume dead coroutine
```

이 4줄이 코루틴의 모든 것을 보여줍니다.

- `create(f)` — 코루틴 객체를 만듭니다. 아직 실행 안 함.
- `resume(co, ...)` — 시작 또는 재개. 첫 호출의 인자는 함수 인자, 이후 호출의 인자는 `yield` 의 반환값.
- `yield(...)` — 잠시 멈춤. `yield` 의 인자는 `resume` 의 반환값.
- `resume` 의 반환값은 `(ok, ...)` — 첫 값은 성공 여부.

## 8.2 상태와 status

```lua
print(coroutine.status(co))
-- suspended  : yield 후 멈춰 있음
-- running    : 지금 실행 중 (자기 자신만 봄)
-- normal     : 다른 코루틴을 resume 한 채 대기
-- dead       : 함수가 끝났거나 에러로 종료됨
```

## 8.3 wrap — 더 짧은 인터페이스

```lua
local gen = coroutine.wrap(function()
    for i = 1, 3 do coroutine.yield(i) end
end)

print(gen())   -- 1
print(gen())   -- 2
print(gen())   -- 3
print(gen())   -- 에러 (cannot resume dead)
```

`wrap` 은 `resume` 의 (ok, ...) 패턴이 사라지고 함수처럼 호출됩니다. 에러가 나면 그대로 던집니다. 에러를 잡고 싶으면 `create` + `resume` 을 직접 쓰세요.

## 8.4 코루틴 = 제너레이터

7.5 의 `fibs` 를 코루틴으로 다시 쓰면 훨씬 자연스럽습니다.

```lua
local function fibs()
    return coroutine.wrap(function()
        local a, b = 0, 1
        while true do
            a, b = b, a + b
            coroutine.yield(a)
        end
    end)
end

local g = fibs()
for i = 1, 10 do io.write(g(), " ") end   -- 1 1 2 3 5 8 13 21 34 55
```

for 루프와 어울리게 만들려면 그대로 사용하면 됩니다. `coroutine.wrap` 은 `pairs` 가 반환하는 형태와 같이 호출 가능한 객체를 줍니다.

```lua
for v in fibs() do
    if v > 100 then break end
    io.write(v, " ")
end
```

## 8.5 producer / consumer

```lua
local function producer()
    return coroutine.wrap(function()
        for i = 1, 5 do coroutine.yield("item " .. i) end
    end)
end

local function consumer(prod)
    for v in prod do print("got:", v) end
end

consumer(producer())
```

생산자가 데이터를 만들 준비가 되면 `yield`, 소비자는 `for` 로 받습니다. 푸시/풀 변환 없이 자연스럽게 흐릅니다.

## 8.6 트리 순회를 코루틴으로

7.6 의 명시적 스택 inorder 를 코루틴으로:

```lua
local function inorder(root)
    return coroutine.wrap(function()
        local function walk(node)
            if not node then return end
            walk(node.left)
            coroutine.yield(node)
            walk(node.right)
        end
        walk(root)
    end)
end

for n in inorder(tree) do
    print(n.value)
end
```

호출 스택이 자연스럽게 yield 위치를 기억합니다. 이게 코루틴이 "이어서 다시 시작"할 수 있다는 뜻입니다.

## 8.7 협력 스케줄러

OS 스레드 없이도 N개의 작업을 번갈아 진행시키는 작은 스케줄러를 만들 수 있습니다.

```lua
-- file: sched.lua
local Sched = {}
local tasks = {}

function Sched.spawn(f, ...)
    local args = table.pack(...)
    tasks[#tasks+1] = coroutine.create(function()
        f(table.unpack(args, 1, args.n))
    end)
end

function Sched.run()
    while #tasks > 0 do
        local alive = {}
        for _, co in ipairs(tasks) do
            local ok, err = coroutine.resume(co)
            if not ok then io.stderr:write("task error: " .. tostring(err) .. "\n") end
            if coroutine.status(co) ~= "dead" then alive[#alive+1] = co end
        end
        tasks = alive
    end
end

return Sched
```

```lua
-- file: main.lua
local S = require "sched"

local function worker(name, n)
    for i = 1, n do
        print(name, i)
        coroutine.yield()
    end
end

S.spawn(worker, "A", 3)
S.spawn(worker, "B", 5)
S.run()
-- A 1
-- B 1
-- A 2
-- B 2
-- A 3
-- B 3
-- B 4
-- B 5
```

각 작업은 자발적으로 `yield` 해서 양보합니다. 이 위에 sleep, channel, future 등을 얹으면 17장의 비동기 패턴이 됩니다.

## 8.8 sleep — 시간 기반 양보

```lua
-- file: sched2.lua
local Sched = {}
local now = os.time
local tasks = {}    -- {co=, due=}

function Sched.spawn(f, ...)
    local args = table.pack(...)
    tasks[#tasks+1] = {
        co = coroutine.create(function() f(table.unpack(args, 1, args.n)) end),
        due = 0,
    }
end

function Sched.sleep(s)
    coroutine.yield("sleep", s)
end

function Sched.run()
    while #tasks > 0 do
        local t = now()
        local alive = {}
        for _, task in ipairs(tasks) do
            if t >= task.due then
                local ok, kind, arg = coroutine.resume(task.co)
                if not ok then io.stderr:write(kind .. "\n") end
                if coroutine.status(task.co) ~= "dead" then
                    if kind == "sleep" then task.due = t + arg end
                    alive[#alive+1] = task
                end
            else
                alive[#alive+1] = task
            end
        end
        tasks = alive
    end
end

return Sched
```

```lua
local S = require "sched2"

S.spawn(function()
    print("A start", os.date("%X"))
    S.sleep(2)
    print("A end",   os.date("%X"))
end)

S.spawn(function()
    print("B start", os.date("%X"))
    S.sleep(1)
    print("B end",   os.date("%X"))
end)

S.run()
```

여기서 sleep 은 진짜 OS sleep이 아니라 "그 시간이 지나기 전에는 다시 깨우지 마라" 신호입니다. 이벤트 루프의 본질입니다.

## 8.9 채널 — 코루틴 사이의 통신

```lua
local Channel = {}
Channel.__index = Channel

function Channel.new()
    return setmetatable({queue={}, recvs={}}, Channel)
end

function Channel:send(v)
    if #self.recvs > 0 then
        local co = table.remove(self.recvs, 1)
        coroutine.resume(co, v)
    else
        self.queue[#self.queue+1] = v
    end
end

function Channel:recv()
    if #self.queue > 0 then
        return table.remove(self.queue, 1)
    end
    self.recvs[#self.recvs+1] = coroutine.running()
    return coroutine.yield()
end

-- 사용: producer 와 consumer 가 채널로 묶임
local ch = Channel.new()
local function producer()
    for i = 1, 3 do ch:send("msg " .. i) end
end
local function consumer()
    for i = 1, 3 do print(ch:recv()) end
end

local pco = coroutine.create(producer)
local cco = coroutine.create(consumer)
coroutine.resume(cco)   -- 먼저 대기
coroutine.resume(pco)   -- 보내면서 깨움
```

Go의 채널 흉내입니다. 단순화 버전이라 라운드 로빈 스케줄러와 함께 쓰면 더 자연스럽게 동작합니다.

## 8.10 코루틴 함정

| 함정 | 증상 | 해결 |
|---|---|---|
| C 함수 안에서 yield | "attempt to yield across C-call" | 메타메서드, pcall 안에서 yield 금지 (5.4는 pcall은 OK) |
| 메인 코루틴에서 yield | 에러 | 항상 `coroutine.create` 안에서만 |
| `wrap` 의 에러 무시 | 디버깅 어려움 | `create + resume` 으로 명시적 처리 |
| dead 코루틴 resume | 에러 | `coroutine.status` 확인 |
| 큰 데이터 yield | 메모리/속도 손해 | 가급적 작은 신호만 |

## 8.11 5.4 의 변경점 — pcall에서 yield 가능

```lua
-- 5.4 부터 OK
local co = coroutine.create(function()
    pcall(coroutine.yield, "hi")
    print("after pcall")
end)
print(coroutine.resume(co))   -- true   hi
print(coroutine.resume(co))   -- after pcall
                              -- true
```

5.1/5.2 에서는 `pcall` 안에서 `yield` 하면 에러였습니다. 5.3 에서 일부 가능해졌고, 5.4 부터는 자유롭게 됩니다. LuaJIT 호환을 신경 쓴다면 의존하지 말 것.

---

# 9. 모듈과 패키지

여러 파일에 코드를 나누고, `require` 로 불러오고, 의존성을 깔끔히 관리하는 법.

## 9.1 모듈의 모양

가장 기본적인 모듈 패턴:

```lua
-- file: math2.lua
local M = {}

function M.clamp(x, lo, hi)
    if x < lo then return lo end
    if x > hi then return hi end
    return x
end

function M.lerp(a, b, t) return a + (b - a) * t end

return M
```

```lua
-- file: main.lua
local m2 = require "math2"
print(m2.clamp(15, 0, 10))   -- 10
print(m2.lerp(0, 100, 0.3))  -- 30
```

`require` 는 **파일 경로가 아니라 모듈 이름**을 받습니다. 검색 경로(`package.path`)를 따라 파일을 찾습니다.

## 9.2 require 의 캐시

`require` 는 같은 모듈을 두 번 부르면 **두 번째부터는 캐시된 값을 그대로** 돌려줍니다.

```lua
local a = require "math2"
local b = require "math2"
print(a == b)   -- true (같은 객체)
```

캐시는 `package.loaded` 에 들어 있습니다.

```lua
package.loaded.math2 = nil          -- 강제 재로딩
local m2 = require "math2"          -- 다시 실행됨
```

이 동작이 9.7 의 핫 리로드 패턴의 기반입니다.

## 9.3 검색 경로 — package.path

`require "foo"` 는 `package.path` 의 `?` 자리에 `foo` 를 끼워 넣어 시도합니다.

```lua
print(package.path)
-- 보통 ./?.lua;./?/init.lua;/usr/share/lua/5.4/?.lua;...
```

`?` 는 모듈 이름. `foo.bar` 이면 `?` 자리에 `foo/bar` 가 들어갑니다(점이 슬래시로 변환).

경로 추가:

```lua
package.path = package.path .. ";./vendor/?.lua;./vendor/?/init.lua"
```

C 모듈은 `package.cpath` 에 있고 `.so` / `.dll` 을 찾습니다.

## 9.4 init.lua — 디렉터리 모듈

```
mylib/
  init.lua
  utils.lua
  parser.lua
```

```lua
-- mylib/init.lua
local M = {}
M.utils  = require "mylib.utils"
M.parser = require "mylib.parser"
return M
```

```lua
local mylib = require "mylib"
print(mylib.utils.something())
```

`require "mylib"` 가 자동으로 `mylib/init.lua` 를 찾습니다.

## 9.5 모듈 스타일 — return 한 객체

권장 스타일은 **로컬 테이블을 만들고, 그 테이블을 return** 하는 것입니다.

```lua
-- 좋은 스타일
local M = {}
function M.foo() end
return M

-- 나쁜 스타일 (전역 오염)
function foo() end
function bar() end
-- (return 없음)
```

`return` 이 없으면 `require` 는 `true` 를 캐시합니다. 그래서 다음 require에서 받을 게 아무것도 없습니다.

## 9.6 비공개 헬퍼 분리

모듈 안의 helper는 모두 `local` 로 선언하세요. `M.helper` 만 외부에 노출됩니다.

```lua
local M = {}

local function _normalize(s) return s:lower():gsub("%s+", " ") end   -- 비공개

function M.compare(a, b)
    return _normalize(a) == _normalize(b)
end

return M
```

`_normalize` 는 모듈 외부에서 보이지 않습니다.

## 9.7 핫 리로드

게임이나 REPL 환경에서 코드를 다시 불러오고 싶을 때:

```lua
local function reload(name)
    package.loaded[name] = nil
    return require(name)
end

local game = require "game"
-- 코드 수정 후
game = reload "game"
```

함정: 이전 모듈 객체를 누가 들고 있다면 그건 그대로 남아 있습니다. 핫 리로드를 본격적으로 하려면 모듈을 통째로 갈아끼우는 대신 모듈 안의 함수만 갱신하는 패턴이 더 안전합니다.

```lua
-- file: hot.lua
local function reload_into(target, name)
    package.loaded[name] = nil
    local fresh = require(name)
    for k, v in pairs(fresh) do target[k] = v end
    return target
end
```

## 9.8 의존성 사이클

A → B → A 처럼 두 모듈이 서로를 require 하면 사이클이 생깁니다. Lua는 **부분적으로 로드된** 모듈을 받게 됩니다.

```lua
-- a.lua
local b = require "b"
local M = {}
function M.greet() return "hi from A" end
M.fromB = b.greet     -- 이 시점 b 는 아직 미완성일 수 있음
return M

-- b.lua
local a = require "a"  -- a 는 부분 로드 (M 빈 테이블)
local M = {}
function M.greet() return "hi from B" end
return M
```

해결책:

1. 사이클 자체를 분리 (인터페이스/공용 모듈을 별도로)
2. 함수 호출 시점에 require (지연 로딩)

```lua
-- a.lua
local M = {}
function M.greet()
    local b = require "b"   -- 호출 시 require → 사이클 풀림
    return b.greet()
end
return M
```

## 9.9 _ENV — 환경 격리

Lua 5.2 부터 모든 코드 청크는 `_ENV` 라는 업밸류를 갖습니다. 전역 접근 `x` 는 사실 `_ENV.x` 입니다.

```lua
local function safe_run(code)
    local env = setmetatable({}, {__index = {print = print, math = math}})
    local f, err = load(code, "sandbox", "t", env)
    if not f then return nil, err end
    return pcall(f)
end

print(safe_run("print(math.sqrt(16))"))
-- 4.0
-- true

print(safe_run("os.execute('rm -rf /')"))
-- nil  attempt to index a nil value (global 'os')
-- false
```

`os`, `io`, `package` 등을 빼면 위험한 작업을 차단할 수 있습니다. 게임 모드, 설정 DSL, 플러그인 시스템에 자주 쓰입니다.

### load 의 모드

`load(chunk, name, mode, env)` 의 `mode` 는 `"t"`(텍스트만), `"b"`(바이너리만), `"bt"`(둘 다)입니다. **샌드박스에서는 반드시 `"t"`** 로 — 바이너리 청크는 검증되지 않은 바이트코드라 Lua VM을 깨뜨릴 수 있습니다.

## 9.10 모듈 실전 패턴

### 싱글톤 모듈

`require` 가 캐시하므로 모듈 자체가 자연스럽게 싱글톤입니다.

```lua
-- file: config.lua
local M = {}
M.host = os.getenv("HOST") or "localhost"
M.port = tonumber(os.getenv("PORT")) or 8080
return M
```

여러 곳에서 `require "config"` 해도 항상 같은 객체.

### 옵션 받는 팩토리 모듈

```lua
-- file: logger.lua
local function new(opts)
    opts = opts or {}
    local prefix = opts.prefix or "LOG"
    return {
        info = function(msg) print(("[%s] %s"):format(prefix, msg)) end,
    }
end

return {new = new}
```

```lua
local Logger = require "logger"
local lg = Logger.new{prefix="GAME"}
lg.info("started")
```

### 명시적 export 리스트

```lua
local function _greet() end
local function _add(a,b) return a+b end

return {
    greet = _greet,
    add   = _add,
}
```

자기 모듈에서 무엇이 공개되는지 한 줄에 보입니다.

---

# 10. 에러 처리

Lua의 에러 모델은 작지만 강력합니다. 핵심 함수는 다섯 개입니다.

| 함수 | 역할 |
|---|---|
| `error(v, level)` | 에러 던지기 |
| `assert(cond, msg)` | 조건 실패 시 error |
| `pcall(f, ...)` | f 보호 호출, `(ok, ret_or_err)` |
| `xpcall(f, handler, ...)` | pcall + 핸들러로 트레이스백 |
| `debug.traceback(msg)` | 호출 스택 문자열 |

## 10.1 에러 던지기

```lua
local function divide(a, b)
    if b == 0 then error("division by zero", 2) end
    return a / b
end
```

`level` 인자:

- `1` (기본) — 에러 메시지에 `error` 가 호출된 위치 표시
- `2` — **호출자**의 위치 표시 (대부분 우리가 원하는 것)
- `0` — 위치 없음

```lua
divide(1, 0)
-- main.lua:1: division by zero    (level=2 라서 호출자 위치)
```

## 10.2 assert — 짧은 가드

```lua
local function open_config(path)
    local f = assert(io.open(path, "r"), "config not found: " .. path)
    -- ...
end
```

`assert(x, msg)` 는 x 가 truthy 면 x 를 그대로 반환, falsy 면 `error(msg)` 합니다.

## 10.3 pcall — 보호 호출

```lua
local ok, ret = pcall(function() return 10 / 0 end)
-- Lua 에서 0 나눗셈은 inf 라 에러 아님

local ok, err = pcall(function() error("boom") end)
print(ok, err)
-- false   main.lua:N: boom
```

여러 반환값:

```lua
local ok, a, b = pcall(function() return 1, 2 end)
print(ok, a, b)   -- true 1 2
```

## 10.4 xpcall + traceback

```lua
local function risky() error("bad") end

local ok, err = xpcall(risky, debug.traceback)
print(err)
-- main.lua:1: bad
-- stack traceback:
--   [C]: in function 'error'
--   main.lua:1: in function <main.lua:1>
--   ...
```

`xpcall(f, handler, ...)` — 에러 발생 시 `handler(err)` 가 호출되고 그 반환값이 `xpcall` 의 두 번째 반환값.

## 10.5 에러 객체

`error` 의 인자는 문자열일 필요가 없습니다. 테이블이면 그대로 전달됩니다.

```lua
local function http_get(url)
    if url:sub(1, 4) ~= "http" then
        error({code = "ESCHEME", msg = "bad scheme: " .. url})
    end
end

local ok, err = pcall(http_get, "ftp://x")
if not ok then
    if type(err) == "table" then
        print(err.code, err.msg)
    end
end
```

이 방식은 Go 의 sentinel error, Java의 exception class 와 유사한 효과를 줍니다.

### 에러 클래스 만들기

```lua
local Error = {}
Error.__index = Error

function Error.new(code, msg, cause)
    return setmetatable({code=code, msg=msg, cause=cause}, Error)
end

function Error:__tostring()
    local s = ("%s: %s"):format(self.code, self.msg)
    if self.cause then s = s .. " (caused by: " .. tostring(self.cause) .. ")" end
    return s
end

local function isError(e, code)
    return type(e) == "table" and getmetatable(e) == Error and (not code or e.code == code)
end

local function fail(code, msg)
    error(Error.new(code, msg), 2)
end

-- 사용
local ok, err = pcall(function() fail("ENOENT", "file not found") end)
if isError(err, "ENOENT") then
    print("file missing")
elseif not ok then
    error(err)
end
```

## 10.6 finally 패턴

Lua에는 try/finally가 없지만 5.4 의 `<close>` 로 만듭니다.

```lua
local function with_close(setup, body)
    local res <close> = setup()
    return body(res)
end

local function file_resource(path, mode)
    local f = assert(io.open(path, mode))
    return setmetatable({f=f}, {
        __close = function(self) self.f:close() end,
        __index = {read = function(s, ...) return s.f:read(...) end},
    })
end

with_close(
    function() return file_resource("/etc/hostname", "r") end,
    function(f)
        print(f:read("l"))
        if math.random() < 0.5 then error("oops") end
    end
)
-- 에러가 나도 close 는 호출됨
```

5.1/5.2 에서는 `pcall` + 명시적 정리:

```lua
local function safe(setup, body)
    local res = setup()
    local ok, err = pcall(body, res)
    res:close()
    if not ok then error(err) end
end
```

## 10.7 에러 변환과 래핑

```lua
local function load_user(id)
    local data, err = db.fetch(id)
    if not data then
        error(Error.new("EDB", "fetch failed", err))
    end
    return data
end
```

원래 에러를 cause 에 보존하면서 의미를 바꿔 재던집니다. `pcall` 로 잡아서 한 단 위에서 메시지를 풍부하게 만들 때 유용합니다.

## 10.8 result 스타일 vs throw 스타일

Lua는 두 스타일을 다 씁니다.

- **(ok, value_or_err) 반환** — Go 식. `tonumber`, `io.open`, `pcall` 결과 등 표준이 이 스타일.
- **error 던지기** — Java/Python 식. assert, 라이브러리 내부 일관성 검사.

가이드라인:

- **예상 가능한 실패**(파일 없음, 파싱 실패) → result 스타일.
- **버그/불변량 위반**(요구사항 위반) → error 스타일.

```lua
-- 예상 가능
local n, err = parseInt(input)
if not n then return nil, err end

-- 불변량
function set:remove(x)
    assert(self[x], "remove: not in set")
    self[x] = nil
end
```

## 10.9 protect 헬퍼

throw 스타일 함수를 result 스타일로 바꿔주는 어댑터:

```lua
local function protect(f)
    return function(...)
        local ok, ret = pcall(f, ...)
        if not ok then return nil, ret end
        return ret
    end
end

local safe_parse = protect(function(s)
    if not s:match("^%d+$") then error("invalid") end
    return tonumber(s)
end)

print(safe_parse("123"))    -- 123
print(safe_parse("abc"))    -- nil   "main.lua:...: invalid"
```

반대 어댑터(result→throw)도 짧습니다.

```lua
local function unwrap(v, err)
    if v == nil then error(err, 2) end
    return v
end
```

## 10.10 트레이스백을 풍부하게

기본 traceback은 충분히 자세하지만 더 정보를 넣고 싶을 때:

```lua
local function trace(err)
    local out = {tostring(err)}
    local i = 2
    while true do
        local info = debug.getinfo(i, "Sln")
        if not info then break end
        local where = info.source .. ":" .. (info.currentline or "?")
        local name  = info.name or "<anon>"
        out[#out+1] = ("  at %s (%s)"):format(name, where)
        i = i + 1
    end
    return table.concat(out, "\n")
end

local ok, err = xpcall(function() error("oops") end, trace)
print(err)
```

12장의 디버그 라이브러리에서 이 도구들을 더 깊이 다룹니다.

---

# 11. 문자열과 패턴

Lua의 패턴은 PCRE보다 작지만 단어 검색, 토큰화, 간단한 파싱에는 충분합니다. 정규표현식이 필요하면 LPeg / lrexlib 같은 외부 라이브러리를 쓰지만, 표준 패턴만으로도 놀라울 만큼 많은 일을 할 수 있습니다.

## 11.1 표준 라이브러리 한눈에

```lua
print(string.len("hello"))       -- 5
print(string.upper("hello"))     -- HELLO
print(string.lower("HELLO"))     -- hello
print(string.rep("ab", 3))       -- ababab
print(string.rep("x", 5, "-"))   -- x-x-x-x-x   (구분자, 5.3+)
print(string.reverse("abc"))     -- cba
print(string.sub("hello", 2, 4)) -- ell
print(string.byte("A"))          -- 65
print(string.char(65, 66, 67))   -- ABC

print(string.format("name=%s age=%d pi=%.2f", "Lua", 30, 3.14159))
-- name=Lua age=30 pi=3.14
```

콜론 호출:

```lua
print(("hello"):upper())
print((" hi "):match("^%s*(.-)%s*$"))   -- "hi"
```

## 11.2 패턴 클래스

| 패턴 | 의미 |
|---|---|
| `.` | 모든 문자 |
| `%a` | 영문자 |
| `%d` | 숫자 |
| `%w` | 영숫자 |
| `%s` | 공백 |
| `%p` | 구두점 |
| `%l` | 소문자 |
| `%u` | 대문자 |
| `%c` | 제어 문자 |
| `%x` | 16진수 |
| `%A %D %W %S %P %L %U %C %X` | 위의 보색(대문자) |
| `[abc]` | a 또는 b 또는 c |
| `[a-z]` | 범위 |
| `[^abc]` | a/b/c 가 아님 |

수량자:

| 수량자 | 의미 |
|---|---|
| `*` | 0개 이상 (욕심) |
| `+` | 1개 이상 (욕심) |
| `-` | 0개 이상 (게으름) |
| `?` | 0 또는 1개 |

앵커:

| 앵커 | 의미 |
|---|---|
| `^` | 문자열 시작 |
| `$` | 문자열 끝 |

`%` 이스케이프:

```lua
print(("a.b.c"):match("(%a)%.(%a)"))   -- a   b
```

`%` 가 매직 문자(`. % + - * ? [ ] ^ $`) 앞에 오면 그 글자 자체를 의미합니다.

## 11.3 string.find — 위치 검색

```lua
local s = "hello world"
print(s:find("world"))             -- 7 11
print(s:find("WORLD"))             -- nil
print(s:find("world", 1, true))    -- 7 11   (plain text, 패턴 해석 X)
```

`find` 는 시작/끝 인덱스를 반환합니다. 캡처가 있으면 추가로 캡처 값들도 반환합니다.

```lua
print(("name=Lua"):find("(%w+)=(%w+)"))
-- 1   8   name   Lua
```

## 11.4 string.match — 캡처만

```lua
print(("name=Lua"):match("(%w+)=(%w+)"))
-- name   Lua

print(("  hi  "):match("^%s*(.-)%s*$"))
-- hi   (트림)
```

`-` 는 게으름 매칭이라 가운데 공백을 보존하면서 양 끝 공백을 정확히 잘라냅니다.

## 11.5 string.gmatch — 토큰 이터레이터

```lua
for word in ("hello, lua, world"):gmatch("%w+") do
    print(word)
end
-- hello
-- lua
-- world

-- 키=값 페어 추출
for k, v in ("a=1; b=2; c=3"):gmatch("(%w+)=(%w+)") do
    print(k, v)
end
```

CSV 파서를 한 줄에:

```lua
local function split_csv(s)
    local r = {}
    for field in s:gmatch("[^,]+") do
        r[#r+1] = field
    end
    return r
end
```

(따옴표가 있는 필드까지 처리하려면 LPeg.)

## 11.6 string.gsub — 치환

```lua
print(("hello world"):gsub("o", "0"))         -- hell0 w0rld   2
print(("hello"):gsub("l", "L", 1))            -- heLlo   1   (개수 제한)

-- 함수 치환
print(("a1 b22 c333"):gsub("(%a)(%d+)", function(c, n)
    return c:upper() .. (#n)
end))
-- A1 B2 C3   3

-- 테이블 치환
local vars = {name="Lua", lang="Programming"}
print(("hello, %{name} %{lang}"):gsub("%%{(%w+)}", vars))
-- hello, Lua Programming
```

`gsub` 는 치환된 문자열과 치환 횟수를 함께 돌려줍니다.

## 11.7 string.format — 자세히

C printf 와 거의 같습니다.

```lua
print(string.format("%5d", 42))      -- "   42"
print(string.format("%-5d|", 42))    -- "42   |"
print(string.format("%05d", 42))     -- "00042"
print(string.format("%.3f", 3.14159))-- "3.142"
print(string.format("%e", 1234567))  -- "1.234567e+06"
print(string.format("%x", 255))      -- "ff"
print(string.format("%X", 255))      -- "FF"
print(string.format("%q", 'he said "hi"'))
-- "he said \"hi\""    (Lua 리터럴로 안전)
```

`%q` 는 직렬화에서 자주 씁니다(5.11).

## 11.8 캡처 응용

### 위치 캡처

```lua
print(("hello"):match("()l()"))   -- 3   4
```

빈 괄호 `()` 는 그 위치의 인덱스를 캡처합니다.

### 후방 참조

```lua
print(("abcabc"):match("(%a+)%1"))   -- abc   (앞 캡처가 그대로 반복)
```

`%1` ~ `%9` 는 같은 패턴 안에서 이전 캡처를 참조합니다.

### `%b()` — 균형 매칭

```lua
print(("f(g(h)i)j"):match("%b()"))   -- (g(h)i)
```

여는/닫는 괄호가 짝을 이루는 부분을 찾습니다. JSON 형태나 LISP 표현 파싱에 유용합니다.

## 11.9 미니 템플릿 엔진

```lua
local function render(tpl, ctx)
    return (tpl:gsub("{{%s*([%w_.]+)%s*}}", function(key)
        local v = ctx
        for part in key:gmatch("[^.]+") do
            v = v[part]
            if v == nil then return "" end
        end
        return tostring(v)
    end))
end

print(render("Hello, {{user.name}}! You have {{user.msgs}} messages.",
    {user = {name = "Lua", msgs = 3}}))
-- Hello, Lua! You have 3 messages.
```

## 11.10 미니 INI 파서

```lua
local function parse_ini(text)
    local out, cur = {}, nil
    for line in text:gmatch("[^\r\n]+") do
        if not line:match("^%s*[#;]") and not line:match("^%s*$") then
            local section = line:match("^%s*%[(.-)%]%s*$")
            if section then
                cur = {}
                out[section] = cur
            else
                local k, v = line:match("^%s*([%w_]+)%s*=%s*(.-)%s*$")
                if k then (cur or out)[k] = v end
            end
        end
    end
    return out
end

local cfg = parse_ini[[
[server]
host = localhost
port = 8080
[db]
url = postgres://...
]]
print(cfg.server.host)   -- localhost
print(cfg.db.url)        -- postgres://...
```

50줄도 안 되는 코드로 INI를 받아냅니다.

## 11.11 패턴 vs 정규표현식 — 한계

Lua 패턴이 못 하는 것:

- 대안(`|`)
- 그룹 수량자(`(abc)+`)
- 룩어헤드/룩비하인드
- 유니코드 클래스 (utf8 라이브러리는 별도)
- 비탐욕 `+`, `*` (단 `-` 가 비슷한 역할)

이런 게 필요하면 LPeg(`lpeg`, `lpeg.re`)로 가세요. LPeg는 PEG 기반이라 패턴보다 강력하고, 표현식이 깔끔합니다.

## 11.12 utf8 라이브러리 (5.3+)

```lua
local s = "한글"
print(#s)              -- 6  (바이트 수)
print(utf8.len(s))     -- 2  (코드포인트 수)

for p, c in utf8.codes(s) do
    print(p, c, utf8.char(c))
end
-- 1   54620   한
-- 4   44544   글

print(utf8.char(0x1F600))   -- 😀
print(utf8.offset(s, 2))    -- 4 (두 번째 문자의 바이트 위치)
```

`string.upper`, `lower`, `sub` 는 ASCII 기준이므로 한글/이모지에 안전하지 않습니다. 다국어 처리에는 `utf8.*` 를 결합해야 합니다.

---

# 12. 디버그와 성찰(introspection)

`debug` 라이브러리는 강력해서 사용자 코드에 노출하면 위험하지만, 디버거/프로파일러/테스트 도구를 만들 때 핵심입니다.

## 12.1 debug.traceback

```lua
local function inner() print(debug.traceback("here", 1)) end
local function outer() inner() end
outer()
-- here
-- stack traceback:
--   main.lua:1: in function 'inner'
--   main.lua:2: in function 'outer'
--   main.lua:3: in main chunk
```

10.4 의 xpcall 핸들러로 자주 씁니다.

## 12.2 debug.getinfo — 함수/스택 메타데이터

```lua
local info = debug.getinfo(1)   -- 현재 위치
print(info.source, info.currentline, info.what, info.name)
```

레벨별로:

```lua
local function tracelevels()
    local i = 1
    while true do
        local info = debug.getinfo(i, "Sln")
        if not info then break end
        print(i, info.short_src .. ":" .. (info.currentline or "?"), info.name or "<anon>")
        i = i + 1
    end
end

local function a() tracelevels() end
local function b() a() end
b()
```

`getinfo(level, what)` 의 `what` 문자:

| 문자 | 정보 |
|---|---|
| `n` | name, namewhat |
| `S` | source, short_src, what, linedefined |
| `l` | currentline |
| `t` | istailcall |
| `u` | nups (업밸류 개수) |
| `f` | func 자체 |
| `L` | activelines (실행 가능 라인) |

## 12.3 debug.getlocal / setlocal

스택의 로컬 변수에 접근:

```lua
local function spy()
    local i = 1
    while true do
        local name, value = debug.getlocal(2, i)   -- 호출자의 i번째 local
        if not name then break end
        print(name, value)
        i = i + 1
    end
end

local function f()
    local x = 10
    local y = "hi"
    spy()
end
f()
-- x   10
-- y   hi
```

`debug.setlocal` 로 변경도 가능합니다(런타임 디버거 빌드에 필수).

## 12.4 debug.getupvalue / setupvalue

함수의 업밸류(클로저가 잡고 있는 외부 변수):

```lua
local function makeC()
    local n = 0
    return function() n = n + 1; return n end
end

local c = makeC()
print(c(), c(), c())   -- 1 2 3

local name, val = debug.getupvalue(c, 1)
print(name, val)       -- n   3
debug.setupvalue(c, 1, 100)
print(c())             -- 101
```

이 메커니즘으로 두 클로저가 같은 업밸류를 공유하게 만들 수도 있습니다(`debug.upvaluejoin`).

## 12.5 debug.sethook — 라인/콜 훅

```lua
local lines = {}
debug.sethook(function(event, line)
    lines[#lines+1] = line
end, "l")    -- l = 라인 단위

local x = 1
local y = 2
local z = x + y

debug.sethook()    -- 끄기

for _, l in ipairs(lines) do print(l) end
```

훅 이벤트:

- `"call"` — 함수 진입
- `"return"` — 함수 종료
- `"line"` — 새 라인 실행
- `"count"` — N 명령마다 (마지막 인자로 횟수 지정)

이걸로 커버리지, 프로파일러, 단계 실행 디버거를 만듭니다.

## 12.6 미니 프로파일러

```lua
local prof = {}
local stats = {}    -- {func_name = {n=, total=, last_enter=}}

local function key(info)
    return (info.short_src or "?") .. ":" ..
           (info.linedefined or "?") .. ":" ..
           (info.name or "?")
end

local function on_event(event)
    local info = debug.getinfo(2, "nS")
    if not info then return end
    local k = key(info)
    local s = stats[k] or {n=0, total=0, last_enter=0}
    if event == "call" then
        s.last_enter = os.clock()
    else
        s.total = s.total + (os.clock() - s.last_enter)
        s.n = s.n + 1
    end
    stats[k] = s
end

function prof.start() debug.sethook(on_event, "cr") end
function prof.stop()  debug.sethook() end
function prof.report()
    local rows = {}
    for k, s in pairs(stats) do
        rows[#rows+1] = {k=k, n=s.n, total=s.total, avg = s.n > 0 and s.total/s.n or 0}
    end
    table.sort(rows, function(a, b) return a.total > b.total end)
    print(("%-50s %6s %10s %10s"):format("func", "calls", "total", "avg"))
    for _, r in ipairs(rows) do
        print(("%-50s %6d %10.4f %10.6f"):format(r.k, r.n, r.total, r.avg))
    end
end

return prof
```

```lua
local prof = require "prof"
prof.start()
-- 측정하고 싶은 코드
for i = 1, 1e5 do math.sqrt(i) end
prof.stop()
prof.report()
```

LuaJIT 의 JIT 컴파일러는 이런 훅이 켜진 동안 인터프리터로 떨어지므로, 프로덕션 측정엔 다른 도구를 쓰세요.

## 12.7 안전한 디버그 사용

`debug` 의 모든 함수는 외부 입력에서 차단해야 합니다. 9.9 의 샌드박스 환경에서 `debug` 를 빼는 이유입니다. 실수로라도 사용자가 작성한 코드가 `debug.setupvalue` 를 부르게 하지 마세요.

---

# 13. 가비지 컬렉션과 메모리

Lua는 incremental mark-and-sweep GC 를 갖고 있고, 5.4 부터 generational mode 를 추가로 제공합니다.

## 13.1 collectgarbage 인터페이스

```lua
print(collectgarbage("count"))   -- 현재 사용 메모리 (KB, 실수)

collectgarbage("collect")        -- 즉시 한 사이클 (debugging용)
collectgarbage("stop")           -- GC 중지
collectgarbage("restart")        -- 재개

collectgarbage("incremental")    -- 5.4: incremental 모드
collectgarbage("generational")   -- 5.4: generational 모드
```

게임 루프에서 stuttering 을 줄이려고 GC를 멈추고, 프레임 끝에 `step` 으로 조금씩 돌리는 패턴을 쓰기도 합니다.

```lua
collectgarbage("stop")
while running do
    update_frame()
    collectgarbage("step", 100)   -- 정수만큼 일을 시킴
end
```

## 13.2 약한 테이블

테이블 메타테이블의 `__mode` 필드로 키/값을 약한 참조로 만듭니다.

```lua
local cache = setmetatable({}, {__mode = "v"})  -- value 가 약함

cache.user1 = {name = "A"}
cache.user2 = {name = "B"}

collectgarbage()
print(cache.user1, cache.user2)
-- nil   nil   (다른 강한 참조가 없으면 GC 됨)
```

`__mode`:

- `"k"` — 키가 약함 (키가 GC 되면 항목 사라짐)
- `"v"` — 값이 약함
- `"kv"` — 둘 다

응용:

```lua
-- 객체별 메타데이터 (객체가 살아 있는 동안만)
local meta = setmetatable({}, {__mode = "k"})

local function setMeta(obj, k, v)
    meta[obj] = meta[obj] or {}
    meta[obj][k] = v
end
local function getMeta(obj, k)
    return meta[obj] and meta[obj][k]
end

local u = {name = "Alice"}
setMeta(u, "score", 100)
print(getMeta(u, "score"))   -- 100
u = nil
collectgarbage()
-- meta 의 항목도 같이 사라짐
```

5.7 C 의 비공개 슬롯이 이 패턴입니다.

## 13.3 __gc — 파이널라이저

테이블에 `__gc` 메타메서드가 있으면 GC 직전에 한 번 호출됩니다.

```lua
local function with_finalizer()
    local t = setmetatable({}, {
        __gc = function(self) print("finalizing", self) end,
    })
    return t
end

do
    local t = with_finalizer()
end
collectgarbage()
-- finalizing   table: 0x...
```

주의:

1. 5.2 부터 메타테이블에 **`__gc` 가 처음 설정될 때** 등록됩니다. 사후 추가는 무시됩니다.
2. 파이널라이저 안에서 에러를 던지면 무시됩니다(메시지만 stderr).
3. 절대 빠른 작업이 아닙니다.

C 자원(파일, 소켓) 정리에 가장 자주 씁니다. Lua 5.4 의 `<close>` 가 더 결정적이라 먼저 검토하세요.

## 13.4 객체 풀

자주 만들고 버리는 작은 객체는 풀에서 재활용하면 GC 압력을 줄일 수 있습니다.

```lua
local function make_pool(create, reset)
    local free, n = {}, 0
    return {
        acquire = function(...)
            if n > 0 then
                local o = free[n]; free[n] = nil; n = n - 1
                reset(o, ...)
                return o
            end
            return create(...)
        end,
        release = function(o)
            n = n + 1
            free[n] = o
        end,
    }
end

local Vec = {}; Vec.__index = Vec
function Vec.new(x, y) return setmetatable({x=x, y=y}, Vec) end

local pool = make_pool(
    function(x, y) return Vec.new(x, y) end,
    function(o, x, y) o.x = x; o.y = y end
)

for i = 1, 1000 do
    local v = pool.acquire(i, i*2)
    -- 사용
    pool.release(v)
end
```

벡터, 파티클, 이벤트 객체에서 효과가 큽니다. 게임 루프에서 흔한 패턴.

## 13.5 메모리 측정

```lua
local function measure(label, f)
    collectgarbage(); collectgarbage()
    local before = collectgarbage("count")
    f()
    local after = collectgarbage("count")
    print(("%s: %.1f KB"):format(label, after - before))
end

measure("array of 100k", function()
    local t = {}
    for i = 1, 100000 do t[i] = i end
end)
```

테이블 1만 개와 클래스 1만 개의 차이를 직접 비교해 보면 클래스 인스턴스의 오버헤드(메타테이블 슬롯)가 보입니다.

## 13.6 GC 친화 코드 팁

1. **불필요한 새 테이블/문자열 생성 금지** — 핫 루프에서 누적.
2. **테이블 재사용** — 같은 테이블을 비우고 다시 채움.
3. **문자열 연결은 `table.concat`** — `..` 의 반복은 새 문자열을 매번 만듦.

```lua
-- 나쁜 예
local s = ""
for i = 1, 10000 do s = s .. i .. "," end

-- 좋은 예
local parts = {}
for i = 1, 10000 do parts[#parts+1] = tostring(i) end
local s = table.concat(parts, ",")
```

4. **string.format 대신 concat** — 단순한 경우엔 format 보다 concat이 빠름.
5. **고차 함수 안 익명 함수의 매번 생성** 피하기 (6.11).

---

# 14. I/O · OS · 비트 연산

이 장은 표준 라이브러리에서 자주 쓰는 부분의 패턴 모음입니다.

## 14.1 파일 읽기

```lua
local f = assert(io.open("notes.txt", "r"))
local text = f:read("a")     -- "a" = 전체 (5.3+), "*a" (5.1)
f:close()
```

라인 단위로 읽기:

```lua
for line in io.lines("notes.txt") do
    print(line)
end
```

특정 길이:

```lua
local f = io.open("data.bin", "rb")
local header = f:read(16)    -- 16 바이트
local body   = f:read("a")
f:close()
```

`f:read` 의 인자:

- `"l"` — 한 줄(개행 제외, 5.3+ 기본)
- `"L"` — 한 줄(개행 포함)
- `"a"` — 전체
- `"n"` — 다음 숫자
- 정수 — 바이트 수

## 14.2 파일 쓰기

```lua
local f = assert(io.open("out.txt", "w"))
f:write("hello\n")
f:write(string.format("count=%d\n", 42))
f:close()
```

추가 모드:

```lua
local f = io.open("log.txt", "a")
f:write(os.date(), " event\n")
f:close()
```

## 14.3 io.lines 와 자원 관리

`io.lines` 는 파일을 자동으로 닫아 줍니다 — 끝까지 다 돌면. 중간에 `break` 하면 닫히지 않을 수 있으므로 5.4 에서는 다음과 같이 쓰세요.

```lua
do
    local f <close> = assert(io.open("log.txt", "r"))
    for line in f:lines() do
        if line:match("error") then break end
    end
end
```

## 14.4 표준 입출력

```lua
io.write("name? ")
local name = io.read("l")    -- 한 줄
io.write("hi, ", name, "\n")
```

`io.read("n")` 으로 숫자, 정수만 검사하려면 직접 검증.

## 14.5 os 라이브러리

```lua
print(os.time())                    -- epoch (s)
print(os.date())                    -- 현재 시각 문자열
print(os.date("%Y-%m-%d %H:%M:%S")) -- 형식 지정
print(os.date("*t"))                -- 테이블 (year, month, day, hour, ...)
print(os.clock())                   -- 프로세스 CPU 시간(s, 실수)
print(os.difftime(os.time(), 0))    -- 시간 차이

print(os.getenv("HOME"))
os.execute("ls -la")    -- 셸 명령 (보안 주의)
os.remove("temp.txt")
os.rename("a.txt", "b.txt")
print(os.tmpname())                 -- 임시 파일 경로
```

## 14.6 시간 측정 헬퍼

```lua
local function bench(label, f, n)
    n = n or 1
    collectgarbage(); collectgarbage()
    local t0 = os.clock()
    for _ = 1, n do f() end
    local t1 = os.clock()
    print(("%-30s %8.3f ms"):format(label, (t1 - t0) * 1000 / n))
end

bench("sort 1k random", function()
    local t = {}
    for i = 1, 1000 do t[i] = math.random() end
    table.sort(t)
end, 100)
```

알고리즘 가이드의 측정 도구도 참조 → [[Lua 알고리즘#2.2 시간 측정 헬퍼]].

## 14.7 비트 연산 (5.3+)

Lua 5.3 부터 비트 연산자가 언어에 들어갔습니다.

```lua
print(5 & 3)     -- 1   AND
print(5 | 3)     -- 7   OR
print(5 ~ 3)     -- 6   XOR
print(~5)        -- -6  NOT (정수 보수)
print(1 << 3)    -- 8   shift left
print(16 >> 2)   -- 4   shift right
```

5.1 / LuaJIT 은 `bit32` 또는 `bit` 라이브러리를 씁니다.

```lua
local bit = require "bit"           -- LuaJIT
print(bit.band(5, 3))    -- 1
print(bit.bor(5, 3))     -- 7
print(bit.bxor(5, 3))    -- 6
print(bit.bnot(5))
print(bit.lshift(1, 3))
```

## 14.8 비트 마스크 패턴

```lua
local FLAG_A = 1 << 0   -- 1
local FLAG_B = 1 << 1   -- 2
local FLAG_C = 1 << 2   -- 4

local set = FLAG_A | FLAG_C
print(set & FLAG_A ~= 0)    -- true
print(set & FLAG_B ~= 0)    -- false

set = set | FLAG_B          -- 추가
set = set & ~FLAG_A         -- 제거
```

색상, 권한, 게임 상태 비트맵에서 자주 씁니다.

## 14.9 바이너리 데이터 — string.pack / unpack

5.3+ 에서 구조체 바이너리를 다룰 수 있습니다.

```lua
local s = string.pack("i4i4f", 100, 200, 3.14)
print(#s)   -- 12

local a, b, c, _ = string.unpack("i4i4f", s)
print(a, b, c)   -- 100   200   3.140000104904175
```

포맷 문자:

| 코드 | 의미 |
|---|---|
| `b/B` | signed/unsigned 1바이트 |
| `h/H` | 2바이트 |
| `i/I` (n) | n바이트 정수 (i4 = 4바이트) |
| `l/L` | long |
| `j/J` | lua_Integer |
| `f/d` | float / double |
| `s` (n) | 길이 접두사 문자열 |
| `z` | null 종료 문자열 |
| `<` `>` `=` | little / big / native endian |
| `!` n | n 바이트 정렬 |

리틀 엔디언 강제:

```lua
local s = string.pack("<i4i4", 1, 256)
print(string.byte(s, 1, #s))
-- 1 0 0 0 0 1 0 0
```

게임 데이터 파일, 바이너리 프로토콜, PNG/PE 헤더 파싱에 강력합니다.

## 14.10 디렉터리 — 표준에 없는 것

표준 Lua는 디렉터리 순회를 못 합니다. 두 가지 길이 있습니다.

1. **LuaFileSystem** (`lfs`) 사용 — 사실상 표준.

```lua
local lfs = require "lfs"
for entry in lfs.dir(".") do
    print(entry, lfs.attributes(entry, "mode"))
end
```

2. **셸 명령으로 우회** (보안 주의).

```lua
local function listdir(path)
    local r = {}
    for name in io.popen("ls -1 " .. path):lines() do
        r[#r+1] = name
    end
    return r
end
```

여러 OS를 지원해야 한다면 `lfs` 를 luarocks 로 받으세요.

---

# 15. 디자인 패턴 카탈로그

GoF 패턴을 Lua의 메타테이블/클로저/다중 반환으로 다시 쓰면 다른 언어보다 짧고 명확해지는 경우가 많습니다. 이 장은 자주 쓰는 패턴 14가지를 동작 코드로 정리합니다.

5장의 `class` 헬퍼를 다시 가져와 시작합니다.

```lua
-- file: oop.lua
local function class(base)
    local cls = setmetatable({}, {
        __index = base,
        __call = function(c, ...)
            local self = setmetatable({}, c)
            if c.init then c.init(self, ...) end
            return self
        end,
    })
    cls.__index = cls
    cls.super = base
    return cls
end
return class
```

이 장의 모든 예제는 `local class = require "oop"` 로 시작한다고 가정합니다.

## 15.1 싱글톤 (Singleton)

`require` 의 캐시 덕에 모듈 자체가 싱글톤입니다.

```lua
-- file: registry.lua
local M = {items = {}}
function M.add(k, v) M.items[k] = v end
function M.get(k)    return M.items[k] end
return M
```

```lua
local R = require "registry"
R.add("user", "Alice")
print((require "registry").get("user"))   -- Alice  (같은 인스턴스)
```

명시적 싱글톤이 필요하면 클래스에 `instance()` 메서드를 둡니다.

```lua
local Logger = class()
local _instance

function Logger.instance()
    if not _instance then
        _instance = Logger()
        _instance.lines = {}
    end
    return _instance
end

function Logger:log(s)
    self.lines[#self.lines+1] = s
    print(s)
end

Logger.instance():log("hi")
```

## 15.2 팩토리 (Factory)

타입 분기를 한 곳에 모읍니다.

```lua
local Shape = class()
function Shape:area() error("abstract") end

local Circle = class(Shape)
function Circle:init(r) self.r = r end
function Circle:area() return math.pi * self.r * self.r end

local Square = class(Shape)
function Square:init(s) self.s = s end
function Square:area() return self.s * self.s end

local registry = {circle = Circle, square = Square}

local function make_shape(spec)
    local cls = registry[spec.kind] or error("unknown shape: " .. spec.kind)
    return cls(table.unpack(spec.args or {}))
end

local s1 = make_shape{kind="circle", args={3}}
local s2 = make_shape{kind="square", args={4}}
print(s1:area(), s2:area())
```

JSON/파일에서 들어오는 데이터를 객체로 풀어낼 때 거의 항상 이 모양입니다.

## 15.3 빌더 (Builder)

체이닝으로 복잡한 객체를 단계별로:

```lua
local QueryBuilder = class()

function QueryBuilder:init()
    self._table = nil
    self._where = {}
    self._fields = {"*"}
    self._limit = nil
end

function QueryBuilder:from(t) self._table = t; return self end
function QueryBuilder:select(...) self._fields = {...}; return self end
function QueryBuilder:where(cond)
    self._where[#self._where+1] = cond; return self
end
function QueryBuilder:limit(n) self._limit = n; return self end

function QueryBuilder:build()
    assert(self._table, "no table")
    local sql = ("SELECT %s FROM %s"):format(
        table.concat(self._fields, ", "), self._table)
    if #self._where > 0 then
        sql = sql .. " WHERE " .. table.concat(self._where, " AND ")
    end
    if self._limit then sql = sql .. " LIMIT " .. self._limit end
    return sql
end

local q = QueryBuilder()
    :from("users")
    :select("id", "name")
    :where("age > 20")
    :where("active = true")
    :limit(10)
    :build()

print(q)
-- SELECT id, name FROM users WHERE age > 20 AND active = true LIMIT 10
```

각 메서드가 `self` 를 반환하면 자연스러운 DSL 이 됩니다.

## 15.4 옵저버 (Observer)

발행-구독:

```lua
local Event = class()

function Event:init() self.listeners = {} end

function Event:on(fn)
    self.listeners[fn] = true
    return function() self.listeners[fn] = nil end   -- unsubscribe
end

function Event:emit(...)
    for fn in pairs(self.listeners) do fn(...) end
end

-- 사용
local clicked = Event()

local off = clicked:on(function(x, y) print("A:", x, y) end)
clicked:on(function(x, y) print("B:", x, y) end)

clicked:emit(10, 20)
-- A: 10  20
-- B: 10  20

off()                -- A 구독 해제
clicked:emit(30, 40) -- B: 30  40
```

여러 이벤트를 한 객체로 모은 dispatcher:

```lua
local Bus = class()
function Bus:init() self.events = {} end

function Bus:on(name, fn)
    local e = self.events[name] or Event()
    self.events[name] = e
    return e:on(fn)
end

function Bus:emit(name, ...)
    local e = self.events[name]
    if e then e:emit(...) end
end

local bus = Bus()
bus:on("login", function(u) print("login:", u) end)
bus:on("login", function(u) print("audit:", u) end)
bus:emit("login", "Alice")
```

자료구조 가이드에서 같은 패턴을 다른 각도로 보여줍니다 → [[Lua 자료구조#16.5 이벤트 디스패처 (관찰자 패턴)]].

## 15.5 전략 (Strategy)

알고리즘을 함수로 주입:

```lua
local Sorter = class()

function Sorter:init(cmp) self.cmp = cmp or function(a, b) return a < b end end

function Sorter:sort(t)
    local r = table.move(t, 1, #t, 1, {})
    table.sort(r, self.cmp)
    return r
end

local asc  = Sorter()
local desc = Sorter(function(a, b) return a > b end)
local byLen = Sorter(function(a, b) return #a < #b end)

print(table.concat(asc:sort({3,1,2}), ","))               -- 1,2,3
print(table.concat(desc:sort({3,1,2}), ","))              -- 3,2,1
print(table.concat(byLen:sort({"hi","x","abcd"}), ","))   -- x,hi,abcd
```

Lua는 함수가 일급이라 굳이 클래스로 감쌀 필요가 없을 때도 많습니다 — 그냥 비교 함수 자체가 전략입니다.

## 15.6 상태 (State)

오브젝트의 동작을 현재 상태에 따라 바꿉니다.

```lua
local TrafficLight = class()

local Red, Yellow, Green = {}, {}, {}

function Red:next(o)    o:set(Green)  end
function Green:next(o)  o:set(Yellow) end
function Yellow:next(o) o:set(Red)    end

function Red:color()    return "RED"    end
function Green:color()  return "GREEN"  end
function Yellow:color() return "YELLOW" end

function TrafficLight:init() self.state = Red end
function TrafficLight:set(s) self.state = s end
function TrafficLight:tick()  self.state:next(self) end
function TrafficLight:color() return self.state:color() end

local t = TrafficLight()
for _ = 1, 7 do
    print(t:color())
    t:tick()
end
-- RED, GREEN, YELLOW, RED, GREEN, YELLOW, RED
```

상태가 더 많아지면 표 기반 FSM 으로:

```lua
local function FSM(initial, transitions)
    return {
        state = initial,
        send = function(self, event)
            local t = transitions[self.state]
            if t and t[event] then self.state = t[event] end
        end,
    }
end

local m = FSM("idle", {
    idle    = {start = "running"},
    running = {pause = "paused", stop = "idle"},
    paused  = {start = "running", stop = "idle"},
})

m:send("start"); print(m.state)   -- running
m:send("pause"); print(m.state)   -- paused
m:send("stop");  print(m.state)   -- idle
```

## 15.7 명령 (Command)

작업을 객체로 감싸 큐에 넣고, undo/redo 도 가능:

```lua
local Cmd = class()
function Cmd:do_()   error("abstract") end
function Cmd:undo()  error("abstract") end

local AddCmd = class(Cmd)
function AddCmd:init(list, val) self.list, self.val = list, val end
function AddCmd:do_()  self.list[#self.list+1] = self.val end
function AddCmd:undo() self.list[#self.list] = nil end

local History = class()
function History:init() self.stack = {} end
function History:exec(cmd)
    cmd:do_()
    self.stack[#self.stack+1] = cmd
end
function History:undo()
    local c = table.remove(self.stack)
    if c then c:undo() end
end

local list = {}
local h = History()

h:exec(AddCmd(list, "a"))
h:exec(AddCmd(list, "b"))
h:exec(AddCmd(list, "c"))
print(table.concat(list, ","))   -- a,b,c

h:undo(); h:undo()
print(table.concat(list, ","))   -- a
```

에디터, 게임 로직, 트랜잭션에 흔합니다.

## 15.8 데코레이터 (Decorator)

함수를 감싸 행동을 추가:

```lua
local function logged(f, name)
    return function(...)
        print(("call %s(%s)"):format(name, table.concat({...}, ", ")))
        local res = f(...)
        print(("ret  %s -> %s"):format(name, tostring(res)))
        return res
    end
end

local function timed(f, name)
    return function(...)
        local t0 = os.clock()
        local res = f(...)
        print(("time %s: %.4f s"):format(name, os.clock() - t0))
        return res
    end
end

local function add(a, b) return a + b end

add = timed(logged(add, "add"), "add")
print(add(3, 4))
```

Python 데코레이터 같은 문법은 없지만, 효과는 같습니다.

객체 데코레이터:

```lua
local function withCache(svc)
    local cache = {}
    return setmetatable({}, {
        __index = function(_, k)
            local v = cache[k]
            if v == nil then
                v = svc[k]
                cache[k] = v
            end
            return v
        end,
    })
end
```

## 15.9 컴포지트 (Composite)

부모와 자식이 같은 인터페이스:

```lua
local Node = class()
function Node:init(name) self.name, self.children = name, {} end
function Node:add(c)     self.children[#self.children+1] = c end

function Node:print(indent)
    indent = indent or ""
    print(indent .. self.name)
    for _, c in ipairs(self.children) do c:print(indent .. "  ") end
end

function Node:size()
    local n = 1
    for _, c in ipairs(self.children) do n = n + c:size() end
    return n
end

local root = Node("root")
local a    = Node("a"); root:add(a)
local b    = Node("b"); root:add(b)
local a1   = Node("a.1"); a:add(a1)
local a2   = Node("a.2"); a:add(a2)

root:print()
print(root:size())   -- 5
```

UI 트리, 파일 시스템, AST 가 전부 컴포지트입니다.

## 15.10 어댑터 (Adapter)

기존 객체를 다른 인터페이스로 감쌉니다.

```lua
-- 기존: stack 인터페이스
local function newStack()
    local s, n = {}, 0
    return {
        push = function(v) n = n + 1; s[n] = v end,
        pop  = function() if n == 0 then return nil end
                          local v = s[n]; s[n] = nil; n = n - 1; return v end,
    }
end

-- 새 코드는 List 의 add/remove 를 기대
local function StackAsList(s)
    return {
        add    = function(v) s.push(v) end,
        remove = function() return s.pop() end,
    }
end

local L = StackAsList(newStack())
L.add(1); L.add(2); L.add(3)
print(L.remove(), L.remove(), L.remove())
```

## 15.11 프록시 (Proxy)

원본에 접근하기 전에 가로채기:

```lua
local function readonly(t)
    return setmetatable({}, {
        __index = t,
        __newindex = function() error("readonly") end,
        __metatable = false,
    })
end

local function logged(t)
    return setmetatable({}, {
        __index = function(_, k)
            print("get " .. tostring(k))
            return t[k]
        end,
        __newindex = function(_, k, v)
            print(("set %s = %s"):format(k, tostring(v)))
            t[k] = v
        end,
    })
end

local data = logged({})
data.a = 1
print(data.a)
-- set a = 1
-- get a
-- 1
```

3.8 의 readonly와 4.3 의 observed 가 같은 가족입니다.

## 15.12 파사드 (Facade)

복잡한 서브시스템 위에 한 줄 인터페이스:

```lua
local AudioFacade = class()
function AudioFacade:init()
    self.mixer = Mixer()
    self.dsp   = DSP()
    self.io    = AudioIO()
end

function AudioFacade:playFile(path, volume)
    local stream = self.io:open(path)
    local processed = self.dsp:apply(stream, "normalize")
    self.mixer:play(processed, volume or 1.0)
end
```

게임 엔진의 `Game.spawn(...)`, 데이터베이스 `db.exec(...)` 가 모두 파사드입니다.

## 15.13 메멘토 (Memento)

상태 스냅샷:

```lua
local Editor = class()
function Editor:init() self.text = "" end
function Editor:write(s) self.text = self.text .. s end
function Editor:save()   return self.text end
function Editor:restore(snapshot) self.text = snapshot end

local e = Editor()
e:write("hello")
local s = e:save()

e:write(" world")
print(e.text)        -- hello world

e:restore(s)
print(e.text)        -- hello
```

15.7 의 Command 의 undo와 결합하면 강력합니다.

## 15.14 인터프리터 (Interpreter)

작은 DSL 평가기:

```lua
-- 전위 표현식: {"+", 1, 2}
-- {"*", {"+", 1, 2}, 3}
local function eval(e)
    if type(e) == "number" then return e end
    local op, a, b = e[1], e[2], e[3]
    a = eval(a); b = eval(b)
    if op == "+" then return a + b end
    if op == "-" then return a - b end
    if op == "*" then return a * b end
    if op == "/" then return a / b end
    error("unknown op: " .. op)
end

print(eval({"*", {"+", 1, 2}, 3}))   -- 9
```

LÖVE2D 의 dialogue tree, 게임 스크립트, 설정 DSL 에서 자주 등장합니다. 큰 표현식을 다루려면 LPeg 로 파서를 만들고 이런 평가기로 실행합니다.

---

# 16. 함수형 패턴

함수형 스타일은 Lua의 클로저, 다중 반환, 메타테이블과 잘 맞습니다. 이 장은 6장의 도구를 더 큰 패턴으로 묶습니다.

## 16.1 컬렉션 함수 풀세트

6.7 에서 본 `map/filter/reduce` 외에 자주 쓰는 것들:

```lua
-- file: fp.lua
local M = {}

function M.map(t, f)
    local r = {}
    for i = 1, #t do r[i] = f(t[i], i) end
    return r
end

function M.filter(t, p)
    local r, n = {}, 0
    for i = 1, #t do
        if p(t[i], i) then n = n + 1; r[n] = t[i] end
    end
    return r
end

function M.reduce(t, f, init)
    local acc, i = init, 1
    if acc == nil then acc = t[1]; i = 2 end
    for j = i, #t do acc = f(acc, t[j]) end
    return acc
end

function M.any(t, p)
    for i = 1, #t do if p(t[i]) then return true end end
    return false
end

function M.all(t, p)
    for i = 1, #t do if not p(t[i]) then return false end end
    return true
end

function M.find(t, p)
    for i = 1, #t do if p(t[i]) then return t[i], i end end
end

function M.flatten(t, depth)
    depth = depth or 1
    local r = {}
    local function go(x, d)
        if type(x) == "table" and d > 0 then
            for i = 1, #x do go(x[i], d - 1) end
        else
            r[#r+1] = x
        end
    end
    for i = 1, #t do go(t[i], depth) end
    return r
end

function M.flatmap(t, f)
    local r = {}
    for i = 1, #t do
        local m = f(t[i], i)
        for j = 1, #m do r[#r+1] = m[j] end
    end
    return r
end

function M.groupby(t, key)
    local g = {}
    for i = 1, #t do
        local k = key(t[i])
        g[k] = g[k] or {}
        g[k][#g[k]+1] = t[i]
    end
    return g
end

function M.unique(t)
    local seen, r = {}, {}
    for i = 1, #t do
        if not seen[t[i]] then seen[t[i]] = true; r[#r+1] = t[i] end
    end
    return r
end

function M.zip(a, b)
    local n = math.min(#a, #b)
    local r = {}
    for i = 1, n do r[i] = {a[i], b[i]} end
    return r
end

function M.sum(t)
    local s = 0
    for i = 1, #t do s = s + t[i] end
    return s
end

return M
```

```lua
local _ = require "fp"

local nums = {1, 2, 3, 4, 5, 6}
print(_.sum(_.map(_.filter(nums, function(x) return x%2==0 end),
                  function(x) return x*x end)))
-- 4 + 16 + 36 = 56

local people = {{n="A",age=30},{n="B",age=20},{n="C",age=30}}
local byAge = _.groupby(people, function(p) return p.age end)
print(#byAge[30])   -- 2
```

## 16.2 lazy seq (지연 평가)

이터레이터 위에 lazy 변환 체인을 올립니다.

```lua
-- file: lazy.lua
local Lazy = {}
Lazy.__index = Lazy

function Lazy.from_gen(g) return setmetatable({_g = g}, Lazy) end

function Lazy.range(a, b, step)
    step = step or 1
    if not b then a, b = 1, a end
    local i = a - step
    return Lazy.from_gen(function()
        i = i + step
        if (step > 0 and i > b) or (step < 0 and i < b) then return nil end
        return i
    end)
end

function Lazy:map(f)
    local g = self._g
    return Lazy.from_gen(function()
        local v = g(); if v == nil then return nil end
        return f(v)
    end)
end

function Lazy:filter(p)
    local g = self._g
    return Lazy.from_gen(function()
        while true do
            local v = g(); if v == nil then return nil end
            if p(v) then return v end
        end
    end)
end

function Lazy:take(n)
    local g, i = self._g, 0
    return Lazy.from_gen(function()
        if i >= n then return nil end
        i = i + 1
        return g()
    end)
end

function Lazy:tolist()
    local r = {}
    while true do
        local v = self._g()
        if v == nil then return r end
        r[#r+1] = v
    end
end

function Lazy:foreach(f)
    while true do
        local v = self._g()
        if v == nil then return end
        f(v)
    end
end

return Lazy
```

```lua
local L = require "lazy"

-- 1..1e9 중 짝수의 제곱 첫 5 개
local r = L.range(1, 1e9)
    :filter(function(x) return x%2 == 0 end)
    :map(function(x) return x*x end)
    :take(5)
    :tolist()

print(table.concat(r, ","))   -- 4,16,36,64,100
```

`take(5)` 가 없으면 무한 루프지만, lazy 라서 take 이후에는 5번만 평가됩니다.

## 16.3 메모이제이션

6.5 의 단일 인자 메모이저를 다중 인자로 확장:

```lua
local function memo(f)
    local cache = {}
    return function(...)
        local n = select("#", ...)
        local node = cache
        for i = 1, n do
            local k = select(i, ...)
            node[k] = node[k] or {}
            node = node[k]
        end
        if node._v == nil then
            node._v = {f(...)}
        end
        return table.unpack(node._v)
    end
end

local function fib(n)
    if n < 2 then return n end
    return fib(n-1) + fib(n-2)
end

fib = memo(fib)   -- 자기 참조도 안전 (이름이 fib 그대로)
print(fib(80))    -- 즉시
```

약한 캐시 메모이저로 GC 친화적:

```lua
local function weakmemo(f)
    local cache = setmetatable({}, {__mode = "k"})
    return function(x)
        local v = cache[x]
        if v == nil then v = f(x); cache[x] = v end
        return v
    end
end
```

키가 테이블/객체일 때 의미가 있습니다.

## 16.4 트랜스듀서 — 합성 가능한 변환

map/filter 를 합성하면 중간 배열이 매번 만들어집니다. 트랜스듀서는 변환 자체를 합성해서 한 번만 순회합니다.

```lua
-- 트랜스듀서: reducer → 새 reducer
local function tmap(f)
    return function(reducer)
        return function(acc, x) return reducer(acc, f(x)) end
    end
end

local function tfilter(p)
    return function(reducer)
        return function(acc, x)
            if p(x) then return reducer(acc, x) end
            return acc
        end
    end
end

local function compose(...)
    local fs = {...}
    return function(x)
        for i = #fs, 1, -1 do x = fs[i](x) end
        return x
    end
end

local function transduce(xform, reducer, init, t)
    local r = xform(reducer)
    local acc = init
    for i = 1, #t do acc = r(acc, t[i]) end
    return acc
end

local xform = compose(
    tfilter(function(x) return x % 2 == 0 end),
    tmap(function(x) return x * x end)
)

local function pushReducer(acc, x) acc[#acc+1] = x; return acc end

local r = transduce(xform, pushReducer, {}, {1,2,3,4,5,6})
print(table.concat(r, ","))   -- 4,16,36
```

처음엔 어렵지만, 큰 컬렉션에서 의미 있는 차이를 줍니다.

## 16.5 partial / curry / flip

6.6 에서 `partial` 과 `curry` 를 봤습니다. 함수 인자 순서 뒤집기도 자주 씁니다.

```lua
local function flip(f)
    return function(a, b, ...) return f(b, a, ...) end
end

local function divide(a, b) return a / b end
local divBy = flip(divide)
print(divBy(2, 10))   -- 5
```

## 16.6 maybe / result 흉내

null 체이닝 흉내:

```lua
local function maybe(v)
    return setmetatable({v = v}, {
        __index = {
            map = function(self, f)
                if self.v == nil then return self end
                return maybe(f(self.v))
            end,
            unwrap = function(self, default)
                if self.v == nil then return default end
                return self.v
            end,
        },
    })
end

local r = maybe(user)
    :map(function(u) return u.address end)
    :map(function(a) return a.zip end)
    :unwrap("00000")
```

JS 의 `?.` 같은 효과. 작은 라이브러리지만 의외로 자주 씁니다.

## 16.7 함수형 vs 명령형 — 가이드

| 상황 | 권장 |
|---|---|
| 작은 컬렉션, 한 번 |  명령형 for 루프 |
| 변환 체인 길고 가독성 중요 | map/filter/reduce |
| 무한/큰 컬렉션 | lazy seq |
| 핫 루프 성능 중요 | 명령형, 인라인 |
| 정확성/테스트 용이 | 함수형 (사이드 이펙트 격리) |

핫 루프에서는 함수형 헬퍼가 만든 클로저/테이블이 GC 비용을 만들 수 있습니다. 13장의 측정 도구로 비교한 후 판단하세요.

---

# 17. 동시성과 비동기 패턴

8장의 코루틴 위에 실용 패턴을 얹습니다.

## 17.1 Future / Promise

```lua
local Future = {}
Future.__index = Future

function Future.new()
    return setmetatable({done=false, callbacks={}, value=nil}, Future)
end

function Future:resolve(v)
    if self.done then return end
    self.done, self.value = true, v
    for _, cb in ipairs(self.callbacks) do cb(v) end
end

function Future:on_done(cb)
    if self.done then cb(self.value)
    else self.callbacks[#self.callbacks+1] = cb end
end

function Future:await()
    if self.done then return self.value end
    local co = coroutine.running()
    self:on_done(function(v) coroutine.resume(co, v) end)
    return coroutine.yield()
end

-- 사용
local sched = require "sched"

local f = Future.new()

sched.spawn(function()
    print("waiting")
    local v = f:await()
    print("got", v)
end)

sched.spawn(function()
    coroutine.yield()  -- 한 번 양보
    f:resolve(42)
end)

sched.run()
-- waiting
-- got   42
```

`await` 가 코루틴 안에 있을 때만 동작합니다. 메인 코루틴에서는 yield 가 불가능하므로 (8.10) 스케줄러와 함께 써야 합니다.

## 17.2 액터 (Actor)

각 액터는 자기 메일박스를 가진 코루틴입니다.

```lua
local Actor = {}
Actor.__index = Actor

function Actor.new(behavior)
    local self = setmetatable({mbox = {}, alive = true}, Actor)
    self.co = coroutine.create(function()
        while self.alive do
            if #self.mbox == 0 then coroutine.yield() end
            local msg = table.remove(self.mbox, 1)
            if msg then behavior(self, msg) end
        end
    end)
    return self
end

function Actor:send(msg)
    self.mbox[#self.mbox+1] = msg
end

function Actor:tick()
    if coroutine.status(self.co) ~= "dead" then
        coroutine.resume(self.co)
    end
end

function Actor:stop() self.alive = false end

-- 사용
local printer = Actor.new(function(self, msg)
    print("printer:", msg)
end)

local counter = Actor.new(function(self, msg)
    self.n = (self.n or 0) + 1
    if msg == "ask" then printer:send("count is " .. self.n) end
end)

counter:send("inc"); counter:send("inc"); counter:send("ask")

for _ = 1, 10 do
    counter:tick()
    printer:tick()
end
```

큰 게임에서 각 시스템(렌더, 입력, AI)을 액터로 분리하면 결합도가 떨어집니다.

## 17.3 채널 — 8.9 확장

버퍼드 채널:

```lua
local Channel = {}
Channel.__index = Channel

function Channel.new(cap)
    return setmetatable({queue={}, recvs={}, sends={}, cap=cap or math.huge}, Channel)
end

function Channel:send(v)
    if #self.recvs > 0 then
        local co = table.remove(self.recvs, 1)
        coroutine.resume(co, v)
        return
    end
    if #self.queue >= self.cap then
        self.sends[#self.sends+1] = {coroutine.running(), v}
        coroutine.yield()
        return
    end
    self.queue[#self.queue+1] = v
end

function Channel:recv()
    if #self.queue > 0 then
        local v = table.remove(self.queue, 1)
        if #self.sends > 0 then
            local s = table.remove(self.sends, 1)
            self.queue[#self.queue+1] = s[2]
            coroutine.resume(s[1])
        end
        return v
    end
    self.recvs[#self.recvs+1] = coroutine.running()
    return coroutine.yield()
end

return Channel
```

생산자/소비자/파이프라인을 깔끔하게 표현할 수 있습니다.

## 17.4 이벤트 루프 — 한 페이지 버전

```lua
-- file: loop.lua
local Loop = {}
local now = os.clock
local timers = {}     -- {due=, co=}
local ready = {}

function Loop.spawn(f, ...)
    local args = table.pack(...)
    local co = coroutine.create(function() f(table.unpack(args, 1, args.n)) end)
    ready[#ready+1] = co
end

function Loop.sleep(s)
    local co = coroutine.running()
    timers[#timers+1] = {due = now() + s, co = co}
    coroutine.yield()
end

local function dueTimers(t)
    local fired, rest = {}, {}
    for _, ti in ipairs(timers) do
        if t >= ti.due then fired[#fired+1] = ti.co
        else rest[#rest+1] = ti end
    end
    timers = rest
    return fired
end

function Loop.run()
    while #ready > 0 or #timers > 0 do
        for _, co in ipairs(dueTimers(now())) do ready[#ready+1] = co end
        local current = ready
        ready = {}
        for _, co in ipairs(current) do
            local ok, err = coroutine.resume(co)
            if not ok then io.stderr:write(err, "\n") end
            if coroutine.status(co) == "suspended" then
                -- timer 가 다시 ready 에 넣어줄 것
            end
        end
        if #ready == 0 and #timers > 0 then
            -- 가장 가까운 타이머까지 (실제 IO 루프라면 select 호출)
            local nearest = math.huge
            for _, ti in ipairs(timers) do
                if ti.due < nearest then nearest = ti.due end
            end
            local wait = nearest - now()
            if wait > 0 then os.execute("sleep " .. wait) end
        end
    end
end

return Loop
```

진짜 IO와 결합하려면 `socket.select` (LuaSocket) 같은 시스템 호출이 필요하지만, 구조 자체는 이게 거의 전부입니다.

## 17.5 race / all 컴비네이터

```lua
local function all(futures)
    local out = Future.new()
    local results, left = {}, #futures
    for i, f in ipairs(futures) do
        f:on_done(function(v)
            results[i] = v
            left = left - 1
            if left == 0 then out:resolve(results) end
        end)
    end
    return out
end

local function race(futures)
    local out = Future.new()
    for _, f in ipairs(futures) do
        f:on_done(function(v) out:resolve(v) end)
    end
    return out
end
```

여러 비동기 작업의 결과를 동시에 기다리거나, 가장 먼저 끝나는 것만 받을 수 있습니다.

## 17.6 동시성 함정

| 함정 | 해결 |
|---|---|
| 메인 코루틴에서 yield | 항상 spawn 안에서만 |
| 코루틴 내부 에러 누락 | xpcall 로 감싸기 |
| 큐가 무한히 쌓임 | bounded channel, 백프레셔 |
| 데드락 (서로 await) | 디펜던시 그래프 정리, timeout |
| 코루틴 누수 | run() 종료 시 status 확인 |

---

# 18. 테스트와 품질

표준 Lua에는 테스트 프레임워크가 없습니다. 대신 100줄짜리 미니 러너로 시작합니다.

## 18.1 미니 어서션

```lua
-- file: test.lua
local M = {}
local pass, fail = 0, 0
local current = "<anon>"

local function fmt(v)
    if type(v) == "table" then
        local parts = {}
        for k, x in pairs(v) do parts[#parts+1] = tostring(k).."="..tostring(x) end
        return "{" .. table.concat(parts, ", ") .. "}"
    end
    return tostring(v)
end

local function deepequal(a, b)
    if a == b then return true end
    if type(a) ~= "table" or type(b) ~= "table" then return false end
    for k, v in pairs(a) do if not deepequal(v, b[k]) then return false end end
    for k in pairs(b) do if a[k] == nil then return false end end
    return true
end

function M.assertEq(a, b, msg)
    if a ~= b then
        error(("[%s] %s\n  expected %s\n  got      %s")
            :format(current, msg or "", fmt(b), fmt(a)), 2)
    end
end

function M.assertDeepEq(a, b, msg)
    if not deepequal(a, b) then
        error(("[%s] %s\n  expected %s\n  got      %s")
            :format(current, msg or "", fmt(b), fmt(a)), 2)
    end
end

function M.assertTrue(v, msg)
    if not v then error(("[%s] %s"):format(current, msg or "expected truthy"), 2) end
end

function M.assertError(f, ...)
    local ok = pcall(f, ...)
    if ok then error(("[%s] expected error"):format(current), 2) end
end

function M.test(name, fn)
    current = name
    local ok, err = xpcall(fn, debug.traceback)
    if ok then
        pass = pass + 1
        print("\27[32mPASS\27[0m " .. name)
    else
        fail = fail + 1
        print("\27[31mFAIL\27[0m " .. name .. "\n" .. err)
    end
end

function M.summary()
    print(("\n%d passed, %d failed"):format(pass, fail))
    return fail == 0
end

return M
```

```lua
-- file: spec.lua
local T = require "test"

T.test("basic math", function()
    T.assertEq(1 + 1, 2)
end)

T.test("deep eq", function()
    T.assertDeepEq({a=1, b={2,3}}, {a=1, b={2,3}})
end)

T.test("error expected", function()
    T.assertError(function() error("boom") end)
end)

if not T.summary() then os.exit(1) end
```

`lua spec.lua` — 완전한 미니 러너입니다.

## 18.2 mock 과 spy

```lua
local function spy(f)
    local s = {calls = {}}
    s.fn = function(...)
        s.calls[#s.calls+1] = table.pack(...)
        if f then return f(...) end
    end
    return s
end

local function mock(t, name, replacement)
    local original = t[name]
    t[name] = replacement
    return function() t[name] = original end   -- 복원
end

-- 사용
local logger = {info = function() end}
local s = spy(logger.info)
local restore = mock(logger, "info", s.fn)

logger.info("hi")
logger.info("there")

print(#s.calls)            -- 2
print(s.calls[1][1])       -- hi
restore()
```

테스트가 끝나면 반드시 `restore()` — `<close>` 와 결합하면 더 안전합니다.

## 18.3 속성 기반 테스트 (mini)

```lua
local function forall(gen, prop, n)
    n = n or 100
    for i = 1, n do
        local x = gen()
        if not prop(x) then
            error(("property failed for %s"):format(tostring(x)), 2)
        end
    end
end

local function intGen() return math.random(-1000, 1000) end

forall(intGen, function(x) return x * 2 == x + x end)
forall(intGen, function(x) return math.abs(x) >= 0 end)
```

엣지 케이스(0, MIN/MAX, 음수)를 의도적으로 생성하는 generator 를 늘리면 강력해집니다.

## 18.4 setUp / tearDown

```lua
local T = require "test"

local function describe(name, fn)
    fn({
        before = function(f)
            T.test(name .. " > setup ok", function() f() end)
        end,
        it = function(case, body)
            T.test(name .. " > " .. case, body)
        end,
    })
end

describe("Counter", function(this)
    local c
    this.before(function() c = {n=0, inc = function(s) s.n = s.n + 1 end} end)
    this.it("starts at 0", function() T.assertEq(c.n, 0) end)
    this.it("increments", function() c:inc(); T.assertEq(c.n, 1) end)
end)
```

매 it 마다 setup이 다시 도는 형태는 직접 만들면 됩니다(busted 비슷).

## 18.5 테스트 가능한 코드

- 사이드 이펙트(파일, 시간, 랜덤)는 인자로 받기.
- 전역 상태 최소화 → 모듈 레벨 변수보다 클래스/팩토리.
- `os.time` 등 시간 의존을 주입해서 테스트에서 고정.

```lua
local function clock() return os.time() end

local function newCache(max_age, now_fn)
    now_fn = now_fn or clock
    local t = {}
    return {
        set = function(k, v) t[k] = {v=v, at=now_fn()} end,
        get = function(k)
            local e = t[k]
            if not e then return nil end
            if now_fn() - e.at > max_age then t[k] = nil; return nil end
            return e.v
        end,
    }
end

-- 테스트에서:
local fakeNow = 1000
local c = newCache(60, function() return fakeNow end)
c.set("x", 1); fakeNow = fakeNow + 30; assert(c.get("x") == 1)
fakeNow = fakeNow + 60; assert(c.get("x") == nil)
```

---

# 19. LuaJIT과 최적화

LuaJIT 은 Mike Pall 이 만든 매우 빠른 Lua 5.1 호환 구현체입니다. 게임/임베디드/네트워크 미들웨어에서 자주 만납니다.

## 19.1 LuaJIT 와 Lua 5.x 의 차이

| 항목 | LuaJIT | Lua 5.4 |
|---|---|---|
| 기반 | 5.1 + 일부 5.2 | 5.4 |
| 정수/실수 분리 | 없음 (모두 double) | 있음 |
| `<close>`, `goto` | goto만 | 둘 다 |
| `bit` 라이브러리 | 내장 (`require"bit"`) | 비트 연산자 |
| FFI | 강력함 (`ffi.cdef` 등) | 없음 |
| 비트 연산 | bit.band 등 | `&`, `|` 연산자 |
| 성능 | JIT, 매우 빠름 | 인터프리터 |

이식성이 중요하다면 5.1 호환 부분만 쓰세요.

## 19.2 FFI — C 호출

```lua
local ffi = require "ffi"

ffi.cdef[[
    int printf(const char *fmt, ...);
    typedef struct { double x, y; } Point;
]]

ffi.C.printf("hello %d\n", ffi.cast("int", 42))

local p = ffi.new("Point", 3, 4)
print(p.x, p.y)
```

Lua 객체보다 가볍고, 외부 라이브러리 호출 비용이 거의 없습니다. 단점:

- 메모리 안전성 책임이 사용자에 있음.
- 표준 Lua에서는 동작 안 함.

## 19.3 JIT 성능 팁

1. **트레이스 컴파일러는 루프를 좋아합니다** — 짧고 빈번한 루프 안에 다양한 분기를 두지 않기.
2. **타입 안정** — 한 변수의 타입을 바꾸지 말기. 정수와 실수를 섞지 말기.
3. **NYI(Not Yet Implemented) 함수 피하기** — `pairs`, `ipairs`, `string.format`, `select`, 코루틴 yield 등 일부는 트레이스 중단을 일으킵니다.
4. **테이블 모양(shape) 일관성** — 같은 클래스 인스턴스는 같은 키 집합을 갖게.
5. **ffi 구조체 활용** — 작은 데이터(파티클, 벡터)는 ffi struct 가 훨씬 빠름.

## 19.4 인라인 캐시와 일관성

```lua
-- 좋은 모양: 모든 인스턴스가 같은 키를 같은 순서로 가짐
local Vec = class()
function Vec:init(x, y) self.x = x; self.y = y end

-- 나쁜 모양: 어떤 건 z 가 있고 어떤 건 없음 → 폴리모픽 → 슬로우
function Vec:init(x, y, z)
    self.x, self.y = x, y
    if z then self.z = z end
end
```

JIT 은 같은 모양의 객체가 반복되는 곳에서 가장 빠릅니다. 그래서 클래스 init 에서 모든 필드를 초기화하는 패턴이 권장됩니다(필요하면 nil 로라도).

## 19.5 데이터 지향 설계

게임에서 흔한 변환: AoS → SoA.

```lua
-- AoS (Array of Structs): 객체별 데이터
local entities = {}
for i = 1, 1000 do entities[i] = {x=0, y=0, hp=100} end

-- SoA (Struct of Arrays): 필드별 배열
local xs, ys, hps = {}, {}, {}
for i = 1, 1000 do xs[i], ys[i], hps[i] = 0, 0, 100 end

-- 갱신 루프
for i = 1, 1000 do xs[i] = xs[i] + 1 end
```

캐시 친화성이 좋고 JIT 최적화도 더 잘됩니다. ffi 와 결합하면 한층 더.

## 19.6 측정 없이 최적화 금지

19.3 의 모든 조언은 의심하면서 받으세요. **실제 워크로드를 측정**한 뒤 핫스팟을 찾고, 그 부분만 최적화합니다. LuaJIT 에는 `jit.dumpoff`, `jit.v` 같은 진단 도구가 있고, `--jit-prof` 옵션을 쓸 수 있습니다.

```bash
luajit -jp myapp.lua
```

---

# 20. 부록

## 20.1 Lua 버전별 변경 요약

### 5.1 → 5.2

- `_ENV` 환경 도입 (이전엔 `setfenv`/`getfenv`)
- `goto` 와 `::label::`
- `__pairs` 메타메서드
- `bit32` 라이브러리 (5.3 에서 deprecated)

### 5.2 → 5.3

- 정수 서브타입 (`math.type`)
- 비트 연산자 `&`, `|`, `~`, `<<`, `>>`
- `//` 정수 나눗셈
- `string.pack`, `unpack`, `packsize`
- `utf8` 라이브러리

### 5.3 → 5.4

- generational GC 모드
- `<const>` 와 `<close>` 변수 어노테이션
- 사용자 정의 warn 함수 (`warn`, `os.warn`)
- 정수 for 루프의 오버플로우 의미 명확화
- `string.format("%s", v)` 가 `__tostring` 호출

## 20.2 자주 쓰는 외부 라이브러리

| 이름 | 용도 |
|---|---|
| LuaSocket | TCP/UDP, HTTP 1.0 |
| LuaSec | TLS |
| LuaFileSystem (lfs) | 디렉터리 순회, attr |
| LPeg | PEG 파서 콤비네이터 |
| dkjson, cjson | JSON |
| busted | 테스트 |
| penlight | 배터리 포함 유틸 |
| inspect | 테이블 pretty-print |
| middleclass / 30log | 클래스 라이브러리 |
| moonscript / fennel | Lua VM 위 다른 언어 |
| LÖVE2D | 2D 게임 프레임워크 |
| Defold, Roblox | 임베드 환경 |

설치는 `luarocks install <name>` 가 표준.

## 20.3 표준 라이브러리 한 페이지 정리

```lua
-- 문자열
string.byte, char, dump, find, format, gmatch, gsub, len, lower, upper,
match, rep, reverse, sub, pack, unpack, packsize

-- 테이블
table.concat, insert, move, pack, unpack, remove, sort

-- 수학
math.abs, ceil, floor, sqrt, pow, exp, log, sin, cos, tan, asin, acos,
atan, max, min, modf, fmod, random, randomseed, pi, huge, maxinteger,
mininteger, type, tointeger

-- io
io.open, lines, read, write, close, stderr, stdout, stdin, tmpfile

-- os
os.time, date, clock, difftime, getenv, execute, remove, rename,
tmpname, exit

-- coroutine
coroutine.create, resume, yield, wrap, status, running, isyieldable, close

-- string lib (bit/utf8)
utf8.char, codepoint, codes, len, offset, charpattern

-- 환경 / 반사
load, loadfile, dofile, require, pcall, xpcall, error, assert, select,
type, tonumber, tostring, ipairs, pairs, next, rawget, rawset, rawequal,
rawlen, setmetatable, getmetatable, collectgarbage

-- debug
debug.traceback, getinfo, getlocal, setlocal, getupvalue, setupvalue,
upvaluejoin, sethook, gethook
```

## 20.4 책에서 쓴 헬퍼 모음

```lua
-- file: helpers.lua
local M = {}

function M.dump(v, indent)
    indent = indent or ""
    if type(v) ~= "table" then io.write(tostring(v)); return end
    io.write("{\n")
    for k, val in pairs(v) do
        io.write(indent .. "  ", tostring(k), " = ")
        M.dump(val, indent .. "  ")
        io.write(",\n")
    end
    io.write(indent .. "}")
end

function M.p(...)
    local n = select("#", ...)
    for i = 1, n do
        M.dump((select(i, ...)))
        io.write(i < n and "\t" or "\n")
    end
end

function M.deepcopy(o, seen)
    if type(o) ~= "table" then return o end
    seen = seen or {}
    if seen[o] then return seen[o] end
    local r = {}
    seen[o] = r
    for k, v in pairs(o) do r[M.deepcopy(k, seen)] = M.deepcopy(v, seen) end
    return setmetatable(r, getmetatable(o))
end

function M.deepequal(a, b)
    if a == b then return true end
    if type(a) ~= "table" or type(b) ~= "table" then return false end
    for k, v in pairs(a) do if not M.deepequal(v, b[k]) then return false end end
    for k in pairs(b) do if a[k] == nil then return false end end
    return true
end

function M.class(base)
    local cls = setmetatable({}, {
        __index = base,
        __call = function(c, ...)
            local self = setmetatable({}, c)
            if c.init then c.init(self, ...) end
            return self
        end,
    })
    cls.__index = cls
    cls.super = base
    return cls
end

function M.bench(label, f, n)
    n = n or 1
    collectgarbage(); collectgarbage()
    local t0 = os.clock()
    for _ = 1, n do f() end
    local t1 = os.clock()
    print(("%-30s %8.3f ms"):format(label, (t1 - t0) * 1000 / n))
end

return M
```

## 20.5 학습 로드맵

이 책을 읽고 나서 가는 길:

1. **본인 미니 라이브러리 만들기** — `class()`, 이벤트 버스, 메모이저를 자기 스타일로.
2. **인터프리터 한 번 만들기** — 산술 표현식 → 명령형 언어 → 작은 함수형 언어. 파서는 LPeg 추천.
3. **LÖVE2D 로 게임 한 번** — Lua가 게임에서 어떻게 다뤄지는지 체감.
4. **Lua 매뉴얼 정독** — 본 가이드의 모든 챕터가 매뉴얼에 한 줄씩 들어 있습니다.
5. **C 임베딩** — `lua_State` 와 스택을 직접 만지면 메타테이블의 진짜 모습이 보입니다.

## 20.6 관련 문서

- [[Lua 기초]] — 기초 문법집 (이 책의 출발점)
- [[Lua 자료구조]] — 배열, 연결 리스트, 트리, 해시, 그래프, 트라이, 유니온 파인드
- [[Lua 알고리즘]] — 정렬, 탐색, DP, 그래프, 문자열 알고리즘, 복잡도 분석
- [[Lua Tetris]] — Lua 응용 예제

## 20.7 더 읽을 거리 (오프라인 우선)

- *Programming in Lua, 4th ed.* — Roberto Ierusalimschy. 언어를 만든 사람의 책.
- *Lua 5.4 Reference Manual* — `lua.org/manual/5.4/`. 짧고 정확합니다.
- *Lua Performance Tips* — Mike Pall. LuaJIT 의 베스트 프랙티스.
- *Lua-users wiki* — 패턴/관용구의 보고.

## 20.8 마치며

Lua는 "작은 코어 + 큰 메타테이블" 의 언어입니다. 처음에는 "이렇게 작다고?" 싶다가도, 메타테이블과 코루틴을 익히고 나면 더 큰 언어가 굳이 필요 없어집니다.

이 책은 그 두 도구의 사용법을 정리한 책일 뿐입니다. 실제로 강력한 코드는 여기에 적힌 패턴을 외워서가 아니라, **자기 문제에 맞춰 패턴을 변형**하면서 나옵니다. 모든 예제를 한 번 직접 입력하고, 한 번씩 깨뜨려 보세요. 그게 가장 빠른 길입니다.

---

*문서 끝.*
