-- 골든 트레이스 대조 (루아) — 파이썬이 얼려 둔 파일과 한 바이트라도 다르면 실패.

package.path = './?.lua;' .. package.path

local golden = (os.getenv('HEXWAR_GOLDEN') or '../golden')
local want = {}
for line in io.lines(golden .. '/trace.jsonl') do
  if line ~= '' then want[#want + 1] = line end
end

local M = require('hexwar.main')   -- require 로 부르면 명령 처리를 건너뛴다

local got = {}
for line in M.run_trace(true):gmatch('([^\n]+)') do got[#got + 1] = line end

if #got ~= #want then
  print(string.format('스텝 수 불일치: %d != %d', #got, #want))
  os.exit(1)
end
local bad = 0
for i = 1, #want do
  if got[i] ~= want[i] then
    if bad < 5 then
      print(string.format('스텝 %d 불일치\n  got  %s\n  want %s', i - 1, got[i], want[i]))
    end
    bad = bad + 1
  end
end
if bad > 0 then
  print(string.format('FAIL — %d스텝 불일치', bad))
  os.exit(1)
end
local frames = 0
for _, l in ipairs(want) do if l:find('fbHash') then frames = frames + 1 end end
print(string.format('trace OK (lua) — %d스텝 · 프레임 해시 %d개 일치', #want, frames))
