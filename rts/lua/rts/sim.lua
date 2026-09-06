-- 시뮬레이션 — 유일한 진입점 (SPEC §18).
--
--    **상태를 바꾸는 함수는 `step` 하나뿐이다.** 렌더는 읽기만 하고, UI 는 명령을
--    만들 뿐이며, AI 조차 같은 자료형의 명령으로 말한다. 이 규율이 19부(락스텝)와
--    20부(리플레이)의 전제 전부다.
--
--    틱의 아홉 단계 순서는 명세다. 바꾸면 골든이 통째로 틀어진다.

local AI = require('rts.ai')
local CB = require('rts.combat')
local C = require('rts.const')
local E = require('rts.econ')
local F = require('rts.fixed')
local FL = require('rts.flow')
local FG = require('rts.fog')
local MO = require('rts.move')
local R = require('rts.rng')
local SEL = require('rts.select')
local S = require('rts.spatial')
local T = require('rts.tmap')

local M = {}
local floor = math.floor

-- ── §18.3 이벤트 종류 ───────────────────────────────────────────────────────
M.EV_SPAWN, M.EV_DIE, M.EV_HIT, M.EV_BUILD_DONE = 0, 1, 2, 3
M.EV_MINE, M.EV_UNLOAD, M.EV_ORDER, M.EV_WIN, M.EV_MESSAGE = 4, 5, 6, 7, 8
local EV_SPAWN, EV_DIE, EV_HIT, EV_BUILD_DONE = 0, 1, 2, 3
local EV_UNLOAD, EV_ORDER, EV_WIN, EV_MESSAGE = 5, 6, 7, 8

-- ── §18.5 트리거 ────────────────────────────────────────────────────────────
M.CT_TICK_GE, M.CT_UNIT_COUNT, M.CT_BUILDING_DESTROYED = 0, 1, 2
M.CT_AREA_ENTERED, M.CT_CREDITS_GE = 3, 4
M.AC_SPAWN, M.AC_MESSAGE, M.AC_WIN, M.AC_LOSE, M.AC_REVEAL = 0, 1, 2, 3, 4
M.CMP_GE, M.CMP_LE, M.CMP_EQ = 0, 1, 2
local CT_TICK_GE, CT_UNIT_COUNT, CT_BUILDING_DESTROYED = 0, 1, 2
local CT_AREA_ENTERED, CT_CREDITS_GE = 3, 4
local AC_SPAWN, AC_MESSAGE, AC_WIN, AC_LOSE, AC_REVEAL = 0, 1, 2, 3, 4
local CMP_GE, CMP_LE = 0, 1

M.AI_PERIOD = 15                 -- §17.5 빌드 오더 평가 주기
local AI_PERIOD = 15

M.CMD = {MOVE = SEL.MOVE, AMOVE = SEL.ATTACK_MOVE, ATTACK = SEL.ATTACK,
         HARVEST = SEL.HARVEST, STOP = SEL.STOP, HOLD = SEL.HOLD,
         BUILD = SEL.BUILD, TRAIN = SEL.TRAIN}

--- 트리거 인자는 길이가 들쭉날쭉하다 — 없는 칸은 0 으로 읽는다.
local function at(t, k)
    if k < t.n then return t[k] end
    return 0
end

--- 0-기반 튜플 배열의 사전식 비교. 파이썬의 튜플 < 와 같다.
local function tuple_lt(a, b)
    local n = a.n < b.n and a.n or b.n
    for k = 0, n - 1 do
        if a[k] ~= b[k] then return a[k] < b[k] end
    end
    return a.n < b.n
end
M.tuple_lt = tuple_lt

--- 0-기반 배열을 사전식으로 제자리 정렬.
local function sort_tuples(arr)
    local tmp = {}
    for k = 0, arr.n - 1 do tmp[k + 1] = arr[k] end
    table.sort(tmp, tuple_lt)
    for k = 0, arr.n - 1 do arr[k] = tmp[k + 1] end
end
M.sort_tuples = sort_tuples

local function tup(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end
M.tup = tup

-- ── §18.6 시나리오 스크립트 ─────────────────────────────────────────────────
local Script = {}
Script.__index = Script
M.Script = Script

function M.newscript()
    return setmetatable({ticks = 0, players = 0, lines = {n = 0}}, Script)
end

--- `#` 로 시작하는 줄은 주석이다.
function M.parse_script(text)
    local sc = M.newscript()
    for raw in (text .. '\n'):gmatch('([^\n]*)\n') do
        local ln = raw:gsub('^%s+', ''):gsub('%s+$', '')
        if ln ~= '' and ln:sub(1, 1) ~= '#' and ln:sub(1, 4) ~= 'RTSS' then
            if ln:sub(1, 6) == 'ticks ' then
                sc.ticks = tonumber(ln:match('^ticks%s+(%-?%d+)'))
            elseif ln:sub(1, 8) == 'players ' then
                sc.players = tonumber(ln:match('^players%s+(%-?%d+)'))
            else
                local p = {n = 0}
                for tok in ln:gmatch('%S+') do
                    p[p.n] = tok
                    p.n = p.n + 1
                end
                sc.lines[sc.lines.n] = tup(tonumber(p[0]), tonumber(p[1]),
                                           p[2], p[3], tonumber(p[4]),
                                           tonumber(p[5]), tonumber(p[6]))
                sc.lines.n = sc.lines.n + 1
            end
        end
    end
    return sc
end

-- ── SPEC §18.4 상태 해시 ────────────────────────────────────────────────────

--- 파이썬 int() 와 같은 0 방향 절단. §19.4 의 주입 버그일 때만 실수가 들어온다.
local function trunc(v)
    if v >= 0 then return floor(v) end
    return -floor(-v)
end

--- FNV-1a 를 흘려 넣는다 — 바이트열을 통째로 만들지 않는 편이 세 언어 모두에서
--- 메모리와 시간이 덜 든다 (SPEC §18.4).
local Hash = {}
Hash.__index = Hash
M.Hash = Hash

function M.newhash()
    return setmetatable({h = F.FNV_OFFSET}, Hash)
end

function Hash:b1(v)
    -- 절단을 한 번 거치는 이유는 §19.4 의 주입 버그 때문이다. 그때만 prog·px·py
    -- 가 실수가 되고, 해시는 그 잘린 값을 그대로 본다.
    self.h = F.fnv1a_step(self.h, trunc(v) % 256)
end

function Hash:b2(v)
    v = trunc(v) % 65536                       -- 음수는 2의 보수로 접는다
    self:b1(floor(v / 256))
    self:b1(v % 256)
end

function Hash:b4(v)
    v = trunc(v) % 4294967296
    self:b2(floor(v / 65536))
    self:b2(v % 65536)
end

-- ── Sim ─────────────────────────────────────────────────────────────────────
local Sim = {}
Sim.__index = Sim
M.Sim = Sim

function M.new(m, seed, players, float_bug)
    players = players or 2
    local self = setmetatable({}, Sim)
    self.m = m
    self.players = players
    self.w = S.new(m.w, m.h)
    self.fog = FG.new(m.w, m.h)
    self.ec = E.new(m)
    self.mv = MO.new(self.w, m, float_bug)
    self.pj = CB.newprojectiles(m.w)
    self.rng = R.new(seed)
    self.orders = SEL.neworders()
    self.mem = {n = C.MAX_PLAYER}
    self.ai_enabled = {n = C.MAX_PLAYER}
    self.last_spawn = {n = C.MAX_PLAYER}
    self._had_building = {n = C.MAX_PLAYER}
    for p = 0, C.MAX_PLAYER - 1 do
        self.mem[p] = AI.newmemory(m.w, m.h)
        self.ai_enabled[p] = false
        self.last_spawn[p] = 0
        self._had_building[p] = false
    end
    self.ai_rules = nil                     -- nil 이면 §17.5 의 여섯 줄
    self.tick = 0
    self.events = {n = 0}
    self.triggers = {n = 0}
    self.fired = {n = 0}
    self.winner = -1
    self.loser = {n = 0}
    self.last_hit = {n = C.MAX_ENT}
    self.sight_at = {n = C.MAX_ENT}         -- 안개가 알고 있는 위치
    for i = 0, C.MAX_ENT - 1 do
        self.last_hit[i] = 0
        self.sight_at[i] = -1
    end
    self._map_hash = 0
    self._map_hash_version = -1
    self._fire = nil
    self._fire_version = -1
    return self
end
Sim.new = M.new

-- ── 생성·소멸 ───────────────────────────────────────────────────────────────
function Sim:spawn(p, kind, x, y)
    local h = self.w:spawn(p, kind, x, y)
    if h == 0 then
        return 0
    end
    local i = S.index(h)
    self.w.hp[i] = C.HP[kind]               -- 태어나는 것은 정격 hp 로
    self.mv:claim(i)
    self.fog:add_sight(p, x, y, C.SIGHT[kind])
    self.sight_at[i] = y * self.m.w + x
    if C.IS_BUILDING[kind] ~= 0 then
        self._had_building[p] = true
    else
        self.last_spawn[p] = h
    end
    if kind == C.HARV then
        self.w.state[i] = C.ST_SEEK
    end
    return h
end

--- §25.4 시작 조건. 골든 시나리오는 스크립트가 몰므로 AI 를 끈다 — 한 지갑을
--- 둘이 쓰면 서로의 건설을 굶긴다(§18.6).
function Sim:setup_start(ai)
    if ai == nil then ai = true end
    local lim = self.players < self.m.starts.n and self.players or self.m.starts.n
    for p = 0, lim - 1 do
        local sx, sy = self.m.starts[p][0], self.m.starts[p][1]
        self:spawn(p, C.HQ, sx - 1, sy - 1)
        for k = 0, C.START_HARV - 1 do
            local x, y = sx + 2, sy + 1 + k
            if not self.m:passable_terrain(x, y, C.MOVE_KIND[C.HARV]) then
                x, y = sx, sy + 2 + k
            end
            self:spawn(p, C.HARV, x, y)
        end
        self.ec.credits[p] = C.START_CREDITS
        self.ai_enabled[p] = ai
    end
    self.ec:recount_supply(self.w)
end

function Sim:add_trigger(cond, act, once)
    self.triggers[self.triggers.n] = {cond, act, once}
    self.triggers.n = self.triggers.n + 1
    self.fired[self.fired.n] = false
    self.fired.n = self.fired.n + 1
end

-- ── SPEC §18.2 틱의 아홉 단계 ───────────────────────────────────────────────
function Sim:step(orders)
    self.events = {n = 0}
    self.tick = self.tick + 1
    self:_check_sorted(orders)
    for k = 0, orders.n - 1 do              -- 1. 명령 적용
        self:_apply_order(orders[k])
    end
    self:_phase_ai()                        -- 2. AI
    self:_phase_econ()                      -- 3. 생산·경제
    self.mv:step()                          -- 4. 이동
    self:_phase_combat()                    -- 5. 전투
    self:_phase_death()                     -- 6. 사망
    self:_phase_sight()                     -- 7. 시야
    self:_phase_triggers()                  -- 8. 트리거·승패
    return self:state_hash()                -- 9. 상태 해시
end

function Sim:_check_sorted(orders)
    for k = 1, orders.n - 1 do
        if tuple_lt(orders[k], orders[k - 1]) then
            error('명령 목록이 정렬되어 있지 않다 (SPEC §18.1)')
        end
    end
end

-- ── 1단계 ───────────────────────────────────────────────────────────────────
function Sim:_apply_order(o)
    local p, issuer, kind, a, b, c = o[0], o[1], o[2], o[3], o[4], o[5]
    if not self.w:valid(issuer) then
        return
    end
    local i = S.index(issuer)
    if self.w.owner[i] ~= p then
        return                              -- 남의 유닛에 내린 명령은 무시
    end
    local w = self.w
    if kind == SEL.MOVE or kind == SEL.ATTACK_MOVE then
        if self.mv:order(i, a, b) then
            w.state[i] = C.ST_MOVE
            w.target[i] = 0
        end
    elseif kind == SEL.ATTACK then
        w.target[i] = c
        w.state[i] = C.ST_ATTACK
        if w:valid(c) then
            local j = S.index(c)
            self.mv:order(i, w.tx[j], w.ty[j])
        end
    elseif kind == SEL.HARVEST then
        if w.kind[i] == C.HARV then
            w.state[i] = C.ST_SEEK
        end
    elseif kind == SEL.STOP then
        self.mv:stop(i)
        self.orders:clear(i)
        w.state[i] = C.ST_IDLE
    elseif kind == SEL.HOLD then
        self.mv:stop(i)
        w.state[i] = C.ST_IDLE
    elseif kind == SEL.TRAIN then
        self.ec:enqueue(w, i, a)
    elseif kind == SEL.BUILD then
        self:_do_build(p, a, b, c)
    end
    self.events[self.events.n] = tup(EV_ORDER, p, issuer, kind)
    self.events.n = self.events.n + 1
end

--- §16.4 — 통과하면 그 자리에 즉시 엔티티가 생기고 짓기 시작한다.
function Sim:_do_build(p, kind, x, y)
    if C.IS_BUILDING[kind] == 0 then
        return false
    end
    if not self.ec:can_build(self.w, p, kind) then
        return false
    end
    if self.ec.credits[p] < C.COST[kind] then
        return false
    end
    if not self.ec:placeable(self.w, self.m, self.mv, kind, x, y, p) then
        self:_shove(p, kind, x, y)          -- §16.5 — 내 유닛이면 비키게 한다
        return false
    end
    self.ec.credits[p] = self.ec.credits[p] - C.COST[kind]      -- 선불
    local h = self:spawn(p, kind, x, y)
    if h == 0 then
        self.ec.credits[p] = self.ec.credits[p] + C.COST[kind]
        return false
    end
    local i = S.index(h)
    self.w.state[i] = C.ST_BUILD
    self.w.hp[i] = 1
    self.w.timer[i] = C.BUILD_TICKS[kind]
    return true
end

--- 발자국을 막은 내 유닛들에게 바깥으로 한 걸음 명령을 준다 (§16.5).
--
--    밀면서 동시에 짓지는 않는다 — 아직 그 칸에 선 유닛 위에 건물을 얹으면
--    불변식 R 이 깨진다. 다음 재시도에서 자리가 빈다.
function Sim:_shove(p, kind, x, y)
    local w, m = self.w, self.m
    local f = C.FOOT[kind]
    local cx, cy = x + floor(f / 2), y + floor(f / 2)
    for dy = 0, f - 1 do
        for dx = 0, f - 1 do
            local u, v = x + dx, y + dy
            if m:in_map(u, v) then
                local h = self.mv.resv[v * m.w + u]
                if w:valid(h) then
                    local j = S.index(h)
                    if w.owner[j] == p and C.IS_BUILDING[w.kind[j]] == 0 then
                        local out = F.atan8(w.tx[j] - cx, w.ty[j] - cy)
                        local pd = MO.push_dir(self.mv, j, F.fmod(out + 4, 8))
                        if pd ~= MO.STOP_DIR then
                            local t = (w.ty[j] + F.DY[pd]) * m.w
                                      + w.tx[j] + F.DX[pd]
                            self.mv.path[j] = {[0] = t, n = 1}
                            self.mv.goal[j] = t
                        end
                    end
                end
            end
        end
    end
end

-- ── 2단계 AI ────────────────────────────────────────────────────────────────
function Sim:_phase_ai()
    for p = 0, self.players - 1 do
        if self.ai_enabled[p] then
            self.mem[p]:update(self.w, self.fog, p)
            if self.tick % AI_PERIOD == 0 then
                self:_ai_decide(p)
            end
            for i = 1, C.MAX_ENT - 1 do
                if self.w.alive[i] == 1 and self.w.owner[i] == p
                   and C.IS_BUILDING[self.w.kind[i]] == 0 then
                    AI.unit_tick(self.w, i, self.m, self.mv, self.orders)
                end
            end
        end
    end
end

function Sim:_brushfire()
    if self._fire_version ~= self.m.version then
        self._fire = FL.brushfire(self.m, 0)
        self._fire_version = self.m.version
    end
    return self._fire
end

function Sim:_ai_decide(p)
    local act = AI.build_order(self.w, self.ec, self.mem[p], p, self.ai_rules)
    if act[0] == 'TRAIN' then
        self.ec:enqueue(self.w, act[2], act[1])
    elseif act[0] == 'BUILD' then
        local centre = self:_base_of(p)
        if centre == nil then return end
        local thr = AI.threat(self.w, self.fog, p, self.m)
        local spot = AI.best_placement(self.w, self.m, self.mv, self.ec,
                                       self:_brushfire(), thr, p, act[1], centre)
        if spot ~= nil then
            self:_do_build(p, act[1], spot[0], spot[1])
        end
    elseif act[0] == 'ATTACK' then
        local army = self:_army(p)
        for k = 0, army.n - 1 do
            local i = army[k]
            self.mv:order(i, act[1], act[2])
            self.w.state[i] = C.ST_MOVE
        end
    else                                    -- DEFEND (+ §17.6 정찰)
        local centre = self:_base_of(p)
        if centre == nil then return end
        local army = self:_army(p)
        local spots = AI.scout_targets(self.m, self.fog, p)
        for k = 0, army.n - 1 do
            local i = army[k]
            if self.w.state[i] == C.ST_IDLE and self.mv.path[i].n == 0 then
                if k == 0 and spots.n > 0 then
                    -- 첫 유닛 하나만 정찰. 이것이 없으면 적 기지를 영영 모르고
                    -- 빌드 오더의 다섯째 줄(전군 공격)이 발화하지 않는다.
                    self.mv:order(i, spots[0][0], spots[0][1])
                    self.w.state[i] = C.ST_MOVE
                else
                    self.mv:order(i, centre[0], centre[1])
                end
            end
        end
    end
end

function Sim:_base_of(p)
    for i = 1, C.MAX_ENT - 1 do
        if self.w.alive[i] == 1 and self.w.owner[i] == p
           and C.IS_BUILDING[self.w.kind[i]] == 1 then
            return {[0] = self.w.tx[i], [1] = self.w.ty[i], n = 2}
        end
    end
    return nil
end

function Sim:_army(p)
    local out = {n = 0}
    for i = 1, C.MAX_ENT - 1 do
        if self.w.alive[i] == 1 and self.w.owner[i] == p
           and C.IS_BUILDING[self.w.kind[i]] == 0
           and C.BASIC[self.w.kind[i]] > 0 then
            out[out.n] = i
            out.n = out.n + 1
        end
    end
    return out
end

-- ── 3단계 생산·경제 ─────────────────────────────────────────────────────────
function Sim:_phase_econ()
    local w = self.w
    for i = 1, C.MAX_ENT - 1 do             -- 건설 진행
        if w.alive[i] == 1 and C.IS_BUILDING[w.kind[i]] ~= 0
           and w.state[i] == C.ST_BUILD then
            local total = C.BUILD_TICKS[w.kind[i]]
            local done = total - w.timer[i]
            if done < 0 then done = 0 end
            w.hp[i] = 1 + floor(done * (C.HP[w.kind[i]] - 1) / total)
            w.timer[i] = w.timer[i] - 1
            if w.timer[i] <= 0 then
                w.timer[i] = 0
                w.hp[i] = C.HP[w.kind[i]]
                w.state[i] = C.ST_IDLE
                self.events[self.events.n] = tup(EV_BUILD_DONE, w.owner[i],
                                                 w:handle(i), w.kind[i])
                self.events.n = self.events.n + 1
            end
        end
    end
    local prod = self.ec:step_production(w)
    for k = 0, prod.n - 1 do
        local bi, kind = prod[k][1], prod[k][2]
        local spot = self:_free_near(bi, kind)
        if spot ~= nil then
            local h = self:spawn(w.owner[bi], kind, spot[0], spot[1])
            if h ~= 0 then
                self.events[self.events.n] = tup(EV_SPAWN, w.owner[bi], h, kind)
                self.events.n = self.events.n + 1
            end
        end
    end
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] == 1 and w.kind[i] == C.HARV then
            local before = self.ec.credits[w.owner[i]]
            self.ec:harvest_tick(w, i, self.m, self.mv)
            if self.ec.credits[w.owner[i]] > before then
                self.events[self.events.n] =
                    tup(EV_UNLOAD, w.owner[i], w:handle(i),
                        self.ec.credits[w.owner[i]] - before)
                self.events.n = self.events.n + 1
            end
        end
    end
    self.ec:recount_supply(w)
end

--- 건물 둘레에서 빈 칸 하나. y 오름차순, 같은 y 안에서 x 오름차순.
function Sim:_free_near(bi, kind)
    local w, m = self.w, self.m
    local mk = C.MOVE_KIND[kind]
    local f = C.FOOT[w.kind[bi]]
    for r = 1, 3 do
        for y = w.ty[bi] - r, w.ty[bi] + f + r - 1 do
            for x = w.tx[bi] - r, w.tx[bi] + f + r - 1 do
                if m:passable_terrain(x, y, mk)
                   and self.mv.resv[y * m.w + x] == 0 then
                    return {[0] = x, [1] = y, n = 2}
                end
            end
        end
    end
    return nil
end

-- ── 5단계 전투 ──────────────────────────────────────────────────────────────
function Sim:_phase_combat()
    local w, m = self.w, self.m
    local pending = {n = 0}
    local function add(tgt, src, dmg)
        pending[pending.n] = tup(tgt, src, dmg)
        pending.n = pending.n + 1
    end
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] ~= 0 and w.hp[i] > 0 then
            local kind = w.kind[i]
            if C.BASIC[kind] ~= 0 then
                if w.cool[i] > 0 then
                    w.cool[i] = w.cool[i] - 1
                else
                    local tgt, approach = CB.pick_target(w, i, self.last_hit[i],
                                                         w.state[i] == C.ST_MOVE)
                    if tgt ~= 0 and not approach then
                        local j = S.index(tgt)
                        w.target[i] = tgt
                        local dmg = CB.roll_damage(self.rng, C.BASIC[kind],
                                                   C.PIERCE[kind],
                                                   C.ARMOUR[w.kind[j]])
                        w.cool[i] = C.RELOAD[kind]
                        if kind == C.ARCHER or kind == C.MORTAR then
                            local pk = (kind == C.MORTAR) and CB.ARC or CB.STRAIGHT
                            local sp = (kind == C.MORTAR) and 0 or CB.ARROW_SPEED
                            if not self.pj:launch(pk, w.px[i], w.py[i],
                                                  w.px[j], w.py[j], sp, tgt, dmg) then
                                add(tgt, w:handle(i), dmg)
                            end
                        else
                            add(tgt, w:handle(i), dmg)
                        end
                    end
                end
            end
        end
    end
    local hits = self.pj:step()
    for k = 0, hits.n - 1 do
        local tgt, dmg, dest, pkind = hits[k][1], hits[k][2], hits[k][3], hits[k][5]
        if pkind == CB.ARC then             -- 포물선만 스플래시 (아군도 맞는다)
            local sh = CB.splash_hits(w, dest % m.w, floor(dest / m.w), dmg)
            for q = 0, sh.n - 1 do
                add(sh[q][1], 0, sh[q][2])
            end
        elseif w:valid(tgt) then
            add(tgt, 0, dmg)
        end
    end
    sort_tuples(pending)
    for k = 0, pending.n - 1 do             -- **피해는 여기서 한꺼번에**
        local tgt, src, dmg = pending[k][0], pending[k][1], pending[k][2]
        if w:valid(tgt) then
            local j = S.index(tgt)
            w.hp[j] = w.hp[j] - dmg
            if src ~= 0 then
                self.last_hit[j] = src
            end
            self.events[self.events.n] = tup(EV_HIT, tgt, src, dmg)
            self.events.n = self.events.n + 1
        end
    end
end

-- ── 6단계 사망 ──────────────────────────────────────────────────────────────
function Sim:_phase_death()
    local w, m = self.w, self.m
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] ~= 0 and w.hp[i] <= 0 then
            self.events[self.events.n] = tup(EV_DIE, w.owner[i], w:handle(i),
                                             w.kind[i])
            self.events.n = self.events.n + 1
            local t = self.sight_at[i]      -- 안개가 아는 위치에서 반납한다
            if t >= 0 then
                self.fog:remove_sight(w.owner[i], t % m.w, floor(t / m.w),
                                      C.SIGHT[w.kind[i]])
                self.sight_at[i] = -1
            end
            local f = C.FOOT[w.kind[i]]
            local building = C.IS_BUILDING[w.kind[i]] == 1
            local cells = {n = 0}
            for dy = 0, f - 1 do
                for dx = 0, f - 1 do
                    cells[cells.n] = {w.tx[i] + dx, w.ty[i] + dy}
                    cells.n = cells.n + 1
                end
            end
            self.mv:unclaim(i)
            if building then
                for k = 0, cells.n - 1 do   -- 잔해를 남긴다
                    local x, y = cells[k][1], cells[k][2]
                    if m:in_map(x, y) then
                        m:set_terrain(x, y, T.RUBBLE)
                    end
                end
            end
            w:kill(w:handle(i))
        end
    end
end

-- ── 7단계 시야 ──────────────────────────────────────────────────────────────
function Sim:_phase_sight()
    local w, m = self.w, self.m
    for k = 0, self.mv.crossed.n - 1 do
        local i, _old, new = self.mv.crossed[k][1], self.mv.crossed[k][2],
                             self.mv.crossed[k][3]
        if w.alive[i] ~= 0 then             -- 6단계에서 이미 반납했다
            local r = C.SIGHT[w.kind[i]]
            local src = self.sight_at[i]
            if src >= 0 then
                self.fog:remove_sight(w.owner[i], src % m.w, floor(src / m.w), r)
            end
            self.fog:add_sight(w.owner[i], new % m.w, floor(new / m.w), r)
            self.sight_at[i] = new
        end
    end
end

-- ── 8단계 트리거·승패 ───────────────────────────────────────────────────────
function Sim:_phase_triggers()
    for k = 0, self.triggers.n - 1 do
        local cond, act, once = self.triggers[k][1], self.triggers[k][2],
                                self.triggers[k][3]
        if not (once and self.fired[k]) then
            if self:_cond(cond) then
                self:_act(act)
                if once then
                    self.fired[k] = true
                end
            end
        end
    end
    self:_check_victory()
end

function Sim:_cond(t)
    local w = self.w
    local kind = t[0]
    if kind == CT_TICK_GE then
        return self.tick >= at(t, 1)
    end
    if kind == CT_UNIT_COUNT then
        local p, uk, cmp_, n = at(t, 1), at(t, 2), at(t, 3), at(t, 4)
        local cnt = 0
        for i = 1, C.MAX_ENT - 1 do
            if w.alive[i] ~= 0 and w.owner[i] == p and w.kind[i] == uk then
                cnt = cnt + 1
            end
        end
        if cmp_ == CMP_GE then return cnt >= n end
        if cmp_ == CMP_LE then return cnt <= n end
        return cnt == n
    end
    if kind == CT_BUILDING_DESTROYED then
        return not self:_has_building(at(t, 1))
    end
    if kind == CT_AREA_ENTERED then
        local p, x, y, r = at(t, 1), at(t, 2), at(t, 3), at(t, 4)
        for i = 1, C.MAX_ENT - 1 do
            if w.alive[i] ~= 0 and w.owner[i] == p
               and C.IS_BUILDING[w.kind[i]] == 0
               and F.dinf(w.tx[i] - x, w.ty[i] - y) <= r then
                return true
            end
        end
        return false
    end
    if kind == CT_CREDITS_GE then
        return self.ec.credits[at(t, 1)] >= at(t, 2)
    end
    return false
end

function Sim:_act(t)
    local kind = t[0]
    if kind == AC_SPAWN then
        local h = self:spawn(at(t, 1), at(t, 2), at(t, 3), at(t, 4))
        if h ~= 0 then
            self.events[self.events.n] = tup(EV_SPAWN, at(t, 1), h, at(t, 2))
            self.events.n = self.events.n + 1
        end
    elseif kind == AC_MESSAGE then
        self.events[self.events.n] = tup(EV_MESSAGE, at(t, 1))
        self.events.n = self.events.n + 1
    elseif kind == AC_WIN then
        self:_declare(at(t, 1))
    elseif kind == AC_LOSE then
        local p = at(t, 1)
        local found = false
        for k = 0, self.loser.n - 1 do
            if self.loser[k] == p then found = true end
        end
        if not found then
            self.loser[self.loser.n] = p
            self.loser.n = self.loser.n + 1
        end
    elseif kind == AC_REVEAL then
        local x, y, r = at(t, 1), at(t, 2), at(t, 3)
        self.fog:add_sight(0, x, y, r)
        self.fog:remove_sight(0, x, y, r)   -- 탐험만 남기고 시야는 돌려준다
    end
end

function Sim:_has_building(p)
    for i = 1, C.MAX_ENT - 1 do
        if self.w.alive[i] == 1 and self.w.owner[i] == p
           and C.IS_BUILDING[self.w.kind[i]] == 1 then
            return true
        end
    end
    return false
end

function Sim:_declare(p)
    if self.winner < 0 then
        self.winner = p
        self.events[self.events.n] = tup(EV_WIN, p)
        self.events.n = self.events.n + 1
    end
end

--- 건물이 전부 파괴되면 패배. 남은 플레이어가 하나면 승리.
function Sim:_check_victory()
    if self.winner >= 0 then
        return
    end
    local alive = {n = 0}
    for p = 0, self.players - 1 do
        if self:_has_building(p) then
            alive[alive.n] = p
            alive.n = alive.n + 1
        elseif self._had_building[p] then
            local found = false
            for k = 0, self.loser.n - 1 do
                if self.loser[k] == p then found = true end
            end
            if not found then
                self.loser[self.loser.n] = p
                self.loser.n = self.loser.n + 1
            end
        end
    end
    if alive.n == 1 and self.loser.n > 0 then
        self:_declare(alive[0])
    end
end

-- ── SPEC §18.4 상태 해시 ────────────────────────────────────────────────────

--- 지형이 바뀔 때만 다시 계산한다. 캐시지만 상태의 순수 함수다.
function Sim:map_hash()
    if self._map_hash_version ~= self.m.version then
        local hh = M.newhash()
        for i = 0, self.m.terrain.n - 1 do hh:b1(self.m.terrain[i]) end
        for i = 0, self.m.pass_.n - 1 do hh:b1(self.m.pass_[i]) end
        self._map_hash = hh.h
        self._map_hash_version = self.m.version
    end
    return self._map_hash
end

function Sim:state_hash()
    local w = self.w
    local hh = M.newhash()
    hh:b4(self.tick)
    hh:b4(self.rng.s)
    for p = 0, C.MAX_PLAYER - 1 do
        hh:b4(self.ec.credits[p])
        hh:b2(self.ec.supply_used[p])
        hh:b2(self.ec.supply_cap[p])
    end
    for i = 1, C.MAX_ENT - 1 do
        hh:b1(w.alive[i])
        if w.alive[i] ~= 0 then
            hh:b1(w.owner[i])
            hh:b1(w.kind[i])
            hh:b1(w.tx[i])
            hh:b1(w.ty[i])
            hh:b2(w.hp[i])
            hh:b1(w.dir[i])
            hh:b1(w.state[i])
            hh:b4(w.px[i])
            hh:b4(w.py[i])
            hh:b2(w.target[i])
            hh:b2(w.load[i])
            hh:b4(w.prog[i])
            hh:b2(w.from_t[i])
            hh:b2(w.to_t[i])
            hh:b2(w.cool[i])
            hh:b2(w.timer[i])
        end
    end
    hh:b2(self.pj:n())
    for k = 0, self.pj:n() - 1 do
        hh:b4(self.pj.x[k])
        hh:b4(self.pj.y[k])
        hh:b4(self.pj.vx[k])
        hh:b4(self.pj.vy[k])
        hh:b2(self.pj.target[k])
        hh:b2(self.pj.dmg[k])
    end
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] ~= 0 and C.IS_BUILDING[w.kind[i]] ~= 0 then
            local q = self.ec.queue[i]
            hh:b1(q.n)
            for k = 0, q.n - 1 do hh:b1(q[k]) end
            hh:b2(self.ec.progress[i])
        end
    end
    local ores = {n = 0}
    for i = 0, self.ec.ore.n - 1 do
        if self.ec.ore[i] > 0 then
            ores[ores.n] = i
            ores.n = ores.n + 1
        end
    end
    hh:b2(ores.n)
    for k = 0, ores.n - 1 do
        hh:b2(ores[k])
        hh:b2(self.ec.ore[ores[k]])
    end
    hh:b4(self:map_hash())
    return hh.h
end

-- ── SPEC §18.6 선택자 ───────────────────────────────────────────────────────
function Sim:_select(p, sel)
    local w = self.w
    local out = {n = 0}
    if sel == 'N' then
        local h = self.last_spawn[p]
        if w:valid(h) then
            out[0] = h
            out.n = 1
        end
        return out
    end
    local tmp = {}
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] ~= 0 and w.owner[i] == p then
            local k = w.kind[i]
            if sel == 'A' then
                if C.IS_BUILDING[k] == 0 then tmp[#tmp + 1] = w:handle(i) end
            elseif sel == 'F' then
                if C.IS_BUILDING[k] == 0 and C.BASIC[k] > 0 then
                    tmp[#tmp + 1] = w:handle(i)
                end
            elseif sel:sub(1, 1) == 'K' then
                if k == tonumber(sel:sub(2)) then tmp[#tmp + 1] = w:handle(i) end
            end
        end
    end
    table.sort(tmp)
    out.n = #tmp
    for k = 1, #tmp do out[k - 1] = tmp[k] end
    return out
end

--- 스크립트도 사람과 똑같은 경로를 지난다 — 뒷문을 내지 않는다.
function Sim:script_orders(script, tick)
    local out = {n = 0}
    for k = 0, script.lines.n - 1 do
        local L = script.lines[k]
        if L[0] == tick then
            local sel = self:_select(L[1], L[2])
            for q = 0, sel.n - 1 do
                out[out.n] = tup(L[1], sel[q], M.CMD[L[3]], L[4], L[5], L[6])
                out.n = out.n + 1
            end
        end
    end
    sort_tuples(out)
    return out
end

return M
