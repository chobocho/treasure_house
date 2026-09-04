-- GUI 셸 — SPEC §11

local H = require('hexwar.hexcoord')
local hexmap = require('hexwar.hexmap')
local P = require('hexwar.path')
local PK = require('hexwar.picker')
local units = require('hexwar.units')

local M = {}

-- 위젯 종류
M.PANEL, M.BUTTON, M.LABEL, M.MINIMAP, M.MAPVIEW, M.LOG, M.DIALOG = 0, 1, 2, 3, 4, 5, 6
-- 상태 기계 (SPEC §11.2)
M.IDLE, M.SELECTED, M.TARGETING, M.DIALOG_ST, M.GAMEOVER = 0, 1, 2, 3, 4
M.STATE_NAMES = { [0] = 'IDLE', 'SELECTED', 'TARGETING', 'DIALOG', 'GAMEOVER' }

-- 화면 배치 상수는 렌더러와 공유한다
M.VIEW = { 0, 0, 256, 168 }
M.PANEL_R = { 256, 0, 64, 200 }
M.MSG = { 0, 168, 256, 32 }

local function widget(id, x, y, w, h, kind, label, children)
  return { id = id, x = x, y = y, w = w, h = h, kind = kind,
           label = label or '', enabled = true, visible = true, children = children or {} }
end
M.widget = widget

function M.build_ui()
  local minimap = widget('minimap', M.PANEL_R[1] + 6, 24, 48, 36, M.MINIMAP)
  local btn_end = widget('end', M.PANEL_R[1] + 4, 150, 56, 12, M.BUTTON, 'END TURN')
  local btn_undo = widget('undo', M.PANEL_R[1] + 4, 164, 56, 12, M.BUTTON, 'UNDO')
  local btn_next = widget('next', M.PANEL_R[1] + 4, 178, 56, 12, M.BUTTON, 'NEXT UNIT')
  local panel = widget('panel', M.PANEL_R[1], M.PANEL_R[2], M.PANEL_R[3], M.PANEL_R[4],
                       M.PANEL, '', { minimap, btn_end, btn_undo, btn_next })
  local mapview = widget('map', M.VIEW[1], M.VIEW[2], M.VIEW[3], M.VIEW[4], M.MAPVIEW)
  local logw = widget('log', M.MSG[1], M.MSG[2], M.MSG[3], M.MSG[4], M.LOG)
  local yes = widget('yes', 100, 112, 40, 14, M.BUTTON, 'YES')
  local no = widget('no', 180, 112, 40, 14, M.BUTTON, 'NO')
  local dlg = widget('dialog', 80, 74, 160, 56, M.DIALOG, 'END TURN?', { yes, no })
  dlg.visible = false
  return widget('root', 0, 0, 320, 200, M.PANEL, '', { mapview, logw, panel, dlg })
end

local function contains(w, px, py)
  return px >= w.x and px < w.x + w.w and py >= w.y and py < w.y + w.h
end

function M.hit_test(w, px, py)
  if not w.visible or not contains(w, px, py) then return nil end
  for i = #w.children, 1, -1 do
    local hit = M.hit_test(w.children[i], px, py)
    if hit then return hit end
  end
  if w.enabled then return w end
  return nil
end

local Ui = {}
Ui.__index = Ui
M.Ui = Ui

function M.new(g)
  local obj = {}
  for _, o in ipairs(g.objectives) do
    obj[g.map:axial_idx(o[1], o[2])] = true
  end
  return setmetatable({
    g = g, root = M.build_ui(), state = M.IDLE, prev_state = M.IDLE,
    cam_x = 0, cam_y = 0, cursor_idx = -1, sel_idx = -1, sel_unit = -1,
    move_overlay = {}, move_n = 0, attack_overlay = {}, attack_n = 0,
    reach = nil, objective_idx = obj,
  }, Ui)
end

function Ui:state_name() return M.STATE_NAMES[self.state] end

function Ui:ascii_log(g, n)
  local out = {}
  local total = #g.log
  for i = total, math.max(1, total - n + 1), -1 do
    out[#out + 1] = g.log[i][2]
  end
  return out
end

function Ui:clamp_cam()
  local render = require('hexwar.render')
  if self.cam_x < 0 then self.cam_x = 0 end
  if self.cam_y < 0 then self.cam_y = 0 end
  if self.cam_x > render.CAM_MAX_X then self.cam_x = render.CAM_MAX_X end
  if self.cam_y > render.CAM_MAX_Y then self.cam_y = render.CAM_MAX_Y end
end

function Ui:scroll(dx, dy)
  self.cam_x = self.cam_x + dx
  self.cam_y = self.cam_y + dy
  self:clamp_cam()
end

function Ui:center_on(idx)
  local row = idx // hexmap.MAP_W
  local col = idx - row * hexmap.MAP_W
  local cx, cy = PK.hex_center(col, row)
  self.cam_x = cx - M.VIEW[3] // 2
  self.cam_y = cy - M.VIEW[4] // 2
  self:clamp_cam()
end

function Ui:_attack_targets(u)
  local out, n = {}, 0
  if u.ammo <= 0 or u.mp <= 0 then return out, n end
  local m = self.g.map
  for _, tid in ipairs(self.g.pool:alive_ids()) do
    local t = self.g.pool:get(tid)
    if t.side ~= u.side then
      local i = m:axial_idx(t.q, t.r)
      if i >= 0 and m.fog[i] == hexmap.FOG_VISIBLE
          and H.distance(u.q, u.r, t.q, t.r) <= units.K_RNG[u.kind] then
        out[i] = true
        n = n + 1
      end
    end
  end
  return out, n
end

function Ui:select(uid)
  local u = self.g.pool:get(uid)
  if not u or u.side ~= self.g.side then return false end
  self.sel_unit = uid
  self.sel_idx = self.g.map:axial_idx(u.q, u.r)
  self.reach = P.reachable(self.g.map, self.g.pool, u)
  local mv, n = {}, 0
  for _, i in ipairs(self.reach.list) do
    if i ~= self.sel_idx and self.g.map.occupant[i] == units.NO_UNIT then
      mv[i] = true
      n = n + 1
    end
  end
  self.move_overlay, self.move_n = mv, n
  self.attack_overlay, self.attack_n = self:_attack_targets(u)
  self.state = M.SELECTED
  return true
end

function Ui:deselect()
  self.sel_unit = -1
  self.sel_idx = -1
  self.reach = nil
  self.move_overlay, self.move_n = {}, 0
  self.attack_overlay, self.attack_n = {}, 0
  self.state = M.IDLE
end

function Ui:next_unit()
  local ids = {}
  for _, uid in ipairs(self.g.pool:alive_ids(self.g.side)) do
    if self.g.pool:get(uid).mp > 0 then ids[#ids + 1] = uid end
  end
  if #ids == 0 then return false end
  local nxt = ids[1]
  for k, v in ipairs(ids) do
    if v == self.sel_unit then
      nxt = ids[(k % #ids) + 1]
      break
    end
  end
  if self:select(nxt) then
    self:center_on(self.sel_idx)
    return true
  end
  return false
end

function Ui:handle(ev)
  local kind, a, b = ev:match('^(%a+)%s*(%-?%w*)%s*(%-?%w*)$')
  if kind == 'click' then return self:on_click(tonumber(a), tonumber(b)) end
  if kind == 'key' then return self:on_key(a) end
  if kind == 'render' then return true end
  error('알 수 없는 이벤트: ' .. ev)
end

function Ui:on_click(x, y)
  local w = M.hit_test(self.root, x, y)
  if not w then return false end
  if self.state == M.DIALOG_ST then
    if w.id == 'yes' then
      self:close_dialog()
      self.g:end_turn()
      self:after_turn()
      return true
    elseif w.id == 'no' then
      self:close_dialog()
      return true
    end
    return false
  end
  if w.kind == M.BUTTON then return self:on_button(w.id) end
  if w.id == 'minimap' then return self:on_minimap(x, y, w) end
  if w.kind == M.MAPVIEW then return self:on_map_click(x, y) end
  return false
end

function Ui:on_button(wid)
  if wid == 'end' then
    self:open_dialog()
    return true
  elseif wid == 'undo' then
    local ok = self.g:undo()
    if ok and self.sel_unit >= 0 then
      if not self.g.pool:get(self.sel_unit) then
        self:deselect()
      else
        self:select(self.sel_unit)
      end
    end
    return ok
  elseif wid == 'next' then
    return self:next_unit()
  end
  return false
end

function Ui:on_minimap(x, y, w)
  local col = math.max(0, math.min(hexmap.MAP_W - 1, (x - w.x) // 2))
  local row = math.max(0, math.min(hexmap.MAP_H - 1, (y - w.y) // 2))
  self:center_on(row * hexmap.MAP_W + col)
  return true
end

function Ui:on_map_click(x, y)
  local col, row = PK.pick(x, y, self.cam_x, self.cam_y)
  if col == nil then return false end
  local i = row * hexmap.MAP_W + col
  self.cursor_idx = i
  local m = self.g.map
  local uid = m.occupant[i]

  if self.state == M.TARGETING then
    if self.attack_overlay[i] and uid ~= units.NO_UNIT then
      self.g:attack(self.sel_unit, uid)
      self:after_action()
      return true
    end
    self.state = M.SELECTED
    return false
  end

  if self.state == M.SELECTED then
    if self.attack_overlay[i] and uid ~= units.NO_UNIT then
      self.g:attack(self.sel_unit, uid)
      self:after_action()
      return true
    end
    if self.move_overlay[i] then
      self.g:move_unit(self.sel_unit, i)
      self:after_action()
      return true
    end
  end

  if uid ~= units.NO_UNIT and m.fog[i] == hexmap.FOG_VISIBLE then
    local u = self.g.pool:get(uid)
    if u and u.side == self.g.side then return self:select(uid) end
  end
  self:deselect()
  return true
end

function Ui:on_key(k)
  if self.state == M.DIALOG_ST then
    if k == 'ESC' then
      self:close_dialog()
      return true
    elseif k == 'ENTER' then
      self:close_dialog()
      self.g:end_turn()
      self:after_turn()
      return true
    end
    return false
  end
  if k == 'LEFT' then self:scroll(-PK.HEX_W, 0)
  elseif k == 'RIGHT' then self:scroll(PK.HEX_W, 0)
  elseif k == 'UP' then self:scroll(0, -PK.ROW_STEP)
  elseif k == 'DOWN' then self:scroll(0, PK.ROW_STEP)
  elseif k == 'TAB' then return self:next_unit()
  elseif k == 'U' then return self:on_button('undo')
  elseif k == 'E' then self:open_dialog()
  elseif k == 'T' then
    if self.state == M.SELECTED and self.attack_n > 0 then
      self.state = M.TARGETING
    else
      return false
    end
  elseif k == 'ESC' then
    if self.state == M.TARGETING then
      self.state = M.SELECTED
    else
      self:deselect()
    end
  else
    return false
  end
  return true
end

function Ui:_dlg()
  for _, c in ipairs(self.root.children) do
    if c.id == 'dialog' then return c end
  end
  error('dialog')
end

function Ui:open_dialog()
  self.prev_state = self.state
  self.state = M.DIALOG_ST
  self:_dlg().visible = true
end

function Ui:close_dialog()
  self:_dlg().visible = false
  self.state = self.prev_state
end

function Ui:after_action()
  local u = self.g.pool:get(self.sel_unit)
  if self.g.over then
    self.state = M.GAMEOVER
    self.move_overlay, self.move_n = {}, 0
    self.attack_overlay, self.attack_n = {}, 0
    return
  end
  if not u or (u.mp <= 0 and u.ammo <= 0) then
    self:deselect()
  else
    self:select(self.sel_unit)
  end
end

function Ui:after_turn()
  self:deselect()
  if self.g.over then self.state = M.GAMEOVER end
end

function Ui:digest()
  return string.format('%s|sel=%d|cur=%d|cam=%d,%d|mov=%d|atk=%d',
    self:state_name(), self.sel_unit, self.cursor_idx,
    self.cam_x, self.cam_y, self.move_n, self.attack_n)
end

return M
