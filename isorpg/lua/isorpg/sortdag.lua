-- 그리기 순서 — SPEC §6. 화가 알고리즘을 DAG 로 푼다.
--
--   '뒤에 있다'는 관계가 반대칭이 아니라서 비교 정렬을 돌리면 비교 함수가
--   모순을 일으킨다. 루아의 table.sort 는 그런 비교자를 만나면 아예
--   "invalid order function" 으로 죽는다 — 파이썬보다 더 요란하게 터진다.
--   그래서 위상 정렬을 쓴다.
--
-- 배열 규약: 상자는 {id, x0, y0, z0, x1, y1, z1} 인 1-기반 배열이고
--   골든 파일에 적힌 순서와 그대로 맞는다. 노드 번호(i, j)만 1-기반이며
--   상자 안의 id 필드는 0-기반 그대로다 (트레이스와 골든에 그 값이 실린다).

local PR = require("isorpg.proj")

local M = {}

-- 상자 필드 위치 (1-기반)
M.I_ID, M.I_X0, M.I_Y0, M.I_Z0, M.I_X1, M.I_Y1, M.I_Z1 = 1, 2, 3, 4, 5, 6, 7

local HW, HH, TZ = PR.HW, PR.HH, PR.TZ

-- 상자의 화면 경계상자 {minx, miny, maxx, maxy}.
-- 여덟 꼭짓점을 다 투영한다 — 상자 하나에 여덟 번은 싸고,
-- 그렇게 써야 왜 그 네 값인지가 코드에 남는다.
function M.box_bbox(b)
  local minx, miny = 1073741824, 1073741824
  local maxx, maxy = -1073741824, -1073741824
  for xi = 0, 1 do
    local x = xi == 0 and b[2] or b[5]
    for yi = 0, 1 do
      local y = yi == 0 and b[3] or b[6]
      for zi = 0, 1 do
        local z = zi == 0 and b[4] or b[7]
        local sx = HW * (x - y)
        local sy = HH * (x + y) - z * TZ
        if sx < minx then minx = sx end
        if sx > maxx then maxx = sx end
        if sy < miny then miny = sy end
        if sy > maxy then maxy = sy end
      end
    end
  end
  return {minx, miny, maxx, maxy}
end

function M.bbox_overlap(a, b)
  return not (a[3] <= b[1] or b[3] <= a[1] or a[4] <= b[2] or b[4] <= a[2])
end

-- a 를 b 보다 먼저 그려야 하는가. 셋 중 하나만 성립해도 참이다.
-- 이 느슨함이 화면에서는 대개 옳지만 반대칭이 아니어서 순환을 만든다.
function M.behind(a, b)
  return a[5] <= b[2] or a[6] <= b[3] or a[7] <= b[4]
end

-- 동점을 가르는 기준 (x0+y0, z0, id). id 가 마지막에 들어가 완전히 결정적이다.
function M.depth_key(b)
  return b[2] + b[3], b[4], b[1]
end

-- ---------------------------------------------------------------- 이진 힙
-- 루아 5.1 에는 heapq 가 없다. 직접 만든다.
-- 키는 (x0+y0, z0, id, 노드번호) 사전식이고 id 가 유일하므로 동점이 없다 —
-- 그래서 어떤 힙 구현을 쓰든 결과가 같다. 파이썬 heapq 와 견줄 수 있는 근거다.
local function key_less(a, b)
  if a[1] ~= b[1] then return a[1] < b[1] end
  if a[2] ~= b[2] then return a[2] < b[2] end
  if a[3] ~= b[3] then return a[3] < b[3] end
  return a[4] < b[4]
end

local function heap_push(h, e)
  local i = #h + 1
  h[i] = e
  while i > 1 do
    local p = math.floor(i / 2)
    if key_less(h[i], h[p]) then
      h[i], h[p] = h[p], h[i]
      i = p
    else
      break
    end
  end
end

local function heap_pop(h)
  local n = #h
  local top = h[1]
  h[1] = h[n]
  h[n] = nil
  n = n - 1
  local i = 1
  while true do
    local l, r = 2 * i, 2 * i + 1
    local s = i
    if l <= n and key_less(h[l], h[s]) then s = l end
    if r <= n and key_less(h[r], h[s]) then s = r end
    if s == i then break end
    h[i], h[s] = h[s], h[i]
    i = s
  end
  return top
end

-- 칸 알고리즘. 순환이 남으면 depth_key 가 가장 작은 것을 강제로 뽑는다.
-- 간선은 화면 x 로 훑으며 만든다(쓸어내기). 반환: (id 순서 배열, 순환 절단 횟수)
function M.topo_sort(items)
  local n = #items
  local bb = {}
  for i = 1, n do bb[i] = M.box_bbox(items[i]) end
  local adj = {}
  local indeg = {}
  for i = 1, n do adj[i] = {}; indeg[i] = 0 end
  -- 화면 x 로 훑는 쓸어내기. 모든 쌍을 보면 O(n^2) 인데, 한 화면에 상자가
  -- 2,100개쯤 되면 220만 번이다. x 구간이 겹치는 것끼리만 보면 10만 번으로,
  -- 22분의 1로 준다.
  local idx = {}
  for i = 1, n do idx[i] = i end
  table.sort(idx, function(p, q)
    if bb[p][1] ~= bb[q][1] then return bb[p][1] < bb[q][1] end
    return p < q
  end)
  for a = 1, n do
    local i = idx[a]
    local bi = bb[i]
    local ii = items[i]
    local ri = bi[3]
    for b = a + 1, n do
      local j = idx[b]
      local bj = bb[j]
      if bj[1] >= ri then break end                -- 이후는 전부 오른쪽
      if not (bi[4] <= bj[2] or bj[4] <= bi[2]) then
        local jj = items[j]
        local aij = M.behind(ii, jj)
        local aji = M.behind(jj, ii)
        -- 양쪽 다 참이면 순서가 무의미하다 — 간선을 걸지 않는다 (보조정리 6.2)
        if aij and not aji then
          adj[i][#adj[i] + 1] = j
          indeg[j] = indeg[j] + 1
        elseif aji and not aij then
          adj[j][#adj[j] + 1] = i
          indeg[i] = indeg[i] + 1
        end
      end
    end
  end
  local heap = {}
  for i = 1, n do
    if indeg[i] == 0 then
      local k1, k2, k3 = M.depth_key(items[i])
      heap_push(heap, {k1, k2, k3, i})
    end
  end
  local done = {}
  for i = 1, n do done[i] = false end
  local order = {}
  local breaks = 0
  local left = n
  while left > 0 do
    local pick
    if #heap > 0 then
      local e = heap_pop(heap)
      pick = e[4]
      if done[pick] then pick = nil end
    else
      -- 순환이다. 남은 것 중 가장 뒤에 있어야 할 것을 강제로 방출한다.
      breaks = breaks + 1
      local b1, b2, b3
      for i = 1, n do
        if not done[i] then
          local k1, k2, k3 = M.depth_key(items[i])
          if pick == nil or k1 < b1 or (k1 == b1 and (k2 < b2 or (k2 == b2 and k3 < b3))) then
            b1, b2, b3, pick = k1, k2, k3, i
          end
        end
      end
      for i = 1, n do
        if not done[i] then
          local ai = adj[i]
          for t = 1, #ai do
            if ai[t] == pick then
              table.remove(ai, t)
              indeg[pick] = indeg[pick] - 1
              break
            end
          end
        end
      end
    end
    if pick ~= nil then
      done[pick] = true
      left = left - 1
      order[#order + 1] = items[pick][1]
      local ap = adj[pick]
      for t = 1, #ap do
        local j = ap[t]
        indeg[j] = indeg[j] - 1
        if indeg[j] == 0 and not done[j] then
          local k1, k2, k3 = M.depth_key(items[j])
          heap_push(heap, {k1, k2, k3, j})
        end
      end
      adj[pick] = {}
    end
  end
  return order, breaks
end

return M
