-- 시야와 안개 — 참조 카운트와 4단계 렌더 (SPEC §14).

local H = require('tests.harness')
local CI = require('rts.circle')
local C = require('rts.const')
local FG = require('rts.fog')
local R = require('rts.rng')
local S = require('rts.spatial')

H.title('fog')

local W, HH = 64, 64

local function arr(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

--- 골든 10절과 같은 형식의 통계 — 가시 칸·합·최대·도수.
local function report(fg, p)
    local cnt = fg.count[p]
    local vis, tot, mx = 0, 0, 0
    for i = 0, cnt.n - 1 do
        if cnt[i] > 0 then vis = vis + 1 end
        tot = tot + cnt[i]
        if cnt[i] > mx then mx = cnt[i] end
    end
    local size = mx + 1
    if size < 3 then size = 3 end
    local hist = {n = size}
    for i = 0, size - 1 do hist[i] = 0 end
    for i = 0, cnt.n - 1 do
        if cnt[i] ~= 0 then hist[cnt[i]] = hist[cnt[i]] + 1 end
    end
    return vis, tot, mx, hist
end

local function sum_of(a)
    local s = 0
    for i = 0, a.n - 1 do s = s + a[i] end
    return s
end

-- ── 골든 10절 ───────────────────────────────────────────────────────────────
local fg = FG.new(W, HH)
for _, u in ipairs({{10, 10, 3}, {12, 11, 5}, {30, 30, 8}}) do
    fg:add_sight(0, u[1], u[2], u[3])
end
local vis, tot, mx, hist = report(fg, 0)
H.check('초기 가시 칸·합·최대', arr(vis, tot, mx), arr(279, 307, 2))
H.check('초기 도수 1·2', arr(hist[1], hist[2]), arr(251, 28))

fg:remove_sight(0, 10, 10, 3)
fg:add_sight(0, 11, 10, 3)
vis, tot, mx, hist = report(fg, 0)
H.check('1번 유닛 이동 뒤', arr(vis, tot, mx, hist[1], hist[2]),
        arr(278, 307, 2, 249, 29))

fg:remove_sight(0, 30, 30, 8)
vis, tot, mx, hist = report(fg, 0)
H.check('3번 유닛 사망 뒤', arr(vis, tot, mx, hist[1], hist[2]),
        arr(81, 110, 2, 52, 29))

fg:remove_sight(0, 11, 10, 3)
fg:remove_sight(0, 12, 11, 5)
H.check('전원 제거 후 카운트 합', sum_of(fg.count[0]), 0)
H.check_true('그래도 탐험 표시는 남는다', sum_of(fg.explored[0]) > 0)
H.note('증분 갱신이 정확히 0 으로 돌아온다 — 이것이 불변식 F 의 최소 조건이다')

-- ── 평면은 플레이어마다 따로다 ──────────────────────────────────────────────
H.check('다른 플레이어의 카운트는 그대로 0', sum_of(fg.count[1]), 0)
H.check('다른 플레이어는 탐험도 0', sum_of(fg.explored[1]), 0)
H.check('플레이어 수는 MAX_PLAYER', fg.count.n, C.MAX_PLAYER)

-- ── 가장자리 잘림 ───────────────────────────────────────────────────────────
local fg2 = FG.new(W, HH)
fg2:add_sight(0, 0, 0, 3)
local inmap = 0
local off3 = CI.offsets(3)
for k = 0, off3.n - 1 do
    local dx, dy = off3[k][0], off3[k][1]
    if dx >= 0 and dx < W and dy >= 0 and dy < HH then inmap = inmap + 1 end
end
H.check('(0,0) 반경 3 은 원의 1/4 만 맵 안', sum_of(fg2.count[0]), inmap)
local mx2 = 0
for i = 0, fg2.count[0].n - 1 do
    if fg2.count[0][i] > mx2 then mx2 = fg2.count[0][i] end
end
H.check('맵 밖은 세지 않는다', mx2, 1)
fg2:remove_sight(0, 0, 0, 3)
H.check('잘린 원도 정확히 0 으로 돌아온다', sum_of(fg2.count[0]), 0)
fg2:add_sight(0, 5, 5, 0)
H.check('반경 0 은 자기 칸 하나', sum_of(fg2.count[0]), 1)
local function min_of(a)
    local v = a[0]
    for i = 0, a.n - 1 do if a[i] < v then v = a[i] end end
    return v
end
fg2:remove_sight(0, 5, 5, 0)
H.check('카운트는 음수가 되지 않는다', min_of(fg2.count[0]), 0)
fg2:remove_sight(0, 5, 5, 0)
H.check('없는 시야를 또 빼도 0 이다', min_of(fg2.count[0]), 0)

-- ── 불변식 F — 무작위 이동 중 매 틱 전수 검증 ───────────────────────────────
local w = S.new(W, HH)
local fg3 = FG.new(W, HH)
local rand = R.new(31)
local KINDS = {[0] = C.INF, C.ARCHER, C.TANK, C.HARV}
local ents = {n = 0}
for k = 0, 11 do
    local kind = KINDS[k % 4]
    local x, y = 4 + rand:roll(56), 4 + rand:roll(56)
    local i = S.index(w:spawn(k % 2, kind, x, y))
    fg3:add_sight(w.owner[i], x, y, C.SIGHT[kind])
    ents[ents.n] = i
    ents.n = ents.n + 1
end
w:spawn(0, C.HQ, 20, 20)
fg3:add_sight(0, 20, 20, C.SIGHT[C.HQ])
local DXT = {[0] = 0, 1, 1, 1, 0, -1, -1, -1}
local DYT = {[0] = -1, -1, 0, 1, 1, 1, 0, -1}
local bad = 0
for _ = 1, 120 do
    for k = 0, ents.n - 1 do
        local i = ents[k]
        local d = rand:roll(8)
        local nx = w.tx[i] + DXT[d]
        local ny = w.ty[i] + DYT[d]
        if nx < 0 then nx = 0 elseif nx > W - 1 then nx = W - 1 end
        if ny < 0 then ny = 0 elseif ny > HH - 1 then ny = HH - 1 end
        if not (nx == w.tx[i] and ny == w.ty[i]) then
            local r = C.SIGHT[w.kind[i]]
            fg3:remove_sight(w.owner[i], w.tx[i], w.ty[i], r)     -- 먼저 빼고
            w:move_tile(i, nx, ny)
            fg3:add_sight(w.owner[i], nx, ny, r)                  -- 나중에 더한다
        end
    end
    bad = bad + fg3:recount(w)
end
H.check('불변식 F — 120틱 × 4플레이어 전수 재계산 불일치', bad, 0)

local dead = ents[0]
fg3:remove_sight(w.owner[dead], w.tx[dead], w.ty[dead], C.SIGHT[w.kind[dead]])
w:kill(w:handle(dead))
H.check('죽으면 remove 만 한다 — 그 뒤에도 불변식 F', fg3:recount(w), 0)

-- 일부러 어긋뜨리면 recount 가 잡아내는가
fg3.count[0][7 * W + 7] = fg3.count[0][7 * W + 7] + 1
H.check('어긋난 칸을 recount 가 센다', fg3:recount(w), 1)
fg3.count[0][7 * W + 7] = fg3.count[0][7 * W + 7] - 1
H.check('되돌리면 다시 0', fg3:recount(w), 0)
H.note('recount 는 고치지 않고 세기만 한다 — 고치면 버그가 조용히 묻힌다')

-- ── SPEC §14.4 4단계 ────────────────────────────────────────────────────────
local fg4 = FG.new(16, 16)
H.check('아무것도 안 봤으면 0(미탐험)', fg4:level(0, 8, 8), 0)
fg4:add_sight(0, 8, 8, 3)
H.check('보고 있으면 3(가시)', fg4:level(0, 8, 8), 3)
H.check('원 밖은 아직 0', fg4:level(0, 8, 15), 0)
fg4:remove_sight(0, 8, 8, 3)
H.check('시야가 빠지면 1(탐험됨)', fg4:level(0, 8, 8), 1)
fg4:add_sight(0, 8, 8, 1)
H.check('가시 칸에 인접한 탐험 칸은 2(경계)', fg4:level(0, 10, 8), 2)
H.check('가시 칸에서 두 칸 떨어진 탐험 칸은 1', fg4:level(0, 11, 8), 1)
H.check('가시 칸 자신은 3', fg4:level(0, 8, 9), 3)
H.check('맵 밖은 0', fg4:level(0, -1, 0), 0)
local lv = {}
local nlv = 0
for y = 0, 15 do
    for x = 0, 15 do
        local v = fg4:level(0, x, y)
        if not lv[v] then lv[v] = true; nlv = nlv + 1 end
    end
end
local lvs = {n = 0}
for v = 0, 3 do
    if lv[v] then lvs[lvs.n] = v; lvs.n = lvs.n + 1 end
end
H.check('단계는 0..3 뿐', lvs, arr(0, 1, 2, 3))

-- ── SPEC §14.2 비트 플레인 (저장·전송용) ────────────────────────────────────
local packed = fg4:pack_bits(0)
H.check('16×16 = 256칸이 32바이트로 접힌다', packed.n, 32)
local inrange = true
for i = 0, packed.n - 1 do
    if packed[i] < 0 or packed[i] > 255 then inrange = false end
end
H.check_true('바이트 범위', inrange)
local fg5 = FG.new(16, 16)
fg5:unpack_bits(0, packed)
H.check('풀면 원래 탐험 평면', fg5.explored[0], fg4.explored[0])
local z8 = {n = 8}
for i = 0, 7 do z8[i] = 0 end
H.check('한 칸도 안 본 평면은 전부 0', FG.new(8, 8):pack_bits(0), z8)
local full = FG.new(8, 8)
for i = 0, 63 do full.explored[0][i] = 1 end
local f8 = {n = 8}
for i = 0, 7 do f8[i] = 255 end
H.check('전부 본 평면은 전부 255', full:pack_bits(0), f8)
local odd = FG.new(4, 3)                     -- 12칸 — 8의 배수가 아니다
odd.explored[0][11] = 1
H.check('8의 배수가 아니면 마지막 바이트를 0으로 채운다', odd:pack_bits(0).n, 2)
H.check('마지막 칸은 마지막 바이트의 3번 비트', odd:pack_bits(0), arr(0, 8))

return H.done()
