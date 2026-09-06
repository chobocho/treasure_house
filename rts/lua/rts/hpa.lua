-- 계층 경로 탐색 — HPA* 2수준 (SPEC §9, Botea–Müller–Schaeffer 2004).
--
--    **HPA* 는 최적이 아니다.** 원 논문이 보고하는 "최적 대비 1 % 안팎"은 그
--    논문의 맵과 클러스터 크기에서 나온 값이다. 이 엔진의 값은 골든 맵에서 직접
--    재어 out/py_prim.txt 8절에 남기고, 덱은 그 숫자만 쓴다.
--
--    루아에는 튜플 열쇠가 없다. 노드 (x,y) 는 타일 번호 y*w+x 를 열쇠로 쓰고
--    좌표는 따로 들고 다닌다 — 같은 노드가 같은 열쇠를 갖기만 하면 되고,
--    **정렬 순서는 파이썬의 튜플 정렬(x 먼저, 그다음 y)** 을 그대로 흉내 낸다.

local F = require('rts.fixed')
local P = require('rts.path')

local M = {}
local floor = math.floor

M.CLUSTER = 8
local CLUSTER = 8

function M.cluster_of(x, y)
    return floor(x / CLUSTER), floor(y / CLUSTER)
end
local cluster_of = M.cluster_of

--- 한 클러스터 안에서만 도는 A*. 8×8 이므로 최악 64칸이다.
function M.intra(m, kind, ax, ay, bx, by)
    local w = m.w
    local cx, cy = cluster_of(ax, ay)
    local lo_x, lo_y = cx * CLUSTER, cy * CLUSTER
    local hi_x, hi_y = lo_x + CLUSTER - 1, lo_y + CLUSTER - 1
    local dist = {[ay * w + ax] = 0}
    local heap = P.newheap()
    local nx, ny = {[0] = ax}, {[0] = ay}    -- 파이썬 nodes 목록과 같은 순서
    local nn = 1
    heap:push(P.h_oct(ax, ay, bx, by), 0, 0)
    local closed = {}
    while heap.n > 0 do
        local _f, _h, k = heap:pop()
        local px, py = nx[k], ny[k]
        local pi = py * w + px
        if not closed[pi] then
            closed[pi] = true
            if px == bx and py == by then
                return dist[pi]
            end
            for d = 0, 7 do
                local u, v = px + F.DX[d], py + F.DY[d]
                if m:passable_terrain(u, v, kind)
                   and u >= lo_x and u <= hi_x and v >= lo_y and v <= hi_y then
                    local j = v * w + u
                    local nd = dist[pi] + F.DCOST[d]
                    local old = dist[j]
                    if old == nil or nd < old then
                        dist[j] = nd
                        nx[nn], ny[nn] = u, v
                        nn = nn + 1
                        heap:push(nd + P.h_oct(u, v, bx, by), 0, nn - 1)
                    end
                end
            end
        end
    end
    return -1
end
local intra = M.intra

--- SPEC §9.2 — 짧은 구간은 가운데 하나, 긴 구간은 양 끝 둘.
function M._place(run, mk)
    local out = {n = 0}
    if run.n == 0 then
        return out
    end
    if run.n <= 5 then
        out[0] = mk(run[floor((run.n - 1) / 2)])
        out.n = 1
    else
        out[0] = mk(run[0])
        out[1] = mk(run[run.n - 1])
        out.n = 2
    end
    return out
end
local place = M._place

--- 클러스터 경계에서 양쪽이 모두 통행 가능한 연속 구간을 찾아 전이를 만든다.
--- 전이 하나는 {ax, ay, bx, by} 다.
local function emit(edges, got)
    for k = 0, got.n - 1 do
        edges[edges.n] = got[k]
        edges.n = edges.n + 1
    end
end

function M.entrances(m, kind)
    local edges = {n = 0}
    local ncx, ncy = floor(m.w / CLUSTER), floor(m.h / CLUSTER)
    for cy = 0, ncy - 1 do
        for cx = 0, ncx - 1 do
            if cx + 1 < ncx then
                local x = cx * CLUSTER + CLUSTER - 1
                local mk = function(yy) return {x, yy, x + 1, yy} end
                local run = {n = 0}
                for y = cy * CLUSTER, cy * CLUSTER + CLUSTER - 1 do
                    if m:passable_terrain(x, y, kind)
                       and m:passable_terrain(x + 1, y, kind) then
                        run[run.n] = y
                        run.n = run.n + 1
                    else
                        emit(edges, place(run, mk))
                        run = {n = 0}
                    end
                end
                emit(edges, place(run, mk))
            end
            if cy + 1 < ncy then
                local y = cy * CLUSTER + CLUSTER - 1
                local mk = function(xx) return {xx, y, xx, y + 1} end
                local run = {n = 0}
                for x = cx * CLUSTER, cx * CLUSTER + CLUSTER - 1 do
                    if m:passable_terrain(x, y, kind)
                       and m:passable_terrain(x, y + 1, kind) then
                        run[run.n] = x
                        run.n = run.n + 1
                    else
                        emit(edges, place(run, mk))
                        run = {n = 0}
                    end
                end
                emit(edges, place(run, mk))
            end
        end
    end
    return edges
end

--- 추상 그래프. 맵 버전이 바뀌면 다시 짓는다.
local function build_abstract(m, kind)
    local w = m.w
    local ab = {version = m.version, kind = kind, graph = {},
                coord = {}, by_cluster = {}}
    local seen = {}
    local nodelist = {n = 0}                 -- 삽입 순서 (파이썬 set 대신)
    local edges = M.entrances(m, kind)
    local function addnode(x, y)
        local id = y * w + x
        if not seen[id] then
            seen[id] = true
            ab.coord[id] = {x, y}
            nodelist[nodelist.n] = id
            nodelist.n = nodelist.n + 1
        end
        return id
    end
    local function addedge(a, b, c)
        local g = ab.graph[a]
        if g == nil then g = {}; ab.graph[a] = g end
        g[#g + 1] = {b, c}
    end
    for k = 0, edges.n - 1 do
        local e = edges[k]
        local a = addnode(e[1], e[2])
        local b = addnode(e[3], e[4])
        addedge(a, b, F.D_STRAIGHT)
        addedge(b, a, F.D_STRAIGHT)
    end
    for k = 0, nodelist.n - 1 do
        local id = nodelist[k]
        local c = ab.coord[id]
        local cx, cy = cluster_of(c[1], c[2])
        local ck = cy * 4096 + cx
        local lst = ab.by_cluster[ck]
        if lst == nil then lst = {}; ab.by_cluster[ck] = lst end
        lst[#lst + 1] = id
    end
    -- 파이썬의 sorted() 는 (x, y) 튜플을 x 먼저, 그다음 y 로 정렬한다.
    for _, ns in pairs(ab.by_cluster) do
        table.sort(ns, function(p, q)
            local a, b = ab.coord[p], ab.coord[q]
            if a[1] ~= b[1] then return a[1] < b[1] end
            return a[2] < b[2]
        end)
    end
    -- 클러스터 순회 순서는 결과에 영향을 주지 않는다 — 한 노드의 클러스터 내
    -- 간선은 자기 클러스터가 처리될 때 한 번에, 정렬된 순서로만 붙기 때문이다.
    for _, ns in pairs(ab.by_cluster) do
        for i = 1, #ns do
            for j = i + 1, #ns do
                local a, b = ab.coord[ns[i]], ab.coord[ns[j]]
                local c1 = intra(m, kind, a[1], a[2], b[1], b[2])
                if c1 >= 0 then
                    addedge(ns[i], ns[j], c1)
                    addedge(ns[j], ns[i], c1)
                end
            end
        end
    end
    return ab
end

local cache = setmetatable({}, {__mode = 'k'})

function M.abstract(m, kind)
    local per = cache[m]
    if per == nil then per = {}; cache[m] = per end
    local a = per[kind]
    if a == nil or a.version ~= m.version then
        a = build_abstract(m, kind)
        per[kind] = a
    end
    return a
end

--- 추상 그래프 위의 A*. 정련 경로의 비용은 추상 비용과 같다.
--- 돌려주는 것은 (비용, 추상 노드 타일번호 목록) 이다.
function M.search(m, kind, s, t)
    local w = m.w
    if not (m:passable_terrain(s[0], s[1], kind)
            and m:passable_terrain(t[0], t[1], kind)) then
        return -1, {n = 0}
    end
    local ab = M.abstract(m, kind)
    -- 인접 목록을 복사한다 — 임시 노드를 붙였다 질의가 끝나면 버려야 한다.
    local graph = {}
    for k, v in pairs(ab.graph) do
        local c = {}
        for i = 1, #v do c[i] = v[i] end
        graph[k] = c
    end
    local coord = {}
    for k, v in pairs(ab.coord) do coord[k] = v end
    local function addedge(a, b, c)
        local g = graph[a]
        if g == nil then g = {}; graph[a] = g end
        g[#g + 1] = {b, c}
    end
    local si, ti = s[1] * w + s[0], t[1] * w + t[0]
    coord[si] = {s[0], s[1]}
    coord[ti] = {t[0], t[1]}
    for _, temp in ipairs({s, t}) do          -- 임시 노드 삽입
        local cx, cy = cluster_of(temp[0], temp[1])
        local lst = ab.by_cluster[cy * 4096 + cx]
        if lst ~= nil then
            local tid = temp[1] * w + temp[0]
            for i = 1, #lst do
                local c = ab.coord[lst[i]]
                local c1 = intra(m, kind, temp[0], temp[1], c[1], c[2])
                if c1 >= 0 then
                    addedge(tid, lst[i], c1)
                    addedge(lst[i], tid, c1)
                end
            end
        end
    end
    local scx, scy = cluster_of(s[0], s[1])
    local tcx, tcy = cluster_of(t[0], t[1])
    if scx == tcx and scy == tcy then
        local c1 = intra(m, kind, s[0], s[1], t[0], t[1])
        if c1 >= 0 then
            addedge(si, ti, c1)
        end
    end

    local dist = {[si] = 0}
    local prev = {}
    local closed = {}
    local heap = P.newheap()
    local nodes = {[0] = si}
    local nn = 1
    heap:push(P.h_oct(s[0], s[1], t[0], t[1]), 0, 0)
    while heap.n > 0 do
        local _f, _h, k = heap:pop()
        local p = nodes[k]
        if not closed[p] then
            closed[p] = true
            if p == ti then
                local rev = {p}
                while prev[rev[#rev]] ~= nil do
                    rev[#rev + 1] = prev[rev[#rev]]
                end
                local out = {n = #rev}
                for i = 1, #rev do out[i - 1] = rev[#rev - i + 1] end
                return dist[p], out
            end
            local adj = graph[p]
            if adj ~= nil then
                for i = 1, #adj do
                    local nid, c1 = adj[i][1], adj[i][2]
                    local nd = dist[p] + c1
                    local old = dist[nid]
                    if old == nil or nd < old then
                        dist[nid] = nd
                        prev[nid] = p
                        nodes[nn] = nid
                        nn = nn + 1
                        local c = coord[nid]
                        heap:push(nd + P.h_oct(c[1], c[2], t[0], t[1]), 0, nn - 1)
                    end
                end
            end
        end
    end
    return -1, {n = 0}
end

--- 추상 경로의 인접 노드 쌍을 클러스터 안 A* 로 실제 타일 열로 편다.
function M.refine(m, kind, absnodes)
    local w = m.w
    local out = {n = 0}
    for i = 0, absnodes.n - 2 do
        local a, b = absnodes[i], absnodes[i + 1]
        local ax, ay = a % w, floor(a / w)
        local bx, by = b % w, floor(b / w)
        local acx, acy = cluster_of(ax, ay)
        local bcx, bcy = cluster_of(bx, by)
        local tiles
        local first = 0
        if acx == bcx and acy == bcy then
            local _c
            _c, tiles = P.astar(m, kind, {[0] = ax, [1] = ay, n = 2},
                                {[0] = bx, [1] = by, n = 2})
        else
            tiles = {[0] = a, [1] = b, n = 2}
        end
        if out.n > 0 and tiles.n > 0 and out[out.n - 1] == tiles[0] then
            first = 1
        end
        for k = first, tiles.n - 1 do
            out[out.n] = tiles[k]
            out.n = out.n + 1
        end
    end
    return out
end

return M
