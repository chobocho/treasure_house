-- 경로 탐색 I — BFS·다익스트라·A* 와 그 성질 (SPEC §8).

local H = require('tests.harness')
local F = require('rts.fixed')
local P = require('rts.path')
local T = require('rts.tmap')

H.title('path')

local MAPS = {n = 6}
for i = 1, 6 do
    MAPS[i - 1] = T.load_text(H.golden('map_' .. i .. '.txt'))
end

local function pt(x, y) return {[0] = x, [1] = y, n = 2} end

-- ---- 골든 7절과 전수 대조
local rows = H.lines(H.golden('prim.txt'))
local i = H.index_of(rows, '== 7. 경로 탐색 ==') + 2
local bad = 0
local n = 0
while H.strip(rows[i]) ~= '' and rows[i]:sub(1, #'다익스트라') ~= '다익스트라' do
    local v = H.ints(rows[i])
    local mi, sx, sy, tx, ty = v[0], v[1], v[2], v[3], v[4]
    local wb, wd, wa, wx = v[5], v[6], v[7], v[8]
    local m = MAPS[mi - 1]
    local gb = P.bfs(m, 0, pt(sx, sy), pt(tx, ty))
    local gd = P.dijkstra(m, 0, {[0] = sy * m.w + sx, n = 1},
                          ty * m.w + tx)[ty * m.w + tx]
    if gd >= P.INF then gd = -1 end
    local ga, _tiles, gx = P.astar(m, 0, pt(sx, sy), pt(tx, ty))
    local got = {[0] = gb, gd, ga, gx, n = 4}
    local wnt = {[0] = wb, wd, wa, wx, n = 4}
    if not H.deep_eq(got, wnt) then
        bad = bad + 1
        H.note('맵%d (%d,%d)->(%d,%d) 기대 %s 실제 %s',
               mi, sx, sy, tx, ty, H.repr(wnt), H.repr(got))
    end
    n = n + 1
    i = i + 1
end
H.check(string.format('골든 7절 %d줄 (BFS·다익스트라·A*·연 노드 수)', n), bad, 0)

-- ---- 다익스트라와 A* 의 비용은 언제나 같아야 한다 (정리 8.1)
bad = 0
for k = 0, MAPS.n - 1 do
    local m = MAPS[k]
    for j = 0, m.pairs.n - 1 do
        local s, t = m.pairs[j][0], m.pairs[j][1]
        local d = P.dijkstra(m, 0, {[0] = s[1] * m.w + s[0], n = 1},
                             t[1] * m.w + t[0])[t[1] * m.w + t[0]]
        local a = P.astar(m, 0, s, t)
        if (d < P.INF and d or -1) ~= a then bad = bad + 1 end
    end
end
H.check('다익스트라 == A*', bad, 0)

-- ---- 휴리스틱의 허용성: h(n) <= 실제 최적 비용 (전수)
local m = MAPS[0]
bad = 0
local checked = 0
local src = pt(16, 16)
local dist = P.dijkstra(m, 0, {[0] = src[1] * m.w + src[0], n = 1})
for j = 0, m.w * m.h - 1 do
    if dist[j] < P.INF then
        local x, y = j % m.w, math.floor(j / m.w)
        if P.h_oct(src[0], src[1], x, y) > dist[j] then bad = bad + 1 end
        checked = checked + 1
    end
end
H.check(string.format('허용성: h <= g* (%d칸 전수)', checked), bad, 0)

-- ---- 일관성: h(n) <= c(n,n') + h(n') (전수)
bad = 0
local t = pt(30, 30)
for y = 1, 30 do
    for x = 1, 30 do
        local nb = P.neighbours(m, x, y, 0)
        for k = 0, nb.n - 1 do
            local d, u, v = nb[k][1], nb[k][2], nb[k][3]
            if P.h_oct(x, y, t[0], t[1])
               > F.DCOST[d] + P.h_oct(u, v, t[0], t[1]) then
                bad = bad + 1
            end
        end
    end
end
H.check("일관성: h(n) <= c + h(n')", bad, 0)
H.note('일관적이므로 닫힌 노드를 다시 열지 않는다 — 재개방 코드가 아예 없다')

-- ---- 경로가 실제로 이어져 있고 비용이 맞는가
bad = 0
for k = 0, MAPS.n - 1 do
    local mm = MAPS[k]
    for j = 0, mm.pairs.n - 1 do
        local s, tt = mm.pairs[j][0], mm.pairs[j][1]
        local cost, tiles = P.astar(mm, 0, s, tt)
        if cost >= 0 then
            local total = 0
            for q = 0, tiles.n - 2 do
                local ax, ay = tiles[q] % mm.w, math.floor(tiles[q] / mm.w)
                local bx, by = tiles[q + 1] % mm.w,
                               math.floor(tiles[q + 1] / mm.w)
                local dx, dy = bx - ax, by - ay
                local adx = dx < 0 and -dx or dx
                local ady = dy < 0 and -dy or dy
                if (adx > ady and adx or ady) ~= 1 then bad = bad + 1 end
                total = total + ((dx ~= 0 and dy ~= 0) and F.D_DIAG
                                 or F.D_STRAIGHT)
            end
            if total ~= cost then bad = bad + 1 end
        end
    end
end
H.check('경로가 한 칸씩 이어지고 비용 합이 같다', bad, 0)

-- ---- 양동이 큐 (정리 8.3): 15개면 충분한가
H.check('양동이 개수', P.NB, 15)
H.check('최대 간선 비용', F.D_DIAG, 14)
H.check_true('양동이 개수 > 최대 간선 비용', P.NB > F.D_DIAG)

-- ---- 코너 컷 허용 (SPEC §8.1)
local m2 = T.new(3, 3)
for y = 0, 2 do
    for x = 0, 2 do m2:set_terrain(x, y, T.DIRT) end
end
m2:set_terrain(1, 0, T.ROCK)
m2:set_terrain(0, 1, T.ROCK)
H.check('바위 두 개 사이 대각을 지나간다',
        P.astar(m2, 0, pt(0, 0), pt(1, 1)), 14)
H.note('이것은 선택이다 — 금지하면 JPS 의 가지치기 규칙이 통째로 달라진다')

-- ---- 도달 불가 목표 (SPEC §8.6)
local m5 = MAPS[4]
H.check('섬 안쪽은 닿지 않는다', P.astar(m5, 0, pt(1, 1), pt(25, 25)), -1)
local alt = P.closest_reachable(m5, 0, pt(1, 1), pt(25, 25))
H.check_true('대체 목표를 찾는다 ' .. H.repr(alt), alt ~= nil)
H.check('대체 목표는 같은 성분',
        m5:labels(0)[alt[1] * m5.w + alt[0]], m5:labels(0)[1 * m5.w + 1])
local cost = P.find(m5, 0, pt(1, 1), pt(25, 25))
H.check_true('find 는 대체 목표까지의 경로를 준다', cost > 0)

-- ---- 경로 캐시 (SPEC §8.7)
local c = P.newcache()
local m1 = MAPS[0]
P.find(m1, 0, pt(1, 1), pt(30, 30), c)
P.find(m1, 0, pt(1, 1), pt(30, 30), c)
H.check('두 번째는 적중', c.hits, 1)
H.check('첫 번째는 실패', c.misses, 1)
m1:set_terrain(15, 15, T.ROCK)
P.find(m1, 0, pt(1, 1), pt(30, 30), c)
H.check('지형이 바뀌면 통째로 비운다', c.hits, 1)
m1:set_terrain(15, 15, T.DIRT)

return H.done()
