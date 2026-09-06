-- 난수 — SPEC §5.2. 볼랜드 계열 LCG.
--
--   승수 22695477 을 상태에 그냥 곱하면 22695477 * 2^32 ~ 2^57 이라
--   배정밀도 가수(53비트)를 넘는다. 루아에는 정수형이 없으니 넘는 순간
--   조용히 반올림된 값이 나오고, 그때부터 세 언어의 난수가 갈린다.
--   그래서 상태를 상·하위 16비트로 쪼개 두 번 곱한다. (정리 5.1)
--   중간값은 모두 2^42 미만이라 정확하다.

local floor = math.floor

local M = {}

M.LCG_A = 22695477
M.LCG_C = 1
M.LCG_M = 4294967296            -- 2^32

local LCG_A, LCG_M = 22695477, 4294967296

local Rng = {}
Rng.__index = Rng
M.Rng = Rng

function M.new(seed)
  return setmetatable({s = seed - LCG_M * floor(seed / LCG_M)}, Rng)
end

-- 상태를 한 걸음 굴리고 15비트 난수를 돌려준다 (0..32767).
-- 하위 비트는 주기가 짧다 — 최하위 비트는 0,1 을 번갈 뿐이라 비트 30..16 을 꺼낸다.
function Rng:next()
  local s = self.s
  local sh = floor(s / 65536)
  local sl = s - sh * 65536
  local lo = LCG_A * sl + 1                       -- < 2^41
  local hi = LCG_A * sh                           -- < 2^41
  local ns = (hi - 65536 * floor(hi / 65536)) * 65536 + lo
  ns = ns - LCG_M * floor(ns / LCG_M)
  self.s = ns
  local top = floor(ns / 65536)
  return top - 32768 * floor(top / 32768)
end

function Rng:below(n)
  local v = self:next()
  return v - n * floor(v / n)
end

function Rng:roll(n, m)
  local t = 0
  for _ = 1, n do
    local v = self:next()
    t = t + (v - m * floor(v / m)) + 1
  end
  return t
end

return M
