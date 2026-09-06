-- 전투 — 피해·표적·투사체·스플래시·란체스터 (SPEC §15).
--
--    피해 공식은 워크래프트 II 의 공식 문서를 따랐다(§15.2). 다만 "50 %에서
--    100 % 사이"의 **반올림 방향**은 블리자드 문서에 없고 팬 사이트의 역산이
--    출처다. 하한 1(방어가 아무리 높아도 피해 1)은 이 덱의 규칙이다.
--    16부는 이 구분을 그대로 적는다 — 어디까지가 문서이고 어디부터가 우리 규칙인지.

local C = require('rts.const')
local F = require('rts.fixed')

local M = {}
local floor = math.floor

M.STRAIGHT, M.ARC = 0, 1
local STRAIGHT, ARC = 0, 1
M.G = 1638                      -- 0.025 px/틱², 16.16
M.ARROW_SPEED = 4 * 65536       -- 화살·총알 4 px/틱 (§15.3)
M.ARC_MIN_TICKS = 6
M.ARC_DIV = 24
M.SPLASH_RINGS = 3
local G, ARC_MIN_TICKS, ARC_DIV, SPLASH_RINGS = 1638, 6, 24, 3

-- ── SPEC §15.2 피해 공식 ────────────────────────────────────────────────────

--- 최대 피해 = 기본 − 방어 + 관통, 하한 1.
--
--    하한이 없으면 방어력이 높은 유닛은 **절대 죽지 않는다**. 이 하한은
--    블리자드 문서에 없는 이 덱의 규칙이다.
function M.max_damage(basic, pierce, armour)
    local mx = basic - armour + pierce
    return mx < 1 and 1 or mx
end

--- 최대치의 50 %, 올림. 올림이라는 부분은 2차 출처다(§15.2).
function M.damage_lo(mx)
    return F.floordiv(mx + 1, 2)
end

function M.roll_damage(rng, basic, pierce, armour)
    local mx = M.max_damage(basic, pierce, armour)
    local lo = M.damage_lo(mx)
    return lo + rng:roll(mx - lo + 1)
end

--- E[dmg] × 100 (정리 15.1). 정수만 쓰려고 100배로 둔다.
function M.expect100(basic, pierce, armour)
    local mx = M.max_damage(basic, pierce, armour)
    return (M.damage_lo(mx) + mx) * 50
end

-- ── SPEC §15.1 사거리와 표적 선택 ───────────────────────────────────────────

--- 체비셰프 거리 — 8방향 격자에서 '몇 걸음 안'과 정확히 같다.
function M.in_range(w, i, j)
    return F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]) <= C.RANGE[w.kind[i]]
end
local in_range = M.in_range

local function enemy(w, i, j)
    return w.alive[j] == 1 and w.owner[j] ~= w.owner[i] and w.hp[j] > 0
end
M._enemy = enemy

--- 사거리 안 적 중 d83 최소, 동점이면 핸들 오름차순.
--
--    동점 규칙이 명세인 이유는 대칭 맵에서 동점이 흔하기 때문이다. 두 기계가
--    다른 표적을 고르면 그 틱부터 상태가 갈린다.
local function nearest(w, i, reach)
    local best = 0
    local bd = -1
    for j = 1, C.MAX_ENT - 1 do
        if enemy(w, i, j) then
            local d = F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j])
            if d <= reach then
                local s = F.d83(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j])
                if bd < 0 or s < bd then      -- 핸들 오름차순으로 훑으므로
                    bd = s                    -- 등호를 빼면 작은 핸들이 이긴다
                    best = w:handle(j)
                end
            end
        end
    end
    return best
end
M._nearest = nearest

--- (표적 핸들, 접근이 필요한가). 규칙 순서는 §15.1 그대로다.
function M.pick_target(w, i, last_hitter, attack_move)
    if C.BASIC[w.kind[i]] == 0 then
        return 0, false                -- 채집기와 비무장 건물은 쏘지 않는다
    end
    local reach = C.RANGE[w.kind[i]]
    local cur = w.target[i]
    if w:valid(cur) then
        local j = floor(cur / 256)
        if enemy(w, i, j) and in_range(w, i, j) then
            return cur, false          -- 1) 표적 유지 — 흔들리지 않는다
        end
    end
    if w:valid(last_hitter) then
        local j = floor(last_hitter / 256)
        if enemy(w, i, j) and in_range(w, i, j) then
            return last_hitter, false  -- 2) 나를 때린 적
        end
    end
    local h = nearest(w, i, reach)     -- 3) 가장 가까운 적
    if h ~= 0 then
        return h, false
    end
    if attack_move then                -- 4) ATTACK_MOVE 만 두 칸 더 본다
        h = nearest(w, i, reach + 2)
        if h ~= 0 then
            return h, true
        end
    end
    return 0, false
end

-- ── SPEC §15.5 스플래시 ─────────────────────────────────────────────────────

--- 링 단위 감쇠 — 0링 전액, 1링 1/2, 2링 1/4, 그 밖은 0. 나눗셈은 내림.
function M.splash_damage(dmg, ring)
    if ring >= SPLASH_RINGS then
        return 0
    end
    return F.floordiv(dmg, 2 ^ ring)
end

--- (핸들, 피해) 목록, 핸들 오름차순. **아군도 맞는다**.
--
--    아군 오사는 AI 의 제약이다(§17). 같은 유닛이 두 링에 걸치는 일은 없다 —
--    유닛의 대표 타일 하나로 판정하기 때문이다.
function M.splash_hits(w, tx, ty, dmg)
    local out = {n = 0}
    for j = 1, C.MAX_ENT - 1 do
        if w.alive[j] ~= 0 and w.hp[j] > 0 then
            local ring = F.dinf(w.tx[j] - tx, w.ty[j] - ty)
            local d = M.splash_damage(dmg, ring)
            if d > 0 then
                out[out.n] = {w:handle(j), d}
                out.n = out.n + 1
            end
        end
    end
    return out
end

-- ── SPEC §15.3·15.4 투사체 ──────────────────────────────────────────────────

--- SoA 로 담는다 — 상태 해시(§18.4)가 배열 순서로 자동 고정되기 때문이다.
local Projectiles = {}
Projectiles.__index = Projectiles
M.Projectiles = Projectiles

local PFIELDS = {'x', 'y', 'vx', 'vy', 'ttl', 'target', 'dmg', 'kind', 'dest'}
M.PFIELDS = PFIELDS

function M.newprojectiles(map_w)
    local self = setmetatable({map_w = map_w, count = 0}, Projectiles)
    for _, f in ipairs(PFIELDS) do
        self[f] = {}
    end
    return self
end
Projectiles.new = M.newprojectiles

function Projectiles:n()
    return self.count
end

function Projectiles:_tile(x, y)
    return F.floordiv(F.fp_floor(y), C.TILE) * self.map_w
           + F.floordiv(F.fp_floor(x), C.TILE)
end

--- 좌표는 전부 16.16 픽셀. 같은 칸이면 발사하지 않는다(즉시 명중).
--
--    **표적을 쫓지 않는다.** 발사 시점의 위치로 날아가므로 빠른 유닛은 화살을
--    피할 수 있다 — 이것도 이 덱의 규칙이고, 유도 변형은 16부에서 나란히
--    비교한다.
function Projectiles:launch(kind, x0, y0, x1, y1, speed, target, dmg)
    local dx = F.fp_floor(x1) - F.fp_floor(x0)
    local dy = F.fp_floor(y1) - F.fp_floor(y0)
    local d = F.isqrt(dx * dx + dy * dy)
    if d == 0 then
        return false
    end
    local vx, vy, ttl
    if kind == ARC then
        local t = ARC_MIN_TICKS
        if F.floordiv(d, ARC_DIV) > t then
            t = F.floordiv(d, ARC_DIV)
        end
        vx = F.fp_div(x1 - x0, F.fp(t))
        vy = F.fp_div(y1 - y0, F.fp(t))
             - F.fp_mul(G, F.fp_div(F.fp(t), F.fp(2)))
        ttl = t
    else
        vx = F.fp_mul(F.fp_div(F.fp(dx), F.fp(d)), speed)
        vy = F.fp_mul(F.fp_div(F.fp(dy), F.fp(d)), speed)
        ttl = F.floordiv(F.fp(d), speed) + 2
    end
    local k = self.count
    self.x[k], self.y[k] = x0, y0
    self.vx[k], self.vy[k] = vx, vy
    self.ttl[k] = ttl
    self.target[k] = target
    self.dmg[k] = dmg
    self.kind[k] = kind
    self.dest[k] = self:_tile(x1, y1)
    self.count = k + 1
    return true
end

--- 한 틱. 명중한 것을 (핸들, 피해, 착탄 타일, 착탄 y, 종류) 로 돌려주고 지운다.
--
--    마지막 칸이 종류인 이유는 sim 이 포물선 명중에만 스플래시(§15.5)를
--    적용해야 하기 때문이다.
function Projectiles:step()
    local hits = {n = 0}
    local keep = {}
    local nkeep = 0
    for k = 0, self.count - 1 do
        if self.kind[k] == ARC then
            self.vy[k] = self.vy[k] + G       -- 수직은 중력만, 수평은 등속
        end
        self.x[k] = self.x[k] + self.vx[k]
        self.y[k] = self.y[k] + self.vy[k]
        self.ttl[k] = self.ttl[k] - 1
        if self:_tile(self.x[k], self.y[k]) == self.dest[k] or self.ttl[k] <= 0 then
            hits[hits.n] = {self.target[k], self.dmg[k], self.dest[k],
                            self.y[k], self.kind[k]}
            hits.n = hits.n + 1
        else
            nkeep = nkeep + 1
            keep[nkeep] = k
        end
    end
    if nkeep ~= self.count then
        for _, name in ipairs(PFIELDS) do
            local a = self[name]
            local b = {}
            for q = 1, nkeep do b[q - 1] = a[keep[q]] end
            self[name] = b
        end
        self.count = nkeep
    end
    return hits
end

-- ── SPEC §15.6 란체스터 ─────────────────────────────────────────────────────

--- 정수 이산 시뮬. 폐형해(정리 15.4)는 엔진이 아니라 gen_prim 이 계산한다.
--
--    종료 조건이 `>= FP_ONE` 인 것이 중요하다. `> 0` 으로 두면 A 가 0.5 인
--    상태에서 감소량이 내림으로 0 이 되어 영원히 돌지 않는다 — 골든을 처음
--    만들 때 이 무한 루프에 걸렸다.
function M.lanchester_sim(a0, b0, alpha, beta)
    local a, b, t = F.fp(a0), F.fp(b0), 0
    while a >= F.FP_ONE and b >= F.FP_ONE and t < 10000 do
        local da = F.fp_mul(beta, b)
        local db = F.fp_mul(alpha, a)
        a = a - da
        b = b - db
        if a < 0 then a = 0 end
        if b < 0 then b = 0 end
        t = t + 1
    end
    return t, F.fp_floor(a), F.fp_floor(b)
end

return M
