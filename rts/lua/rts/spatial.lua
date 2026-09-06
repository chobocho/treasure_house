-- 엔티티와 공간 분할 — SoA·세대 핸들·균일 격자 버킷 (SPEC §7).
--
--    엔티티를 구조체의 배열이 아니라 배열의 구조체로 담는다. 성능도 이유지만
--    더 큰 이유는 **직렬화 순서가 배열 순서로 자동으로 고정**된다는 것이다.
--    상태 해시(SPEC §18.4)가 언어별 필드 순서에 영향을 받지 않는다.

local F = require('rts.fixed')

local M = {}
local floor = math.floor

M.MAX_ENT = 256
M.GEN_MOD = 256
M.BUCKET = 8
local MAX_ENT, GEN_MOD, BUCKET = 256, 256, 8

function M.index(h)
    return floor(h / 256)
end

function M.generation(h)
    return h % 256
end
local hindex = M.index

-- 엔티티 필드 이름 — 배열을 한꺼번에 만들 때와 해시를 찍을 때 쓴다.
local FIELDS = {'alive', 'gen', 'owner', 'kind', 'tx', 'ty', 'px', 'py',
                'hp', 'dir', 'state', 'target', 'load', 'prog',
                'from_t', 'to_t', 'cool', 'timer'}
M.FIELDS = FIELDS

--- 엔티티 배열과 버킷. 시뮬레이션 규칙은 여기 없다 — 담는 그릇일 뿐이다.
local World = {}
World.__index = World
M.World = World

function M.new(w, h)
    local self = setmetatable({}, World)
    self.w = w
    self.h = h
    self.bw = floor((w + BUCKET - 1) / BUCKET)
    self.bh = floor((h + BUCKET - 1) / BUCKET)
    for _, f in ipairs(FIELDS) do
        local a = {n = MAX_ENT}
        for i = 0, MAX_ENT - 1 do a[i] = 0 end
        self[f] = a
    end
    self.buckets = {n = self.bw * self.bh}
    for i = 0, self.bw * self.bh - 1 do
        self.buckets[i] = {}                 -- 1-기반 오름차순 목록
    end
    return self
end
World.new = M.new

-- ── SPEC §7.2 핸들 ──────────────────────────────────────────────────────────
function World:handle(i)
    return i * 256 + self.gen[i]
end

function World:valid(h)
    if h == 0 then
        return false
    end
    local i = hindex(h)
    return i > 0 and i < MAX_ENT and self.alive[i] == 1
           and (h % 256) == self.gen[i]
end

function World:bucket_of(tx, ty)
    return floor(ty / BUCKET) * self.bw + floor(tx / BUCKET)
end

-- ── 생성·소멸 ───────────────────────────────────────────────────────────────

--- 슬롯 0 은 절대 쓰지 않는다 — 핸들 0 이 "없음"을 뜻해야 하기 때문이다.
function World:spawn(owner, kind, tx, ty)
    for i = 1, MAX_ENT - 1 do
        if self.alive[i] == 0 then
            self.alive[i] = 1
            self.owner[i] = owner
            self.kind[i] = kind
            self.tx[i] = tx
            self.ty[i] = ty
            self.px[i] = tx * 16 * 65536
            self.py[i] = ty * 16 * 65536
            self.dir[i] = 4
            self.state[i] = 0
            self.target[i] = 0
            self.load[i] = 0
            self.prog[i] = 0
            self.from_t[i] = ty * self.w + tx
            self.to_t[i] = ty * self.w + tx
            self.cool[i] = 0
            self.timer[i] = 0
            self:_bucket_add(i)
            return self:handle(i)
        end
    end
    return 0                                 -- 상한 초과 — 조용히 실패한다
end

function World:kill(h)
    if not self:valid(h) then
        return false
    end
    local i = hindex(h)
    self:_bucket_del(i)
    self.alive[i] = 0
    self.gen[i] = (self.gen[i] + 1) % GEN_MOD
    return true
end

-- ── SPEC §7.3 버킷 ──────────────────────────────────────────────────────────
function World:_bucket_add(i)
    local b = self.buckets[self:bucket_of(self.tx[i], self.ty[i])]
    local k = 1
    while k <= #b and b[k] < i do            -- 오름차순 유지 — 결정론을 위해서다
        k = k + 1
    end
    table.insert(b, k, i)
end

function World:_bucket_del(i)
    local b = self.buckets[self:bucket_of(self.tx[i], self.ty[i])]
    for k = 1, #b do
        if b[k] == i then
            table.remove(b, k)
            return
        end
    end
end

--- 타일을 넘을 때만 부른다. 픽셀 이동마다 부르는 것이 아니다.
function World:move_tile(i, tx, ty)
    if self:bucket_of(self.tx[i], self.ty[i]) ~= self:bucket_of(tx, ty) then
        self:_bucket_del(i)
        self.tx[i] = tx
        self.ty[i] = ty
        self:_bucket_add(i)
    else
        self.tx[i] = tx
        self.ty[i] = ty
    end
end

--- 반경 r(체비셰프) 안의 엔티티 인덱스. 오름차순으로 돌려준다.
function World:query(tx, ty, r)
    local out = {n = 0}
    local lo = tx - r; if lo < 0 then lo = 0 end
    local hi = tx + r; if hi > self.w - 1 then hi = self.w - 1 end
    local x0, x1 = floor(lo / BUCKET), floor(hi / BUCKET)
    lo = ty - r; if lo < 0 then lo = 0 end
    hi = ty + r; if hi > self.h - 1 then hi = self.h - 1 end
    local y0, y1 = floor(lo / BUCKET), floor(hi / BUCKET)
    for by = y0, y1 do
        for bx = x0, x1 do
            local b = self.buckets[by * self.bw + bx]
            for k = 1, #b do
                local i = b[k]
                if F.dinf(self.tx[i] - tx, self.ty[i] - ty) <= r then
                    out[out.n] = i
                    out.n = out.n + 1
                end
            end
        end
    end
    -- 버킷을 훑는 순서가 인덱스 순서와 다르므로 마지막에 오름차순으로 맞춘다.
    local tmp = {}
    for i = 0, out.n - 1 do tmp[i + 1] = out[i] end
    table.sort(tmp)
    for i = 0, out.n - 1 do out[i] = tmp[i + 1] end
    return out
end

return M
