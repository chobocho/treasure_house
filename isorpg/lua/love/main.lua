-- LÖVE 11.5 프런트엔드 — SPEC §13 의 `play` 자리(루아 쪽).
--
--   엔진은 320x200 짜리 8비트 인덱스 버퍼를 내놓는다. 여기서 하는 일은 넷뿐이다.
--   팔레트 씌우기, 텍스처로 올리기, 정수배 확대, 입력 읽기. 엔진 상태는
--   읽기만 하고 쓰지 않는다 — 프런트엔드가 규칙을 조금이라도 건드리면
--   파이썬/루아/타입스크립트 트레이스가 갈라진다.
--
--   ★ 이 파일은 OpenGL 이 있는 기계에서 도는 코드다. 이 저장소를 만든 기계에는
--     GPU 가 없어 love.graphics 자체가 뜨지 않는다. 그래서 실행으로는 확인하지
--     못했고, 대신 tools/gfx_recorder.lua 스텁에 걸어 tests/test_love_draw.lua 가
--     "어떤 그리기 호출을 어떤 인자로 내는가"와 "무슨 픽셀을 올리는가"를 검사한다.
--     증명하지 못하는 것은 GPU 가 그 픽셀을 실제로 화면에 뿌리는 부분뿐이다.
--
--   루아 5.1 문법만 쓴다 — //, 비트연산자, goto, table.unpack 금지.

-- ---------------------------------------------------------------- 부트스트랩
--
--   LÖVE 는 작업 디렉터리를 바꾸지 않지만, 어디서 실행됐는지도 보장하지 않는다.
--   love.filesystem.getSourceBaseDirectory() 는 게임 폴더의 부모, 즉 이 저장소의
--   lua/ 를 준다. 그것으로 package.path 와 골든 경로를 스스로 잡는다.
--   못 잡으면 손대지 않는다 — luajit 으로 lua/ 에서 돌릴 때의 기존 상대경로
--   폴백(raster.golden_dir)이 이미 듣기 때문이다. 스텁 아래서 도는 테스트도 이 길로 온다.
local BASE = nil
do
  if love and love.filesystem and love.filesystem.getSourceBaseDirectory then
    local b = love.filesystem.getSourceBaseDirectory()
    if type(b) == 'string' and b ~= '' then
      local probe = io.open(b .. '/../golden/palette.txt', 'r')
      if probe then
        probe:close()
        BASE = b
        package.path = b .. '/?.lua;' .. package.path
      end
    end
  end
end

local G = require('isorpg.game')
local P = require('isorpg.path')
local RA = require('isorpg.raster')
local SV = require('isorpg.save')

-- 골든 파일 위치를 실제 소스 위치에서 못 박는다. 모듈 테이블의 필드를 갈아 끼우면
-- 안쪽 호출(M.golden_dir())도 같이 따라온다 — 호출 시점에 테이블을 짚기 때문이다.
if BASE then
  local GOLDEN = BASE .. '/../golden/'
  RA.golden_dir = function() return GOLDEN end
end

local floor = math.floor

local FE = {}

FE.SCR_W = 320
FE.SCR_H = 200

-- SPEC §0. PIT 기본 분주(18.2065 Hz) 한 번. 다른 수를 쓰면 안 된다.
FE.TICK_US = 54925

-- 한 프레임에 몰아서 돌릴 틱의 상한. 창을 끌거나 잠들었다 깨면 실시간이 몇 초씩
-- 밀리는데, 그걸 전부 따라잡으려 들면 프레임이 더 길어지고 다음 프레임은 더 많이
-- 밀리는 악순환에 빠진다. 그냥 버린다.
FE.MAX_CATCHUP_TICKS = 8

-- 'bytes' 는 rgba8 바이트열을 한 번에 넘기는 빠른 길, 'setpixel' 은 픽셀마다
-- ImageData:setPixel 을 부르는 느린 길. 아래 upload 주석 참조.
FE.upload_mode = 'bytes'
FE.hud = true

-- 화면 기준 여덟 방향 -> 월드 방향 인덱스(P.DIR_NAME 의 0-기반 값).
--
--   기저가 e_x = (16, 8), e_y = (-16, 8) 이라 월드 축과 화면 축이 45도 어긋난다.
--   그래서 월드 E 는 화면에서 '오른쪽아래'로 간다. ↑ 를 월드 N 에 그대로 이으면
--   캐릭터가 비스듬히 올라가 조작이 어긋나 보인다. 도스 쿼터뷰 게임들이 그랬듯
--   **화면에서 보이는 방향**에 맞춘다. pygame 프런트엔드의 SCREEN_DIR 과 같은 표다.
--     ↑ = NW  ↓ = SE  ← = SW  → = NE
local SCREEN_DIR = {
  ['0,-1'] = 5,   -- NW  화면 위
  ['1,-1'] = 6,   -- N   화면 오른쪽위
  ['1,0'] = 7,    -- NE  화면 오른쪽
  ['1,1'] = 0,    -- E   화면 오른쪽아래
  ['0,1'] = 1,    -- SE  화면 아래
  ['-1,1'] = 2,   -- S   화면 왼쪽아래
  ['-1,0'] = 3,   -- SW  화면 왼쪽
  ['-1,-1'] = 4,  -- W   화면 왼쪽위
}
FE.SCREEN_DIR = SCREEN_DIR

-- {키, 화면 dx, 화면 dy}. 화살표와 숫자패드를 한 표에 넣어 두 키를 같이 눌러도
-- 벡터가 그냥 더해지게 한다 — ↑ 와 → 를 같이 누르면 (1,-1) 이 되어 N 이다.
local DIR_KEYS = {
  {'up', 0, -1}, {'down', 0, 1}, {'left', -1, 0}, {'right', 1, 0},
  {'kp8', 0, -1}, {'kp2', 0, 1}, {'kp4', -1, 0}, {'kp6', 1, 0},
  {'kp7', -1, -1}, {'kp9', 1, -1}, {'kp1', -1, 1}, {'kp3', 1, 1},
}
FE.DIR_KEYS = DIR_KEYS

-- HUD 색. 팔레트 앞 16색은 EGA 계열 고정색이라 물 사이클링(16..31)에 휩쓸리지 않는다.
FE.HUD_RECT = {x = 4, y = 4, w = 64, h = 6}
local HUD_FRAME, HUD_BACK, HUD_HP_HI, HUD_HP_LO = 15, 8, 10, 12

FE.SAVE_NAME = 'quick.sav'

-- ---------------------------------------------------------------- 팔레트
--
--   물 램프 위상(pal_phase)은 4틱에 한 번만 바뀐다. 그래서 위상이 그대로면
--   팔레트도 LUT 도 다시 만들지 않는다. 프레임마다 256색을 다시 펴는 것은
--   그 자체로는 싸지만, 아래 make_pixels 가 이 LUT 를 64,000번 짚으므로
--   같은 테이블을 계속 쓰는 편이 캐시에도 낫다.
local function build_lut(pal)
  local lut = {}
  for i = 1, RA.PAL_SIZE do
    local c = pal[i]
    -- expand6 은 PPM 출력과 같은 함수다. 같은 함수를 타야 창에 뜬 그림과
    -- out/frame_*.ppm 이 픽셀 단위로 같아진다.
    lut[i] = string.char(RA.expand6(c[1]), RA.expand6(c[2]), RA.expand6(c[3]), 255)
  end
  return lut
end

function FE.palette(phase)
  if FE._phase ~= phase then
    FE._phase = phase
    FE._pal = RA.cycle_palette(FE._base_pal, phase)
    FE._lut = build_lut(FE._pal)
  end
  return FE._pal, FE._lut
end

-- ---------------------------------------------------------------- 올리기
--
--   빠른 길: 인덱스마다 4바이트 문자열을 표에서 꺼내 table.concat 로 한 번에 잇고,
--   love.image.newImageData(w, h, 'rgba8', data) 로 통째로 넘긴다.
--   루아에서 문자열을 .. 로 64,000번 이으면 O(n^2) 이 되어 못 쓴다 —
--   raster.to_ppm 이 쓰는 것과 같은 요령이다.
--
--   느린 길(setpixel)은 픽셀마다 ImageData:setPixel 을 부른다. 프레임당 64,000번의
--   C 호출이라 18.2 Hz 를 지키기 버겁지만, 오래된 LÖVE 나 rgba8 생성자를 못 쓰는
--   환경에서도 도는 폴백으로 남겨 둔다. 두 길이 같은 픽셀을 낸다는 것은
--   tests/test_love_draw.lua 가 검사한다.
function FE.make_pixels(fb, lut)
  local parts = FE._parts
  if parts == nil then
    parts = {}
    FE._parts = parts
  end
  local n = FE.SCR_W * FE.SCR_H
  for i = 1, n do
    parts[i] = lut[fb[i] + 1]
  end
  return table.concat(parts, '', 1, n)
end

function FE.fill_imagedata(imgdata, fb, pal)
  local w, h = FE.SCR_W, FE.SCR_H
  local k = 0
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      k = k + 1
      local c = pal[fb[k] + 1]
      -- LÖVE 11 의 setPixel 은 0..1 실수를 받는다. 0..255 를 그대로 넣으면
      -- 전부 흰색으로 잘린다 — 10.x 에서 11.x 로 넘어올 때 가장 흔한 함정이다.
      imgdata:setPixel(x, y, RA.expand6(c[1]) / 255, RA.expand6(c[2]) / 255,
                       RA.expand6(c[3]) / 255, 1)
    end
  end
end

-- ---------------------------------------------------------------- HUD
--
--   love.graphics.print 로 글자를 얹으면 그 픽셀은 8비트 세계 바깥에 있게 되어
--   '모드 13h 를 흉내 낸다'는 전제가 깨진다. 그래서 채우기만으로 막대 하나를
--   인덱스 버퍼에 직접 그린다. render() 가 매 프레임 clear(0) 로 시작하므로
--   여기서 덧칠해도 다음 프레임에 남지 않고, 엔진 상태도 건드리지 않는다.
function FE.draw_hp_bar(fb, cur, mx)
  local r = FE.HUD_RECT
  local W = FE.SCR_W
  for y = r.y - 1, r.y + r.h do
    local base = y * W
    for x = r.x - 1, r.x + r.w do
      fb[base + x + 1] = HUD_FRAME
    end
  end
  local fill = 0
  if mx > 0 then fill = floor(cur * r.w / mx) end
  if fill < 0 then fill = 0 elseif fill > r.w then fill = r.w end
  -- 3분의 1 아래면 빨강. 도스 게임의 관례이고, 색 두 개면 충분히 읽힌다.
  local color = HUD_HP_HI
  if mx > 0 and cur * 3 <= mx then color = HUD_HP_LO end
  for y = r.y, r.y + r.h - 1 do
    local base = y * W
    for x = r.x, r.x + r.w - 1 do
      if x - r.x < fill then
        fb[base + x + 1] = color
      else
        fb[base + x + 1] = HUD_BACK
      end
    end
  end
end

-- ---------------------------------------------------------------- 저장
--
--   엔진의 pack_state 는 바이트 '테이블'을 준다(루아에는 bytes 형이 없다).
--   love.filesystem 은 문자열을 받으므로 옮겨 담는다. string.char 를 바이트마다
--   부르지 않고 4096개씩 묶는 이유는 인자 개수 한계와 호출 비용 둘 다다.
local function bytes_to_string(t)
  local chunks = {}
  local i = 1
  local n = #t
  while i <= n do
    local j = i + 4095
    if j > n then j = n end
    local piece = {}
    for k = i, j do piece[k - i + 1] = string.char(t[k]) end
    chunks[#chunks + 1] = table.concat(piece)
    i = j + 1
  end
  return table.concat(chunks)
end

local function string_to_bytes(s)
  local t = {}
  for i = 1, #s do t[i] = string.byte(s, i) end
  return t
end

function FE.quick_save()
  -- 엔진의 save 명령과 완전히 같은 바이트열이다. 프런트엔드가 형식을 따로 만들지 않는다.
  local blob = SV.pack_state(FE.game)
  FE.game.slot = blob
  if love and love.filesystem and love.filesystem.write then
    love.filesystem.write(FE.SAVE_NAME, bytes_to_string(blob))
  end
end

function FE.quick_load()
  local blob = FE.game.slot
  if blob == nil and love and love.filesystem and love.filesystem.read then
    local s = love.filesystem.read(FE.SAVE_NAME)
    if type(s) == 'string' and #s > 0 then blob = string_to_bytes(s) end
  end
  if blob ~= nil then SV.unpack_state(blob, FE.game) end
end

-- ---------------------------------------------------------------- 입력
function FE.held_dir()
  local dx, dy = 0, 0
  if love and love.keyboard and love.keyboard.isDown then
    for i = 1, #DIR_KEYS do
      local k = DIR_KEYS[i]
      if love.keyboard.isDown(k[1]) then
        dx = dx + k[2]
        dy = dy + k[3]
      end
    end
  end
  -- 부호만 남긴다. ←→ 를 같이 누르면 0 이 되어 서는데, 그게 가장 덜 놀라운 동작이다.
  if dx > 0 then dx = 1 elseif dx < 0 then dx = -1 end
  if dy > 0 then dy = 1 elseif dy < 0 then dy = -1 end
  local d = SCREEN_DIR[dx .. ',' .. dy]
  if d == nil then return -1 end
  return d
end

-- ---------------------------------------------------------------- 한 틱
function FE.step()
  local g = FE.game
  g.in_dir = FE.held_dir()
  -- act/atk 은 정확히 한 틱짜리다. 키를 누르고 있어도 매 틱 발동하면 안 된다.
  if FE.pending_act then g.in_act = 1 else g.in_act = 0 end
  if FE.pending_atk then g.in_atk = 1 else g.in_atk = 0 end
  FE.pending_act = false
  FE.pending_atk = false
  g:tick()
end

-- 창 크기에서 정수 배율과 가운데 맞춤 오프셋을 구한다.
-- 배율을 실수로 두면 픽셀이 뭉개져 모드 13h 의 계단이 사라진다 —
-- 그건 이 문서가 보이려는 것과 정반대다. 그래서 내림한 정수만 쓴다.
function FE.layout(w, h)
  local sx = floor(w / FE.SCR_W)
  local sy = floor(h / FE.SCR_H)
  local s = sx
  if sy < s then s = sy end
  if s < 1 then s = 1 end
  return s, floor((w - FE.SCR_W * s) / 2), floor((h - FE.SCR_H * s) / 2)
end

-- ---------------------------------------------------------------- LÖVE 콜백
function love.load()
  FE.game = G.new_game()
  FE._base_pal = RA.load_palette()
  FE._phase = nil
  FE.acc_us = 0
  FE.pending_act = false
  FE.pending_atk = false

  love.graphics.setDefaultFilter('nearest', 'nearest')
  -- letterbox 여백을 검게. 매 프레임 clear 를 부르지 않아도 love.run 이 이 색으로 지운다.
  love.graphics.setBackgroundColor(0, 0, 0)

  FE.imgdata = love.image.newImageData(FE.SCR_W, FE.SCR_H)
  -- 텍스처는 한 번만 만든다. 프레임마다 newImage 를 부르면 GPU 텍스처를
  -- 초당 열여덟 개씩 새로 잡았다 버리는 셈이라, 그림은 같아도 값이 너무 비싸다.
  FE.image = love.graphics.newImage(FE.imgdata)
  FE.image:setFilter('nearest', 'nearest')
end

function love.update(dt)
  -- 고정 타임스텝. '남은 시간으로 반 틱' 은 절대 하지 않는다. 반 틱을 허용하는
  -- 순간 프레임률에 따라 결과가 달라져 세 언어 트레이스 대조가 무의미해진다.
  local us = dt * 1000000
  if us < 0 then us = 0 end
  FE.acc_us = FE.acc_us + us
  local cap = FE.TICK_US * FE.MAX_CATCHUP_TICKS
  if FE.acc_us > cap then FE.acc_us = cap end
  while FE.acc_us >= FE.TICK_US do
    FE.acc_us = FE.acc_us - FE.TICK_US
    FE.step()
  end
end

function love.draw()
  local g = FE.game
  local fb = g:render()
  if FE.hud then
    local p = g.ents[1]
    FE.draw_hp_bar(fb, p.hp, p.maxhp)
  end
  local pal, lut = FE.palette(g.pal_phase)
  local w, h = love.graphics.getDimensions()
  local scale, ox, oy = FE.layout(w, h)
  if FE.upload_mode == 'bytes' then
    local id = love.image.newImageData(FE.SCR_W, FE.SCR_H, 'rgba8',
                                       FE.make_pixels(fb, lut))
    FE.image:replacePixels(id)
  else
    FE.fill_imagedata(FE.imgdata, fb, pal)
    FE.image:replacePixels(FE.imgdata)
  end
  love.graphics.draw(FE.image, ox, oy, 0, scale, scale)
end

function love.keypressed(key)
  if key == 'escape' then
    love.event.quit(0)
  elseif key == 'space' then
    FE.pending_atk = true
  elseif key == 'return' or key == 'kpenter' or key == 'e' then
    FE.pending_act = true
  elseif key == 'f5' then
    FE.quick_save()
  elseif key == 'f9' then
    FE.quick_load()
  elseif key == 'tab' then
    FE.hud = not FE.hud
  end
end

-- LÖVE 는 main.lua 의 반환값을 쓰지 않는다. 이 return 은 테스트를 위한 것이다 —
-- tests/test_love_draw.lua 가 require('love.main') 으로 내부를 들여다본다.
return FE
