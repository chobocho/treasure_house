-- 화면 좌표 → 헥스 — SPEC §4
--
-- 마스크 표는 파일에서 읽지 않고 코드가 만든다. 세 언어가 같은 규칙으로
-- 만들었는지 자체가 검사 대상이기 때문이다(golden/pick_mask.txt 와 대조).

local hexmap = require('hexwar.hexmap')

local M = {}

M.HEX_W, M.HEX_H, M.ROW_STEP, M.ODD_SHIFT = 32, 32, 24, 16

-- SPEC §4.3 의 768바이트 마스크. 규칙에서 만들되, 만들어진 표가
-- golden/pick_mask.txt 와 같은지 테스트가 확인한다.
function M.build_mask()
  local m = {}
  for oy = 0, M.ROW_STEP - 1 do
    for ox = 0, M.HEX_W - 1 do
      local v = 0
      if oy < 8 and ox < 16 - 2 * oy then
        v = 1
      elseif oy < 8 and ox >= 16 + 2 * oy then
        v = 2
      end
      m[oy * M.HEX_W + ox] = v
    end
  end
  return m
end

M.PICK_MASK = M.build_mask()

function M.hex_origin(col, row)
  return col * M.HEX_W + (row & 1) * M.ODD_SHIFT, row * M.ROW_STEP
end

function M.hex_center(col, row)
  local x, y = M.hex_origin(col, row)
  return x + M.HEX_W // 2, y + M.HEX_H // 2
end

function M.nw_neighbor(col, row) return col - 1 + (row & 1), row - 1 end
function M.ne_neighbor(col, row) return col + (row & 1), row - 1 end

-- 화면 (mx,my) 아래의 헥스. 맵 밖이면 nil.
-- `//` 는 내림 나눗셈이라 카메라가 음수여도 그대로 맞는다.
function M.pick(mx, my, camx, camy, w, h)
  w = w or hexmap.MAP_W
  h = h or hexmap.MAP_H
  local yy = my + camy
  local by = yy // M.ROW_STEP
  local oy = yy - by * M.ROW_STEP
  local xx = mx + camx - (by & 1) * M.ODD_SHIFT
  local bx = xx // M.HEX_W
  local ox = xx - bx * M.HEX_W

  local v = M.PICK_MASK[oy * M.HEX_W + ox]
  local col, row
  if v == 0 then
    col, row = bx, by
  elseif v == 1 then
    col, row = M.nw_neighbor(bx, by)
  else
    col, row = M.ne_neighbor(bx, by)
  end
  if col >= 0 and col < w and row >= 0 and row < h then
    return col, row
  end
  return nil
end

return M
