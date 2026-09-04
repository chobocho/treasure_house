-- 헥스 좌표계 — SPEC §1, §4.4, §9.1
--
-- 파이썬판과 같은 알고리즘이지만 루아의 성질 두 가지를 조심한다.
--   1. `>>` 는 논리 시프트다. 음수를 오른쪽으로 밀면 거대한 양수가 된다.
--      그래서 floor(x/2) 가 필요한 자리에는 반드시 `//` 를 쓴다.
--   2. `/` 는 언제나 실수를 만든다. 정수 나눗셈은 `//`, 나머지는 `%`.
-- 이 둘만 지키면 나머지는 파이썬과 한 줄씩 대응된다.

local M = {}

-- SPEC §1.5 — 방향 인덱스는 세이브·골든 트레이스의 일부라 순서가 불변이다.
-- 루아 테이블은 1부터 세지만, 방향 인덱스는 0..5 라는 규격을 지키려고
-- 0-베이스로 직접 채운다.
M.DIRS = {}
M.DIRS[0] = { 1, 0 }
M.DIRS[1] = { 1, -1 }
M.DIRS[2] = { 0, -1 }
M.DIRS[3] = { -1, 0 }
M.DIRS[4] = { -1, 1 }
M.DIRS[5] = { 0, 1 }
M.DIR_NAMES = { [0] = 'E', 'NE', 'NW', 'W', 'SW', 'SE' }

M.SCALE = 1024
M.NUDGE = { 1, 1, -2 }

function M.to_cube(q, r)
  return q, -q - r, r
end

function M.axial_to_oddr(q, r)
  return q + (r - (r & 1)) // 2, r
end

function M.oddr_to_axial(col, row)
  return col - (row - (row & 1)) // 2, row
end

function M.axial_to_oddq(q, r)
  return q, r + (q - (q & 1)) // 2
end

function M.oddq_to_axial(col, row)
  return col, row - (col - (col & 1)) // 2
end

function M.distance(aq, ar, bq, br)
  local dq, dr = aq - bq, ar - br
  local s = dq + dr
  if dq < 0 then dq = -dq end
  if dr < 0 then dr = -dr end
  if s < 0 then s = -s end
  return (dq + dr + s) // 2
end

function M.neighbor(q, r, d)
  local dd = M.DIRS[d]
  return q + dd[1], r + dd[2]
end

function M.neighbors(q, r)
  local out = {}
  for d = 0, 5 do
    local dd = M.DIRS[d]
    out[#out + 1] = { q + dd[1], r + dd[2] }
  end
  return out
end

function M.rotate_cw(x, y, z)
  return -y, -z, -x
end

function M.rotate_ccw(x, y, z)
  return -z, -x, -y
end

function M.rotate_about(q, r, cq, cr, steps)
  local x, y, z = M.to_cube(q - cq, r - cr)
  for _ = 1, steps % 6 do
    x, y, z = M.rotate_cw(x, y, z)
  end
  return x + cq, z + cr
end

function M.reflect_q(x, y, z)
  return x, z, y
end

function M.ring(cq, cr, n)
  if n == 0 then return { { cq, cr } } end
  local q = cq + M.DIRS[4][1] * n
  local r = cr + M.DIRS[4][2] * n
  local out = {}
  for d = 0, 5 do
    local dd = M.DIRS[d]
    for _ = 1, n do
      out[#out + 1] = { q, r }
      q = q + dd[1]
      r = r + dd[2]
    end
  end
  return out
end

function M.spiral(cq, cr, n)
  local out = { { cq, cr } }
  for k = 1, n do
    for _, h in ipairs(M.ring(cq, cr, k)) do
      out[#out + 1] = h
    end
  end
  return out
end

-- d > 0 인 반올림 나눗셈, 동점은 0에서 먼 쪽. SPEC §4.4
-- 루아의 // 는 내림이므로 음수 쪽을 따로 처리해야 파이썬과 답이 같다.
function M.round_div(n, d)
  if n >= 0 then
    return (2 * n + d) // (2 * d)
  end
  return -((-2 * n + d) // (2 * d))
end

function M.cube_round(xf, yf, zf, scale)
  scale = scale or M.SCALE
  local rx = M.round_div(xf, scale)
  local ry = M.round_div(yf, scale)
  local rz = M.round_div(zf, scale)
  local dx = rx * scale - xf
  local dy = ry * scale - yf
  local dz = rz * scale - zf
  if dx < 0 then dx = -dx end
  if dy < 0 then dy = -dy end
  if dz < 0 then dz = -dz end
  if dx > dy and dx > dz then
    rx = -ry - rz
  elseif dy > dz then
    ry = -rx - rz
  else
    rz = -rx - ry
  end
  return rx, rz
end

function M.line(aq, ar, bq, br)
  local n = M.distance(aq, ar, bq, br)
  local ax, ay, az = M.to_cube(aq, ar)
  local bx, by, bz = M.to_cube(bq, br)
  local S = M.SCALE
  ax = ax * S + M.NUDGE[1]
  ay = ay * S + M.NUDGE[2]
  az = az * S + M.NUDGE[3]
  bx, by, bz = bx * S, by * S, bz * S
  if n == 0 then
    local q, r = M.cube_round(ax, ay, az)
    return { { q, r } }
  end
  local out = {}
  for i = 0, n do
    local ti = i * S // n
    local q, r = M.cube_round(ax + (bx - ax) * ti // S,
                              ay + (by - ay) * ti // S,
                              az + (bz - az) * ti // S)
    out[#out + 1] = { q, r }
  end
  return out
end

return M
