-- 맵 — LCG, 다이아몬드-스퀘어, 셀 패킹, RLE 왕복.

local H = require("tests.harness")
local M = require("isorpg.gamemap")
local R = require("isorpg.rng")

local floor = math.floor

H.title('gamemap')

-- ---- LCG : 골든 앞 8개
local r = R.new(1)
local got = {}
for i = 1, 8 do
  local v = r:next()
  got[i] = {r.s, v}
end
H.check('seed 1 첫 상태', got[1], {22695478, 346})
H.check('seed 1 여덟째 상태', got[8], {420428313, 6415})
local inrange = true
for i = 1, 8 do
  if not (got[i][2] >= 0 and got[i][2] < 32768) then inrange = false end
end
H.check('rand15 범위', inrange, true)

-- ---- 분할 곱이 진짜 곱과 같은가 (2^53 우회로 검증)
--   파이썬은 큰 정수를 그냥 곱해 기준값을 얻지만 루아는 그럴 수 없다
--   (22695477 * 2^32 ~ 2^57). 그래서 rng 와는 **다른 방식으로** 쪼갠 기준을 쓴다.
--   rng 는 상태 s 를 쪼개고, 여기서는 승수 a 를 쪼갠다. 두 갈래가 2만 걸음 내내
--   같으면 어느 한쪽의 자릿수 실수는 배제된다.
local AH = floor(22695477 / 65536)                 -- 346
local AL = 22695477 - AH * 65536                   -- 20021
local function ref_next(s)
  local t = AH * s
  t = t - 65536 * floor(t / 65536)                 -- (a_hi * s) mod 2^16
  local v = t * 65536 + AL * s + 1
  return v - 4294967296 * floor(v / 4294967296)
end
local s = 1
local bad = 0
for _ = 1, 20000 do
  local want = ref_next(s)
  local r2 = R.new(s)
  r2:next()
  if r2.s ~= want then bad = bad + 1 end
  s = want
end
H.check('분할 곱 == (a*s+c) mod 2^32 (2만 걸음)', bad, 0)

-- ---- Hull-Dobell 조건
H.check('gcd(c, m) = 1', R.LCG_C - 2 * floor(R.LCG_C / 2), 1)
H.check('(a-1) 이 2로 나누어짐', (R.LCG_A - 1) - 2 * floor((R.LCG_A - 1) / 2), 0)
H.check('(a-1) 이 4로 나누어짐', (R.LCG_A - 1) - 4 * floor((R.LCG_A - 1) / 4), 0)

-- ---- 주기: 하위 비트는 주기가 짧다 (도스 시절의 유명한 함정)
local seen = {}
s = 1
for i = 1, 16 do
  s = ref_next(s)
  seen[i] = s - 2 * floor(s / 2)
end
local alt = {}
for i = 1, 8 do alt[#alt + 1] = 0; alt[#alt + 1] = 1 end
H.check('상태 최하위 비트는 0,1 을 번갈아 (주기 2)', seen, alt)

-- ---- 셀 패킹
for t = 0, 15 do
  for h = 0, 15 do
    local c = M.make_cell(t, h)
    H.check_true(string.format('패킹 t=%d h=%d', t, h),
                 M.terrain_of(c) == t and M.height_of(c) == h and c >= 0 and c < 256)
  end
end

-- ---- 다이아몬드-스퀘어 5x5 골든
local mini = M.gen_height(4, {50, 60, 70, 80}, 100, 1)
H.check('5x5 격자', mini,
        {{50, 40, 103, 132, 60}, {86, 130, 106, 72, 72}, {104, 73, 110, 94, 68},
         {82, 156, 116, 68, 130}, {70, 88, 185, 145, 80}})
H.check('두 번 돌려도 같은가', M.gen_height(4, {50, 60, 70, 80}, 100, 1), mini)

-- ---- 실제 맵
local m = M.gen_map()
H.check('맵 크기', {m.w, m.h, #m.cells}, {48, 48, 48 * 48})
local ok255, ok15 = true, true
for i = 1, #m.cells do
  local c = m.cells[i]
  if not (c >= 0 and c < 256) then ok255 = false end
  if M.height_of(c) > 15 then ok15 = false end
end
H.check_true('모든 셀이 0..255', ok255)
H.check_true('높이는 0..15', ok15)

-- ---- 마을이 제대로 찍혔는가
local corners = {}
local CP = {{18, 18}, {29, 18}, {18, 29}, {29, 29}}
for i = 1, 4 do corners[i] = M.terrain_of(m:at(CP[i][1], CP[i][2])) end
H.check('마을 네 귀퉁이는 벽', corners,
        {M.T_WALL, M.T_WALL, M.T_WALL, M.T_WALL})
H.check('남문은 길', M.terrain_of(m:at(24, 29)), M.T_ROAD)
local hs = {}
for y = 18, 29 do
  for x = 18, 29 do hs[M.height_of(m:at(x, y))] = true end
end
local hl = {}
for v = 0, 15 do if hs[v] then hl[#hl + 1] = v end end
H.check('마을 바닥은 높이 2, 성벽은 4', hl, {2, 4})
local wall = {}
for x = 19, 23 do wall[#wall + 1] = M.terrain_of(m:at(x, 18)) end
H.check('성벽 한 줄', wall, {M.T_WALL, M.T_WALL, M.T_WALL, M.T_WALL, M.T_WALL})
local road = {}
for _, y in ipairs({31, 35, 40, 47}) do road[#road + 1] = M.terrain_of(m:at(24, y)) end
H.check('마을 남쪽 길', road, {M.T_ROAD, M.T_ROAD, M.T_ROAD, M.T_ROAD})
local ts, hs2 = {}, {}
local nt, nh = 0, 0
for i = 1, #m.cells do
  local t = M.terrain_of(m.cells[i])
  local h = M.height_of(m.cells[i])
  if not ts[t] then ts[t] = true; nt = nt + 1 end
  if not hs2[h] then hs2[h] = true; nh = nh + 1 end
end
H.check_true('지형이 7종 이상 나온다', nt >= 7)
H.check_true('높이가 5단계 이상 나온다', nh >= 5)

-- ---- RLE 왕복
local text = M.save_rle(m)
local m2 = M.load_rle(text)
H.check('RLE 왕복', m2.cells, m.cells)
H.check('RLE 다시 저장해도 같은 글자', M.save_rle(m2), text)
-- 런 하나는 (개수, 값) 두 바이트다. 텍스트 형식은 사람이 읽으려고 늘려 쓴 것이라
-- 원본보다 길다 — 정직하게 둘 다 센다.
local tl = H.lines(text)
local runs = 0
for i = 2, #tl do
  for _ in tl[i]:gmatch('%S+') do runs = runs + 1 end
end
H.note('셀 %d개 -> 런 %d개 (이진 RLE %d바이트, 텍스트 %d바이트)',
       #m.cells, runs, runs * 2, #text)
H.check_true('이진 RLE 는 원본보다 짧다', runs * 2 < #m.cells)
H.check_true('평균 런 길이가 2.5 이상', floor(#m.cells * 10 / runs) >= 25)

-- ---- 골든 파일과 같은가
H.check('golden/map.txt', text, H.golden('map.txt'))

H.done()
