-- 래스터 — 클리핑, 광원표, 더티 렉트, PPM.

local H = require("tests.harness")
local R = require("isorpg.raster")

H.title('raster')

local pal = R.load_palette()
H.check('팔레트 256색', #pal, 256)
local seen = {}
local nuniq = 0
for i = 1, #pal do
  local k = pal[i][1] .. ',' .. pal[i][2] .. ',' .. pal[i][3]
  if not seen[k] then seen[k] = true; nuniq = nuniq + 1 end
end
H.check('중복된 색이 없다 (명암표 항등을 깨뜨린다)', nuniq, 256)
local dac_ok = true
for i = 1, #pal do
  for c = 1, 3 do
    if not (pal[i][c] >= 0 and pal[i][c] <= 63) then dac_ok = false end
  end
end
H.check_true('DAC 는 6비트', dac_ok)
H.check('0번은 검정', pal[1], {0, 0, 0})

local light = R.build_light(pal)
H.check('광원표 크기', #light, 16 * 256)
local ident = true
for c = 0, 255 do
  if light[15 * 256 + c + 1] ~= c then ident = false end
end
H.check_true('15단계는 항등', ident)
local zero = {}
local nz = 0
for c = 0, 255 do
  local v = light[0 * 256 + c + 1]
  if not zero[v] then zero[v] = true; nz = nz + 1 end
end
H.check_true('0단계는 전부 검정에 가장 가까운 색', nz <= 4)
local function level_sum(l)
  local s = 0
  for c = 0, 255 do
    local p = pal[light[l * 256 + c + 1] + 1]
    s = s + p[1] + p[2] + p[3]
  end
  return s
end
local mono = true
for l = 0, 14 do
  if not (level_sum(l) <= level_sum(l + 1)) then mono = false end
end
H.check_true('단계가 낮을수록 밝기 합이 줄어든다', mono)

local spr = R.load_sprites()
H.check('스프라이트 48개', #spr, 48)
H.check('0번은 tile_0', {spr[1].name, spr[1].w, spr[1].h, spr[1].ox, spr[1].oy},
        {'tile_0', 32, 16, 16, 0})
local runs_ok = true
for i = 1, #spr do
  local s = spr[i]
  for r = 1, s.h do
    local t = 0
    local row = s.rows[r]
    for k = 1, #row, 2 do t = t + row[k] end
    if t ~= s.w then runs_ok = false end
  end
end
H.check_true('모든 런의 합이 폭과 같다', runs_ok)
local dia = 0
for r = 1, spr[1].h do
  local row = spr[1].rows[r]
  for k = 1, #row, 2 do
    if row[k + 1] ~= 0 then dia = dia + row[k] end
  end
end
H.check('마름모 픽셀 수 256', dia, 256)

-- ---- 클리핑: 화면 밖, 걸침, 완전히 안
local function fb_sum(f)
  local s = 0
  for i = 1, #f.fb do s = s + f.fb[i] end
  return s
end
local function fb_count(f)
  local n = 0
  for i = 1, #f.fb do if f.fb[i] ~= 0 then n = n + 1 end end
  return n
end

local f = R.new_frame()
f:clear(0)
f:blit_rle(spr[1], -1000, -1000, 15)
H.check('완전히 밖 (왼위)', fb_sum(f), 0)
f:blit_rle(spr[1], 1000, 1000, 15)
H.check('완전히 밖 (오른아래)', fb_sum(f), 0)
f:blit_rle(spr[1], 16, 0, 15)
H.check('안쪽 블릿 픽셀 수', fb_count(f), 256)
f:clear(0)
f:blit_rle(spr[1], 0, 0, 15)
H.check_true('왼쪽으로 걸치면 잘린다', fb_count(f) > 0 and fb_count(f) < 256)
f:clear(0)
f:blit_rle(spr[1], 16, R.SCR_H - 4, 15)
H.check_true('아래로 걸치면 잘린다', fb_count(f) > 0 and fb_count(f) < 256)
local bad = 0
local x = -40
while x < R.SCR_W + 40 do
  local y = -20
  while y < R.SCR_H + 20 do
    f:clear(0)
    f:blit_rle(spr[1], x, y, 15)
    if #f.fb ~= R.SCR_W * R.SCR_H then bad = bad + 1 end
    y = y + 5
  end
  x = x + 7
end
H.check('클리핑 중 버퍼 크기 불변', bad, 0)

-- ---- 색 0 은 투명
f:clear(7)
f:blit_rle(spr[1], 16, 0, 15)
H.check_true('투명 픽셀은 배경이 남는다', f:px(0, 0) == 7)

-- ---- 명암: 인덱스 합이 아니라 실제 밝기(팔레트 값)로 재야 한다
local function screen_brightness(frame)
  local s = 0
  for i = 1, #frame.fb do
    local p = pal[frame.fb[i] + 1]
    s = s + p[1] + p[2] + p[3]
  end
  return s
end
f:clear(0)
f:blit_rle(spr[4], 16, 0, 15)
local bright = screen_brightness(f)
f:clear(0)
f:blit_rle(spr[4], 16, 0, 8)
local mid = screen_brightness(f)
f:clear(0)
f:blit_rle(spr[4], 16, 0, 2)
local dark = screen_brightness(f)
H.note('같은 타일 밝기 합 — 15단계 %d, 8단계 %d, 2단계 %d', bright, mid, dark)
H.check_true('단계가 낮을수록 어둡다', dark < mid and mid < bright)

-- ---- 더티 렉트
local d = R.new_dirty()
d:add(10, 10, 20, 20)
d:add(15, 15, 20, 20)
d:merge()
H.check('겹치는 둘은 하나로', #d.rects, 1)
d = R.new_dirty()
d:add(0, 0, 10, 10)
d:add(300, 190, 40, 40)
d:merge()
H.check('먼 둘은 그대로', #d.rects, 2)
H.check('화면 밖은 잘린다', d.rects[2], {300, 190, 20, 10})
d = R.new_dirty()
d:add(-50, -50, 10, 10)
d:merge()
H.check('완전히 밖이면 버린다', #d.rects, 0)

-- ---- 팔레트 사이클링
local p2 = R.cycle_palette(pal, 1)
H.check('물 구간이 한 칸 돈다', p2[R.WATER_LO + 1], pal[R.WATER_LO + 2])
H.check('물 구간 끝이 앞으로', p2[R.WATER_HI + 1], pal[R.WATER_LO + 1])
local a1, a2 = {}, {}
for i = 1, R.WATER_LO do a1[i] = p2[i]; a2[i] = pal[i] end
H.check('물 밖은 그대로', a1, a2)
H.check('한 바퀴 돌면 원래대로', R.cycle_palette(pal, 16), pal)

-- ---- PPM
f:clear(15)
local ppm = R.to_ppm(f.fb, pal)
H.check('PPM 크기', #ppm, 192015)
H.check('PPM 머리말', ppm:sub(1, 15), 'P6\n320 200\n255\n')
H.check('흰색은 255,255,255', ppm:sub(16, 18), string.char(255, 255, 255))
f:clear(0)
H.check('검정은 0,0,0', R.to_ppm(f.fb, pal):sub(16, 18), string.char(0, 0, 0))

H.done()
