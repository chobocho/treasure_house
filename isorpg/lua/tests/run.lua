-- 루아 테스트 러너 — 파이썬의 `for t in $(PYTESTS); do python3 $t.py; done` 자리.
--
--   파이썬은 테스트 파일 하나가 곧 프로세스 하나라 sys.exit 로 끝내면 그만이다.
--   루아에는 그런 관례가 없고, 테스트마다 프로세스를 띄우면 맵 생성과 팔레트 적재를
--   그 횟수만큼 반복하게 된다. 그래서 한 프로세스에서 차례로 돌리고,
--   하네스의 standalone 을 꺼서 os.exit 가 중간에 튀지 않게 한다.
--   출력 모양(== 이름 == / 이름: 통과 N · 실패 M)은 파이썬과 한 글자도 같다.

do
  local self_path = (arg and arg[0]) or ''
  local dir = self_path:match('^(.*)[/\\][^/\\]*$')
  if dir then package.path = dir .. '/../?.lua;' .. package.path end
  package.path = './?.lua;' .. package.path
end

local H = require("tests.harness")
H.standalone = false

-- test_love_draw 는 맨 뒤다. love 전역을 스텁으로 갈아 끼웠다 되돌리므로,
-- 진짜 LÖVE 안에서 돌 때(tools/love_headless) 다른 테스트와 섞이지 않게 한다.
local TESTS = {'test_fixed', 'test_proj', 'test_sort', 'test_map', 'test_path',
               'test_raster', 'test_los', 'test_dice', 'test_save',
               'test_prim', 'test_trace', 'test_engine', 'test_love_draw'}

-- 테스트 파일이 놓인 곳. `luajit tests/run.lua` 든 `cd tests && luajit run.lua` 든 듣게 한다.
local base = (arg and arg[0] or ''):match('^(.*)[/\\][^/\\]*$')
if base then base = base .. '/' else base = '' end

for i = 1, #TESTS do
  local path = base .. TESTS[i] .. '.lua'
  local chunk, err = loadfile(path)
  if not chunk then error(err) end
  chunk()
end

print(string.format('전체: 통과 %d · 실패 %d (%d개 모듈)',
                    H.total_ok, H.total_bad, #H.summaries))
os.exit(H.total_bad > 0 and 1 or 0)
