-- AI — 영향 지도·안개 존중·건물 배치·빌드 오더·정찰 (SPEC §17).

local H = require('tests.harness')
local A = require('rts.ai')
local C = require('rts.const')
local E = require('rts.econ')
local F = require('rts.fixed')
local FL = require('rts.flow')
local FG = require('rts.fog')
local MV = require('rts.move')
local SEL = require('rts.select')
local S = require('rts.spatial')
local T = require('rts.tmap')

H.title('ai')

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
local function pt(x, y) return {[0] = x, [1] = y, n = 2} end

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

local function spawn(w, p, kind, x, y)
    local i = S.index(w:spawn(p, kind, x, y))
    w.hp[i] = C.HP[kind]
    return i
end

local function maxof(a)
    local v = a[0]
    for i = 0, a.n - 1 do if a[i] > v then v = a[i] end end
    return v
end
local function minof(a)
    local v = a[0]
    for i = 0, a.n - 1 do if a[i] < v then v = a[i] end end
    return v
end
local function sumof(a)
    local s = 0
    for i = 0, a.n - 1 do s = s + a[i] end
    return s
end

-- ── SPEC §17.2 전력 ─────────────────────────────────────────────────────────
local m = grid(rep(string.rep('.', 16), 16))
local w = S.new(16, 16)
local inf = spawn(w, 0, C.INF, 8, 8)
H.check('전력 = 기본 + 관통 + hp/4', A.strength(w, inf),
        C.BASIC[C.INF] + C.PIERCE[C.INF] + floor(C.HP[C.INF] / 4))
w.hp[inf] = 4
H.check('hp 가 줄면 전력도 준다', A.strength(w, inf),
        C.BASIC[C.INF] + C.PIERCE[C.INF] + 1)
w.hp[inf] = C.HP[C.INF]
H.check('채집기의 전력은 hp 뿐', A.strength(w, spawn(w, 0, C.HARV, 1, 1)),
        floor(C.HP[C.HARV] / 4))

-- ── SPEC §17.2 영향 지도 ────────────────────────────────────────────────────
local w2 = S.new(16, 16)
local fg = FG.new(16, 16)
local a = spawn(w2, 0, C.INF, 8, 8)
fg:add_sight(0, 8, 8, C.SIGHT[C.INF])
local inf0 = A.influence(w2, fg, 0, m)
local c = 8 * 16 + 8
H.check('내 유닛 자리가 가장 크다', inf0[c], maxof(inf0))
H.check_true('정수 내림 때문에 총합이 준다 — 그 감쇠가 곧 거리 감쇠다',
             sumof(inf0) < A.strength(w2, a))
H.check('먼 구석은 0', inf0[0], 0)
H.check('보병 한 기의 영향은 3회 확산 만에 이웃에서 사라진다', inf0[c - 1], 0)
H.note('영향 지도가 보는 것은 한 기가 아니라 밀집이다 — 이것도 감쇠의 결과다')

local wt = S.new(16, 16)
local ft = FG.new(16, 16)
local tank = spawn(wt, 0, C.TANK, 8, 8)
ft:add_sight(0, 8, 8, C.SIGHT[C.TANK])
local inft = A.influence(wt, ft, 0, m)
H.check_true(string.format('전차 한 기(전력 %d)는 이웃까지 번진다',
                           A.strength(wt, tank)), inft[c - 1] > 0)
H.check_true('멀수록 작다', inft[c - 1] > inft[c - 3])

spawn(w2, 1, C.TANK, 9, 8)
local fg2 = FG.new(16, 16)
fg2:add_sight(0, 8, 8, C.SIGHT[C.INF])
local inf1 = A.influence(w2, fg2, 0, m)
H.check_true('보이는 적은 음수로 들어간다', inf1[8 * 16 + 9] < inf0[8 * 16 + 9])
local fg3 = FG.new(16, 16)                 -- 아무것도 안 보이는 안개
local inf2 = A.influence(w2, fg3, 0, m)
H.check('안개 속의 적은 seed 에 들어가지 않는다 (§17.3) — 적이 없을 때와 같다',
        inf2, inf0)
H.check_true('보일 때와는 다르다', inf2[8 * 16 + 9] > inf1[8 * 16 + 9])
local thr = A.threat(w2, fg2, 0, m)
H.check_true('위협도는 적만으로 계산한다', thr[8 * 16 + 9] > 0)
H.check('내 유닛은 위협이 아니다', minof(thr), 0)

-- ── SPEC §17.3 유령 (마지막으로 본 위치) ────────────────────────────────────
local gh = A.newmemory(16, 16)
gh:update(w2, fg2, 0)
H.check('보이는 적은 유령으로 남는다', gh.ttl[8 * 16 + 9], A.GHOST_TICKS)
H.check_true('적 기지가 알려지지 않았다', not gh:enemy_base_known(w2, fg2, 0))
for _ = 1, A.GHOST_TICKS - 1 do
    gh:update(w2, fg3, 0)
end
H.check('안 보이면 매 틱 준다', gh.ttl[8 * 16 + 9], 1)
gh:update(w2, fg3, 0)
H.check('30틱이면 잊는다', gh.ttl[8 * 16 + 9], 0)
H.check('그 자리가 유령 목록에서도 빠진다', gh:ghosts(), {n = 0})
spawn(w2, 1, C.HQ, 2, 2)
local fg4 = FG.new(16, 16)
fg4:add_sight(0, 2, 2, 4)
gh:update(w2, fg4, 0)
H.check_true('적 건물을 보면 기지가 알려진다', gh:enemy_base_known(w2, fg4, 0))
H.check('알려진 기지 위치', gh:enemy_base(w2, fg4, 0), pt(2, 2))
H.note('이 제약이 없으면 AI 가 전지적이 되고, 그건 게임이 아니다')

-- ── SPEC §17.4 건물 배치 ────────────────────────────────────────────────────
local m5rows = rep(string.rep('.', 20), 10)
m5rows[#m5rows + 1] = string.rep('.', 16) .. '****'
for _ = 1, 9 do m5rows[#m5rows + 1] = string.rep('.', 20) end
local m5 = grid(m5rows)
local w5 = S.new(20, 20)
local mv5 = MV.new(w5, m5)
local ec5 = E.new(m5)
local hq = spawn(w5, 0, C.HQ, 5, 5)
mv5:claim(hq)
local fg5 = FG.new(20, 20)
fg5:add_sight(0, 5, 5, C.SIGHT[C.HQ])
local fire = FL.brushfire(m5, 0)
local thr5 = A.threat(w5, fg5, 0, m5)
local spot = A.best_placement(w5, m5, mv5, ec5, fire, thr5, 0, C.POW, pt(5, 5))
H.check_true('발전소 자리를 찾았다', spot ~= nil)
H.check('찾은 자리는 실제로 지을 수 있다',
        ec5:placeable(w5, m5, mv5, C.POW, spot[0], spot[1], 0), true)

--- 같은 점수를 아주 느리게 계산하는 참조 구현 (SPEC §17.4).
local function brute(kind)
    local best, bs, bi = nil, nil, nil
    local ore = ec5:nearest_ore(m5, 5, 5)
    for y = 0, 19 do
        for x = 0, 19 do
            if F.dinf(x - 5, y - 5) <= A.PLACE_R
               and ec5:placeable(w5, m5, mv5, kind, x, y, 0) then
                local i = y * 20 + x
                local sc = 100 - 3 * F.d83(x - 5, y - 5) + 2 * fire[i] - thr5[i]
                if kind == C.REF and ore >= 0 then
                    sc = sc + 40 - 8 * F.d83(ore % 20 - x, floor(ore / 20) - y)
                end
                if bs == nil or sc > bs or (sc == bs and i < bi) then
                    best, bs, bi = pt(x, y), sc, i
                end
            end
        end
    end
    return best
end

H.check('발전소 자리는 참조 구현과 같다', spot, brute(C.POW))
local ref_spot = A.best_placement(w5, m5, mv5, ec5, fire, thr5, 0, C.REF, pt(5, 5))
H.check('정제소 자리도 같다', ref_spot, brute(C.REF))
H.check_true('정제소는 광맥 쪽으로 끌린다', ref_spot[0] > spot[0])
H.check('기지 반경 밖에서는 못 찾는다',
        A.best_placement(w5, m5, mv5, ec5, fire, thr5, 3, C.POW, pt(60, 60)), nil)
H.note('점수의 fire 항이 벽에 붙지 않게 하고, threat 항이 전선을 피하게 한다')

-- ── SPEC §17.5 빌드 오더 ────────────────────────────────────────────────────
local m6rows = rep(string.rep('.', 24), 12)
m6rows[#m6rows + 1] = string.rep('.', 20) .. '****'
for _ = 1, 11 do m6rows[#m6rows + 1] = string.rep('.', 24) end
local m6 = grid(m6rows)
local w6 = S.new(24, 24)
local mv6 = MV.new(w6, m6)
local ec6 = E.new(m6)
local fg6 = FG.new(24, 24)
local gh6 = A.newmemory(24, 24)
local hq6 = spawn(w6, 0, C.HQ, 4, 4)
mv6:claim(hq6)
ec6:recount_supply(w6)
ec6.credits[0] = 1000
local act = A.build_order(w6, ec6, gh6, 0)
H.check('채집기가 4기 미만이면 채집기', act, arr('TRAIN', C.HARV, hq6))
for _ = 1, 4 do spawn(w6, 0, C.HARV, 8, 8) end
ec6:recount_supply(w6)
act = A.build_order(w6, ec6, gh6, 0)
H.check('채집기가 차면 정제소', arr(act[0], act[1]), arr('BUILD', C.REF))
ec6.credits[0] = 100
H.check('돈이 없으면 다음 줄로 내려간다', A.build_order(w6, ec6, gh6, 0),
        arr('DEFEND'))
H.note('군대가 없고 병영도 없고 돈도 없으면 남는 것은 방어뿐이다')
ec6.credits[0] = 1000
spawn(w6, 0, C.REF, 9, 4)
act = A.build_order(w6, ec6, gh6, 0)
H.check('정제소가 서면 병영', arr(act[0], act[1]), arr('BUILD', C.BARR))
local barr = spawn(w6, 0, C.BARR, 4, 9)
H.check('병영이 서면 보병', A.build_order(w6, ec6, gh6, 0),
        arr('TRAIN', C.INF, barr))
for _ = 1, 6 do spawn(w6, 0, C.INF, 6, 6) end
ec6:recount_supply(w6)
H.check('군대가 6 이면, 적 기지를 모르면 방어', A.build_order(w6, ec6, gh6, 0),
        arr('DEFEND'))
spawn(w6, 1, C.HQ, 20, 20)
fg6:add_sight(0, 20, 20, 4)
gh6:update(w6, fg6, 0)
H.check('적 기지를 알면 전군 공격', A.build_order(w6, ec6, gh6, 0),
        arr('ATTACK', 20, 20))
H.check('여섯 줄이 전부다', #A.RULES, 6)

-- ── SPEC §17.1 유닛 FSM ─────────────────────────────────────────────────────
local m7 = grid(rep(string.rep('.', 16), 16))
local w7 = S.new(16, 16)
local mv7 = MV.new(w7, m7)
local ords = SEL.neworders()
local me = spawn(w7, 0, C.ARCHER, 2, 2)     -- 사거리 4
mv7:claim(me)
w7.state[me] = C.ST_IDLE
A.unit_tick(w7, me, m7, mv7, ords)
H.check('적이 없으면 IDLE 그대로', w7.state[me], C.ST_IDLE)
local foe = spawn(w7, 1, C.INF, 4, 2)
mv7:claim(foe)
A.unit_tick(w7, me, m7, mv7, ords)
H.check('사거리 안에 적이 있으면 ATTACK', w7.state[me], C.ST_ATTACK)
H.check('표적이 잡힌다', w7.target[me], w7:handle(foe))
w7.tx[foe] = 2 + C.RANGE[C.ARCHER] + A.CHASE_R
A.unit_tick(w7, me, m7, mv7, ords)
H.check(string.format('사거리 + 추격 %d타일 안이면 쫓아간다', A.CHASE_R),
        w7.state[me], C.ST_MOVE)
w7.tx[foe] = w7.tx[foe] + 1
w7.state[me] = C.ST_ATTACK
A.unit_tick(w7, me, m7, mv7, ords)
H.check('한 칸만 더 멀어도 포기하고 IDLE', w7.state[me], C.ST_IDLE)
w7:kill(w7:handle(foe))
w7.state[me] = C.ST_ATTACK
w7.target[me] = 0
A.unit_tick(w7, me, m7, mv7, ords)
H.check('표적이 죽으면 IDLE', w7.state[me], C.ST_IDLE)

local hv = spawn(w7, 0, C.HARV, 3, 3)
mv7:claim(hv)
w7.hp[hv] = floor(C.HP[C.HARV] / 5)         -- 25% 아래
spawn(w7, 0, C.REF, 1, 1)
A.unit_tick(w7, hv, m7, mv7, ords)
H.check('hp 25% 아래인 채집기는 도망친다', w7.state[hv], C.ST_FLEE)
w7.hp[hv] = C.HP[C.HARV]
A.unit_tick(w7, hv, m7, mv7, ords)
H.check('회복하면 다시 캔다', w7.state[hv], C.ST_SEEK)

-- ── SPEC §17.6 정찰 ─────────────────────────────────────────────────────────
local m8 = grid(rep(string.rep('.', 16), 16))
local fg8 = FG.new(16, 16)
local tg = A.scout_targets(m8, fg8, 0)
H.check('16x16 이면 클러스터 4개', tg.n, 4)
H.check('클러스터 중심, 번호 오름차순', tg,
        arr(pt(4, 4), pt(12, 4), pt(4, 12), pt(12, 12)))
fg8:add_sight(0, 2, 2, 1)                   -- 클러스터 0 안에만 드는 작은 원
local rest = {n = tg.n - 1}
for k = 1, tg.n - 1 do rest[k - 1] = tg[k] end
H.check('탐험한 클러스터는 빠진다', A.scout_targets(m8, fg8, 0), rest)
local fg9 = FG.new(16, 16)
for i = 0, 16 * 16 - 1 do fg9.explored[0][i] = 1 end
H.check('전부 탐험하면 빈 목록', A.scout_targets(m8, fg9, 0), {n = 0})
H.note('정찰병이 죽으면 다음 유닛이 목록의 다음 항목부터 이어 간다')

return H.done()
