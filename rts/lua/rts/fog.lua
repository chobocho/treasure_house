-- 시야와 안개 — 참조 카운트 세 평면 (SPEC §14).
--
--    안개는 **그리기 단계에서만** 쓰인다. 시뮬레이션은 안개를 무시한다 —
--    안개를 시뮬레이션의 일부로 만들면 플레이어마다 상태가 갈리고, 그러면
--    락스텝의 전제가 무너진다(§14.5). 도스 RTS 의 맵 핵이 그토록 쉬웠던 이유가
--    정확히 이것이고, 19부에서 그 이야기를 한다.
--
--    칸당 1바이트를 쓴다. 비트 플레인이 8배 작지만 참조 카운트는 비트로 담을 수
--    없고, 루아 5.1 에서 비트 연산을 산술로 흉내내면 칸 하나에 나눗셈이 붙는다.
--    비트 플레인은 저장·전송용 pack_bits 로만 남겼다(§14.2).

local CI = require('rts.circle')
local C = require('rts.const')

local M = {}
local floor = math.floor

--- 플레이어마다 explored·count 두 평면. visible 은 count > 0 의 별칭이다.
local Fog = {}
Fog.__index = Fog
M.Fog = Fog

function M.new(w, h, players)
    players = players or C.MAX_PLAYER
    local self = setmetatable({}, Fog)
    self.w = w
    self.h = h
    self.players = players
    self.count = {n = players}
    self.explored = {n = players}
    for p = 0, players - 1 do
        local a = {n = w * h}
        local b = {n = w * h}
        for i = 0, w * h - 1 do a[i] = 0; b[i] = 0 end
        self.count[p] = a
        self.explored[p] = b
    end
    return self
end
Fog.new = M.new

function Fog:visible(p, i)
    return self.count[p][i] > 0
end

-- ── SPEC §14.3 증분 갱신 ────────────────────────────────────────────────────

--- O(r²) — 원 안의 칸마다 카운트 +1 과 탐험 표시.
function Fog:add_sight(p, tx, ty, r)
    local cnt, exp = self.count[p], self.explored[p]
    local off = CI.offsets(r)
    for k = 0, off.n - 1 do
        local x, y = tx + off[k][0], ty + off[k][1]
        if x >= 0 and x < self.w and y >= 0 and y < self.h then
            local i = y * self.w + x
            cnt[i] = cnt[i] + 1
            exp[i] = 1
        end
    end
end

--- 카운트 −1. 0 아래로는 내려가지 않는다 — 내려간다면 그것은 버그다.
function Fog:remove_sight(p, tx, ty, r)
    local cnt = self.count[p]
    local off = CI.offsets(r)
    for k = 0, off.n - 1 do
        local x, y = tx + off[k][0], ty + off[k][1]
        if x >= 0 and x < self.w and y >= 0 and y < self.h then
            local i = y * self.w + x
            if cnt[i] > 0 then
                cnt[i] = cnt[i] - 1
            end
        end
    end
end

--- 타일을 넘을 때 — **빼기가 먼저다**(§14.3).
function Fog:move_sight(p, ox, oy, nx, ny, r)
    self:remove_sight(p, ox, oy, r)
    self:add_sight(p, nx, ny, r)
end

--- 불변식 F 를 전수로 검증하고 **어긋난 칸 수만** 돌려준다.
--
--    고치지 않는 이유는 하나다. 증분 갱신이 새면 그것은 버그이고, 조용히 고쳐
--    버리면 그 버그는 영원히 드러나지 않는다. O(플레이어 × 칸수 + 엔티티 × r²)
--    이라 매 틱 돌릴 수는 없다 — 세이브 직후와 100틱마다 돌린다.
function Fog:recount(world)
    local np = self.count.n
    local want = {}
    for p = 0, np - 1 do
        local a = {}
        for i = 0, self.w * self.h - 1 do a[i] = 0 end
        want[p] = a
    end
    for i = 1, C.MAX_ENT - 1 do
        if world.alive[i] ~= 0 then
            local r = C.SIGHT[world.kind[i]]
            local p = world.owner[i]
            if p < np then
                local off = CI.offsets(r)      -- 건물의 시야 중심은 좌상단이다
                for k = 0, off.n - 1 do
                    local x = world.tx[i] + off[k][0]
                    local y = world.ty[i] + off[k][1]
                    if x >= 0 and x < self.w and y >= 0 and y < self.h then
                        want[p][y * self.w + x] = want[p][y * self.w + x] + 1
                    end
                end
            end
        end
    end
    local bad = 0
    for p = 0, np - 1 do
        for i = 0, self.w * self.h - 1 do
            if self.count[p][i] ~= want[p][i] then bad = bad + 1 end
        end
    end
    return bad
end

-- ── SPEC §14.4 4단계 렌더 ───────────────────────────────────────────────────

--- 0 미탐험 · 1 탐험 · 2 경계 · 3 가시.
--
--    2단계는 순전히 눈을 위한 것이다. 1과 3만 있으면 안개 경계가 계단처럼
--    보인다. 명암 단계는 팔레트 명암표(§22.2)의 행 번호다.
function Fog:level(p, x, y)
    if not (x >= 0 and x < self.w and y >= 0 and y < self.h) then
        return 0
    end
    local i = y * self.w + x
    if self.count[p][i] > 0 then
        return 3
    end
    if self.explored[p][i] == 0 then
        return 0
    end
    for dy = -1, 1 do
        for dx = -1, 1 do
            local u, v = x + dx, y + dy
            if u >= 0 and u < self.w and v >= 0 and v < self.h
               and self.count[p][v * self.w + u] > 0 then
                return 2
            end
        end
    end
    return 1
end

-- ── SPEC §14.2 비트 플레인 (저장·전송용) ────────────────────────────────────

--- 탐험 평면 8칸을 1바이트로. 칸 i 는 바이트 i//8 의 2^(i%8) 자리다.
--- 비트 연산자를 쓰지 않는다(§1.1) — 곱셈과 덧셈이면 충분하다.
function Fog:pack_bits(p)
    local n = self.w * self.h
    local out = {n = floor((n + 7) / 8)}
    for i = 0, out.n - 1 do out[i] = 0 end
    local exp = self.explored[p]
    for i = 0, n - 1 do
        if exp[i] ~= 0 then
            local b = floor(i / 8)
            out[b] = out[b] + 2 ^ (i % 8)
        end
    end
    return out
end

function Fog:unpack_bits(p, data)
    local n = self.w * self.h
    local exp = self.explored[p]
    for i = 0, n - 1 do
        exp[i] = floor(data[floor(i / 8)] / 2 ^ (i % 8)) % 2
    end
end

return M
