-- 전투 판정 — SPEC §7

local H = require('hexwar.hexcoord')
local hexmap = require('hexwar.hexmap')
local units = require('hexwar.units')

local M = {}

function M.defense_of(m, pool, d)
  local i = m:axial_idx(d.q, d.r)
  local terr = i >= 0 and hexmap.T_DEF[m.cells[i] & hexmap.TERRAIN_MASK] or 0
  return units.K_DEF[d.kind] * d.hp // 10 + terr + d.ent
end

function M.attack_of(a)
  return units.K_ATK[a.kind] * a.hp // 10
end

function M.resolve(m, pool, rng, a, d)
  local atk = M.attack_of(a)
  local dfn = M.defense_of(m, pool, d)
  local roll = rng:d6() + rng:d6()
  local score = atk - dfn + roll - 7

  local dl, al
  if score >= 4 then dl, al = 3, 0
  elseif score >= 1 then dl, al = 2, 1
  elseif score >= -2 then dl, al = 1, 1
  else dl, al = 0, 2 end

  a.ammo = a.ammo - 1
  a.mp = 0
  d.hp = d.hp - dl
  a.hp = a.hp - al

  local counter = 0
  if d.hp > 0 and d.ammo > 0 and units.K_RNG[d.kind] >= 1
      and H.distance(a.q, a.r, d.q, d.r) == 1 then
    counter = dl // 2
    if counter > 0 then
      a.hp = a.hp - counter
      d.ammo = d.ammo - 1
    end
  end
  return al + counter, dl, roll, score
end

function M.can_attack(m, pool, a, d)
  if a.side == d.side or a.ammo <= 0 or a.mp <= 0 then return false end
  return H.distance(a.q, a.r, d.q, d.r) <= units.K_RNG[a.kind]
end

return M
