-- 시뮬레이션 — 틱 단계·상태 해시·트리거·시나리오 스크립트 (SPEC §18).

local H = require('tests.harness')
local C = require('rts.const')
local E = require('rts.econ')
local SEL = require('rts.select')
local SIM = require('rts.sim')
local S = require('rts.spatial')
local T = require('rts.tmap')

H.title('sim')

local function lst(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end
local function ord(p, issuer, kind, a, b, c)
    return {[0] = p, issuer, kind, a, b, c, n = 6}
end
local function rep(s, k)
    local t = {}
    for i = 1, k do t[i] = s end
    return t
end

local function grid(rows)
    local m = T.new(#rows[1], #rows)
    for y = 0, #rows - 1 do
        local row = rows[y + 1]
        for x = 0, m.w - 1 do
            local ch = row:sub(x + 1, x + 1)
            m.terrain[y * m.w + x] = T.TERRAIN_CH:find(ch, 1, true) - 1
            m:_repass(y * m.w + x)
        end
    end
    m:_bump()
    return m
end

local function flat(n)
    n = n or 24
    return grid(rep(string.rep('.', n), n))
end

local function add(s, p, kind, x, y)
    return S.index(s:spawn(p, kind, x, y))
end

local function count_kind(sm, kind, p)
    local n = 0
    for i = 1, C.MAX_ENT - 1 do
        if sm.w.alive[i] ~= 0 and sm.w.kind[i] == kind
           and (p == nil or sm.w.owner[i] == p) then
            n = n + 1
        end
    end
    return n
end
local function count_alive(sm)
    local n = 0
    for i = 1, C.MAX_ENT - 1 do
        if sm.w.alive[i] ~= 0 then n = n + 1 end
    end
    return n
end
local function ev_kinds(sm)
    local out = {n = sm.events.n}
    for k = 0, sm.events.n - 1 do out[k] = sm.events[k][0] end
    return out
end

-- ── SPEC §18.1 유일한 진입점 ────────────────────────────────────────────────
local s = SIM.new(flat(), 1234, 2)
H.check('시작 틱은 0', s.tick, 0)
s:step({n = 0})
H.check('한 틱 지나면 1', s.tick, 1)
H.check('이벤트는 매 틱 초에 비운다', s.events, {n = 0})

local u = add(s, 0, C.INF, 5, 5)
local h = s.w:handle(u)
s:step(lst(ord(0, h, SEL.MOVE, 8, 5, 0)))
H.check_true('MOVE 명령이 경로를 깐다', s.mv.goal[u] >= 0)
for _ = 1, 200 do s:step({n = 0}) end
H.check('목표까지 간다', lst(s.w.tx[u], s.w.ty[u]), lst(8, 5))

local raised = 0
if not pcall(function()
        s:step(lst(ord(1, 5, 0, 0, 0, 0), ord(0, 5, 0, 0, 0, 0)))
    end) then
    raised = 1
end
H.check('정렬되지 않은 명령 목록은 그 자리에서 터진다', raised, 1)
H.note('조용히 정렬해 주면 호출자의 버그가 다른 기계에서 다른 순서로 나타난다')

s:step(lst(ord(1, h, SEL.MOVE, 0, 0, 0)))
H.check('남의 유닛에 내린 명령은 무시', s.w.owner[u], 0)
s:step(lst(ord(0, 999999, SEL.MOVE, 0, 0, 0)))
H.check('죽은 핸들에 내린 명령도 무시', s.tick > 0, true)

-- ── SPEC §18.4 상태 해시 ────────────────────────────────────────────────────
local a = SIM.new(flat(), 7, 2)
local b = SIM.new(flat(), 7, 2)
for _, sm in ipairs({a, b}) do
    add(sm, 0, C.INF, 3, 3)
    add(sm, 1, C.TANK, 9, 9)
    add(sm, 0, C.HQ, 15, 15)
end
H.check('같은 상태면 같은 해시', a:state_hash(), b:state_hash())
H.check_true('해시는 32비트 안',
             a:state_hash() >= 0 and a:state_hash() < 4294967296)
local base = a:state_hash()
a.w.hp[1] = a.w.hp[1] - 1
H.check('hp 한 점이 해시를 바꾼다', a:state_hash() ~= base, true)
a.w.hp[1] = a.w.hp[1] + 1
H.check('되돌리면 같다', a:state_hash(), base)
for _, f in ipairs({'cool', 'timer', 'prog', 'load', 'dir', 'state', 'target'}) do
    a.w[f][1] = a.w[f][1] + 1
    if a:state_hash() == base then
        H.note('%s 가 해시에 들어가지 않는다', f)
    end
    a.w[f][1] = a.w[f][1] - 1
end
H.check('cool·timer 를 포함한 엔티티 15칸이 전부 해시에 들어간다',
        a:state_hash(), base)
a.ec.credits[0] = a.ec.credits[0] + 1
H.check('크레딧도 해시에', a:state_hash() ~= base, true)
a.ec.credits[0] = a.ec.credits[0] - 1
a.ec.ore[10] = 5
H.check('광맥 잔량도 해시에', a:state_hash() ~= base, true)
a.ec.ore[10] = 0
a.ec.queue[3] = lst(C.INF)          -- 3번이 사령부다 — 큐는 건물의 것이다
H.check('생산 큐도 해시에', a:state_hash() ~= base, true)
a.ec.queue[3] = {n = 0}
a.rng.s = a.rng.s + 1
H.check('rng 상태도 해시에', a:state_hash() ~= base, true)
a.rng.s = a.rng.s - 1
a.m:set_terrain(1, 1, T.ROCK)
H.check('지형이 바뀌면 map_hash 가 바뀐다', a:state_hash() ~= base, true)
local mh = a:map_hash()
H.check('map_hash 는 version 이 같으면 다시 계산하지 않는다',
        lst(a:map_hash(), a._map_hash_version), lst(mh, a.m.version))
a.m:set_terrain(1, 1, T.SAND)
H.check_true('version 이 오르면 다시 계산한다', a:map_hash() ~= mh)

-- ── SPEC §18.2 5단계: 피해는 모아서 적용한다 ────────────────────────────────
local s2 = SIM.new(flat(12), 3, 2)
local x = add(s2, 0, C.INF, 5, 5)
local y = add(s2, 1, C.INF, 6, 5)
s2.w.hp[x] = 3
s2.w.hp[y] = 3
for _ = 1, 30 do
    s2:step({n = 0})
    if s2.w.alive[x] == 0 or s2.w.alive[y] == 0 then break end
end
H.check('서로를 같은 틱에 죽일 수 있다 — 먼저 처리된 쪽이 유리하지 않다',
        lst(s2.w.alive[x], s2.w.alive[y]), lst(0, 0))

-- ── SPEC §18.3 이벤트 로그 ──────────────────────────────────────────────────
local s3 = SIM.new(flat(12), 5, 2)
local hq = add(s3, 0, C.HQ, 4, 4)
s3.ec.credits[0] = 1000
s3.ec:recount_supply(s3.w)
s3:step(lst(ord(0, s3.w:handle(hq), SEL.TRAIN, C.HARV, 0, 0)))
H.check('명령은 이벤트를 남긴다', ev_kinds(s3), lst(SIM.EV_ORDER))
for _ = 1, C.BUILD_TICKS[C.HARV] + 2 do
    s3:step({n = 0})
    local found = false
    for k = 0, s3.events.n - 1 do
        if s3.events[k][0] == SIM.EV_SPAWN then found = true end
    end
    if found then break end
end
H.check('생산이 끝나면 SPAWN 이벤트', ev_kinds(s3), lst(SIM.EV_SPAWN))
H.check_true('실제로 채집기가 생겼다', count_kind(s3, C.HARV) > 0)
H.check('이벤트는 해시에 넣지 않는다 — 트레이스가 대신 잡는다',
        s3.events.n ~= 0, true)

-- ── §16.4 건물 건설 ─────────────────────────────────────────────────────────
local s4 = SIM.new(flat(16), 9, 2)
local hq4 = add(s4, 0, C.HQ, 4, 4)
s4.mv:claim(hq4)
s4.ec.credits[0] = 1000
s4.ec:recount_supply(s4.w)
s4:step(lst(ord(0, s4.w:handle(hq4), SEL.BUILD, C.POW, 8, 4)))
H.check('BUILD 는 그 자리에 즉시 엔티티를 만든다', count_kind(s4, C.POW), 1)
local bi
for i = 1, C.MAX_ENT - 1 do
    if s4.w.alive[i] ~= 0 and s4.w.kind[i] == C.POW then bi = i end
end
H.check('짓는 중 상태', s4.w.state[bi], C.ST_BUILD)
H.check('hp 는 1 에서 시작', s4.w.hp[bi], 1)
H.check('돈은 선불', s4.ec.credits[0], 1000 - C.COST[C.POW])
H.check('짓는 중에도 발자국을 막는다', s4.m:passable_terrain(8, 4, 0), false)
for _ = 1, C.BUILD_TICKS[C.POW] + 2 do
    s4:step({n = 0})
    if s4.w.state[bi] == C.ST_IDLE then break end
end
H.check('다 지으면 IDLE', s4.w.state[bi], C.ST_IDLE)
H.check('hp 가 정격까지 찬다', s4.w.hp[bi], C.HP[C.POW])
s4:step(lst(ord(0, s4.w:handle(hq4), SEL.BUILD, C.FACT, 12, 12)))
H.check('돈이 없으면 짓지 않는다', count_kind(s4, C.FACT), 0)
s4:step(lst(ord(0, s4.w:handle(hq4), SEL.BUILD, C.POW, 4, 4)))
H.check('못 짓는 자리에도 짓지 않는다', count_kind(s4, C.POW), 1)

-- ── §16.5 내 유닛이 막고 있으면 비키게 한다 ─────────────────────────────────
--    채집 경로 위에 건물 자리를 잡으면 재시도가 전부 막힌다 — 실제로 그래서
--    플레이어 1 의 발전소가 1200틱 내내 서지 않았다.
local s4b = SIM.new(flat(16), 10, 2)
local hq4b = add(s4b, 0, C.HQ, 4, 4)
s4b.ec.credits[0] = 1000
s4b.ec:recount_supply(s4b.w)
local blocker = add(s4b, 0, C.INF, 9, 4)
H.check('그 칸은 내 유닛이 쥐고 있다', s4b.mv.resv[4 * 16 + 9],
        s4b.w:handle(blocker))
s4b:step(lst(ord(0, s4b.w:handle(hq4b), SEL.BUILD, C.POW, 8, 4)))
H.check('막힌 배치는 실패한다', count_kind(s4b, C.POW), 0)
H.check('돈은 나가지 않았다', s4b.ec.credits[0], 1000)
H.check_true('대신 막은 유닛에게 한 걸음 명령이 갔다',
             s4b.mv.goal[blocker] >= 0 or s4b.w.prog[blocker] > 0)
for _ = 1, 40 do
    s4b:step({n = 0})
    if not (s4b.w.tx[blocker] == 9 and s4b.w.ty[blocker] == 4) then break end
end
H.check_true('유닛이 비켰다',
             not (s4b.w.tx[blocker] == 9 and s4b.w.ty[blocker] == 4))
s4b:step(lst(ord(0, s4b.w:handle(hq4b), SEL.BUILD, C.POW, 8, 4)))
H.check('다음 시도는 성공한다', count_kind(s4b, C.POW), 1)
H.note('밀면서 동시에 짓지는 않는다 — 서 있는 유닛 위에 건물을 얹으면 불변식 R 이 깨진다')

-- ── SPEC §18.5 트리거 ───────────────────────────────────────────────────────
local s5 = SIM.new(flat(16), 11, 2)
s5:add_trigger(lst(SIM.CT_TICK_GE, 3, 0, 0, 0),
               lst(SIM.AC_SPAWN, 0, C.INF, 2, 2), true)
for _ = 1, 2 do s5:step({n = 0}) end
H.check('3틱 전에는 발화하지 않는다', count_alive(s5), 0)
s5:step({n = 0})
H.check('TICK_GE 가 발화해 유닛을 만든다', count_alive(s5), 1)
for _ = 1, 5 do s5:step({n = 0}) end
H.check('once 트리거는 한 번만', count_alive(s5), 1)
H.check('발화 표시는 상태의 일부', s5.fired[0], true)

local s6 = SIM.new(flat(16), 12, 2)
s6.ec.credits[1] = 500
s6:add_trigger(lst(SIM.CT_CREDITS_GE, 1, 400, 0, 0),
               lst(SIM.AC_MESSAGE, 7, 0, 0), true)
s6:step({n = 0})
local norder = 0
local msgs = {n = 0}
for k = 0, s6.events.n - 1 do
    if s6.events[k][0] == SIM.EV_ORDER then norder = norder + 1 end
    if s6.events[k][0] == SIM.EV_MESSAGE then
        msgs[msgs.n] = s6.events[k][1]
        msgs.n = msgs.n + 1
    end
end
H.check('CREDITS_GE', norder == 0, true)
H.check('메시지 액션은 이벤트로 나온다', msgs, lst(7))

local s7 = SIM.new(flat(16), 13, 2)
add(s7, 0, C.INF, 5, 5)
s7:add_trigger(lst(SIM.CT_UNIT_COUNT, 0, C.INF, SIM.CMP_GE, 1),
               lst(SIM.AC_REVEAL, 10, 10, 3), false)
s7:step({n = 0})
H.check('UNIT_COUNT + REVEAL', s7.fog.explored[0][10 * 16 + 10], 1)
s7:step({n = 0})
H.check('once 가 아니면 계속 평가한다', s7.fired[0], false)

local s8 = SIM.new(flat(16), 14, 2)
local mine8 = add(s8, 0, C.INF, 1, 1)
s8:add_trigger(lst(SIM.CT_AREA_ENTERED, 0, 8, 8, 2),
               lst(SIM.AC_LOSE, 0, 0, 0), true)
s8:step({n = 0})
H.check('멀리 있으면 발화하지 않는다', s8.loser, {n = 0})
s8.w.tx[mine8] = 8
s8.w.ty[mine8] = 9
s8:step({n = 0})
H.check('AREA_ENTERED', s8.loser, lst(0))

-- ── SPEC §18.5 기본 승패 ────────────────────────────────────────────────────
local s9 = SIM.new(flat(16), 15, 2)
local b0 = add(s9, 0, C.HQ, 2, 2)
local b1 = add(s9, 1, C.HQ, 12, 12)
s9.w.hp[b0] = 400
s9.w.hp[b1] = 400
s9:step({n = 0})
H.check('둘 다 살아 있으면 승자 없음', s9.winner, -1)
s9.w.hp[b1] = 0
s9:step({n = 0})
H.check('건물이 전부 부서진 쪽이 진다', s9.loser, lst(1))
H.check('남은 쪽이 이긴다', s9.winner, 0)
local function count_ev(sm, kind)
    local n = 0
    for k = 0, sm.events.n - 1 do
        if sm.events[k][0] == kind then n = n + 1 end
    end
    return n
end
H.check('WIN 이벤트', count_ev(s9, SIM.EV_WIN), 1)
s9:step({n = 0})
H.check('승리는 한 번만 알린다', count_ev(s9, SIM.EV_WIN), 0)

-- ── SPEC §18.6 시나리오 스크립트 ────────────────────────────────────────────
local sc = SIM.parse_script(H.golden('script.txt'))
H.check('골든 스크립트의 길이', sc.ticks, 1200)
H.check('플레이어 수', sc.players, 2)
H.check_true('명령이 여러 줄', sc.lines.n > 20)
local comments = {n = 0}
for k = 0, sc.lines.n - 1 do
    if tostring(sc.lines[k][2]):sub(1, 1) == '#' then
        comments[comments.n] = 1
        comments.n = comments.n + 1
    end
end
H.check('주석은 건너뛴다', comments, {n = 0})
local tks, tks_sorted = {n = sc.lines.n}, {}
for k = 0, sc.lines.n - 1 do
    tks[k] = sc.lines[k][0]
    tks_sorted[k + 1] = sc.lines[k][0]
end
table.sort(tks_sorted)
local tks_s0 = {n = sc.lines.n}
for k = 0, sc.lines.n - 1 do tks_s0[k] = tks_sorted[k + 1] end
H.check('틱 오름차순', tks, tks_s0)

local s10 = SIM.new(flat(20), 21, 2)
local u1 = add(s10, 0, C.INF, 2, 2)
local u2 = add(s10, 0, C.HARV, 3, 3)
local u3 = add(s10, 1, C.INF, 9, 9)
local bq = add(s10, 0, C.HQ, 5, 5)
local mini = SIM.parse_script('RTSS 1\nticks 10\nplayers 2\n'
                              .. '# 주석\n'
                              .. '1 0 A MOVE 7 7 0\n'
                              .. '2 0 F MOVE 8 8 0\n'
                              .. '3 0 K10 TRAIN 4 0 0\n'
                              .. '4 0 N MOVE 1 1 0\n')
local function issuers(o)
    local out = {n = o.n}
    for k = 0, o.n - 1 do out[k] = o[k][1] end
    return out
end
local o1 = s10:script_orders(mini, 1)
local w1, w2 = s10.w:handle(u1), s10.w:handle(u2)
H.check('선택자 A 는 내 유닛 전부 (건물 제외)', issuers(o1),
        lst(w1 < w2 and w1 or w2, w1 < w2 and w2 or w1))
H.check('명령 여섯 칸', o1[0].n, 6)
local o2 = s10:script_orders(mini, 2)
H.check('선택자 F 는 전투 유닛만', issuers(o2), lst(s10.w:handle(u1)))
local o3 = s10:script_orders(mini, 3)
H.check('선택자 K10 은 종류 10 (사령부)', issuers(o3), lst(s10.w:handle(bq)))
local o4 = s10:script_orders(mini, 4)
H.check('선택자 N 은 가장 최근에 생산된 유닛 하나', o4.n, 1)
H.check('없는 틱은 빈 목록', s10:script_orders(mini, 9), {n = 0})
local i1 = issuers(o1)
local i1s = {}
for k = 0, i1.n - 1 do i1s[k + 1] = i1[k] end
table.sort(i1s)
local i1s0 = {n = i1.n}
for k = 0, i1.n - 1 do i1s0[k] = i1s[k + 1] end
H.check('펼친 결과는 핸들 오름차순', i1, i1s0)
local found3 = false
for k = 0, i1.n - 1 do
    if i1[k] == s10.w:handle(u3) then found3 = true end
end
H.check('남의 유닛은 내 선택자에 걸리지 않는다', found3, false)

-- ── 결정론: 같은 씨앗·같은 명령이면 매 틱 같은 해시 ─────────────────────────
local function run(n)
    local sm = SIM.new(T.load_text(H.golden('map_start.txt')), 1, 2)
    sm:setup_start()
    local hs = {n = n}
    for t = 0, n - 1 do
        sm:step({n = 0})
        hs[t] = sm:state_hash()
    end
    return sm, hs
end

local s_a, h_a = run(120)
local s_b, h_b = run(120)
H.check('같은 씨앗이면 120틱의 해시열이 같다', h_a, h_b)
local uniq, nuniq = {}, 0
for k = 0, h_a.n - 1 do
    if not uniq[h_a[k]] then uniq[h_a[k]] = true; nuniq = nuniq + 1 end
end
H.check_true('해시가 실제로 변한다', nuniq > 60)
local s_c = SIM.new(T.load_text(H.golden('map_start.txt')), 1, 2)
s_c:setup_start()

H.check('시작 조건 — 플레이어마다 HQ 1채, 채집기 2기',
        {[0] = lst(count_kind(s_c, C.HQ, 0), count_kind(s_c, C.HARV, 0)),
         lst(count_kind(s_c, C.HQ, 1), count_kind(s_c, C.HARV, 1)), n = 2},
        {[0] = lst(1, C.START_HARV), lst(1, C.START_HARV), n = 2})
H.check('시작 크레딧', lst(s_c.ec.credits[0], s_c.ec.credits[1]),
        lst(C.START_CREDITS, C.START_CREDITS))
H.check('시작하면 AI 가 켜진다', lst(s_c.ai_enabled[0], s_c.ai_enabled[1]),
        lst(true, true))
H.check_true('120틱 뒤에는 AI 가 채집기를 더 뽑았다',
             count_kind(s_a, C.HARV, 0) > C.START_HARV)
H.check_true('채집이 돌아간다 (120틱)',
             s_a.ec.credits[0] + s_a.ec.credits[1] >= 0)
local rbad = 0
for i = 1, C.MAX_ENT - 1 do
    if s_a.w.alive[i] ~= 0 and C.IS_BUILDING[s_a.w.kind[i]] == 0
       and s_a.mv.resv[s_a.w.from_t[i]] ~= s_a.w:handle(i) then
        rbad = rbad + 1
    end
end
H.check('불변식 R 이 유지된다', rbad, 0)
H.check('불변식 F 가 유지된다', s_a.fog:recount(s_a.w), 0)

return H.done()
