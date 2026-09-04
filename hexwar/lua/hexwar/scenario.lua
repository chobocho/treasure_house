-- 시나리오 로더 — golden/scenario.txt

local H = require('hexwar.hexcoord')
local hexmap = require('hexwar.hexmap')
local units = require('hexwar.units')

local M = {}

-- 이 파일 기준으로 golden/ 을 찾는다. lua 는 __FILE__ 이 없으므로
-- 호출자가 정해 준 경로(HEXWAR_GOLDEN)를 우선 쓰고, 없으면 상대 경로.
function M.golden_dir()
  return os.getenv('HEXWAR_GOLDEN') or '../golden'
end

function M.parse(text)
  local blocks, cur = {}, nil
  -- 루아 5.4부터 for 의 제어 변수는 상수다. 그래서 지역 변수로 한 번 받는다.
  for raw in (text .. '\n'):gmatch('([^\n]*)\n') do
    local line = (raw:gsub('\r$', ''))
    if line ~= '' and line:sub(1, 1) ~= ';' then
      local name = line:match('^%[(.+)%]$')
      if name then
        cur = name
        blocks[cur] = {}
      else
        if not cur then error('블록 밖의 줄: ' .. line) end
        local t = blocks[cur]
        t[#t + 1] = line
      end
    end
  end
  return blocks
end

function M.load(path)
  path = path or (M.golden_dir() .. '/scenario.txt')
  local f = assert(io.open(path, 'rb'))
  local blocks = M.parse(f:read('a'))
  f:close()

  local terr, elev, road = blocks.terrain, blocks.elev, blocks.road
  if #terr ~= hexmap.MAP_H or #elev ~= hexmap.MAP_H or #road ~= hexmap.MAP_H then
    error('맵 높이가 ' .. hexmap.MAP_H .. ' 이 아니다')
  end

  local m = hexmap.new()
  for row = 0, hexmap.MAP_H - 1 do
    local tl, el, rl = terr[row + 1], elev[row + 1], road[row + 1]
    if #tl ~= hexmap.MAP_W or #el ~= hexmap.MAP_W or #rl ~= hexmap.MAP_W then
      error(row .. '행의 너비가 ' .. hexmap.MAP_W .. ' 이 아니다')
    end
    for col = 0, hexmap.MAP_W - 1 do
      local t = hexmap.CHAR_TO_TERRAIN[tl:sub(col + 1, col + 1)]
      local e = tonumber(el:sub(col + 1, col + 1))
      local rd = rl:sub(col + 1, col + 1) == 'R' and 1 or 0
      m:set_cell(col, row, t, e, rd)
    end
  end

  local pool = units.new_pool()
  for _, line in ipairs(blocks.units) do
    local side, kind, col, row = line:match('(%-?%d+) (%-?%d+) (%-?%d+) (%-?%d+)')
    side, kind, col, row = tonumber(side), tonumber(kind), tonumber(col), tonumber(row)
    local q, r = H.oddr_to_axial(col, row)
    local uid = pool:spawn(side, kind, q, r)
    m.occupant[m:idx(col, row)] = uid
  end

  local objectives = {}
  for _, line in ipairs(blocks.objectives) do
    local col, row = line:match('(%-?%d+) (%-?%d+)')
    local q, r = H.oddr_to_axial(tonumber(col), tonumber(row))
    objectives[#objectives + 1] = { q, r }
  end

  return m, pool, objectives
end

return M
