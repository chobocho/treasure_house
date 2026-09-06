-- 고정소수점·거리·방향 — 경계값과 오차 상계를 실제로 확인한다 (SPEC §1, §2).

local H = require('tests.harness')
local F = require('rts.fixed')
local C = require('rts.const')

H.title('fixed')

-- ---- floordiv / fmod : 음수에서도 내림인가
for _, t in ipairs({{7, 2, 3, 1}, {-7, 2, -4, 1}, {0, 3, 0, 0},
                    {-1, 65536, -1, 65535}, {-65536, 65536, -1, 0},
                    {-65537, 65536, -2, 65535}}) do
    local a, b, q, r = t[1], t[2], t[3], t[4]
    H.check(string.format('floordiv(%d,%d)', a, b), F.floordiv(a, b), q)
    H.check(string.format('fmod(%d,%d)', a, b), F.fmod(a, b), r)
end

-- ---- 비트 연산의 산술 대체 (SPEC §1.1)
for _, t in ipairs({{0, 0, 0}, {1, 0, 1}, {2, 0, 0}, {2, 1, 1},
                    {255, 7, 1}, {128, 7, 1}}) do
    H.check(string.format('bit(%d,%d)', t[1], t[2]), F.bit(t[1], t[2]), t[3])
end
H.check('setbit(0,3)', F.setbit(0, 3), 8)
H.check('setbit(8,3)', F.setbit(8, 3), 8)
H.check('clrbit(9,3)', F.clrbit(9, 3), 1)
H.check('clrbit(1,3)', F.clrbit(1, 3), 1)

-- 루아 5.1 에는 XOR 연산자가 없다. 시험에서만 독립 기준이 필요하므로
-- LuaJIT/LÖVE 의 bit 모듈을 오라클로 쓰고, 없으면 표로 만든 기준을 쓴다.
-- 엔진 쪽(rts/*.lua)은 여전히 비트 모듈을 쓰지 않는다(SPEC §1.1).
local ok_bit, bitlib = pcall(require, 'bit')
local function ref_xor(a, b)
    if ok_bit then return bitlib.band(bitlib.bxor(a, b), 255) end
    -- 대체 기준: 자리올림 없는 덧셈을 자릿수 표로 직접 만든다
    local r, p = 0, 1
    for _ = 1, 8 do
        local x, y = a % 2, b % 2
        if x + y == 1 then r = r + p end
        a = (a - x) / 2
        b = (b - y) / 2
        p = p * 2
    end
    return r
end
local bad = 0
for a = 0, 255 do
    for b = 0, 255, 7 do
        if F.xor8(a, b) ~= ref_xor(a, b) then bad = bad + 1 end
    end
end
H.check('xor8 == ^ (전수 근사)', bad, 0)
H.check('xor_low8(0x12345678, 0xFF)', F.xor_low8(305419896, 255), 305419911)

-- ---- fp 변환
H.check('fp(3)', F.fp(3), 196608)
H.check('fp_floor(-1)', F.fp_floor(-1), -1)
H.check('fp_round(32767)', F.fp_round(32767), 0)
H.check('fp_round(32768)', F.fp_round(32768), 1)
H.check('fp_frac(-1)', F.fp_frac(-1), 65535)
H.check('FP_DIAG', F.FP_DIAG, 46341)
H.check('FP_SQRT2M1', F.FP_SQRT2M1, 27146)

-- ---- fp_mul : 분할 곱이 진짜 곱과 같은가
local CASES = {}
for _, p in ipairs({{0, 0}, {1, 1}, {65536, 65536}, {-65536, 65536},
                    {65535, 65535}, {-1, 1}, {1, -1}, {-1, -1},
                    {1073741824, 3}, {-1073741824, 3}, {46341, 46341},
                    {13107, 46341}, {2147483647, 5}, {-2147483648, 5}}) do
    CASES[#CASES + 1] = p
end
-- 파이썬 시험이 쓰는 것과 같은 보조 LCG. 1103515245*rs 는 2^61 까지 커지므로
-- 루아에서는 그대로 곱하면 가수를 넘는다 — 여기서도 분할 곱을 쓴다.
local function lcg31(rs)
    local hi = math.floor(rs / 65536)
    local lo = rs % 65536
    return ((1103515245 * hi % 32768) * 65536 + 1103515245 * lo + 12345)
           % 2147483648
end
local rs = 12345
for _ = 1, 4000 do
    rs = lcg31(rs)
    local a = rs % 134217728 - 67108864
    rs = lcg31(rs)
    local b = rs % 134217728 - 67108864
    CASES[#CASES + 1] = {a, b}
end
bad = 0
local big = 0
for _, p in ipairs(CASES) do
    local a, b = p[1], p[2]
    if F.fp_mul(a, b) ~= F.floordiv(a * b, 65536) then bad = bad + 1 end
    local ah = F.floordiv(a, 65536)
    local al = a - ah * 65536
    local u = ah * b; if u < 0 then u = -u end
    local v = al * b; if v < 0 then v = -v end
    if u > big then big = u end
    if v > big then big = v end
end
H.check(string.format('fp_mul == floor(a*b/65536) (%d개)', #CASES), bad, 0)
H.check_true(string.format('분할 곱 중간값 < 2^53 (최대 %d)', big),
             big < 9007199254740992)

-- ---- fp_div
bad = 0
for _, p in ipairs(CASES) do
    local a, b = p[1], p[2]
    local aa = a < 0 and -a or a
    if b ~= 0 and aa < 134217728 and F.fp_div(a, b) ~= F.floordiv(a * 65536, b) then
        bad = bad + 1
    end
end
H.check('fp_div == floor(a*65536/b)', bad, 0)
if pcall(function() F.fp_div(1, 0) end) then
    H.check('fp_div(1,0) 은 터져야 한다', 'no raise', 'raise')
else
    H.check('fp_div(1,0) 은 터져야 한다', 'raise', 'raise')
end

-- ---- isqrt
bad = 0
local ns = {}
for n = 0, 1999 do ns[#ns + 1] = n end
for _, n in ipairs({65535, 65536, 65537, 1000000, 2147483647, 1099511627776}) do
    ns[#ns + 1] = n
end
for _, n in ipairs(ns) do
    local r = F.isqrt(n)
    if not (r * r <= n and n < (r + 1) * (r + 1)) then bad = bad + 1 end
end
H.check('isqrt 는 floor(sqrt(n))', bad, 0)
H.check('fp_sqrt(fp(4))', F.fp_sqrt(F.fp(4)), F.fp(2))

-- ---- 거리 척도 (SPEC §2.6) — 골든 1절과 대조
local rows = H.lines(H.golden('prim.txt'))
local i = H.index_of(rows, '== 1. 거리 척도 ==') + 2
bad = 0
local n = 0
while H.strip(rows[i]) ~= '' and rows[i]:sub(1, 3) ~= 'eu3' do
    local v = H.ints(rows[i])
    local dx, dy = v[0], v[1]
    local got = {[0] = F.d1(dx, dy), F.dinf(dx, dy), F.d83(dx, dy),
                 F.dab(dx, dy), F.doct(dx, dy), n = 5}
    local want = {[0] = v[2], v[3], v[4], v[5], v[6], n = 5}
    if not H.deep_eq(got, want) then
        bad = bad + 1
        H.note('%d,%d 기대 %s 실제 %s', dx, dy, H.repr(want), H.repr(got))
    end
    n = n + 1
    i = i + 1
end
H.check(string.format('거리 척도 %d줄이 골든과 같다', n), bad, 0)
H.check('dab(1,0) 은 0 이 아니다', F.dab(1, 0), 1)
H.check('dinf 는 8방향 걸음 수', F.dinf(-7, 3), 7)

-- ---- atan8 (SPEC §2.7)
i = H.index_of(rows, '== 3. 8방향 판별 ==') + 2
bad = 0
n = 0
while i < rows.n and H.strip(rows[i]) ~= '' do
    local p = H.split(rows[i])
    local dx, dy, want = tonumber(p[0]), tonumber(p[1]), tonumber(p[5])
    if F.atan8(dx, dy) ~= want then
        bad = bad + 1
        H.note('atan8(%d,%d) 기대 %d 실제 %d', dx, dy, want, F.atan8(dx, dy))
    end
    n = n + 1
    i = i + 1
end
H.check(string.format('atan8 %d줄이 골든과 같다', n), bad, 0)
H.check('atan8(0,0) 은 E', F.atan8(0, 0), 2)
bad = 0
for d = 0, 7 do
    if F.atan8(F.DX[d] * 9, F.DY[d] * 9) ~= d then bad = bad + 1 end
end
H.check('여덟 방향의 대표 벡터가 자기 번호로 돌아온다', bad, 0)
H.note('경계각 tan22.5 ~ 5/12: (12,5)는 대각, (12,4)는 직각 방향')

-- ── 골든 13절 CRC·FNV (SPEC §20.1, §18.4) ───────────────────────────────────
i = H.index_of(rows, '== 13. CRC 와 FNV ==') + 1
bad = 0
n = 0
while i < rows.n and H.strip(rows[i]) ~= '' do
    local line = rows[i]
    local fn = line:match('^(%S+)')
    local hex = line:match('(%S+)%s*$')
    -- 파이썬의 rsplit(None, 2)[0] — 뒤에서 토큰 둘을 떼고 남은 것이 인자다
    local rest = line:sub(#fn + 1)
    rest = rest:gsub('%s+%S+%s*$', ''):gsub('%s+%S+%s*$', '')
    rest = H.strip(rest)
    local data
    if rest == 'bytes(0..15)' then
        data = {n = 16}
        for k = 0, 15 do data[k] = k end
    else
        data = rest:sub(2, #rest - 1)            -- 골든이 repr 로 적었다
    end
    local got = (fn == 'crc16') and F.crc16(data) or F.fnv1a(data)
    if got ~= tonumber(hex:sub(3), 16) then
        bad = bad + 1
        H.note('%s %s 기대 %s 실제 %d', fn, rest, hex, got)
    end
    n = n + 1
    i = i + 1
end
H.check(string.format('골든 13절 %d줄 (crc16·fnv1a)', n), bad, 0)
H.check('FNV 오프셋과 소수', {[0] = F.FNV_OFFSET, F.FNV_PRIME, n = 2},
        {[0] = 2166136261, 16777619, n = 2})
H.check('빈 입력의 fnv1a 는 오프셋 그대로', F.fnv1a(''), F.FNV_OFFSET)
H.check('한 바이트 차이가 해시를 바꾼다',
        F.fnv1a('\0') ~= F.fnv1a('\1'), true)
local mx = 0
for k = 0, 255 do
    local v = F.fnv1a(string.char(k))
    if v > mx then mx = v end
end
H.check('32비트를 넘지 않는다', mx < 4294967296, true)

-- ── fixed 와 const 에 두 번 적힌 값은 서로 같아야 한다 (SPEC §0) ────────────
H.check('fixed 와 const 의 §0 값이 일치',
        {[0] = F.FP_BITS, F.FP_ONE, F.FP_HALF, F.FP_DIAG, F.FP_SQRT2M1,
         F.D_STRAIGHT, F.D_DIAG, n = 7},
        {[0] = C.FP_BITS, C.FP_ONE, C.FP_HALF, C.FP_DIAG, C.FP_SQRT2M1,
         C.D_STRAIGHT, C.D_DIAG, n = 7})

return H.done()
