-- 렌더링 — SPEC §10
--
-- 프레임버퍼는 0..63999 인덱스의 정수 테이블이다. 파이썬의 bytearray 나
-- 타입스크립트의 Uint8Array 와 달리 루아 테이블은 값마다 태그가 붙은 64비트
-- 슬롯이라 메모리는 훨씬 크다. 대신 코드는 같다 — 도스식 '한 바이트 = 한
-- 픽셀' 모델이 언어와 무관하게 성립한다는 것을 보여 주는 자리다.

local F = require('hexwar.font')
local hexmap = require('hexwar.hexmap')
local PK = require('hexwar.picker')
local rngmod = require('hexwar.rng')
local units = require('hexwar.units')

local M = {}

M.SCR_W, M.SCR_H = 320, 200
M.VIEW = { 0, 0, 256, 168 }
M.PANEL = { 256, 0, 64, 200 }
M.MSG = { 0, 168, 256, 32 }

M.MAP_PX_W = hexmap.MAP_W * PK.HEX_W + PK.ODD_SHIFT
M.MAP_PX_H = hexmap.MAP_H * PK.ROW_STEP + (PK.HEX_H - PK.ROW_STEP)
M.CAM_MAX_X = math.max(0, M.MAP_PX_W - M.VIEW[3])
M.CAM_MAX_Y = math.max(0, M.MAP_PX_H - M.VIEW[4])

M.TILE_NAME = { [0] = 't_clear', 't_forest', 't_hill', 't_mountain',
                't_city', 't_river', 't_swamp', 't_sea' }
M.MINI_COLOR = { [0] = 24, 38, 56, 72, 120, 88, 104, 84 }

local function golden_dir()
  return os.getenv('HEXWAR_GOLDEN') or '../golden'
end

function M.load_palette(path)
  path = path or (golden_dir() .. '/palette.txt')
  local pal = {}
  local i = 0
  for line in io.lines(path) do
    local r, g, b = line:match('(%d+) (%d+) (%d+)')
    if r then
      pal[i] = { tonumber(r), tonumber(g), tonumber(b) }
      i = i + 1
    end
  end
  return pal
end

function M.load_sprites(path)
  path = path or (golden_dir() .. '/tiles.rle')
  local sprites = {}
  local name, w, h, buf, need, pos = nil, 0, 0, nil, 0, 0
  for line in io.lines(path) do
    if line ~= '' and line:sub(1, 1) ~= ';' then
      if need == 0 then
        local n, ws, hs = line:match('(%S+) (%d+) (%d+)')
        name, w, h = n, tonumber(ws), tonumber(hs)
        buf, need, pos = {}, w * h, 0
      else
        -- for 의 제어 변수는 상수이므로 지역 변수로 받아 쓴다(루아 5.4+)
        for cs, vs in line:gmatch('(%d+) (%d+)') do
          local cnt, val = tonumber(cs), tonumber(vs)
          for _ = 1, cnt do
            buf[pos] = val
            pos = pos + 1
          end
          need = need - cnt
        end
        if need == 0 then
          sprites[name] = { w = w, h = h, data = buf }
        end
      end
    end
  end
  return sprites
end

-- 프레임버퍼 -----------------------------------------------------------------
local FB = {}
FB.__index = FB
M.FB = FB

function M.new_fb(w, h)
  w = w or M.SCR_W
  h = h or M.SCR_H
  local d = {}
  for i = 0, w * h - 1 do d[i] = 0 end
  return setmetatable({ w = w, h = h, data = d }, FB)
end

function FB:clear(v)
  v = v or 0
  for i = 0, self.w * self.h - 1 do self.data[i] = v end
end

function FB:fill_rect(x, y, w, h, v)
  local x0 = math.max(0, x)
  local y0 = math.max(0, y)
  local x1 = math.min(self.w, x + w)
  local y1 = math.min(self.h, y + h)
  for yy = y0, y1 - 1 do
    local base = yy * self.w
    for xx = x0, x1 - 1 do self.data[base + xx] = v end
  end
end

function FB:frame_rect(x, y, w, h, v)
  self:fill_rect(x, y, w, 1, v)
  self:fill_rect(x, y + h - 1, w, 1, v)
  self:fill_rect(x, y, 1, h, v)
  self:fill_rect(x + w - 1, y, 1, h, v)
end

function FB:blit(sp, x, y, clip)
  local cx, cy, cw, ch = 0, 0, self.w, self.h
  if clip then cx, cy, cw, ch = clip[1], clip[2], clip[3], clip[4] end
  local x0 = math.max(x, cx)
  local y0 = math.max(y, cy)
  local x1 = math.min(x + sp.w, cx + cw)
  local y1 = math.min(y + sp.h, cy + ch)
  if x0 >= x1 or y0 >= y1 then return end
  local src, dst = sp.data, self.data
  for yy = y0, y1 - 1 do
    local srow = (yy - y) * sp.w - x
    local drow = yy * self.w
    for xx = x0, x1 - 1 do
      local v = src[srow + xx]
      if v ~= 0 then dst[drow + xx] = v end
    end
  end
end

function FB:text(s, x, y, color, clip)
  local cx, cy, cw, ch = 0, 0, self.w, self.h
  if clip then cx, cy, cw, ch = clip[1], clip[2], clip[3], clip[4] end
  for k = 1, #s do
    local gx = x + (k - 1) * F.ADV
    local rows = F.rows(s:sub(k, k))
    for ry = 0, F.FH - 1 do
      local bits = rows[ry]
      if bits ~= 0 then
        local py = y + ry
        if py >= cy and py < cy + ch then
          local base = py * self.w
          for bx = 0, F.FW - 1 do
            if (bits & (1 << (F.FW - 1 - bx))) ~= 0 then
              local px = gx + bx
              if px >= cx and px < cx + cw then self.data[base + px] = color end
            end
          end
        end
      end
    end
  end
end

function FB:to_ppm(pal)
  local lut = {}
  for i = 0, 255 do
    local c = pal[i] or { 0, 0, 0 }
    lut[i] = string.char(c[1] * 255 // 63, c[2] * 255 // 63, c[3] * 255 // 63)
  end
  local parts = { string.format('P6\n%d %d\n255\n', self.w, self.h) }
  local n = self.w * self.h
  local chunk, ci = {}, 0
  for i = 0, n - 1 do
    ci = ci + 1
    chunk[ci] = lut[self.data[i]]
    if ci == 4096 then
      parts[#parts + 1] = table.concat(chunk)
      chunk, ci = {}, 0
    end
  end
  if ci > 0 then parts[#parts + 1] = table.concat(chunk, '', 1, ci) end
  return table.concat(parts)
end

-- 렌더러 ---------------------------------------------------------------------
local Renderer = {}
Renderer.__index = Renderer
M.Renderer = Renderer

function M.new_renderer()
  return setmetatable({ fb = M.new_fb(), pal = M.load_palette(), sp = M.load_sprites() }, Renderer)
end

function Renderer:visible_rows(cam_y)
  local top = (cam_y - (PK.HEX_H - PK.ROW_STEP)) // PK.ROW_STEP
  local bot = (cam_y + M.VIEW[4]) // PK.ROW_STEP + 1
  return math.max(0, top), math.min(hexmap.MAP_H - 1, bot)
end

function Renderer:draw_roads(m, i, x, y)
  local nb, k = m:neighbors_with_dir(i)
  for j = 1, k do
    local d, ni = nb[j][1], nb[j][2]
    if (m.cells[ni] & 0x80) ~= 0 then
      self.fb:blit(self.sp['road' .. d], x, y, M.VIEW)
    end
  end
end

function Renderer:draw_unit(u, x, y)
  self.fb:blit(self.sp[string.format('u%d_%d', u.side, u.kind)], x + 8, y + 8, M.VIEW)
  local w = math.max(0, u.hp * 12 // 10)
  self.fb:fill_rect(x + 10, y + 25, 12, 2, 8)
  self.fb:fill_rect(x + 10, y + 25, w, 2, u.hp > 5 and 10 or 12)
end

function Renderer:draw_map(g, ui)
  local fb, m = self.fb, g.map
  local camx, camy = ui.cam_x, ui.cam_y
  fb:fill_rect(M.VIEW[1], M.VIEW[2], M.VIEW[3], M.VIEW[4], 0)
  local r0, r1 = self:visible_rows(camy)
  for row = r0, r1 do
    for col = 0, hexmap.MAP_W - 1 do
      local ox, oy = PK.hex_origin(col, row)
      local x, y = ox - camx, oy - camy
      if not (x <= -PK.HEX_W or x >= M.VIEW[3] or y <= -PK.HEX_H or y >= M.VIEW[4]) then
        local i = row * hexmap.MAP_W + col
        local fog = m.fog[i]
        if fog == hexmap.FOG_HIDDEN then
          fb:blit(self.sp.ov_black, x, y, M.VIEW)
        else
          local t = m.cells[i] & hexmap.TERRAIN_MASK
          fb:blit(self.sp[M.TILE_NAME[t]], x, y, M.VIEW)
          if (m.cells[i] & 0x80) ~= 0 then self:draw_roads(m, i, x, y) end
          if fog == hexmap.FOG_EXPLORED then
            fb:blit(self.sp.ov_dim, x, y, M.VIEW)
          else
            if ui.objective_idx[i] then fb:blit(self.sp.ov_obj, x, y, M.VIEW) end
            if ui.move_overlay[i] then fb:blit(self.sp.ov_move, x, y, M.VIEW) end
            if ui.attack_overlay[i] then fb:blit(self.sp.ov_attack, x, y, M.VIEW) end
            local uid = m.occupant[i]
            if uid ~= units.NO_UNIT then
              local u = g.pool:get(uid)
              if u then self:draw_unit(u, x, y) end
            end
            if ui.sel_idx == i then fb:blit(self.sp.ov_sel, x, y, M.VIEW) end
            if ui.cursor_idx == i then fb:blit(self.sp.ov_cursor, x, y, M.VIEW) end
          end
        end
      end
    end
  end
end

function Renderer:draw_minimap(g, ui, x, y)
  local m = g.map
  for row = 0, hexmap.MAP_H - 1 do
    for col = 0, hexmap.MAP_W - 1 do
      local i = row * hexmap.MAP_W + col
      local v
      if m.fog[i] == hexmap.FOG_HIDDEN then
        v = 0
      else
        v = M.MINI_COLOR[m.cells[i] & hexmap.TERRAIN_MASK]
        local uid = m.occupant[i]
        if uid ~= units.NO_UNIT and m.fog[i] ~= hexmap.FOG_EXPLORED then
          local u = g.pool:get(uid)
          if u then v = (u.side == 1) and 155 or 170 end
        end
      end
      self.fb:fill_rect(x + col * 2, y + row * 2, 2, 2, v)
    end
  end
  local vx = x + ui.cam_x * 2 // PK.HEX_W
  local vy = y + ui.cam_y * 2 // PK.ROW_STEP
  self.fb:frame_rect(vx, vy, M.VIEW[3] * 2 // PK.HEX_W, M.VIEW[4] * 2 // PK.ROW_STEP, 15)
end

function Renderer:draw_panel(g, ui)
  local fb = self.fb
  local px, py, pw, ph = M.PANEL[1], M.PANEL[2], M.PANEL[3], M.PANEL[4]
  fb:fill_rect(px, py, pw, ph, 8)
  fb:frame_rect(px, py, pw, ph, 7)
  fb:text('TURN ' .. g.turn, px + 4, py + 4, 15)
  fb:text('SIDE ' .. g.side, px + 4, py + 13, 15)
  self:draw_minimap(g, ui, px + 6, py + 24)
  local u = ui.sel_unit >= 0 and g.pool:get(ui.sel_unit) or nil
  local ty = py + 70
  if u then
    fb:text(units.KINDS[u.kind][1], px + 4, ty, 14)
    fb:text('HP ' .. u.hp, px + 4, ty + 10, 15)
    fb:text('MP ' .. u.mp, px + 4, ty + 19, 15)
    fb:text('AM ' .. u.ammo, px + 4, ty + 28, 15)
    fb:text('EN ' .. u.ent, px + 4, ty + 37, 15)
  else
    fb:text('NO UNIT', px + 4, ty, 7)
  end
  fb:text(ui:state_name(), px + 4, py + 136, 11)
end

function Renderer:draw_msg(g, ui)
  local fb = self.fb
  local mx, my, mw, mh = M.MSG[1], M.MSG[2], M.MSG[3], M.MSG[4]
  fb:fill_rect(mx, my, mw, mh, 0)
  fb:frame_rect(mx, my, mw, mh, 7)
  local lines = ui:ascii_log(g, 3)
  for i = 1, #lines do
    fb:text(lines[i]:sub(1, 41), mx + 3, my + 4 + (i - 1) * 9, (i == 1) and 15 or 7, M.MSG)
  end
end

function Renderer:draw_widgets(ui)
  local uimod = require('hexwar.ui')
  local queue = { ui.root }
  local qi = 1
  while qi <= #queue do
    local w = queue[qi]
    qi = qi + 1
    if w.visible then
      if w.kind == uimod.BUTTON then
        local on = w.enabled
        self.fb:fill_rect(w.x, w.y, w.w, w.h, on and 7 or 8)
        self.fb:frame_rect(w.x, w.y, w.w, w.h, on and 15 or 7)
        self.fb:text(w.label, w.x + 3, w.y + 3, on and 0 or 8)
      elseif w.kind == uimod.DIALOG then
        self.fb:fill_rect(w.x + 4, w.y + 4, w.w, w.h, 0)
        self.fb:fill_rect(w.x, w.y, w.w, w.h, 8)
        self.fb:frame_rect(w.x, w.y, w.w, w.h, 15)
        self.fb:frame_rect(w.x + 2, w.y + 2, w.w - 4, w.h - 4, 7)
        self.fb:text(w.label, w.x + 12, w.y + 14, 15)
      end
      for _, c in ipairs(w.children) do queue[#queue + 1] = c end
    end
  end
end

function Renderer:draw(g, ui)
  self:draw_map(g, ui)
  self:draw_panel(g, ui)
  self:draw_msg(g, ui)
  self:draw_widgets(ui)
  return self.fb
end

function Renderer:frame_hash()
  return rngmod.fnv1a(self.fb:to_ppm(self.pal))
end

return M
