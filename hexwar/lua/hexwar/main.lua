-- 명령줄 진입점 — 파이썬판과 같은 하위 명령을 가진다.
--
--   lua hexwar/main.lua trace           골든 트레이스를 표준출력으로
--   lua hexwar/main.lua render out.ppm  한 프레임을 PPM 으로
--   lua hexwar/main.lua bench           간단한 성능 측정

-- 이 파일은 모듈이면서 스크립트다. require 로 불리면 인자로 모듈 이름이 오고,
-- 직접 실행되면 명령줄 인자가 온다 — 그 차이로 '메인인지'를 판별한다.
local ENTRY = ...

local ai = require('hexwar.ai')
local G = require('hexwar.game')
local render = require('hexwar.render')
local rngmod = require('hexwar.rng')
local scenario = require('hexwar.scenario')
local uimod = require('hexwar.ui')

local M = {}

local function golden_dir()
  return os.getenv('HEXWAR_GOLDEN') or '../golden'
end

function M.load_script(path)
  path = path or (golden_dir() .. '/script.txt')
  local evs = {}
  for line in io.lines(path) do
    local s = line:match('^%s*(.-)%s*$')
    if s ~= '' and s:sub(1, 1) ~= ';' then evs[#evs + 1] = s end
  end
  return evs
end

-- JSON 한 줄. 파이썬의 json.dumps(sort_keys=True, separators=(',',':')) 와
-- 바이트 단위로 같아야 하므로 키 순서를 사전순으로 못 박는다.
-- ('fbHash' 가 'fogHash' 보다 앞인 것은 대문자 B(0x42)가 소문자 o 보다 작아서가
--  아니라 두 번째 글자 b < o 때문이다 — 사전순은 바이트 비교다.)
local function json_line(d)
  local parts = {}
  local function s(k, v) parts[#parts + 1] = string.format('"%s":"%s"', k, v) end
  local function n(k, v) parts[#parts + 1] = string.format('"%s":%d', k, v) end
  s('ev', d.ev)
  if d.fbHash then s('fbHash', d.fbHash) end
  s('fogHash', d.fogHash)
  n('rng', d.rng)
  n('sel', d.sel)
  n('side', d.side)
  s('state', d.state)
  n('step', d.step)
  n('turn', d.turn)
  s('ui', d.ui)
  s('unitHash', d.unitHash)
  return '{' .. table.concat(parts, ',') .. '}'
end

function M.digest_state(g, ui, r, with_frame)
  local d = {
    state = ui:state_name(),
    sel = ui.sel_unit,
    turn = g.turn,
    side = g.side,
    rng = g.rng:save(),
    unitHash = rngmod.hex8(rngmod.fnv1a(g:serialize_units())),
    fogHash = rngmod.hex8(rngmod.fnv1a(g.map:fog_text())),
    ui = ui:digest(),
  }
  if with_frame and r then
    r:draw(g, ui)
    d.fbHash = rngmod.hex8(rngmod.fnv1a(r.fb:to_ppm(r.pal)))
  end
  return d
end

function M.run_trace(render_frames)
  local m, pool, obj = scenario.load()
  local g = G.new(m, pool, obj)
  local ui = uimod.new(g)
  local r = render_frames and render.new_renderer() or nil
  local out = {}
  local evs = M.load_script()
  for k = 1, #evs do
    local ev = evs[k]
    if ev == 'ai' then
      ai.take_turn(g)
      g:end_turn()
      ui:after_turn()
    else
      ui:handle(ev)
    end
    local d = M.digest_state(g, ui, r, ev == 'render')
    d.step = k - 1
    d.ev = ev
    out[#out + 1] = json_line(d)
  end
  return table.concat(out, '\n') .. '\n'
end

function M.run_render(path, step)
  local m, pool, obj = scenario.load()
  local g = G.new(m, pool, obj)
  local ui = uimod.new(g)
  local r = render.new_renderer()
  local evs = M.load_script()
  local limit = step and math.min(step, #evs) or #evs
  for k = 1, limit do
    local ev = evs[k]
    if ev == 'ai' then
      ai.take_turn(g)
      g:end_turn()
      ui:after_turn()
    else
      ui:handle(ev)
    end
  end
  r:draw(g, ui)
  local data = r.fb:to_ppm(r.pal)
  local f = assert(io.open(path, 'wb'))
  f:write(data)
  f:close()
  io.stderr:write(string.format('%s · %d바이트 · FNV %s\n',
    path, #data, rngmod.hex8(rngmod.fnv1a(data))))
  return rngmod.fnv1a(data)
end

function M.run_bench()
  local P = require('hexwar.path')
  local m, pool, obj = scenario.load()
  local g = G.new(m, pool, obj)
  local u = pool:get(pool:alive_ids(0)[1])
  local t0 = os.clock()
  local n = 2000
  for _ = 1, n do P.reachable(g.map, g.pool, u) end
  local t1 = os.clock()
  local r = render.new_renderer()
  local ui = uimod.new(g)
  local t2 = os.clock()
  for _ = 1, 20 do r:draw(g, ui) end
  local t3 = os.clock()
  print(string.format('reachable %d회 %.3f초 (%.1f us/회)', n, t1 - t0, (t1 - t0) * 1e6 / n))
  print(string.format('draw 20프레임 %.3f초 (%.1f ms/프레임)', t3 - t2, (t3 - t2) * 1000 / 20))
end

if ENTRY ~= 'hexwar.main' then
  local cmd = arg and arg[1] or 'trace'
  if cmd == 'trace' then
    io.write(M.run_trace(true))
  elseif cmd == 'render' then
    M.run_render(arg[2] or 'frame.ppm', arg[3] and tonumber(arg[3]) or nil)
  elseif cmd == 'bench' then
    M.run_bench()
  else
    io.stderr:write('사용법: trace | render <파일> [스텝] | bench\n')
    os.exit(2)
  end
end

return M
