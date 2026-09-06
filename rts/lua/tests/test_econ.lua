-- 경제 — 자원·채집기 FSM·수입률·생산 큐·기술 트리·인구 (SPEC §16).

local H = require('tests.harness')
local C = require('rts.const')
local E = require('rts.econ')
local F = require('rts.fixed')
local MV = require('rts.move')
local S = require('rts.spatial')
local T = require('rts.tmap')

H.title('econ')

local floor = math.floor
local function arr(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end
local function rep(s, k)
    local t = {}
    for i = 1, k do t[i] = s end
    return t
end

local g = H.lines(H.golden('prim.txt'))

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

-- ── 골든 12절 수입률 ────────────────────────────────────────────────────────
local i = H.index_of(g, '== 12. 경제 ==') + 2
local bad = 0
local rows = 0
while g[i]:sub(1, 1) == ' ' do
    local v = H.ints(g[i])
    local d, sp = v[0], v[1]
    local got = arr(E.round_trip_ticks(d, sp), E.income10000(d, sp))
    local wnt = arr(v[2], v[3])
    if not H.deep_eq(got, wnt) then
        bad = bad + 1
        H.note('d=%d v=%d 기대 %s 실제 %s', d, sp, H.repr(wnt), H.repr(got))
    end
    rows = rows + 1
    i = i + 1
end
H.check(string.format('골든 12절 수입률 %d줄', rows), bad, 0)
H.check('골든 마지막 줄의 세 상수', g[i],
        string.format('적재 %d · 틱당 채굴 %d · 반납 %d틱',
                      E.LOAD_MAX, E.MINE_PER_TICK, E.UNLOAD_TICKS))

-- ── 정리 16.1 의 상한 ───────────────────────────────────────────────────────
H.check('거리 0 이어도 총틱은 20+12', E.round_trip_ticks(0, F.fp(1)), 32)
H.check('그 상한 수입률은 3.125 크레딧/틱', E.income10000(0, F.fp(1)), 31250)
local mono = true
for d = 0, 39 do
    if E.income10000(d, 6554) < E.income10000(d + 1, 6554) then mono = false end
end
H.check_true('거리가 늘면 수입률은 단조 감소', mono)
H.note('정제소를 광맥에 붙여도 상한이 있다 — 17부에서 실측과 대조한다')

-- ── SPEC §16.1 광맥 ─────────────────────────────────────────────────────────
local m = grid({',,,,,,', ',**,,,', ',,,,,,', ',,,,,,'})
local ec = E.new(m)
local nore = 0
for k = 0, ec.ore.n - 1 do
    if ec.ore[k] > 0 then nore = nore + 1 end
end
H.check('광맥 두 칸이 잡혔다', nore, 2)
H.check('한 칸의 매장량', ec.ore[1 * m.w + 1], E.ORE_PER_TILE)
H.check('광맥이 아닌 칸은 0', ec.ore[0], 0)
H.check('가장 가까운 광맥 (d83 최소, 동점은 타일 번호 오름차순)',
        ec:nearest_ore(m, 3, 0), 1 * m.w + 2)
H.check('동점이면 작은 타일 번호', ec:nearest_ore(m, 1, 3), 1 * m.w + 1)
local took = ec:mine(m, 1 * m.w + 1, 30)
H.check('30 을 캐면 30 이 나온다', took, 30)
H.check('잔량이 준다', ec.ore[1 * m.w + 1], E.ORE_PER_TILE - 30)
H.check('남은 것보다 많이 캘 수는 없다',
        ec:mine(m, 1 * m.w + 1, 9999), E.ORE_PER_TILE - 30)
H.check('다 캐면 모래가 된다', m:terrain_at(1, 1), T.SAND)
H.check('다 캔 칸은 광맥 목록에서 빠진다', ec:nearest_ore(m, 1, 1), 1 * m.w + 2)
local mempty = grid({',,', ',,'})
H.check('광맥이 하나도 없으면 -1', E.new(mempty):nearest_ore(mempty, 0, 0), -1)

-- ── SPEC §16.4 생산 큐 ──────────────────────────────────────────────────────
local m2 = grid(rep(string.rep('.', 12), 12))
local w = S.new(m2.w, m2.h)
ec = E.new(m2)
local hq = S.index(w:spawn(0, C.HQ, 2, 2))
w.hp[hq] = C.HP[C.HQ]
ec.credits[0] = 1000
ec:recount_supply(w)
H.check('사령부가 주는 인구 상한', ec.supply_cap[0], C.POP[C.HQ])
H.check('처음 인구 사용은 0', ec.supply_used[0], 0)

H.check('선불 — 큐에 넣는 순간 크레딧이 빠진다', ec:enqueue(w, hq, C.HARV), true)
H.check('크레딧', ec.credits[0], 1000 - C.COST[C.HARV])
H.check('큐 길이 1', ec.queue[hq].n, 1)
for _ = 1, 4 do ec:enqueue(w, hq, C.HARV) end
H.check('큐 상한은 5', ec.queue[hq].n, E.QUEUE_MAX)
H.check('상한을 넘으면 거부하고 돈도 안 뺀다',
        arr(ec:enqueue(w, hq, C.HARV), ec.credits[0]),
        arr(false, 1000 - 5 * C.COST[C.HARV]))
H.check('취소는 100% 환불 (이 덱의 규칙)', ec:cancel(w, hq, 4), C.COST[C.HARV])
H.check('환불 뒤 크레딧', ec.credits[0], 1000 - 4 * C.COST[C.HARV])
H.check('없는 항목 취소는 0', ec:cancel(w, hq, 9), 0)

local done = {n = 0}
for _ = 1, C.BUILD_TICKS[C.HARV] do
    local d = ec:step_production(w)
    for k = 0, d.n - 1 do
        done[done.n] = d[k]
        done.n = done.n + 1
    end
end
H.check('건설틱만큼 지나면 하나 완성', done.n, 1)
H.check('완성 정보는 (건물 인덱스, 종류)', done[0], {hq, C.HARV})
H.check('큐에서 빠진다', ec.queue[hq].n, 3)
H.check('진행률은 0 부터 다시', ec.progress[hq], 0)
H.check('돈이 모자라면 큐에 못 넣는다', E.new(m2):enqueue(w, hq, C.FACT), false)

-- ── SPEC §16.6 기술 트리 ────────────────────────────────────────────────────
local order = E.topo_order()
H.check('위상 정렬에 16개가 전부 들어간다', order.n, 16)
local pos = {}
for k = 0, order.n - 1 do pos[order[k]] = k end
local viol = {n = 0}
for k = 0, 15 do
    for j = 0, C.PREREQ[k].n - 1 do
        if pos[C.PREREQ[k][j]] > pos[k] then
            viol[viol.n] = 1
            viol.n = viol.n + 1
        end
    end
end
H.check('선행이 반드시 앞에 온다', viol, {n = 0})
H.check('진입차수 0 은 번호 오름차순으로 나온다',
        arr(order[0], order[1], order[2]), arr(5, 6, 7))
H.note('5..9 는 비어 있는 번호라 선행이 없다 — 그래서 맨 앞에 온다')
H.check('순환을 넣으면 즉시 실패한다',
        E.topo_order({[0] = {C.HQ, C.BARR}, n = 1}), nil)

local w2 = S.new(m2.w, m2.h)
local ec2 = E.new(m2)
H.check('아무 건물도 없으면 사령부조차 못 짓는다... 는 아니다 (선행 없음)',
        ec2:can_build(w2, 0, C.HQ), true)
H.check('사령부 없이 채집기는 못 뽑는다', ec2:can_build(w2, 0, C.HARV), false)
local b = S.index(w2:spawn(0, C.HQ, 2, 2))
w2.hp[b] = 400
H.check('사령부가 있으면 채집기·정제소·병영', ec2:can_build(w2, 0, C.HARV), true)
H.check('병영 없이 보병은 못 뽑는다', ec2:can_build(w2, 0, C.INF), false)
H.check('남의 건물은 내 선행이 아니다', ec2:can_build(w2, 1, C.HARV), false)
local bar = S.index(w2:spawn(0, C.BARR, 5, 5))
w2.hp[bar] = 200
H.check('병영이 서면 보병', ec2:can_build(w2, 0, C.INF), true)
H.check('공장은 발전소가 더 필요하다', ec2:can_build(w2, 0, C.FACT), false)
local pw = S.index(w2:spawn(0, C.POW, 8, 5))
w2.hp[pw] = 150
H.check('둘 다 있으면 공장', ec2:can_build(w2, 0, C.FACT), true)
w2:kill(w2:handle(bar))
H.check('병영이 부서지면 보병을 못 뽑는다', ec2:can_build(w2, 0, C.INF), false)
H.note('선행은 "완성된 채 살아 있는지" 를 본다')

-- ── SPEC §16.5 배치 판정 ────────────────────────────────────────────────────
local m3rows = {string.rep('.', 10), '..~~......'}
for _ = 1, 8 do m3rows[#m3rows + 1] = string.rep('.', 10) end
local m3 = grid(m3rows)
local w3 = S.new(m3.w, m3.h)
local mv = MV.new(w3, m3)
local ec3 = E.new(m3)
H.check('첫 건물은 4타일 규칙을 면제받는다',
        ec3:placeable(w3, m3, mv, C.POW, 0, 4, 0), true)
local first = S.index(w3:spawn(0, C.HQ, 0, 4))
w3.hp[first] = 400
mv:claim(first)
H.check('예약된 칸에는 못 짓는다',
        ec3:placeable(w3, m3, mv, C.POW, 0, 4, 0), false)
H.check('물 위에는 못 짓는다', ec3:placeable(w3, m3, mv, C.POW, 2, 1, 0), false)
H.check('맵 밖으로 삐져나가면 안 된다',
        ec3:placeable(w3, m3, mv, C.POW, 9, 9, 0), false)
H.check('기지에서 4타일 안이면 된다',
        ec3:placeable(w3, m3, mv, C.POW, 3, 4, 0), true)
H.check('4타일 밖은 안 된다', ec3:placeable(w3, m3, mv, C.POW, 6, 0, 0), false)
H.check('남의 기지 옆이어도 내 첫 건물이면 지을 수 있다',
        ec3:placeable(w3, m3, mv, C.POW, 3, 4, 1), true)
H.note('4타일 규칙은 기지를 한 덩어리로 유지시켜 AI 의 방어를 단순하게 만든다')

-- ── SPEC §16.7 인구 ─────────────────────────────────────────────────────────
local w4 = S.new(m2.w, m2.h)
local ec4 = E.new(m2)
ec4.credits[0] = 5000
local hq4 = S.index(w4:spawn(0, C.HQ, 2, 2))
w4.hp[hq4] = 400
for _ = 1, 10 do
    local u = S.index(w4:spawn(0, C.INF, 5, 5))
    w4.hp[u] = 40
end
ec4:recount_supply(w4)
H.check('인구 사용 10 · 상한 10',
        arr(ec4.supply_used[0], ec4.supply_cap[0]), arr(10, 10))
H.check('꽉 차면 큐에 못 넣는다', ec4:enqueue(w4, hq4, C.HARV), false)
H.note('보병이 아니라 채집기로 시험한다 — 병영이 없으면 선행에서 먼저 걸린다')
local p2 = S.index(w4:spawn(0, C.POW, 8, 8))
w4.hp[p2] = 150
ec4:recount_supply(w4)
H.check('발전소가 상한을 10 올린다', ec4.supply_cap[0], 20)
H.check('이제는 들어간다', ec4:enqueue(w4, hq4, C.HARV), true)
H.check('큐에 든 것도 인구를 먹는다 (§16.7)', ec4:reserved(w4, 0), C.POP[C.HARV])
local ntrue = 0
for _ = 1, 12 do
    if ec4:enqueue(w4, hq4, C.HARV) then ntrue = ntrue + 1 end
end
H.check('큐 상한 5칸까지만 더 들어간다 (인구 여유는 10)', ntrue, E.QUEUE_MAX - 1)
H.note('이 예약이 없으면 큐 다섯 칸이 상한을 조용히 넘어선다 — 실제로 16/10 이 나왔다')
H.check('전차는 인구 2 를 먹는다', C.POP[C.TANK], 2)
local u
for _ = 1, 50 do
    u = S.index(w4:spawn(0, C.INF, 5, 5))
    w4.hp[u] = 40
end
ec4:recount_supply(w4)
H.check('상한은 100 을 넘지 않는다',
        (ec4.supply_cap[0] < 999 and ec4.supply_cap[0] or 999) <= 100, true)
w4:kill(w4:handle(u))
ec4:recount_supply(w4)
H.check('죽은 유닛은 인구를 먹지 않는다', ec4.supply_used[0], 59)

-- ── SPEC §16.2 채집기 FSM — 한 판 돌려 본다 ─────────────────────────────────
local m5rows = rep(string.rep('.', 16), 4)
m5rows[#m5rows + 1] = string.rep('.', 12) .. '**..'
for _ = 1, 11 do m5rows[#m5rows + 1] = string.rep('.', 16) end
local m5 = grid(m5rows)
local w5 = S.new(m5.w, m5.h)
local mv5 = MV.new(w5, m5)
local ec5 = E.new(m5)
local ref = S.index(w5:spawn(0, C.REF, 1, 4))
w5.hp[ref] = C.HP[C.REF]
mv5:claim(ref)
local hv = S.index(w5:spawn(0, C.HARV, 3, 4))
w5.hp[hv] = C.HP[C.HARV]
mv5:claim(hv)
w5.state[hv] = E.H_SEEK
local states = {}
local first_unload = -1
for t = 0, 1199 do
    ec5:harvest_tick(w5, hv, m5, mv5)
    mv5:step()
    states[w5.state[hv]] = true
    if ec5.credits[0] > 0 and first_unload < 0 then first_unload = t end
end
local sl = {n = 0}
for v = 0, 9 do
    if states[v] then sl[sl.n] = v; sl.n = sl.n + 1 end
end
local wantstates = {E.H_SEEK, E.H_TO_ORE, E.H_MINE, E.H_TO_BASE, E.H_UNLOAD}
table.sort(wantstates)
local wantstates0 = {n = 5}
for k = 0, 4 do wantstates0[k] = wantstates[k + 1] end
H.check('FSM 다섯 상태를 모두 거친다', sl, wantstates0)
H.check_true(string.format('1200틱 안에 첫 반납이 있었다 (%d틱)', first_unload),
             first_unload > 0 and first_unload < 1200)
H.check('적재량은 상한을 넘지 않는다', w5.load[hv] <= E.LOAD_MAX, true)
H.check_true('크레딧이 적재 단위로 들어온다', ec5.credits[0] % E.LOAD_MAX == 0)
local oresum = 0
for k = 0, ec5.ore.n - 1 do oresum = oresum + ec5.ore[k] end
H.check_true('광맥이 실제로 줄었다', oresum < 2 * E.ORE_PER_TILE)
local rate = F.floordiv(ec5.credits[0] * 10000, 1200)
H.note('실측 수입률 %d/10000 크레딧/틱 — 정리 16.1 의 이론값과 17부에서 대조', rate)
H.check_true('실측이 이론 상한을 넘지 않는다', rate <= 31250)

-- ── §16.2 도크 — 건물 원점으로 명령하면 안 되는 이유 ────────────────────────
--    실제로 겪은 버그다: 정제소가 세 면이 막혀 동쪽으로만 열려 있었는데,
--    북서쪽 채집기가 §8.6 의 대체 목표로 "지금 서 있는 칸"을 받아 굳었다.
local md = grid(rep(string.rep('.', 10), 10))
local wd = S.new(10, 10)
local mvd = MV.new(wd, md)
local ecd = E.new(md)
local refd = S.index(wd:spawn(0, C.REF, 4, 4))   -- 2x2 = (4,4)-(5,5)
wd.hp[refd] = C.HP[C.REF]
mvd:claim(refd)
for x = 3, 6 do                                   -- 북·서·남을 막는다
    md:set_terrain(x, 3, T.ROCK)
    md:set_terrain(x, 6, T.ROCK)
end
for y = 3, 6 do
    md:set_terrain(3, y, T.ROCK)
end
local hvd = S.index(wd:spawn(0, C.HARV, 1, 1))
wd.hp[hvd] = C.HP[C.HARV]
mvd:claim(hvd)
local dock = ecd:dock(wd, md, mvd, hvd, refd)
H.check_true('도크는 발자국에 접한 칸이다',
             dock ~= nil and F.dinf(dock[0] - 4, dock[1] - 4) <= 2)
H.check('도크는 통행 가능하다', md:passable_terrain(dock[0], dock[1], 0), true)
H.check('막힌 면에는 도크를 잡지 않는다',
        md:terrain_at(dock[0], dock[1]) ~= T.ROCK, true)
H.check('도크는 건물 안이 아니다',
        (dock[0] >= 4 and dock[0] <= 5 and dock[1] >= 4 and dock[1] <= 5), false)
wd.load[hvd] = E.LOAD_MAX
wd.state[hvd] = E.H_MINE
ecd.ore_target[hvd] = 0
local tlast = 0
for t = 0, 399 do
    tlast = t
    ecd:harvest_tick(wd, hvd, md, mvd)
    mvd:step()
    if ecd.credits[0] > 0 then break end
end
H.check_true(string.format('세 면이 막힌 정제소에도 결국 반납한다 (%d틱)', tlast),
             ecd.credits[0] == E.LOAD_MAX)

-- ── §16.2 도달 가능한 광맥만 고른다 ─────────────────────────────────────────
local mr = grid({'....#....*', '....#.....', '....#.....', '....#.....',
                 '....#.....', '....#.....', '....#.....', '..*.#.....',
                 '....#.....', '....#....'})
local ecr = E.new(mr)
H.check('벽 이쪽의 광맥을 고른다', ecr:nearest_ore(mr, 0, 0), 7 * 10 + 2)
H.check('벽 저쪽의 광맥은 고르지 않는다',
        ecr:nearest_ore(mr, 0, 0) ~= 0 * 10 + 9, true)
H.check('벽 저쪽에서 보면 저쪽 것을 고른다', ecr:nearest_ore(mr, 9, 0), 0 * 10 + 9)
H.note('도달 판정을 빼면 채집기가 바위 건너편을 향해 영원히 선다')

-- 광맥이 없으면 IDLE
local m6 = grid(rep(string.rep('.', 8), 8))
local w6 = S.new(8, 8)
local mv6 = MV.new(w6, m6)
local ec6 = E.new(m6)
local h6 = S.index(w6:spawn(0, C.HARV, 3, 3))
w6.hp[h6] = 60
mv6:claim(h6)
ec6:harvest_tick(w6, h6, m6, mv6)
H.check('광맥이 없으면 IDLE', w6.state[h6], E.H_IDLE)

return H.done()
