-- 프리미티브 보고서가 골든과 바이트 단위로 같은가.
--
--   같은 보고서를 파이썬·타입스크립트도 찍는다. 세 언어의 출력이 이 한 파일과
--   전부 같으면 이식이 맞다는 뜻이다.

local H = require("tests.harness")
local MAIN = require("isorpg.main")

H.title('prim')

local got = MAIN.prim_report()
local want = H.golden('prim.txt')

-- 파이썬의 str.split('\n') 과 똑같이 자른다 — 끝의 빈 조각도 남긴다.
-- 그래야 '줄 수' 가 파이썬과 같은 208 로 나온다. 루아의 gmatch 방식으로 자르면
-- 마지막 개행 뒤의 빈 조각이 사라져 하나 적게 세어진다.
local function pysplit(s)
  local out = {}
  local start = 1
  while true do
    local i = s:find('\n', start, true)
    if not i then
      out[#out + 1] = s:sub(start)
      break
    end
    out[#out + 1] = s:sub(start, i - 1)
    start = i + 1
  end
  return out
end
local gl, wl = pysplit(got), pysplit(want)
H.check('줄 수', #gl, #wl)
local bad = 0
local n = #gl < #wl and #gl or #wl
for i = 1, n do
  if gl[i] ~= wl[i] then
    bad = bad + 1
    if bad <= 5 then
      print(string.format('  %d줄 다름', i))
      print('    기대 ' .. H.repr(wl[i]))
      print('    실제 ' .. H.repr(gl[i]))
    end
  end
end
H.check('다른 줄', bad, 0)
H.check('전체 바이트', got == want, true)
H.note('보고서 %d줄 · %d바이트', #gl, #got)

H.done()
