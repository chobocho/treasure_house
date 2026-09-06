-- 경로 탐색 — BFS·다익스트라(양동이 큐)·A*(이진 힙) (SPEC §8).
--
--    코너 컷은 **허용한다**. 대각 이동은 도착 칸만 본다. 선택이며, 그 이유와
--    대가는 SPEC §8.1 에 적어 두었다 — 요약하면 JPS 의 가지치기 규칙이
--    코너 컷 격자 위에서 정의되어 있기 때문이다.
--
--    경로 탐색은 점유 비트를 보지 않는다(SPEC §4.3). 움직이는 유닛 때문에
--    경로가 매 틱 흔들리면 무리 이동이 통째로 무너진다.

local F = require('rts.fixed')

local M = {}
local floor = math.floor

M.INF = 1073741824                -- 1 << 30
local INF = 1073741824
M.NB = 15                         -- 양동이 15개 — 최대 간선 비용보다 커야 한다
local NB = 15

local DX, DY, DCOST = F.DX, F.DY, F.DCOST

--- 옥타일 휴리스틱 = 10*max + 4*min. 허용적이고 일관적이다 (SPEC 정리 8.1/8.2).
function M.h_oct(ax, ay, bx, by)
    return F.doct(ax - bx, ay - by)
end
local h_oct = M.h_oct

--- (방향, u, v) 들을 0-기반 배열로. 코너 컷 허용이므로 도착 칸만 검사한다.
--- 파이썬은 제너레이터지만 루아 5.1 의 코루틴은 느리므로 배열을 돌려준다 —
--- 순서는 방향 번호 오름차순으로 같다.
function M.neighbours(m, x, y, kind)
    local out = {n = 0}
    for d = 0, 7 do
        local u, v = x + DX[d], y + DY[d]
        if m:passable_terrain(u, v, kind) then
            out[out.n] = {d, u, v}
            out.n = out.n + 1
        end
    end
    return out
end

-- ── BFS ─────────────────────────────────────────────────────────────────────

--- 걸음 수(가중치 없음). 대각도 한 걸음이다.
function M.bfs(m, kind, s, t)
    if not (m:passable_terrain(s[0], s[1], kind)
            and m:passable_terrain(t[0], t[1], kind)) then
        return -1
    end
    local w = m.w
    local seen = {}
    for i = 0, w * m.h - 1 do seen[i] = -1 end
    local si = s[1] * w + s[0]
    seen[si] = 0
    local q = {[1] = si}
    local head = 1
    local qn = 1
    while head <= qn do
        local p = q[head]
        head = head + 1
        local x, y = p % w, floor(p / w)
        if x == t[0] and y == t[1] then
            return seen[p]
        end
        for d = 0, 7 do
            local u, v = x + DX[d], y + DY[d]
            if m:passable_terrain(u, v, kind) then
                local j = v * w + u
                if seen[j] < 0 then
                    seen[j] = seen[p] + 1
                    qn = qn + 1
                    q[qn] = j
                end
            end
        end
    end
    return -1
end

-- ── SPEC §8.4 다익스트라 (Dial 양동이 큐) ───────────────────────────────────

--- 모든 칸까지의 비용 배열. 간선 비용이 10 과 14 뿐이라 힙이 필요 없다.
--
--    정리 8.3 이 보장한다 — 처리 중인 거리 cur 와 새 거리 nd 는 항상
--    cur <= nd < cur + 15 이므로 원형 양동이 15개면 충돌하지 않는다.
function M.dijkstra(m, kind, starts, goal)
    local w, h = m.w, m.h
    local dist = {n = w * h}
    for i = 0, w * h - 1 do dist[i] = INF end
    local buckets = {}
    for i = 0, NB - 1 do buckets[i] = {n = 0} end
    local pending = 0
    for k = 0, starts.n - 1 do
        local s = starts[k]
        if dist[s] > 0 then
            dist[s] = 0
            local b = buckets[0]
            b.n = b.n + 1
            b[b.n] = s
            pending = pending + 1
        end
    end
    local cur = 0
    while pending > 0 do
        local b = buckets[cur % NB]
        while b.n == 0 do
            cur = cur + 1
            b = buckets[cur % NB]
        end
        local p = b[b.n]                    -- 파이썬 list.pop() 과 같은 끝에서 꺼내기
        b[b.n] = nil
        b.n = b.n - 1
        pending = pending - 1
        if dist[p] == cur then              -- 낡은 항목 — 감소키를 구현하지 않는다
            if goal ~= nil and p == goal then
                return dist
            end
            local x, y = p % w, floor(p / w)
            for d = 0, 7 do
                local u, v = x + DX[d], y + DY[d]
                if m:passable_terrain(u, v, kind) then
                    local j = v * w + u
                    local nd = cur + DCOST[d]
                    if nd < dist[j] then
                        dist[j] = nd
                        local nb = buckets[nd % NB]
                        nb.n = nb.n + 1
                        nb[nb.n] = j
                        pending = pending + 1
                    end
                end
            end
        end
    end
    return dist
end

-- ── SPEC §8.5 A* (손으로 쓴 이진 힙) ────────────────────────────────────────

--- (f, h, idx) 사전식 최소 힙.
--
--    파이썬 heapq · 루아 table.sort · 자바스크립트 Array.sort 는 서로 다른
--    순서를 낼 수 있다. 비교자가 전순서이기만 하면 손으로 쓴 힙이 세 언어에서
--    같은 순서로 뽑는다 — 그래서 손으로 쓴다.
local Heap = {}
Heap.__index = Heap
M.Heap = Heap

function M.newheap()
    -- 세 배열을 나란히 둔다. 튜플 테이블을 매번 만들면 GC 가 일을 너무 많이 한다.
    return setmetatable({f = {}, h = {}, i = {}, n = 0}, Heap)
end
Heap.new = M.newheap

function Heap:len()
    return self.n
end

--- (f, h, idx) 사전식 비교. a < b 인가.
local function lt(af, ah, ai, bf, bh, bi)
    if af ~= bf then return af < bf end
    if ah ~= bh then return ah < bh end
    return ai < bi
end

function Heap:push(f, hh, idx)
    local n = self.n + 1
    self.n = n
    self.f[n], self.h[n], self.i[n] = f, hh, idx
    local af, ah, ai = self.f, self.h, self.i
    local c = n
    while c > 1 do
        local p = floor(c / 2)
        if not lt(af[c], ah[c], ai[c], af[p], ah[p], ai[p]) then
            break
        end
        af[p], af[c] = af[c], af[p]
        ah[p], ah[c] = ah[c], ah[p]
        ai[p], ai[c] = ai[c], ai[p]
        c = p
    end
end

function Heap:pop()
    local af, ah, ai = self.f, self.h, self.i
    local tf, th, ti = af[1], ah[1], ai[1]
    local n = self.n
    af[1], ah[1], ai[1] = af[n], ah[n], ai[n]
    af[n], ah[n], ai[n] = nil, nil, nil
    n = n - 1
    self.n = n
    local c = 1
    while true do
        local l, r = 2 * c, 2 * c + 1
        local s = c
        if l <= n and lt(af[l], ah[l], ai[l], af[s], ah[s], ai[s]) then s = l end
        if r <= n and lt(af[r], ah[r], ai[r], af[s], ah[s], ai[s]) then s = r end
        if s == c then break end
        af[s], af[c] = af[c], af[s]
        ah[s], ah[c] = ah[c], ah[s]
        ai[s], ai[c] = ai[c], ai[s]
        c = s
    end
    return tf, th, ti
end

--- (비용, 경로 타일 목록, 연 노드 수). 도달 불가면 (-1, 빈 목록, n).
function M.astar(m, kind, s, t)
    local w = m.w
    if not (m:passable_terrain(s[0], s[1], kind)
            and m:passable_terrain(t[0], t[1], kind)) then
        return -1, {n = 0}, 0
    end
    local si, ti = s[1] * w + s[0], t[1] * w + t[0]
    local dist = {[si] = 0}
    local prev = {}
    local closed = {}
    local heap = M.newheap()
    local h0 = h_oct(s[0], s[1], t[0], t[1])
    heap:push(h0, h0, si)
    local expanded = 0
    while heap.n > 0 do
        local _f, _hh, p = heap:pop()
        if not closed[p] then
            closed[p] = true               -- 일관적이므로 재개방하지 않는다
            expanded = expanded + 1
            if p == ti then
                local rev = {}
                local cnt = 1
                rev[1] = p
                while rev[cnt] ~= si do
                    cnt = cnt + 1
                    rev[cnt] = prev[rev[cnt - 1]]
                end
                local out = {n = cnt}
                for k = 1, cnt do out[k - 1] = rev[cnt - k + 1] end
                return dist[p], out, expanded
            end
            local x, y = p % w, floor(p / w)
            local dp = dist[p]
            for d = 0, 7 do
                local u, v = x + DX[d], y + DY[d]
                if m:passable_terrain(u, v, kind) then
                    local j = v * w + u
                    local nd = dp + DCOST[d]
                    local old = dist[j]
                    if old == nil or nd < old then
                        dist[j] = nd
                        prev[j] = p
                        local hn = h_oct(u, v, t[0], t[1])
                        heap:push(nd + hn, hn, j)
                    end
                end
            end
        end
    end
    return -1, {n = 0}, expanded
end

-- ── SPEC §8.6 도달 불가 목표 ────────────────────────────────────────────────

--- 목표가 다른 성분이면 같은 성분에서 목표에 가장 가까운 칸으로 바꾼다.
--
--    이 한 줄이 없으면 '섬 건너편 클릭' 한 번이 A* 에게 맵 전체를 펴게 한다.
function M.closest_reachable(m, kind, s, t)
    local lab = m:labels(kind)
    local si = s[1] * m.w + s[0]
    local ti = t[1] * m.w + t[0]
    if lab[si] < 0 then
        return nil
    end
    if lab[ti] == lab[si] then
        return t
    end
    local best, bd, bi = nil, INF, INF
    for i = 0, m.w * m.h - 1 do
        if lab[i] == lab[si] then
            local x, y = i % m.w, floor(i / m.w)
            local d = F.d83(x - t[0], y - t[1])
            if d < bd or (d == bd and i < bi) then
                best, bd, bi = {[0] = x, [1] = y, n = 2}, d, i
            end
        end
    end
    return best
end

-- ── SPEC §8.7 경로 캐시 ─────────────────────────────────────────────────────

--- 64칸 LRU. 지형이 바뀌면 통째로 비운다 — 낡은 경로는 곧 디싱크다.
--
--    LRU 순서는 상태가 아니다(해시에 넣지 않는다). 캐시는 같은 답을 더 빨리 줄
--    뿐이고, 다른 답을 주면 그것은 버그다.
local Cache = {}
Cache.__index = Cache
M.Cache = Cache
Cache.LIMIT = 64

function M.newcache()
    return setmetatable({map_version = -1, data = {}, order = {},
                         hits = 0, misses = 0}, Cache)
end
Cache.new = M.newcache

local function order_remove(order, key)
    for i = 1, #order do
        if order[i] == key then
            table.remove(order, i)
            return
        end
    end
end

function Cache:get(m, key)
    if m.version ~= self.map_version then
        self.map_version = m.version
        self.data = {}
        self.order = {}
    end
    if self.data[key] ~= nil then
        self.hits = self.hits + 1
        order_remove(self.order, key)
        self.order[#self.order + 1] = key
        return self.data[key]
    end
    self.misses = self.misses + 1
    return nil
end

function Cache:put(key, value)
    if self.data[key] ~= nil then
        order_remove(self.order, key)
    elseif #self.order >= Cache.LIMIT then
        local oldest = table.remove(self.order, 1)
        self.data[oldest] = nil
    end
    self.data[key] = value
    self.order[#self.order + 1] = key
end

--- 캐시를 거치는 표준 경로 질의. 목표가 닿지 않으면 대체 목표로 바꾼다.
function M.find(m, kind, s, t, cache)
    local goal = M.closest_reachable(m, kind, s, t)
    if goal == nil then
        return -1, {n = 0}
    end
    -- 캐시 열쇠는 (출발, 목표, 종류) 세 정수다 — 루아에 튜플 열쇠가 없어
    -- 문자열로 잇는다. 캐시는 상태가 아니므로 표현 방식은 자유다.
    local key = (s[1] * m.w + s[0]) .. ',' .. (goal[1] * m.w + goal[0])
                .. ',' .. kind
    if cache ~= nil then
        local hit = cache:get(m, key)
        if hit ~= nil then
            return hit[1], hit[2]
        end
    end
    local cost, tiles = M.astar(m, kind, s, goal)
    if cache ~= nil then
        cache:put(key, {cost, tiles})
    end
    return cost, tiles
end

return M
