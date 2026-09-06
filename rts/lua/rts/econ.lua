-- 경제 — 자원·채집기 FSM·생산 큐·기술 트리·인구 (SPEC §16).
--
--    생산은 **선불**이다. 큐에 넣는 순간 크레딧이 빠진다. 후불로 두면 "완성
--    시점에 돈이 없는" 상태가 생기고, 그 처리 규칙이 언어마다 미묘하게 갈릴
--    여지가 생긴다 — 결정론을 위해 게임 디자인을 고른 자리다.

local C = require('rts.const')
local F = require('rts.fixed')
local T = require('rts.tmap')

local M = {}
local floor = math.floor

M.ORE_PER_TILE = 500
M.LOAD_MAX = 100
M.MINE_PER_TICK = 5
M.UNLOAD_TICKS = 12
M.QUEUE_MAX = 5
M.SUPPLY_MAX = 100
M.BASE_R = 4                  -- §16.5 기지 반경 (체비셰프, 건물 원점 기준)
M.TOUCH_R = 1                 -- 채집기가 "닿았다"고 보는 거리
local ORE_PER_TILE, LOAD_MAX, MINE_PER_TICK = 500, 100, 5
local UNLOAD_TICKS, QUEUE_MAX, SUPPLY_MAX = 12, 5, 100
local BASE_R, TOUCH_R = 4, 1

-- §16.2 채집기 FSM 상태 — 번호는 const 가 소유한다(§17.1 의 표).
M.H_SEEK, M.H_TO_ORE, M.H_MINE = C.ST_SEEK, C.ST_TO_ORE, C.ST_MINE
M.H_TO_BASE, M.H_UNLOAD, M.H_IDLE = C.ST_TO_BASE, C.ST_UNLOAD, C.ST_IDLE
local H_SEEK, H_TO_ORE, H_MINE = C.ST_SEEK, C.ST_TO_ORE, C.ST_MINE
local H_TO_BASE, H_UNLOAD, H_IDLE = C.ST_TO_BASE, C.ST_UNLOAD, C.ST_IDLE

M.DEPOT = {[0] = C.HQ, C.REF, n = 2}      -- 자원 반납처 (§25.2)
local function is_depot(k)
    return k == C.HQ or k == C.REF
end
M.is_depot = is_depot

-- ── SPEC §16.3 수입률 (정리 16.1) ───────────────────────────────────────────

--- 왕복 d 타일, 속도 v(16.16 타일/틱)인 채집기 한 기의 주기 (틱).
--
--    세 항은 왕복 이동·채굴·반납이다. d 가 0 이어도 20 + 12 = 32틱이 든다 —
--    **정제소를 광맥에 붙여도 상한이 있다.**
function M.round_trip_ticks(d, v)
    return F.floordiv(F.fp(2 * d), v)
           + F.floordiv(LOAD_MAX, MINE_PER_TICK) + UNLOAD_TICKS
end

--- 크레딧/틱 × 10000. 나눗셈 한 번으로 끝내려고 정수 배율을 쓴다.
function M.income10000(d, v)
    return F.floordiv(LOAD_MAX * 10000, M.round_trip_ticks(d, v))
end

-- ── SPEC §16.6 기술 트리 = DAG (정리 16.2) ──────────────────────────────────

--- 칸(Kahn) 위상 정렬. 진입차수 0 은 **번호 오름차순**으로 꺼낸다.
--
--    순환이 있으면 nil 을 돌려준다 — 조용히 넘어가지 않는다. 기술 트리는
--    데이터이고, 데이터가 잘못되면 터지는 편이 낫다.
function M.topo_order(extra)
    local pre = {}
    for k = 0, C.KIND_COUNT - 1 do
        local t = {n = C.PREREQ[k].n}
        for j = 0, t.n - 1 do t[j] = C.PREREQ[k][j] end
        pre[k] = t
    end
    if extra ~= nil then
        for e = 0, extra.n - 1 do
            local k, p = extra[e][1], extra[e][2]
            pre[k][pre[k].n] = p
            pre[k].n = pre[k].n + 1
        end
    end
    local indeg = {}
    for k = 0, C.KIND_COUNT - 1 do indeg[k] = pre[k].n end
    local out = {n = 0}
    local done = {}
    for k = 0, C.KIND_COUNT - 1 do done[k] = 0 end
    while true do
        local pick = -1
        for k = 0, C.KIND_COUNT - 1 do     -- 오름차순 선형 탐색 — 16개다
            if done[k] == 0 and indeg[k] == 0 then
                pick = k
                break
            end
        end
        if pick < 0 then break end
        done[pick] = 1
        out[out.n] = pick
        out.n = out.n + 1
        for k = 0, C.KIND_COUNT - 1 do
            if done[k] == 0 then
                for j = 0, pre[k].n - 1 do
                    if pre[k][j] == pick then
                        indeg[k] = indeg[k] - 1
                        break
                    end
                end
            end
        end
    end
    if out.n ~= C.KIND_COUNT then
        return nil                         -- 남은 노드가 있으면 순환이다
    end
    return out
end

--- 플레이어별 크레딧·인구, 타일별 광맥, 건물별 생산 큐.
local Econ = {}
Econ.__index = Econ
M.Econ = Econ

function M.new(m)
    local self = setmetatable({}, Econ)
    local n = m.w * m.h
    self.ore = {n = n}
    for i = 0, n - 1 do
        self.ore[i] = (m.terrain[i] == T.ORE) and ORE_PER_TILE or 0
    end
    self.credits = {n = C.MAX_PLAYER}
    self.supply_used = {n = C.MAX_PLAYER}
    self.supply_cap = {n = C.MAX_PLAYER}
    for p = 0, C.MAX_PLAYER - 1 do
        self.credits[p] = 0
        self.supply_used[p] = 0
        self.supply_cap[p] = 0
    end
    self.queue = {n = C.MAX_ENT}
    self.progress = {n = C.MAX_ENT}
    self.ore_target = {n = C.MAX_ENT}
    for i = 0, C.MAX_ENT - 1 do
        self.queue[i] = {n = 0}
        self.progress[i] = 0
        self.ore_target[i] = -1
    end
    return self
end
Econ.new = M.new

-- ── SPEC §16.1 자원 ─────────────────────────────────────────────────────────

--- **도달 가능한** 광맥 중 d83 최소, 동점이면 타일 번호 오름차순. 없으면 −1.
--
--    도달 가능 판정을 빼면 채집기가 바위 건너편 광맥을 잡고 §8.6 의 대체
--    목표가 제자리를 돌려주어 영원히 선다(SPEC §16.2). 연결 성분은 지형
--    version 마다 한 번만 계산되므로 여기서 불러도 싸다.
function Econ:nearest_ore(m, x, y, kind)
    kind = kind or 0
    local lab = m:labels(kind)
    local here = m:in_map(x, y) and lab[y * m.w + x] or -1
    local best, bd = -1, -1
    for i = 0, m.w * m.h - 1 do
        if self.ore[i] > 0 and not (here >= 0 and lab[i] ~= here) then
            local d = F.d83(i % m.w - x, floor(i / m.w) - y)
            if bd < 0 or d < bd then
                bd, best = d, i
            end
        end
    end
    return best
end

--- 캔 양을 돌려준다. 다 캐면 그 칸은 모래가 되고 지형 version 이 오른다.
function Econ:mine(m, tile, amount)
    local got = self.ore[tile]
    if got > amount then got = amount end
    self.ore[tile] = self.ore[tile] - got
    if self.ore[tile] <= 0 and m.terrain[tile] == T.ORE then
        m:set_terrain(tile % m.w, floor(tile / m.w), T.SAND)
    end
    return got
end

-- ── SPEC §16.4 생산 큐 ──────────────────────────────────────────────────────
function Econ:enqueue(w, bi, kind)
    local p = w.owner[bi]
    if self.queue[bi].n >= QUEUE_MAX then
        return false
    end
    if not self:can_build(w, p, kind) then
        return false
    end
    if self.credits[p] < C.COST[kind] then
        return false
    end
    if C.IS_BUILDING[kind] == 0 then
        if self.supply_used[p] + self:reserved(w, p) + C.POP[kind]
           > self.supply_cap[p] then
            return false            -- 큐에 든 것도 인구를 먹는다 (§16.7)
        end
    end
    self.credits[p] = self.credits[p] - C.COST[kind]      -- 선불
    self.queue[bi][self.queue[bi].n] = kind
    self.queue[bi].n = self.queue[bi].n + 1
    return true
end

--- 큐에 들어 있는 유닛이 예약한 인구. 이것을 빼면 상한이 헐거워진다.
function Econ:reserved(w, p)
    local n = 0
    for bi = 1, C.MAX_ENT - 1 do
        if w.alive[bi] ~= 0 and w.owner[bi] == p then
            local q = self.queue[bi]
            for k = 0, q.n - 1 do
                if C.IS_BUILDING[q[k]] == 0 then
                    n = n + C.POP[q[k]]
                end
            end
        end
    end
    return n
end

--- 환불은 100 %. 이 덱의 규칙이며, 부분 환불은 반올림 규칙을 하나 더 만든다.
function Econ:cancel(w, bi, k)
    local q = self.queue[bi]
    if k < 0 or k >= q.n then
        return 0
    end
    local kind = q[k]
    local nq = {n = 0}
    for j = 0, q.n - 1 do
        if j ~= k then
            nq[nq.n] = q[j]
            nq.n = nq.n + 1
        end
    end
    self.queue[bi] = nq
    if k == 0 then
        self.progress[bi] = 0
    end
    self.credits[w.owner[bi]] = self.credits[w.owner[bi]] + C.COST[kind]
    return C.COST[kind]
end

--- 한 틱. 완성된 (건물 인덱스, 종류) 목록을 인덱스 오름차순으로.
function Econ:step_production(w)
    local done = {n = 0}
    for bi = 1, C.MAX_ENT - 1 do
        local q = self.queue[bi]
        if w.alive[bi] ~= 0 and q.n > 0 then
            local kind = q[0]
            self.progress[bi] = self.progress[bi] + 1
            if self.progress[bi] >= C.BUILD_TICKS[kind] then
                self.progress[bi] = 0
                local nq = {n = q.n - 1}
                for j = 1, q.n - 1 do nq[j - 1] = q[j] end
                self.queue[bi] = nq
                done[done.n] = {bi, kind}
                done.n = done.n + 1
            end
        end
    end
    return done
end

--- 선행이 **완성된 채 살아 있는지** 본다. 병영이 부서지면 보병을 못 뽑는다.
function Econ:can_build(w, p, kind)
    local pre = C.PREREQ[kind]
    for k = 0, pre.n - 1 do
        local need = pre[k]
        local found = false
        for j = 1, C.MAX_ENT - 1 do
            if w.alive[j] == 1 and w.owner[j] == p and w.kind[j] == need
               and w.hp[j] > 0 then
                found = true
                break
            end
        end
        if not found then
            return false
        end
    end
    return true
end

-- ── SPEC §16.5 배치 판정 ────────────────────────────────────────────────────

--- 발자국 전체가 건설 가능 지형이고 비어 있고, 기지에서 4타일 안.
function Econ:placeable(w, m, mv, kind, x, y, p)
    local f = C.FOOT[kind]
    for dy = 0, f - 1 do
        for dx = 0, f - 1 do
            local u, v = x + dx, y + dy
            if not m:in_map(u, v) then
                return false
            end
            local i = v * m.w + u
            if F.bit(m.pass_[i], T.BUILD_BIT) ~= 1 then
                return false
            end
            if mv.resv[i] ~= 0 then
                return false
            end
        end
    end
    local near = false
    local any_own = false
    for j = 1, C.MAX_ENT - 1 do
        if w.alive[j] == 1 and w.owner[j] == p
           and C.IS_BUILDING[w.kind[j]] == 1 then
            any_own = true
            if F.dinf(w.tx[j] - x, w.ty[j] - y) <= BASE_R then
                near = true
                break
            end
        end
    end
    return near or not any_own                 -- 첫 건물은 면제
end

-- ── SPEC §16.7 인구 ─────────────────────────────────────────────────────────

--- 유닛은 먹고 건물은 준다. 상한 100. 매 틱 전수로 세도 256칸이다.
function Econ:recount_supply(w)
    for p = 0, C.MAX_PLAYER - 1 do
        self.supply_used[p] = 0
        self.supply_cap[p] = 0
    end
    for j = 1, C.MAX_ENT - 1 do
        if w.alive[j] ~= 0 and w.hp[j] > 0 then
            local p = w.owner[j]
            if p < C.MAX_PLAYER then
                if C.IS_BUILDING[w.kind[j]] ~= 0 then
                    self.supply_cap[p] = self.supply_cap[p] + C.POP[w.kind[j]]
                else
                    self.supply_used[p] = self.supply_used[p] + C.POP[w.kind[j]]
                end
            end
        end
    end
    for p = 0, C.MAX_PLAYER - 1 do
        if self.supply_cap[p] > SUPPLY_MAX then
            self.supply_cap[p] = SUPPLY_MAX
        end
    end
end

-- ── SPEC §16.2 채집기 FSM ───────────────────────────────────────────────────

--- 건물 발자국의 어느 칸에라도 한 칸 안으로 붙었는가.
function Econ:_touching(w, i, bi)
    local f = C.FOOT[w.kind[bi]]
    local dx = 0
    if w.tx[i] < w.tx[bi] then
        dx = w.tx[bi] - w.tx[i]
    elseif w.tx[i] > w.tx[bi] + f - 1 then
        dx = w.tx[i] - (w.tx[bi] + f - 1)
    end
    local dy = 0
    if w.ty[i] < w.ty[bi] then
        dy = w.ty[bi] - w.ty[i]
    elseif w.ty[i] > w.ty[bi] + f - 1 then
        dy = w.ty[i] - (w.ty[bi] + f - 1)
    end
    return F.dinf(dx, dy) <= TOUCH_R
end

function Econ:_nearest_depot(w, i)
    local best, bd = 0, -1
    for j = 1, C.MAX_ENT - 1 do
        if w.alive[j] ~= 0 and w.owner[j] == w.owner[i]
           and is_depot(w.kind[j]) and w.hp[j] > 0 then
            local d = F.d83(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i])
            if bd < 0 or d < bd then
                bd, best = d, w:handle(j)
            end
        end
    end
    return best
end

--- 건물 발자국을 둘러싼 고리에서 채집기가 붙을 칸 (SPEC §16.2).
--
--    건물 원점으로 그냥 명령하면 §8.6 의 대체 목표가 "건물 반대편"이나 심지어
--    "지금 서 있는 칸"을 고를 수 있다 — d83 동점에서 타일 번호가 작은 쪽이
--    이기기 때문이다. 그러면 채집기가 적재를 든 채 굳는다.
function Econ:dock(w, m, mv, i, bi)
    local kind = C.MOVE_KIND[w.kind[i]]
    local f = C.FOOT[w.kind[bi]]
    for pass = 0, 1 do
        local ignore_resv = (pass == 1)
        local best = nil
        local bd, bt = -1, -1
        for dy = -1, f do
            for dx = -1, f do
                if not (dx >= 0 and dx < f and dy >= 0 and dy < f) then
                    -- 발자국 내부는 도크가 아니다
                    local x, y = w.tx[bi] + dx, w.ty[bi] + dy
                    if m:passable_terrain(x, y, kind) then
                        local t = y * m.w + x
                        local free = ignore_resv or mv.resv[t] == 0
                                     or mv.resv[t] == w:handle(i)
                        if free then
                            local d = F.d83(x - w.tx[i], y - w.ty[i])
                            if bd < 0 or d < bd or (d == bd and t < bt) then
                                best = {[0] = x, [1] = y, n = 2}
                                bd, bt = d, t
                            end
                        end
                    end
                end
            end
        end
        if best ~= nil then
            return best
        end
    end
    return nil
end

--- 이동이 포기된 상태 — §13.3 이 24틱 만에 명령을 버렸다는 뜻이다.
function Econ:_stuck(w, mv, i)
    return mv.goal[i] < 0 and mv.path[i].n == 0 and w.prog[i] == 0
end

--- 채집기 한 기의 한 틱. sim 의 3단계에서 핸들 오름차순으로 부른다.
function Econ:harvest_tick(w, i, m, mv)
    local st = w.state[i]
    local p = w.owner[i]
    if st == H_SEEK then
        local tile = self:nearest_ore(m, w.tx[i], w.ty[i], C.MOVE_KIND[w.kind[i]])
        if tile < 0 then
            w.state[i] = H_IDLE                -- 캘 것이 없으면 멈춘다
            return
        end
        self.ore_target[i] = tile
        mv:order(i, tile % m.w, floor(tile / m.w))
        w.state[i] = H_TO_ORE
        return
    end
    if st == H_TO_ORE then
        local t = self.ore_target[i]
        if t < 0 or self.ore[t] <= 0 then
            w.state[i] = H_SEEK
            return
        end
        if F.dinf(t % m.w - w.tx[i], floor(t / m.w) - w.ty[i]) <= TOUCH_R then
            w.state[i] = H_MINE
        elseif self:_stuck(w, mv, i) then
            mv:order(i, t % m.w, floor(t / m.w))  -- 길막에 포기했으면 다시 건다
        end
        return
    end
    if st == H_MINE then
        local room = LOAD_MAX - w.load[i]
        local want = MINE_PER_TICK < room and MINE_PER_TICK or room
        local got = self:mine(m, self.ore_target[i], want)
        w.load[i] = w.load[i] + got
        if w.load[i] >= LOAD_MAX then
            local h = self:_nearest_depot(w, i)
            if h == 0 then
                return              -- 반납처가 없으면 실어 둔 채 기다린다
            end
            w.target[i] = h
            local bi = floor(h / 256)
            local d = self:dock(w, m, mv, i, bi)
            if d ~= nil then
                mv:order(i, d[0], d[1])
            end
            w.state[i] = H_TO_BASE
        elseif got == 0 then
            w.state[i] = H_SEEK                -- 칸이 말랐다
        end
        return
    end
    if st == H_TO_BASE then
        local h = w.target[i]
        if not w:valid(h) then
            w.state[i] = (w.load[i] < LOAD_MAX) and H_MINE or H_TO_BASE
            w.target[i] = self:_nearest_depot(w, i)
            if w.target[i] == 0 then
                w.state[i] = H_SEEK
            end
            return
        end
        local bi = floor(h / 256)
        if self:_touching(w, i, bi) then
            w.state[i] = H_UNLOAD
            w.timer[i] = UNLOAD_TICKS
        elseif self:_stuck(w, mv, i) then
            local d = self:dock(w, m, mv, i, bi)
            if d ~= nil then
                mv:order(i, d[0], d[1])
            end
        end
        return
    end
    if st == H_UNLOAD then
        w.timer[i] = w.timer[i] - 1
        if w.timer[i] <= 0 then
            self.credits[p] = self.credits[p] + w.load[i]
            w.load[i] = 0
            w.state[i] = H_SEEK
        end
        return
    end
end

return M
