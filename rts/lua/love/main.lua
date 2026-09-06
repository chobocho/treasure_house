-- LÖVE 11.5 프런트엔드 — pygame 쪽과 같은 껍데기다 (SPEC §12·§23).
--
--    입력 → 명령 → net(§19) → sim:step → render → 화면. 반대 방향 화살표는 없다.
--    UI 가 sim 의 상태를 직접 건드리는 줄은 여기 하나도 없고, 그래야 §12.5 가
--    산다. 사람의 클릭이 AI·스크립트와 **완전히 같은 경로**를 지난다.
--
--    그리기는 다시 구현하지 않는다. rts.render 가 320×200 팔레트 인덱스
--    프레임버퍼를 채우고, 이 파일은 그것을 팔레트로 색칠해 ImageData 하나로
--    올릴 뿐이다. 그래서 이 프런트엔드가 그린 그림은 루아 엔진의 PPM 과
--    바이트까지 같다 — record.lua 가 그것을 매번 확인한다.

local C = require('rts.const')
local F = require('rts.fixed')
local MAIN = require('rts.main')
local NET = require('rts.net')
local RD = require('rts.render')
local RS = require('rts.raster')
local S = require('rts.spatial')
local SEL = require('rts.select')
local SIM = require('rts.sim')
local T = require('rts.tmap')

local floor = math.floor

local SCALE = RTS_SCALE or 3
local KEY_SCROLL = 8             -- 화살표는 가장자리 스크롤(4px/틱)의 두 배
local DRAG_MIN = 3               -- 이보다 짧게 끈 것은 상자가 아니라 클릭이다
local CYCLE_EVERY = 2            -- §22.6 물 색은 두 틱에 한 칸
local TICK_S = C.TICK_US / 1000000

-- F1..F5 로 생산. 숫자 키는 §12.3 컨트롤 그룹이 이미 쓰고 있어서 비켜 놨다.
local TRAIN_KEYS = {f1 = C.INF, f2 = C.ARCHER, f3 = C.TANK,
                    f4 = C.MORTAR, f5 = C.HARV}

local RECORD = (RTS_FLAG ~= nil) and RTS_FLAG('--record') or false
-- 전역인 이유는 record.lua 가 이 스위치를 잠깐 내리고 love.update·love.draw 를
-- 직접 불러 보기 때문이다 — 창이 없어 사람이 못 눌러 보는 경로를 그렇게 훑는다.
RTS_RECORDING = RECORD

-- ── §12.1 픽킹이 쓰는 알파 마스크 ───────────────────────────────────────────
--
--    RLE 를 한 번 펴서 (종류, 방향)마다 캐시한다. 국소 좌표를 그대로 쓸 수 있는
--    이유는 블릿 기준점이 px + TILE*FOOT/2 이고 스프라이트의 ox 가 폭의 절반이라,
--    스프라이트 상자의 좌상단이 §12.1 의 AABB 좌상단과 정확히 겹치기 때문이다.
local mask_cache = {}

local function sprite_mask(kind, d, lx, ly)
    local key = kind * 16 + d
    local ent = mask_cache[key]
    if ent == nil then
        local spr, flip = RS.sprite_for(kind, d)
        ent = {spr, flip, spr ~= nil and spr:pixels() or nil}
        mask_cache[key] = ent
    end
    local spr, flip, px = ent[1], ent[2], ent[3]
    if spr == nil then
        return true                          -- 그림이 없으면 AABB 로 만족한다
    end
    if flip then
        lx = spr.w - 1 - lx
    end
    if lx < 0 or lx >= spr.w or ly < 0 or ly >= spr.h then
        return false
    end
    return px[ly * spr.w + lx] ~= 0
end

local function in_minimap(sx, sy)
    return sx >= C.MINI_X and sx < C.MINI_X + C.MINI_W
           and sy >= C.MINI_Y and sy < C.MINI_Y + C.MINI_H
end

-- ── 게임 ────────────────────────────────────────────────────────────────────
local Game = {}
Game.__index = Game

--- mode 'scenario' 는 골든 시나리오(§18.6)를 그대로 재생한다. 'play' 는 사람이
--- 0번을 잡고 나머지를 §17 의 AI 에게 맡긴다.
local function newgame(mode, player, seed)
    local self = setmetatable({}, Game)
    local m = T.load_text(MAIN.golden('map_start.txt'))
    self.p = player or 0
    if mode == 'scenario' then
        self.script = SIM.parse_script(MAIN.golden('script.txt'))
        self.sim = SIM.new(m, seed or 1, self.script.players)
        self.sim:setup_start(false)          -- 스크립트가 몬다(§18.6)
    else
        self.script = nil
        self.sim = SIM.new(m, seed or 1, 2)
        self.sim:setup_start(false)
        for p = 1, self.sim.players - 1 do
            self.sim.ai_enabled[p] = true
        end
    end
    self.pal = RS.build_palette()
    self.light = RS.build_light(self.pal)    -- 262,144회 비교 — 시작할 때 한 번
    self.frame = RS.newframe()
    self.view = RD.newview()
    self.view:center_on(self.sim.m, self.sim.m.starts[self.p][0],
                        self.sim.m.starts[self.p][1])
    self.net = NET.new(1, C.ORDER_DELAY)
    self.outbox = {n = 0}
    self.uq = SEL.neworders()                -- §12.4 — UI 쪽 명령 큐
    self.wait = {}
    for i = 0, C.MAX_ENT - 1 do self.wait[i] = 0 end
    self.groups = SEL.newgroups()
    self.selection = {n = 0}
    self.phase = 0
    self.message = ''
    self.drag = nil
    self.amove = false
    self.scale = SCALE
    self.acc = 0
    self.paused = false
    self.mx, self.my = -1, -1
    return self
end

function Game:cam()
    return {[0] = self.view.cam_x, [1] = self.view.cam_y}
end

--- 선택된 전원에게 같은 명령. 여기서 큐에 넣을 뿐 시뮬은 건드리지 않는다.
--- STOP 만 큐를 지나지 않는다 — §12.4 의 push 가 STOP 을 "큐를 비우는 신호"로
--- 정의했기 때문이다. 비운 뒤 곧바로 보내야 실제로 선다.
function Game:issue(kind, a, b, c, shift)
    a, b, c = a or 0, b or 0, c or 0
    local w = self.sim.w
    for k = 0, self.selection.n - 1 do
        local h = self.selection[k]
        if w:valid(h) then
            local i = S.index(h)
            self.uq:push(i, SIM.tup(kind, a, b, c), shift)
            if kind == SEL.STOP then
                self.outbox[self.outbox.n] = SIM.tup(self.p, h, SEL.STOP, 0, 0, 0)
                self.outbox.n = self.outbox.n + 1
                self.wait[i] = C.ORDER_DELAY + 1
            elseif not shift then
                self.wait[i] = 0             -- 새 명령은 다음 틱에 바로 나간다
            end
        end
    end
end

--- 큐의 머리를 하나씩 내보낸다. 유닛이 놀고 있을 때만 다음 것을 꺼낸다.
--- 보낸 뒤 ORDER_DELAY+1 틱을 기다리는 이유: 명령은 §12.5 대로 2틱 뒤에
--- 도착하므로, 그 사이에 상태를 보면 아직 ST_IDLE 이라 같은 명령을 두 번 보낸다.
function Game:pump()
    local w = self.sim.w
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] == 0 then
            if self.uq.q[i].n > 0 then self.uq:clear(i) end
        elseif self.wait[i] > 0 then
            self.wait[i] = self.wait[i] - 1
        elseif self.uq.q[i].n > 0 and w.state[i] == C.ST_IDLE then
            local o = self.uq:pop(i)
            self.outbox[self.outbox.n] =
                SIM.tup(self.p, w:handle(i), o[0], o[1], o[2], o[3])
            self.outbox.n = self.outbox.n + 1
            self.wait[i] = C.ORDER_DELAY + 1
        end
    end
end

--- 한 틱. 사람·스크립트·AI 의 명령이 여기 한 곳에서 합쳐져 정렬된다.
function Game:advance()
    self:pump()
    local now = self.sim.tick
    for k = 0, self.outbox.n - 1 do
        self.net:send(now, self.p, self.outbox[k])
    end
    self.outbox = {n = 0}
    self.net:flush(now, self.p)              -- 빈 턴도 보낸다(§19.2)
    local nt = now + 1
    local orders = self.net:take(nt)
    if self.script ~= nil then
        local so = self.sim:script_orders(self.script, nt)
        for k = 0, so.n - 1 do
            orders[orders.n] = so[k]
            orders.n = orders.n + 1
        end
    end
    SIM.sort_tuples(orders)                  -- §18.1 — 정렬은 sim 이 검사한다
    local h = self.sim:step(orders)
    self.phase = floor(self.sim.tick / CYCLE_EVERY) % RS.WATER_N
    local keep = {n = 0}
    for k = 0, self.selection.n - 1 do
        if self.sim.w:valid(self.selection[k]) then
            keep[keep.n] = self.selection[k]
            keep.n = keep.n + 1
        end
    end
    self.selection = keep
    return h
end

-- ── 입력 ────────────────────────────────────────────────────────────────────
--- 카메라는 정수 픽셀이다(§23.2). 화살표가 눌렸으면 가장자리는 쉰다.
function Game:scroll()
    local dx, dy = 0, 0
    local kb = love.keyboard
    if kb.isDown('left') then dx = dx - KEY_SCROLL end
    if kb.isDown('right') then dx = dx + KEY_SCROLL end
    if kb.isDown('up') then dy = dy - KEY_SCROLL end
    if kb.isDown('down') then dy = dy + KEY_SCROLL end
    if dx == 0 and dy == 0 then
        dx, dy = RD.edge_scroll(self.mx, self.my)
    end
    if dx ~= 0 or dy ~= 0 then
        self.view:move(self.sim.m, dx, dy)
    end
end

function Game:left_down(sx, sy)
    if SEL.in_view(sx, sy) then
        self.drag = {sx, sy}
    end
end

function Game:left_up(sx, sy, shift)
    local start = self.drag
    self.drag = nil
    if in_minimap(sx, sy) then
        local tx, ty = RD.minimap_to_tile(sx - C.MINI_X, sy - C.MINI_Y)
        self.view:center_on(self.sim.m, tx, ty)
        return
    end
    if not SEL.in_view(sx, sy) then
        return
    end
    if self.amove then                       -- A 다음의 좌클릭은 공격 이동
        self.amove = false
        local wx, wy = SEL.screen_to_world(self:cam(), sx, sy)
        self:issue(SEL.ATTACK_MOVE, F.floordiv(wx, C.TILE),
                   F.floordiv(wy, C.TILE), 0, shift)
        self.message = ''
        return
    end
    if start ~= nil and (math.abs(sx - start[1]) >= DRAG_MIN
                         or math.abs(sy - start[2]) >= DRAG_MIN) then
        self.selection = SEL.box_select(self.sim.w, self.p, self:cam(),
                                        start[1], start[2], sx, sy)
        return
    end
    local h = SEL.pick(self.sim.w, self:cam(), sx, sy, sprite_mask)
    if h ~= 0 and self.sim.w.owner[S.index(h)] == self.p then
        self.selection = {n = 1, [0] = h}
    else
        self.selection = {n = 0}             -- 남의 것은 고르지 않는다
    end
end

--- §12.4 의 문맥 규칙을 그대로 따른다 — 판정 순서가 곧 명세다.
function Game:right_click(sx, sy, shift)
    if in_minimap(sx, sy) then
        local tx, ty = RD.minimap_to_tile(sx - C.MINI_X, sy - C.MINI_Y)
        self:issue(SEL.MOVE, tx, ty, 0, shift)
        return
    end
    if not SEL.in_view(sx, sy) then
        return
    end
    self.amove = false
    local wx, wy = SEL.screen_to_world(self:cam(), sx, sy)
    local tx, ty = F.floordiv(wx, C.TILE), F.floordiv(wy, C.TILE)
    local h = SEL.pick(self.sim.w, self:cam(), sx, sy, sprite_mask)
    local kind = SEL.context_order(self.sim.w, self.sim.ec, self.sim.m,
                                   self.p, tx, ty, h)
    self:issue(kind, tx, ty, (kind == SEL.ATTACK) and h or 0, shift)
end

function Game:key_down(key, ctrl, shift)
    local w = self.sim.w
    local g = tonumber(key)
    if g ~= nil and #key == 1 then
        if ctrl then
            self.groups:set(g, self.selection)   -- §12.3 — 핸들만 담는다
            self.message = 'GROUP ' .. g .. ' SET'
        else
            self.selection = self.groups:recall(w, g)
            if self.selection.n > 0 then
                local j = S.index(self.selection[0])
                self.view:center_on(self.sim.m, w.tx[j], w.ty[j])
            end
        end
        return
    end
    if TRAIN_KEYS[key] ~= nil then
        self:issue(SEL.TRAIN, TRAIN_KEYS[key], 0, 0, shift)
    elseif key == 's' then
        self:issue(SEL.STOP)
    elseif key == 'h' then
        self:issue(SEL.HOLD)
    elseif key == 'a' then
        self.amove = true
        self.message = 'ATTACK MOVE'
    elseif key == 'space' and self.selection.n > 0 then
        local j = S.index(self.selection[0])
        self.view:center_on(self.sim.m, w.tx[j], w.ty[j])
    end
end

-- ── 그리기 ──────────────────────────────────────────────────────────────────
--- 드래그 상자는 시뮬과 무관한 UI 라 프레임버퍼에 직접 긋는다.
--- _fill 이 뷰포트로 잘라 주므로 경계 검사를 다시 하지 않는다.
function Game:drag_box()
    if self.drag == nil then
        return
    end
    local x0, y0 = self.drag[1], self.drag[2]
    local x1, y1 = self.mx, self.my
    if x1 < x0 then x0, x1 = x1, x0 end
    if y1 < y0 then y0, y1 = y1, y0 end
    local fb, v = self.frame.fb, RD.UI_SELECT
    RD._fill(fb, x0, y0, x1 - x0 + 1, 1, v)
    RD._fill(fb, x0, y1, x1 - x0 + 1, 1, v)
    RD._fill(fb, x0, y0, 1, y1 - y0 + 1, v)
    RD._fill(fb, x1, y0, 1, y1 - y0 + 1, v)
end

--- 프레임버퍼 → RGBA8 바이트열. setPixel 6만4천 번 대신 문자열을 한 번에 만든다.
--- 같은 그림이므로 결과는 setPixel 로 채운 것과 한 바이트도 다르지 않다.
function Game:rgba(pal)
    if self.lut_phase ~= self.phase then
        local lut = {}
        for c = 0, pal.n - 1 do
            lut[c] = string.char(RS.expand(pal[c][1]), RS.expand(pal[c][2]),
                                 RS.expand(pal[c][3]), 255)
        end
        self.lut, self.lut_phase = lut, self.phase
    end
    local lut, fb = self.lut, self.frame.fb
    local rows, row = {}, {}
    for y = 0, C.SCR_H - 1 do
        local base = y * C.SCR_W
        for x = 0, C.SCR_W - 1 do
            row[x + 1] = lut[fb[base + x]]
        end
        rows[y + 1] = table.concat(row)
    end
    return table.concat(rows)
end

--- 프레임버퍼를 채우고 ImageData 를 새로 만든다. 팔레트 사이클(§22.6)은
--- 프레임버퍼를 건드리지 않는다 — 팔레트만 갈아 끼운다.
function Game:render()
    local pal = RS.cycle_water(self.pal, self.phase)
    RD.draw(self.frame.fb, self.sim, self.view, self.phase, pal, self.light,
            self.p, self.selection, self.message)
    self:drag_box()
    self.pal_now = pal
    self.idata = love.image.newImageData(C.SCR_W, C.SCR_H, 'rgba8',
                                         self:rgba(pal))
    return self.idata
end

--- love.graphics 를 쓰는 유일한 자리. record.lua 는 여기를 가짜로 받아 적는다.
function Game:blit()
    local g = love.graphics
    g.clear(0, 0, 0, 1)
    if self.image == nil then
        self.image = g.newImage(self.idata)
    else
        self.image:replacePixels(self.idata)
    end
    g.setColor(1, 1, 1, 1)
    g.draw(self.image, 0, 0, 0, self.scale, self.scale)
end

--- 프레임버퍼의 FNV-1a. 세 언어·두 프런트엔드가 같은 그림을 그렸는지 한 줄로
--- 비교하는 값이다 (pygame 쪽 shots.py 가 같은 값을 낸다).
function Game:fb_hash()
    return F.fnv1a(self.frame.fb)
end

-- ── LÖVE 콜백 ───────────────────────────────────────────────────────────────
local G = nil

function love.load()
    if RECORD then
        -- 창도 GL 도 없이 한 프레임을 찍어 본다. record 가 가짜 love.graphics 를
        -- 꽂고, Game:blit 이 그것을 잡아 쓴다. love.image 는 진짜다.
        local rec = require('record')
        G = newgame('scenario')
        love.event.quit(rec.run(G, newgame))
        return
    end
    love.graphics.setDefaultFilter('nearest', 'nearest')   -- 정수배 확대(§22.1)
    G = newgame('play')
end

function love.update(dt)
    if G == nil or RTS_RECORDING then
        return
    end
    G.mx, G.my = -1, -1
    if love.window.hasMouseFocus() then
        G.mx = floor(love.mouse.getX() / G.scale)
        G.my = floor(love.mouse.getY() / G.scale)
    end
    G:scroll()
    if not G.paused then
        -- 한 프레임에 최대 세 틱만 따라간다. 못 따라가는 기계에서 무한히
        -- 밀리는 것보다 느려지는 편이 낫다.
        G.acc = G.acc + dt
        local n = 0
        while G.acc >= TICK_S and n < 3 do
            G.acc = G.acc - TICK_S
            G:advance()
            n = n + 1
        end
        if G.acc >= TICK_S then
            G.acc = 0
        end
    end
    G.message = G.paused and 'PAUSED' or ('T' .. G.sim.tick)
end

function love.draw()
    if G == nil or RTS_RECORDING then
        return
    end
    G:render()
    G:blit()
end

function love.mousepressed(x, y, button)
    if G == nil then return end
    if button == 1 then
        G:left_down(floor(x / G.scale), floor(y / G.scale))
    end
end

function love.mousereleased(x, y, button)
    if G == nil then return end
    local shift = love.keyboard.isDown('lshift', 'rshift')
    local sx, sy = floor(x / G.scale), floor(y / G.scale)
    if button == 1 then
        G:left_up(sx, sy, shift)
    elseif button == 2 then
        G:right_click(sx, sy, shift)
    end
end

function love.keypressed(key)
    if G == nil then return end
    if key == 'escape' then
        love.event.quit(0)
    elseif key == 'p' then
        G.paused = not G.paused
    elseif key == 'f' and G.paused then
        G:advance()                          -- 한 틱만 — 버그를 볼 때 쓴다
    else
        G:key_down(key, love.keyboard.isDown('lctrl', 'rctrl'),
                   love.keyboard.isDown('lshift', 'rshift'))
    end
end
