-- 투영과 역투영 — 마스크 방식과 대수적 역이 화면 전체에서 같은가.

local H = require("tests.harness")
local P = require("isorpg.proj")

H.title('proj')

-- ---- 기저와 행렬식
H.check('e_x', {P.tile_to_screen(1, 0, 0)}, {16, 8})
H.check('e_y', {P.tile_to_screen(0, 1, 0)}, {-16, 8})
H.check('det', 16 * 8 - (-16) * 8, 256)
H.check('높이 1단계', {P.tile_to_screen(5, 3, 1)}, {32, 56})

-- ---- 타일 -> 화면 -> 타일 왕복 (중심 픽셀)
local bad = 0
for tx = -8, 55 do
  for ty = -8, 55 do
    local sx, sy = P.tile_to_screen(tx, ty, 0)
    local ax, ay = P.screen_to_tile(sx, sy + 8)
    if ax ~= tx or ay ~= ty then bad = bad + 1 end
  end
end
H.check('타일 중심 왕복 64x64', bad, 0)

-- ---- 마름모 정의로 직접 찾은 것과 같은가
bad = 0
for px = -64, 64 do
  for py = -40, 40 do
    local ax, ay = P.screen_to_tile(px, py)
    local bx, by = P.screen_to_tile_slow(px, py)
    if ax ~= bx or ay ~= by then bad = bad + 1 end
  end
end
H.check('대수적 역 == 마름모 전수 탐색 (129x81)', bad, 0)

-- ---- 마스크가 골든과 같은가
local want = H.lines(H.golden('pick_mask.txt'))
local got = {}
for oy = 0, 15 do
  local row = {}
  for ox = 0, 31 do row[ox + 1] = string.format('%d', P.PICK_MASK[oy * 32 + ox + 1]) end
  got[oy + 1] = table.concat(row)
end
H.check('pick_mask.txt', got, want)
local seen = {}
for i = 1, 512 do seen[P.PICK_MASK[i]] = true end
local uniq = {}
for v = 0, 9 do if seen[v] then uniq[#uniq + 1] = v end end
H.check('마스크 값은 0..3 뿐', uniq, {0, 1, 2, 3})

-- ---- 전수 확인: 화면 64,000픽셀 x 카메라 5개
local CAMS = {{0, 0}, {137, 91}, {-137, -91}, {768, 640}, {-768, -120}}
bad = 0
for i = 1, #CAMS do
  local cx, cy = CAMS[i][1], CAMS[i][2]
  for py = 0, P.SCR_H - 1 do
    local base = py + cy
    for px = 0, P.SCR_W - 1 do
      local ax, ay = P.pick_mask(px + cx, base)
      local bx, by = P.screen_to_tile(px + cx, base)
      if ax ~= bx or ay ~= by then bad = bad + 1 end
    end
  end
end
H.check(string.format('마스크 == 대수적 역 (카메라 %d개 x 64,000픽셀)', #CAMS), bad, 0)

-- ---- 마름모가 평면을 빈틈없이 덮는가: 각 타일이 정확히 256픽셀
--   파이썬은 Counter 를 쓰지만 루아에는 없다. 타일 좌표를 문자열 열쇠로 접어 센다.
local cnt = {}
for py = 0, 159 do
  for px = -160, 159 do
    local tx, ty = P.screen_to_tile(px, py)
    local k = tx .. ',' .. ty
    cnt[k] = (cnt[k] or 0) + 1
  end
end
local inner = {}
local vals = {}
for k, v in pairs(cnt) do
  local tx, ty = k:match('^(-?%d+),(-?%d+)$')
  tx, ty = tonumber(tx), tonumber(ty)
  -- 표본 영역에 마름모가 통째로 들어오는 타일만 센다 — 가장자리는 잘려서 당연히 적다
  if -160 <= 16 * (tx - ty) - 16 and 16 * (tx - ty) + 16 < 160
     and 0 <= 8 * (tx + ty) and 8 * (tx + ty) + 16 < 160 then
    inner[#inner + 1] = v
    vals[v] = true
  end
end
H.check_true('온전히 담긴 타일이 여럿', #inner > 20)
local uv = {}
for v in pairs(vals) do uv[#uv + 1] = v end
table.sort(uv)
H.check('그 타일들은 모두 256픽셀', uv, {256})

-- ---- 가시 범위: 무식하게 센 것과 같은가
bad = 0
local VC = {{0, 0}, {100, 50}, {-200, 300}, {-700, 100}}
for i = 1, #VC do
  local cx, cy = VC[i][1], VC[i][2]
  local tx0, ty0, tx1, ty1 = P.visible_range(cx, cy, cx + P.SCR_W, cy + P.SCR_H)
  local seen2 = {}
  for py = cy, cy + P.SCR_H - 1 do
    for px = cx, cx + P.SCR_W - 1 do
      local tx, ty = P.screen_to_tile(px, py)
      seen2[tx .. ',' .. ty] = true
    end
  end
  for k in pairs(seen2) do
    local tx, ty = k:match('^(-?%d+),(-?%d+)$')
    tx, ty = tonumber(tx), tonumber(ty)
    if tx >= 0 and tx < 48 and ty >= 0 and ty < 48 then
      if not (tx0 <= tx and tx <= tx1 and ty0 <= ty and ty <= ty1) then
        bad = bad + 1
      end
    end
  end
end
H.check('가시 범위가 화면에 나오는 타일을 모두 담는가', bad, 0)

H.done()
