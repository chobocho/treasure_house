-- 지형 맵 — SPEC §5. 한 칸 1바이트, 다이아몬드-스퀘어 생성, RLE 저장.
--
--   모듈 이름이 map 이 아닌 것은 파이썬 내장 map 을 피하려던 것인데,
--   세 언어가 같은 파일 이름을 쓰기로 해서 루아도 gamemap 이다.
--
-- 배열 규약: 좌표 (x, y) 는 파이썬과 똑같이 0-기반이고, 셀 배열을 짚을 때만
--   +1 한다 — cells[y*w + x + 1]. 높이 격자 h 도 마찬가지로 h[y+1][x+1] 이다.
--   지형표(TERRAIN/MOVE/OPAQUE)는 지형 id 0..15 에 대해 [id+1] 로 읽는다.

local RNG = require("isorpg.rng")

local floor = math.floor

local M = {}

M.MAP_W = 48
M.MAP_H = 48
M.MAXH = 15

-- 지형 id — 셀 바이트의 하위 4비트
M.T_DEEP, M.T_WATER, M.T_SAND, M.T_GRASS = 0, 1, 2, 3
M.T_DIRT, M.T_ROCK, M.T_FOREST, M.T_MOUNTAIN = 4, 5, 6, 7
M.T_ROAD, M.T_FLOOR, M.T_WALL, M.T_BRIDGE = 8, 9, 10, 11
M.T_SNOW, M.T_SWAMP, M.T_LAVA, M.T_VOID = 12, 13, 14, 15

-- {이름, 이동비용 0=불가, 시야차단}
M.TERRAIN = {
  {'DEEP', 0, false}, {'WATER', 0, false}, {'SAND', 12, false},
  {'GRASS', 10, false}, {'DIRT', 10, false}, {'ROCK', 14, false},
  {'FOREST', 16, true}, {'MOUNTAIN', 0, true}, {'ROAD', 8, false},
  {'FLOOR', 10, false}, {'WALL', 0, true}, {'BRIDGE', 10, false},
  {'SNOW', 13, false}, {'SWAMP', 20, false}, {'LAVA', 0, false},
  {'VOID', 0, true},
}

M.MOVE = {}
M.OPAQUE = {}
for i = 1, 16 do
  M.MOVE[i] = M.TERRAIN[i][2]
  M.OPAQUE[i] = M.TERRAIN[i][3]
end

M.MIN_MOVE = 0
for i = 1, 16 do
  local v = M.MOVE[i]
  if v > 0 and (M.MIN_MOVE == 0 or v < M.MIN_MOVE) then M.MIN_MOVE = v end
end                                                -- ROAD 의 8

function M.make_cell(t, h)
  return t + h * 16
end

function M.terrain_of(cell)
  return cell - 16 * floor(cell / 16)
end

function M.height_of(cell)
  return floor(cell / 16)
end

-- ---------------------------------------------------------------- Map
local Map = {}
Map.__index = Map
M.Map = Map

function M.new_map(w, h, cells)
  if cells == nil then
    cells = {}
    for i = 1, w * h do cells[i] = 0 end
  end
  return setmetatable({w = w, h = h, cells = cells}, Map)
end

function Map:inside(x, y)
  return x >= 0 and x < self.w and y >= 0 and y < self.h
end

function Map:at(x, y)
  return self.cells[y * self.w + x + 1]
end

function Map:put(x, y, cell)
  self.cells[y * self.w + x + 1] = cell
end

function Map:terrain(x, y)
  local c = self.cells[y * self.w + x + 1]
  return c - 16 * floor(c / 16)
end

function Map:height(x, y)
  return floor(self.cells[y * self.w + x + 1] / 16)
end

-- ---------------------------------------------------------------- 다이아몬드-스퀘어
M.DS_N = 64
M.DS_SEED = 1
M.DS_CORNER = {520, 300, 700, 420}
M.DS_SCALE = 560
M.DS_ROUGH_NUM = 58
M.DS_ROUGH_DEN = 100
M.DS_OFF = floor((M.DS_N + 1 - M.MAP_W) / 2)       -- 65x65 에서 가운데 48x48 을 오려 쓴다

-- 프랙탈 중점 변위. 반복 순서가 난수 소비 순서를 정하므로 명세의 일부다.
-- O(n^2) 시간·공간. 격자는 (2^k + 1) 이어야 중점을 계속 반으로 접을 수 있다.
function M.gen_height(n, corners, scale, seed, rough_num, rough_den)
  rough_num = rough_num or M.DS_ROUGH_NUM
  rough_den = rough_den or M.DS_ROUGH_DEN
  local size = n + 1
  local h = {}
  for y = 1, size do
    local row = {}
    for x = 1, size do row[x] = 0 end
    h[y] = row
  end
  h[1][1] = corners[1]
  h[1][n + 1] = corners[2]
  h[n + 1][1] = corners[3]
  h[n + 1][n + 1] = corners[4]
  local r = RNG.new(seed)
  local step = n
  while step > 1 do
    local half = floor(step / 2)
    local span = 2 * scale + 1
    -- 다이아몬드: 정사각형 네 꼭짓점의 평균 + 흔들림
    local y = half
    while y < size do
      local x = half
      while x < size do
        local s = h[y - half + 1][x - half + 1] + h[y - half + 1][x + half + 1]
                + h[y + half + 1][x - half + 1] + h[y + half + 1][x + half + 1]
        local v = r:next()
        h[y + 1][x + 1] = floor(s / 4) + (v - span * floor(v / span) - scale)
        x = x + step
      end
      y = y + step
    end
    -- 스퀘어: 마름모 네 꼭짓점(격자 밖은 뺀다)의 평균 + 흔들림.
    -- 행 간격은 half, 열 간격은 step 이고 홀짝 행마다 시작 열이 어긋난다.
    y = 0
    while y < size do
      local q = floor(y / half)
      local x = (q - 2 * floor(q / 2)) == 0 and half or 0
      while x < size do
        local s, cnt = 0, 0
        if x - half >= 0 then s = s + h[y + 1][x - half + 1]; cnt = cnt + 1 end
        if x + half < size then s = s + h[y + 1][x + half + 1]; cnt = cnt + 1 end
        if y - half >= 0 then s = s + h[y - half + 1][x + 1]; cnt = cnt + 1 end
        if y + half < size then s = s + h[y + half + 1][x + 1]; cnt = cnt + 1 end
        local v = r:next()
        h[y + 1][x + 1] = floor(s / cnt) + (v - span * floor(v / span) - scale)
        x = x + step
      end
      y = y + half
    end
    step = half
    scale = floor(scale * rough_num / rough_den)
  end
  for y = 1, size do
    local row = h[y]
    for x = 1, size do
      local v = row[x]
      row[x] = v < 0 and 0 or (v > 1023 and 1023 or v)
    end
  end
  return h
end

M.DS_BLUR = 2

-- 3x3 상자 흐리기. 프랙탈 그대로는 타일 눈금에서 잡음처럼 보인다.
-- O(9 * n^2). 가장자리는 격자 안의 이웃만 평균한다.
function M.smooth(h)
  local n = #h
  for _ = 1, M.DS_BLUR do
    local g = {}
    for y = 1, n do
      local gr = {}
      for x = 1, n do
        local s, c = 0, 0
        for dy = -1, 1 do
          local yy = y + dy
          if yy >= 1 and yy <= n then
            local row = h[yy]
            for dx = -1, 1 do
              local xx = x + dx
              if xx >= 1 and xx <= n then
                s = s + row[xx]
                c = c + 1
              end
            end
          end
        end
        gr[x] = floor(s / c)
      end
      g[y] = gr
    end
    h = g
  end
  return h
end

-- 높이값 -> 지형. 문턱은 SPEC §5.5 가 정한다.
function M.terrain_of_value(v)
  if v < 100 then return 0 end
  if v < 205 then return 1 end
  if v < 240 then return 2 end
  if v < 460 then return 3 end
  if v < 630 then return 6 end
  if v < 800 then return 5 end
  return 7
end

function M.height_of_value(v)
  if v < 205 then return 0 end
  local hh = floor((v - 205) / 90)
  return hh > 12 and 12 or hh
end

M.TOWN_X0, M.TOWN_Y0, M.TOWN_X1, M.TOWN_Y1 = 18, 18, 30, 30
M.TOWN_MID = 24
M.TOWN_H = 2
M.TOWN_WALL_H = 4       -- 성벽은 바닥보다 두 단계 높다 — 그래야 옆면이 보인다

-- 마을을 찍는다. 순서가 중요하다 — 벽을 먼저 두르고 문을 나중에 뚫는다.
function M.stamp_town(m)
  local X0, Y0, X1, Y1, MID = M.TOWN_X0, M.TOWN_Y0, M.TOWN_X1, M.TOWN_Y1, M.TOWN_MID
  for ty = Y0, Y1 - 1 do
    for tx = X0, X1 - 1 do
      if tx == X0 or tx == X1 - 1 or ty == Y0 or ty == Y1 - 1 then
        m:put(tx, ty, M.make_cell(M.T_WALL, M.TOWN_WALL_H))
      else
        local t = (tx == MID or ty == MID) and M.T_ROAD or M.T_FLOOR
        m:put(tx, ty, M.make_cell(t, M.TOWN_H))
      end
    end
  end
  local gates = {{MID, Y0}, {MID, Y1 - 1}, {X0, MID}, {X1 - 1, MID}}
  for i = 1, 4 do
    m:put(gates[i][1], gates[i][2], M.make_cell(M.T_ROAD, M.TOWN_H))
  end
  for ty = 0, Y0 - 1 do
    m:put(MID, ty, M.make_cell(M.T_ROAD, M.TOWN_H))
  end
  for ty = Y1, M.MAP_H - 1 do
    m:put(MID, ty, M.make_cell(M.T_ROAD, M.TOWN_H))
  end
end

-- 맵 한 장. 같은 씨앗이면 언제나 같은 맵이다.
function M.gen_map()
  local hg = M.smooth(M.gen_height(M.DS_N, M.DS_CORNER, M.DS_SCALE, M.DS_SEED))
  local m = M.new_map(M.MAP_W, M.MAP_H)
  for ty = 0, M.MAP_H - 1 do
    local row = hg[ty + M.DS_OFF + 1]
    for tx = 0, M.MAP_W - 1 do
      local v = row[tx + M.DS_OFF + 1]
      m:put(tx, ty, M.make_cell(M.terrain_of_value(v), M.height_of_value(v)))
    end
  end
  M.stamp_town(m)
  return m
end

-- ---------------------------------------------------------------- RLE
-- 행 우선으로 훑어 같은 값을 묶는다. 런 하나는 최대 255칸.
function M.save_rle(m)
  local runs = {}
  local cells = m.cells
  local n = #cells
  local i = 0                                     -- 0-기반 커서
  while i < n do
    local v = cells[i + 1]
    local j = i
    while j < n and cells[j + 1] == v and j - i < 255 do j = j + 1 end
    runs[#runs + 1] = string.format('%d:%d', j - i, v)
    i = j
  end
  local lines = {string.format('ISORPG-MAP 1 %d %d', m.w, m.h)}
  local k = 0
  while k < #runs do
    local part = {}
    for t = k + 1, math.min(k + 16, #runs) do part[#part + 1] = runs[t] end
    lines[#lines + 1] = table.concat(part, ' ')
    k = k + 16
  end
  return table.concat(lines, '\n') .. '\n'
end

function M.load_rle(text)
  local lines = {}
  for line in (text:gsub('^%s+', ''):gsub('%s+$', '') .. '\n'):gmatch('([^\n]*)\n') do
    lines[#lines + 1] = line
  end
  local head = {}
  for tok in lines[1]:gmatch('%S+') do head[#head + 1] = tok end
  if head[1] ~= 'ISORPG-MAP' then
    error('맵 매직이 다르다: ' .. tostring(head[1]))
  end
  local w, h = tonumber(head[3]), tonumber(head[4])
  local cells = {}
  for li = 2, #lines do
    for run in lines[li]:gmatch('%S+') do
      local c, v = run:match('^(%-?%d+):(%-?%d+)$')
      c, v = tonumber(c), tonumber(v)
      for _ = 1, c do cells[#cells + 1] = v end
    end
  end
  if #cells ~= w * h then
    error(string.format('칸 수가 %d 여야 하는데 %d', w * h, #cells))
  end
  return M.new_map(w, h, cells)
end

return M
