-- 시나리오 트레이스 — 골든과 한 줄도 어긋나지 않는가.

local H = require("tests.harness")
local G = require("isorpg.game")

H.title('trace')

local got = G.run_script_trace()
local want = H.golden('trace.jsonl')
local gl = H.lines(got)
local wl = H.lines(want)

H.check('줄 수', #gl, #wl)
local bad = 0
local n = #gl < #wl and #gl or #wl
for i = 1, n do
  if gl[i] ~= wl[i] then
    bad = bad + 1
    if bad <= 3 then
      print(string.format('  %d줄 다름', i))
      print('    기대 ' .. wl[i])
      print('    실제 ' .. gl[i])
    end
  end
end
H.check('다른 줄', bad, 0)

-- ---- 두 번 돌려도 같은가
H.check('재현성', G.run_script_trace(), got)

-- ---- 트레이스가 실제로 뭔가를 했는가 (빈 시나리오 방지)
--   루아 5.1 에는 json 이 없다. 트레이스는 서식이 고정된 정수 전용 줄이라
--   "키":값 을 그대로 긁어 표로 만드는 것으로 족하다.
local function parse(line)
  local o = {}
  for k, v in line:gmatch('"([%a]+)":(-?%d+)') do o[k] = tonumber(v) end
  return o
end
local ticks, marks = {}, {}
for i = 1, #gl do
  if gl[i]:sub(1, 5) == '{"t":' then
    ticks[#ticks + 1] = parse(gl[i])
  elseif gl[i]:sub(1, 8) == '{"mark":' then
    marks[#marks + 1] = gl[i]
  end
end
H.check('표식 개수', #marks, 11)
H.check_true('222줄의 틱 (되돌린 뒤 다시 진행한 몫 포함)', #ticks == 222)
H.check_true('몬스터가 줄었다', ticks[#ticks].mon < ticks[1].mon)
H.check_true('레벨이 올랐다', ticks[#ticks].lv > ticks[1].lv)
local rewound = false
for i = 1, #ticks - 1 do
  if ticks[i + 1].t < ticks[i].t then rewound = true end
end
H.check_true('되돌리기가 실제로 시간을 되돌렸다', rewound)
H.check_true('플레이어가 움직였다',
             ticks[1].px ~= ticks[#ticks].px or ticks[1].py ~= ticks[#ticks].py)
H.check_true('본 칸이 늘었다', ticks[#ticks].seen > ticks[1].seen)
-- 숫자 자리에 부동소수점 표기가 섞이면 언어마다 자릿수가 달라져 파리티가 깨진다.
-- 루아에서 특히 위험하다 — tostring(1/1) 은 "1" 이지만 tostring(2^31) 은 "2.147483648e+09" 다.
bad = 0
for i = 1, #gl do
  local l = gl[i]
  if l:sub(1, 5) == '{"t":' then
    for tok in l:gmatch('[:%[,]%s*(-?[%d%.eE%+]+)') do
      if not tok:match('^%-?%d+$') then bad = bad + 1 end
    end
  end
end
H.check('정수가 아닌 숫자 토큰', bad, 0)

H.done()
