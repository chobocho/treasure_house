-- LÖVE 프런트엔드 설정 — 창 크기와 모듈 선택, 그리고 package.path.
--
--    conf.lua 는 love 의 어떤 모듈보다도 먼저 불린다. 엔진을 찾는 경로를 여기서
--    손봐야 main.lua 의 첫 require 가 확실히 성공한다. 저장소 뿌리(rts/)에서
--    부르든 lua/ 에서 부르든 `rts.*` 가 풀리도록 후보를 둘 다 넣는다 —
--    lua/tools/love_headless 는 lua/ 에서만 부르므로 './?.lua' 하나로 족했지만,
--    이 프런트엔드는 `love lua/love` 로도 부른다.
package.path = './?.lua;./lua/?.lua;../?.lua;' .. package.path

local C = require('rts.const')

RTS_SCALE = 3                    -- 정수배만 쓴다. 팔레트 화면을 부드럽게 늘리면
                                 -- 팔레트에 없는 색이 생긴다(§22.1).

--- 명령줄에 그 낱말이 있는가. LÖVE 는 게임 경로 뒤의 인자를 arg 에 그대로 준다.
function RTS_FLAG(name)
    if type(arg) ~= 'table' then
        return false
    end
    for _, v in ipairs(arg) do
        if v == name then
            return true
        end
    end
    return false
end

function love.conf(t)
    t.identity = 'rts_love'
    t.console = false
    t.modules.audio = false      -- 스피커(§21)는 엔진이 WAV 로 뽑는다. 실시간
    t.modules.sound = false      -- 재생은 이 덱의 주제가 아니다.
    t.modules.joystick = false
    t.modules.physics = false
    t.modules.touch = false
    t.modules.video = false
    if RTS_FLAG('--record') then
        -- 이 환경에는 OpenGL 이 없다(더미 비디오 드라이버). 그래픽 모듈을 켜면
        -- 창 생성에서 그 자리에 죽으므로, 녹화 모드는 love.graphics 를 아예
        -- 올리지 않고 record.lua 의 가짜로 갈아 끼운다. love.image 는 GL 이
        -- 필요 없어서 **진짜**를 쓴다 — 픽셀은 실제로 만들어진다.
        t.modules.window = false
        t.modules.graphics = false
        t.window = nil
        return
    end
    t.window.title = 'DOS-RTS — LÖVE'
    t.window.width = C.SCR_W * RTS_SCALE
    t.window.height = C.SCR_H * RTS_SCALE
    t.window.resizable = false
    t.window.vsync = 1
end
