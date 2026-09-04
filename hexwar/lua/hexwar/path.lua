-- 이동 범위와 경로 — SPEC §6

local H = require('hexwar.hexcoord')
local hexmap = require('hexwar.hexmap')
local units = require('hexwar.units')

local M = {}

M.UNREACHED = 0x7FFFFFFF
M.MIN_COST = 1

function M.zoc_mask(m, pool, side)
  local mask = {}
  for i = 0, m.n - 1 do mask[i] = 0 end
  for _, uid in ipairs(pool:alive_ids()) do
    local u = pool:get(uid)
    if u.side ~= side then
      local i = m:axial_idx(u.q, u.r)
      if i >= 0 then
        local nb, k = m:neighbors_with_dir(i)
        for j = 1, k do mask[nb[j][2]] = 1 end
      end
    end
  end
  return mask
end

function M.step_cost(m, pool, side, frm, to)
  local c = m.cells[to]
  local mv = hexmap.T_MOVE[c & hexmap.TERRAIN_MASK]
  if mv < 0 then return -1 end
  if m.occupant[to] ~= units.NO_UNIT then return -1 end
  if (m.cells[frm] & 0x80) ~= 0 and (c & 0x80) ~= 0 then return 1 end
  return mv
end

-- 이동 범위 결과. 파이썬의 Reach 클래스와 같은 모양이다.
--   cost[i] 쓴 이동력 · came[i] 들어온 방향 · list 인덱스 오름차순 목록
local Reach = {}
Reach.__index = Reach
M.Reach = Reach

function Reach:has(i) return self.cost[i] ~= nil end

local function new_reach(cost, came, list)
  return setmetatable({ cost = cost, came = came, list = list }, Reach)
end
M.new_reach = new_reach

-- Dial 의 양동이 큐. 비용이 1..6 이라 힙이 필요 없다 — O(V+E+maxMP).
function M.reachable(m, pool, unit)
  local start = m:axial_idx(unit.q, unit.r)
  local budget = unit.mp
  if start < 0 then return new_reach({}, {}, {}) end
  if budget <= 0 then
    return new_reach({ [start] = 0 }, { [start] = -1 }, { start })
  end

  local best, came = {}, {}
  for i = 0, m.n - 1 do best[i] = M.UNREACHED end
  best[start] = 0
  local zoc = M.zoc_mask(m, pool, unit.side)
  local buckets = {}
  for c = 0, budget do buckets[c] = {} end
  buckets[0][1] = start

  for c = 0, budget do
    local b = buckets[c]
    local bi = 1
    while bi <= #b do
      local cur = b[bi]
      bi = bi + 1
      if best[cur] == c and (cur == start or zoc[cur] == 0) then
        local nb, k = m:neighbors_with_dir(cur)
        for j = 1, k do
          local d, ni = nb[j][1], nb[j][2]
          local sc = M.step_cost(m, pool, unit.side, cur, ni)
          if sc >= 0 then
            local nc = c + sc
            if nc <= budget and nc < best[ni] then
              best[ni] = nc
              came[ni] = d
              local bk = buckets[nc]
              bk[#bk + 1] = ni
            end
          end
        end
      end
    end
  end

  local cost, came2, list = {}, {}, {}
  for i = 0, m.n - 1 do
    if best[i] ~= M.UNREACHED then
      cost[i] = best[i]
      came2[i] = came[i] or -1
      list[#list + 1] = i
    end
  end
  return new_reach(cost, came2, list)
end

function M.trace_path(m, reach, target)
  if not reach:has(target) then return {} end
  local path = { target }
  local cur = target
  while true do
    local d = reach.came[cur]
    if d < 0 then break end
    local row = cur // m.w
    local col = cur - row * m.w
    local back = hexmap.NEIGHBOR_DELTA[row & 1][(d + 3) % 6]
    col = col + back[1]
    row = row + back[2]
    cur = row * m.w + col
    path[#path + 1] = cur
  end
  local out = {}
  for i = #path, 1, -1 do out[#out + 1] = path[i] end
  return out
end

-- A* — 이진 힙. 동점은 삽입 순번으로 깨서 언어마다 답이 달라지지 않게 한다.
local function heap_push(h, f, ord, idx)
  h[#h + 1] = { f, ord, idx }
  local i = #h
  while i > 1 do
    local p = i // 2
    local a, b = h[i], h[p]
    if a[1] < b[1] or (a[1] == b[1] and a[2] < b[2]) then
      h[i], h[p] = h[p], h[i]
      i = p
    else
      break
    end
  end
end

local function heap_pop(h)
  local top = h[1]
  local last = h[#h]
  h[#h] = nil
  local n = #h
  if n > 0 then
    h[1] = last
    local i = 1
    while true do
      local l, r, s = i * 2, i * 2 + 1, i
      if l <= n and (h[l][1] < h[s][1] or (h[l][1] == h[s][1] and h[l][2] < h[s][2])) then s = l end
      if r <= n and (h[r][1] < h[s][1] or (h[r][1] == h[s][1] and h[r][2] < h[s][2])) then s = r end
      if s == i then break end
      h[i], h[s] = h[s], h[i]
      i = s
    end
  end
  return top
end

function M.astar(m, pool, side, start, goal)
  if start == goal then return { start } end
  local gq, gr = m:idx_axial(goal)
  local g, came = {}, {}
  for i = 0, m.n - 1 do g[i] = M.UNREACHED; came[i] = -1 end
  g[start] = 0
  local order = 0
  local sq, sr = m:idx_axial(start)
  local heap = {}
  heap_push(heap, H.distance(sq, sr, gq, gr) * M.MIN_COST, 0, start)
  local closed = {}

  while #heap > 0 do
    local top = heap_pop(heap)
    local cur = top[3]
    if not closed[cur] then
      closed[cur] = true
      if cur == goal then break end
      local nb, k = m:neighbors_with_dir(cur)
      for j = 1, k do
        local ni = nb[j][2]
        if not closed[ni] then
          local sc = M.step_cost(m, pool, side, cur, ni)
          if sc >= 0 then
            local ng = g[cur] + sc
            if ng < g[ni] then
              g[ni] = ng
              came[ni] = cur
              local nq, nr = m:idx_axial(ni)
              order = order + 1
              heap_push(heap, ng + H.distance(nq, nr, gq, gr) * M.MIN_COST, order, ni)
            end
          end
        end
      end
    end
  end

  if g[goal] == M.UNREACHED then return {} end
  local rev = { goal }
  while rev[#rev] ~= start do rev[#rev + 1] = came[rev[#rev]] end
  local out = {}
  for i = #rev, 1, -1 do out[#out + 1] = rev[i] end
  return out
end

return M
