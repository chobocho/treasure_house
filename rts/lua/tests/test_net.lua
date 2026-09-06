-- 락스텝 네트워크 — 지연·지터·디싱크 주입 (SPEC §19).

local H = require('tests.harness')
local C = require('rts.const')
local N = require('rts.net')
local SEL = require('rts.select')
local SIM = require('rts.sim')
local T = require('rts.tmap')
local F = require('rts.fixed')

H.title('net')

local function ord(p, issuer, kind, a, b, c)
    return {[0] = p, issuer, kind, a, b, c, n = 6}
end
local function lst(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

local O1 = ord(0, 256, SEL.MOVE, 3, 3, 0)
local O2 = ord(1, 512, SEL.MOVE, 4, 4, 0)

-- ── SPEC §19.2 모형 ─────────────────────────────────────────────────────────
local n = N.new(2)
H.check('기본 지연은 ORDER_DELAY', n.latency, C.ORDER_DELAY)
H.check('보낸 명령의 실행 틱은 보낼 때 정해진다', n:send(10, 0, O1), 12)
H.check('지터가 없으면 도착도 같은 틱', n:arrive_of(10, 0), 12)
n:flush(10, 0)
H.check('한 플레이어만 보냈으면 아직 준비되지 않았다', n:ready(12), false)
n:flush(10, 1)
H.check('둘 다 보냈으면 준비 완료', n:ready(12), true)
H.check('그 틱의 명령을 정렬해 돌려준다', n:take(12), lst(O1))
H.check('가져간 뒤에는 비어 있다', n:take(12), {n = 0})
H.check('명령이 없는 틱도 준비될 수 있다', n:ready(13), false)

local n2 = N.new(2)
n2:send(0, 1, O2)
n2:send(0, 0, O1)
n2:flush(0, 0)
n2:flush(0, 1)
H.check('정렬은 플레이어·핸들 순', n2:take(2), lst(O1, O2))
H.check('빈 턴도 보내야 한다 — 그래야 상대가 기다리지 않는다',
        N.new(2):ready(2), false)

-- ── SPEC §19.2 지터 ─────────────────────────────────────────────────────────
local n3 = N.new(2, C.ORDER_DELAY, 99, 2)
local seen = {}
for t = 0, 39 do
    n3:send(t, 0, ord(0, 256, SEL.MOVE, t % 8, 0, 0))
    n3:flush(t, 0)
    n3:flush(t, 1)
    seen[n3:arrive_of(t, 0) - (t + C.ORDER_DELAY)] = true
end
local delays = {n = 0}
for v = 0, 8 do
    if seen[v] then delays[delays.n] = v; delays.n = delays.n + 1 end
end
H.check('지터는 0..2 틱', delays, lst(0, 1, 2))
H.check('실행 틱은 지터와 무관하다', n3:exec_of(7, 0), 7 + C.ORDER_DELAY)
H.check_true('늦게 도착한 턴이 실제로 있다', n3.stalls > 0)
H.note('늦게 도착한 명령을 앞당겨 실행하는 경로는 존재하지 않는다')

local n4 = N.new(2, C.ORDER_DELAY, 5, 2)
n4:send(0, 0, O1)
n4:flush(0, 0)
n4:flush(0, 1)
local a1, a2 = n4:arrive_of(0, 0), n4:arrive_of(0, 1)
local late = a1 > a2 and a1 or a2
H.check('도착 전에는 준비되지 않는다',
        (late > 2) and n4:ready(2, late - 1) or false, false)
H.check('도착하면 준비된다', n4:ready(2, late), true)
H.check('기다린 뒤에도 명령은 그대로', n4:take(2), lst(O1))

-- ── 지터가 있어도 결과가 같아야 한다 ────────────────────────────────────────
local function play(jit_seed, jit_max)
    local m = T.load_text(H.golden('map_start.txt'))
    local s = SIM.new(m, 1, 2)
    s:setup_start()
    local net = N.new(2, C.ORDER_DELAY, jit_seed, jit_max)
    local sc = SIM.parse_script(H.golden('script.txt'))
    local hs = {n = 0}
    local wall = 0
    for t = 1, 60 do
        local os_ = s:script_orders(sc, t)
        for k = 0, os_.n - 1 do
            net:send(t, os_[k][0], os_[k])
        end
        for p = 0, 1 do net:flush(t, p) end
        local et = t + C.ORDER_DELAY
        local guard = 0
        while not net:ready(et, wall) and guard < 100 do   -- 늦으면 기다린다
            wall = wall + 1
            guard = guard + 1
        end
        hs[hs.n] = s:step(net:take(et))
        hs.n = hs.n + 1
        wall = wall + 1
    end
    return hs
end

local clean = play(0, 0)
local jit = play(1234, 2)
H.check('지터가 있어도 60틱의 해시열이 같다', clean, jit)
local uniq, nuniq = {}, 0
for k = 0, clean.n - 1 do
    if not uniq[clean[k]] then uniq[clean[k]] = true; nuniq = nuniq + 1 end
end
H.check_true('해시가 실제로 변한다', nuniq > 30)

-- ── SPEC §19.4 디싱크 주입 ──────────────────────────────────────────────────
local function run(bug, n_ticks)
    local m = T.load_text(H.golden('map_start.txt'))
    local s = SIM.new(m, 1, 2, bug)
    s:setup_start()
    local out = {n = n_ticks}
    for k = 0, n_ticks - 1 do
        out[k] = s:step({n = 0})
    end
    return out
end

local a = run(false, 80)
local b = run(false, 80)
local c = run(true, 80)
H.check('버그가 없으면 두 시뮬이 같다', a, b)
local first = -1
for k = 0, a.n - 1 do
    if a[k] ~= c[k] then
        first = k + 1
        break
    end
end
H.check_true(string.format('실수 누적을 켜면 갈린다 (처음 어긋난 틱 %d)', first),
             first > 0)

--- 눈에 보이는 차이(타일 좌표)가 처음 나는 틱. 없으면 -1.
local function tiles_diverge(n_ticks)
    local m1 = T.load_text(H.golden('map_start.txt'))
    local m2 = T.load_text(H.golden('map_start.txt'))
    local s1 = SIM.new(m1, 1, 2, false)
    local s2 = SIM.new(m2, 1, 2, true)
    s1:setup_start()
    s2:setup_start()
    for t = 1, n_ticks do
        s1:step({n = 0})
        s2:step({n = 0})
        for i = 1, C.MAX_ENT - 1 do
            if s1.w.alive[i] ~= s2.w.alive[i] or s1.w.tx[i] ~= s2.w.tx[i]
               or s1.w.ty[i] ~= s2.w.ty[i] then
                return t
            end
        end
    end
    return -1
end

H.check('80틱 동안 타일 좌표는 한 칸도 어긋나지 않는다', tiles_diverge(80), -1)
H.note('해시는 1틱에 갈리는데 화면은 그대로다 — 상태 해시가 없으면')
H.note('이 버그는 한참 뒤 "어쩐지 결과가 다른 게임"으로만 나타난다')
H.note('일부러 넣은 버그다 — "부동소수점이면 반드시 디싱크"가 아니라')
H.note('"이 조건에서 이렇게 어긋났다"가 말할 수 있는 전부다')

-- 명세가 정정한 부분: fpmul 을 실수로 해도 이 크기에서는 어긋나지 않는다
local bad = 0
for _, a_ in ipairs({6144, 4344, 65536, 1048576, 46341, 4194304}) do
    for _, b_ in ipairs({46341, 65536, 27146, 32768}) do
        -- 파이썬의 int(a*b/65536.0) 은 0 방향 절단이다. 여기 값들은 전부
        -- 양수라 math.floor 와 같다.
        if F.fp_mul(a_, b_) ~= math.floor(a_ * b_ / 65536.0) then
            bad = bad + 1
        end
    end
end
H.check('16.16 곱은 실수로 해도 정수와 비트 단위로 같다 (SPEC §19.4 의 정정)',
        bad, 0)
H.note('배정밀도 가수 53비트 · 곱은 커야 2^42 · 65536 은 2의 거듭제곱')

return H.done()
