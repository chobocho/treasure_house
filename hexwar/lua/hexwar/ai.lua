-- 적군 AI — SPEC 밖의 규칙이지만 결정성은 규격이다(골든 트레이스에 들어간다)

local H = require('hexwar.hexcoord')
local combat = require('hexwar.combat')
local P = require('hexwar.path')
local units = require('hexwar.units')

local M = {}

function M.score_attack(m, pool, a, d)
  return (combat.attack_of(a) - combat.defense_of(m, pool, d)) * 4 + (10 - d.hp) * 2
end

function M.best_attack(g, u)
  local best, bs = nil, -999
  for _, tid in ipairs(g.pool:alive_ids()) do
    local t = g.pool:get(tid)
    if t.side ~= u.side and H.distance(u.q, u.r, t.q, t.r) <= units.K_RNG[u.kind] then
      local s = M.score_attack(g.map, g.pool, u, t)
      if s > bs or (s == bs and best and t.id < best.id) then
        best, bs = t, s
      end
    end
  end
  return best
end

function M.nearest_enemy(g, u)
  local best, bd = nil, 1 << 30
  for _, tid in ipairs(g.pool:alive_ids()) do
    local t = g.pool:get(tid)
    if t.side ~= u.side then
      local d = H.distance(u.q, u.r, t.q, t.r)
      if d < bd or (d == bd and best and t.id < best.id) then
        best, bd = t, d
      end
    end
  end
  return best
end

function M.take_turn(g)
  local acted = 0
  for _, uid in ipairs(g.pool:alive_ids(g.side)) do
    local u = g.pool:get(uid)
    local skip = false
    if u and u.ammo > 0 and u.mp > 0 then
      local t = M.best_attack(g, u)
      if t and M.score_attack(g.map, g.pool, u, t) > -6 then
        g:attack(uid, t.id)
        acted = acted + 1
        skip = true
      end
    end
    if u and not skip then
      local tgt = M.nearest_enemy(g, u)
      if tgt and u.mp > 0 then
        local reach = P.reachable(g.map, g.pool, u)
        local goal, gs = -1, 1 << 30
        for _, i in ipairs(reach.list) do
          if g.map.occupant[i] == units.NO_UNIT then
            local q, r = g.map:idx_axial(i)
            local key = H.distance(q, r, tgt.q, tgt.r) * 100 + reach.cost[i]
            if key < gs or (key == gs and i < goal) then goal, gs = i, key end
          end
        end
        if goal >= 0 and goal ~= g.map:axial_idx(u.q, u.r) then
          g:move_unit(uid, goal)
          acted = acted + 1
          u = g.pool:get(uid)
          if u and u.ammo > 0 and u.mp > 0 then
            local t2 = M.best_attack(g, u)
            if t2 then
              g:attack(uid, t2.id)
              acted = acted + 1
            end
          end
        end
      end
    end
  end
  return acted
end

return M
