-- 난수 — 주기·분할 곱·모듈로 편향 (SPEC §3).

local H = require('tests.harness')
local R = require('rts.rng')

H.title('rng')

-- ---- 골든 4절과 대조
local rows = H.lines(H.golden('prim.txt'))
local i = H.index_of(rows, '== 4. LCG ==') + 2
local g = R.new(1)
local bad = 0
for k = 0, 9 do
    local p = H.split(rows[i + k])
    local v = g:next15()
    if g.s ~= tonumber(p[1]) or v ~= tonumber(p[2]) then
        bad = bad + 1
        H.note('%d번째: 기대 상태 %s next15 %s / 실제 %d %d',
               k + 1, p[1], p[2], g.s, v)
    end
end
H.check('LCG 첫 10회가 골든과 같다', bad, 0)

-- ---- 분할 곱이 직접 곱과 같은가
-- 파이썬은 큰 정수를 그대로 곱해 확인하지만 루아에는 그런 정수가 없다.
-- 그래서 rng 와 **다른 자리(2^10)** 에서 쪼갠 곱을 기준으로 삼는다 — 같은
-- 코드 경로를 두 번 도는 것이 아니라는 점이 이 시험의 요점이다.
local function direct_step(s)
    local q = math.floor(s / 1024)
    local r = s % 1024
    return ((22695477 * q % 4194304) * 1024 + 22695477 * r + 1) % 4294967296
end
g = R.new(12345)
bad = 0
local direct = 12345
for _ = 1, 20000 do
    g:next15()
    direct = direct_step(direct)
    if g.s ~= direct then
        bad = bad + 1
        break
    end
end
H.check('분할 곱 == (22695477*s+1) mod 2^32 (2만회)', bad, 0)

-- ---- 중간값이 2^53 을 넘지 않는가
local worst = 0
g = R.new(1)
for _ = 1, 5000 do
    local s = g.s
    local a = 22695477 * (s % 65536)
    local b = 22695477 * math.floor(s / 65536)
    if a > worst then worst = a end
    if b > worst then worst = b end
    g:next15()
end
H.check_true(string.format('분할 항의 최대 %d < 2^53', worst),
             worst < 9007199254740992)

-- ---- Hull–Dobell 세 조건 (SPEC 정리 3.2)
local a, c = 22695477, 1
H.check('gcd(c, m) == 1', c == 1 and 1 or 0, 1)
H.check('m 의 소인수 2 가 a-1 을 나눈다', (a - 1) % 2, 0)
H.check('4 | m 이므로 4 | a-1', (a - 1) % 4, 0)

-- ---- 하위 비트의 짧은 주기: 상태의 하위 k비트는 주기 2^k
bad = 0
for _, k in ipairs({1, 2, 3, 8}) do
    g = R.new(1)
    local period = 2 ^ k
    local seen = {}
    for j = 1, period * 3 do
        g:next15()
        seen[j] = g.s % period
    end
    local same = true
    for j = 1, period do
        if seen[j] ~= seen[j + period] then same = false; break end
    end
    if not same then bad = bad + 1 end
end
H.check('상태 하위 k비트의 주기가 2^k', bad, 0)
H.note('그래서 next15 는 상위 15비트(비트 30..16)만 쓴다')

-- ---- roll: 범위와 편향
g = R.new(2026)
bad = 0
for _ = 1, 20000 do
    local v = g:roll(7)
    if not (v >= 0 and v < 7) then bad = bad + 1 end
end
H.check('roll(7) 범위', bad, 0)
H.check('roll(0)', R.new(1):roll(0), 0)
H.check('roll(1)', R.new(1):roll(1), 0)

i = H.index_of(rows, '== 4. LCG ==')
local PRE1 = 'roll(6) x20: '
local line
for k = i, i + 29 do
    if rows[k] and rows[k]:sub(1, #PRE1) == PRE1 then line = rows[k]; break end
end
local want = H.ints(line:sub(#PRE1 + 1))
g = R.new(2026)
local got = {n = 20}
for k = 0, 19 do got[k] = g:roll(6) end
H.check('roll(6) 20회가 골든과 같다', got, want)

local PRE2 = 'roll(6) x6000 도수: '
for k = i, i + 29 do
    if rows[k] and rows[k]:sub(1, #PRE2) == PRE2 then line = rows[k]; break end
end
want = H.ints(line:sub(#PRE2 + 1))
g = R.new(2026)
local hist = {n = 6}
for k = 0, 5 do hist[k] = 0 end
for _ = 1, 6000 do
    local v = g:roll(6)
    hist[v] = hist[v] + 1
end
H.check('roll(6) 6000회 도수가 골든과 같다', hist, want)
H.note('기각 %d회 — 기대 시도 횟수는 2 미만이어야 한다', g.rejects)
H.check_true('기각 횟수가 표본의 절반 미만', g.rejects < 3000)

-- ---- 편향 실험: 기각 없이 나머지만 쓰면 어떻게 되는가
g = R.new(7)
local biased = {[0] = 0, 0, 0, n = 3}
for _ = 1, 32768 * 4 do
    local v = g:next15() % 3
    biased[v] = biased[v] + 1
end
H.note('나머지만 쓴 roll(3) 도수 %s (32768 이 3으로 나뉘지 않는다)',
       H.repr(biased))
local uniq = 0
for k = 0, 2 do
    local dup = false
    for j = 0, k - 1 do if biased[j] == biased[k] then dup = true end end
    if not dup then uniq = uniq + 1 end
end
H.check_true('세 도수가 완전히 같지는 않다', uniq > 1)

-- ---- 상태 저장·복원
g = R.new(99)
for _ = 1, 50 do g:next15() end
local s = g:save()
local va = {n = 10}
for k = 0, 9 do va[k] = g:next15() end
g:load(s)
local vb = {n = 10}
for k = 0, 9 do vb[k] = g:next15() end
H.check('save/load 후 같은 수열', va, vb)

return H.done()
