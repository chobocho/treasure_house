-- 점프 포인트 탐색 — A* 와 비용이 같은가를 전수로 확인한다 (SPEC §10).

local H = require('tests.harness')
local J = require('rts.jps')
local P = require('rts.path')
local R = require('rts.rng')
local T = require('rts.tmap')

H.title('jps')

local MAPS = {n = 6}
for i = 1, 6 do
    MAPS[i - 1] = T.load_text(H.golden('map_' .. i .. '.txt'))
end
local function pt(x, y) return {[0] = x, [1] = y, n = 2} end
local floor = math.floor

-- ---- 골든 8절의 JPS 열과 대조
local rows = H.lines(H.golden('prim.txt'))
local i = H.index_of(rows, '== 8. HPA* 와 JPS ==') + 2
local bad = 0
local n = 0
while H.strip(rows[i]) ~= '' and rows[i]:sub(1, #'JPS 비용') ~= 'JPS 비용' do
    local v = H.ints(rows[i])
    local mi, sx, sy, tx, ty = v[0], v[1], v[2], v[3], v[4]
    local wj, wjx = v[6], v[7]
    local m = MAPS[mi - 1]
    local c, _tiles, ex = J.search(m, 0, pt(sx, sy), pt(tx, ty))
    if c ~= wj or ex ~= wjx then
        bad = bad + 1
        H.note('맵%d (%d,%d)->(%d,%d) 기대 %s 실제 %s', mi, sx, sy, tx, ty,
               H.repr({[0] = wj, wjx, n = 2}), H.repr({[0] = c, ex, n = 2}))
    end
    n = n + 1
    i = i + 1
end
H.check(string.format('골든 8절 %d줄의 JPS 비용·연 노드 수', n), bad, 0)

-- ---- 전수 검사: 정리 10.1 을 옮겨 적는 대신 직접 확인한다
bad = 0
local total = 0
for mi = 0, MAPS.n - 1 do
    local m = MAPS[mi]
    local free = {n = 0}
    for j = 0, m.w * m.h - 1 do
        if m:passable_terrain(j % m.w, floor(j / m.w), 0) then
            free[free.n] = j
            free.n = free.n + 1
        end
    end
    local rand = R.new(1000 + mi)
    for _ = 1, 120 do
        local a = free[rand:roll(free.n)]
        local b = free[rand:roll(free.n)]
        local s = pt(a % m.w, floor(a / m.w))
        local t = pt(b % m.w, floor(b / m.w))
        local ca = P.astar(m, 0, s, t)
        local cj = J.search(m, 0, s, t)
        total = total + 1
        if ca ~= cj then
            bad = bad + 1
            if bad < 4 then
                H.note('맵%d (%d,%d)->(%d,%d) A*=%d JPS=%d',
                       mi + 1, s[0], s[1], t[0], t[1], ca, cj)
            end
        end
    end
end
H.check(string.format('무작위 %d쌍에서 JPS 비용 == A* 비용', total), bad, 0)

-- ---- 경로가 실제로 이어지는가 (점프점 사이는 직선이어야 한다)
bad = 0
for k = 0, MAPS.n - 1 do
    local m = MAPS[k]
    for j = 0, m.pairs.n - 1 do
        local s, t = m.pairs[j][0], m.pairs[j][1]
        local cost, tiles = J.search(m, 0, s, t)
        if cost >= 0 then
            for q = 0, tiles.n - 2 do
                local ax, ay = tiles[q] % m.w, floor(tiles[q] / m.w)
                local bx, by = tiles[q + 1] % m.w, floor(tiles[q + 1] / m.w)
                local dx, dy = bx - ax, by - ay
                local adx = dx < 0 and -dx or dx
                local ady = dy < 0 and -dy or dy
                if dx ~= 0 and dy ~= 0 and adx ~= ady then
                    bad = bad + 1                -- 대각 구간은 45도여야 한다
                end
                if dx == 0 and dy == 0 then bad = bad + 1 end
            end
        end
    end
end
H.check('점프점 사이가 직선 또는 45도', bad, 0)

-- ---- JPS 가 여는 노드 수는 A* 이하인가
local worse, same = 0, 0
for k = 0, MAPS.n - 1 do
    local m = MAPS[k]
    for j = 0, m.pairs.n - 1 do
        local s, t = m.pairs[j][0], m.pairs[j][1]
        local _c1, _t1, ax = P.astar(m, 0, s, t)
        local _c2, _t2, jx = J.search(m, 0, s, t)
        if jx > ax then
            worse = worse + 1
        elseif jx == ax then
            same = same + 1
        end
    end
end
H.check('JPS 의 연 노드 수가 A* 보다 많은 경우', worse, 0)
H.note('연 노드 수가 같은 경우 %d건 — 줄어드는 것은 연 노드지 훑는 칸이 아니다',
       same)

-- ---- 강제 이웃 규칙 (SPEC §10.1)
local m2 = T.new(5, 5)
for y = 0, 4 do
    for x = 0, 4 do m2:set_terrain(x, y, T.DIRT) end
end
m2:set_terrain(2, 1, T.ROCK)
H.check_true('(2,2) 로 동쪽으로 들어오면 (3,1) 이 강제 이웃',
             J._forced(m2, 2, 2, 1, 0, 0))
m2:set_terrain(2, 1, T.DIRT)
H.check_true('막힌 칸이 없으면 강제 이웃도 없다',
             not J._forced(m2, 2, 2, 1, 0, 0))

return H.done()
