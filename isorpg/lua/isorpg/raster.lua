-- 래스터 — SPEC §7. 320x200 8비트 인덱스 프레임버퍼.
--
--   모드 13h 를 그대로 흉내 낸다. 파이썬의 bytearray, 타입스크립트의 Uint8Array
--   자리에 루아는 그냥 숫자 테이블을 쓴다. 값 검사는 하지 않는다 —
--   0..255 를 넘기지 않는 것은 호출자 책임이고, 넘기면 PPM 에서 바로 드러난다.
--
-- 배열 규약: fb, light, 팔레트, 스프라이트 행 모두 1-기반이다.
--   화면 좌표 (x, y) 와 오프셋 y*320+x 는 파이썬과 똑같이 0-기반으로 계산하고,
--   테이블을 짚는 순간에만 +1 한다. 팔레트 색 인덱스 c(0..255) 도 pal[c+1] 이다.

local floor = math.floor

local M = {}

M.SCR_W = 320
M.SCR_H = 200
M.PAL_SIZE = 256
M.LIGHT_LEVELS = 16
M.DAC_MAX = 63

M.WATER_LO = 16
M.WATER_HI = 31

local SCR_W, SCR_H, PAL_SIZE = 320, 200, 256

-- 골든 디렉터리 찾기.
--   파이썬은 __file__ 로 저장소 뿌리를 잡지만 루아 5.1 에는 그런 것이 없다.
--   LÖVE 는 작업 디렉터리가 또 달라서 상대 경로 하나로는 부족하다.
--   그래서 ISORPG_ROOT 환경변수를 먼저 보고, 없으면 후보를 훑어
--   palette.txt 가 실제로 열리는 곳을 고른다.
local _golden = nil
function M.golden_dir()
  if _golden then return _golden end
  local root = os.getenv('ISORPG_ROOT')
  if root and root ~= '' then
    if root:sub(-1) ~= '/' then root = root .. '/' end
    _golden = root .. 'golden/'
    return _golden
  end
  local cands = {'../golden/', 'golden/', '../../golden/', '../../../golden/'}
  for i = 1, #cands do
    local f = io.open(cands[i] .. 'palette.txt', 'r')
    if f then
      f:close()
      _golden = cands[i]
      return _golden
    end
  end
  _golden = '../golden/'
  return _golden
end

function M.read_text(path)
  local f = io.open(path, 'r')
  if not f then error('파일을 열 수 없다: ' .. path) end
  local s = f:read('*a')
  f:close()
  return s
end

-- 줄 단위로 자른다. 마지막 빈 줄은 버린다 (파이썬의 rstrip('\n').split('\n') 과 같다).
local function split_lines(text)
  local out = {}
  for line in (text .. '\n'):gmatch('([^\n]*)\n') do out[#out + 1] = line end
  while #out > 0 and out[#out] == '' do out[#out] = nil end
  return out
end
M.split_lines = split_lines

local function split_ws(line)
  local out = {}
  for tok in line:gmatch('%S+') do out[#out + 1] = tok end
  return out
end
M.split_ws = split_ws

-- golden/palette.txt -> {{r,g,b}} 256개. 값은 6비트 DAC (0..63). pal[c+1] 이 색 c 다.
function M.load_palette(path)
  local lines = split_lines(M.read_text(path or (M.golden_dir() .. 'palette.txt')))
  local head = split_ws(lines[1])
  if head[1] ~= 'ISORPG-PAL' then
    error('팔레트 매직이 다르다: ' .. tostring(head[1]))
  end
  local pal = {}
  for i = 2, #lines do
    local p = split_ws(lines[i])
    pal[#pal + 1] = {tonumber(p[2]), tonumber(p[3]), tonumber(p[4])}
  end
  if #pal ~= PAL_SIZE then
    error(string.format('팔레트가 %d색', #pal))
  end
  return pal
end

-- 명암표 16 x 256. LIGHT[l*256 + c + 1] = 색 c 를 l/15 로 어둡게 한 것에 가장 가까운 색.
-- 16 * 256 * 256 = 1,048,576 번의 거리 계산 — 시작할 때 한 번뿐이다.
-- 동점은 인덱스가 작은 쪽으로 간다(부등호가 < 라서). 이 규칙이 곧 명세다.
function M.build_light(pal)
  local tbl = {}
  local pr, pg, pb = {}, {}, {}
  for k = 1, PAL_SIZE do
    pr[k] = pal[k][1]
    pg[k] = pal[k][2]
    pb[k] = pal[k][3]
  end
  for l = 0, 15 do
    for c = 0, PAL_SIZE - 1 do
      local tr = floor(pr[c + 1] * l / 15)
      local tg = floor(pg[c + 1] * l / 15)
      local tb = floor(pb[c + 1] * l / 15)
      local best, bd = 0, 1073741824
      for k = 1, PAL_SIZE do
        local dr = pr[k] - tr
        local dg = pg[k] - tg
        local db = pb[k] - tb
        local d = dr * dr + dg * dg + db * db
        if d < bd then
          bd = d
          best = k - 1
          if d == 0 then break end
        end
      end
      tbl[l * PAL_SIZE + c + 1] = best
    end
  end
  return tbl
end

-- ---------------------------------------------------------------- 스프라이트
local Sprite = {}
Sprite.__index = Sprite
M.Sprite = Sprite

-- golden/tiles.rle 을 읽는다. 색 0 은 투명.
-- rows[r+1] 은 {개수1, 색1, 개수2, 색2, ...} 로 평평하게 편 배열이다 —
-- 런마다 표를 만들면 블릿 안쪽 루프에서 테이블 참조가 두 번씩 더 든다.
function M.load_sprites(path)
  local lines = split_lines(M.read_text(path or (M.golden_dir() .. 'tiles.rle')))
  local head = split_ws(lines[1])
  if head[1] ~= 'ISORPG-TILES' then
    error('스프라이트 매직이 다르다: ' .. tostring(head[1]))
  end
  local out = {}
  local i = 2
  while i <= #lines do
    local p = split_ws(lines[i])
    local name = p[3]
    local w, h = tonumber(p[4]), tonumber(p[5])
    local ox, oy = tonumber(p[6]), tonumber(p[7])
    i = i + 1
    local rows = {}
    for k = 0, h - 1 do
      local runs = {}
      local total = 0
      for tok in lines[i + k]:gmatch('%S+') do
        local a, b = tok:match('^(%d+):(%d+)$')
        a, b = tonumber(a), tonumber(b)
        runs[#runs + 1] = a
        runs[#runs + 1] = b
        total = total + a
      end
      if total ~= w then
        error(string.format('%s 의 %d행 런 합이 %d (폭 %d)', name, k, total, w))
      end
      rows[k + 1] = runs
    end
    i = i + h
    out[#out + 1] = setmetatable(
      {name = name, w = w, h = h, ox = ox, oy = oy, rows = rows}, Sprite)
  end
  if #out ~= tonumber(head[3]) then
    error(string.format('스프라이트 개수가 %d 여야 하는데 %d', tonumber(head[3]), #out))
  end
  return out
end

local _light_cache = nil

-- 기본 명암표. 만드는 데 시간이 걸리므로 한 번만 만들어 둔다.
function M.get_light()
  if _light_cache == nil then
    _light_cache = M.build_light(M.load_palette())
  end
  return _light_cache
end

-- ---------------------------------------------------------------- 프레임
local Frame = {}
Frame.__index = Frame
M.Frame = Frame

function M.new_frame(light)
  local fb = {}
  for i = 1, SCR_W * SCR_H do fb[i] = 0 end
  return setmetatable({fb = fb, light = light or M.get_light()}, Frame)
end

function Frame:clear(c)
  c = c or 0
  local fb = self.fb
  for i = 1, SCR_W * SCR_H do fb[i] = c end
end

function Frame:px(x, y)
  return self.fb[y * SCR_W + x + 1]
end

-- 런 단위로 자르며 그린다. 픽셀마다 조건을 걸지 않는 것이 도스식이다.
-- 세로는 행 통째로 건너뛰고, 가로는 런 하나를 [a,b) 로 잘라 채운다.
function Frame:blit_rle(spr, x, y, level)
  if level == nil then level = 15 end
  local light = self.light
  local fb = self.fb
  local top = y - spr.oy
  local left = x - spr.ox
  local rows = spr.rows
  local lbase = level * PAL_SIZE
  for r = 0, spr.h - 1 do
    local py = top + r
    if py >= 0 and py < SCR_H then
      local base = py * SCR_W
      local px = left
      local runs = rows[r + 1]
      for t = 1, #runs, 2 do
        local count = runs[t]
        local color = runs[t + 1]
        if color ~= 0 then
          local a = px > 0 and px or 0
          local b = px + count
          if b > SCR_W then b = SCR_W end
          if a < b then
            local v = light and light[lbase + color + 1] or color
            for i = base + a + 1, base + b do fb[i] = v end
          end
        end
        px = px + count
        if px >= SCR_W then break end
      end
    end
  end
end

-- ---------------------------------------------------------------- 더티 렉트
local Dirty = {}
Dirty.__index = Dirty
M.Dirty = Dirty

function M.new_dirty()
  return setmetatable({rects = {}}, Dirty)
end

function Dirty:add(x, y, w, h)
  if x < 0 then w = w + x; x = 0 end
  if y < 0 then h = h + y; y = 0 end
  if x + w > SCR_W then w = SCR_W - x end
  if y + h > SCR_H then h = SCR_H - y end
  if w > 0 and h > 0 then
    self.rects[#self.rects + 1] = {x, y, w, h}
  end
end

-- 겹치거나 맞닿은 사각형을 합친다. 낭비가 1.5배를 넘으면 그냥 둔다.
--
--   마지막 정렬에 주의. 파이썬의 sorted 는 안정 정렬이지만 루아의 table.sort 는
--   아니다. 그래서 원래 자리를 마지막 열쇠로 붙여 넣어 전순서를 만든다 —
--   그러지 않으면 같은 (y, x) 가 둘 나왔을 때 언어마다 순서가 갈린다.
function Dirty:merge()
  local changed = true
  while changed do
    changed = false
    local out = {}
    local used = {}
    local n = #self.rects
    for i = 1, n do used[i] = false end
    for i = 1, n do
      if not used[i] then
        local r = self.rects[i]
        local x, y, w, h = r[1], r[2], r[3], r[4]
        for j = i + 1, n do
          if not used[j] then
            local s = self.rects[j]
            local x2, y2, w2, h2 = s[1], s[2], s[3], s[4]
            if not (x + w < x2 or x2 + w2 < x or y + h < y2 or y2 + h2 < y) then
              local nx = x < x2 and x or x2
              local ny = y < y2 and y or y2
              local nr = (x + w > x2 + w2) and (x + w) or (x2 + w2)
              local nb = (y + h > y2 + h2) and (y + h) or (y2 + h2)
              if (nr - nx) * (nb - ny) * 2 <= (w * h + w2 * h2) * 3 then
                x, y, w, h = nx, ny, nr - nx, nb - ny
                used[j] = true
                changed = true
              end
            end
          end
        end
        used[i] = true
        out[#out + 1] = {x, y, w, h}
      end
    end
    self.rects = out
  end
  local ord = {}
  for i = 1, #self.rects do ord[i] = i end
  local rects = self.rects
  table.sort(ord, function(p, q)
    local a, b = rects[p], rects[q]
    if a[2] ~= b[2] then return a[2] < b[2] end
    if a[1] ~= b[1] then return a[1] < b[1] end
    return p < q                                   -- 안정 정렬 흉내
  end)
  local sorted = {}
  for i = 1, #ord do sorted[i] = rects[ord[i]] end
  self.rects = sorted
  return self.rects
end

-- 물 램프 구간만 왼쪽으로 n 칸 돌린다. 프레임버퍼는 건드리지 않는다.
function M.cycle_palette(pal, n)
  local span = M.WATER_HI - M.WATER_LO + 1
  local k = n - span * floor(n / span)
  local out = {}
  for i = 1, #pal do out[i] = pal[i] end
  for i = 0, span - 1 do
    local j = i + k
    out[M.WATER_LO + i + 1] = pal[M.WATER_LO + (j - span * floor(j / span)) + 1]
  end
  return out
end

-- 6비트 DAC -> 8비트. v*4 + v/16 이라 0 -> 0, 63 -> 255 가 정확히 맞는다.
function M.expand6(v)
  return v * 4 + floor(v / 16)
end

-- P6 PPM. 머리말 15바이트 + 192,000바이트 = 192,015바이트.
-- 색마다 3바이트 문자열을 미리 만들어 두고 table.concat 로 한 번에 잇는다 —
-- 루아에서 문자열을 .. 로 19만 번 이으면 O(n^2) 가 되어 못 쓴다.
function M.to_ppm(fb, pal)
  local lut = {}
  for i = 0, PAL_SIZE - 1 do
    local c = pal[i + 1]
    lut[i + 1] = string.char(M.expand6(c[1]), M.expand6(c[2]), M.expand6(c[3]))
  end
  local body = {}
  local n = SCR_W * SCR_H
  for i = 1, n do
    body[i] = lut[fb[i] + 1]
  end
  return 'P6\n320 200\n255\n' .. table.concat(body)
end

return M
