-- 시야와 안개 — SPEC §9

local H = require('hexwar.hexcoord')
local hexmap = require('hexwar.hexmap')
local units = require('hexwar.units')

local M = {}

function M.hex_height(m, i)
  local c = m.cells[i]
  return ((c >> 4) & hexmap.ELEV_MASK) + hexmap.T_LOSH[c & hexmap.TERRAIN_MASK]
end

function M.blocks_sight(m, i)
  return hexmap.T_BLOCK[m.cells[i] & hexmap.TERRAIN_MASK] == 1
end

function M.los_clear(m, aq, ar, bq, br)
  local n = H.distance(aq, ar, bq, br)
  if n <= 1 then return true end
  local ia, ib = m:axial_idx(aq, ar), m:axial_idx(bq, br)
  if ia < 0 or ib < 0 then return false end
  local ha = M.hex_height(m, ia) + 1
  local hb = M.hex_height(m, ib)
  local pts = H.line(aq, ar, bq, br)
  for i = 1, n - 1 do
    local p = pts[i + 1]
    local im = m:axial_idx(p[1], p[2])
    if im < 0 then return false end
    local hm = M.hex_height(m, im)
    local line_h = ha * (n - i) + hb * i
    if hm * n > line_h or (M.blocks_sight(m, im) and hm * n >= line_h) then
      return false
    end
  end
  return true
end

function M.visible_hexes(m, u, vis)
  local out = {}
  for _, h in ipairs(H.spiral(u.q, u.r, vis)) do
    local i = m:axial_idx(h[1], h[2])
    if i >= 0 and M.los_clear(m, u.q, u.r, h[1], h[2]) then
      out[#out + 1] = i
    end
  end
  return out
end

function M.update_fog(m, pool, side)
  for i = 0, m.n - 1 do
    if m.fog[i] == hexmap.FOG_VISIBLE then m.fog[i] = hexmap.FOG_EXPLORED end
  end
  for _, uid in ipairs(pool:alive_ids(side)) do
    local u = pool:get(uid)
    for _, i in ipairs(M.visible_hexes(m, u, units.K_VIS[u.kind])) do
      m.fog[i] = hexmap.FOG_VISIBLE
    end
  end
end

return M
