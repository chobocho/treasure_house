-- 저장·리플레이·압축 (SPEC §20).
--
--    리플레이는 **명령 로그**다. 상태는 한 바이트도 저장하지 않는다. 재생한다는
--    것은 같은 시드로 시뮬을 새로 만들어 같은 명령을 같은 틱에 먹이는 것이고,
--    결과가 같다는 증명은 hashes.txt 와의 대조가 대신한다. 1200틱 게임의
--    리플레이가 수백 바이트인 것과 상태 스냅샷이 틱당 4 KB 인 것을 20부가
--    나란히 놓는다.
--
--    비트 연산자는 쓰지 않는다(§1.1). LZSS 의 토큰도 곱셈과 나눗셈으로 접는다.

local F = require('rts.fixed')

local M = {}
local floor = math.floor

M.MAGIC = 'RTSR'
M.VERSION = 1
M.WINDOW, M.MIN_MATCH, M.MAX_MATCH = 4096, 3, 18
local WINDOW, MIN_MATCH, MAX_MATCH = 4096, 3, 18

-- 바이트열은 1-기반 문자 테이블로 모았다가 마지막에 이어 붙인다.
local function push(out, v)
    out[#out + 1] = string.char(v)
end

local function b2(out, v)
    v = v % 65536
    push(out, floor(v / 256))
    push(out, v % 256)
end

local function b4(out, v)
    v = v % 4294967296
    b2(out, floor(v / 65536))
    b2(out, v % 65536)
end

--- 0-기반 바이트 배열에서 읽는다. (값, 다음 위치) 를 돌려준다.
local function r2(b, i)
    return b[i] * 256 + b[i + 1], i + 2
end

local function r4(b, i)
    local hi, j = r2(b, i)
    local lo, k = r2(b, j)
    return hi * 65536 + lo, k
end

local function to_bytes(s)
    local b = {n = #s}
    for i = 1, #s do b[i - 1] = s:byte(i) end
    return b
end
M.to_bytes = to_bytes

local function from_bytes(b)
    local t = {}
    for i = 0, b.n - 1 do t[i + 1] = string.char(b[i]) end
    return table.concat(t)
end
M.from_bytes = from_bytes

-- ── SPEC §20.2 ──────────────────────────────────────────────────────────────

--- log 는 (틱, 명령 목록)의 0-기반 배열. 명령은 §18.1 의 여섯 칸이다.
function M.save(seed, players, ticks, log)
    local out = {}
    out[#out + 1] = M.MAGIC
    push(out, M.VERSION)
    b4(out, seed)
    push(out, players)
    b4(out, ticks)
    b2(out, log.n)
    -- 파이썬의 sorted(log) 와 같은 순서 — 틱이 먼저고, 같으면 명령 목록끼리
    -- 사전식으로 비교한다.
    local tmp = {}
    for k = 0, log.n - 1 do tmp[k + 1] = log[k] end
    table.sort(tmp, function(a, b_)
        if a[1] ~= b_[1] then return a[1] < b_[1] end
        local oa, ob = a[2], b_[2]
        local n = oa.n < ob.n and oa.n or ob.n
        for k = 0, n - 1 do
            for q = 0, 5 do
                if oa[k][q] ~= ob[k][q] then return oa[k][q] < ob[k][q] end
            end
        end
        return oa.n < ob.n
    end)
    for k = 1, #tmp do
        local t, orders = tmp[k][1], tmp[k][2]
        b4(out, t)
        push(out, orders.n)
        for q = 0, orders.n - 1 do
            local o = orders[q]
            push(out, o[0])                        -- p
            push(out, o[2])                        -- kind
            b2(out, o[1])                          -- issuer
            push(out, o[3])                        -- a
            push(out, o[4])                        -- b
            b2(out, o[5])                          -- c
        end
    end
    local blob = table.concat(out)
    local crc = F.crc16(blob)
    return blob .. string.char(floor(crc / 256)) .. string.char(crc % 256)
end

function M.load(blob)
    if blob:sub(1, 4) ~= M.MAGIC then
        error('리플레이 파일이 아니다')
    end
    local n = #blob
    local want = blob:byte(n - 1) * 256 + blob:byte(n)
    if F.crc16(blob:sub(1, n - 2)) ~= want then
        error('CRC 불일치 — 리플레이가 깨졌다')
    end
    local b = to_bytes(blob)
    local i = 5
    local seed
    seed, i = r4(b, i)
    local players = b[i]
    i = i + 1
    local ticks
    ticks, i = r4(b, i)
    local cnt
    cnt, i = r2(b, i)
    local log = {n = 0}
    for _ = 1, cnt do
        local t
        t, i = r4(b, i)
        local nord = b[i]
        i = i + 1
        local orders = {n = 0}
        for _ = 1, nord do
            local p = b[i]
            local kind = b[i + 1]
            local issuer, i2 = r2(b, i + 2)
            local a = b[i2]
            local bb = b[i2 + 1]
            local c
            c, i = r2(b, i2 + 2)
            orders[orders.n] = {[0] = p, issuer, kind, a, bb, c, n = 6}
            orders.n = orders.n + 1
        end
        log[log.n] = {t, orders}
        log.n = log.n + 1
    end
    return seed, players, ticks, log
end

-- ── SPEC §20.3 RLE ──────────────────────────────────────────────────────────

--- (개수, 값) 쌍. 개수는 1..255 — 넘으면 쌍을 나눈다.
function M.rle_encode(data)
    local out = {}
    local b = to_bytes(data)
    local i = 0
    while i < b.n do
        local v = b[i]
        local run = 1
        while i + run < b.n and b[i + run] == v and run < 255 do
            run = run + 1
        end
        push(out, run)
        push(out, v)
        i = i + run
    end
    return table.concat(out)
end

function M.rle_decode(data)
    local out = {}
    local b = to_bytes(data)
    local i = 0
    while i < b.n do
        for _ = 1, b[i] do
            push(out, b[i + 1])
        end
        i = i + 2
    end
    return table.concat(out)
end

-- ── SPEC §20.4 LZSS ─────────────────────────────────────────────────────────

--- 가장 긴 일치, 동점이면 가장 가까운 것. 탐욕적이다 — 최적 파싱은 안 한다.
--
--    O(창 × 최대일치) = 4096 × 18. 20부는 이 단순함의 대가를 실측으로 보인다.
local function match(b, pos)
    local best_len, best_off = 0, 0
    local start = pos - WINDOW
    if start < 0 then start = 0 end
    local limit = b.n - pos
    if limit > MAX_MATCH then limit = MAX_MATCH end
    for j = pos - 1, start, -1 do              -- 가까운 쪽부터 훑는다
        local k = 0
        while k < limit and b[j + k] == b[pos + k] do
            k = k + 1                          -- 겹치는 일치도 허용한다
        end
        if k > best_len then
            best_len, best_off = k, pos - j
            if best_len == limit then
                break
            end
        end
    end
    return best_len, best_off
end
M._match = match

function M.lzss_encode(data)
    local b = to_bytes(data)
    local out = {}
    local pos = 0
    while pos < b.n do
        local flag = 0
        local chunk = {}
        local bit = 1
        local used = 0
        while used < 8 and pos < b.n do
            local ln, off = match(b, pos)
            if ln >= MIN_MATCH then
                local o = off - 1                  -- 1..4096 → 0..4095
                push(chunk, floor(o / 16))
                push(chunk, (o % 16) * 16 + (ln - MIN_MATCH))
                pos = pos + ln
            else
                flag = flag + bit                  -- 비트 1 = 리터럴
                push(chunk, b[pos])
                pos = pos + 1
            end
            bit = bit * 2
            used = used + 1
        end
        push(out, flag)
        out[#out + 1] = table.concat(chunk)
    end
    return table.concat(out)
end

function M.lzss_decode(data)
    local b = to_bytes(data)
    local out = {n = 0}
    local i = 0
    while i < b.n do
        local flag = b[i]
        i = i + 1
        for _ = 1, 8 do
            if i >= b.n then break end
            if flag % 2 == 1 then
                out[out.n] = b[i]
                out.n = out.n + 1
                i = i + 1
            else
                local o = b[i] * 16 + floor(b[i + 1] / 16)
                local ln = b[i + 1] % 16 + MIN_MATCH
                i = i + 2
                local src = out.n - (o + 1)
                for j = 0, ln - 1 do
                    out[out.n] = out[src + j]      -- 한 바이트씩 — 겹침 허용
                    out.n = out.n + 1
                end
            end
            flag = floor(flag / 2)
        end
    end
    return from_bytes(out)
end

return M
