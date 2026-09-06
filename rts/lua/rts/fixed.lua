-- 16.16 고정소수점 · 정수 기하 · 거리 척도 — SPEC §1, §2.
--
--    여기 있는 함수 대부분은 한 줄이면 끝난다. 그런데도 이렇게 쪼개 놓은 이유는
--    루아 5.1 과 타입스크립트 때문이다. 두 언어에서 정수는 배정밀도 부동소수점
--    (가수 53비트)에 얹혀 있고, 자바스크립트의 >> 는 32비트로 잘린다. 그래서
--    이 모듈은
--      · 시프트를 쓰지 않고 (floordiv 로만)
--      · 곱셈 중간값이 2^53 을 넘지 않게 쪼개서
--      · 비트 연산자 대신 산술로
--    계산한다. 루아 5.1 표준에는 비트 연산자가 아예 없다(SPEC §1.1) — LuaJIT 의
--    bit 모듈은 여기서 쓰지 않는다.
--
--    이 파일은 다른 모듈을 하나도 참조하지 않는다. 나머지 전부가 여기에 기댄다.

local M = {}

local floor = math.floor

M.FP_BITS = 16
M.FP_ONE = 65536
M.FP_HALF = 32768
M.FP_DIAG = 46341                    -- 1/√2 의 16.16 반올림 (46340.950…)
M.FP_SQRT2M1 = 27146                 -- √2−1 의 16.16 반올림 (27145.951…)

local FP_ONE = 65536
local FP_HALF = 32768

M.D_STRAIGHT = 10
M.D_DIAG = 14
local D_STRAIGHT = 10
local D_DIAG = 14

-- SPEC §2.7 — 화면 좌표이므로 y 는 아래로 증가한다. 0-기반 배열이다.
M.DX = {[0] = 0, 1, 1, 1, 0, -1, -1, -1}
M.DY = {[0] = -1, -1, 0, 1, 1, 1, 0, -1}
M.DNAME = {[0] = 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}
M.DCOST = {[0] = D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG,
                 D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG}

-- ── SPEC §1 정수 연산 규약 ──────────────────────────────────────────────────

--- 파이썬 // 와 같은 -무한대 방향 내림.
--
--    루아의 수는 배정밀도 부동소수라 a/b 가 정확한 몫의 바로 아래·위로 흔들릴 수
--    있다. 그래서 나머지를 되계산해 한 칸 보정한다 — 값이 2^53 안에 있는 한
--    (SPEC §1 의 전제) 이 보정으로 정확해진다. 보통은 한 번도 돌지 않는다.
local function floordiv(a, b)
    local q = floor(a / b)
    local r = a - q * b
    if b > 0 then
        while r < 0 do q = q - 1; r = r + b end
        while r >= b do q = q + 1; r = r - b end
    else
        while r > 0 do q = q - 1; r = r + b end
        while r <= b do q = q + 1; r = r - b end
    end
    return q
end
M.floordiv = floordiv

--- 항상 0 <= 결과 < b.
local function fmod(a, b)
    return a - floordiv(a, b) * b
end
M.fmod = fmod

--- 산술 우시프트 = 2^k 로 내림 나눗셈. 음수에서도 내림이다.
function M.ashr(a, k)
    return floordiv(a, 2 ^ k)
end

function M.ashl(a, k)
    return a * 2 ^ k
end

-- ── SPEC §1.1 비트 연산의 산술 대체 ─────────────────────────────────────────

--- k번째 비트 — 시프트도 AND 도 쓰지 않는다.
local function bit(v, k)
    return fmod(floordiv(v, 2 ^ k), 2)
end
M.bit = bit

function M.setbit(v, k)
    return v + (1 - bit(v, k)) * 2 ^ k
end

function M.clrbit(v, k)
    return v - bit(v, k) * 2 ^ k
end

--- 바이트 두 개의 XOR — 여덟 번 도는 것이 전부다.
--
--    루아 5.1 에는 비트 연산자가 없다. LuaJIT 의 bit 모듈은 LÖVE 에서도 쓸 수
--    있지만 Lua 5.1 표준이 아니므로 쓰지 않기로 했다(SPEC §1.1).
local function xor8(x, y)
    local r = 0
    local p = 1
    for _ = 1, 8 do
        if (x % 2) ~= (y % 2) then
            r = r + p
        end
        x = floor(x / 2)
        y = floor(y / 2)
        p = p * 2
    end
    return r
end
M.xor8 = xor8

--- 32비트 값의 하위 8비트에만 XOR — FNV-1a(SPEC §18.4)가 쓴다.
local function xor_low8(h, b)
    return h - h % 256 + xor8(h % 256, b)
end
M.xor_low8 = xor_low8

-- ── SPEC §2.1 변환 ──────────────────────────────────────────────────────────
function M.fp(n)
    return n * FP_ONE
end

function M.fp_floor(x)
    return floordiv(x, FP_ONE)
end

function M.fp_round(x)
    return floordiv(x + FP_HALF, FP_ONE)
end

function M.fp_frac(x)
    return fmod(x, FP_ONE)
end

-- ── SPEC §2.3 곱셈 (분할 곱) ────────────────────────────────────────────────

--- floor(a*b / 65536). a 를 상·하위로 쪼개 중간값을 2^53 아래로 붙든다.
--
--    a = ah·2^16 + al 이므로 a·b/2^16 = ah·b + al·b/2^16 이고, 첫 항이 정수라
--    바닥함수 밖으로 나온다 (SPEC 정리 2.1).
function M.fp_mul(a, b)
    local ah = floordiv(a, FP_ONE)
    local al = a - ah * FP_ONE
    return ah * b + floordiv(al * b, FP_ONE)
end

--- floor(a*65536 / b). b == 0 은 호출자의 버그이므로 그냥 터진다.
function M.fp_div(a, b)
    if b == 0 then
        error('fp_div: b == 0')
    end
    return floordiv(a * FP_ONE, b)
end

-- ── SPEC §2.5 정수 제곱근 ───────────────────────────────────────────────────

--- 뉴턴 반복. 초기값과 종료 조건까지 명세다 — 세 언어가 같은 횟수를 돈다.
local function isqrt(n)
    if n < 2 then
        return n
    end
    local x = n
    local y = floordiv(x + 1, 2)
    while y < x do
        x = y
        y = floordiv(x + floordiv(n, x), 2)
    end
    return x
end
M.isqrt = isqrt

--- 고정소수점 제곱근. x < 2^31 이므로 x*65536 < 2^47 — 안전하다.
function M.fp_sqrt(x)
    return isqrt(x * FP_ONE)
end

-- ── SPEC §2.6 거리 척도 ─────────────────────────────────────────────────────
local function mxmn(dx, dy)
    local ax = dx >= 0 and dx or -dx
    local ay = dy >= 0 and dy or -dy
    if ax >= ay then return ax, ay end
    return ay, ax
end

--- L1 (맨해튼) — 4방향 이동의 정확한 걸음 수.
function M.d1(dx, dy)
    return (dx >= 0 and dx or -dx) + (dy >= 0 and dy or -dy)
end

--- L∞ (체비셰프) — 8방향 이동의 정확한 걸음 수. 사거리 판정은 전부 이것.
function M.dinf(dx, dy)
    local mx = mxmn(dx, dy)
    return mx
end

--- 옥타일 8분의 3 근사. √2−1 = 0.41421 을 3/8 로 바꾼 도스식 값.
function M.d83(dx, dy)
    local mx, mn = mxmn(dx, dy)
    return mx + floor(3 * mn / 8)
end

--- 경로 비용 단위의 옥타일 거리. 직선 10, 대각 14 — A* 휴리스틱이 이것이다.
function M.doct(dx, dy)
    local mx, mn = mxmn(dx, dy)
    return D_STRAIGHT * mx + (D_DIAG - D_STRAIGHT) * mn
end

--- alpha-max-beta-min. 마지막 반올림(+32768)이 없으면 dab(1,0) = 0 이 된다.
--
--    거리 1 이 0 으로 나오면 사거리 판정과 타깃 선택이 통째로 무너진다.
--    골든 벡터를 처음 만들 때 오차 −100 % 로 드러난 자리다(SPEC §2.6).
function M.dab(dx, dy)
    local mx, mn = mxmn(dx, dy)
    return floordiv(62943 * mx + 26072 * mn + FP_HALF, FP_ONE)
end

-- ── SPEC §2.7 8방향 판별 ────────────────────────────────────────────────────

--- 비교만으로 8방향을 고른다. 나눗셈도 삼각함수도 없다.
--
--    경계는 22.5°이고 tan 22.5° = √2−1 = 0.414214 다. 5/12 = 0.416667 로 바꾸면
--    경계각이 22.62° — 0.12° 넓어질 뿐이다. √2−1 의 연분수 수렴분수가
--    1/2, 2/5, 5/12, 12/29 … (펠 수의 비)이므로 5/12 는 우연이 아니다.
function M.atan8(dx, dy)
    if dx == 0 and dy == 0 then
        return 2                                 -- 규약: 정지 상태는 E 를 본다
    end
    local ax = dx >= 0 and dx or -dx
    local ay = dy >= 0 and dy or -dy
    local mx, mn
    if ax >= ay then mx, mn = ax, ay else mx, mn = ay, ax end
    local diag = 12 * mn > 5 * mx
    if ax >= ay then                             -- 동서가 주축
        if dx > 0 then
            if diag then
                return dy < 0 and 1 or 3
            end
            return 2
        end
        if diag then
            return dy < 0 and 7 or 5
        end
        return 6
    end
    if dy < 0 then                               -- 남북이 주축
        if diag then
            return dx > 0 and 1 or 7
        end
        return 0
    end
    if diag then
        return dx > 0 and 3 or 5
    end
    return 4
end

-- ── SPEC §20.1 CRC-16/CCITT-FALSE ───────────────────────────────────────────
-- 여기 있는 이유: tmap(맵 파일)과 replay(리플레이 꼬리)가 둘 다 쓰는데,
-- fixed 는 아무것도 참조하지 않으므로 순환이 생기지 않는다.

--- 16비트 XOR — 바이트 두 번으로 나눠 xor8 을 쓴다.
local function xor16(a, b)
    return xor8(floor(a / 256), floor(b / 256)) * 256 + xor8(a % 256, b % 256)
end
M.xor16 = xor16

-- ── SPEC §18.4 FNV-1a 32비트 ────────────────────────────────────────────────
M.FNV_OFFSET = 2166136261
M.FNV_PRIME = 16777619
local FNV_OFFSET = 2166136261
local FNV_PRIME = 16777619

--- 바이트 하나. XOR 은 하위 8비트만 바뀌므로 xor8 로 끝나고, 곱셈은 분할한다 —
--- hl * 16777619 < 2^40 이라 53비트 가수에 담긴다.
local function fnv1a_step(h, b)
    h = xor_low8(h, b)
    local hh = floor(h / 65536)
    local hl = h % 65536
    return (hl * FNV_PRIME + (hh * FNV_PRIME % 65536) * 65536) % 4294967296
end
M.fnv1a_step = fnv1a_step

--- data 는 바이트 문자열이거나 0-기반 바이트 배열({n=…})이다.
function M.fnv1a(data)
    local h = FNV_OFFSET
    if type(data) == 'string' then
        for i = 1, #data do
            h = fnv1a_step(h, data:byte(i))
        end
    else
        for i = 0, data.n - 1 do
            h = fnv1a_step(h, data[i])
        end
    end
    return h
end

--- poly 0x1021, init 0xFFFF, 반사 없음. crc16('123456789') == 0x29B1.
--
--    `c >= 32768` 이 "최상위 비트가 1"과 같다. 이것이 GF(2) 위의 다항식
--    나눗셈이며, 곱셈 2 가 다항식의 x 곱이다.
function M.crc16(data)
    local c = 65535
    local n, get
    if type(data) == 'string' then
        n = #data
        get = function(i) return data:byte(i + 1) end
    else
        n = data.n
        get = function(i) return data[i] end
    end
    for i = 0, n - 1 do
        c = xor16(c, get(i) * 256)
        for _ = 1, 8 do
            if c >= 32768 then
                c = xor16((c * 2) % 65536, 4129)
            else
                c = (c * 2) % 65536
            end
        end
    end
    return c
end

return M
