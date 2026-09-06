-- 화면 구성 — 레이어·스크롤·y 정렬·미니맵·패널 (SPEC §23).
--
--    렌더는 **상태를 읽기만 한다.** sim 을 건드리는 줄이 하나라도 생기면
--    락스텝이 끝난다(§18.1). 팔레트 사이클 위상도 인자로만 받는다.
--
--    지형 타일은 그림이 아니라 색이다(§23.1). 아티스트가 없으므로 한 칸을
--    MINI_COLOR 로 채우고, 오토타일 마스크가 가리키는 "나와 다른 지형" 쪽
--    가장자리 1px 만 어둡게 긋는다. 5부는 그 선으로 마스크가 화면에서 무엇을
--    바꾸는지 보인다.

local C = require('rts.const')
local F = require('rts.fixed')
local RS = require('rts.raster')
local S = require('rts.spatial')
local T = require('rts.tmap')

local M = {}
local floor = math.floor

M.TILES_X = floor(C.VIEW_W / C.TILE) + 1
M.TILES_Y = floor(C.VIEW_H / C.TILE) + 1
M.EDGE_SPEED = 4
M.EDGE_MARGIN = 8
M.MAX_CAM_X = C.MAP_W * C.TILE - C.VIEW_W
M.MAX_CAM_Y = C.MAP_H * C.TILE - C.VIEW_H
local TILES_X, TILES_Y, EDGE_SPEED, EDGE_MARGIN = M.TILES_X, M.TILES_Y, 4, 8

M.UI_DARK, M.UI_MID, M.UI_LIGHT, M.UI_TEXT = 193, 195, 197, 198
M.UI_HP_GOOD, M.UI_HP_BAD, M.UI_SELECT = 201, 200, 199
local UI_DARK, UI_MID, UI_LIGHT, UI_TEXT = 193, 195, 197, 198
local UI_HP_GOOD, UI_HP_BAD, UI_SELECT = 201, 200, 199

-- ── SPEC §23.2 스크롤 ───────────────────────────────────────────────────────

--- 카메라는 **정수 픽셀**이다. 서브픽셀 스크롤은 도스 시절 흔치 않았고,
--- 정수로 두면 타일 그리기가 오프셋 하나로 끝난다.
local View = {}
View.__index = View
M.View = View

function M.newview(cam_x, cam_y)
    return setmetatable({cam_x = cam_x or 0, cam_y = cam_y or 0}, View)
end
View.new = M.newview

function View:_clamp(m)
    local mx = m.w * C.TILE - C.VIEW_W
    local my = m.h * C.TILE - C.VIEW_H
    if self.cam_x < 0 then self.cam_x = 0 end
    if self.cam_y < 0 then self.cam_y = 0 end
    if self.cam_x > mx then self.cam_x = mx end
    if self.cam_y > my then self.cam_y = my end
end

function View:move(m, dx, dy)
    self.cam_x = self.cam_x + dx
    self.cam_y = self.cam_y + dy
    self:_clamp(m)
end

function View:center_on(m, tx, ty)
    self.cam_x = tx * C.TILE - floor(C.VIEW_W / 2)
    self.cam_y = ty * C.TILE - floor(C.VIEW_H / 2)
    self:_clamp(m)
end

--- (첫 타일 x, 첫 타일 y, 픽셀 오프셋 x, 오프셋 y).
function View:first_tile()
    return F.floordiv(self.cam_x, C.TILE), F.floordiv(self.cam_y, C.TILE),
           F.fmod(self.cam_x, C.TILE), F.fmod(self.cam_y, C.TILE)
end

--- 마우스가 뷰포트 가장자리 8px 안이면 그 방향으로 4px/틱.
function M.edge_scroll(mx, my)
    if not (mx >= 0 and mx < C.VIEW_W and my >= 0 and my < C.VIEW_H) then
        return 0, 0
    end
    local dx, dy = 0, 0
    if mx < EDGE_MARGIN then
        dx = -EDGE_SPEED
    elseif mx >= C.VIEW_W - EDGE_MARGIN then
        dx = EDGE_SPEED
    end
    if my < EDGE_MARGIN then
        dy = -EDGE_SPEED
    elseif my >= C.VIEW_H - EDGE_MARGIN then
        dy = EDGE_SPEED
    end
    return dx, dy
end

-- ── SPEC §23.3 y 정렬 ───────────────────────────────────────────────────────

--- 발밑 y · x · 핸들. 키가 전순서라 안정 정렬 여부에 의존하지 않는다.
function M.sort_key(w, i)
    local foot = C.FOOT[w.kind[i]]
    return {[0] = F.fp_floor(w.py[i]) + foot * C.TILE, F.fp_floor(w.px[i]),
            w:handle(i), n = 3}
end
local sort_key = M.sort_key

local function key_gt(a, b)
    for k = 0, 2 do
        if a[k] ~= b[k] then return a[k] > b[k] end
    end
    return false
end

--- 삽입 정렬. 프레임 사이에 목록이 거의 정렬되어 있어 거의 O(n) 이다.
function M.y_order(w)
    local out = {}                              -- 1-기반 (table.insert 를 쓴다)
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] ~= 0 then
            local k = sort_key(w, i)
            local j = #out + 1
            while j > 1 and key_gt(sort_key(w, out[j - 1]), k) do
                j = j - 1
            end
            table.insert(out, j, i)
        end
    end
    local res = {n = #out}
    for j = 1, #out do res[j - 1] = out[j] end
    return res
end

-- ── SPEC §23.4 미니맵 ───────────────────────────────────────────────────────
function M.minimap_nearest(m, sx, sy)
    return m.terrain[floor(sy * m.h / C.MINI_H) * m.w
                     + floor(sx * m.w / C.MINI_W)]
end

--- 블록에서 가장 많이 나온 지형, 동점이면 지형 번호 최소. 128 맵을 대비한다.
function M.minimap_majority(m, sx, sy)
    local x0 = floor(sx * m.w / C.MINI_W)
    local x1 = floor((sx + 1) * m.w / C.MINI_W)
    local y0 = floor(sy * m.h / C.MINI_H)
    local y1 = floor((sy + 1) * m.h / C.MINI_H)
    if x1 <= x0 then x1 = x0 + 1 end
    if y1 <= y0 then y1 = y0 + 1 end
    local cnt = {}
    for t = 0, 7 do cnt[t] = 0 end
    local ylim = y1 < m.h and y1 or m.h
    local xlim = x1 < m.w and x1 or m.w
    for y = y0, ylim - 1 do
        for x = x0, xlim - 1 do
            local t = m.terrain[y * m.w + x]
            cnt[t] = cnt[t] + 1
        end
    end
    local best, bn = 0, -1
    for t = 0, 7 do
        if cnt[t] > bn then
            bn, best = cnt[t], t
        end
    end
    return best
end

function M.minimap_to_tile(sx, sy)
    return floor(sx * C.MAP_W / C.MINI_W), floor(sy * C.MAP_H / C.MINI_H)
end

-- ── 안개가 가리는 것 ────────────────────────────────────────────────────────

--- §23.1 — **유닛 숨기기는 명암표가 못 한다.** 보이는 칸의 것만 그린다.
function M.visible_entities(sim, p)
    local out = {n = 0}
    local order = M.y_order(sim.w)
    for k = 0, order.n - 1 do
        local i = order[k]
        local t = sim.w.ty[i] * sim.m.w + sim.w.tx[i]
        if sim.fog:visible(p, t) then
            out[out.n] = i
            out.n = out.n + 1
        end
    end
    return out
end

--- 자릿수 고정 — 숫자가 흔들리면 더티 렉트가 커진다.
function M.credits_text(v)
    if v > 99999 then v = 99999 end
    local s = string.format('%d', v)
    return string.rep(' ', 5 - #s) .. s
end
local credits_text = M.credits_text

-- ── SPEC §23.1 레이어 ───────────────────────────────────────────────────────
local function fill(fb, x, y, w, h, v)
    local j0 = y > 0 and y or 0
    local j1 = (y + h) < C.VIEW_H and (y + h) or C.VIEW_H
    local i0 = x > 0 and x or 0
    local i1 = (x + w) < C.VIEW_W and (x + w) or C.VIEW_W
    for j = j0, j1 - 1 do
        local row = j * C.SCR_W
        for i = i0, i1 - 1 do
            fb[row + i] = v
        end
    end
end
M._fill = fill

local function draw_terrain(fb, sim, view, light, p)
    local m = sim.m
    local tx0, ty0, ox, oy = view:first_tile()
    local ylim = m.h < ty0 + TILES_Y and m.h or ty0 + TILES_Y
    local xlim = m.w < tx0 + TILES_X and m.w or tx0 + TILES_X
    for ty = ty0, ylim - 1 do
        for tx = tx0, xlim - 1 do
            local px = (tx - tx0) * C.TILE - ox
            local py = (ty - ty0) * C.TILE - oy
            local level = sim.fog:level(p, tx, ty)
            if level == 0 then
                fill(fb, px, py, C.TILE, C.TILE, 0)
            else
                local t = m.terrain[ty * m.w + tx]
                local base = T.MINI_COLOR[t]
                local edge = (base % 8 >= 2) and (base - 2) or (base + 1)
                if level < 3 then
                    base = light[level][base]
                    edge = light[level][edge]
                end
                fill(fb, px, py, C.TILE, C.TILE, base)
                local mask = m:mask(tx, ty)   -- §4.4 — 다른 지형 쪽만 긋는다
                if F.bit(mask, 0) == 0 then
                    fill(fb, px, py, C.TILE, 1, edge)
                end
                if F.bit(mask, 4) == 0 then
                    fill(fb, px, py + C.TILE - 1, C.TILE, 1, edge)
                end
                if F.bit(mask, 6) == 0 then
                    fill(fb, px, py, 1, C.TILE, edge)
                end
                if F.bit(mask, 2) == 0 then
                    fill(fb, px + C.TILE - 1, py, 1, C.TILE, edge)
                end
            end
        end
    end
end

--- 체력바와 선택 표시. 뷰포트 안에서만 그린다.
local function bars(fb, w, i, x0, y0, spr, selected)
    local hp = w.hp[i]
    local full = C.HP[w.kind[i]]
    if full <= 0 then
        return
    end
    local wdt = spr.w - 2
    local f = floor(wdt * hp / full)
    local y = y0 - 2
    if y >= 0 and y < C.VIEW_H then
        for k = 0, wdt - 1 do
            local x = x0 + 1 + k
            if x >= 0 and x < C.VIEW_W then
                fb[y * C.SCR_W + x] = (k < f) and UI_HP_GOOD or UI_HP_BAD
            end
        end
    end
    if selected then
        for k = 0, spr.w - 1 do
            local x = x0 + k
            for _, yy in ipairs({y0, y0 + spr.h - 1}) do
                if x >= 0 and x < C.VIEW_W and yy >= 0 and yy < C.VIEW_H then
                    fb[yy * C.SCR_W + x] = UI_SELECT
                end
            end
        end
    end
end

local function draw_entities(fb, sim, view, light, p, selection)
    local w = sim.w
    local sel = {}
    for k = 0, selection.n - 1 do sel[selection[k]] = true end
    local vis = M.visible_entities(sim, p)
    for k = 0, vis.n - 1 do
        local i = vis[k]
        local spr, flip = RS.sprite_for(w.kind[i], w.dir[i])
        if spr ~= nil then
            local sx = F.fp_floor(w.px[i]) - view.cam_x
            local sy = F.fp_floor(w.py[i]) - view.cam_y
            local anchor_x = sx + floor(C.TILE * C.FOOT[w.kind[i]] / 2)
            local anchor_y = sy + C.TILE * C.FOOT[w.kind[i]] - 2
            RS.blit(fb, spr, anchor_x, anchor_y, w.owner[i], flip)
            bars(fb, w, i, anchor_x - spr.ox, anchor_y - spr.oy, spr,
                 sel[w:handle(i)] == true)
        end
    end
end

local function draw_projectiles(fb, sim, view)
    for k = 0, sim.pj:n() - 1 do
        local x = F.fp_floor(sim.pj.x[k]) - view.cam_x
        local y = F.fp_floor(sim.pj.y[k]) - view.cam_y
        if x >= 0 and x < C.VIEW_W and y >= 0 and y < C.VIEW_H then
            fb[y * C.SCR_W + x] = UI_TEXT
        end
    end
end

--- UTF-8 문자열의 첫 n 글자 (파이썬의 s[:n] 과 같은 단위).
local function utf8_head(s, n)
    local cps = RS.codepoints(s)
    if cps.n <= n then
        return s
    end
    -- 코드포인트 n 개까지의 바이트 길이를 다시 센다.
    local i, cnt = 1, 0
    while i <= #s and cnt < n do
        local b = s:byte(i)
        local len = 1
        if b >= 0xF0 then len = 4
        elseif b >= 0xE0 then len = 3
        elseif b >= 0xC0 then len = 2 end
        i = i + len
        cnt = cnt + 1
    end
    return s:sub(1, i - 1)
end
M.utf8_head = utf8_head

local function draw_panel(fb, sim, view, p, selection)
    local m = sim.m
    for y = 0, C.SCR_H - 1 do
        local row = y * C.SCR_W
        for x = C.PANEL_X, C.SCR_W - 1 do
            fb[row + x] = UI_DARK
        end
    end
    for sy = 0, C.MINI_H - 1 do                -- 미니맵 — 한 타일이 한 픽셀
        local row = (C.MINI_Y + sy) * C.SCR_W
        for sx = 0, C.MINI_W - 1 do
            local tx, ty = M.minimap_to_tile(sx, sy)
            local level = sim.fog:level(p, tx, ty)
            if level == 0 then
                fb[row + C.MINI_X + sx] = 0
            else
                fb[row + C.MINI_X + sx] =
                    T.MINI_COLOR[M.minimap_nearest(m, sx, sy)]
            end
        end
    end
    for i = 1, C.MAX_ENT - 1 do                -- 미니맵 위의 유닛
        if sim.w.alive[i] ~= 0 then
            local t = sim.w.ty[i] * m.w + sim.w.tx[i]
            if sim.fog:visible(p, t) then
                local sx = floor(sim.w.tx[i] * C.MINI_W / m.w)
                local sy = floor(sim.w.ty[i] * C.MINI_H / m.h)
                fb[(C.MINI_Y + sy) * C.SCR_W + C.MINI_X + sx] =
                    RS.PLAYER_BASE + sim.w.owner[i] * 8 + 5
            end
        end
    end
    RS.text(fb, 'SEL', C.PANEL_X + 2, C.MINI_H + 4, UI_TEXT)
    if selection.n > 0 then
        local h = selection[0]
        if sim.w:valid(h) then
            local j = S.index(h)
            RS.text(fb, utf8_head(C.NAME[sim.w.kind[j]], 1)
                    .. string.format('%d', sim.w.kind[j]),
                    C.PANEL_X + 2, C.MINI_H + 14, UI_TEXT)
            RS.text(fb, credits_text(sim.w.hp[j]), C.PANEL_X + 2,
                    C.MINI_H + 24, UI_HP_GOOD)
        end
    end
end

local function draw_bottom(fb, sim, p, message)
    for y = C.BAR_Y, C.SCR_H - 1 do
        local row = y * C.SCR_W
        for x = 0, C.PANEL_X - 1 do
            fb[row + x] = UI_MID
        end
    end
    RS.text(fb, 'CREDITS' .. credits_text(sim.ec.credits[p]), 4, C.BAR_Y + 2,
            UI_TEXT)
    RS.text(fb, 'POP' .. credits_text(sim.ec.supply_used[p])
            .. '/' .. credits_text(sim.ec.supply_cap[p]), 4, C.BAR_Y + 12,
            UI_TEXT)
    if message ~= nil and message ~= '' then
        RS.text(fb, utf8_head(message, 24), 130, C.BAR_Y + 12, UI_LIGHT)
    end
end

M._draw_terrain = draw_terrain
M._draw_entities = draw_entities
M._draw_projectiles = draw_projectiles
M._draw_panel = draw_panel
M._draw_bottom = draw_bottom

--- §23.1 의 여덟 층을 순서대로. 팔레트 위상은 그림을 바꾸지 않는다.
function M.draw(fb, sim, view, phase, pal, light, p, selection, message)
    draw_terrain(fb, sim, view, light, p)
    draw_entities(fb, sim, view, light, p, selection)
    draw_projectiles(fb, sim, view)
    draw_panel(fb, sim, view, p, selection)
    draw_bottom(fb, sim, p, message)
end

return M
