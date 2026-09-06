-- 지형 맵 — 한 칸 두 바이트, 오토타일, 연결 성분, RLE (SPEC §4).
--
--    맵은 두 평면으로 나뉜다. 한 배열에 비트로 우겨 넣지 않는다.
--      terrain[i]  지형 종류
--      pass_[i]    통행 비트 — 지형에서 파생되지만 건물이 서면 달라지므로 별도 상태다
--
--    비트마스크는 전부 산술로 다룬다(SPEC §1.1). 루아 5.1 에 비트 연산자가 없고,
--    타입스크립트의 & 는 32비트로 잘린다. 오토타일 마스크는 8비트뿐이라 잘릴 일이
--    없어 보이지만, 규칙을 한 군데서만 어기면 반드시 다른 곳에서 샌다.

local F = require('rts.fixed')

local M = {}
local floor = math.floor

-- ── SPEC §4.1 지형표 ────────────────────────────────────────────────────────
M.SAND, M.ROCK, M.WATER, M.DIRT = 0, 1, 2, 3
M.ORE, M.HILL, M.RUBBLE, M.ROAD = 4, 5, 6, 7
local SAND, ROCK = 0, 1

M.TERRAIN_CH = '.#~,*^;='
M.TERRAIN_NAME = {[0] = '모래', '바위', '물', '흙', '광맥', '언덕', '잔해', '도로',
                  n = 8}
M.MINI_COLOR = {[0] = 216, 220, 232, 214, 240, 218, 222, 226, n = 8}

-- 보병 통행 · 차량 통행 · 건설 가능
M.FOOT_OK = {[0] = 1, 0, 0, 1, 1, 1, 1, 1, n = 8}
M.VEHICLE_OK = {[0] = 1, 0, 0, 1, 1, 0, 1, 1, n = 8}   -- 차량은 언덕에 못 오른다
M.BUILD_OK = {[0] = 1, 0, 0, 1, 0, 0, 1, 1, n = 8}
local FOOT_OK, VEHICLE_OK, BUILD_OK = M.FOOT_OK, M.VEHICLE_OK, M.BUILD_OK

M.FOOT_BIT, M.VEH_BIT, M.BUILD_BIT, M.OCC_BIT = 0, 1, 2, 3
local OCC_BIT = 3

-- 통행 비트는 0..15 의 작은 음이 아닌 정수뿐이므로 나눗셈 한 번이면 충분하다.
-- (일반형 F.bit 은 음수까지 다루느라 보정 루프가 붙어 있다 — 여기선 낭비다.)
local POW2 = {[0] = 1, 2, 4, 8, 16, 32, 64, 128}
local function pbit(v, k)
    return floor(v / POW2[k]) % 2
end

-- ── SPEC §4.4 오토타일 ──────────────────────────────────────────────────────
-- (모서리 방향, 양옆 변 방향 둘). 방향 번호는 fixed.DX/DY 와 같다.
local CORNERS = {{1, 0, 2}, {3, 4, 2}, {5, 4, 6}, {7, 0, 6}}

--- 모서리 비트는 양옆 변이 둘 다 있을 때만 살린다 (SPEC 정리 4.1).
local function canon(m)
    local r = m
    for i = 1, 4 do
        local c, a, b = CORNERS[i][1], CORNERS[i][2], CORNERS[i][3]
        if not (pbit(m, a) == 1 and pbit(m, b) == 1) then
            r = r - pbit(r, c) * POW2[c]
        end
    end
    return r
end
M.canon = canon

-- 정규화된 마스크의 오름차순 목록과 역인덱스. 파이썬의 sorted(set(...)) 과
-- 같은 순서여야 그림 번호가 골든과 맞는다.
local CLASSES = {}
local CLASS_INDEX = {}
do
    local seen = {}
    for m = 0, 255 do
        local c = canon(m)
        if not seen[c] then
            seen[c] = true
            CLASSES[#CLASSES + 1] = c
        end
    end
    table.sort(CLASSES)
    for i = 1, #CLASSES do
        CLASS_INDEX[CLASSES[i]] = i - 1
    end
end
M.CLASS_COUNT = #CLASSES
M.CLASSES = CLASSES

--- 정규화된 마스크 → 0..46 그림 번호.
function M.canon_index(cm)
    return CLASS_INDEX[cm]
end

--- 4모서리(마칭 스퀘어) 16케이스. v = [좌상, 우상, 우하, 좌하] 의 0/1.
function M.corner_mask(v)
    return v[0] + 2 * v[1] + 4 * v[2] + 8 * v[3]
end

-- ── TMap ────────────────────────────────────────────────────────────────────
local TMap = {}
TMap.__index = TMap
M.TMap = TMap

function M.new(w, h)
    local self = setmetatable({}, TMap)
    self.w = w
    self.h = h
    local n = w * h
    self.terrain = {n = n}
    self.pass_ = {n = n}
    for i = 0, n - 1 do
        self.terrain[i] = SAND
        self.pass_[i] = 0
    end
    self.version = 0
    self.starts = {n = 0}
    self.pairs = {n = 0}
    self._labels = {}
    for i = 0, n - 1 do
        self:_repass(i)
    end
    return self
end
TMap.new = M.new

-- ── SPEC §4.2 좌표 ──────────────────────────────────────────────────────────
function TMap:idx(x, y)
    return y * self.w + x
end

function TMap:in_map(x, y)
    return x >= 0 and x < self.w and y >= 0 and y < self.h
end

--- 맵 밖은 ROCK 이다 — 호출자가 경계 검사를 하지 않아도 되고, 오토타일 마스크가
--- 가장자리에서 자연스럽게 닫힌다.
function TMap:terrain_at(x, y)
    if x < 0 or x >= self.w or y < 0 or y >= self.h then
        return ROCK
    end
    return self.terrain[y * self.w + x]
end

-- ── SPEC §4.3 통행 비트 ─────────────────────────────────────────────────────
function TMap:_repass(i)
    local t = self.terrain[i]
    local occ = pbit(self.pass_[i], OCC_BIT)
    self.pass_[i] = FOOT_OK[t] + 2 * VEHICLE_OK[t] + 4 * BUILD_OK[t] + 8 * occ
end

function TMap:set_terrain(x, y, t)
    local i = y * self.w + x
    if self.terrain[i] == t then
        return
    end
    self.terrain[i] = t
    self:_repass(i)
    self:_bump()
end

function TMap:occupy(x, y, on)
    local i = y * self.w + x
    local p = self.pass_[i]
    if on then
        self.pass_[i] = p + (1 - pbit(p, OCC_BIT)) * 8
    else
        self.pass_[i] = p - pbit(p, OCC_BIT) * 8
    end
end

--- 건물이 선 칸 — 통행 비트를 내리고 점유 비트를 세운다 (SPEC §4.3).
--
--    유닛과 달리 건물은 비키지 않는다. 예약(§13.2)만으로 막으면 유닛이 건물을
--    향해 24틱을 두드리다 포기하므로, 경로 그래프에서 아예 뺀다. `version` 이
--    오르니 경로 캐시와 연결 성분이 함께 무효가 된다.
function TMap:set_building(x, y, on)
    local i = y * self.w + x
    if on then
        self.pass_[i] = 8                          -- 점유 비트만 남긴다
    else
        self:_repass(i)
        self.pass_[i] = self.pass_[i] - pbit(self.pass_[i], OCC_BIT) * 8
    end
    self:_bump()
end

function TMap:walkable(x, y, kind)
    if x < 0 or x >= self.w or y < 0 or y >= self.h then
        return false
    end
    local p = self.pass_[y * self.w + x]
    return pbit(p, kind) == 1 and pbit(p, OCC_BIT) == 0
end

--- 점유를 보지 않는 통행 판정 — 경로 탐색은 이것을 쓴다(SPEC §4.3).
function TMap:passable_terrain(x, y, kind)
    if x < 0 or x >= self.w or y < 0 or y >= self.h then
        return false
    end
    return pbit(self.pass_[y * self.w + x], kind) == 1
end

function TMap:buildable(x, y)
    if x < 0 or x >= self.w or y < 0 or y >= self.h then
        return false
    end
    local p = self.pass_[y * self.w + x]
    return pbit(p, 2) == 1 and pbit(p, OCC_BIT) == 0
end

function TMap:_bump()
    self.version = self.version + 1
    self._labels = {}
end

-- ── SPEC §4.4 이웃 마스크 ───────────────────────────────────────────────────

--- 이웃 8칸 중 나와 같은 지형인 방향의 비트합.
function TMap:mask(x, y)
    local t = self:terrain_at(x, y)
    local m = 0
    for d = 0, 7 do
        if self:terrain_at(x + F.DX[d], y + F.DY[d]) == t then
            m = m + (1 - pbit(m, d)) * POW2[d]
        end
    end
    return m
end

function TMap:tile_index(x, y)
    return CLASS_INDEX[canon(self:mask(x, y))]
end

-- ── SPEC §4.6 연결 성분 (유니온–파인드) ─────────────────────────────────────

--- 통행 가능 칸을 8방향으로 묶은 대표 원소 배열. 막힌 칸은 -1.
--
--    지형이 바뀌면 통째로 다시 계산한다. 증분 삭제가 되는 유니온–파인드는
--    복잡하고, 4096칸 재계산은 측정상 1 ms 미만이다.
function TMap:labels(kind)
    local cached = self._labels[kind]
    if cached then return cached end
    local w, h = self.w, self.h
    local n = w * h
    local parent = {}
    for i = 0, n - 1 do parent[i] = i end

    local function find(a)
        local root = a
        while parent[root] ~= root do
            root = parent[root]
        end
        while parent[a] ~= root do                 -- 경로 압축
            local nxt = parent[a]
            parent[a] = root
            a = nxt
        end
        return root
    end

    for y = 0, h - 1 do
        for x = 0, w - 1 do
            if self:passable_terrain(x, y, kind) then
                local a = find(y * w + x)
                for d = 0, 7 do
                    local u, v = x + F.DX[d], y + F.DY[d]
                    if self:passable_terrain(u, v, kind) then
                        local b = find(v * w + u)
                        if a ~= b then
                            parent[b] = a
                            a = find(a)
                        end
                    end
                end
            end
        end
    end
    local out = {n = n}
    for i = 0, n - 1 do out[i] = -1 end
    for y = 0, h - 1 do
        for x = 0, w - 1 do
            if self:passable_terrain(x, y, kind) then
                out[y * w + x] = find(y * w + x)
            end
        end
    end
    self._labels[kind] = out
    return out
end

-- ── SPEC §4.7 RLE ───────────────────────────────────────────────────────────
function TMap:save_rle()
    local body = {}
    local function push(b) body[#body + 1] = string.char(b) end
    body[#body + 1] = 'RTSM'
    push(1)
    push(self.w)
    push(self.h)
    for _, plane in ipairs({self.terrain, self.pass_}) do
        local run, val = 0, -1
        for i = 0, plane.n - 1 do
            local v = plane[i]
            if v == val and run < 255 then
                run = run + 1
            else
                if run ~= 0 then
                    push(run)
                    push(val)
                end
                run, val = 1, v
            end
        end
        if run ~= 0 then
            push(run)
            push(val)
        end
    end
    local blob = table.concat(body)
    local c = F.crc16(blob)
    return blob .. string.char(floor(c / 256)) .. string.char(c % 256)
end

function M.load_rle(blob)
    if blob:sub(1, 4) ~= 'RTSM' then
        error('맵 파일이 아니다')
    end
    local n = #blob
    local want = blob:byte(n - 1) * 256 + blob:byte(n)
    if F.crc16(blob:sub(1, n - 2)) ~= want then
        error('CRC 불일치 — 맵이 깨졌다')
    end
    local w, h = blob:byte(6), blob:byte(7)
    local m = M.new(w, h)
    local pos = 8                                  -- 파이썬 pos=7 의 1-기반
    for _, plane in ipairs({m.terrain, m.pass_}) do
        local i = 0
        while i < w * h do
            local run, val = blob:byte(pos), blob:byte(pos + 1)
            pos = pos + 2
            for _ = 1, run do
                plane[i] = val
                i = i + 1
            end
        end
    end
    m:_bump()
    return m
end
TMap.load_rle = M.load_rle

-- ── 골든 맵 텍스트 (시험용) ─────────────────────────────────────────────────

--- golden/map_*.txt 를 읽는다. '.'/'#' 격자와 지형 문자 격자 둘 다.
function M.load_text(text)
    local lines = {n = 0}
    local start = 1
    while true do
        local p = text:find('\n', start, true)
        if not p then
            lines[lines.n] = text:sub(start); lines.n = lines.n + 1
            break
        end
        lines[lines.n] = text:sub(start, p - 1); lines.n = lines.n + 1
        start = p + 1
    end
    local w, h = 0, 0
    local m = nil
    local i = 0
    while i < lines.n do
        local ln = lines[i]
        if ln:sub(1, 5) == 'size ' then
            local a, b = ln:match('^size%s+(%-?%d+)%s+(%-?%d+)')
            w, h = tonumber(a), tonumber(b)
        elseif ln == 'map' or ln == 'terrain' then
            m = M.new(w, h)
            for y = 0, h - 1 do
                local row = lines[i + 1 + y]
                for x = 0, w - 1 do
                    local ch = row:sub(x + 1, x + 1)
                    if ln == 'map' then
                        m.terrain[y * w + x] = (ch == '#') and 1 or 3
                    else
                        m.terrain[y * w + x] = M.TERRAIN_CH:find(ch, 1, true) - 1
                    end
                    m:_repass(y * w + x)
                end
            end
            i = i + h
        elseif ln:sub(1, 6) == 'pairs ' then
            local cnt = tonumber(ln:sub(7))
            for k = 0, cnt - 1 do
                local v = {n = 0}
                for tok in lines[i + 1 + k]:gmatch('%-?%d+') do
                    v[v.n] = tonumber(tok); v.n = v.n + 1
                end
                m.pairs[m.pairs.n] = {[0] = {[0] = v[0], [1] = v[1], n = 2},
                                      [1] = {[0] = v[2], [1] = v[3], n = 2},
                                      n = 2}
                m.pairs.n = m.pairs.n + 1
            end
            i = i + cnt
        elseif ln:sub(1, 6) == 'start ' then
            local cnt = tonumber(ln:sub(7))
            for k = 0, cnt - 1 do
                local v = {n = 0}
                for tok in lines[i + 1 + k]:gmatch('%-?%d+') do
                    v[v.n] = tonumber(tok); v.n = v.n + 1
                end
                m.starts[m.starts.n] = {[0] = v[0], [1] = v[1], n = 2}
                m.starts.n = m.starts.n + 1
            end
            i = i + cnt
        end
        i = i + 1
    end
    m:_bump()
    return m
end
TMap.load_text = M.load_text

return M
