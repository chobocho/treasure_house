-- 16.16 고정소수점 — SPEC §2. (루아 5.1 / LuaJIT / LÖVE 11.5 공용)
--
--   루아 5.1 에는 정수형도 비트 연산자도 없다. 숫자는 전부 배정밀도 실수 하나뿐이라
--   가수 53비트 안에서만 정수가 정확하다. 그래서 이 모듈은
--     · 시프트 대신 math.floor 나눗셈만 쓰고
--     · 곱셈 중간값이 2^53 을 넘지 않도록 쪼개고
--     · xor 를 산술로 직접 만든다 (LuaJIT 의 bit 라이브러리는 5.1 표준이 아니다)
--   파이썬·타입스크립트와 한 비트도 다르지 않게 만드는 것이 목적이다.
--
-- 배열 규약: 이 파일의 모든 표(ATAN_BRAD, COS, SIN, NIB_XOR)는 1-기반이다.
--   좌표·각도 계산은 파이썬과 똑같이 0-기반으로 하고, 표를 짚는 순간에만 +1 한다.
--   그래서 COS[a] 가 아니라 COS[a + 1] 로 읽는다.

local floor = math.floor

local M = {}

M.FP_BITS = 16
M.FP_ONE = 65536
local FP_ONE = 65536

-- b > 0 일 때 -무한대 방향 내림. 루아의 / 는 항상 실수 나눗셈이라
-- math.floor 를 씌워야 파이썬의 // 와 같아진다. a, b 가 2^53 안이면 정확하다.
function M.floordiv(a, b)
  return floor(a / b)
end

-- 항상 0 <= 결과 < b. 루아 5.1 의 % 는 이미 a - b*floor(a/b) 로 정의돼 있어
-- 파이썬과 의미가 같지만(C 의 fmod 와는 다르다), 명세가 요구하는 것이
-- '내림 나머지'라는 사실을 코드에 남기려고 직접 쓴다.
function M.fmod(a, b)
  return a - b * floor(a / b)
end

-- 산술 우시프트. 루아에는 >> 가 없고, 있더라도 32비트로 잘려 쓸 수 없다.
function M.ashr(a, k)
  return floor(a / 2 ^ k)
end

function M.fp(n)
  return n * FP_ONE
end

function M.fp_floor(x)
  return floor(x / FP_ONE)
end

function M.fp_round(x)
  return floor((x + 32768) / FP_ONE)
end

function M.fp_frac(x)
  return x - FP_ONE * floor(x / FP_ONE)
end

-- floor(a*b / 65536). a 를 상·하위 16비트로 쪼개 중간값을 2^53 아래로 묶는다.
-- 루아에서는 이 분할이 선택이 아니라 필수다 — a*b 를 그냥 곱하면 2^62 까지
-- 커져 가수를 넘고, 넘는 순간 조용히 틀린 값이 나온다. (정리 2.1)
function M.fp_mul(a, b)
  local ah = floor(a / FP_ONE)
  local al = a - ah * FP_ONE                  -- 0 <= al < 65536
  return ah * b + floor(al * b / FP_ONE)
end

-- 반올림 곱. 광원 감쇠처럼 한쪽으로 쏠리면 곤란한 곳에만 쓴다.
function M.fp_mulr(a, b)
  local ah = floor(a / FP_ONE)
  local al = a - ah * FP_ONE
  return ah * b + floor((al * b + 32768) / FP_ONE)
end

-- floor(a*65536 / b). |a| < 2^37 이면 a*65536 이 2^53 미만이라 정확하다.
function M.fp_div(a, b)
  return floor(a * FP_ONE / b)
end

-- floor(sqrt(n)). 뉴턴 반복 — 단조 감소라 반드시 멈춘다. (정리 2.2)
--
--   루아에는 정수 제곱근이 없고 math.sqrt 는 실수라 언어마다 마지막 자리가
--   갈릴 수 있다. 나눗셈만 쓰는 이 형태라야 세 언어가 같은 값을 낸다.
--   n < 2^52 면 floor(n/x) 도 정확하다 — n/x 가 정수가 아닐 때
--   가장 가까운 정수와의 거리 1/x 가 그 자리의 ulp 보다 크기 때문이다.
function M.isqrt(n)
  if n < 2 then
    return n
  end
  local x = n
  local y = floor((x + 1) / 2)
  while y < x do
    x = y
    y = floor((x + floor(n / x)) / 2)
  end
  return x
end

function M.fp_sqrt(x)
  return M.isqrt(x * FP_ONE)
end

-- 알파 맥스 플러스 베타 민 — 최소최대오차 최적 계수를 1024배 해 반올림한 것.
M.OCT_A = 983
M.OCT_B = 407

function M.oct_dist(dx, dy)
  local ax = dx >= 0 and dx or -dx
  local ay = dy >= 0 and dy or -dy
  local hi, lo
  if ax > ay then hi, lo = ax, ay else hi, lo = ay, ax end
  return floor((983 * hi + 407 * lo) / 1024)
end

-- ---------------------------------------------------------------- CORDIC (SPEC §2.6)
M.N_ITER = 20
M.GUARD = 8
-- atan(2^-i) 를 brad(한 바퀴=256) 로 환산해 16.16 으로 반올림한 값. 1-기반이라 [i+1].
M.ATAN_BRAD = {2097152, 1238021, 654136, 332050, 166669, 83416, 41718, 20860,
               10430, 5215, 2608, 1304, 652, 326, 163, 81, 41, 20, 10, 5}
M.K_INV = 10188014

-- 2^i 를 미리 만들어 둔다. 루프 안에서 2^i 를 계산하면 pow 호출이 스무 번 들어가고,
-- LuaJIT 이 상수 접기를 못 하는 형태라 표가 눈에 띄게 빠르다. 1-기반이라 [i+1].
local POW2 = {}
for i = 0, 40 do POW2[i + 1] = 2 ^ i end
M.POW2 = POW2

local ATAN_BRAD = M.ATAN_BRAD
local K_INV = M.K_INV

-- 16.16 brad 각도 -> cos, sin (16.16 두 값을 그대로 돌려준다).
-- 가드 8비트를 안에서 들고 다니다가 끝에서 반올림해 버린다.
function M.cordic(theta)
  local t = theta - (256 * FP_ONE) * floor(theta / (256 * FP_ONE))
  local quad = floor(t / (64 * FP_ONE))
  t = t - quad * 64 * FP_ONE
  local x, y, z = K_INV, 0, t
  for i = 0, 19 do
    local p = POW2[i + 1]
    local d = z >= 0 and 1 or -1
    local nx = x - d * floor(y / p)
    local ny = y + d * floor(x / p)
    z = z - d * ATAN_BRAD[i + 1]
    x, y = nx, ny
  end
  x = floor((x + 128) / 256)
  y = floor((y + 128) / 256)
  if quad == 0 then return x, y end
  if quad == 1 then return -y, x end
  if quad == 2 then return -x, -y end
  return y, -x
end

local COS, SIN = {}, {}
for a = 0, 255 do
  local c, s = M.cordic(a * FP_ONE)
  COS[a + 1] = c
  SIN[a + 1] = s
end
M.COS = COS
M.SIN = SIN

-- 니블 xor 표. 16x16 = 256칸이면 8비트 xor 를 두 번 조회로 끝낼 수 있다.
local NIB_XOR = {}
for a = 0, 15 do
  for b = 0, 15 do
    local r, p, x, y = 0, 1, a, b
    for _ = 1, 4 do
      if x - 2 * floor(x / 2) ~= y - 2 * floor(y / 2) then r = r + p end
      x = floor(x / 2)
      y = floor(y / 2)
      p = p * 2
    end
    NIB_XOR[a * 16 + b + 1] = r
  end
end
M.NIB_XOR = NIB_XOR

-- 8비트 배타적 논리합. 니블 표 두 번이면 끝난다.
function M.xor8(a, b)
  local ah = floor(a / 16)
  local bh = floor(b / 16)
  return NIB_XOR[ah * 16 + bh + 1] * 16 + NIB_XOR[(a - ah * 16) * 16 + (b - bh * 16) + 1]
end

-- 표 없이 만든 16비트 배타적 논리합.
--
--   루아 5.1 에는 비트 연산자가 없다. LuaJIT 에는 bit 라이브러리가 있지만
--   그것은 5.1 표준이 아니고 LÖVE 밖에서 늘 있는 것도 아니라 쓰지 않는다.
--   나눗셈만으로 만들면 세 언어가 같은 코드를 돌게 된다. O(16).
function M.xor16(a, b)
  local r, p = 0, 1
  for _ = 1, 16 do
    local ha = floor(a / 2)
    local hb = floor(b / 2)
    if a - 2 * ha ~= b - 2 * hb then r = r + p end
    a = ha
    b = hb
    p = p * 2
  end
  return r
end

return M
