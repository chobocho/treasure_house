-- 유닛 풀 — SPEC §3
--
-- 파이썬의 __slots__ 에 해당하는 것이 루아에는 없다. 대신 유닛 하나가
-- 해시 테이블이라 필드 접근마다 문자열 해시를 탄다. 도스식으로 하려면
-- 필드를 배열 첨자(1..9)로 두는 편이 빠르지만, 그러면 코드가 읽히지 않는다.
-- 여기서는 가독성을 택하고, 대신 뜨거운 경로(경로 탐색)에서는 유닛 대신
-- 정수 인덱스만 만지도록 설계했다.

local M = {}

M.MAX_UNITS = 64
M.NO_UNIT = -1
M.INF, M.TANK, M.ARTY, M.RECON = 0, 1, 2, 3

--         key      이름   mp atk def rng vis hp ammo 글자
M.KINDS = {
  [0] = { 'INF', '보병', 6, 4, 5, 1, 2, 10, 6, 'I' },
  { 'TANK', '전차', 12, 8, 6, 1, 2, 10, 6, 'T' },
  { 'ARTY', '포병', 6, 10, 2, 3, 2, 8, 5, 'A' },
  { 'RECON', '정찰', 16, 3, 3, 1, 4, 10, 4, 'R' },
}
M.K_MP, M.K_ATK, M.K_DEF, M.K_RNG, M.K_VIS, M.K_HP, M.K_AMMO, M.K_CHAR = {}, {}, {}, {}, {}, {}, {}, {}
for i = 0, 3 do
  local k = M.KINDS[i]
  M.K_MP[i], M.K_ATK[i], M.K_DEF[i], M.K_RNG[i] = k[3], k[4], k[5], k[6]
  M.K_VIS[i], M.K_HP[i], M.K_AMMO[i], M.K_CHAR[i] = k[7], k[8], k[9], k[10]
end

local Unit = {}
Unit.__index = Unit
M.Unit = Unit

function M.new_unit(uid, side, kind, q, r)
  return setmetatable({
    id = uid, side = side, kind = kind, q = q, r = r,
    hp = M.K_HP[kind], mp = M.K_MP[kind], ammo = M.K_AMMO[kind],
    ent = 0, alive = true, moved = false,
  }, Unit)
end

-- SPEC §12.1 의 정규 직렬화. 필드 순서가 해시에 그대로 반영되므로 고정이다.
function Unit:serialize()
  return string.format('%d,%d,%d,%d,%d,%d,%d,%d,%d\n',
    self.id, self.side, self.kind, self.q, self.r,
    self.hp, self.mp, self.ammo, self.ent)
end

local UnitPool = {}
UnitPool.__index = UnitPool
M.UnitPool = UnitPool

function M.new_pool(cap)
  cap = cap or M.MAX_UNITS
  local self = setmetatable({ cap = cap, slots = {}, nextfree = {}, freehead = -1 }, UnitPool)
  for i = 0, cap - 1 do
    self.slots[i] = false
    self.nextfree[i] = -1
  end
  return self
end

function UnitPool:spawn(side, kind, q, r)
  local uid
  if self.freehead >= 0 then
    uid = self.freehead
    self.freehead = self.nextfree[uid]
  else
    uid = -1
    for i = 0, self.cap - 1 do
      if not self.slots[i] then uid = i break end
    end
    if uid < 0 then error('유닛 풀이 가득 찼다') end
  end
  self.slots[uid] = M.new_unit(uid, side, kind, q, r)
  return uid
end

function UnitPool:kill(uid)
  local u = self.slots[uid]
  if not u then return end
  u.alive = false
  self.slots[uid] = false
  self.nextfree[uid] = self.freehead
  self.freehead = uid
end

function UnitPool:get(uid)
  if uid == nil or uid < 0 or uid >= self.cap then return nil end
  local u = self.slots[uid]
  if u then return u end
  return nil
end

-- 살아 있는 유닛을 아이디 오름차순으로. pairs 를 쓰지 않는 이유는
-- 루아가 해시 순회 순서를 보장하지 않기 때문이다 — 순서가 결과를 바꾸는
-- 자리가 하나라도 있으면 세 구현의 답이 갈린다.
function UnitPool:alive_ids(side)
  local out = {}
  for i = 0, self.cap - 1 do
    local u = self.slots[i]
    if u and (side == nil or u.side == side) then out[#out + 1] = i end
  end
  return out
end

function UnitPool:count(side)
  return #self:alive_ids(side)
end

function UnitPool:serialize()
  local parts = {}
  for i = 0, self.cap - 1 do
    local u = self.slots[i]
    if u then parts[#parts + 1] = u:serialize() end
  end
  return table.concat(parts)
end

return M
