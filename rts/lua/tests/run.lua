-- 루아 시험 전체 실행 — Makefile 의 `make lua` 가 이것을 부른다.
--
--    파이썬은 시험 파일 하나가 프로세스 하나였다(harness.done 이 exit 한다).
--    루아는 한 프로세스에서 전부 돌리므로 done() 이 실패 수를 돌려주고
--    여기서 모은다. 출력 형식은 파이썬과 **글자 단위로 같다** — 덱이 두 로그를
--    나란히 놓기 때문이다.
--
--    LÖVE 에서도 그대로 불린다(tools/love_headless). 그래서 os.exit 을 여기서
--    부르지 않고 실패 수만 돌려준다.

package.path = './?.lua;' .. package.path

local M = {}

-- 순서는 Makefile 의 PYTESTS 와 같다 — 의존 방향이기도 하다.
M.NAMES = {
    'test_const', 'test_fixed', 'test_rng', 'test_tmap', 'test_mapgen',
    'test_circle', 'test_spatial', 'test_select', 'test_path', 'test_hpa',
    'test_jps', 'test_flow', 'test_move', 'test_fog', 'test_combat',
    'test_econ', 'test_ai', 'test_sim', 'test_net', 'test_replay',
    'test_speaker', 'test_raster', 'test_render', 'test_prim', 'test_trace',
}

function M.run()
    local failed = 0
    for _, name in ipairs(M.NAMES) do
        local bad = require('tests.' .. name)
        if type(bad) ~= 'number' then
            print('★ ' .. name .. ' 이 실패 수를 돌려주지 않았다')
            failed = failed + 1
        elseif bad ~= 0 then
            print('★ ' .. name .. ' 실패')
            failed = failed + 1
        end
    end
    return failed
end

-- 스크립트로 직접 실행할 때만 종료 코드를 낸다.
if arg ~= nil and arg[0] ~= nil and arg[0]:match('run%.lua$') then
    os.exit(M.run() > 0 and 1 or 0)
end

return M
