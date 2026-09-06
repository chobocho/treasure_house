-- 흐름장·클리어런스·브러시파이어 (SPEC §11).
--
--    골든 9절과 대조하고, 정리 11.1 은 완전 탐색으로 직접 확인한다.

local H = require('tests.harness')
local F = require('rts.fixed')
local FL = require('rts.flow')
local P = require('rts.path')
local T = require('rts.tmap')

H.title('flow')

local floor = math.floor

-- tools/gen_prim.py 의 FLOWMAP 과 **글자 단위로 같아야 한다**.
local FLOWMAP = {
    '............',
    '.##########.',
    '.#........#.',
    '.#.######.#.',
    '.#.#....#.#.',
    '.#.#.##.#.#.',
    '.#.#.##.#.#.',
    '.#.#....#.#.',
    '.#.######.#.',
    '.#........#.',
    '.##########.',
    '............',
}

local function grid(rows)
    local m = T.new(#rows[1], #rows)
    for y = 0, #rows - 1 do
        local row = rows[y + 1]
        for x = 0, m.w - 1 do
            local ch = row:sub(x + 1, x + 1)
            m.terrain[y * m.w + x] = (ch == '#') and T.ROCK or T.DIRT
            m:_repass(y * m.w + x)
        end
    end
    m:_bump()
    return m
end

local function rows_of(field, m, width)
    local out = {}
    local fmt = '%' .. width .. 'd'
    for y = 0, m.h - 1 do
        local cells = {}
        for x = 0, m.w - 1 do
            cells[#cells + 1] = string.format(fmt, field[y * m.w + x])
        end
        out[#out + 1] = '  ' .. table.concat(cells, ' ')
    end
    return out
end

local function pt(x, y) return {[0] = x, [1] = y, n = 2} end
local function ptlist(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

local FM = grid(FLOWMAP)

-- ── 골든 9절 세 표와 한 줄씩 대조 ───────────────────────────────────────────
local g = H.lines(H.golden('prim.txt'))
local i = H.index_of(g, '== 9. 흐름장과 클리어런스 ==')
local integ = FL.integration(FM, 0, ptlist(pt(4, 4)))
local fl = FL.flow_dirs(FM, 0, integ)
local cl = FL.clearance(FM, 0)
local want = {}
for k = 0, 11 do want[#want + 1] = g[i + 2 + k] end
for k = 0, 11 do want[#want + 1] = g[i + 15 + k] end
for k = 0, 11 do want[#want + 1] = g[i + 28 + k] end
local got = {}
for _, r in ipairs(rows_of(integ, FM, 5)) do got[#got + 1] = r end
for _, r in ipairs(rows_of(fl, FM, 3)) do got[#got + 1] = r end
for _, r in ipairs(rows_of(cl, FM, 2)) do got[#got + 1] = r end
local bad = 0
for k = 1, 36 do
    if got[k] ~= want[k] then
        bad = bad + 1
        if bad < 4 then
            H.note('%d행 기대 %s', k - 1, H.repr(want[k]))
            H.note('     실제 %s', H.repr(got[k]))
        end
    end
end
H.check('골든 9절 36줄 (적분장·경사장·클리어런스)', bad, 0)

-- ── 적분장 = 목표에서 거꾸로 돌린 다익스트라 ────────────────────────────────
local d = P.dijkstra(FM, 0, {[0] = 4 * FM.w + 4, n = 1})
bad = 0
for j = 0, FM.w * FM.h - 1 do
    local want_v = (d[j] >= FL.INF) and FL.INF or d[j]
    if not FM:passable_terrain(j % FM.w, floor(j / FM.w), 0) then
        want_v = FL.INF
    end
    if integ[j] ~= want_v then bad = bad + 1 end
end
H.check('적분장 == path.dijkstra (INF 는 65535 로 자름)', bad, 0)

-- ── 다중 목표는 목표별 장의 최솟값이다 ──────────────────────────────────────
local a = FL.integration(FM, 0, ptlist(pt(2, 2)))
local b = FL.integration(FM, 0, ptlist(pt(9, 9)))
local ab = FL.integration(FM, 0, ptlist(pt(2, 2), pt(9, 9)))
local mins = {n = FM.w * FM.h}
for j = 0, FM.w * FM.h - 1 do
    mins[j] = (a[j] < b[j]) and a[j] or b[j]
end
H.check('다중 목표 == 목표별 최솟값', ab, mins)

-- ── 경계 조건 ───────────────────────────────────────────────────────────────
local empt = FL.integration(FM, 0, ptlist())
local uniq = {}
local uniqn = 0
for j = 0, empt.n - 1 do
    if not uniq[empt[j]] then uniq[empt[j]] = true; uniqn = uniqn + 1 end
end
H.check('목표가 없으면 전부 INF',
        {[0] = uniqn, uniq[FL.INF] and 1 or 0, n = 2}, {[0] = 1, 1, n = 2})
H.check('막힌 목표는 무시한다 (SPEC §11.1)',
        FL.integration(FM, 0, ptlist(pt(1, 1))), empt)
H.check('막힌 목표 + 성한 목표 = 성한 목표만',
        FL.integration(FM, 0, ptlist(pt(1, 1), pt(4, 4))), integ)
local one = grid({'.'})
H.check('1x1 맵', FL.integration(one, 0, ptlist(pt(0, 0))), {[0] = 0, n = 1})
H.check('1x1 맵의 경사장', FL.flow_dirs(one, 0, {[0] = 0, n = 1}),
        {[0] = 255, n = 1})
H.check('1x1 맵의 클리어런스', FL.clearance(one, 0), {[0] = 1, n = 1})
local solid = grid({'##', '##'})
H.check('전부 막힌 맵의 클리어런스', FL.clearance(solid, 0),
        {[0] = 0, 0, 0, 0, n = 4})
H.check('전부 막힌 맵의 브러시파이어', FL.brushfire(solid, 0),
        {[0] = 0, 0, 0, 0, n = 4})

-- ── 경사장: 막힌 칸과 INF 칸은 255, 나머지는 내리막이다 ─────────────────────
bad = 0
local stops = 0
for j = 0, FM.w * FM.h - 1 do
    local x, y = j % FM.w, floor(j / FM.w)
    if integ[j] == FL.INF then
        if fl[j] ~= 255 then bad = bad + 1 end
    elseif fl[j] == 255 then
        stops = stops + 1
    elseif integ[j] ~= 0 then       -- 목표 칸은 예외 — 오르막을 가리킨다
        local u, v = x + F.DX[fl[j]], y + F.DY[fl[j]]
        if not FM:passable_terrain(u, v, 0)
           or integ[v * FM.w + u] >= integ[j] then
            bad = bad + 1
        end
    end
end
H.check('INF·막힌 칸의 경사는 255', bad, 0)
H.check('정지 칸은 없다 (모든 도달 가능 칸에 후보가 있다)', stops, 0)

-- ── 경사장 동점 규칙: 대칭 맵에서 항상 작은 방향 번호 ───────────────────────
local open3 = grid({'...', '...', '...'})
local of = FL.flow_dirs(open3, 0, FL.integration(open3, 0, ptlist(pt(1, 1))))
H.check('(0,0) 은 목표를 향한 대각 3(SE)', of[0], 3)
H.check('목표 칸도 255 가 아니다 — 가장 싼 이웃(오르막)을 가리킨다', of[4], 0)
local tie = FL.flow_dirs(open3, 0,
                         FL.integration(open3, 0, ptlist(pt(0, 0), pt(2, 0))))
H.check('동점이면 작은 방향 번호 — (1,1) 은 1(NE), 7(NW) 이 아니다', tie[4], 1)

-- ── 정리 11.1 을 완전 탐색으로 확인 ─────────────────────────────────────────
local function max_square(m, kind, x, y)
    local k = 0
    while true do
        local s = k + 1
        if x + s > m.w or y + s > m.h then return k end
        for v = y, y + s - 1 do
            for u = x, x + s - 1 do
                if not m:passable_terrain(u, v, kind) then return k end
            end
        end
        k = s
    end
end

local MAPS = {n = 7}
MAPS[0] = FM
for k = 1, 6 do
    MAPS[k] = T.load_text(H.golden('map_' .. k .. '.txt'))
end
bad = 0
local cells = 0
for k = 0, MAPS.n - 1 do
    local m = MAPS[k]
    local c = FL.clearance(m, 0)
    for y = 0, m.h - 1 do
        for x = 0, m.w - 1 do
            cells = cells + 1
            if c[y * m.w + x] ~= max_square(m, 0, x, y) then bad = bad + 1 end
        end
    end
end
H.check(string.format('정리 11.1 — %d칸에서 clear == 최대 정사각 변', cells), bad, 0)

-- ── 크기 s 유닛의 통행 판정 ─────────────────────────────────────────────────
local M1 = MAPS[1]
local c1 = FL.clearance(M1, 0)
local n1, n2 = 0, 0
for j = 0, c1.n - 1 do
    if c1[j] >= 1 then n1 = n1 + 1 end
end
for j = 0, M1.w * M1.h - 1 do
    if M1:passable_terrain(j % M1.w, floor(j / M1.w), 0) then n2 = n2 + 1 end
end
H.check_true('크기 1 통행 칸 수 == 지형 통행 칸 수', n1 == n2)
local subset = true
for j = 0, c1.n - 1 do
    if c1[j] >= 2 and not (c1[j] >= 1) then subset = false end
end
H.check_true('크기 2 통행 칸은 크기 1 통행 칸의 부분집합', subset)
local sp, sw = {n = 20}, {n = 20}
for j = 0, 19 do
    sp[j] = FL.size_passable(c1, M1, j % M1.w, floor(j / M1.w), 2)
    sw[j] = c1[j] >= 2
end
H.check('size_passable 는 clear >= s 와 같다', sp, sw)
H.check('맵 밖은 어떤 크기로도 통행 불가',
        FL.size_passable(c1, M1, -1, 0, 1), false)

-- ── 브러시파이어: 벨만-포드로 다시 풀어 비교 ────────────────────────────────

--- 같은 답을 아주 느리게 구하는 참조 구현 — 완화가 멈출 때까지 돈다.
local function brushfire_ref(m, kind)
    local n = m.w * m.h
    local dist = {n = n}
    for j = 0, n - 1 do dist[j] = FL.INF end
    for y = 0, m.h - 1 do
        for x = 0, m.w - 1 do
            if not m:passable_terrain(x, y, kind) then
                dist[y * m.w + x] = 0
            else
                for d = 0, 7 do
                    if not m:in_map(x + F.DX[d], y + F.DY[d]) then
                        if F.DCOST[d] < dist[y * m.w + x] then
                            dist[y * m.w + x] = F.DCOST[d]
                        end
                    end
                end
            end
        end
    end
    local changed = true
    while changed do
        changed = false
        for y = 0, m.h - 1 do
            for x = 0, m.w - 1 do
                if m:passable_terrain(x, y, kind) then
                    local j = y * m.w + x
                    for d = 0, 7 do
                        local u, v = x + F.DX[d], y + F.DY[d]
                        if m:in_map(u, v) then
                            local nd = dist[v * m.w + u] + F.DCOST[d]
                            if nd < dist[j] then
                                dist[j] = nd
                                changed = true
                            end
                        end
                    end
                end
            end
        end
    end
    return dist
end

bad = 0
for k = 0, 3 do
    if not H.deep_eq(FL.brushfire(MAPS[k], 0), brushfire_ref(MAPS[k], 0)) then
        bad = bad + 1
    end
end
H.check('브러시파이어 == 참조 구현 (맵 4장)', bad, 0)

local fire = FL.brushfire(FM, 0)
H.check('막힌 칸의 fire 는 0', fire[1 * FM.w + 1], 0)
H.check('가장자리 자유 칸의 fire 는 10 (맵 밖 = 막힌 칸)', fire[0], 10)
H.check_true('바위 덩어리 반대편으로 0 이 새지 않는다',
             fire[0 * FM.w + 6] > 0 and fire[2 * FM.w + 5] > 0)

-- ── 한 번 계산하면 유닛 수와 무관하다 (§11.1 의 손익분기) ───────────────────
local free = {n = 0}
for j = 0, FM.w * FM.h - 1 do
    if FM:passable_terrain(j % FM.w, floor(j / FM.w), 0) then
        free[free.n] = j
        free.n = free.n + 1
    end
end
bad = 0
local lim = free.n < 40 and free.n or 40
for k = 0, lim - 1 do
    local j = free[k]
    if integ[j] < FL.INF then
        if P.astar(FM, 0, pt(j % FM.w, floor(j / FM.w)), pt(4, 4)) ~= integ[j] then
            bad = bad + 1
        end
    end
end
H.check(string.format('적분장 값 == 그 칸에서 목표까지의 A* 비용 (%d칸)', lim),
        bad, 0)

return H.done()
