-- 맵 자료구조 — SPEC §2
--
-- 루아 테이블은 1부터 세는 것이 관례지만, 여기서는 저장 인덱스를 0부터 쓴다.
-- 파이썬·타입스크립트와 인덱스가 한 칸이라도 어긋나면 골든 트레이스가 깨지고,
-- 무엇보다 row*W+col 이라는 도스식 주소 계산이 그대로 살아야 하기 때문이다.
-- 대신 길이를 `#t` 로 알 수 없으므로 항상 w*h 를 따로 들고 다닌다.

local M = {}

M.MAP_W, M.MAP_H = 24, 18
M.MAP_N = M.MAP_W * M.MAP_H

M.TERRAIN_MASK = 0x0F
M.ELEV_SHIFT, M.ELEV_MASK = 4, 0x07
M.ROAD_BIT = 0x80

function M.pack_cell(terrain, elev, road)
  return ((road & 1) << 7) | ((elev & M.ELEV_MASK) << 4) | (terrain & M.TERRAIN_MASK)
end

function M.cell_terrain(c) return c & M.TERRAIN_MASK end
function M.cell_elev(c) return (c >> 4) & M.ELEV_MASK end
function M.cell_road(c) return (c >> 7) & 1 end

M.CLEAR, M.FOREST, M.HILL, M.MOUNTAIN = 0, 1, 2, 3
M.CITY, M.RIVER, M.SWAMP, M.SEA = 4, 5, 6, 7

--            key         이름     이동 방어 차단 높이 글자
M.TERRAIN = {
  [0] = { 'CLEAR', '평지', 2, 0, 0, 0, '.' },
  { 'FOREST', '숲', 4, 2, 1, 1, 'f' },
  { 'HILL', '언덕', 4, 1, 0, 1, 'h' },
  { 'MOUNTAIN', '산', 6, 3, 1, 2, 'M' },
  { 'CITY', '도시', 2, 4, 1, 1, 'C' },
  { 'RIVER', '강', 6, 1, 0, 0, '~' },
  { 'SWAMP', '늪', 6, 0, 0, 0, 's' },
  { 'SEA', '바다', -1, 0, 0, 0, '#' },
}
M.T_MOVE, M.T_DEF, M.T_BLOCK, M.T_LOSH, M.T_CHAR = {}, {}, {}, {}, {}
M.CHAR_TO_TERRAIN = {}
for i = 0, 7 do
  local t = M.TERRAIN[i]
  M.T_MOVE[i], M.T_DEF[i], M.T_BLOCK[i], M.T_LOSH[i], M.T_CHAR[i] = t[3], t[4], t[5], t[6], t[7]
  M.CHAR_TO_TERRAIN[t[7]] = i
end

M.FOG_HIDDEN, M.FOG_EXPLORED, M.FOG_VISIBLE = 0, 1, 2

-- odd-r 이웃 델타 — [행 홀짝][방향 0..5]
M.NEIGHBOR_DELTA = {
  [0] = { [0] = { 1, 0 }, { 0, -1 }, { -1, -1 }, { -1, 0 }, { -1, 1 }, { 0, 1 } },
  [1] = { [0] = { 1, 0 }, { 1, -1 }, { 0, -1 }, { -1, 0 }, { 0, 1 }, { 1, 1 } },
}

local HexMap = {}
HexMap.__index = HexMap
M.HexMap = HexMap

function M.new(w, h)
  w = w or M.MAP_W
  h = h or M.MAP_H
  local self = setmetatable({ w = w, h = h, n = w * h, cells = {}, fog = {}, occupant = {} }, HexMap)
  for i = 0, self.n - 1 do
    self.cells[i], self.fog[i], self.occupant[i] = 0, 0, -1
  end
  return self
end

function HexMap:idx(col, row) return row * self.w + col end

function HexMap:in_bounds(col, row)
  return col >= 0 and col < self.w and row >= 0 and row < self.h
end

function HexMap:axial_idx(q, r)
  local H = require('hexwar.hexcoord')
  local col, row = H.axial_to_oddr(q, r)
  if col >= 0 and col < self.w and row >= 0 and row < self.h then
    return row * self.w + col
  end
  return -1
end

function HexMap:idx_axial(i)
  local H = require('hexwar.hexcoord')
  local row = i // self.w
  local col = i - row * self.w
  return H.oddr_to_axial(col, row)
end

function HexMap:terrain_at(i) return self.cells[i] & M.TERRAIN_MASK end
function HexMap:elev_at(i) return (self.cells[i] >> 4) & M.ELEV_MASK end
function HexMap:road_at(i) return (self.cells[i] >> 7) & 1 end

function HexMap:set_cell(col, row, terrain, elev, road)
  self.cells[row * self.w + col] = M.pack_cell(terrain, elev or 0, road or 0)
end

function HexMap:passable(i)
  return M.T_MOVE[self.cells[i] & M.TERRAIN_MASK] >= 0
end

-- (방향, 이웃 인덱스) 쌍 목록. 방향 순서는 항상 0..5 오름차순이라
-- 세 언어의 탐색 순서가 같다.
function HexMap:neighbors_with_dir(i)
  local row = i // self.w
  local col = i - row * self.w
  local deltas = M.NEIGHBOR_DELTA[row & 1]
  local out, k = {}, 0
  for d = 0, 5 do
    local dd = deltas[d]
    local c, r = col + dd[1], row + dd[2]
    if c >= 0 and c < self.w and r >= 0 and r < self.h then
      k = k + 1
      out[k] = { d, r * self.w + c }
    end
  end
  return out, k
end

function HexMap:to_text()
  local lines = {}
  for row = 0, self.h - 1 do
    local a, b = {}, {}
    for col = 0, self.w - 1 do
      local c = self.cells[row * self.w + col]
      a[#a + 1] = M.T_CHAR[c & M.TERRAIN_MASK]
      b[#b + 1] = tostring((c >> 4) & M.ELEV_MASK)
    end
    lines[#lines + 1] = table.concat(a)
    lines[#lines + 1] = table.concat(b)
  end
  return table.concat(lines, '\n')
end

function HexMap:fog_text()
  local lines = {}
  for row = 0, self.h - 1 do
    local a = {}
    for col = 0, self.w - 1 do
      a[#a + 1] = tostring(self.fog[row * self.w + col])
    end
    lines[#lines + 1] = table.concat(a)
  end
  return table.concat(lines, '\n')
end

return M
