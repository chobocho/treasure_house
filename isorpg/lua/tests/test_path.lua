-- 경로 — 허용성·일관성·모서리 자르기·A* == 다익스트라.

local H = require("tests.harness")
local M = require("isorpg.gamemap")
local P = require("isorpg.path")

H.title('path')

local m = M.gen_map()

-- ---- 방향표
H.check('방향 8개', {#P.DIRX, #P.DIRY}, {8, 8})
H.check('대각 표시', P.DIAG, {false, true, false, true, false, true, false, true})
H.check('걸음 기본값', P.STEP_BASE, {10, 14, 10, 14, 10, 14, 10, 14})

-- ---- 옥타일 골든
H.check('h((0,0),(0,0))', P.octile(0, 0, 0, 0), 0)
H.check('h((0,0),(1,0))', P.octile(0, 0, 1, 0), 8)
H.check('h((0,0),(1,1))', P.octile(0, 0, 1, 1), 11)
H.check('h((0,0),(47,47))', P.octile(0, 0, 47, 47), 517)
H.note('내림을 두 번 하는 흔한 형태는 같은 자리에서 526 을 낸다 — 허용성이 깨진 값')

-- ---- 허용성: 다익스트라 실제 비용 >= h
local sx, sy = 24, 34
local dist = P.dijkstra(m, sx, sy)
local bad = 0
for y = 0, 47 do
  for x = 0, 47 do
    local d = dist[y * 48 + x + 1]
    if d ~= nil then
      if P.octile(sx, sy, x, y) > d then bad = bad + 1 end
    end
  end
end
H.check('허용성 위반 (실제 비용 < h)', bad, 0)

-- ---- 일관성: 모든 간선에서 h(a)-h(n) <= cost
local gx, gy = 24, 20
bad = 0
for y = 0, 47 do
  for x = 0, 47 do
    if P.passable(m, x, y) then
      for d = 0, 7 do
        if P.step_ok(m, x, y, d) then
          local nx, ny = x + P.DIRX[d + 1], y + P.DIRY[d + 1]
          if P.octile(x, y, gx, gy) - P.octile(nx, ny, gx, gy)
             > P.step_cost(m, nx, ny, d) then
            bad = bad + 1
          end
        end
      end
    end
  end
end
H.check('일관성 위반 간선', bad, 0)

-- ---- 모서리 자르기 금지
local cut = 0
for y = 1, 46 do
  for x = 1, 46 do
    for _, d in ipairs({1, 3, 5, 7}) do
      if P.step_ok(m, x, y, d) then
        if not (P.passable(m, x + P.DIRX[d + 1], y)
                and P.passable(m, x, y + P.DIRY[d + 1])) then
          cut = cut + 1
        end
      end
    end
  end
end
H.check('막힌 모서리를 대각으로 통과한 사례', cut, 0)

-- ---- 오르막 제한
bad = 0
for y = 0, 46 do
  for x = 0, 46 do
    for d = 0, 7 do
      local nx, ny = x + P.DIRX[d + 1], y + P.DIRY[d + 1]
      if m:inside(nx, ny) and P.step_ok(m, x, y, d) then
        local dh = M.height_of(m:at(nx, ny)) - M.height_of(m:at(x, y))
        if dh < 0 then dh = -dh end
        if dh > P.CLIMB_MAX then bad = bad + 1 end
      end
    end
  end
end
H.check('오르막 제한 위반', bad, 0)

-- ---- A* 가 다익스트라와 같은 비용을 내는가
local targets = {{24, 20}, {20, 20}, {29, 29}, {24, 44}, {18, 24}, {26, 26}, {2, 2}}
local same, miss = 0, 0
for i = 1, #targets do
  local tx, ty = targets[i][1], targets[i][2]
  local gp, gc = P.astar(m, sx, sy, tx, ty)
  local want = dist[ty * 48 + tx + 1]
  if want == nil then
    miss = miss + 1
    H.check(string.format('A* 도 못 감 (%d,%d)', tx, ty), gp, nil)
  else
    H.check(string.format('A* 비용 == 다익스트라 (%d,%d)', tx, ty), gc, want)
    same = same + 1
  end
end
H.note('도달 가능 %d개 / 도달 불가 %d개', same, miss)

-- ---- 경로가 실제로 이어지는가
local path, cost, expanded = P.astar(m, sx, sy, 24, 20)
H.check('경로 시작', path[1], {sx, sy})
H.check('경로 끝', path[#path], {24, 20})
bad = 0
local tot = 0
for i = 1, #path - 1 do
  local ax, ay = path[i][1], path[i][2]
  local bx, by = path[i + 1][1], path[i + 1][2]
  local dd = -1
  for d = 0, 7 do
    if P.DIRX[d + 1] == bx - ax and P.DIRY[d + 1] == by - ay then dd = d; break end
  end
  if dd < 0 or not P.step_ok(m, ax, ay, dd) then
    bad = bad + 1
  else
    tot = tot + P.step_cost(m, bx, by, dd)
  end
end
H.check('경로 각 걸음이 합법', bad, 0)
H.check('걸음 비용 합 == A* 비용', tot, cost)
local reach = 0
for i = 0, 48 * 48 - 1 do
  if dist[i + 1] ~= nil then reach = reach + 1 end
end
H.note('A* 확장 노드 %d개 (다익스트라 전체 %d칸)', expanded, reach)
H.check_true('A* 가 다익스트라보다 적게 본다', expanded < reach)

-- ---- 양동이 큐 경계
local mx = 0
for y = 0, 47 do
  for x = 0, 47 do
    if P.passable(m, x, y) then
      for d = 0, 7 do
        local c = P.step_cost(m, x, y, d)
        if c > mx then mx = c end
      end
    end
  end
end
H.check_true('최대 간선 비용 < BUCKET_N', mx < P.BUCKET_N)

H.done()
