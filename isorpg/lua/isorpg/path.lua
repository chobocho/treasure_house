-- 경로 탐색 — SPEC §8. 8방향 격자, 다익스트라(양동이 큐), A*(옥타일).
--
-- 배열 규약: 방향표 DIRX/DIRY/DIAG/STEP_BASE/DIR_NAME 은 방향 d = 0..7 에 대해
--   [d + 1] 로 읽는다. 칸 번호 idx = y*w + x 는 파이썬과 똑같이 0-기반으로 계산하고
--   dist/gcost/prev/closed 를 짚을 때만 +1 한다. 양동이도 [key mod 64] + 1 이다.
--
--   '아직 값이 없다'는 파이썬에서 None 이지만 루아에서는 nil 이다. 그래서
--   dist 테이블에는 구멍이 생기고 # 연산자를 쓸 수 없다 — 길이가 필요하면 w*h 를 쓴다.

local M2 = require("isorpg.gamemap")

local floor = math.floor

local M = {}

--            E  SE  S  SW  W  NW  N  NE
M.DIRX = {1, 1, 0, -1, -1, -1, 0, 1}
M.DIRY = {0, 1, 1, 1, 0, -1, -1, -1}
M.DIAG = {false, true, false, true, false, true, false, true}
M.STEP_BASE = {10, 14, 10, 14, 10, 14, 10, 14}
M.DIR_NAME = {'E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE'}
M.CLIMB_MAX = 1
M.MIN_MOVE = M2.MIN_MOVE        -- 8 (ROAD)
M.BUCKET_N = 64                 -- 최대 간선 비용 floordiv(14*20,10)=28 보다 크면 된다

local DIRX, DIRY, DIAG, STEP_BASE = M.DIRX, M.DIRY, M.DIAG, M.STEP_BASE
local MOVE = M2.MOVE
local BUCKET_N = 64

function M.passable(m, x, y)
  if not (x >= 0 and x < m.w and y >= 0 and y < m.h) then return false end
  return MOVE[m:terrain(x, y) + 1] > 0
end

-- (x,y) 에서 방향 d 로 한 칸 갈 수 있는가.
-- 마지막 조건이 '모서리 자르기 금지'다 — 벽 두 장이 만나는 모서리를
-- 대각선으로 스쳐 지나가면 캐릭터가 벽을 뚫은 것처럼 보인다.
function M.step_ok(m, x, y, d)
  local nx = x + DIRX[d + 1]
  local ny = y + DIRY[d + 1]
  if not M.passable(m, nx, ny) then return false end
  local dh = m:height(nx, ny) - m:height(x, y)
  if dh > 1 or dh < -1 then return false end
  if DIAG[d + 1] then
    if not M.passable(m, nx, y) or not M.passable(m, x, ny) then return false end
  end
  return true
end

-- 도착 칸의 지형으로 값을 매긴다. 떠나는 칸이 아니라.
function M.step_cost(m, nx, ny, d)
  return floor(STEP_BASE[d + 1] * MOVE[m:terrain(nx, ny) + 1] / 10)
end

M.STRAIGHT_MIN = floor(10 * M.MIN_MOVE / 10)      -- 8  — 가장 싼 지형에서의 직진 비용
M.DIAG_MIN = floor(14 * M.MIN_MOVE / 10)          -- 11 — 같은 지형에서의 대각 비용

local STRAIGHT_MIN, DIAG_MIN = M.STRAIGHT_MIN, M.DIAG_MIN

-- 가장 싼 지형만 밟았을 때의 정확한 8방향 최단거리. (정리 8.1, 8.2)
-- 나눗셈이 하나도 없어서 내림이 두 번 겹치는 일이 아예 생기지 않는다.
function M.octile(ax, ay, bx, by)
  local dx = ax - bx
  if dx < 0 then dx = -dx end
  local dy = ay - by
  if dy < 0 then dy = -dy end
  local hi, lo
  if dx < dy then hi, lo = dy, dx else hi, lo = dx, dy end
  return STRAIGHT_MIN * hi + (DIAG_MIN - STRAIGHT_MIN) * lo
end

-- ---------------------------------------------------------------- 원형 양동이 큐
-- 간선 비용이 [0, BUCKET_N) 이면 이진 힙과 같은 순서를 준다. (정리 8.3)
-- 비교가 없어 push/pop 이 O(1) 이고, 커서 한 바퀴 비용만 전체에 분산된다.
local Bucket = {}
Bucket.__index = Bucket
M.Bucket = Bucket

function M.new_bucket()
  local b = {}
  for i = 1, BUCKET_N do b[i] = {} end
  return setmetatable({b = b, cur = 0, n = 0}, Bucket)
end

function Bucket:push(key, node)
  local k = key - BUCKET_N * floor(key / BUCKET_N)
  local q = self.b[k + 1]
  q[#q + 1] = key
  q[#q + 1] = node
  self.n = self.n + 1
end

-- 커서부터 한 바퀴 돌며 처음 비지 않은 양동이의 마지막 원소를 꺼낸다.
-- 키와 노드를 두 값으로 돌려준다 — 표를 만들면 탐색마다 쓰레기가 수만 개 쌓인다.
function Bucket:pop_min()
  if self.n == 0 then return nil end
  for _ = 1, BUCKET_N do
    local q = self.b[self.cur + 1]
    local len = #q
    if len > 0 then
      self.n = self.n - 1
      local node = q[len]
      local key = q[len - 1]
      q[len] = nil
      q[len - 1] = nil
      return key, node
    end
    self.cur = self.cur + 1
    if self.cur >= BUCKET_N then self.cur = 0 end
  end
  return nil
end

-- 시작점에서 모든 칸까지의 최소 비용. 못 가는 칸은 nil 이다.
function M.dijkstra(m, sx, sy)
  local w, h = m.w, m.h
  local dist = {}
  if not M.passable(m, sx, sy) then return dist end
  dist[sy * w + sx + 1] = 0
  local q = M.new_bucket()
  q:push(0, sy * w + sx)
  while true do
    local g, idx = q:pop_min()
    if g == nil then break end
    local cur = dist[idx + 1]
    if cur == nil or g <= cur then
      local y = floor(idx / w)
      local x = idx - y * w
      for d = 0, 7 do
        if M.step_ok(m, x, y, d) then
          local nx = x + DIRX[d + 1]
          local ny = y + DIRY[d + 1]
          local ng = g + M.step_cost(m, nx, ny, d)
          local ni = ny * w + nx
          local old = dist[ni + 1]
          if old == nil or ng < old then
            dist[ni + 1] = ng
            q:push(ng, ni)
          end
        end
      end
    end
  end
  return dist
end

-- (경로, 비용, 확장 노드 수). 못 가면 (nil, nil, 확장 수).
-- f = g + h 를 같은 양동이 큐에 넣는다. h 가 일관적이라 f 는 단조 증가하고
-- 한 걸음에 최대 28 늘어난다 — 활성 폭이 BUCKET_N 미만이다.
function M.astar(m, sx, sy, gx, gy)
  local w = m.w
  if not M.passable(m, sx, sy) or not M.passable(m, gx, gy) then
    return nil, nil, 0
  end
  local gcost = {}
  local prev = {}
  local closed = {}
  local si = sy * w + sx
  local gi = gy * w + gx
  gcost[si + 1] = 0
  local q = M.new_bucket()
  q:push(M.octile(sx, sy, gx, gy), si)
  local expanded = 0
  while true do
    local f, idx = q:pop_min()
    if f == nil then return nil, nil, expanded end
    if not closed[idx + 1] then
      closed[idx + 1] = true
      expanded = expanded + 1
      if idx == gi then break end
      local y = floor(idx / w)
      local x = idx - y * w
      local g = gcost[idx + 1]
      for d = 0, 7 do
        if M.step_ok(m, x, y, d) then
          local nx = x + DIRX[d + 1]
          local ny = y + DIRY[d + 1]
          local ni = ny * w + nx
          if not closed[ni + 1] then
            local ng = g + M.step_cost(m, nx, ny, d)
            local old = gcost[ni + 1]
            if old == nil or ng < old then
              gcost[ni + 1] = ng
              prev[ni + 1] = idx
              q:push(ng + M.octile(nx, ny, gx, gy), ni)
            end
          end
        end
      end
    end
  end
  local rev = {}
  local i = gi
  while i ~= nil do
    local y = floor(i / w)
    rev[#rev + 1] = {i - y * w, y}
    i = prev[i + 1]
  end
  local path = {}
  for k = #rev, 1, -1 do path[#path + 1] = rev[k] end
  return path, gcost[gi + 1], expanded
end

return M
