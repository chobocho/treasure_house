-- 맵 생성 — 셀룰러 오토마타·다이아몬드 스퀘어·포아송 자원·대칭 (SPEC §5).
--
--    생성기는 게임이 시작하기 전에 한 번만 돈다. 그래서 시뮬레이션 RNG 와
--    **다른 인스턴스**를 쓴다(SPEC §3.3). 여기서 뽑은 난수가 시뮬 수열에 끼어들면
--    두 기계가 같은 맵을 놓고도 다른 게임을 하게 된다.

local R = require('rts.rng')
local T = require('rts.tmap')

local M = {}
local floor = math.floor

M.MW, M.MH = 64, 64
local MW, MH = 64, 64
M.START = {[0] = {[0] = 8, [1] = 8, n = 2},
           [1] = {[0] = 55, [1] = 55, n = 2}, n = 2}
M.ORE_TRIES = 4000
M.ORE_COUNT = 12
M.ORE_RMIN = 9

-- 높이 → 지형 (SPEC §5.2). 위에서부터 처음 걸리는 것.
M.THRESH = {[0] = {[0] = 63, [1] = T.WATER, n = 2},
            {[0] = 95, [1] = T.SAND, n = 2},
            {[0] = 175, [1] = T.DIRT, n = 2},
            {[0] = 207, [1] = T.HILL, n = 2},
            {[0] = 255, [1] = T.ROCK, n = 2}, n = 5}

M.LAST_ORE = {n = 0}             -- 마지막 생성의 광맥 중심점 — 시험·덱용

function M.terrain_of(v)
    for i = 0, M.THRESH.n - 1 do
        if v <= M.THRESH[i][0] then
            return M.THRESH[i][1]
        end
    end
    return T.ROCK
end

local function clamp(v)
    if v < 0 then return 0 end
    if v > 255 then return 255 end
    return v
end

-- ── SPEC §5.1 셀룰러 오토마타 ───────────────────────────────────────────────

--- B5678/S45678 한 세대. 맵 밖은 벽으로 센다.
--
--    살아 있는 벽은 이웃 벽이 4 이상이면 남고, 빈 칸은 5 이상이면 벽이 된다.
--    2세대면 덩어리가 덜 뭉치고 6세대면 좁은 통로가 전부 막힌다 — 4세대가
--    통로와 개활지가 함께 남는 자리다.
function M.cellular_step(cur, w, h)
    local nxt = {n = w * h}
    for y = 0, h - 1 do
        for x = 0, w - 1 do
            local n = 0
            for dy = -1, 1 do
                for dx = -1, 1 do
                    if not (dx == 0 and dy == 0) then
                        local u, v = x + dx, y + dy
                        if u < 0 or u >= w or v < 0 or v >= h then
                            n = n + 1
                        else
                            n = n + cur[v * w + u]
                        end
                    end
                end
            end
            if cur[y * w + x] == 1 then
                nxt[y * w + x] = (n >= 4) and 1 or 0
            else
                nxt[y * w + x] = (n >= 5) and 1 or 0
            end
        end
    end
    return nxt
end

function M.cellular(w, h, rand, gens, fill)
    gens = gens or 4
    fill = fill or 45
    local cur = {n = w * h}
    for i = 0, w * h - 1 do
        cur[i] = (rand:roll(100) < fill) and 1 or 0
    end
    for _ = 1, gens do
        cur = M.cellular_step(cur, w, h)
    end
    return cur
end

-- ── SPEC §5.2 다이아몬드-스퀘어 ─────────────────────────────────────────────

--- (2^6)+1 = 65 칸 격자. 평균은 반올림이 아니라 내림이다 — 명세다.
function M.diamond_square(rand)
    local n = 65
    local h = {n = n}
    for y = 0, n - 1 do
        local row = {n = n}
        for x = 0, n - 1 do row[x] = 0 end
        h[y] = row
    end
    for _, p in ipairs({{0, 0}, {0, 64}, {64, 0}, {64, 64}}) do
        h[p[2]][p[1]] = rand:roll(256)
    end
    local step = 64
    while step > 1 do
        local half = floor(step / 2)
        local amp = floor(step * 255 / 128)
        local y = 0
        while y < n - 1 do
            local x = 0
            while x < n - 1 do
                local a = floor((h[y][x] + h[y][x + step]
                                 + h[y + step][x] + h[y + step][x + step]) / 4)
                h[y + half][x + half] = clamp(a + rand:roll(2 * amp + 1) - amp)
                x = x + step
            end
            y = y + step
        end
        local row = 0
        y = 0
        while y < n do
            local start = (row % 2 == 0) and half or 0
            local x = start
            while x < n do
                local t, c = 0, 0
                for _, d in ipairs({{-half, 0}, {half, 0}, {0, -half}, {0, half}}) do
                    local u, v = x + d[1], y + d[2]
                    if u >= 0 and u < n and v >= 0 and v < n then
                        t = t + h[v][u]
                        c = c + 1
                    end
                end
                h[y][x] = clamp(floor(t / c) + rand:roll(2 * amp + 1) - amp)
                x = x + step
            end
            row = row + 1
            y = y + half
        end
        step = half
    end
    return h
end

-- ── SPEC §5.3 정수 포아송 디스크 ────────────────────────────────────────────

--- 앞쪽 절반에만 놓고 대칭 복사한다. 시도 상한이 반드시 있어야 한다 —
--- 상한 없는 재시도는 디싱크보다 나쁘다(맵 생성이 영원히 끝나지 않는다).
function M.place_ore(m, rand, n, rmin)
    n = n or M.ORE_COUNT
    rmin = rmin or M.ORE_RMIN
    local pts = {n = 0}
    local tries = 0
    while pts.n < n and tries < M.ORE_TRIES do
        tries = tries + 1
        local x, y = rand:roll(MW), rand:roll(floor(MH / 2))
        local t = m.terrain[y * MW + x]
        if t == T.DIRT or t == T.SAND then
            local ok = true
            for k = 0, pts.n - 1 do
                local px, py = pts[k][0], pts[k][1]
                if (x - px) * (x - px) + (y - py) * (y - py) < rmin * rmin then
                    ok = false
                    break
                end
            end
            if ok then
                pts[pts.n] = {[0] = x, [1] = y, n = 2}
                pts.n = pts.n + 1
            end
        end
    end
    for k = 0, pts.n - 1 do
        local px, py = pts[k][0], pts[k][1]
        for dy = -2, 2 do
            for dx = -2, 2 do
                if dx * dx + dy * dy <= 4 then
                    local u, v = px + dx, py + dy
                    if u >= 0 and u < MW and v >= 0 and v < MH then
                        local t = m.terrain[v * MW + u]
                        if t == T.DIRT or t == T.SAND then
                            m.terrain[v * MW + u] = T.ORE
                            m.terrain[(MH - 1 - v) * MW + (MW - 1 - u)] = T.ORE
                        end
                    end
                end
            end
        end
    end
    return pts, tries
end

-- ── SPEC §5.4 대칭과 시작 지점 ──────────────────────────────────────────────

--- 180도 회전 대칭. 앞쪽 절반이 원본이다.
function M.symmetrize(m)
    for y = 0, MH - 1 do
        for x = 0, MW - 1 do
            if y * MW + x < floor(MW * MH / 2) then
                m.terrain[(MH - 1 - y) * MW + (MW - 1 - x)] = m.terrain[y * MW + x]
            end
        end
    end
end

--- 시작 지점 5×5 를 흙으로 — 사령부 3×3 이 반드시 들어가야 한다.
function M.clear_base(m)
    for k = 0, M.START.n - 1 do
        local bx, by = M.START[k][0], M.START[k][1]
        for dy = -2, 2 do
            for dx = -2, 2 do
                local u, v = bx + dx, by + dy
                if u >= 0 and u < MW and v >= 0 and v < MH then
                    m.terrain[v * MW + u] = T.DIRT
                end
            end
        end
    end
end

--- 시드를 1씩 올리며 두 시작점이 이어질 때까지 다시 만든다.
--
--    재시도가 필요하다는 것 자체가 명세의 일부다 — 다이아몬드-스퀘어는 가끔
--    두 기지 사이를 물로 끊어 놓는다.
function M.gen_start(seed)
    seed = seed or 3
    local retries = 0
    while true do
        local rand = R.new(seed)
        local m = T.new(MW, MH)
        local h = M.diamond_square(rand)
        for y = 0, MH - 1 do
            for x = 0, MW - 1 do
                m.terrain[y * MW + x] = M.terrain_of(h[y][x])
            end
        end
        M.symmetrize(m)
        local pts = M.place_ore(m, rand)
        M.clear_base(m)
        for i = 0, MW * MH - 1 do
            m:_repass(i)
        end
        m:_bump()
        m.starts = {[0] = {[0] = M.START[0][0], [1] = M.START[0][1], n = 2},
                    [1] = {[0] = M.START[1][0], [1] = M.START[1][1], n = 2},
                    n = 2}
        local lab = m:labels(0)
        local a = lab[m:idx(M.START[0][0], M.START[0][1])]
        local b = lab[m:idx(M.START[1][0], M.START[1][1])]
        if a == b and b >= 0 then
            M.LAST_ORE = pts
            return m, seed, retries
        end
        seed = seed + 1
        retries = retries + 1
    end
end

return M
