-- 지형 맵 — 오토타일·통행·연결 성분·RLE (SPEC §4).

local H = require('tests.harness')
local T = require('rts.tmap')
local F = require('rts.fixed')

H.title('tmap')

local m = T.new(8, 8)

-- ---- 좌표와 경계 (SPEC §4.2)
H.check('idx(3,2)', m:idx(3, 2), 2 * 8 + 3)
H.check('in_map(0,0)', m:in_map(0, 0), true)
H.check('in_map(-1,0)', m:in_map(-1, 0), false)
H.check('맵 밖은 ROCK', m:terrain_at(-1, 0), T.ROCK)
H.check('맵 밖은 ROCK (오른쪽)', m:terrain_at(8, 0), T.ROCK)

-- ---- 통행 비트 (SPEC §4.3)
m:set_terrain(1, 1, T.DIRT)
m:set_terrain(2, 1, T.WATER)
m:set_terrain(3, 1, T.HILL)
m:set_terrain(4, 1, T.ORE)
H.check('흙은 보병 통행', m:walkable(1, 1, 0), true)
H.check('흙은 차량 통행', m:walkable(1, 1, 1), true)
H.check('물은 통행 불가', m:walkable(2, 1, 0), false)
H.check('언덕은 보병만', m:walkable(3, 1, 0), true)
H.check('언덕은 차량 불가', m:walkable(3, 1, 1), false)
H.check('광맥은 통행 가능', m:walkable(4, 1, 0), true)
H.check('광맥은 건설 불가', m:buildable(4, 1), false)
H.check('흙은 건설 가능', m:buildable(1, 1), true)
m:occupy(1, 1, true)
H.check('점유되면 통행 불가', m:walkable(1, 1, 0), false)
H.check('점유는 경로 탐색이 보지 않는 비트', T.OCC_BIT, 3)
m:occupy(1, 1, false)
H.check('점유 해제', m:walkable(1, 1, 0), true)

-- ---- 오토타일 정규화 (SPEC §4.4) — 골든 5절과 대조
local rows = H.lines(H.golden('prim.txt'))
local i = H.index_of(rows, '== 5. 오토타일 ==')
H.check('클래스 개수', T.CLASS_COUNT,
        tonumber(H.split(rows[i + 1])[1]:match('^(%d+)')))
local bad = 0
for r = 0, 15 do
    local want = H.ints(rows[i + 3 + r])
    local got = {n = 16}
    for c = 0, 15 do got[c] = T.canon_index(T.canon(r * 16 + c)) end
    if not H.deep_eq(want, got) then
        bad = bad + 1
        H.note('행 %d 기대 %s 실제 %s', r, H.repr(want), H.repr(got))
    end
end
H.check('256개 마스크의 정규화 인덱스가 골든과 같다', bad, 0)

local N, NE, E, W = 1, 2, 4, 64
H.check('모서리는 양옆이 있어야 산다', T.canon(NE), 0)
H.check('N+E 가 있으면 NE 가 산다', T.canon(N + E + NE), N + E + NE)
H.check('N 만 없으면 NE 는 죽는다', T.canon(E + NE), E)
H.check('canon 은 멱등', T.canon(T.canon(255)), T.canon(255))

-- ---- 이웃 마스크
local m2 = T.new(5, 5)
for y = 0, 4 do
    for x = 0, 4 do m2:set_terrain(x, y, T.SAND) end
end
m2:set_terrain(2, 2, T.DIRT)
H.check('혼자 있는 칸의 마스크는 0', m2:mask(2, 2), 0)
m2:set_terrain(2, 1, T.DIRT)
H.check('북쪽만 같으면 마스크는 N', m2:mask(2, 2), N)
H.check('가장자리 칸은 맵 밖을 ROCK 으로 본다',
        F.bit(m2:mask(0, 0), 6) * W, 0)

-- ---- 4모서리 마스크 (SPEC §4.5)
H.check('corner_mask 는 0..15', T.corner_mask({[0] = 0, 0, 0, 0}), 0)
H.check('corner_mask 전부', T.corner_mask({[0] = 1, 1, 1, 1}), 15)
H.check('corner_mask 좌상단만', T.corner_mask({[0] = 1, 0, 0, 0}), 1)

-- ---- 연결 성분 (SPEC §4.6)
local m3 = T.new(8, 8)
for y = 0, 7 do
    for x = 0, 7 do m3:set_terrain(x, y, T.WATER) end
end
for _, p in ipairs({{1, 1}, {2, 1}, {1, 2}, {5, 5}, {6, 5}}) do
    m3:set_terrain(p[1], p[2], T.DIRT)
end
local lab = m3:labels(0)
H.check('두 덩어리는 다른 라벨',
        lab[m3:idx(1, 1)] ~= lab[m3:idx(5, 5)], true)
H.check('같은 덩어리는 같은 라벨', lab[m3:idx(1, 1)], lab[m3:idx(2, 1)])
H.check('대각으로도 이어진다', lab[m3:idx(1, 1)], lab[m3:idx(1, 2)])
H.check('물은 라벨 -1', lab[m3:idx(0, 0)], -1)
local v0 = m3.version
m3:set_terrain(3, 3, T.DIRT)
H.check_true('지형을 고치면 버전이 오른다', m3.version > v0)
H.check('라벨은 다시 계산된다', m3:labels(0)[m3:idx(3, 3)] >= 0, true)

-- ---- 차량용 라벨은 언덕에서 끊긴다
local m4 = T.new(5, 1)
for x = 0, 4 do m4:set_terrain(x, 0, T.DIRT) end
m4:set_terrain(2, 0, T.HILL)
H.check('보병은 이어진다', m4:labels(0)[0], m4:labels(0)[4])
H.check('차량은 끊긴다', m4:labels(1)[0] ~= m4:labels(1)[4], true)

-- ---- RLE 왕복 (SPEC §4.7)
-- 1103515245 * r 은 2^61 까지 커진다 — 루아에서는 분할 곱이 필요하다.
local function lcg31(r)
    local hi = math.floor(r / 65536)
    local lo = r % 65536
    return ((1103515245 * hi % 32768) * 65536 + 1103515245 * lo + 12345)
           % 2147483648
end
local m5 = T.new(64, 64)
local r = 1
for y = 0, 63 do
    for x = 0, 63 do
        r = lcg31(r)
        m5:set_terrain(x, y, r % 8)
    end
end
local blob = m5:save_rle()
local m6 = T.load_rle(blob)
H.check('RLE 왕복: 지형', m6.terrain, m5.terrain)
H.check('RLE 왕복: 통행', m6.pass_, m5.pass_)
H.check('헤더', blob:sub(1, 4), 'RTSM')
H.check_true(string.format('CRC 가 붙어 있다 (%d바이트)', #blob), #blob > 6)
local broken = blob:sub(1, 10) .. string.char((blob:byte(11) + 1) % 256)
                   .. blob:sub(12)
if pcall(function() T.load_rle(broken) end) then
    H.check('CRC 가 깨지면 터져야 한다', 'no raise', 'raise')
else
    H.check('CRC 가 깨지면 터져야 한다', 'raise', 'raise')
end

-- ---- 골든 맵 읽기
local g = T.load_text(H.golden('map_1.txt'))
H.check('map_1 크기', {[0] = g.w, g.h, n = 2}, {[0] = 32, 32, n = 2})
H.check('가장자리는 막혀 있다', g:walkable(0, 0, 0), false)
H.check('안쪽은 통행 가능', g:walkable(1, 1, 0), true)
H.check('시험 쌍 4개', g.pairs.n, 4)
local gs = T.load_text(H.golden('map_start.txt'))
H.check('시작 맵 크기', {[0] = gs.w, gs.h, n = 2}, {[0] = 64, 64, n = 2})
H.check('시작점 2개', gs.starts,
        {[0] = {[0] = 8, [1] = 8, n = 2}, {[0] = 55, [1] = 55, n = 2}, n = 2})
H.check('시작점 주변은 흙', gs:terrain_at(8, 8), T.DIRT)

-- ── SPEC §4.3 건물이 선 칸 ──────────────────────────────────────────────────
local bm = T.new(4, 4)
for y = 0, 3 do
    for x = 0, 3 do bm:set_terrain(x, y, T.DIRT) end
end
local bv = bm.version
bm:set_building(1, 1, true)
H.check('건물 칸은 보병·차량 통행 불가',
        {[0] = bm:passable_terrain(1, 1, 0), bm:passable_terrain(1, 1, 1), n = 2},
        {[0] = false, false, n = 2})
H.check('건물 칸은 건설도 불가', bm:buildable(1, 1), false)
H.check_true('건물은 version 을 올린다 — 경로 캐시가 무효가 된다',
             bm.version > bv)
bm:set_building(1, 1, false)
H.check('철거하면 통행이 돌아온다', bm:passable_terrain(1, 1, 0), true)
H.check('철거하면 점유 비트도 내려간다', bm:buildable(1, 1), true)
bm:set_building(2, 2, true)
bm:set_terrain(2, 2, T.RUBBLE)
H.check('잔해로 바꾸는 것만으로 통행이 복구된다 (§4.3)',
        bm:passable_terrain(2, 2, 0), true)

return H.done()
