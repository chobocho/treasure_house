-- LÖVE 런타임에서 같은 시험을 돌린다 (make love).
--
--    `cd lua && love tools/love_headless` 로 부르므로 프로세스의 현재 디렉터리는
--    lua/ 다. 그래서 package.path 와 golden 경로가 luajit 으로 돌릴 때와 같다 —
--    love.filesystem 이 아니라 표준 io 를 그대로 쓴다.

package.path = './?.lua;' .. package.path

local exit_code = 0

function love.load()
    local runner = require('tests.run')
    local ok, res = pcall(runner.run)
    if not ok then
        print('★ 시험 도중 오류: ' .. tostring(res))
        exit_code = 1
    elseif res > 0 then
        exit_code = 1
    end
    love.event.quit(exit_code)
end

-- 그래픽 모듈을 끄고 돌리므로 draw 는 비어 있다.
function love.draw()
end
