-- 상자 정렬 — 부분순서, 순환, 보조정리 6.2 를 실제로 확인한다.

local H = require("tests.harness")
local S = require("isorpg.sortdag")

H.title('sortdag')

local function load_cases()
  local rows = {}
  for _, line in ipairs(H.lines(H.golden('sortcase.txt'))) do
    local t = {}
    for tok in line:gmatch('%S+') do t[#t + 1] = tok end
    rows[#rows + 1] = t
  end
  local out = {}
  local i = 2
  while i <= #rows do
    local num, name, n = tonumber(rows[i][2]), rows[i][3], tonumber(rows[i][4])
    i = i + 1
    local items = {}
    for k = 0, n - 1 do
      local it = {}
      for t = 1, #rows[i + k] do it[t] = tonumber(rows[i + k][t]) end
      items[k + 1] = it
    end
    i = i + n
    out[#out + 1] = {num, name, items}
  end
  return out
end

local CASES = load_cases()
H.check('사례 개수', #CASES, 6)

local EXPECT = {
  [1] = {{0, 1}, 0}, [2] = {{0, 1}, 0}, [3] = {{0, 1}, 0},
  [4] = {{2, 0, 1}, 0}, [5] = {{0, 1}, 0}, [6] = {{0, 1, 2}, 1},
}
local BY = {}
for i = 1, #CASES do
  local num, name, items = CASES[i][1], CASES[i][2], CASES[i][3]
  BY[num] = items
  local order, breaks = S.topo_sort(items)
  H.check(string.format('case %d %s', num, name), {order, breaks}, EXPECT[num])
end

-- ---- 6번은 진짜 3-순환인가 (간선이 정확히 세 개, 한 방향씩)
local items = BY[6]
local bb = {}
for i = 1, 3 do bb[i] = S.box_bbox(items[i]) end
local edges = {}
for i = 1, 3 do
  for j = 1, 3 do
    if i ~= j and S.bbox_overlap(bb[i], bb[j]) then
      if S.behind(items[i], items[j]) and not S.behind(items[j], items[i]) then
        edges[#edges + 1] = {i - 1, j - 1}
      end
    end
  end
end
table.sort(edges, function(a, b)
  if a[1] ~= b[1] then return a[1] < b[1] end
  return a[2] < b[2]
end)
H.check('3-순환 간선', edges, {{0, 1}, {1, 2}, {2, 0}})

-- ---- 5번은 상호 관계인데 화면에서 겹치는가
local items5 = BY[5]
local b5 = {S.box_bbox(items5[1]), S.box_bbox(items5[2])}
H.check_true('5번 경계상자 겹침', S.bbox_overlap(b5[1], b5[2]))
H.check_true('5번 상호 behind', S.behind(items5[1], items5[2])
             and S.behind(items5[2], items5[1]))

-- ---- 보조정리 6.2 : x/y 상호는 겹칠 수 없다
local rs = 999
local function rnd(n)
  rs = H.lcg31(rs)
  return rs - n * math.floor(rs / n)
end

local viol, xy_mutual = 0, 0
for _ = 1, 60000 do
  local a1, a2, a3 = rnd(6), rnd(6), rnd(4)
  local a = {0, a1, a2, a3, a1 + 1 + rnd(3), a2 + 1 + rnd(3), a3 + 1 + rnd(2)}
  local b1, b2, b3 = rnd(6), rnd(6), rnd(4)
  local b = {1, b1, b2, b3, b1 + 1 + rnd(3), b2 + 1 + rnd(3), b3 + 1 + rnd(2)}
  if (a[5] <= b[2] and b[6] <= a[3]) or (b[5] <= a[2] and a[6] <= b[3]) then
    xy_mutual = xy_mutual + 1
    if S.bbox_overlap(S.box_bbox(a), S.box_bbox(b)) then viol = viol + 1 end
  end
end
H.note('x/y 상호 사례 %d건 생성', xy_mutual)
H.check('보조정리 6.2 반례', viol, 0)

-- ---- 정렬 결과는 결정적인가 (같은 입력 -> 같은 출력)
for i = 1, #CASES do
  local num, _, its = CASES[i][1], CASES[i][2], CASES[i][3]
  local o1, b1 = S.topo_sort(its)
  local o2, b2 = S.topo_sort(its)
  H.check(string.format('결정성 case %d', num), {o1, b1}, {o2, b2})
end

-- ---- 순환이 없으면 위상 순서가 실제로 모든 간선을 지키는가
for i = 1, #CASES do
  local num, _, its = CASES[i][1], CASES[i][2], CASES[i][3]
  local order, breaks = S.topo_sort(its)
  if breaks == 0 then
    local pos = {}
    for k = 1, #order do pos[order[k]] = k end
    local bad = 0
    local bbs = {}
    for k = 1, #its do bbs[k] = S.box_bbox(its[k]) end
    for p = 1, #its do
      for q = 1, #its do
        if p ~= q and S.bbox_overlap(bbs[p], bbs[q]) then
          if S.behind(its[p], its[q]) and not S.behind(its[q], its[p]) then
            if pos[its[p][1]] > pos[its[q][1]] then bad = bad + 1 end
          end
        end
      end
    end
    H.check(string.format('case %d 간선 위반', num), bad, 0)
  end
end

H.done()
