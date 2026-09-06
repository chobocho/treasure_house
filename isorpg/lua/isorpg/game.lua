-- 게임 상태와 틱 — SPEC §12.
--
--   고정 타임스텝(PIT 18.2065 Hz)이라 프레임을 몇 장 그리든 결과가 같다.
--
-- 루아로 옮기며 특히 조심한 곳 둘.
--   (1) 파이썬은 0 이 거짓이지만 루아는 0 도 참이다. alive, in_atk, in_act 처럼
--       0/1 로 쓰는 값은 반드시 ~= 0 으로 비교한다. 이걸 놓치면 죽은 몬스터가
--       계속 얻어맞고, 트레이스가 조용히 갈린다.
--   (2) 파이썬의 None 은 루아의 nil 이다. e.path 는 nil 이거나 비지 않은 배열이고,
--       빈 배열은 루아에서 참이므로 #e.path 로 길이를 따로 본다.
--
-- 배열 규약: ents, boxes, kinds 는 1-기반이다. 다만 상자 id 와 엔티티 eid 는
--   파이썬과 같은 0-기반 값이라 kinds 를 짚을 때 kinds[bid + 1] 로 읽는다.

local CAM = require("isorpg.camera")
local DICE = require("isorpg.dice")
local M2 = require("isorpg.gamemap")
local LOS = require("isorpg.los")
local P = require("isorpg.path")
local PR = require("isorpg.proj")
local RA = require("isorpg.raster")
local SV = require("isorpg.save")
local SD = require("isorpg.sortdag")
local F = require("isorpg.fixed")
local RNG = require("isorpg.rng")

local floor = math.floor
local fp_mul = F.fp_mul
local FP_ONE = F.FP_ONE

local M = {}

M.SPEED = 13107                 -- 한 틱에 0.2타일
M.MON_SPEED = 9830              -- 몬스터는 조금 느리다 (0.15타일)
M.DIAG_FACTOR = 46341           -- round(65536 / sqrt(2))
M.AGGRO_R = 7
M.ATTACK_EVERY = 12
M.PATH_EVERY = 8
M.GAME_SEED = 20260906

M.K_PLAYER, M.K_MON, M.K_CHEST, M.K_NPC = 0, 1, 2, 3

-- 8방향 -> 스프라이트 4방향. [dirn + 1] 로 읽는다.
M.SPRDIR = {0, 0, 1, 1, 3, 3, 2, 2}

M.PLACE_MON = {{20, 20}, {28, 21}, {21, 28}, {27, 27}, {24, 14}, {24, 40}}
M.PLACE_CHEST = {{22, 22}, {26, 26}, {24, 20}}
M.PLACE_NPC = {{23, 25}, {25, 23}}

-- ---------------------------------------------------------------- 엔티티
local Entity = {}
Entity.__index = Entity
M.Entity = Entity

function M.new_entity(eid, kind, tx, ty)
  return setmetatable({
    eid = eid, kind = kind,
    fx = tx * FP_ONE + 32768,                     -- 타일 중앙
    fy = ty * FP_ONE + 32768,
    h = 0, hp = 1, maxhp = 1, lv = 1, xp = 0,
    atk = 0, dfn = 0, armor = 0, dirn = 2, alive = 1,
    anim = 0, cool = 0, path = nil,
  }, Entity)
end

function Entity:tile()
  return floor(self.fx / FP_ONE), floor(self.fy / FP_ONE)
end

-- ---------------------------------------------------------------- 게임
local Game = {}
Game.__index = Game
M.Game = Game

function M.new_game()
  local g = setmetatable({}, Game)
  g.map = M2.gen_map()
  g.rng = RNG.new(M.GAME_SEED)
  g.fog = LOS.new_fog(M2.MAP_W, M2.MAP_H)
  g.tick_n = 0
  g.cycle_breaks = 0
  g.pal_phase = 0
  g.slot = nil
  g.in_dir = -1
  g.in_act = 0
  g.in_atk = 0
  g.ents = {}
  g.log = {}
  g:build_entities()
  local p = g.ents[1]
  local px, py = PR.world_to_screen(p.fx, p.fy, p.h)
  g.cam_x, g.cam_y = CAM.clamp_cam(px - 160, py - 100)
  local ptx, pty = p:tile()
  g.fog:update(g.map, ptx, pty)
  g._frame = nil
  g._sprites = nil
  return g
end

function Game:build_entities()
  local p = M.new_entity(0, M.K_PLAYER, 24, 34)
  p.hp, p.maxhp = 60, 60
  p.atk, p.dfn, p.armor = 4, 3, 2
  self.ents[1] = p
  for k = 0, #M.PLACE_MON - 1 do
    local q = M.PLACE_MON[k + 1]
    local e = M.new_entity(k + 1, M.K_MON, q[1], q[2])
    e.hp, e.maxhp = 8 + k, 8 + k
    e.atk, e.dfn, e.armor = 1, 0, 0
    self.ents[#self.ents + 1] = e
  end
  for k = 1, #M.PLACE_CHEST do
    local q = M.PLACE_CHEST[k]
    self.ents[#self.ents + 1] = M.new_entity(#self.ents, M.K_CHEST, q[1], q[2])
  end
  for k = 1, #M.PLACE_NPC do
    local q = M.PLACE_NPC[k]
    self.ents[#self.ents + 1] = M.new_entity(#self.ents, M.K_NPC, q[1], q[2])
  end
  for i = 1, #self.ents do
    local e = self.ents[i]
    local tx, ty = e:tile()
    e.h = self.map:height(tx, ty)
  end
end

-- ---------------------------------------------------------------- 이동
function Game:can_stand(e, fx, fy)
  local tx, ty = floor(fx / FP_ONE), floor(fy / FP_ONE)
  if not P.passable(self.map, tx, ty) then return false end
  local dh = self.map:height(tx, ty) - e.h
  return dh >= -P.CLIMB_MAX and dh <= P.CLIMB_MAX
end

-- 방향 d 로 한 틱만큼. 막히면 축을 하나씩 떼어 미끄러진다.
-- 도스 RPG 의 조작감은 이 '미끄러짐'에서 온다.
function Game:move_entity(e, d, speed)
  local dx = P.DIRX[d + 1] * speed
  local dy = P.DIRY[d + 1] * speed
  if P.DIAG[d + 1] then
    dx = fp_mul(dx, M.DIAG_FACTOR)
    dy = fp_mul(dy, M.DIAG_FACTOR)
  end
  local nfx = e.fx + dx
  local nfy = e.fy + dy
  local moved = false
  if self:can_stand(e, nfx, nfy) then
    e.fx, e.fy = nfx, nfy
    moved = true
  elseif dx ~= 0 and self:can_stand(e, nfx, e.fy) then
    e.fx = nfx
    moved = true
  elseif dy ~= 0 and self:can_stand(e, e.fx, nfy) then
    e.fy = nfy
    moved = true
  end
  e.dirn = d
  local tx, ty = e:tile()
  e.h = self.map:height(tx, ty)
  if moved then e.anim = e.anim + 1 end
  return moved
end

-- ---------------------------------------------------------------- 전투
function Game:adjacent(a, b)
  local ax, ay = a:tile()
  local bx, by = b:tile()
  local dx = ax - bx
  local dy = ay - by
  return dx >= -1 and dx <= 1 and dy >= -1 and dy <= 1
end

function Game:do_attack(a, b)
  local hit, dmg = DICE.attack(self.rng, a.atk, b.dfn, 1, 6, a.atk, b.armor)
  if not hit then return false end
  b.hp = b.hp - dmg
  if b.hp <= 0 then
    b.hp = 0
    b.alive = 0
    if a.kind == M.K_PLAYER then
      a.xp = a.xp + 20 + 5 * b.maxhp
      while a.xp >= DICE.xp_to_next(a.lv) do
        a.xp = a.xp - DICE.xp_to_next(a.lv)
        a.lv = a.lv + 1
        local v = self.rng:next()
        a.maxhp = a.maxhp + 4 + (v - 5 * floor(v / 5))
        a.hp = a.maxhp
        a.atk = a.atk + 1
        if a.lv - 2 * floor(a.lv / 2) == 0 then a.dfn = a.dfn + 1 end
      end
    end
  end
  return true
end

-- ---------------------------------------------------------------- 한 틱
-- SPEC §12.2 의 순서를 그대로. 순서가 곧 명세다.
function Game:tick()
  local p = self.ents[1]
  -- 1~2. 입력과 플레이어 이동
  if self.in_dir >= 0 then
    self:move_entity(p, self.in_dir, M.SPEED)
  end
  -- 3. 몬스터
  local ptx, pty = p:tile()
  for i = 1, #self.ents do
    local e = self.ents[i]
    if e.kind == M.K_MON and e.alive ~= 0 then
      local etx, ety = e:tile()
      local dx = etx - ptx
      local dy = ety - pty
      local near = dx >= -M.AGGRO_R and dx <= M.AGGRO_R
                   and dy >= -M.AGGRO_R and dy <= M.AGGRO_R
      if not (near and LOS.visible(self.map, etx, ety, ptx, pty)) then
        e.path = nil
      elseif self:adjacent(e, p) then
        if e.cool <= 0 then
          self:do_attack(e, p)
          e.cool = M.ATTACK_EVERY
        else
          e.cool = e.cool - 1
        end
      else
        if e.cool > 0 then e.cool = e.cool - 1 end
        if e.path == nil or self.tick_n - M.PATH_EVERY * floor(self.tick_n / M.PATH_EVERY) == 0 then
          e.path = P.astar(self.map, etx, ety, ptx, pty)
        end
        if e.path ~= nil and #e.path > 1 then
          local nx, ny = e.path[2][1], e.path[2][2]
          local d = -1
          for k = 0, 7 do
            if P.DIRX[k + 1] == nx - etx and P.DIRY[k + 1] == ny - ety then
              d = k
              break
            end
          end
          if d >= 0 then
            self:move_entity(e, d, M.MON_SPEED)
            local ex, ey = e:tile()
            if ex == nx and ey == ny then
              table.remove(e.path, 1)
            end
          end
        end
      end
    end
  end
  -- 4. 플레이어 명령
  if self.in_atk ~= 0 then
    for i = 1, #self.ents do
      local e = self.ents[i]
      if e.kind == M.K_MON and e.alive ~= 0 and self:adjacent(p, e) then
        self:do_attack(p, e)
        break
      end
    end
  end
  if self.in_act ~= 0 then
    for i = 1, #self.ents do
      local e = self.ents[i]
      if e.kind == M.K_CHEST and e.alive ~= 0 and self:adjacent(p, e) then
        e.alive = 0
        p.xp = p.xp + 30
        while p.xp >= DICE.xp_to_next(p.lv) do
          p.xp = p.xp - DICE.xp_to_next(p.lv)
          p.lv = p.lv + 1
          local v = self.rng:next()
          p.maxhp = p.maxhp + 4 + (v - 5 * floor(v / 5))
          p.hp = p.maxhp
          p.atk = p.atk + 1
          if p.lv - 2 * floor(p.lv / 2) == 0 then p.dfn = p.dfn + 1 end
        end
        break
      end
    end
  end
  -- 5. 안개와 조명
  self.fog:update(self.map, ptx, pty)
  -- 6. 카메라
  local sx, sy = PR.world_to_screen(p.fx, p.fy, p.h)
  self.cam_x, self.cam_y = CAM.follow(self.cam_x, self.cam_y, sx, sy)
  -- 7. 틱
  self.tick_n = self.tick_n + 1
  self.pal_phase = floor(self.tick_n / 4)
end

-- ---------------------------------------------------------------- 트레이스
function Game:trace_line()
  local p = self.ents[1]
  local mon = 0
  for i = 1, #self.ents do
    local e = self.ents[i]
    if e.kind == M.K_MON and e.alive ~= 0 then mon = mon + 1 end
  end
  -- 세이브 끝에 붙은 CRC 를 그대로 읽는다. 세이브 전체를 다시 crc16 하면
  -- 언제나 0이 나온다 — CCITT-FALSE 의 성질이라 값으로는 쓸모가 없다.
  local blob = SV.pack_state(self)
  local crc = blob[#blob - 1] * 256 + blob[#blob]
  return string.format(
    '{"t":%d,"px":%d,"py":%d,"ph":%d,"hp":%d,"lv":%d,"xp":%d,' ..
    '"rng":%d,"cam":[%d,%d],"seen":%d,"vis":%d,"mon":%d,"crc":%d}',
    self.tick_n, p.fx, p.fy, p.h, p.hp, p.lv, p.xp, self.rng.s,
    self.cam_x, self.cam_y, self.fog:count_seen(),
    self.fog:count_visible(), mon, crc)
end

local function dir_index(name)
  for i = 1, 8 do
    if P.DIR_NAME[i] == name then return i - 1 end
  end
  error('모르는 방향: ' .. tostring(name))
end

-- 골든 시나리오를 돌린다. emit 이 있으면 매 틱 한 줄씩 넘긴다.
-- limit 은 tick_n 이 아니라 '실제로 돌린 횟수'다 — load 가 시계를 되돌리기 때문이다.
function Game:run_script(path, emit, limit)
  local done = 0
  local text = RA.read_text(path or (RA.golden_dir() .. 'script.txt'))
  for raw in (text .. '\n'):gmatch('([^\n]*)\n') do
    local line = raw:match('^%s*(.-)%s*$')
    if line ~= '' and line:sub(1, 1) ~= '#' then
      local p = {}
      for tok in line:gmatch('%S+') do p[#p + 1] = tok end
      local cmd = p[1]
      local n = nil
      if cmd == 'mark' then
        if emit then
          emit(string.format('{"mark":"%s","t":%d}', p[2], self.tick_n))
        end
      elseif cmd == 'save' then
        self.slot = SV.pack_state(self)
      elseif cmd == 'load' then
        if self.slot ~= nil then SV.unpack_state(self.slot, self) end
      elseif cmd == 'hold' then
        n = tonumber(p[3])
        self.in_dir, self.in_act, self.in_atk = dir_index(p[2]), 0, 0
      elseif cmd == 'wait' then
        n = tonumber(p[2])
        self.in_dir, self.in_act, self.in_atk = -1, 0, 0
      elseif cmd == 'act' then
        n = 1
        self.in_dir, self.in_act, self.in_atk = -1, 1, 0
      elseif cmd == 'atk' then
        n = 1
        self.in_dir, self.in_act, self.in_atk = -1, 0, 1
      else
        error('모르는 명령: ' .. tostring(cmd))
      end
      if n ~= nil then
        for _ = 1, n do
          self:tick()
          done = done + 1
          if emit then emit(self:trace_line()) end
          if limit ~= nil and done >= limit then
            self.in_dir, self.in_act, self.in_atk = -1, 0, 0
            return self
          end
        end
      end
    end
  end
  self.in_dir, self.in_act, self.in_atk = -1, 0, 0
  return self
end

-- ---------------------------------------------------------------- 렌더
function Game:sprites()
  if self._sprites == nil then
    self._sprites = RA.load_sprites()
  end
  return self._sprites
end

-- 정렬에 넣을 상자들. 지형 기둥과 물체를 한 통에 넣는다 —
-- 따로 정렬하면 절벽 뒤에 선 캐릭터가 절벽 위로 뜬다.
function Game:boxes()
  local m = self.map
  local tx0, ty0, tx1, ty1 = PR.visible_range(
    self.cam_x, self.cam_y, self.cam_x + 320, self.cam_y + 200)
  local boxes = {}
  local kinds = {}
  for ty = ty0, ty1 do
    for tx = tx0, tx1 do
      local h = m:height(tx, ty)
      boxes[#boxes + 1] = {#boxes, tx, ty, 0, tx + 1, ty + 1, h + 1}
      kinds[#kinds + 1] = {1, tx, ty}
    end
  end
  for i = 1, #self.ents do
    local e = self.ents[i]
    if not (e.alive == 0 and e.kind == M.K_MON) then
      local tx, ty = e:tile()
      if tx >= tx0 and tx <= tx1 and ty >= ty0 and ty <= ty1 then
        boxes[#boxes + 1] = {#boxes, tx, ty, e.h, tx + 1, ty + 1, e.h + 3}
        kinds[#kinds + 1] = {2, e}
      end
    end
  end
  -- 장식: 숲에는 나무, 바위 지형에는 바위. 좌표만으로 정해 결정적이다.
  for ty = ty0, ty1 do
    for tx = tx0, tx1 do
      local t = m:terrain(tx, ty)
      local h = m:height(tx, ty)
      local a = tx * 7 + ty * 13
      local b = tx * 11 + ty * 5
      if t == M2.T_FOREST and a - 5 * floor(a / 5) == 0 then
        boxes[#boxes + 1] = {#boxes, tx, ty, h, tx + 1, ty + 1, h + 4}
        kinds[#kinds + 1] = {3, 46, tx, ty, h}
      elseif t == M2.T_ROCK and b - 7 * floor(b / 7) == 0 then
        boxes[#boxes + 1] = {#boxes, tx, ty, h, tx + 1, ty + 1, h + 2}
        kinds[#kinds + 1] = {3, 47, tx, ty, h}
      end
    end
  end
  return boxes, kinds
end

-- 한 프레임. 정렬 결과대로 지형 기둥과 물체를 차례로 올린다.
function Game:render()
  local spr = self:sprites()
  local f = self._frame
  if f == nil then
    f = RA.new_frame()
    self._frame = f
  end
  f:clear(0)
  local m = self.map
  local boxes, kinds = self:boxes()
  local order, breaks = SD.topo_sort(boxes)
  self.cycle_breaks = self.cycle_breaks + breaks
  local ptx, pty = self.ents[1]:tile()
  for oi = 1, #order do
    local kind = kinds[order[oi] + 1]
    if kind[1] == 1 then
      local tx, ty = kind[2], kind[3]
      local lv = self.fog:light_of(tx, ty, ptx, pty)
      if lv ~= 0 then
        local t = m:terrain(tx, ty)
        local h = m:height(tx, ty)
        if h == 0 then
          local sx, sy = PR.tile_to_screen(tx, ty, 0)
          f:blit_rle(spr[t + 1], sx - self.cam_x, sy - self.cam_y, lv)
        else
          for k = 1, h do
            local sx, sy = PR.tile_to_screen(tx, ty, k)
            f:blit_rle(spr[16 + t + 1], sx - self.cam_x, sy - self.cam_y, lv)
          end
        end
      end
    elseif kind[1] == 2 then
      local e = kind[2]
      local tx, ty = e:tile()
      local lv = self.fog:light_of(tx, ty, ptx, pty)
      if lv ~= 0 then
        local sx, sy = PR.world_to_screen(e.fx, e.fy, e.h)
        sy = sy + PR.HH
        local sid
        if e.kind == M.K_PLAYER then
          local a = floor(e.anim / 4)
          sid = 32 + M.SPRDIR[e.dirn + 1] * 2 + (a - 2 * floor(a / 2))
        elseif e.kind == M.K_MON then
          local a = floor(self.tick_n / 6) + e.eid
          sid = 40 + (a - 2 * floor(a / 2))
        elseif e.kind == M.K_CHEST then
          sid = e.alive ~= 0 and 42 or 43
        else
          sid = 44 + (e.eid - 2 * floor(e.eid / 2))
        end
        f:blit_rle(spr[sid + 1], sx - self.cam_x, sy - self.cam_y, lv)
      end
    else
      local sid = kind[2]
      local tx, ty, h = kind[3], kind[4], kind[5]
      local lv = self.fog:light_of(tx, ty, ptx, pty)
      if lv ~= 0 then
        local sx, sy = PR.tile_to_screen(tx, ty, h)
        f:blit_rle(spr[sid + 1], sx - self.cam_x, sy + PR.HH - self.cam_y, lv)
      end
    end
  end
  return f.fb
end

function Game:render_ppm()
  local pal = RA.cycle_palette(RA.load_palette(), self.pal_phase)
  return RA.to_ppm(self:render(), pal)
end

function M.run_script_trace(path)
  local g = M.new_game()
  local out = {}
  g:run_script(path, function(s) out[#out + 1] = s end)
  return table.concat(out, '\n') .. '\n'
end

return M
