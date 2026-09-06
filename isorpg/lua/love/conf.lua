-- LÖVE 11.5 설정 — GPU 가 있는 기계에서 도는 진짜 프런트엔드용.
--
--   이 저장소를 만든 기계에는 OpenGL 이 없어 love.graphics 가 아예 뜨지 않는다.
--   그래서 이 파일과 main.lua 는 여기서 **실행으로는 검증되지 않았다**.
--   대신 tools/gfx_recorder.lua 가 love.graphics 를 흉내 내어 그리기 호출의
--   순서와 인자, 그리고 올라가는 픽셀까지 tests/test_love_draw.lua 에서 검사한다.
--   헤드리스로 돌릴 수 있는 쪽은 tools/love_headless 다.
--
--   창 크기를 320x200 의 정수배로 잡는 이유는 main.lua 의 확대 계산 때문이다.
--   정수배가 아니면 letterbox 여백이 생기는데, 그것도 잘못이 아니라
--   화면비를 지키는 정상 동작이다 — main.lua 가 가운데로 맞춰 준다.

local SCALE = 3

function love.conf(t)
  t.identity = 'isorpg'
  t.version = '11.5'
  t.console = false

  t.window.title = 'IsoRPG — 320x200 / 8bit (Mode 13h)'
  t.window.width = 320 * SCALE
  t.window.height = 200 * SCALE
  t.window.minwidth = 320
  t.window.minheight = 200
  t.window.resizable = true
  -- vsync 를 켜도 게임 속도는 변하지 않는다. 틱은 54925us 고정이고
  -- 그리기는 몇 번을 하든 상태를 바꾸지 않기 때문이다.
  t.window.vsync = 1

  -- 쓰지 않는 모듈은 끈다. 특히 audio/sound 는 이 문서의 주제가 아니고,
  -- 소리 장치가 없는 기계에서 켜 두면 시작할 때 그대로 죽는다.
  t.modules.audio = false
  t.modules.sound = false
  t.modules.physics = false
  t.modules.video = false
  t.modules.touch = false
  t.modules.joystick = false
end
