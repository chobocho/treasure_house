-- CLI — SPEC §13.
--
--   prim / trace / render 의 출력은 세 언어에서 바이트 단위로 같아야 한다.
--   그래서 이 파일의 서식 문자열 하나하나가 명세다. 칸 맞춤에 한글을 쓰지 않는 것도
--   그 때문이다 — 루아의 string.format 은 %-22s 를 글자가 아니라 바이트로 채운다.
--   한글 한 자가 UTF-8 로 세 바이트라 한글을 넣는 순간 파이썬과 폭이 달라진다.
--
--   숫자는 전부 string.format('%d', ...) 로 찍는다. tostring 을 쓰면 -0 이
--   "-0" 으로 나오고(quad 1 의 cos 가 실제로 -0 이다), 소수가 섞이면
--   LuaJIT 이 %d 에서 그대로 죽는다.

-- 모듈 경로를 스스로 잡는다. `luajit isorpg/main.lua` 처럼 하위 디렉터리에서
-- 실행돼도 require 가 듣게 하려는 것이다.
do
  local self_path = (arg and arg[0]) or ''
  local dir = self_path:match('^(.*)[/\\][^/\\]*$')
  if dir then package.path = dir .. '/../?.lua;' .. package.path end
  package.path = './?.lua;' .. package.path
end

local DICE = require("isorpg.dice")
local F = require("isorpg.fixed")
local M2 = require("isorpg.gamemap")
local P = require("isorpg.path")
local PR = require("isorpg.proj")
local RA = require("isorpg.raster")
local SV = require("isorpg.save")
local SD = require("isorpg.sortdag")
local G = require("isorpg.game")
local RNG = require("isorpg.rng")

local floor = math.floor
local fmt = string.format

local M = {}

local TILE_CASES = {{0, 0, 0}, {1, 0, 0}, {0, 1, 0}, {1, 1, 0}, {2, 0, 0}, {0, 2, 0},
                    {5, 3, 0}, {5, 3, 1}, {5, 3, 7}, {47, 47, 0}, {-1, -1, 0},
                    {24, 24, 15}}
local PIX_CASES = {{0, 8}, {15, 8}, {16, 8}, {17, 8}, {0, 0}, {31, 15}, {32, 16},
                   {-1, 0}, {-1, -1}, {-16, 8}, {-17, 8}, {16, 0}, {16, 15},
                   {159, 99}, {319, 199}, {-320, -200}, {7, 3}, {8, 4}, {9, 4}, {0, 16}}
local CAM_CASES = {{0, 0}, {137, 91}, {-137, -91}, {768, 640}, {-768, -120}}
local VIS_CASES = {{0, 0}, {100, 50}, {-200, 300}, {700, 700}, {-768, -120}}
local FP_CASES = {{65536, 65536}, {65536, 32768}, {98304, 98304}, {-65536, 32768},
                  {-98304, 98304}, {1, 65536}, {65535, 65535}, {46341, 46341},
                  {3277, 46341}, {-1, 65536}, {123456, -654321}, {2147483647, 3}}
local SQRT_N = {0, 1, 2, 3, 4, 8, 15, 16, 17, 1000, 65535, 65536, 1000000,
                4294967295, 8796093022207}
local SQRT_X = {65536, 131072, 196608, 262144, 32768, 6553600}
local TRIG_A = {0, 8, 16, 24, 32, 40, 48, 56, 64, 96, 128, 160, 192, 224, 255}
local OCT_CASES = {{3, 4}, {100, 0}, {0, 100}, {100, 100}, {1000, 414}, {-7, 24},
                   {65, 72}, {1, 1}, {0, 0}}
local OCTILE_CASES = {{0, 0, 0, 0}, {0, 0, 1, 0}, {0, 0, 1, 1}, {0, 0, 3, 0},
                      {0, 0, 3, 3}, {0, 0, 5, 2}, {10, 10, 2, 7}, {0, 0, 47, 47}}

-- 루아에는 bytes 리터럴이 없다. CRC 사례는 바이트 배열로 적는다.
local function bytes_of(s)
  local t = {}
  for i = 1, #s do t[i] = s:byte(i) end
  return t
end
local CRC_CASES = {bytes_of(''), bytes_of('A'), bytes_of('123456789'),
                   bytes_of('ISORPG'), (function()
                     local t = {}
                     for i = 0, 15 do t[i + 1] = i end
                     return t
                   end)()}

-- 골든 프리미티브 보고서. golden/prim.txt 와 한 글자도 달라선 안 된다.
function M.prim_report()
  local L = {}
  local function w(s) L[#L + 1] = s end

  w('== 1. 타일 -> 화면 ==')
  w('tx ty h  sx sy')
  for i = 1, #TILE_CASES do
    local c = TILE_CASES[i]
    local sx, sy = PR.tile_to_screen(c[1], c[2], c[3])
    w(fmt('%d %d %d  %d %d', c[1], c[2], c[3], sx, sy))
  end
  w('')
  w('기저 e_x = (16, 8)   e_y = (-16, 8)   det = 256')
  w('역행렬 * 256 = [[8, 16], [-8, 16]]')
  w('')

  w('== 2. 화면 -> 타일 (대수적 역) ==')
  w('px py  tx ty')
  local same = true
  for i = 1, #PIX_CASES do
    local c = PIX_CASES[i]
    local tx, ty = PR.screen_to_tile(c[1], c[2])
    local sx, sy = PR.screen_to_tile_slow(c[1], c[2])
    if sx ~= tx or sy ~= ty then same = false end
    w(fmt('%d %d  %d %d', c[1], c[2], tx, ty))
  end
  w('')
  w('마름모 정의(|u| + 2|v| <= 16)로 직접 찾은 타일과 ' ..
    (same and '전부 일치' or '어긋남'))
  w('')

  w('== 3. 모서리 마스크 32x16 ==')
  for oy = 0, 15 do
    local row = {}
    for ox = 0, 31 do row[ox + 1] = fmt('%d', PR.PICK_MASK[oy * 32 + ox + 1]) end
    w(table.concat(row))
  end
  w('')
  local cnt = {0, 0, 0, 0}
  for i = 1, 512 do
    local v = PR.PICK_MASK[i]
    cnt[v + 1] = cnt[v + 1] + 1
  end
  w(fmt('값 분포  0:%d 1:%d 2:%d 3:%d  합 %d',
        cnt[1], cnt[2], cnt[3], cnt[4], cnt[1] + cnt[2] + cnt[3] + cnt[4]))
  local bad = 0
  for i = 1, #CAM_CASES do
    local cx, cy = CAM_CASES[i][1], CAM_CASES[i][2]
    for py = 0, PR.SCR_H - 1 do
      for px = 0, PR.SCR_W - 1 do
        local ax, ay = PR.pick_mask(px + cx, py + cy)
        local bx, by = PR.screen_to_tile(px + cx, py + cy)
        if ax ~= bx or ay ~= by then bad = bad + 1 end
      end
    end
  end
  w(fmt('전수 확인  카메라 %d개 x %d픽셀 = %d  불일치 %d',
        #CAM_CASES, PR.SCR_W * PR.SCR_H, #CAM_CASES * PR.SCR_W * PR.SCR_H, bad))
  w('')

  w('== 4. 가시 타일 범위 ==')
  w('camX camY  tx0 ty0 tx1 ty1')
  for i = 1, #VIS_CASES do
    local cx, cy = VIS_CASES[i][1], VIS_CASES[i][2]
    local a, b, c, d = PR.visible_range(cx, cy, cx + PR.SCR_W, cy + PR.SCR_H)
    w(fmt('%d %d  %d %d %d %d', cx, cy, a, b, c, d))
  end
  w('')

  w('== 5. 고정소수점 16.16 ==')
  w('a b  fp_mul fp_div')
  for i = 1, #FP_CASES do
    local a, b = FP_CASES[i][1], FP_CASES[i][2]
    w(fmt('%d %d  %d %d', a, b, F.fp_mul(a, b), F.fp_div(a, b)))
  end
  w('')
  w(fmt('fp_floor  %d %d %d %d %d',
        F.fp_floor(65536), F.fp_floor(-1), F.fp_floor(-65536),
        F.fp_floor(-65537), F.fp_floor(131071)))
  w('')

  w('== 6. 정수 제곱근 ==')
  w('n  isqrt(n)')
  for i = 1, #SQRT_N do
    w(fmt('%d  %d', SQRT_N[i], F.isqrt(SQRT_N[i])))
  end
  w('')
  w('x  fp_sqrt(x)')
  for i = 1, #SQRT_X do
    w(fmt('%d  %d', SQRT_X[i], F.fp_sqrt(SQRT_X[i])))
  end
  w('')

  w('== 7. CORDIC 사인/코사인 표 ==')
  w('a  COS SIN')
  for i = 1, #TRIG_A do
    local a = TRIG_A[i]
    w(fmt('%d  %d %d', a, F.COS[a + 1], F.SIN[a + 1]))
  end
  w('')
  local sc, ss = 0, 0
  for a = 0, 255 do
    sc = sc + F.COS[a + 1]
    ss = ss + F.SIN[a + 1]
  end
  w(fmt('sum COS = %d   sum SIN = %d', sc, ss))
  local mx = 0
  for a = 0, 255 do
    local s, c = F.SIN[a + 1], F.COS[a + 1]
    local e = F.fp_mul(s, s) + F.fp_mul(c, c) - 65536
    if e < 0 then e = -e end
    if e > mx then mx = e end
  end
  w(fmt('max |sin^2 + cos^2 - 1| = %d / 65536', mx))
  w('')

  w('== 8. 팔각 거리 근사 ==')
  w('dx dy  oct exact')
  for i = 1, #OCT_CASES do
    local dx, dy = OCT_CASES[i][1], OCT_CASES[i][2]
    w(fmt('%d %d  %d %d', dx, dy, F.oct_dist(dx, dy), F.isqrt(dx * dx + dy * dy)))
  end
  w('')
  local lo, hi = 1000000000, -1000000000
  for a = 0, 255 do
    local dx = floor(1000 * F.COS[a + 1] / 65536)
    local dy = floor(1000 * F.SIN[a + 1] / 65536)
    local ex = F.isqrt(dx * dx + dy * dy)
    if ex ~= 0 then
      local e = floor((F.oct_dist(dx, dy) - ex) * 1000000 / ex)
      if e < lo then lo = e end
      if e > hi then hi = e end
    end
  end
  w(fmt('반지름 1000, 256방향  상대오차 %d ~ %d ppm', lo, hi))
  w('')

  w('== 9. LCG (a=22695477, c=1, m=2^32) ==')
  w('i  state rand15')
  local r = RNG.new(1)
  for i = 0, 7 do
    local v = r:next()
    w(fmt('%d  %d %d', i + 1, r.s, v))
  end
  w('')
  r = RNG.new(12345)
  local eight = {}
  for i = 1, 8 do eight[i] = fmt('%d', r:next()) end
  w('seed 12345 의 처음 8개 rand15: ' .. table.concat(eight, ' '))
  w('')

  w('== 10. 다이아몬드-스퀘어 5x5 ' ..
    '(n=4, seed=1, scale=100, rough 58/100, corners 50/60/70/80) ==')
  local grid = M2.gen_height(4, {50, 60, 70, 80}, 100, 1)
  for y = 1, #grid do
    local row = {}
    for x = 1, #grid[y] do row[x] = fmt('%4d', grid[y][x]) end
    w(table.concat(row, ' '))
  end
  w('')

  w('== 11. 옥타일 휴리스틱 (MIN_MOVE=8) ==')
  w('ax ay bx by  h')
  for i = 1, #OCTILE_CASES do
    local c = OCTILE_CASES[i]
    w(fmt('%d %d %d %d  %d', c[1], c[2], c[3], c[4],
          P.octile(c[1], c[2], c[3], c[4])))
  end
  w('')

  w('== 12. 주사위 분포 ==')
  local DCASES = {{1, 6}, {2, 6}, {3, 6}, {2, 20}}
  for i = 1, #DCASES do
    local n, m = DCASES[i][1], DCASES[i][2]
    local d = DICE.dist(n, m)
    local tot, esum = 0, 0
    for s = 0, #d - 1 do
      tot = tot + d[s + 1]
      esum = esum + s * d[s + 1]
    end
    w(fmt('%dd%d  경우의 수 %d = %d^%d  합계기대값*%d = %d',
          n, m, tot, m, n, tot, esum))
  end
  w('')
  local function tail_join(c, from)
    local t = {}
    for i = from + 1, #c do t[#t + 1] = fmt('%d', c[i]) end
    return table.concat(t, ' ')
  end
  w('2d6 분포: ' .. tail_join(DICE.dist(2, 6), 2))
  w('3d6 분포: ' .. tail_join(DICE.dist(3, 6), 3))
  w('')

  w('== 13. CRC-16/CCITT-FALSE ==')
  w(fmt('표 앞 4개: %d %d %d %d',
        SV.CRC_TBL[1], SV.CRC_TBL[2], SV.CRC_TBL[3], SV.CRC_TBL[4]))
  w(fmt('표 뒤 4개: %d %d %d %d',
        SV.CRC_TBL[253], SV.CRC_TBL[254], SV.CRC_TBL[255], SV.CRC_TBL[256]))
  for i = 1, #CRC_CASES do
    local data = CRC_CASES[i]
    local hx = {}
    for k = 1, #data do hx[k] = fmt('%02X', data[k]) end
    w(fmt('crc16 [%s] = 0x%04X', table.concat(hx), SV.crc16(data)))
  end
  w('')

  w('== 14. 상자 정렬 사례 ==')
  w('case name  겹침쌍 상호쌍 순서 절단')
  local rows = {}
  for _, line in ipairs(RA.split_lines(RA.read_text(RA.golden_dir() .. 'sortcase.txt'))) do
    rows[#rows + 1] = RA.split_ws(line)
  end
  local i = 2
  while i <= #rows do
    local num, name, n = rows[i][2], rows[i][3], tonumber(rows[i][4])
    i = i + 1
    local items = {}
    for k = 0, n - 1 do
      local src = rows[i + k]
      local it = {}
      for t = 1, #src do it[t] = tonumber(src[t]) end
      items[k + 1] = it
    end
    i = i + n
    local order, br = SD.topo_sort(items)
    local bb = {}
    for k = 1, n do bb[k] = SD.box_bbox(items[k]) end
    local ov, mu = 0, 0
    for a = 1, n do
      for b = a + 1, n do
        if SD.bbox_overlap(bb[a], bb[b]) then ov = ov + 1 end
        if SD.behind(items[a], items[b]) and SD.behind(items[b], items[a]) then
          mu = mu + 1
        end
      end
    end
    local os_ = {}
    for k = 1, #order do os_[k] = fmt('%d', order[k]) end
    w(fmt('%s %s  %d %d  %s  %d', num, name, ov, mu, table.concat(os_, ' '), br))
  end
  w('')
  local s = table.concat(L, '\n')
  s = (s:gsub('\n+$', ''))
  return s .. '\n'
end

-- 구간별 성능. 기계마다 다르므로 파리티 대상이 아니다.
function M.bench()
  local out = {}
  local function t(name, fn, n)
    local s = os.clock()
    for _ = 1, n do fn() end
    local d = os.clock() - s
    -- 칸 맞춤에 한글을 쓰지 않는다 — %-22s 는 바이트 수로 채운다.
    out[#out + 1] = fmt('%-22s %6d x  %8.1f ms  %10.1f us/call',
                        name, n, d * 1000, d * 1000000 / n)
  end
  local g = G.new_game()
  local m = g.map
  t('screen_to_tile x1000', function()
    for x = 0, 999 do PR.screen_to_tile(x, x - 200 * floor(x / 200)) end
  end, 20)
  t('pick_mask x1000', function()
    for x = 0, 999 do PR.pick_mask(x, x - 200 * floor(x / 200)) end
  end, 20)
  t('fp_mul x1000', function()
    for x = 0, 999 do F.fp_mul(x * 7919, 46341) end
  end, 20)
  t('isqrt x1000', function()
    for x = 0, 999 do F.isqrt(x * 104729) end
  end, 20)
  t('astar (24,34)->(24,20)', function() P.astar(m, 24, 34, 24, 20) end, 50)
  t('dijkstra 48x48', function() P.dijkstra(m, 24, 34) end, 10)
  t('fog update r=9', function() g.fog:update(m, 24, 25) end, 100)
  t('game tick', function() g:tick() end, 200)
  t('render frame', function() g:render() end, 20)
  t('pack_state + crc16', function() SV.pack_state(g) end, 100)
  return table.concat(out, '\n') .. '\n'
end

function M.main(argv)
  local cmd = argv[1] or 'prim'
  if cmd == 'prim' then
    io.stdout:write(M.prim_report())
    return 0
  end
  if cmd == 'trace' then
    io.stdout:write(G.run_script_trace())
    return 0
  end
  if cmd == 'render' then
    local path = argv[2]
    local steps = argv[3] and tonumber(argv[3]) or -1
    local g = G.new_game()
    -- 루아의 `cond and a or b` 는 a 가 nil/false 이면 무너진다.
    -- `steps < 0 and nil or steps` 라고 쓰면 언제나 steps 가 나와서
    -- limit = -1 로 첫 틱에 멈춰 버린다. 그래서 if 로 또박또박 쓴다.
    local limit = nil
    if steps >= 0 then limit = steps end
    g:run_script(nil, nil, limit)
    -- 바이트 그대로 써야 한다. 텍스트 모드로 열면 플랫폼에 따라 0x0A 가 부풀 수 있다.
    local f = io.open(path, 'wb')
    f:write(g:render_ppm())
    f:close()
    return 0
  end
  if cmd == 'bench' then
    io.stdout:write(M.bench())
    return 0
  end
  io.stderr:write('모르는 명령: ' .. tostring(cmd) .. '\n')
  return 1
end

-- 스크립트로 직접 돌렸을 때만 실행한다. require 로 불러 쓰는 테스트가 있어서다.
if arg and arg[0] and arg[0]:match('main%.lua$') then
  local a = {}
  for i = 1, #arg do a[i] = arg[i] end
  os.exit(M.main(a))
end

return M
