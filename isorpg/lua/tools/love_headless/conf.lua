-- 창도 그래픽도 없이 LÖVE 런타임만 쓰는 설정.
--
--   이 기계에는 OpenGL 이 없다. love.graphics 를 켜는 순간 LÖVE 는 시작조차 못 한다.
--   그래서 t.window 를 통째로 비우고 window/graphics 모듈을 끈다. 여기에
--   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy 를 얹으면 SDL 이 장치를 찾지 않는다.
--   Makefile 의 love 타깃이 그 두 환경변수를 붙여 준다.
--
--   그래도 남는 것이 있다 — 루아 런타임 자체다. LÖVE 11.5 는 LuaJIT(5.1 의미론)로
--   돌고, 전역 환경도 표준 lua 와 다르다. 엔진이 그 위에서 그대로 도는지는
--   이 방법으로만 확인할 수 있고, 그것이 이 폴더가 있는 이유다.
--   그리기 쪽은 tools/gfx_recorder.lua 와 tests/test_love_draw.lua 가 맡는다.

function love.conf(t)
  t.identity = 'isorpg_headless'
  t.version = '11.5'
  t.console = false

  t.window = nil
  t.modules.window = false
  t.modules.graphics = false
  t.modules.audio = false
  t.modules.sound = false
  t.modules.physics = false
  t.modules.video = false
  t.modules.touch = false
  t.modules.joystick = false
  t.modules.font = false
  -- love.image 는 GPU 를 쓰지 않으므로 켜 둔 채로 둔다.
end
