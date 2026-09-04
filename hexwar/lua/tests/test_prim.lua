-- 골든 프리미티브 대조 (루아) — golden/prim.txt 를 파이썬판과 같은 순서로 읽는다.

package.path = './?.lua;' .. package.path

local H = require('hexwar.hexcoord')
local hexmap = require('hexwar.hexmap')
local PK = require('hexwar.picker')
local R = require('hexwar.rng')

local fails = {}

local function eq(name, got, want)
  if got ~= want then
    fails[#fails + 1] = string.format('%s: got %s want %s', name, tostring(got), tostring(want))
  end
end

-- got 을 want[from..] 과 견준다. n 을 주면 그만큼만, 안 주면 끝까지 같아야 한다.
local function eqlist(name, got, want, from, n)
  from = from or 1
  if n == nil and #got ~= (#want - from + 1) then
    fails[#fails + 1] = string.format('%s: 길이 %d != %d', name, #got, #want - from + 1)
    return
  end
  if n ~= nil and #got ~= n then
    fails[#fails + 1] = string.format('%s: 길이 %d != %d', name, #got, n)
    return
  end
  for i = 1, #got do
    if got[i] ~= want[from + i - 1] then
      fails[#fails + 1] = string.format('%s: [%d] %d != %d', name, i, got[i], want[from + i - 1])
      return
    end
  end
end

local function unhex(s)
  if s == '-' then return '' end
  local out = {}
  for i = 1, #s, 2 do out[#out + 1] = string.char(tonumber(s:sub(i, i + 1), 16)) end
  return table.concat(out)
end

local path = (os.getenv('HEXWAR_GOLDEN') or '../golden') .. '/prim.txt'
local nline = 0
for line in io.lines(path) do
  if line ~= '' and line:sub(1, 1) ~= ';' then
    nline = nline + 1
    local parts = {}
    for w in line:gmatch('%S+') do parts[#parts + 1] = w end
    local key = parts[1]
    if key == 'fnv' then
      eq('fnv ' .. parts[2], R.fnv1a(unhex(parts[2])), tonumber(parts[3]))
    else
      local v = {}
      for i = 2, #parts do v[i - 1] = tonumber(parts[i]) end
      if key == 'dirs' then
        local got = {}
        for d = 0, 5 do got[#got + 1] = H.DIRS[d][1]; got[#got + 1] = H.DIRS[d][2] end
        eqlist('dirs', got, v)
      elseif key == 'oddr' then
        local c, r = H.axial_to_oddr(v[1], v[2])
        eqlist('axial_to_oddr', { c, r }, v, 3)
        local q, rr = H.oddr_to_axial(v[3], v[4])
        eqlist('oddr_to_axial', { q, rr }, v, 1, 2)
      elseif key == 'oddq' then
        local c, r = H.axial_to_oddq(v[1], v[2])
        eqlist('axial_to_oddq', { c, r }, v, 3)
        local q, rr = H.oddq_to_axial(v[3], v[4])
        eqlist('oddq_to_axial', { q, rr }, v, 1, 2)
      elseif key == 'dist' then
        eq('distance', H.distance(v[1], v[2], v[3], v[4]), v[5])
      elseif key == 'neighbors' then
        local got = {}
        for _, h in ipairs(H.neighbors(v[1], v[2])) do
          got[#got + 1] = h[1]; got[#got + 1] = h[2]
        end
        eqlist('neighbors', got, v, 3)
      elseif key == 'ring' then
        local got = {}
        for _, h in ipairs(H.ring(0, 0, v[1])) do got[#got + 1] = h[1]; got[#got + 1] = h[2] end
        eqlist('ring' .. v[1], got, v, 2)
      elseif key == 'spiral' then
        eq('spiral' .. v[1], #H.spiral(0, 0, v[1]), v[2])
      elseif key == 'line' then
        local hexes = H.line(v[1], v[2], v[3], v[4])
        local got = { #hexes }
        for _, h in ipairs(hexes) do got[#got + 1] = h[1]; got[#got + 1] = h[2] end
        eqlist('line', got, v, 5)
      elseif key == 'pick' then
        local col, row = PK.pick(v[1], v[2], v[3], v[4])
        eqlist('pick', { col or -1, row or -1 }, v, 5)
      elseif key == 'lcg' then
        local st = R.new(v[1])
        local got = {}
        for i = 2, #v do got[#got + 1] = st:next() end
        eqlist('lcg', got, v, 2)
      elseif key == 'd6' then
        local st = R.new(0x1BADB002)
        local got = {}
        for i = 1, #v do got[#got + 1] = st:d6() end
        eqlist('d6', got, v)
      elseif key == 'cell' then
        eq('pack', hexmap.pack_cell(v[1], v[2], v[3]), v[4])
        eqlist('unpack', { hexmap.cell_terrain(v[4]), hexmap.cell_elev(v[4]),
                           hexmap.cell_road(v[4]) }, v, 1, 3)
      else
        fails[#fails + 1] = '알 수 없는 키: ' .. key
      end
    end
  end
end

-- 마스크 표가 golden/pick_mask.txt 와 같은지도 본다
do
  local oy = 0
  for line in io.lines((os.getenv('HEXWAR_GOLDEN') or '../golden') .. '/pick_mask.txt') do
    if line ~= '' then
      for ox = 0, 31 do
        eq(string.format('mask[%d][%d]', oy, ox),
           PK.PICK_MASK[oy * 32 + ox], tonumber(line:sub(ox + 1, ox + 1)))
      end
      oy = oy + 1
    end
  end
  eq('mask 행 수', oy, 24)
end

if #fails > 0 then
  print(string.format('FAIL %d / %d줄', #fails, nline))
  for i = 1, math.min(20, #fails) do print('  ' .. fails[i]) end
  os.exit(1)
end
print(string.format('prim OK (lua) — %d줄 + 마스크 768칸 전부 일치', nline))
