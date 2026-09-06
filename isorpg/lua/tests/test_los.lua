-- 시야 — 브레젠험, 대칭성, 안개, 조명 단계.

local H = require("tests.harness")
local M = require("isorpg.gamemap")
local L = require("isorpg.los")

H.title('los')

-- ---- 브레젠험 기본 성질
H.check('한 점', L.line(3, 3, 3, 3), {{3, 3}})
H.check('가로', L.line(0, 0, 4, 0), {{0, 0}, {1, 0}, {2, 0}, {3, 0}, {4, 0}})
H.check('대각', L.line(0, 0, 3, 3), {{0, 0}, {1, 1}, {2, 2}, {3, 3}})
local bad = 0
for x1 = -12, 12 do
  for y1 = -12, 12 do
    local pts = L.line(0, 0, x1, y1)
    if pts[1][1] ~= 0 or pts[1][2] ~= 0
       or pts[#pts][1] ~= x1 or pts[#pts][2] ~= y1 then
      bad = bad + 1
    end
    for i = 1, #pts - 1 do
      local dx = pts[i + 1][1] - pts[i][1]
      local dy = pts[i + 1][2] - pts[i][2]
      if dx < 0 then dx = -dx end
      if dy < 0 then dy = -dy end
      if dx > 1 or dy > 1 or (dx == 0 and dy == 0) then bad = bad + 1 end
    end
    local ax = x1 < 0 and -x1 or x1
    local ay = y1 < 0 and -y1 or y1
    if #pts ~= (ax > ay and ax or ay) + 1 then bad = bad + 1 end
  end
end
H.check('브레젠험 25x25 성질 (끝점·연결성·길이)', bad, 0)

-- ---- 뒤집으면 같은 점 집합인가 (대칭성은 보장되지 않는다 — 실제로 세어 본다)
local function pointset(pts)
  local s = {}
  for i = 1, #pts do s[pts[i][1] .. ',' .. pts[i][2]] = true end
  return s
end
local function set_eq(a, b)
  for k in pairs(a) do if not b[k] then return false end end
  for k in pairs(b) do if not a[k] then return false end end
  return true
end
local asym = 0
for x1 = -12, 12 do
  for y1 = -12, 12 do
    if not set_eq(pointset(L.line(0, 0, x1, y1)), pointset(L.line(x1, y1, 0, 0))) then
      asym = asym + 1
    end
  end
end
H.note('브레젠험 역방향과 다른 선 %d개 / 625', asym)

local m = M.gen_map()

-- ---- 벽 너머는 안 보인다
H.check_true('자기 자신은 보인다', L.visible(m, 24, 25, 24, 25))
H.check_true('북문(24,18)은 길이라 그 너머가 보인다', L.visible(m, 24, 25, 24, 17))
H.check_true('벽(22,18) 너머는 안 보인다', not L.visible(m, 22, 25, 22, 16))

-- ---- 안개
local fog = L.new_fog(48, 48)
H.check('처음엔 아무것도 안 봤다', fog:count_seen(), 0)
fog:update(m, 24, 34)
local seen1 = fog:count_seen()
local vis1 = fog:count_visible()
H.check_true(string.format('갱신하면 주변이 보인다 (%d칸)', vis1), vis1 > 0)
H.check_true('본 칸 >= 보이는 칸', seen1 >= vis1)
local inr = true
for y = 0, 47 do
  for x = 0, 47 do
    if fog:is_visible(x, y) then
      local dx = x - 24
      local dy = y - 34
      if dx < 0 then dx = -dx end
      if dy < 0 then dy = -dy end
      if not (dx <= L.SIGHT_R and dy <= L.SIGHT_R) then inr = false end
    end
  end
end
H.check_true('시야 반경 안에만 보인다', inr)
fog:update(m, 24, 30)
H.check_true('한 번 본 칸은 기억한다', fog:count_seen() >= seen1)
H.check_true('시야 반경 밖은 보이지 않는다', not fog:is_visible(24, 45))
fog:update(m, 24, 20)
H.check_true(string.format('멀어져도 기억은 남는다 (%d칸)', fog:count_seen()),
             fog:is_seen(24, 34) and not fog:is_visible(24, 34))

-- ---- 조명 단계
fog:update(m, 24, 34)
H.check('발밑은 가장 밝다', fog:light_of(24, 34, 24, 34), 15)
H.check_true('멀수록 어둡다',
             fog:light_of(30, 34, 24, 34) < fog:light_of(25, 34, 24, 34))
local lr = true
for y = 0, 47 do
  for x = 0, 47 do
    if fog:is_visible(x, y) then
      local l = fog:light_of(x, y, 24, 34)
      if not (l >= 7 and l <= 15) then lr = false end
    end
  end
end
H.check_true('보이는 칸의 조명은 7..15', lr)
H.check('안 본 칸은 0', fog:light_of(0, 0, 24, 34), 0)

H.done()
