-- 드로우 콜 레코더 — 창 없이 프런트엔드가 실제로 그리는지 확인한다.
--
--    이 환경에는 OpenGL 이 없다(SDL 더미 드라이버). `love.graphics` 를 켜면
--    창 생성에서 죽으므로 스크린샷을 찍을 수 없다 — PLAN.md 에 적힌 제약이다.
--    그래서 그림 대신 **호출 기록**과 **프레임버퍼 해시**를 남긴다.
--
--    핵심은 마지막 대조다. 프런트엔드가 만든 프레임버퍼를 PPM 으로 굳혀
--    엔진 CLI 가 낸 out/frame_1200.ppm 과 192,015바이트를 통째로 견준다.
--    빈 화면을 그렸거나, 시뮬을 덜 돌렸거나, 카메라가 어긋났으면 여기서 걸린다.
--    love.image 는 GL 이 필요 없으므로 **진짜**를 쓴다 — 픽셀은 실제로 만들어지고,
--    그 RGBA 바이트열도 따로 해시한다.

local C = require('rts.const')
local F = require('rts.fixed')
local MAIN = require('rts.main')
local RD = require('rts.render')
local RS = require('rts.raster')
local S = require('rts.spatial')

local M = {}

local TICK = 1200                -- §25.4 시나리오의 마지막 틱
local fmt = string.format

--- 호출을 받아 적기만 하는 love.graphics. 인자는 이름과 개수만 남긴다 —
--- 값까지 남기면 로그가 프레임버퍼보다 커지고, 우리가 보려는 것도 아니다.
local function fake_graphics(log)
    local function note(name)
        return function(...)
            log.n = log.n + 1
            log[log.n] = {name = name, argc = select('#', ...)}
            log.count[name] = (log.count[name] or 0) + 1
        end
    end
    local Image = {}
    Image.__index = Image
    function Image:getWidth() return self.w end
    function Image:getHeight() return self.h end
    function Image:replacePixels(id)
        log.n = log.n + 1
        log[log.n] = {name = 'Image:replacePixels', argc = 1}
        log.count['Image:replacePixels'] =
            (log.count['Image:replacePixels'] or 0) + 1
        self.w, self.h = id:getWidth(), id:getHeight()
    end
    local g = {}
    for _, name in ipairs({'clear', 'setColor', 'draw', 'print', 'rectangle',
                           'setDefaultFilter', 'push', 'pop', 'present'}) do
        g[name] = note(name)
    end
    g.newImage = function(id)
        log.n = log.n + 1
        log[log.n] = {name = 'newImage', argc = 1}
        log.count['newImage'] = (log.count['newImage'] or 0) + 1
        log.image_w, log.image_h = id:getWidth(), id:getHeight()
        return setmetatable({w = id:getWidth(), h = id:getHeight()}, Image)
    end
    g.getWidth = function() return C.SCR_W * 3 end
    g.getHeight = function() return C.SCR_H * 3 end
    return g
end

--- 엔진만으로 같은 틱을 다시 그린다. 프런트엔드를 **거치지 않는** 경로라,
--- 두 프레임버퍼가 같다면 프런트엔드가 엔진을 비켜 가지 않은 것이다.
local function reference_frame()
    local s, sc = MAIN.scenario()
    for t = 1, TICK do
        s:step(s:script_orders(sc, t))
    end
    local pal = RS.build_palette()
    local light = RS.build_light(pal)
    local view = RD.newview()
    view:center_on(s.m, s.m.starts[0][0], s.m.starts[0][1])
    local fb = RS.newframe()
    RD.draw(fb.fb, s, view, 0, pal, light, 0, {n = 0}, fmt('TICK %d', TICK))
    return fb.fb, pal
end

--- out/frame_1200.ppm 을 찾아 읽는다. 없으면 nil — 그때는 그 대조만 건너뛴다.
local function read_ppm()
    for _, d in ipairs({'out/', '../out/', '../../out/'}) do
        local f = io.open(fmt('%sframe_%d.ppm', d, TICK), 'rb')
        if f then
            local blob = f:read('*a')
            f:close()
            return blob, fmt('%sframe_%d.ppm', d, TICK)
        end
    end
    return nil, nil
end

--- 입력 경로 점검 — 창이 없어 사람이 눌러 볼 수 없으니 기계가 대신 누른다.
--
--    LÖVE 콜백(love.mousereleased 등)이 그대로 부르는 Game 메서드를 직접 부른다.
--    보는 것은 하나다: **클릭이 sim:step 까지 닿아서 유닛이 실제로 움직였는가.**
--    닿지 않았다면 §12.5 를 어딘가에서 우회한 것이다.
local function input_check(newgame, push)
    local h = newgame('play')
    for _ = 1, 30 do h:advance() end
    h.view:center_on(h.sim.m, 8, 9)
    h:left_down(0, 0)
    h:left_up(C.VIEW_W - 1, C.VIEW_H - 1, false)     -- 뷰포트 전체 상자 선택
    local nsel = h.selection.n
    local w = h.sim.w
    local before = {}
    for k = 0, nsel - 1 do
        local i = S.index(h.selection[k])
        before[k] = w.tx[i] * 1000 + w.ty[i]
    end
    h:right_click(200, 150, false)                   -- 빈 땅으로 이동 명령
    local queued = 0
    for k = 0, nsel - 1 do
        queued = queued + h.uq.q[S.index(h.selection[k])].n
    end
    for _ = 1, 25 do h:advance() end
    local moved = 0
    for k = 0, nsel - 1 do
        local i = S.index(h.selection[k])
        if w:valid(h.selection[k]) and w.tx[i] * 1000 + w.ty[i] ~= before[k] then
            moved = moved + 1
        end
    end
    h.groups:set(1, h.selection)
    local recalled = h.groups:recall(w, 1).n
    h:key_down('s', false, false)                    -- STOP 은 큐를 지나지 않는다
    local stops = h.outbox.n
    push(fmt('  입력 점검   상자 선택 %d기 · 큐에 든 명령 %d개 · 실제로 움직인'
             .. ' 유닛 %d기', nsel, queued, moved))
    push(fmt('              그룹1 복귀 %d기 · S 로 즉시 나간 STOP %d개',
             recalled, stops))
    local bad = 0
    if nsel == 0 or queued == 0 or moved == 0 or recalled ~= nsel
            or stops ~= nsel then
        push('★ 입력이 sim 까지 닿지 않았다')
        bad = 1
    end
    return bad
end

--- 콜백 점검 — love.update·love.draw·love.keypressed 를 직접 불러 본다.
--
--    창이 없어 LÖVE 가 이 콜백들을 돌려 주지 않는다. 그래서 window·keyboard·
--    mouse 를 최소한만 흉내내고 스위치를 잠깐 내려서 **실제 대화형 경로**를
--    다섯 프레임 돌린다. 여기서 죽으면 창이 있는 기계에서도 죽는다.
local function callback_check(log, push)
    local saved = {love.window, love.keyboard, love.mouse}
    love.window = {hasMouseFocus = function() return true end}
    love.keyboard = {isDown = function() return false end}
    love.mouse = {getX = function() return 300 end,
                  getY = function() return 300 end}
    local n0, t0 = log.n, nil
    RTS_RECORDING = false
    local ok, err = pcall(function()
        for _ = 1, 5 do
            love.update(1 / 18)
            love.draw()
        end
        love.mousepressed(30, 30, 1)
        love.mousereleased(300, 300, 1)
        love.mousereleased(300, 300, 2)
        love.keypressed('a')
        love.keypressed('p')
        love.keypressed('f')
        love.keypressed('1')
    end)
    RTS_RECORDING = true
    love.window, love.keyboard, love.mouse = saved[1], saved[2], saved[3]
    if not ok then
        push('★ 대화형 콜백에서 오류: ' .. tostring(err))
        return 1
    end
    push(fmt('  콜백 점검   love.update·love.draw 5프레임 + 마우스·키 7건 —'
             .. ' 드로우 콜 %d회 추가', log.n - n0))
    return 0
end

--- 한 프레임을 녹화한다. 돌려주는 값은 종료 코드다 (0 = 통과).
function M.run(g, newgame)
    local log = {n = 0, count = {}}
    love.graphics = fake_graphics(log)        -- 여기서만 갈아 끼운다

    local t0 = os.clock()
    for _ = 1, TICK do
        g:advance()
    end
    -- 엔진 CLI(`rts/main.lua render`)와 **같은 조건**으로 맞춘다. 카메라·선택·
    -- 메시지가 셋 다 같아야 바이트 비교가 성립한다 — 메시지 한 글자만 달라도
    -- 하단 바 픽셀이 달라진다.
    g.view:center_on(g.sim.m, g.sim.m.starts[0][0], g.sim.m.starts[0][1])
    g.selection = {n = 0}
    g.message = fmt('TICK %d', TICK)
    g.phase = 0
    g.lut_phase = nil
    local idata = g:render()
    g:blit()
    local secs = os.clock() - t0

    local fb_hash = g:fb_hash()
    local rgba = g:rgba(g.pal_now)
    local ref_fb = reference_frame()
    local ref_hash = F.fnv1a(ref_fb)
    local ppm, ppm_path = read_ppm()
    local mine = RS.to_ppm(g.frame.fb, g.pal_now)

    local out = {}
    local function push(s) out[#out + 1] = s end
    push('== LÖVE 프런트엔드 드로우 콜 레코더 (창 없이 한 프레임) ==')
    push(fmt('  런타임      LÖVE %d.%d.%d · 그래픽 모듈 없음 (가짜 love.graphics)',
             love.getVersion()))
    push(fmt('  시뮬        골든 시나리오 %d틱 (%.2f초)', TICK, secs))
    push(fmt('  드로우 콜   %d회', log.n))
    for _, name in ipairs({'clear', 'newImage', 'Image:replacePixels',
                           'setColor', 'draw'}) do
        if log.count[name] then
            push(fmt('    %-20s %d회', name, log.count[name]))
        end
    end
    push(fmt('  이미지      %dx%d (ImageData %dx%d · rgba8 %d바이트)',
             log.image_w or 0, log.image_h or 0,
             idata:getWidth(), idata:getHeight(), #rgba))
    push(fmt('  프레임버퍼  %d바이트 · FNV %08X', g.frame.fb.n, fb_hash))
    push(fmt('  RGBA 바이트열        FNV %08X', F.fnv1a(rgba)))
    push(fmt('  엔진만으로 다시 그린 것 FNV %08X — %s', ref_hash,
             (ref_hash == fb_hash) and '같다' or '★ 다르다'))
    if ppm then
        push(fmt('  %s 와 PPM 바이트 비교 (%d바이트) — %s', ppm_path, #ppm,
                 (ppm == mine) and '같다' or '★ 다르다'))
    else
        push('  out/frame_1200.ppm 이 없어 PPM 대조는 건너뛴다 (make frames)')
    end

    local bad = input_check(newgame, push)
    bad = bad + callback_check(log, push)
    if ref_hash ~= fb_hash then bad = bad + 1 end
    if ppm and ppm ~= mine then bad = bad + 1 end
    if log.n == 0 then
        push('★ 드로우 콜이 하나도 없다 — blit 이 불리지 않았다')
        bad = bad + 1
    end
    push(fmt('결과: 어긋난 항목 %d개', bad))
    print(table.concat(out, '\n'))
    return bad > 0 and 1 or 0
end

return M
