-- LÖVE 헤드리스 설정 — 창도 소리도 열지 않는다.
--
--    엔진은 love 를 하나도 쓰지 않는다. 이 디렉터리가 있는 이유는 단 하나,
--    **같은 시험이 LÖVE 런타임에서도 통과하는지** 보이기 위해서다.
--    (LuaJIT 과 LÖVE 의 루아는 같은 5.1 이지만, 로더와 표준 라이브러리 노출이
--     조금 다르다 — 실제로 돌려 봐야 안다.)

function love.conf(t)
    t.identity = 'rts_headless'
    t.console = false
    t.window = nil
    t.modules.window = false
    t.modules.graphics = false
    t.modules.audio = false
    t.modules.sound = false
    t.modules.joystick = false
    t.modules.physics = false
    t.modules.touch = false
    t.modules.video = false
end
