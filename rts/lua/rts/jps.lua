-- 점프 포인트 탐색 — Harabor & Grastien 2011 (SPEC §10).
--
--    격자의 대칭 경로를 가지치기해 A* 가 여는 노드 수를 줄인다. 비용은 A* 와
--    **정확히 같다**. 그 등가성을 정리로 옮겨 적는 대신 전수 검사로 증명한다
--    (tests/test_jps.lua).
--
--    여기 있는 가지치기 규칙은 **코너 컷을 허용하는 격자**의 것이다. 금지하면
--    강제 이웃 조건이 통째로 달라진다 — 그것이 SPEC §8.1 에서 코너 컷을
--    허용하기로 한 첫 번째 이유다.

local F = require('rts.fixed')
local P = require('rts.path')

local M = {}
local floor = math.floor

--- (x,y) 에 방향 (dx,dy) 로 들어왔을 때 강제 이웃이 있는가 (SPEC §10.1).
local function forced(m, x, y, dx, dy, kind)
    if dx ~= 0 and dy ~= 0 then
        return ((not m:passable_terrain(x - dx, y, kind)
                 and m:passable_terrain(x - dx, y + dy, kind))
                or (not m:passable_terrain(x, y - dy, kind)
                    and m:passable_terrain(x + dx, y - dy, kind)))
    end
    if dx ~= 0 then
        for _, s in ipairs({-1, 1}) do
            if not m:passable_terrain(x, y + s, kind)
               and m:passable_terrain(x + dx, y + s, kind) then
                return true
            end
        end
        return false
    end
    for _, s in ipairs({-1, 1}) do
        if not m:passable_terrain(x + s, y, kind)
           and m:passable_terrain(x + s, y + dy, kind) then
            return true
        end
    end
    return false
end
M.forced = forced
M._forced = forced

--- 방향 (dx,dy) 로 계속 나아가다 점프점을 만나면 그 칸을 돌려준다 (nil = 없음).
--
--    대각 점프가 먼저 두 성분 방향을 재귀로 훑는 것이 핵심이다. 그 방향에서
--    점프점이 나오면 지금 서 있는 대각 칸 자체가 점프점이 된다.
function M.jump(m, x, y, dx, dy, t, kind)
    local u, v = x + dx, y + dy
    if not m:passable_terrain(u, v, kind) then
        return nil
    end
    if u == t[0] and v == t[1] then
        return u, v
    end
    if forced(m, u, v, dx, dy, kind) then
        return u, v
    end
    if dx ~= 0 and dy ~= 0 then
        if M.jump(m, u, v, dx, 0, t, kind) ~= nil
           or M.jump(m, u, v, 0, dy, t, kind) ~= nil then
            return u, v
        end
    end
    return M.jump(m, u, v, dx, dy, t, kind)
end

--- 부모에서 온 방향에 따라 살아남는 이웃 방향들 (SPEC §10.1). 0-기반 배열.
function M.prune(m, x, y, parent, kind)
    local out = {n = 0}
    local function add(dx, dy)
        out[out.n] = {dx, dy}
        out.n = out.n + 1
    end
    if parent == nil or parent == false then
        for d = 0, 7 do
            if m:passable_terrain(x + F.DX[d], y + F.DY[d], kind) then
                add(F.DX[d], F.DY[d])
            end
        end
        return out
    end
    local px, py = parent[1], parent[2]
    local sx, sy = x - px, y - py
    local dx = (sx > 0 and 1 or 0) - (sx < 0 and 1 or 0)
    local dy = (sy > 0 and 1 or 0) - (sy < 0 and 1 or 0)
    if dx ~= 0 and dy ~= 0 then
        if m:passable_terrain(x + dx, y, kind) then add(dx, 0) end
        if m:passable_terrain(x, y + dy, kind) then add(0, dy) end
        if m:passable_terrain(x + dx, y + dy, kind) then add(dx, dy) end
        if not m:passable_terrain(x - dx, y, kind)
           and m:passable_terrain(x - dx, y + dy, kind) then add(-dx, dy) end
        if not m:passable_terrain(x, y - dy, kind)
           and m:passable_terrain(x + dx, y - dy, kind) then add(dx, -dy) end
    elseif dx ~= 0 then
        if m:passable_terrain(x + dx, y, kind) then add(dx, 0) end
        for _, s in ipairs({-1, 1}) do
            if not m:passable_terrain(x, y + s, kind)
               and m:passable_terrain(x + dx, y + s, kind) then add(dx, s) end
        end
    else
        if m:passable_terrain(x, y + dy, kind) then add(0, dy) end
        for _, s in ipairs({-1, 1}) do
            if not m:passable_terrain(x + s, y, kind)
               and m:passable_terrain(x + s, y + dy, kind) then add(s, dy) end
        end
    end
    return out
end

--- (비용, 점프점 목록, 연 노드 수). A* 와 같은 비교자·같은 힙을 쓴다.
function M.search(m, kind, s, t)
    local w = m.w
    if not (m:passable_terrain(s[0], s[1], kind)
            and m:passable_terrain(t[0], t[1], kind)) then
        return -1, {n = 0}, 0
    end
    local si, ti = s[1] * w + s[0], t[1] * w + t[0]
    local dist = {[si] = 0}
    -- 파이썬의 None 은 루아에서 false 로 적는다 — nil 은 "열쇠 없음"과 구별되지
    -- 않기 때문이다.
    local parent = {[si] = false}
    local closed = {}
    local heap = P.newheap()
    local h0 = P.h_oct(s[0], s[1], t[0], t[1])
    heap:push(h0, h0, si)
    local expanded = 0
    while heap.n > 0 do
        local _f, _hh, p = heap:pop()
        if not closed[p] then
            closed[p] = true
            expanded = expanded + 1
            local x, y = p % w, floor(p / w)
            if p == ti then
                local rev = {p}
                while parent[rev[#rev]] do
                    local q = parent[rev[#rev]]
                    rev[#rev + 1] = q[2] * w + q[1]
                end
                local out = {n = #rev}
                for i = 1, #rev do out[i - 1] = rev[#rev - i + 1] end
                return dist[p], out, expanded
            end
            local par = parent[p]
            local dirs = M.prune(m, x, y, par, kind)
            for k = 0, dirs.n - 1 do
                local dx, dy = dirs[k][1], dirs[k][2]
                local jx, jy = M.jump(m, x, y, dx, dy, t, kind)
                if jx ~= nil then
                    local ax = jx - x; if ax < 0 then ax = -ax end
                    local ay = jy - y; if ay < 0 then ay = -ay end
                    local steps = ax > ay and ax or ay
                    local nd = dist[p] + steps
                              * ((dx ~= 0 and dy ~= 0) and F.D_DIAG or F.D_STRAIGHT)
                    local j = jy * w + jx
                    local old = dist[j]
                    if old == nil or nd < old then
                        dist[j] = nd
                        parent[j] = {x, y}
                        local hn = P.h_oct(jx, jy, t[0], t[1])
                        heap:push(nd + hn, hn, j)
                    end
                end
            end
        end
    end
    return -1, {n = 0}, expanded
end

return M
