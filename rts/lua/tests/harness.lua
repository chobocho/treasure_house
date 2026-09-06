-- 세 언어 공통의 아주 작은 테스트 하네스 (파이썬 py/tests/harness.py 의 포팅).
--
--    프레임워크를 쓰지 않는 이유는 하나다. 같은 테스트를 파이썬·루아·타입스크립트로
--    돌려야 하는데, 프레임워크가 다르면 출력이 달라지고 출력이 달라지면 덱에 실을
--    로그도 달라진다. 그래서 '이름 · 기대 · 실제' 만 찍는다.
--
--    파이썬과 다른 점이 딱 하나 있다. 파이썬의 == 는 리스트를 값으로 비교하지만
--    루아의 == 는 테이블을 주소로 비교한다. 그래서 deep_eq 를 직접 쓴다.

local M = {}

local state = {ok = 0, bad = 0, name = '?'}
M.state = state

-- 골든 파일 위치 — 실행 위치가 lua/ 든 love 런타임이든 찾아지도록 후보를 훑는다.
local GOLDEN_CANDIDATES = {'../golden/', 'golden/', '../../golden/'}
local golden_dir = nil

local function find_golden_dir()
    if golden_dir then return golden_dir end
    for _, d in ipairs(GOLDEN_CANDIDATES) do
        local f = io.open(d .. 'prim.txt', 'rb')
        if f then f:close(); golden_dir = d; return d end
    end
    error('golden 디렉터리를 찾지 못했다')
end

-- ── 파이썬 %r 흉내 ──────────────────────────────────────────────────────────
-- 실패했을 때만 쓰이므로 완벽할 필요는 없다. 다만 두 suite 의 로그를 눈으로
-- 나란히 놓고 볼 수 있을 만큼은 닮아야 한다.
local function repr(v)
    local t = type(v)
    if t == 'nil' then
        return 'None'
    elseif t == 'boolean' then
        return v and 'True' or 'False'
    elseif t == 'number' then
        if v == math.floor(v) and v == v and v ~= math.huge and v ~= -math.huge then
            return string.format('%d', v)
        end
        return tostring(v)
    elseif t == 'string' then
        local s = v:gsub('\\', '\\\\'):gsub("'", "\\'"):gsub('\n', '\\n')
        return "'" .. s .. "'"
    elseif t == 'table' then
        local parts = {}
        local lo = (v[0] ~= nil or v.n ~= nil) and 0 or 1
        local hi
        if v.n ~= nil then hi = v.n - 1 + lo - lo else hi = nil end
        if v.n ~= nil then
            for i = lo, lo + v.n - 1 do parts[#parts + 1] = repr(v[i]) end
        else
            local i = lo
            while v[i] ~= nil do parts[#parts + 1] = repr(v[i]); i = i + 1 end
        end
        return '[' .. table.concat(parts, ', ') .. ']'
    end
    return tostring(v)
end
M.repr = repr

-- 값 비교 — 테이블은 재귀적으로 원소를 본다 (파이썬 리스트/튜플 == 와 같은 뜻).
local function deep_eq(a, b)
    if a == b then return true end
    if type(a) ~= 'table' or type(b) ~= 'table' then return false end
    -- 0-기반·1-기반·n 필드가 섞여 있어도 같은 키 집합이면 같다고 본다.
    for k, v in pairs(a) do
        if not deep_eq(v, b[k]) then return false end
    end
    for k, v in pairs(b) do
        if a[k] == nil and v ~= nil then return false end
    end
    return true
end
M.deep_eq = deep_eq

function M.title(name)
    state.name = name
    state.ok = 0
    state.bad = 0
    print('== ' .. name .. ' ==')
end

function M.check(what, got, want)
    local eq = deep_eq(got, want)
    if eq then
        state.ok = state.ok + 1
    else
        state.bad = state.bad + 1
        print('  실패 ' .. what)
        print('    기대 ' .. repr(want))
        print('    실제 ' .. repr(got))
    end
    return eq
end

function M.check_true(what, cond)
    return M.check(what, cond and true or false, true)
end

function M.note(fmt, ...)
    if select('#', ...) > 0 then
        print('  ' .. string.format(fmt, ...))
    else
        print('  ' .. fmt)
    end
end

function M.golden(name)
    local f = assert(io.open(find_golden_dir() .. name, 'rb'))
    local s = f:read('*a')
    f:close()
    return s
end

--- 저장소 최상위(SPEC.md 등)의 파일을 읽는다.
function M.root_file(name)
    local f = assert(io.open(find_golden_dir() .. '../' .. name, 'rb'))
    local s = f:read('*a')
    f:close()
    return s
end

function M.done()
    print(string.format('%s: 통과 %d · 실패 %d', state.name, state.ok, state.bad))
    return state.bad
end

-- ── 문자열 보조 (파이썬 str 메서드가 없어 자주 쓰는 것만) ───────────────────

--- 파이썬 text.split('\n') 과 같은 결과를 0-기반 배열로.
function M.lines(text)
    local out = {n = 0}
    local start = 1
    while true do
        local p = text:find('\n', start, true)
        if not p then
            out[out.n] = text:sub(start)
            out.n = out.n + 1
            break
        end
        out[out.n] = text:sub(start, p - 1)
        out.n = out.n + 1
        start = p + 1
    end
    return out
end

--- 공백 기준 분해 (파이썬 str.split() 과 같다) — 0-기반 배열.
function M.split(s)
    local out = {n = 0}
    for tok in s:gmatch('%S+') do
        out[out.n] = tok
        out.n = out.n + 1
    end
    return out
end

function M.strip(s)
    return (s:gsub('^%s+', ''):gsub('%s+$', ''))
end

--- 0-기반 배열에서 값 v 의 첫 위치. 없으면 error (파이썬 list.index 와 같다).
function M.index_of(arr, v)
    for i = 0, arr.n - 1 do
        if arr[i] == v then return i end
    end
    error('index_of: 값을 찾지 못했다 — ' .. tostring(v))
end

function M.ints(s)
    local out = {n = 0}
    for tok in s:gmatch('%-?%d+') do
        out[out.n] = tonumber(tok)
        out.n = out.n + 1
    end
    return out
end

return M
