-- 래스터 — 프레임버퍼·팔레트·스프라이트·블릿·폰트·PPM (SPEC §22).
--
--    세 언어 모두 프레임버퍼가 **1차원 정수 배열**이다. 이것이 세 구현을 바이트
--    단위로 비교 가능하게 만드는 유일한 이유다. 프런트엔드는 이 배열에 팔레트로
--    색을 입혀 화면에 올릴 뿐이고, `make parity` 는 192,015바이트짜리 PPM 을
--    `cmp` 한다.
--
--    팔레트와 스프라이트는 정수식으로 만든다(§22.2·§22.3). 표를 세 언어에 옮겨
--    적는 대신 같은 식을 세 번 쓰고, 결과를 골든과 대조한다.

local CI = require('rts.circle')
local C = require('rts.const')
local F = require('rts.fixed')

local M = {}
local floor = math.floor

M.PLAYER_BASE = 160
M.PLAYER_SHADES = 8
M.SHADOW = 251
M.WATER_BASE, M.WATER_N = 232, 8
M.DRAWN_DIRS = 5                 -- §22.7 그린 방향 수 (나머지 셋은 좌우 반전)
local PLAYER_BASE, PLAYER_SHADES, SHADOW = 160, 8, 251
local WATER_BASE, WATER_N, DRAWN_DIRS = 232, 8, 5

M.UNIT_R = {[0] = 5, 4, 6, 5, 5}
M.UNIT_M = {[0] = 3, 3, 4, 3, 3}
M.UNIT_NAME = {[0] = 'INF', 'ARCHER', 'TANK', 'MORTAR', 'HARV'}
M.BLD_NAME = {[0] = {C.HQ, 'HQ'}, {C.REF, 'REF'}, {C.BARR, 'BARR'},
              {C.FACT, 'FACT'}, {C.POW, 'POW'}, {C.TOWER, 'TOWER'}, n = 6}
local UNIT_R, UNIT_M, UNIT_NAME, BLD_NAME =
    M.UNIT_R, M.UNIT_M, M.UNIT_NAME, M.BLD_NAME

local EGA = {[0] = {0, 0, 42}, {0, 42, 0}, {0, 42, 42}, {42, 0, 0}, {42, 0, 42},
             {42, 21, 0}, {42, 42, 42}, {21, 21, 21}, {21, 21, 63},
             {21, 63, 21}, {21, 63, 63}, {63, 21, 21}, {63, 21, 63},
             {63, 63, 21}, {63, 63, 63}}
local PLAYER_RAMP = {[0] = {{16, 4, 4}, {63, 26, 26}},
                     {{4, 8, 20}, {26, 38, 63}},
                     {{4, 18, 6}, {26, 56, 26}},
                     {{20, 16, 4}, {63, 58, 20}}}
local TERRAIN_RAMP = {[0] = {{24, 14, 6}, {46, 34, 18}},
                      {{44, 40, 26}, {18, 18, 20}},
                      {{20, 20, 22}, {40, 40, 42}},
                      {{6, 10, 30}, {22, 34, 54}},
                      {{40, 32, 4}, {63, 58, 26}},
                      {{0, 0, 0}, {30, 30, 30}}}
local UI = {[0] = {0, 0, 0}, {10, 10, 12}, {20, 20, 24}, {30, 30, 34},
            {42, 42, 46}, {52, 52, 56}, {63, 63, 63}, {63, 52, 20},
            {52, 20, 20}, {20, 52, 20}, {20, 20, 52}, {40, 40, 10},
            {30, 8, 8}, {8, 30, 8}, {8, 8, 30}, {32, 32, 32}}
M.EGA, M.PLAYER_RAMP, M.TERRAIN_RAMP, M.UI = EGA, PLAYER_RAMP, TERRAIN_RAMP, UI

local FONT_HEX =
    '000000000000000008080808080008000000000000000000143e14143e14000000000000'
    .. '000000003234081026060000000000000000000000000000000000000408101010080400'
    .. '100804040408100000000000000000000008083e0808000000000000181810000000003e'
    .. '00000000000000000018180002020408102020001c22262a32221c000818080808081c00'
    .. '1c22020408103e003c02021c02023c00040c14243e0404003e203c0202221c000c10203c'
    .. '22221c003e020408101010001c22221c22221c001c22221e020418000018180018180000'
    .. '00000000000000000000000000000000000000000000000000000000000000001c220204'
    .. '0800080000000000000000001c22223e222222003c22223c22223c001c22202020221c00'
    .. '3c22222222223c003e20203c20203e003e20203c202020001c22202e22221c002222223e'
    .. '222222001c08080808081c000e0404040424180022242830282422002020202020203e00'
    .. '22362a2a2222220022322a2a262222001c22222222221c003c22223c202020001c222222'
    .. '2a241a003c22223c282422001e20201c02023c003e080808080808002222222222221c00'
    .. '22222222221408002222222a2a362200222214081422220022221408080808003e020408'
    .. '10203e000000000000000000000000000000000000000000000000000000000000000000'
    .. '000000000000000000000000000000000000000000000000000000000000000000000000'
    .. '000000000000000000000000000000000000000000000000000000000000000000000000'
    .. '000000000000000000000000000000000000000000000000000000000000000000000000'
    .. '000000000000000000000000000000000000000000000000000000000000000000000000'
    .. '000000000000000000000000000000000000000000000000000000000000000000000000'
    .. '000000000000000000000000000000000000000000000000000000000000000000000000'
    .. '000000000000000000000000000000000000000000000000000000000000000000000000'
    .. '00000000'
local FONT = {n = floor(#FONT_HEX / 2)}
for k = 0, FONT.n - 1 do
    FONT[k] = tonumber(FONT_HEX:sub(k * 2 + 1, k * 2 + 2), 16)
end
M.FONT = FONT
M.FONT_W, M.FONT_H, M.FONT_ADV = 6, 8, 6
M.FONT_FIRST = 32
local FONT_W, FONT_H, FONT_ADV, FONT_FIRST = 6, 8, 6, 32

-- ── SPEC §22.2 팔레트 ───────────────────────────────────────────────────────

--- 두 끝색 사이의 정수 보간. 나눗셈은 내림이다.
function M.ramp(c0, c1, i)
    return {c0[1] + F.floordiv((c1[1] - c0[1]) * i, 7),
            c0[2] + F.floordiv((c1[2] - c0[2]) * i, 7),
            c0[3] + F.floordiv((c1[3] - c0[3]) * i, 7)}
end
local ramp = M.ramp

function M.build_palette()
    local pal = {n = 256}
    for k = 0, 255 do pal[k] = {0, 0, 0} end
    for k = 0, 14 do pal[1 + k] = EGA[k] end
    for i = 0, 15 do
        local g = F.floordiv(i * 63, 15)
        pal[16 + i] = {g, g, g}
    end
    for p = 0, 3 do
        local c0, c1 = PLAYER_RAMP[p][1], PLAYER_RAMP[p][2]
        for i = 0, PLAYER_SHADES - 1 do
            pal[PLAYER_BASE + p * PLAYER_SHADES + i] = ramp(c0, c1, i)
        end
    end
    for i = 0, 15 do pal[192 + i] = UI[i] end
    for r = 0, 5 do
        local c0, c1 = TERRAIN_RAMP[r][1], TERRAIN_RAMP[r][2]
        for i = 0, 7 do
            pal[208 + r * 8 + i] = ramp(c0, c1, i)
        end
    end
    return pal
end

--- 명암 단계 l 에서 색 c 에 가장 가까운 항목. 동점이면 인덱스 최소.
--
--    256 × 256 × 4 = 262,144회 비교이며 **시작할 때 한 번**이다. 안개(§14.4)가
--    이 표를 쓴다 — 안개 때문에 색 계산을 하지 않으려고 표로 미리 굳힌다.
function M.build_light(pal)
    local out = {n = 4}
    for l = 0, 3 do
        local row = {n = 256}
        for c = 0, 255 do
            local wr = F.floordiv(pal[c][1] * l, 3)
            local wg = F.floordiv(pal[c][2] * l, 3)
            local wb = F.floordiv(pal[c][3] * l, 3)
            local best, bd = 0, -1
            for j = 0, 255 do
                local dr = pal[j][1] - wr
                local dg = pal[j][2] - wg
                local db = pal[j][3] - wb
                local d = dr * dr + dg * dg + db * db
                if bd < 0 or d < bd then
                    bd, best = d, j
                end
            end
            row[c] = best
        end
        out[l] = row
    end
    return out
end

-- ── SPEC §22.6 팔레트 사이클링 ──────────────────────────────────────────────

--- 물 색 8칸을 한 칸씩 돌린다. **프레임버퍼는 건드리지 않는다** — 팔레트 모드의
--- 가장 큰 장점이었던 공짜 애니메이션이다.
function M.cycle_water(pal, phase)
    local out = {n = pal.n}
    for k = 0, pal.n - 1 do out[k] = pal[k] end
    for i = 0, WATER_N - 1 do
        out[WATER_BASE + i] = pal[WATER_BASE + (i + phase) % WATER_N]
    end
    return out
end

-- ── SPEC §22.3 스프라이트 ───────────────────────────────────────────────────
local Sprite = {}
Sprite.__index = Sprite
M.Sprite = Sprite

function M.newsprite(w, h, ox, oy, data)
    return setmetatable({w = w, h = h, ox = ox, oy = oy, data = data}, Sprite)
end

function Sprite:pixels()
    local out = {n = 0}
    local d = self.data
    local i = 1
    while i <= #d do
        local run, val = d:byte(i), d:byte(i + 1)
        for _ = 1, run do
            out[out.n] = val
            out.n = out.n + 1
        end
        i = i + 2
    end
    return out
end

local function rle(px)
    local out = {}
    local i = 0
    while i < px.n do
        local v = px[i]
        local run = 1
        while i + run < px.n and px[i + run] == v and run < 255 do
            run = run + 1
        end
        out[#out + 1] = string.char(run)
        out[#out + 1] = string.char(v)
        i = i + run
    end
    return table.concat(out)
end

--- §6.2 의 행 span 으로 원을 채운다 — 곱셈도 제곱근도 쓰지 않는다.
local function disc(px, w, cx, cy, r, colour, only_below, only_empty)
    local sp = CI.spans(r)
    local rows = floor(px.n / w)
    for dy = -r, r do
        if not (only_below and dy < 0) then
            local wdt = sp[dy >= 0 and dy or -dy]
            local y = cy + dy
            for dx = -wdt, wdt do
                local x = cx + dx
                if x >= 0 and x < w and y >= 0 and y < rows then
                    if not (only_empty and px[y * w + x] ~= 0) then
                        px[y * w + x] = colour
                    end
                end
            end
        end
    end
end

function M.unit_sprite(k, d)
    local w, h = C.TILE, C.TILE
    local px = {n = w * h}
    for i = 0, w * h - 1 do px[i] = 0 end
    local r = UNIT_R[k]
    disc(px, w, 8, 9, r, PLAYER_BASE + 1)           -- 테두리
    disc(px, w, 8, 9, r - 1, PLAYER_BASE + 3)       -- 속
    disc(px, w, 8, 14, 3, SHADOW, true, true)       -- 그림자 (아래 절반, 빈 곳만)
    local mx, my = 8 + F.DX[d] * UNIT_M[k], 9 + F.DY[d] * UNIT_M[k]
    for y = my, my + 1 do
        for x = mx, mx + 1 do
            if x >= 0 and x < w and y >= 0 and y < h then
                px[y * w + x] = PLAYER_BASE + 6      -- 방향 표시
            end
        end
    end
    return M.newsprite(w, h, 8, 14, rle(px))
end

function M.building_sprite(foot)
    local w, h = C.TILE * foot, C.TILE * foot
    local px = {n = w * h}
    for i = 0, w * h - 1 do px[i] = 0 end
    for y = 4, h - 3 do
        for x = 2, w - 3 do
            local edge = (x == 2 or x == w - 3 or y == 4 or y == h - 3)
            px[y * w + x] = PLAYER_BASE + (edge and 5 or 2)
        end
    end
    for y = 4, 6 do
        for x = 2, w - 3 do
            px[y * w + x] = PLAYER_BASE + 6          -- 지붕
        end
    end
    for y = h - 6, h - 3 do
        for x = floor(w / 2) - 2, floor(w / 2) + 1 do
            px[y * w + x] = PLAYER_BASE              -- 문
        end
    end
    return M.newsprite(w, h, floor(w / 2), h - 2, rle(px))
end

local SPRITES = {}
for k = 0, 4 do
    for d = 0, DRAWN_DIRS - 1 do
        SPRITES[UNIT_NAME[k] .. '_' .. d] = M.unit_sprite(k, d)
    end
end
for k = 0, BLD_NAME.n - 1 do
    SPRITES[BLD_NAME[k][2]] = M.building_sprite(C.FOOT[BLD_NAME[k][1]])
end
M.SPRITES = SPRITES

--- §22.7 — 그린 것은 5방향뿐이다. (스프라이트, 반전 여부).
function M.sprite_for(kind, d)
    if C.IS_BUILDING[kind] ~= 0 then
        for k = 0, BLD_NAME.n - 1 do
            if BLD_NAME[k][1] == kind then
                return SPRITES[BLD_NAME[k][2]], false
            end
        end
        return nil, false
    end
    if d <= 4 then
        return SPRITES[UNIT_NAME[kind] .. '_' .. d], false
    end
    return SPRITES[UNIT_NAME[kind] .. '_' .. (8 - d)], true
end

-- ── SPEC §22.1 프레임버퍼 ───────────────────────────────────────────────────
local Frame = {}
Frame.__index = Frame
M.Frame = Frame

function M.newframe(w, h)
    w = w or C.SCR_W
    h = h or C.SCR_H
    local self = setmetatable({w = w, h = h}, Frame)
    self.fb = {n = w * h}
    for i = 0, w * h - 1 do self.fb[i] = 0 end
    return self
end

function Frame:clear(v)
    v = v or 0
    for i = 0, self.fb.n - 1 do self.fb[i] = v end
end

function Frame:rect(x, y, w, h, v)
    local y0 = y > 0 and y or 0
    local y1 = (y + h) < self.h and (y + h) or self.h
    local x0 = x > 0 and x or 0
    local x1 = (x + w) < self.w and (x + w) or self.w
    for j = y0, y1 - 1 do
        local row = j * self.w
        for i = x0, x1 - 1 do
            self.fb[row + i] = v
        end
    end
end

-- ── SPEC §22.4 클리핑 블릿 ──────────────────────────────────────────────────

--- 런 단위로 자른다 — 픽셀마다 경계를 검사하지 않는다 (정리 22.1).
--- 완전히 화면 밖이면 런을 하나도 훑지 않고 돌아간다.
function M.blit(fb, spr, x, y, owner, flip, light, level)
    owner = owner or 0
    if level == nil then level = 3 end
    -- 반전해도 상자 자체는 그대로 두고 상자 **안에서** 뒤집는다. 기준점은
    -- (w - 1 - 2*ox) 픽셀만큼 옮겨지는데(폭 16·ox 8 이면 1px), 세 언어가
    -- 같은 자리에 그리는 것이 그 1px 보다 중요하다.
    local x0 = x - spr.ox
    local y0 = y - spr.oy
    if x0 + spr.w <= 0 or x0 >= C.SCR_W or y0 + spr.h <= 0 or y0 >= C.SCR_H then
        return
    end
    local add = owner * PLAYER_SHADES
    local d = spr.data
    local i = 1
    local pos = 0
    while i <= #d do
        local run, val = d:byte(i), d:byte(i + 1)
        i = i + 2
        if val == 0 then                              -- 컬러키 — 통째로 건너뛴다
            pos = pos + run
        else
            local colour = val
            if val >= PLAYER_BASE and val < PLAYER_BASE + PLAYER_SHADES then
                colour = val + add
            end
            if light ~= nil and level < 3 then
                colour = light[level][colour]
            end
            local p = pos
            local e = pos + run
            while p < e do
                local sy = floor(p / spr.w)
                local sx = p % spr.w
                local n = e - p
                if n > spr.w - sx then
                    n = spr.w - sx                    -- 이 줄에 걸치는 만큼만
                end
                local fy = y0 + sy
                if fy >= 0 and fy < C.SCR_H then
                    local fx
                    if flip then
                        fx = x0 + (spr.w - 1 - (sx + n - 1))
                    else
                        fx = x0 + sx
                    end
                    local a = fx > 0 and fx or 0
                    local b = fx + n
                    if b > C.SCR_W then b = C.SCR_W end
                    local row = fy * C.SCR_W
                    for q = a, b - 1 do
                        fb[row + q] = colour
                    end
                end
                p = p + n
            end
            pos = e
        end
    end
end

-- ── SPEC §22.8 폰트 ─────────────────────────────────────────────────────────

--- UTF-8 문자열을 코드포인트 배열로. 파이썬의 `for ch in s` 와 같은 단위로
--- 돌기 위해서다 — 한글 한 글자가 세 바이트라고 세 칸을 밀면 안 된다.
local function codepoints(s)
    local out = {n = 0}
    local i = 1
    while i <= #s do
        local b = s:byte(i)
        local cp, len
        if b < 0x80 then
            cp, len = b, 1
        elseif b < 0xE0 then
            cp, len = (b - 0xC0) * 64 + (s:byte(i + 1) - 0x80), 2
        elseif b < 0xF0 then
            cp = (b - 0xE0) * 4096 + (s:byte(i + 1) - 0x80) * 64
                 + (s:byte(i + 2) - 0x80)
            len = 3
        else
            cp = (b - 0xF0) * 262144 + (s:byte(i + 1) - 0x80) * 4096
                 + (s:byte(i + 2) - 0x80) * 64 + (s:byte(i + 3) - 0x80)
            len = 4
        end
        out[out.n] = cp
        out.n = out.n + 1
        i = i + len
    end
    return out
end
M.codepoints = codepoints

--- 6×8 칸에 5×7 획. 소문자는 빈 글자다(§22.8).
function M.text(fb, s, x, y, colour)
    local cps = codepoints(s)
    for k = 0, cps.n - 1 do
        local code = cps[k]
        if code >= FONT_FIRST and code < FONT_FIRST + 95 then
            local base = (code - FONT_FIRST) * FONT_H
            for j = 0, FONT_H - 1 do
                local v = FONT[base + j]
                local fy = y + j
                if fy >= 0 and fy < C.SCR_H then
                    for q = 0, FONT_W - 1 do
                        if floor(v / 2 ^ (5 - q)) % 2 == 1 then
                            local fx = x + q
                            if fx >= 0 and fx < C.SCR_W then
                                fb[fy * C.SCR_W + fx] = colour
                            end
                        end
                    end
                end
            end
        end
        x = x + FONT_ADV
    end
end

-- ── SPEC §22.9 더티 렉트 ────────────────────────────────────────────────────

--- 8개를 넘으면 전체를 다시 그린다 — 합치는 비용이 이득을 넘는 지점이다.
local Dirty = {}
Dirty.__index = Dirty
M.Dirty = Dirty
Dirty.MAX = 8

function M.newdirty()
    return setmetatable({_r = {n = 0}}, Dirty)
end

function Dirty:add(x, y, w, h)
    self._r[self._r.n] = {[0] = x, y, w, h, n = 4}
    self._r.n = self._r.n + 1
end

function Dirty:rects()
    if self._r.n > Dirty.MAX then
        return {[0] = {[0] = 0, 0, C.SCR_W, C.SCR_H, n = 4}, n = 1}
    end
    local out = {n = self._r.n}
    for k = 0, self._r.n - 1 do out[k] = self._r[k] end
    return out
end

function Dirty:clear()
    self._r = {n = 0}
end

-- ── SPEC §22.10 PPM ─────────────────────────────────────────────────────────

--- 0…63 을 0…255 로. v*255/63 이 아니라 곱셈·나눗셈 하나씩이다.
function M.expand(v)
    return v * 4 + F.floordiv(v, 16)
end

function M.to_ppm(fb, pal)
    local head = 'P6\n' .. C.SCR_W .. ' ' .. C.SCR_H .. '\n255\n'
    local lut = {}
    for c = 0, pal.n - 1 do
        lut[c * 3 + 1] = string.char(M.expand(pal[c][1]))
        lut[c * 3 + 2] = string.char(M.expand(pal[c][2]))
        lut[c * 3 + 3] = string.char(M.expand(pal[c][3]))
    end
    local out = {}
    for i = 0, fb.n - 1 do
        local j = fb[i] * 3
        out[i + 1] = lut[j + 1] .. lut[j + 2] .. lut[j + 3]
    end
    return head .. table.concat(out)
end

return M
