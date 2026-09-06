-- 고정소수점 모듈 — 경계값과 오차 상계를 실제로 확인한다.

local H = require("tests.harness")
local F = require("isorpg.fixed")

local floor = math.floor

H.title('fixed')

-- ---- floordiv / fmod : 음수에서도 내림인가
local DIVC = {{7, 2, 3, 1}, {-7, 2, -4, 1}, {0, 3, 0, 0}, {-1, 65536, -1, 65535},
              {-65536, 65536, -1, 0}, {-65537, 65536, -2, 65535}}
for i = 1, #DIVC do
  local a, b, q, r = DIVC[i][1], DIVC[i][2], DIVC[i][3], DIVC[i][4]
  H.check(string.format('floordiv(%d,%d)', a, b), F.floordiv(a, b), q)
  H.check(string.format('fmod(%d,%d)', a, b), F.fmod(a, b), r)
end

-- ---- fp 변환
H.check('fp(3)', F.fp(3), 196608)
H.check('fp_floor(-1)', F.fp_floor(-1), -1)
H.check('fp_round(32767)', F.fp_round(32767), 0)
H.check('fp_round(32768)', F.fp_round(32768), 1)
H.check('fp_frac(-1)', F.fp_frac(-1), 65535)

-- ---- fp_mul : 분할 곱이 진짜 곱과 같은가
--   기준값은 floor(a*b/65536) 을 그냥 계산한 것이다. 이렇게 비교해도 되는 이유는
--   아래 사례가 전부 |a*b| < 2^53 이라 배정밀도에 정확히 담기기 때문이다.
--   엔진이 실제로 쓰는 범위는 그보다 훨씬 커서 분할 곱이 필요하다.
local CASES = {{0, 0}, {1, 1}, {65536, 65536}, {-65536, 65536}, {65535, 65535},
               {-1, 1}, {1, -1}, {-1, -1}, {1073741824, 3}, {-1073741824, 3},
               {46341, 46341}, {13107, 46341}, {2147483647, 5}, {-2147483648, 5}}
local rs = 12345
for _ = 1, 4000 do
  rs = H.lcg31(rs)
  local a = rs - 134217728 * floor(rs / 134217728) - 67108864
  rs = H.lcg31(rs)
  local b = rs - 134217728 * floor(rs / 134217728) - 67108864
  CASES[#CASES + 1] = {a, b}
end
local bad = 0
for i = 1, #CASES do
  local a, b = CASES[i][1], CASES[i][2]
  if F.fp_mul(a, b) ~= floor(a * b / 65536) then bad = bad + 1 end
end
H.check(string.format('fp_mul == floor(a*b/65536) (%d개)', #CASES), bad, 0)
H.note('중간값 상계 확인: |a|<2^31, |b|<2^37 에서 분할 곱의 항이 2^53 미만')

-- ---- fp_div
bad = 0
for i = 1, #CASES do
  local a, b = CASES[i][1], CASES[i][2]
  local aa = a < 0 and -a or a
  if b ~= 0 and aa < 134217728 and F.fp_div(a, b) ~= floor(a * 65536 / b) then
    bad = bad + 1
  end
end
H.check('fp_div == floor(a*65536/b)', bad, 0)

-- ---- isqrt : 0, 1, 완전제곱수 앞뒤, 큰 값
bad = 0
local NS = {}
for n = 0, 1999 do NS[#NS + 1] = n end
NS[#NS + 1] = 65535; NS[#NS + 1] = 65536; NS[#NS + 1] = 65537
NS[#NS + 1] = 1000000; NS[#NS + 1] = 4294967295; NS[#NS + 1] = 8796093022207
for i = 1, #NS do
  local n = NS[i]
  local r = F.isqrt(n)
  if not (r * r <= n and n < (r + 1) * (r + 1)) then bad = bad + 1 end
end
H.check('isqrt 불변식 r^2 <= n < (r+1)^2', bad, 0)
H.check('isqrt(0)', F.isqrt(0), 0)
H.check('fp_sqrt(fp(1))', F.fp_sqrt(65536), 65536)
H.check('fp_sqrt(fp(2))', F.fp_sqrt(131072), 92681)

-- ---- CORDIC : 참값과의 오차 상계 (테스트에서만 부동소수점을 쓴다)
--   루아에는 파이썬의 round() 가 없다. 여기서 필요한 것은 '반올림'이지
--   은행가 반올림이 아니고, 실제로 정확히 .5 가 나오는 각도도 없다.
local function rnd(x)
  if x >= 0 then return floor(x + 0.5) end
  return -floor(-x + 0.5)
end
local mx = 0
for a = 0, 255 do
  local tc = rnd(65536 * math.cos(2 * math.pi * a / 256.0))
  local ts = rnd(65536 * math.sin(2 * math.pi * a / 256.0))
  local dc = F.COS[a + 1] - tc
  local ds = F.SIN[a + 1] - ts
  if dc < 0 then dc = -dc end
  if ds < 0 then ds = -ds end
  if dc > mx then mx = dc end
  if ds > mx then mx = ds end
end
H.check_true(string.format('CORDIC 표 오차 <= 1 (실측 %d)', mx), mx <= 1)
H.check('SIN[0]', F.SIN[1], 0)
H.check('COS[0]', F.COS[1], 65536)
H.check('SIN[32] == COS[32] == 46341', {F.SIN[33], F.COS[33]}, {46341, 46341})
H.check('SIN[64]', F.SIN[65], 65536)
local mx2 = 0
for a = 0, 255 do
  local s, c = F.SIN[a + 1], F.COS[a + 1]
  local e = F.fp_mul(s, s) + F.fp_mul(c, c) - 65536
  if e < 0 then e = -e end
  if e > mx2 then mx2 = e end
end
H.check_true(string.format('sin^2+cos^2 오차 <= 2/65536 (실측 %d)', mx2), mx2 <= 2)

-- ---- 팔각 거리 오차
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
H.note('팔각 거리 상대오차 %d ~ %d ppm', lo, hi)
H.check_true('팔각 거리 오차가 ±5% 안', -50000 < lo and hi < 50000)
H.check('oct_dist(3,4)', F.oct_dist(3, 4), 5)
H.check('oct_dist(0,0)', F.oct_dist(0, 0), 0)

-- ---- xor16 : 나눗셈 루프로 만든 배타적 논리합이 진짜 xor 인가
--   파이썬은 ^ 와 견주면 그만이지만 루아 5.1 에는 배타적 논리합이 아예 없다.
--   그래서 완전히 다른 방식으로 만든 기준값과 견준다 —
--   xor16 은 한 비트씩 도는 루프, 기준은 256칸 니블 표를 두 번 조회하는 xor8 이다.
--   두 구현이 65,536쌍에서 모두 같으면 어느 한쪽의 실수는 사실상 배제된다.
local function xor16_ref(a, b)
  local ah = floor(a / 256)
  local bh = floor(b / 256)
  return F.xor8(ah, bh) * 256 + F.xor8(a - ah * 256, b - bh * 256)
end
bad = 0
local pairs_n = 0
local a = 0
while a < 65536 do
  local b = 0
  while b < 65536 do
    pairs_n = pairs_n + 1
    if F.xor16(a, b) ~= xor16_ref(a, b) then bad = bad + 1 end
    b = b + 257
  end
  a = a + 251
end
H.check(string.format('xor16 == 니블표 xor (표본 %d쌍)', pairs_n), bad, 0)

H.done()
