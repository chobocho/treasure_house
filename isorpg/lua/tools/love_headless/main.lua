-- 엔진 테스트 열세 개를 '진짜 LÖVE 런타임' 위에서 그대로 돌린다.
--
--   왜 굳이. luajit 으로 통과했다고 LÖVE 에서도 통과한다는 보장이 없기 때문이다.
--   LÖVE 는 자기 부팅 코드로 전역을 손보고, 작업 디렉터리와 모듈 경로를 다르게 잡으며,
--   io 대신 love.filesystem 을 쓰라고 권한다. 엔진이 5.1 의미론만 쓰고
--   금지된 전역에 손대지 않는다는 주장은 여기서 실제로 돌려 봐야 증거가 된다.
--
--   출력은 tests/run.lua 와 같다. 딱 하나 다른 것이 통과 수인데, love.image 가
--   실제로 떠 있을 때만 할 수 있는 검사 둘이 test_love_draw 에 더 붙기 때문이다
--   (프런트엔드가 넘기는 rgba8 바이트열을 진짜 ImageData 가 그대로 되돌려 주는가).
--   luajit: 613 · LÖVE: 615.
--
--   루아 5.1 문법만 쓴다.

function love.load()
  -- LÖVE 는 게임 폴더(tools/love_headless)의 부모를 준다 -> <저장소>/isorpg/lua/tools
  local base = love.filesystem.getSourceBaseDirectory()
  local luaroot = base .. '/..'                  -- <저장소>/isorpg/lua
  local golden = luaroot .. '/../golden/'        -- <저장소>/isorpg/golden/

  package.path = luaroot .. '/?.lua;' .. package.path

  -- 골든 파일 위치를 소스 위치에서 못 박는다.
  --
  --   엔진은 ISORPG_ROOT 환경변수를 먼저 보고, 없으면 '../golden/' 같은 후보를 훑는다.
  --   그 폴백은 작업 디렉터리에 기대는데, LÖVE 는 작업 디렉터리를 바꾸지는 않지만
  --   어디서 실행될지를 보장하지도 않는다. 루아에는 환경변수를 세우는 방법이 없으므로
  --   모듈 테이블의 필드를 갈아 끼운다 — 안쪽 호출도 호출 시점에 테이블을 짚으니 같이 따라온다.
  if io.open(golden .. 'palette.txt', 'r') then
    local H = require('tests.harness')
    H.GOLDEN = golden
    local RA = require('isorpg.raster')
    RA.golden_dir = function() return golden end
  end

  -- run.lua 는 arg[0] 로 자기 위치를 잡아 테스트 파일을 찾는다.
  -- LÖVE 는 arg[0] 를 주지 않으므로(arg[1] 이 게임 경로다) 여기서 채워 준다.
  -- run.lua 를 고치지 않고 그대로 쓰기 위한 최소한의 손질이다.
  arg = arg or {}
  arg[0] = luaroot .. '/tests/run.lua'

  -- run.lua 는 끝에서 os.exit 를 부른다. LÖVE 안에서 os.exit 를 그냥 부르면
  -- 런타임 정리를 건너뛰고 튀어나간다. 그래서 잠깐 가로채 종료 코드만 받아 두고,
  -- love.event.quit 으로 정상적으로 끝낸다. 종료 코드는 그대로 셸에 전달된다.
  local SENTINEL = {}
  local code = 0
  local real_exit = os.exit
  os.exit = function(c)
    if c == true then c = 0 elseif c == false then c = 1 end
    code = c or 0
    error(SENTINEL)
  end

  local chunk, err = loadfile(arg[0])
  if not chunk then
    os.exit = real_exit
    io.stderr:write('run.lua 를 열 수 없다: ' .. tostring(err) .. '\n')
    love.event.quit(1)
    return
  end

  local ok, e = pcall(chunk)
  os.exit = real_exit
  if not ok and e ~= SENTINEL then
    io.stderr:write(tostring(e) .. '\n')
    love.event.quit(1)
    return
  end
  love.event.quit(code)
end
