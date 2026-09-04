-- 게임 상태와 명령 — SPEC §8, §11.3

local combat = require('hexwar.combat')
local hexmap = require('hexwar.hexmap')
local los = require('hexwar.los')
local P = require('hexwar.path')
local rngmod = require('hexwar.rng')
local units = require('hexwar.units')

local M = {}

M.MOVE, M.ATTACK, M.ENDTURN = 0, 1, 2
M.MAX_TURN = 20

local function new_command(kind)
  return {
    kind = kind, unit = -1, frm = -1, to = -1, path = {},
    mp = 0, ent = 0, moved = false, target = -1,
    thp = 0, tammo = 0, ahp = 0, aammo = 0, amp = 0,
    rng_state = 0, killed = {}, log = '', alog = '',
  }
end
M.new_command = new_command

local Game = {}
Game.__index = Game
M.Game = Game

function M.new(m, pool, objectives, seed)
  local self = setmetatable({
    map = m, pool = pool, objectives = objectives,
    rng = rngmod.new(seed or 0x1BADB002),
    turn = 1, side = 0, undo_stack = {}, log = {},
    over = false, winner = -1,
  }, Game)
  los.update_fog(m, pool, 0)
  return self
end

local function unit_name(self, u)
  return units.KINDS[u.kind][2] .. u.id
end

function Game:move_unit(uid, target_idx)
  local u = self.pool:get(uid)
  if not u or u.side ~= self.side or self.over then return nil end
  local reach = P.reachable(self.map, self.pool, u)
  local here = self.map:axial_idx(u.q, u.r)
  if not reach:has(target_idx) or target_idx == here then return nil end

  local cmd = new_command(M.MOVE)
  cmd.unit = uid
  cmd.frm = here
  cmd.to = target_idx
  cmd.path = P.trace_path(self.map, reach, target_idx)
  cmd.mp, cmd.ent, cmd.moved = u.mp, u.ent, u.moved

  local cost = reach.cost[target_idx]
  self.map.occupant[cmd.frm] = units.NO_UNIT
  self.map.occupant[target_idx] = uid
  u.q, u.r = self.map:idx_axial(target_idx)
  u.mp = u.mp - cost
  local zoc = P.zoc_mask(self.map, self.pool, u.side)
  if zoc[target_idx] == 1 then u.mp = 0 end
  u.ent = 0
  u.moved = true
  cmd.log = string.format('%s 이동 %d칸', unit_name(self, u), #cmd.path - 1)
  cmd.alog = string.format('MOVE U%d %d STEP', uid, #cmd.path - 1)
  self:_after_command(cmd)
  return cmd
end

function Game:attack(uid, target_uid)
  local u = self.pool:get(uid)
  local t = self.pool:get(target_uid)
  if not u or not t or u.side ~= self.side or self.over then return nil end
  if not combat.can_attack(self.map, self.pool, u, t) then return nil end

  local cmd = new_command(M.ATTACK)
  cmd.unit = uid
  cmd.target = target_uid
  cmd.frm = self.map:axial_idx(u.q, u.r)
  cmd.mp, cmd.ent, cmd.moved = u.mp, u.ent, u.moved
  cmd.ahp, cmd.aammo, cmd.amp = u.hp, u.ammo, u.mp
  cmd.thp, cmd.tammo = t.hp, t.ammo
  cmd.rng_state = self.rng:save()

  local al, dl, roll, score = combat.resolve(self.map, self.pool, self.rng, u, t)
  cmd.log = string.format('%s → %s  2d6=%d 점수%+d  피해 %d/%d',
    unit_name(self, u), unit_name(self, t), roll, score, dl, al)
  cmd.alog = string.format('ATK U%d>U%d ROLL %d DMG %d/%d', uid, target_uid, roll, dl, al)

  for _, x in ipairs({ t, u }) do
    if x.hp <= 0 then
      local i = self.map:axial_idx(x.q, x.r)
      if i >= 0 and self.map.occupant[i] == x.id then
        self.map.occupant[i] = units.NO_UNIT
      end
      cmd.killed[#cmd.killed + 1] = { x.id, x.side, x.kind, x.q, x.r }
      self.pool:kill(x.id)
    end
  end
  self:_after_command(cmd)
  return cmd
end

function Game:_check_victory_on_end()
  if self.pool:count(1) == 0 then
    self.over, self.winner = true, 0
  elseif self.pool:count(0) == 0 then
    self.over, self.winner = true, 1
  elseif self.side == 0 then
    local held = 0
    for _, o in ipairs(self.objectives) do
      local i = self.map:axial_idx(o[1], o[2])
      local uid = i >= 0 and self.map.occupant[i] or units.NO_UNIT
      local u = self.pool:get(uid)
      if u and u.side == 0 then held = held + 1 end
    end
    if held == #self.objectives then self.over, self.winner = true, 0 end
  end
end

function Game:end_turn()
  local cmd = new_command(M.ENDTURN)
  cmd.log = string.format('%d턴 %s 종료', self.turn, self.side == 0 and '청군' or '적군')
  cmd.alog = string.format('END TURN %d SIDE %d', self.turn, self.side)
  self.undo_stack = {}
  self:_check_victory_on_end()
  if self.over then
    self.log[#self.log + 1] = { cmd.log, cmd.alog }
    return cmd
  end
  self.side = 1 - self.side
  if self.side == 0 then
    self.turn = self.turn + 1
    if self.turn > M.MAX_TURN then
      self.over, self.winner = true, -1
    end
  end
  for _, uid in ipairs(self.pool:alive_ids(self.side)) do
    local u = self.pool:get(uid)
    if not u.moved then u.ent = math.min(3, u.ent + 1) end
    u.mp = units.K_MP[u.kind]
    u.moved = false
  end
  los.update_fog(self.map, self.pool, 0)
  self.log[#self.log + 1] = { cmd.log, cmd.alog }
  return cmd
end

function Game:_revive(uid, side, kind, q, r)
  local u = units.new_unit(uid, side, kind, q, r)
  self.pool.slots[uid] = u
  if self.pool.freehead == uid then
    self.pool.freehead = self.pool.nextfree[uid]
  else
    local prev = self.pool.freehead
    while prev >= 0 and self.pool.nextfree[prev] ~= uid do
      prev = self.pool.nextfree[prev]
    end
    if prev >= 0 then self.pool.nextfree[prev] = self.pool.nextfree[uid] end
  end
  local i = self.map:axial_idx(q, r)
  if i >= 0 then self.map.occupant[i] = uid end
end

function Game:undo()
  local n = #self.undo_stack
  if n == 0 then return false end
  local cmd = self.undo_stack[n]
  self.undo_stack[n] = nil
  if cmd.kind == M.MOVE then
    local u = self.pool:get(cmd.unit)
    self.map.occupant[cmd.to] = units.NO_UNIT
    self.map.occupant[cmd.frm] = cmd.unit
    u.q, u.r = self.map:idx_axial(cmd.frm)
    u.mp, u.ent, u.moved = cmd.mp, cmd.ent, cmd.moved
  elseif cmd.kind == M.ATTACK then
    for _, k in ipairs(cmd.killed) do
      self.pool.slots[k[1]] = false
      self:_revive(k[1], k[2], k[3], k[4], k[5])
    end
    local u = self.pool:get(cmd.unit)
    local t = self.pool:get(cmd.target)
    u.hp, u.ammo, u.mp, u.ent, u.moved = cmd.ahp, cmd.aammo, cmd.amp, cmd.ent, cmd.moved
    t.hp, t.ammo = cmd.thp, cmd.tammo
    self.rng:restore(cmd.rng_state)
  else
    return false
  end
  los.update_fog(self.map, self.pool, 0)
  if #self.log > 0 then self.log[#self.log] = nil end
  return true
end

function Game:_after_command(cmd)
  self.undo_stack[#self.undo_stack + 1] = cmd
  self.log[#self.log + 1] = { cmd.log, cmd.alog }
  los.update_fog(self.map, self.pool, 0)
  self:assert_consistent()
end

function Game:assert_consistent()
  local seen = {}
  for _, uid in ipairs(self.pool:alive_ids()) do
    local u = self.pool:get(uid)
    local i = self.map:axial_idx(u.q, u.r)
    assert(i >= 0, '유닛이 맵 밖에 있다')
    assert(self.map.occupant[i] == u.id, 'occupant 와 유닛 좌표가 어긋났다')
    assert(not seen[i], '한 칸에 유닛 둘')
    seen[i] = true
  end
  for i = 0, self.map.n - 1 do
    local uid = self.map.occupant[i]
    if uid ~= units.NO_UNIT then
      assert(self.pool:get(uid), 'occupant 가 죽은 유닛을 가리킨다')
    end
  end
end

function Game:serialize_units()
  return self.pool:serialize()
end

return M
