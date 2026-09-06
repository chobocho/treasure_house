-- LÖVE 프런트엔드 — 그리기 호출의 순서·인자와 텍스처에 올라가는 픽셀.
--
--   이 기계에는 OpenGL 이 없어 love.graphics 가 뜨지 않는다. 그래서 LÖVE 화면을
--   찍은 스크린샷은 이 저장소에 영영 없다. 대신 tools/gfx_recorder.lua 를
--   love 전역 자리에 끼워 넣고 love/main.lua 를 평소대로 돌린 다음,
--   그 프런트엔드가 무엇을 어떤 순서로 불렀는지, 그리고 그때 올린 256,000바이트가
--   엔진이 따로 돌린 game:render() 와 같은지 검사한다.
--
--   증명하지 못하는 것은 하나뿐이다 — GPU 가 그 텍스처를 실제로 화면에 뿌리는 부분.
--   그 앞은 전부 여기서 확인된다.

local H = require("tests.harness")
local REC = require("tools.gfx_recorder")
local G = require("isorpg.game")
local RA = require("isorpg.raster")

H.title('love_draw')

local SCR_W, SCR_H = 320, 200
local WIN_W, WIN_H = 1000, 640          -- 일부러 320x200 의 정수배가 아닌 창.
                                        -- 배율 내림과 가운데 맞춤이 맞는지 보려는 것이다.
local WANT_SCALE, WANT_OX, WANT_OY = 3, 20, 20

-- love 전역을 스텁으로 갈아 끼운다. LÖVE 런타임 안에서 이 테스트가 돌 수도 있으므로
-- (tools/love_headless) 반드시 원래 것을 되돌려 놓는다.
local saved_love = _G.love
local rec = REC.new({width = WIN_W, height = WIN_H})
_G.love = rec.love

-- source_base 를 주지 않았으므로 main.lua 는 부트스트랩을 건너뛰고
-- 기존 상대경로 폴백을 그대로 쓴다 — luajit 으로 lua/ 에서 돌릴 때와 같은 길이다.
local FE = require("love.main")

-- ---------------------------------------------------------------- 기대 픽셀
--
--   프런트엔드가 만든 것과 견줄 값을 여기서 **따로** 만든다. FE.make_pixels 를
--   불러 쓰면 같은 코드를 자기 자신과 비교하는 꼴이라 아무것도 증명하지 못한다.
local base_pal = RA.load_palette()

local function expected_rgba(fb, phase)
  local pal = RA.cycle_palette(base_pal, phase)
  local lut = {}
  for i = 1, 256 do
    local c = pal[i]
    lut[i] = string.char(RA.expand6(c[1]), RA.expand6(c[2]), RA.expand6(c[3]), 255)
  end
  local parts = {}
  for i = 1, SCR_W * SCR_H do parts[i] = lut[fb[i] + 1] end
  return table.concat(parts)
end

-- 엔진만 따로 돌리는 대조군. 프런트엔드가 쥔 것과 다른 인스턴스여야 한다.
local ref = G.new_game()
local function ref_tick()
  ref.in_dir, ref.in_act, ref.in_atk = -1, 0, 0
  ref:tick()
end

-- ---------------------------------------------------------------- love.load
FE.hud = false                          -- 프레임 세 장은 엔진 출력 그대로와 견준다
rec.reset()
love.load()
H.check('load 호출 순서', rec.names(), {
  'love.graphics.setDefaultFilter',
  'love.graphics.setBackgroundColor',
  'love.image.newImageData',
  'love.graphics.newImage',
  'Image:setFilter',
})
H.check('기본 필터는 nearest', {rec.calls[1].args[1], rec.calls[1].args[2]},
        {'nearest', 'nearest'})
H.check('빈 ImageData 는 320x200', {rec.calls[3].args[1], rec.calls[3].args[2]},
        {SCR_W, SCR_H})
local the_image = FE.image
H.check_true('텍스처가 만들어졌다', the_image ~= nil and the_image == rec.calls[4].ret)

-- ---------------------------------------------------------------- 세 프레임
--
--   dt = 0.06초 = 60,000us. 한 틱이 54,925us 이므로 프레임마다 정확히 한 틱씩
--   돌고 5,075us 가 남는다. 남은 시간으로 '반 틱' 을 돌리지 않는다는 것이
--   고정 타임스텝의 전부다.
local DT = 0.06
for frame = 1, 3 do
  rec.reset()
  love.update(DT)
  ref_tick()
  H.check(string.format('%d프레임 뒤 틱 수', frame), FE.game.tick_n, frame)
  H.check(string.format('%d프레임: 엔진 틱 수도 같다', frame), ref.tick_n, frame)

  love.draw()

  H.check(string.format('%d프레임 그리기 호출 순서', frame), rec.names(), {
    'love.graphics.getDimensions',
    'love.image.newImageData',
    'Image:replacePixels',
    'love.graphics.draw',
  })

  local nid = rec.calls[2]
  H.check(string.format('%d프레임 newImageData 인자', frame),
          {nid.args[1], nid.args[2], nid.args[3], #nid.args[4]},
          {SCR_W, SCR_H, 'rgba8', SCR_W * SCR_H * 4})

  local rp = rec.calls[3]
  H.check_true(string.format('%d프레임 replacePixels 는 같은 텍스처에', frame),
               rp.args[1] == the_image)
  H.check_true(string.format('%d프레임 replacePixels 가 받은 것이 방금 만든 ImageData', frame),
               rp.args[2] == nid.ret)

  local dr = rec.calls[4]
  H.check_true(string.format('%d프레임 draw 대상이 그 텍스처', frame),
               dr.args[1] == the_image)
  H.check(string.format('%d프레임 draw 인자 (x, y, r, sx, sy)', frame),
          {dr.args[2], dr.args[3], dr.args[4], dr.args[5], dr.args[6]},
          {WANT_OX, WANT_OY, 0, WANT_SCALE, WANT_SCALE})

  -- 올린 픽셀이 엔진이 따로 낸 프레임과 같은가. 이 한 줄이 이 파일의 핵심이다.
  H.check(string.format('%d프레임 올린 픽셀 == game:render()', frame),
          nid.args[4], expected_rgba(ref:render(), ref.pal_phase))
end

-- 매 프레임 새 텍스처를 잡지 않았는지. 초당 열여덟 번씩 GPU 텍스처를 새로 만들면
-- 그림은 같아도 값이 너무 비싸다.
rec.reset()
love.draw()
love.draw()
local made = 0
for i = 1, #rec.calls do
  if rec.calls[i].name == 'love.graphics.newImage' then made = made + 1 end
end
H.check('두 프레임 더 그려도 newImage 는 다시 부르지 않는다', made, 0)
H.check_true('텍스처 객체가 그대로', FE.image == the_image)

-- ---------------------------------------------------------------- 고정 타임스텝
local before = FE.game.tick_n
love.update(0.03)                       -- 30,000us — 한 틱에 못 미친다
H.check('한 틱에 못 미치는 dt 는 틱을 돌리지 않는다', FE.game.tick_n, before)
love.update(0.03)                       -- 합 60,000us + 남은 것
H.check_true('모아 두었다가 넘으면 돈다', FE.game.tick_n > before)
before = FE.game.tick_n
FE.acc_us = 0
love.update(0.11)                       -- 110,000us = 두 틱 + 나머지
H.check('큰 dt 는 온전한 틱만큼만', FE.game.tick_n - before, 2)
H.check_true('나머지는 남겨 둔다 (반 틱 금지)',
             FE.acc_us > 0 and FE.acc_us < FE.TICK_US)
FE.acc_us = 0
love.update(100)                        -- 100초 — 창을 끌었다 놓은 상황
H.check('따라잡기 상한', FE.game.tick_n - before - 2, FE.MAX_CATCHUP_TICKS)

-- ---------------------------------------------------------------- setPixel 폴백
--
--   rgba8 생성자를 못 쓰는 환경을 위한 느린 길. 두 길이 같은 픽셀을 낸다는 것을
--   확인해 두지 않으면 폴백은 있으나 마나다.
rec.reset()
FE.upload_mode = 'setpixel'
love.draw()
H.check('setpixel 모드의 호출 순서', rec.names(), {
  'love.graphics.getDimensions',
  'Image:replacePixels',
  'love.graphics.draw',
})
local slow_id = rec.calls[2].args[2]
H.check('setPixel 은 픽셀마다 한 번씩', slow_id.set_count, SCR_W * SCR_H)
FE.upload_mode = 'bytes'
rec.reset()
love.draw()
local fast_id = rec.calls[3].args[2]
H.check('두 길이 같은 픽셀을 낸다', slow_id:rgba_bytes(), fast_id:rgba_bytes())

-- ---------------------------------------------------------------- HUD
--
--   HUD 는 8비트 인덱스 버퍼 안에서만 그린다. love.graphics.print 로 글자를 얹으면
--   그 픽셀은 모드 13h 바깥에 있게 되어 이 문서의 전제가 깨진다.
rec.reset()
FE.hud = false
love.draw()
local plain = rec.calls[2].args[4]
rec.reset()
FE.hud = true
love.draw()
local withhud = rec.calls[2].args[4]
H.check('HUD 는 그리기 호출을 늘리지 않는다', rec.names(), {
  'love.graphics.getDimensions',
  'love.image.newImageData',
  'Image:replacePixels',
  'love.graphics.draw',
})
local r = FE.HUD_RECT
local outside_diff, inside_diff = 0, 0
for y = 0, SCR_H - 1 do
  for x = 0, SCR_W - 1 do
    local o = (y * SCR_W + x) * 4
    if plain:sub(o + 1, o + 4) ~= withhud:sub(o + 1, o + 4) then
      if x >= r.x - 1 and x <= r.x + r.w and y >= r.y - 1 and y <= r.y + r.h then
        inside_diff = inside_diff + 1
      else
        outside_diff = outside_diff + 1
      end
    end
  end
end
H.check('HUD 는 막대 바깥을 한 픽셀도 건드리지 않는다', outside_diff, 0)
H.check_true('HUD 가 실제로 그려졌다', inside_diff > 0)
FE.hud = false

-- ---------------------------------------------------------------- 입력
--
--   기저가 45도 기울어 있어 화살표를 월드 방향에 그대로 이으면 조작이 어긋난다.
--   ↑ 는 화면에서 곧게 올라가는 NW 여야 한다.
local P = require("isorpg.path")
local function pressed(...)
  rec.keys = {}
  local n = select('#', ...)
  for i = 1, n do rec.keys[(select(i, ...))] = true end
  return P.DIR_NAME[FE.held_dir() + 1]
end
H.check('아무것도 안 누르면 -1', (function() rec.keys = {}; return FE.held_dir() end)(), -1)
H.check('위쪽 화살표 -> NW (화면 정위)', pressed('up'), 'NW')
H.check('아래쪽 -> SE', pressed('down'), 'SE')
H.check('왼쪽 -> SW', pressed('left'), 'SW')
H.check('오른쪽 -> NE', pressed('right'), 'NE')
H.check('위+오른쪽 -> N', pressed('up', 'right'), 'N')
H.check('아래+오른쪽 -> E', pressed('down', 'right'), 'E')
H.check('아래+왼쪽 -> S', pressed('down', 'left'), 'S')
H.check('위+왼쪽 -> W', pressed('up', 'left'), 'W')
H.check('숫자패드 8 도 NW', pressed('kp8'), 'NW')
H.check('숫자패드 3 은 E', pressed('kp3'), 'E')
H.check('좌우 동시 -> 제자리', (function() rec.keys = {left = true, right = true}
                                return FE.held_dir() end)(), -1)
-- 여덟 방향이 화면에서 실제로 그 방향으로 가는지. 기저 e_x=(16,8), e_y=(-16,8).
local screen_ok = true
for k, d in pairs(FE.SCREEN_DIR) do
  local dx, dy = k:match('^(-?%d+),(-?%d+)$')
  dx, dy = tonumber(dx), tonumber(dy)
  local sx = 16 * P.DIRX[d + 1] - 16 * P.DIRY[d + 1]
  local sy = 8 * P.DIRX[d + 1] + 8 * P.DIRY[d + 1]
  local nx = 0
  if sx > 0 then nx = 1 elseif sx < 0 then nx = -1 end
  local ny = 0
  if sy > 0 then ny = 1 elseif sy < 0 then ny = -1 end
  if nx ~= dx or ny ~= dy then screen_ok = false end
end
H.check_true('여덟 방향이 화면 방향과 일치', screen_ok)
rec.keys = {}

-- ---------------------------------------------------------------- 키 이벤트
love.keypressed('space')
H.check_true('스페이스는 다음 틱 한 번만 공격', FE.pending_atk)
love.keypressed('e')
H.check_true('E 는 상호작용', FE.pending_act)
FE.step()
H.check_true('한 틱 뒤 예약이 지워진다', not FE.pending_atk and not FE.pending_act)

-- 저장/불러오기. 엔진의 save/load 명령과 똑같은 바이트열을 쓴다.
local t0 = FE.game.tick_n
FE.quick_save()
H.check_true('세이브가 파일로도 나간다', type(rec.files[FE.SAVE_NAME]) == 'string')
H.check('세이브 매직', rec.files[FE.SAVE_NAME]:sub(1, 4), 'ISO1')
for _ = 1, 5 do FE.step() end
H.check('다섯 틱 흘렀다', FE.game.tick_n, t0 + 5)
FE.quick_load()
H.check('F9 가 시계를 되돌린다', FE.game.tick_n, t0)

rec.reset()
love.keypressed('escape')
H.check('Esc 는 0으로 끝낸다', rec.quit_code, 0)

-- ---------------------------------------------------------------- 진짜 LÖVE
--
--   love.image 는 GPU 를 쓰지 않는 모듈이라 그래픽이 죽은 이 기계에서도 뜬다.
--   그래서 tools/love_headless 로 돌 때만은, 스텁이 아니라 **진짜 LÖVE 의**
--   ImageData 가 프런트엔드가 넘기는 rgba8 바이트열을 그대로 받아 그대로
--   돌려주는지까지 확인할 수 있다. 여기까지 오면 확인하지 못한 것은
--   GPU 가 그 텍스처를 화면에 뿌리는 마지막 한 걸음뿐이다.
--   luajit 으로 돌 때는 saved_love 가 nil 이라 건너뛴다 — 그만큼 통과 수가 적다.
if saved_love and saved_love.image and saved_love.image.newImageData then
  local fb = FE.game:render()
  local _, lut = FE.palette(FE.game.pal_phase)
  local data = FE.make_pixels(fb, lut)
  local id = saved_love.image.newImageData(SCR_W, SCR_H, 'rgba8', data)
  H.check('진짜 LÖVE ImageData 의 크기와 형식',
          {id:getWidth(), id:getHeight(), id:getFormat()}, {SCR_W, SCR_H, 'rgba8'})
  H.check('진짜 LÖVE ImageData 가 같은 256,000바이트를 되돌려 준다',
          id:getString(), data)
end

_G.love = saved_love

H.done()
