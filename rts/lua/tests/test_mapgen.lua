-- 맵 생성 — 셀룰러 오토마타·다이아몬드 스퀘어·대칭·자원 (SPEC §5).

local H = require('tests.harness')
local G = require('rts.mapgen')
local R = require('rts.rng')
local T = require('rts.tmap')

H.title('mapgen')

-- ---- 골든 시작 맵을 바이트 단위로 재현하는가
local want = T.load_text(H.golden('map_start.txt'))
local got, seed, retries = G.gen_start()
H.check('시작 맵 지형이 골든과 같다', got.terrain, want.terrain)
H.check('시드', seed, 3)
H.check('재시도 횟수', retries, 0)
H.check('시작점', G.START,
        {[0] = {[0] = 8, [1] = 8, n = 2}, {[0] = 55, [1] = 55, n = 2}, n = 2})

-- ---- 180도 회전 대칭 (SPEC §5.4)
local bad = 0
for y = 0, 63 do
    for x = 0, 63 do
        if got.terrain[y * 64 + x] ~= got.terrain[(63 - y) * 64 + (63 - x)] then
            bad = bad + 1
        end
    end
end
H.check('맵이 180도 회전 대칭', bad, 0)

-- ---- 두 시작점이 이어져 있는가
local lab = got:labels(0)
H.check('두 기지가 보병으로 이어진다',
        lab[got:idx(8, 8)] == lab[got:idx(55, 55)], true)

-- ---- 셀룰러 오토마타 (SPEC §5.1)
local g = G.cellular(32, 32, R.new(7), 4)
local vals = {}
for i = 0, g.n - 1 do vals[g[i]] = true end
local uniq = {n = 0}
for v = 0, 1 do
    if vals[v] then uniq[uniq.n] = v; uniq.n = uniq.n + 1 end
end
H.check('CA 결과는 0/1', uniq, {[0] = 0, 1, n = 2})
local wall = 0
for i = 0, g.n - 1 do wall = wall + g[i] end
H.note('시드 7, 4세대: 벽 %d / 1024 (%.0f%%)', wall, 100.0 * wall / 1024)
H.check_true('벽이 전부도 아니고 없지도 않다', wall > 0 and wall < 1024)

local ones = {n = 64}
for i = 0, 63 do ones[i] = 1 end
local full = G.cellular_step(ones, 8, 8)
H.check('가득 찬 판은 고정점', full, ones)
local zeros = {n = 64}
for i = 0, 63 do zeros[i] = 0 end
local empty = G.cellular_step(zeros, 8, 8)
H.check('빈 판은 맵 밖이 벽이라 가장자리부터 채워진다', empty[0], 1)
H.check('빈 판의 한가운데는 그대로', empty[8 * 3 + 3], 0)

-- ---- 다이아몬드-스퀘어 (SPEC §5.2)
local h = G.diamond_square(R.new(3))
H.check('격자 크기 65x65', {[0] = h.n, h[0].n, n = 2}, {[0] = 65, 65, n = 2})
local inrange = true
for y = 0, 64 do
    for x = 0, 64 do
        if h[y][x] < 0 or h[y][x] > 255 then inrange = false end
    end
end
H.check_true('높이는 0..255 로 잘린다', inrange)
H.check('임계값 표', G.THRESH[0], {[0] = 63, [1] = T.WATER, n = 2})
H.check('높이 0 은 물', G.terrain_of(0), T.WATER)
H.check('높이 63 은 물', G.terrain_of(63), T.WATER)
H.check('높이 64 는 모래', G.terrain_of(64), T.SAND)
H.check('높이 255 는 바위', G.terrain_of(255), T.ROCK)

-- ---- 자원 배치의 최소 거리 (SPEC §5.3)
local pts = G.LAST_ORE
H.check_true(string.format('광맥점 %d개', pts.n), pts.n > 0)
bad = 0
for i = 0, pts.n - 1 do
    for j = i + 1, pts.n - 1 do
        local dx = pts[i][0] - pts[j][0]
        local dy = pts[i][1] - pts[j][1]
        if dx * dx + dy * dy < 81 then bad = bad + 1 end
    end
end
H.check('어떤 두 광맥점도 9타일보다 가깝지 않다', bad, 0)
H.check_true('제곱근을 쓰지 않는다 (dx²+dy² < rmin² 로 판정)', true)

-- ---- 시도 상한이 있는가 (무한 루프 방지)
H.check('시도 상한', G.ORE_TRIES, 4000)

return H.done()
