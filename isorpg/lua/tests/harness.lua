-- 세 언어 공통의 아주 작은 테스트 하네스 (루아판).
--
--   프레임워크를 쓰지 않는 이유는 하나다. 같은 테스트를 파이썬·타입스크립트로도
--   돌려야 하는데, 프레임워크가 다르면 출력이 달라지고 출력이 달라지면
--   덱에 실을 로그도 달라진다. 그래서 '이름 · 기대 · 실제' 만 찍는다.
--
--   파이썬과 다른 점 둘.
--   (1) 파이썬은 튜플·리스트를 == 하나로 비교하지만 루아의 == 는 테이블 주소를 본다.
--       그래서 깊은 비교 eq() 를 직접 만든다.
--   (2) 파이썬은 테스트 파일 하나가 곧 프로세스 하나라 sys.exit 로 끝내면 되지만,
--       루아는 run.lua 가 열두 개를 한 프로세스에서 돌린다. 그래서 done() 은
--       standalone 일 때만 os.exit 하고, 아닐 때는 셈만 넘긴다.

local H = {}

H.ok = 0
H.bad = 0
H.name = '?'
H.total_ok = 0
H.total_bad = 0
H.summaries = {}
H.standalone = true

-- 저장소 뿌리 찾기. 파이썬은 __file__ 을 쓰지만 루아 5.1 에는 그런 것이 없다.
local function golden_dir()
  local root = os.getenv('ISORPG_ROOT')
  if root and root ~= '' then
    if root:sub(-1) ~= '/' then root = root .. '/' end
    return root .. 'golden/'
  end
  local cands = {'../golden/', 'golden/', '../../golden/', '../../../golden/'}
  for i = 1, #cands do
    local f = io.open(cands[i] .. 'palette.txt', 'r')
    if f then f:close(); return cands[i] end
  end
  return '../golden/'
end
H.GOLDEN = golden_dir()

local function eq(a, b)
  if a == b then return true end
  if type(a) ~= 'table' or type(b) ~= 'table' then return false end
  for k, v in pairs(a) do
    if not eq(v, b[k]) then return false end
  end
  for k in pairs(b) do
    if a[k] == nil then return false end
  end
  return true
end
H.eq = eq

local function repr(v, depth)
  depth = depth or 0
  local t = type(v)
  if t == 'string' then
    if #v > 160 then
      return string.format('%q', v:sub(1, 160)) .. '...(' .. #v .. '바이트)'
    end
    return string.format('%q', v)
  end
  if t ~= 'table' then return tostring(v) end
  if depth > 2 then return '{...}' end
  local n = #v
  local parts = {}
  local shown = n < 24 and n or 24
  for i = 1, shown do parts[#parts + 1] = repr(v[i], depth + 1) end
  if n > shown then parts[#parts + 1] = '...(' .. n .. '개)' end
  if n == 0 then
    local keys = {}
    for k in pairs(v) do keys[#keys + 1] = tostring(k) end
    table.sort(keys)
    if #keys == 0 then return '{}' end
    return '{키 ' .. table.concat(keys, ',', 1, math.min(#keys, 8)) .. '}'
  end
  return '{' .. table.concat(parts, ', ') .. '}'
end
H.repr = repr

function H.title(name)
  H.name = name
  H.ok = 0
  H.bad = 0
  print(string.format('== %s ==', name))
end

function H.check(what, got, want)
  if eq(got, want) then
    H.ok = H.ok + 1
    return true
  end
  H.bad = H.bad + 1
  print('  실패 ' .. what)
  print('    기대 ' .. repr(want))
  print('    실제 ' .. repr(got))
  return false
end

function H.check_true(what, cond)
  return H.check(what, cond and true or false, true)
end

function H.note(fmt, ...)
  if select('#', ...) > 0 then
    print('  ' .. string.format(fmt, ...))
  else
    print('  ' .. fmt)
  end
end

function H.golden(name)
  local f = io.open(H.GOLDEN .. name, 'r')
  if not f then error('골든 파일을 열 수 없다: ' .. H.GOLDEN .. name) end
  local s = f:read('*a')
  f:close()
  return s
end

-- 문자열을 줄 배열로. 파이썬의 rstrip('\n').split('\n') 과 같다.
function H.lines(text)
  local out = {}
  for line in (text .. '\n'):gmatch('([^\n]*)\n') do out[#out + 1] = line end
  while #out > 0 and out[#out] == '' do out[#out] = nil end
  return out
end

-- 파이썬 테스트가 쓰는 `rs = (1103515245*rs + 12345) % 2^31` 을 그대로 옮긴 것.
-- 그냥 곱하면 1103515245 * 2^31 ~ 2^61 이라 배정밀도를 넘는다. 상·하위로 쪼갠다.
function H.lcg31(rs)
  local h = math.floor(rs / 65536)
  local l = rs - h * 65536
  local hh = 1103515245 * h
  hh = hh - 32768 * math.floor(hh / 32768)          -- mod 2^15 (2^15 * 2^16 = 2^31)
  local v = hh * 65536 + 1103515245 * l + 12345
  return v - 2147483648 * math.floor(v / 2147483648)
end

function H.done()
  print(string.format('%s: 통과 %d · 실패 %d', H.name, H.ok, H.bad))
  H.total_ok = H.total_ok + H.ok
  H.total_bad = H.total_bad + H.bad
  H.summaries[#H.summaries + 1] = {H.name, H.ok, H.bad}
  if H.standalone then
    os.exit(H.bad > 0 and 1 or 0)
  end
end

return H
