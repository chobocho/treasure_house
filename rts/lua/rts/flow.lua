-- 흐름장·클리어런스·브러시파이어 (SPEC §11).
--
--    A* 는 "한 유닛이 한 목표로" 가는 도구다. 무리 40기가 같은 깃발로 몰려갈 때
--    A* 를 40번 부르는 것은 같은 답을 40번 계산하는 것이다. 적분장은 반대로
--    목표에서 한 번 거꾸로 퍼뜨려 두고, 유닛은 자기 칸의 방향 하나만 읽는다.
--    손익분기는 out/bench.txt 3절에 실측으로 남긴다.
--
--    여기의 모든 장은 **지형만** 본다. 점유 비트를 넣으면 유닛이 움직일 때마다
--    장을 다시 깔아야 하고, 그러면 애초에 장을 쓰는 이유가 없어진다.

local F = require('rts.fixed')

local M = {}
local floor = math.floor

M.INF = 65535               -- SPEC §11.1 — 세 언어가 같은 수를 찍어야 한다
M.NB = 15                   -- 양동이 15개 (§8.4 와 같은 이유)
M.STOP = 255
local INF, NB, STOP = 65535, 15, 255
local DX, DY, DCOST = F.DX, F.DY, F.DCOST

--- 다중 시작점 다익스트라. seeds 는 {칸번호, 초기비용} 목록(0-기반 배열).
--
--    O(칸수 × 8) 시간, O(칸수) 공간. 간선 비용이 10 과 14 둘뿐이라 원형
--    양동이 15개로 힙 없이 돈다 — 정리 8.3 이 그대로 적용된다.
local function dial(m, kind, seeds)
    local w, h = m.w, m.h
    local dist = {n = w * h}
    for i = 0, w * h - 1 do dist[i] = INF end
    local buckets = {}
    for i = 0, NB - 1 do buckets[i] = {n = 0} end
    local pending = 0
    local lo = INF
    for k = 0, seeds.n - 1 do
        local i, c = seeds[k][1], seeds[k][2]
        if c < dist[i] then
            dist[i] = c
            local b = buckets[c % NB]
            b.n = b.n + 1
            b[b.n] = i
            pending = pending + 1
            if c < lo then lo = c end
        end
    end
    if pending == 0 then
        return dist
    end
    local cur = lo
    while pending > 0 do
        local b = buckets[cur % NB]
        while b.n == 0 do
            cur = cur + 1
            b = buckets[cur % NB]
        end
        local p = b[b.n]
        b[b.n] = nil
        b.n = b.n - 1
        pending = pending - 1
        if dist[p] == cur then          -- 낡은 항목 — 감소키는 만들지 않는다
            local x, y = p % w, floor(p / w)
            for d = 0, 7 do
                local u, v = x + DX[d], y + DY[d]
                if m:passable_terrain(u, v, kind) then  -- 확장은 통행 가능 칸으로만
                    local nd = cur + DCOST[d]
                    local j = v * w + u
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
M.dial = dial

-- ── SPEC §11.1 적분장 ───────────────────────────────────────────────────────

--- 목표 집합에서 거꾸로 퍼뜨린 비용장. 도달 불가는 INF.
--
--    막힌 목표는 무시한다(§11.1). 닿을 수 없는 칸을 0 으로 심으면 장 전체가
--    그쪽으로 기울고, 그것은 §8.6 의 대체 목표가 맡을 몫이다.
function M.integration(m, kind, goals)
    local seeds = {n = 0}
    for k = 0, goals.n - 1 do
        local x, y = goals[k][0], goals[k][1]
        if m:passable_terrain(x, y, kind) then
            seeds[seeds.n] = {y * m.w + x, 0}
            seeds.n = seeds.n + 1
        end
    end
    return dial(m, kind, seeds)
end

-- ── SPEC §11.2 경사장 ───────────────────────────────────────────────────────

--- 각 칸에서 갈 방향. 후보가 없으면 255(정지).
--
--    동점은 **방향 번호가 작은 쪽**이다. 언어별 min 구현에 맡기면 대칭 맵에서
--    무리가 좌우로 갈리고, 그 갈림은 PPM 바이트 비교에서 바로 잡힌다.
function M.flow_dirs(m, kind, integ)
    local w, h = m.w, m.h
    local out = {n = w * h}
    for i = 0, w * h - 1 do out[i] = STOP end
    for y = 0, h - 1 do
        for x = 0, w - 1 do
            local i = y * w + x
            if integ[i] < INF and m:passable_terrain(x, y, kind) then
                local best, bd = INF, STOP
                for d = 0, 7 do
                    local u, v = x + DX[d], y + DY[d]
                    if m:passable_terrain(u, v, kind) then
                        local c = integ[v * w + u]
                        if c < best then       -- 등호를 빼면 작은 d 가 이긴다
                            best, bd = c, d
                        end
                    end
                end
                out[i] = bd
            end
        end
    end
    return out
end

-- ── SPEC §11.3 클리어런스 ───────────────────────────────────────────────────

--- clear[i] = (x,y) 를 좌상단으로 하는 통행 가능 정사각형의 최대 변 (정리 11.1).
--
--    O(칸수) 시간, O(칸수) 공간 — 오른쪽 아래에서 한 번만 훑는다. 맵 밖은 0
--    이므로 오른쪽·아래 가장자리의 자유 칸은 1 이 된다.
function M.clearance(m, kind)
    local w, h = m.w, m.h
    local c = {n = w * h}
    for i = 0, w * h - 1 do c[i] = 0 end
    for y = h - 1, 0, -1 do
        for x = w - 1, 0, -1 do
            if m:passable_terrain(x, y, kind) then
                if x + 1 >= w or y + 1 >= h then
                    c[y * w + x] = 1
                else
                    local r = c[y * w + x + 1]
                    local d = c[(y + 1) * w + x]
                    local q = c[(y + 1) * w + x + 1]
                    local mn = r
                    if d < mn then mn = d end
                    if q < mn then mn = q end
                    c[y * w + x] = 1 + mn
                end
            end
        end
    end
    return c
end

--- 크기 size 인 유닛이 (x,y) 를 좌상단으로 설 수 있는가.
function M.size_passable(clear, m, x, y, size)
    if not m:in_map(x, y) then
        return false
    end
    return clear[y * m.w + x] >= size
end

-- ── SPEC §11.4 브러시파이어 ─────────────────────────────────────────────────

--- 가장 가까운 막힌 칸까지의 옥타일 비용. 막힌 칸은 0.
--
--    맵 밖도 막힌 칸이다(§4.2 의 terrain_at 규약). 그래서 가장자리 자유 칸은
--    10 이고, AI 는 맵 끝에 건물을 붙이지 않는다(§17.4).
function M.brushfire(m, kind)
    local w, h = m.w, m.h
    local seeds = {n = 0}
    for y = 0, h - 1 do
        for x = 0, w - 1 do
            if not m:passable_terrain(x, y, kind) then
                seeds[seeds.n] = {y * w + x, 0}
                seeds.n = seeds.n + 1
            else
                local best = INF
                for d = 0, 7 do      -- 맵 밖 이웃은 비용 0 짜리 시작점이다
                    if not m:in_map(x + DX[d], y + DY[d]) then
                        if DCOST[d] < best then best = DCOST[d] end
                    end
                end
                if best < INF then
                    seeds[seeds.n] = {y * w + x, best}
                    seeds.n = seeds.n + 1
                end
            end
        end
    end
    return dial(m, kind, seeds)
end

return M
