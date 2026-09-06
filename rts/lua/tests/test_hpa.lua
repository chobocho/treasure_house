-- 계층 경로 탐색 — 최적이 아니라는 것을 숫자로 남긴다 (SPEC §9).

local H = require('tests.harness')
local A = require('rts.hpa')
local P = require('rts.path')
local T = require('rts.tmap')

H.title('hpa')

local MAPS = {n = 6}
for i = 1, 6 do
    MAPS[i - 1] = T.load_text(H.golden('map_' .. i .. '.txt'))
end
local function pt(x, y) return {[0] = x, [1] = y, n = 2} end

-- ---- 골든 8절의 HPA* 열과 대조
local rows = H.lines(H.golden('prim.txt'))
local i = H.index_of(rows, '== 8. HPA* 와 JPS ==') + 2
local bad = 0
local n = 0
local ratios = {n = 0}
while H.strip(rows[i]) ~= '' and rows[i]:sub(1, #'JPS 비용') ~= 'JPS 비용' do
    local v = H.ints(rows[i])
    local mi, sx, sy, tx, ty = v[0], v[1], v[2], v[3], v[4]
    local wh, wr = v[8], v[9]
    local m = MAPS[mi - 1]
    local c = A.search(m, 0, pt(sx, sy), pt(tx, ty))
    if c ~= wh then
        bad = bad + 1
        H.note('맵%d (%d,%d)->(%d,%d) 기대 %d 실제 %d', mi, sx, sy, tx, ty, wh, c)
    end
    if wr > 0 then
        ratios[ratios.n] = wr
        ratios.n = ratios.n + 1
    end
    n = n + 1
    i = i + 1
end
H.check(string.format('골든 8절 %d줄의 HPA* 비용', n), bad, 0)
local rmin, rmax, rsum = ratios[0], ratios[0], 0
for k = 0, ratios.n - 1 do
    if ratios[k] < rmin then rmin = ratios[k] end
    if ratios[k] > rmax then rmax = ratios[k] end
    rsum = rsum + ratios[k]
end
H.note('최적 대비 %d~%d 천분율 (평균 %d) — 논문의 "1%%" 를 옮겨 적지 않는다',
       rmin, rmax, math.floor(rsum / ratios.n))

-- ---- HPA* 는 최적 이상이다 (아래로 내려갈 수는 없다)
bad = 0
for k = 0, MAPS.n - 1 do
    local m = MAPS[k]
    for j = 0, m.pairs.n - 1 do
        local s, t = m.pairs[j][0], m.pairs[j][1]
        local a = P.astar(m, 0, s, t)
        local c = A.search(m, 0, s, t)
        if a > 0 and c > 0 and c < a then
            bad = bad + 1
            H.note('HPA* 가 A* 보다 싸다?! %s %s %d < %d',
                   H.repr(s), H.repr(t), c, a)
        end
    end
end
H.check('HPA* 비용 >= A* 비용', bad, 0)

-- ---- 클러스터와 전이
local m1 = MAPS[0]
H.check('클러스터 한 변', A.CLUSTER, 8)
H.check('32x32 맵의 클러스터 수',
        math.floor(m1.w / 8) * math.floor(m1.h / 8), 16)
local cx, cy = A.cluster_of(0, 0)
H.check('cluster_of(0,0)', {[0] = cx, cy, n = 2}, {[0] = 0, 0, n = 2})
cx, cy = A.cluster_of(8, 8)
H.check('cluster_of(8,8)', {[0] = cx, cy, n = 2}, {[0] = 1, 1, n = 2})
local ents = A.entrances(m1, 0)
H.check_true(string.format('빈 들판에도 전이가 있다 (%d개)', ents.n), ents.n > 0)
local adj = true
for k = 0, ents.n - 1 do
    local e = ents[k]
    local dx = e[1] - e[3]; if dx < 0 then dx = -dx end
    local dy = e[2] - e[4]; if dy < 0 then dy = -dy end
    if dx + dy ~= 1 then adj = false end
end
H.check_true('전이는 이웃한 두 칸을 잇는다', adj)

-- ---- 구간 길이에 따른 전이 개수 (SPEC §9.2)
local id = function(v) return v end
local function run(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end
H.check('길이 1 구간은 전이 1개', A._place(run(5), id).n, 1)
H.check('길이 5 구간은 전이 1개', A._place(run(1, 2, 3, 4, 5), id).n, 1)
H.check('길이 5 구간의 위치는 가운데', A._place(run(1, 2, 3, 4, 5), id),
        {[0] = 3, n = 1})
H.check('길이 6 구간은 양 끝 2개', A._place(run(1, 2, 3, 4, 5, 6), id),
        {[0] = 1, 6, n = 2})
H.check('빈 구간은 전이 없음', A._place(run(), id), {n = 0})

-- ---- 정련 (SPEC §9.4)
local m3 = MAPS[3]
local s, t = m3.pairs[0][0], m3.pairs[0][1]
local cost, nodes = A.search(m3, 0, s, t)
local tiles = A.refine(m3, 0, nodes)
H.check_true('정련 결과가 출발에서 시작한다', tiles[0] == s[1] * m3.w + s[0])
H.check_true('정련 결과가 도착에서 끝난다',
             tiles[tiles.n - 1] == t[1] * m3.w + t[0])

-- ---- 추상 그래프는 맵 버전마다 다시 짓는다
local a1 = A.abstract(m1, 0)
local a2 = A.abstract(m1, 0)
H.check('같은 버전이면 같은 그래프 객체', a1 == a2, true)
m1:set_terrain(4, 4, T.ROCK)
local a3 = A.abstract(m1, 0)
H.check('버전이 바뀌면 다시 짓는다', a3 == a1, false)
m1:set_terrain(4, 4, T.DIRT)

return H.done()
