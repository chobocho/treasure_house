-- 시야·안개·조명 — SPEC §9.
--
--   브레젠험 직선 하나로 셋을 다 만든다.
--
-- 배열 규약: line() 이 돌려주는 점 목록은 1-기반 배열이고 각 점은 {x, y} 다.
--   Fog.bits 는 타일 (x, y) 를 bits[y*w + x + 1] 로 짚는다.

local M2 = require("isorpg.gamemap")
local F = require("isorpg.fixed")

local floor = math.floor
local oct_dist = F.oct_dist
local OPAQUE = M2.OPAQUE

local M = {}

M.EYE = 2
M.SIGHT_R = 9

-- 브레젠험 정수 직선. 양 끝을 포함한다.
-- err 는 '이상적 직선에서 벗어난 양'을 2*dx 배로 확대해 정수로 들고 다니는 값이라
-- 나눗셈도 실수도 없이 어느 축을 밟을지 정할 수 있다.
function M.line(x0, y0, x1, y1)
  local dx = x1 - x0
  if dx < 0 then dx = -dx end
  local dy = y1 - y0
  if dy < 0 then dy = -dy end
  dy = -dy
  local sx = x0 < x1 and 1 or -1
  local sy = y0 < y1 and 1 or -1
  local err = dx + dy
  local x, y = x0, y0
  local out = {}
  while true do
    out[#out + 1] = {x, y}
    if x == x1 and y == y1 then return out end
    local e2 = 2 * err
    if e2 >= dy then
      err = err + dy
      x = x + sx
    end
    if e2 <= dx then
      err = err + dx
      y = y + sy
    end
  end
end

-- (sx,sy) 에서 (gx,gy) 가 보이는가. 중간 칸만 검사한다.
-- 양 끝보다 EYE-1 단계 넘게 솟은 칸이 있으면 막힌다 — 진짜 3D 광선은 쏘지 않는다.
function M.visible(m, sx, sy, gx, gy)
  if sx == gx and sy == gy then return true end
  if not (gx >= 0 and gx < m.w and gy >= 0 and gy < m.h) then return false end
  local hs = m:height(sx, sy)
  local hg = m:height(gx, gy)
  local top = (hs > hg and hs or hg) + M.EYE - 1
  local pts = M.line(sx, sy, gx, gy)
  for i = 2, #pts - 1 do
    local p = pts[i]
    local x, y = p[1], p[2]
    if not (x >= 0 and x < m.w and y >= 0 and y < m.h) then return false end
    if OPAQUE[m:terrain(x, y) + 1] then return false end
    if m:height(x, y) > top then return false end
  end
  return true
end

-- ---------------------------------------------------------------- 안개
-- 타일마다 2비트. bit0 = 본 적 있다, bit1 = 지금 보인다.
local Fog = {}
Fog.__index = Fog
M.Fog = Fog

function M.new_fog(w, h)
  local bits = {}
  for i = 1, w * h do bits[i] = 0 end
  return setmetatable({w = w, h = h, bits = bits, n_seen = 0, n_vis = 0}, Fog)
end

function Fog:is_seen(x, y)
  local v = self.bits[y * self.w + x + 1]
  return v - 2 * floor(v / 2) == 1
end

function Fog:is_visible(x, y)
  local v = self.bits[y * self.w + x + 1]
  return floor(v / 2) == 1
end

function Fog:count_seen()
  return self.n_seen
end

function Fog:count_visible()
  return self.n_vis
end

-- 비트에서 누적 개수를 다시 센다. 세이브를 되돌린 직후에 부른다.
-- 개수는 세이브에 넣지 않는다 — 비트에서 유도되는 값이라 넣으면 같은 사실이
-- 두 곳에 적히고, 둘이 어긋나면 어느 쪽이 옳은지 알 수 없다.
function Fog:recount()
  local seen, vis = 0, 0
  local bits = self.bits
  for i = 1, self.w * self.h do
    local v = bits[i]
    if v - 2 * floor(v / 2) == 1 then seen = seen + 1 end
    if floor(v / 2) - 2 * floor(v / 4) == 1 then vis = vis + 1 end
  end
  self.n_seen = seen
  self.n_vis = vis
end

-- 지금 보이는 칸을 다시 세운다. 기억(bit0)은 지우지 않는다.
function Fog:update(m, px, py)
  local bits = self.bits
  local w = self.w
  for i = 1, w * self.h do
    local v = bits[i]
    bits[i] = v - 2 * floor(v / 2)
  end
  local R = M.SIGHT_R
  local x0, x1 = px - R, px + R
  local y0, y1 = py - R, py + R
  if x0 < 0 then x0 = 0 end
  if y0 < 0 then y0 = 0 end
  if x1 > w - 1 then x1 = w - 1 end
  if y1 > self.h - 1 then y1 = self.h - 1 end
  local seen = self.n_seen
  local vis = 0
  local rr = R * R
  for y = y0, y1 do
    local dy = y - py
    local row = y * w
    for x = x0, x1 do
      local dx = x - px
      -- 정사각형이 아니라 원 안만 본다 — 사각형 모서리는 반경 밖이다
      if dx * dx + dy * dy <= rr then
        if M.visible(m, px, py, x, y) then
          if bits[row + x + 1] == 0 then seen = seen + 1 end
          bits[row + x + 1] = 3        -- 지금 보이면 본 적도 있는 것이다
          vis = vis + 1
        end
      end
    end
  end
  self.n_seen = seen
  self.n_vis = vis
end

-- 조명 단계 0..15. 지금 보이면 거리에 따라, 기억만 있으면 4, 아니면 0.
function Fog:light_of(x, y, px, py)
  local v = self.bits[y * self.w + x + 1]
  local hi = floor(v / 2)
  if hi - 2 * floor(hi / 2) == 1 then
    local d = oct_dist((x - px) * 256, (y - py) * 256)
    local l = 15 - floor(8 * d / (M.SIGHT_R * 256))
    if l < 7 then return 7 end
    if l > 15 then return 15 end
    return l
  end
  if v - 2 * floor(v / 2) == 1 then return 4 end
  return 0
end

return M
