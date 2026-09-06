-- AI — 영향 지도·유령 기억·건물 배치·빌드 오더·정찰 (SPEC §17).
--
--    AI 는 **시뮬레이션의 일부**다. sim.step 안에서 돌고 명령을 자기 큐에 바로
--    넣는다. 네트워크 지연을 거치지 않아도 되는 이유는 모든 기계가 같은 AI 를
--    같은 틱에 돌리기 때문이다 — 결정론이 통신을 대신한다.
--
--    AI 는 안개를 존중한다(§17.3). 이 제약이 없으면 AI 가 전지적이 되고, 그건
--    게임이 아니다. 대신 마지막으로 본 위치를 30틱 기억해서 정찰에 값어치를 만든다.

local CB = require('rts.combat')
local C = require('rts.const')
local E = require('rts.econ')
local F = require('rts.fixed')
local SEL = require('rts.select')
local S = require('rts.spatial')

local M = {}
local floor = math.floor

M.GHOST_TICKS = 30               -- §17.3 마지막으로 본 위치를 기억하는 틱
M.PLACE_R = 12                   -- §17.4 건물 후보 반경 (타일)
M.CHASE_R = 3                    -- §17.1 추격은 사거리 + 이만큼까지
M.SPREAD = 3                     -- §17.2 확산 반복 횟수
M.FLEE_NUM, M.FLEE_DEN = 1, 4    -- §17.1 hp 가 1/4 아래면 도망
M.ARMY_MIN = 6                   -- §17.5 이만큼 모이면 나간다
M.HARV_MIN = 4
local GHOST_TICKS, PLACE_R, CHASE_R, SPREAD = 30, 12, 3, 3
local FLEE_NUM, FLEE_DEN, ARMY_MIN, HARV_MIN = 1, 4, 6, 4

-- ── SPEC §17.2 영향 지도 ────────────────────────────────────────────────────

--- 전력 = 기본 + 관통 + hp/4. 이 덱의 규칙이다.
function M.strength(w, i)
    return C.BASIC[w.kind[i]] + C.PIERCE[w.kind[i]] + F.floordiv(w.hp[i], 4)
end
local strength = M.strength

--- 3회 확산. 가중치 4 + 8 = 12 로 나눈다.
--
--    정수 나눗셈의 내림 때문에 매 반복 조금씩 줄어드는데, 그 감쇠가 곧 "멀수록
--    영향이 적다"이다. 별도의 감쇠 계수를 두지 않는 이유가 이것이다.
--    O(3 × 칸수 × 9).
local function spread(m, seed)
    local cur = seed
    for _ = 1, SPREAD do
        local nxt = {n = m.w * m.h}
        for y = 0, m.h - 1 do
            for x = 0, m.w - 1 do
                local acc = 4 * cur[y * m.w + x]
                for d = 0, 7 do
                    local u, v = x + F.DX[d], y + F.DY[d]
                    if u >= 0 and u < m.w and v >= 0 and v < m.h then
                        acc = acc + cur[v * m.w + u]
                    end
                end
                nxt[y * m.w + x] = F.floordiv(acc, 12)
            end
        end
        cur = nxt
    end
    return cur
end
M._spread = spread

local function seeds(w, fog, p, m, enemy_only)
    local seed = {n = m.w * m.h}
    for i = 0, m.w * m.h - 1 do seed[i] = 0 end
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] ~= 0 and w.hp[i] > 0 then
            local t = w.ty[i] * m.w + w.tx[i]
            if w.owner[i] == p then
                if not enemy_only then
                    seed[t] = seed[t] + strength(w, i)
                end
            elseif fog:visible(p, t) then      -- 보이는 적만 (§17.3)
                if enemy_only then
                    seed[t] = seed[t] + strength(w, i)
                else
                    seed[t] = seed[t] - strength(w, i)
                end
            end
        end
    end
    return seed
end
M._seeds = seeds

function M.influence(w, fog, p, m)
    return spread(m, seeds(w, fog, p, m, false))
end

function M.threat(w, fog, p, m)
    return spread(m, seeds(w, fog, p, m, true))
end

-- ── SPEC §17.3 유령 (마지막으로 본 위치) ────────────────────────────────────

--- 적을 마지막으로 본 자리를 30틱 기억한다. 건물 자리는 잊지 않는다 — 건물은
--- 움직이지 않으므로 한 번 본 것을 잊는 편이 오히려 거짓말이다.
local Memory = {}
Memory.__index = Memory
M.Memory = Memory

function M.newmemory(w, h)
    local self = setmetatable({w = w, h = h, base_tile = -1}, Memory)
    self.ttl = {n = w * h}
    for i = 0, w * h - 1 do self.ttl[i] = 0 end
    return self
end
Memory.new = M.newmemory

function Memory:update(world, fog, p)
    for i = 0, self.ttl.n - 1 do
        if self.ttl[i] > 0 then
            self.ttl[i] = self.ttl[i] - 1
        end
    end
    for j = 1, C.MAX_ENT - 1 do
        if world.alive[j] ~= 0 and world.owner[j] ~= p and world.hp[j] > 0 then
            local t = world.ty[j] * self.w + world.tx[j]
            if fog:visible(p, t) then
                self.ttl[t] = GHOST_TICKS
                if C.IS_BUILDING[world.kind[j]] ~= 0 then
                    if self.base_tile < 0 or t < self.base_tile then
                        self.base_tile = t
                    end
                end
            end
        end
    end
end

function Memory:ghosts()
    local out = {n = 0}
    for i = 0, self.ttl.n - 1 do
        if self.ttl[i] > 0 then
            out[out.n] = i
            out.n = out.n + 1
        end
    end
    return out
end

function Memory:enemy_base_known(world, fog, p)
    return self.base_tile >= 0
end

function Memory:enemy_base(world, fog, p)
    if self.base_tile < 0 then
        return nil
    end
    return {[0] = self.base_tile % self.w, [1] = floor(self.base_tile / self.w),
            n = 2}
end

-- ── SPEC §17.4 건물 배치 ────────────────────────────────────────────────────

--- 점수 — fire 항이 벽에 붙지 않게 하고, threat 항이 전선을 피하게 한다.
function M.place_score(m, ec, fire, thr, kind, x, y, cx, cy, ore)
    local i = y * m.w + x
    local sc = 100 - 3 * F.d83(x - cx, y - cy) + 2 * fire[i] - thr[i]
    if kind == C.REF and ore >= 0 then
        sc = sc + 40 - 8 * F.d83(ore % m.w - x, floor(ore / m.w) - y)
    end
    return sc
end

--- 기지 중심 반경 12 안에서 점수 최대, 동점이면 타일 번호 최소.
function M.best_placement(w, m, mv, ec, fire, thr, p, kind, centre)
    local cx, cy = centre[0], centre[1]
    local ore = (kind == C.REF) and ec:nearest_ore(m, cx, cy) or -1
    local best, bs, bi = nil, nil, nil
    for y = cy - PLACE_R, cy + PLACE_R do
        for x = cx - PLACE_R, cx + PLACE_R do
            if m:in_map(x, y) and F.dinf(x - cx, y - cy) <= PLACE_R
               and ec:placeable(w, m, mv, kind, x, y, p) then
                local i = y * m.w + x
                local sc = M.place_score(m, ec, fire, thr, kind, x, y, cx, cy, ore)
                if bs == nil or sc > bs or (sc == bs and i < bi) then
                    best, bs, bi = {[0] = x, [1] = y, n = 2}, sc, i
                end
            end
        end
    end
    return best
end

-- ── SPEC §17.5 빌드 오더 ────────────────────────────────────────────────────
local function count(w, p, kind)
    local n = 0
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] == 1 and w.owner[i] == p and w.kind[i] == kind
           and w.hp[i] > 0 then
            n = n + 1
        end
    end
    return n
end
M._count = count

local function army(w, p)
    local n = 0
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] == 1 and w.owner[i] == p and w.hp[i] > 0
           and C.IS_BUILDING[w.kind[i]] == 0 and C.BASIC[w.kind[i]] > 0 then
            n = n + 1
        end
    end
    return n
end
M._army = army

--- 그 유닛을 뽑을 수 있는 내 건물 중 인덱스가 가장 작은 것. 없으면 -1.
function M.producer(w, ec, p, kind)
    if C.PREREQ[kind].n == 0 then
        return -1
    end
    local need = C.PREREQ[kind][0]
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] == 1 and w.owner[i] == p and w.kind[i] == need
           and w.hp[i] > 0 and ec.queue[i].n < E.QUEUE_MAX then
            return i
        end
    end
    return -1
end

local function can_train(w, ec, p, kind)
    local bi = M.producer(w, ec, p, kind)
    if bi < 0 or not ec:can_build(w, p, kind) then
        return -1
    end
    if ec.credits[p] < C.COST[kind] then
        return -1
    end
    if ec.supply_used[p] + C.POP[kind] > ec.supply_cap[p] then
        return -1
    end
    return bi
end

local function can_build_(w, ec, p, kind, credits)
    if ec.credits[p] < credits or not ec:can_build(w, p, kind) then
        return false
    end
    return true
end

-- 행동은 0-기반 배열로 돌려준다: {[0]='TRAIN', 종류, 건물 인덱스} 등.
local function act(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end
M._act = act

local function rule_harvester(w, ec, mem, p)
    if count(w, p, C.HARV) >= HARV_MIN then
        return nil
    end
    local bi = can_train(w, ec, p, C.HARV)
    if bi >= 0 then return act('TRAIN', C.HARV, bi) end
    return nil
end

local function rule_refinery(w, ec, mem, p)
    if count(w, p, C.REF) > 0 then
        return nil
    end
    if can_build_(w, ec, p, C.REF, 300) then return act('BUILD', C.REF) end
    return nil
end

local function rule_barracks(w, ec, mem, p)
    if count(w, p, C.BARR) > 0 then
        return nil
    end
    if can_build_(w, ec, p, C.BARR, 400) then return act('BUILD', C.BARR) end
    return nil
end

local function rule_infantry(w, ec, mem, p)
    if army(w, p) >= ARMY_MIN then
        return nil
    end
    local bi = can_train(w, ec, p, C.INF)
    if bi >= 0 then return act('TRAIN', C.INF, bi) end
    return nil
end

local function rule_attack(w, ec, mem, p)
    if army(w, p) < ARMY_MIN or not mem:enemy_base_known(w, nil, p) then
        return nil
    end
    local b = mem:enemy_base(w, nil, p)
    return act('ATTACK', b[0], b[1])
end

local function rule_defend(w, ec, mem, p)
    return act('DEFEND')
end

--- 일곱째 줄 — 실험용이다(§17.5). 여섯 줄짜리 AI 는 인구 10 에서 멈춘다.
local function rule_power(w, ec, mem, p)
    if ec.supply_cap[p] - ec.supply_used[p] >= 2 then
        return nil
    end
    if ec.supply_cap[p] >= E.SUPPLY_MAX then
        return nil
    end
    if can_build_(w, ec, p, C.POW, 200) then return act('BUILD', C.POW) end
    return nil
end

M._rule_harvester = rule_harvester
M._rule_refinery = rule_refinery
M._rule_barracks = rule_barracks
M._rule_infantry = rule_infantry
M._rule_attack = rule_attack
M._rule_defend = rule_defend
M._rule_power = rule_power

-- 여섯 줄이 AI 전부다. 위에서부터 훑어 처음으로 조건을 만족하는 하나를 실행한다.
M.RULES = {rule_harvester, rule_refinery, rule_barracks,
           rule_infantry, rule_attack, rule_defend}
-- 발전소 한 줄을 더한 판. 18부가 두 실행을 나란히 놓는다.
M.RULES7 = {rule_harvester, rule_refinery, rule_barracks, rule_power,
            rule_infantry, rule_attack, rule_defend}

function M.build_order(w, ec, mem, p, rules)
    rules = rules or M.RULES
    for k = 1, #rules do
        local a = rules[k](w, ec, mem, p)
        if a ~= nil then
            return a
        end
    end
    return act('DEFEND')
end

-- ── SPEC §17.1 유닛 FSM ─────────────────────────────────────────────────────

--- 한 유닛의 상태 전이. 평가 순서가 곧 우선순위다.
function M.unit_tick(w, i, m, mv, orders)
    local kind = w.kind[i]
    if C.IS_BUILDING[kind] ~= 0 then
        return
    end
    if kind == C.HARV then
        if w.hp[i] * FLEE_DEN < C.HP[kind] * FLEE_NUM then   -- hp 25 % 아래
            local h = 0
            for j = 1, C.MAX_ENT - 1 do
                if w.alive[j] == 1 and w.owner[j] == w.owner[i]
                   and E.is_depot(w.kind[j]) and w.hp[j] > 0 then
                    h = j
                    break
                end
            end
            w.state[i] = C.ST_FLEE
            if h ~= 0 then
                mv:order(i, w.tx[h], w.ty[h])
            end
            return
        end
        if w.state[i] == C.ST_FLEE then
            w.state[i] = C.ST_SEEK        -- 회복하면 하던 일로 돌아간다
        end
        return
    end
    local tgt, approach = CB.pick_target(w, i, 0, w.state[i] == C.ST_MOVE)
    if tgt ~= 0 and not approach then
        w.target[i] = tgt
        w.state[i] = C.ST_ATTACK
        return
    end
    if w.state[i] == C.ST_ATTACK or w.state[i] == C.ST_MOVE then
        local cur = w.target[i]
        if w:valid(cur) then
            local j = S.index(cur)
            local d = F.dinf(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i])
            if d <= C.RANGE[kind] + CHASE_R then
                w.state[i] = C.ST_MOVE    -- 추격
                mv:order(i, w.tx[j], w.ty[j])
                orders:push(i, act(SEL.ATTACK_MOVE, w.tx[j], w.ty[j], cur), false)
                return
            end
        end
        w.target[i] = 0
        w.state[i] = C.ST_IDLE
        return
    end
    if tgt ~= 0 then
        w.target[i] = tgt
        w.state[i] = C.ST_MOVE
        return
    end
    if mv.path[i].n == 0 and mv.goal[i] < 0 then
        w.state[i] = C.ST_IDLE
    end
end

-- ── SPEC §17.6 정찰 ─────────────────────────────────────────────────────────

--- 미탐험 클러스터의 중심, **클러스터 번호 오름차순**.
--
--    정찰병이 죽으면 다음 유닛이 목록의 다음 항목부터 이어 간다 — 목록이
--    결정론적이어야 그 이어받기가 세 언어에서 같다.
function M.scout_targets(m, fog, p)
    local out = {n = 0}
    local cw = floor((m.w + C.CLUSTER - 1) / C.CLUSTER)
    local ch = floor((m.h + C.CLUSTER - 1) / C.CLUSTER)
    for cy = 0, ch - 1 do
        for cx = 0, cw - 1 do
            local seen = false
            local ylim = (cy + 1) * C.CLUSTER
            if m.h < ylim then ylim = m.h end
            local xlim = (cx + 1) * C.CLUSTER
            if m.w < xlim then xlim = m.w end
            for y = cy * C.CLUSTER, ylim - 1 do
                for x = cx * C.CLUSTER, xlim - 1 do
                    if fog.explored[p][y * m.w + x] ~= 0 then
                        seen = true
                        break
                    end
                end
                if seen then break end
            end
            if not seen then
                out[out.n] = {[0] = cx * C.CLUSTER + floor(C.CLUSTER / 2),
                              [1] = cy * C.CLUSTER + floor(C.CLUSTER / 2), n = 2}
                out.n = out.n + 1
            end
        end
    end
    return out
end

return M
