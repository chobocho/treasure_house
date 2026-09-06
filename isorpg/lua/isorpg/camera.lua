-- 카메라 — SPEC §4. 정수 픽셀 스크롤과 데드존 추적.

local PR = require("isorpg.proj")

local M = {}

M.DEADZONE_X = 48
M.DEADZONE_Y = 24

-- 맵 전체가 차지하는 월드 픽셀 범위. 마름모 배치라 가로가 세로의 두 배다.
M.WORLD_X0 = -PR.HW * (PR.MAP_H - 1) - PR.HW
M.WORLD_X1 = PR.HW * (PR.MAP_W - 1) + PR.HW
M.WORLD_Y0 = -PR.MAXH * PR.TZ
M.WORLD_Y1 = 8 * (PR.MAP_W + PR.MAP_H - 2) + 16

local SCR_W, SCR_H = PR.SCR_W, PR.SCR_H

function M.clamp_cam(cx, cy)
  local lo_x, hi_x = M.WORLD_X0, M.WORLD_X1 - SCR_W
  local lo_y, hi_y = M.WORLD_Y0, M.WORLD_Y1 - SCR_H
  if cx < lo_x then cx = lo_x end
  if cx > hi_x then cx = hi_x end
  if cy < lo_y then cy = lo_y end
  if cy > hi_y then cy = hi_y end
  return cx, cy
end

-- 대상이 데드존을 벗어난 만큼만 카메라를 민다.
-- 매 프레임 중앙에 붙여 두면 걸을 때마다 화면이 흔들린다.
function M.follow(cx, cy, tgt_x, tgt_y)
  local dx = tgt_x - cx - 160
  local dy = tgt_y - cy - 100
  if dx > M.DEADZONE_X then
    cx = cx + dx - M.DEADZONE_X
  elseif dx < -M.DEADZONE_X then
    cx = cx + dx + M.DEADZONE_X
  end
  if dy > M.DEADZONE_Y then
    cy = cy + dy - M.DEADZONE_Y
  elseif dy < -M.DEADZONE_Y then
    cy = cy + dy + M.DEADZONE_Y
  end
  return M.clamp_cam(cx, cy)
end

return M
