-- 쿼터뷰 투영과 역투영 — SPEC §3.
--
--   두 방향 모두 정수만 쓴다. 루아에서 특히 조심할 것은 나눗셈이다.
--   px + 2*py 를 32로 나눌 때 / 만 쓰면 실수가 되어 -0.5 같은 값이 남고,
--   그 뒤 string.format("%d", ...) 에서 바로 터진다. 그래서 전부 floordiv 다.
--
-- 배열 규약: PICK_MASK 는 1-기반이다. 오프셋 계산(oy*32 + ox)은 파이썬과 똑같이
--   0-기반으로 하고, 표를 짚는 순간에만 +1 한다.

local F = require("isorpg.fixed")

local floor = math.floor
local floordiv = F.floordiv
local FP_ONE = F.FP_ONE

local M = {}

M.TW = 32               -- 마름모 가로 지름
M.TH = 16               -- 마름모 세로 지름
M.TZ = 8                -- 높이 한 단계
M.SCR_W = 320
M.SCR_H = 200
M.MAP_W = 48
M.MAP_H = 48
M.MAXH = 15

M.HW = 16               -- TW/2
M.HH = 8                -- TH/2

local TW, TH, TZ, HW, HH = 32, 16, 8, 16, 8

-- 타일 -> 마름모 꼭대기 꼭짓점의 월드 픽셀. 두 값을 그대로 돌려준다
-- (루아에는 튜플이 없다 — 표를 만들면 프레임마다 쓰레기가 쌓인다).
function M.tile_to_screen(tx, ty, h)
  return HW * (tx - ty), HH * (tx + ty) - h * TZ
end

-- 16.16 타일 좌표 -> 월드 픽셀. 엔티티가 타일 사이에 있을 때 쓴다.
function M.world_to_screen(fx, fy, h)
  return floor((fx - fy) * HW / FP_ONE), floor((fx + fy) * HH / FP_ONE) - h * TZ
end

-- 대수적 역. 나눗셈 두 번이면 끝난다. (정리 3.2)
function M.screen_to_tile(px, py)
  return floor((px + 2 * py) / 32), floor((2 * py - px) / 32)
end

-- 마름모 정의(|u| + 2|v| <= 16)로 직접 찾는다 — 빠른 식을 검산하는 용도.
-- 경계 픽셀은 여러 마름모에 걸치므로 (tx+ty, tx) 가 큰 쪽을 택해 floor 규칙과 맞춘다.
function M.screen_to_tile_slow(px, py)
  local gx, gy = M.screen_to_tile(px, py)
  local bx, by, has = 0, 0, false
  for tx = gx - 2, gx + 2 do
    for ty = gy - 2, gy + 2 do
      local cx = HW * (tx - ty)
      local cy = HH * (tx + ty) + HH
      local u = px - cx
      local v = py - cy
      if u < 0 then u = -u end
      if v < 0 then v = -v end
      if u + 2 * v <= HW then
        if not has or (tx + ty > bx + by) or (tx + ty == bx + by and tx > bx) then
          bx, by, has = tx, ty, true
        end
      end
    end
  end
  if not has then return nil, nil end
  return bx, by
end

-- 32x16 모서리 마스크. 값은 2*A + (B+1) 로 0..3 네 가지뿐이다. (SPEC §3.4)
local PICK_MASK = {}
for oy = 0, TH - 1 do
  for ox = 0, TW - 1 do
    local a = floordiv(ox + 2 * oy, 32)
    local b = floordiv(2 * oy - ox, 32)
    PICK_MASK[oy * TW + ox + 1] = 2 * a + (b + 1)
  end
end
M.PICK_MASK = PICK_MASK

-- 도스식 역투영 — 나눗셈 두 번(사각형 찾기)과 표 조회 한 번.
function M.pick_mask(px, py)
  local rc = floor(px / TW)
  local rr = floor(py / TH)
  local ox = px - TW * rc
  local oy = py - TH * rr
  local m = PICK_MASK[oy * TW + ox + 1]
  local mh = floor(m / 2)
  return rc + rr + mh, rr - rc + (m - 2 * mh) - 1
end

M.MARGIN_X = HW
-- 세로 여백: 마름모 반, 최대 높이 15단계, 그리고 가장 큰 스프라이트(나무 32px)
M.MARGIN_Y = HH + 15 * TZ + 32

local MARGIN_X, MARGIN_Y = M.MARGIN_X, M.MARGIN_Y

-- 뷰포트에 걸치는 타일 범위. 네 모서리만 역투영하면 된다. (정리 3.3)
function M.visible_range(x0, y0, x1, y1)
  local ax0 = x0 - MARGIN_X
  local ax1 = x1 + MARGIN_X
  local ay0 = y0 - MARGIN_Y
  local ay1 = y1 + MARGIN_Y
  local tx0 = floor((ax0 + 2 * ay0) / 32)
  local tx1 = floor((ax1 + 2 * ay1) / 32)
  local ty0 = floor((2 * ay0 - ax1) / 32)
  local ty1 = floor((2 * ay1 - ax0) / 32)
  if tx0 < 0 then tx0 = 0 end
  if ty0 < 0 then ty0 = 0 end
  if tx1 > M.MAP_W - 1 then tx1 = M.MAP_W - 1 end
  if ty1 > M.MAP_H - 1 then ty1 = M.MAP_H - 1 end
  return tx0, ty0, tx1, ty1
end

return M
