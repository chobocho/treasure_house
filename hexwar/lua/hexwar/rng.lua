-- 난수와 해시 — SPEC §5, §10.4
--
-- 루아 5.3 이후의 정수는 64비트다. 32비트 LCG 를 흉내내려면 곱셈 뒤에
-- 반드시 0xFFFFFFFF 로 자른다. 자르지 않으면 값이 64비트로 자라 파이썬·
-- 타입스크립트와 수열이 갈린다.

local M = {}

local M32 = 0xFFFFFFFF
local MUL, ADD = 1664525, 1013904223

local Rng = {}
Rng.__index = Rng
M.Rng = Rng

function M.new(seed)
  return setmetatable({ state = seed & M32 }, Rng)
end

function Rng:next()
  self.state = (self.state * MUL + ADD) & M32
  return self.state
end

function Rng:d6()
  return ((self:next() >> 16) % 6) + 1
end

function Rng:below(n)
  return (self:next() >> 16) % n
end

function Rng:save()
  return self.state
end

function Rng:restore(s)
  self.state = s & M32
end

-- FNV-1a 32비트. 문자열의 바이트를 그대로 먹인다.
function M.fnv1a(s)
  local h = 2166136261
  for i = 1, #s do
    h = ((h ~ s:byte(i)) * 16777619) & M32
  end
  return h
end

function M.hex8(v)
  return string.format('%08x', v & M32)
end

return M
