-- 주사위 — 합성곱 분포, 기대값·분산을 정수 항등식으로.

local H = require("tests.harness")
local D = require("isorpg.dice")
local R = require("isorpg.rng")

H.title('dice')

-- dist 는 1-기반이라 '합 s' 가 c[s+1] 이다. 파이썬의 c[n:] 는 여기서 c[n+1..] 이다.
local function tail(c, from)
  local t = {}
  for i = from + 1, #c do t[#t + 1] = c[i] end
  return t
end

H.check('0면? 1d1', D.dist(1, 1), {0, 1})
H.check('1d6', D.dist(1, 6), {0, 1, 1, 1, 1, 1, 1})
H.check('2d6', tail(D.dist(2, 6), 2), {1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1})
H.check('3d6', tail(D.dist(3, 6), 3),
        {1, 3, 6, 10, 15, 21, 25, 27, 27, 25, 21, 15, 10, 6, 3, 1})

for n = 1, 4 do
  for _, mm in ipairs({4, 6, 8, 20}) do
    local c = D.dist(n, mm)
    local tot, s1, s2 = 0, 0, 0
    for i = 1, #c do
      local s = i - 1
      tot = tot + c[i]
      s1 = s1 + s * c[i]
      s2 = s2 + s * s * c[i]
    end
    local mn = mm ^ n
    H.check(string.format('경우의 수 %dd%d', n, mm), tot, mn)
    -- 기대값 n(m+1)/2 를 정수 항등식으로: 2*sum(s*c[s]) == n*(m+1)*m^n
    H.check(string.format('기대값 %dd%d', n, mm), 2 * s1, n * (mm + 1) * mn)
    -- 분산 n(m^2-1)/12 : 12*(sum(s^2 c) * m^n - (sum(s c))^2) == n(m^2-1) * m^(2n)
    H.check(string.format('분산 %dd%d', n, mm),
            12 * (s2 * mn - s1 * s1), n * (mm * mm - 1) * (mm ^ (2 * n)))
    local t = tail(c, n)
    local rev = {}
    for i = #t, 1, -1 do rev[#rev + 1] = t[i] end
    H.check(string.format('%dd%d 분포는 좌우 대칭', n, mm), t, rev)
  end
end

-- ---- 명중률
H.check('to_hit(atk=0, def=0)', D.to_hit(0, 0), 11)
H.check('명중 눈의 수 (0,0)', D.p_hit(0, 0), 10)
H.check('아주 센 공격도 19/20 이 상한', D.p_hit(100, 0), 19)
H.check('아주 약한 공격도 1/20 은 남는다', D.p_hit(0, 100), 1)

-- ---- 실제 굴림 분포가 이론과 어긋나지 않는가 (골든 난수)
local r = R.new(4242)
local cnt = {}
for i = 1, 13 do cnt[i] = 0 end
for _ = 1, 36000 do
  local s = D.roll(r, 2, 6)
  cnt[s + 1] = cnt[s + 1] + 1
end
local exp = D.dist(2, 6)
local worst = 0
for s = 2, 12 do
  local e = exp[s + 1] * 1000
  local d = cnt[s + 1] - e
  if d < 0 then d = -d end
  local v = math.floor(d * 1000 / e)
  if v > worst then worst = v end
end
H.note('2d6 36,000회 — 이론 대비 최대 편차 %d/1000', worst)
H.check_true('편차가 10% 안', worst < 100)

-- ---- 성장 곡선
H.check('xp_to_next(1)', D.xp_to_next(1), 50)
H.check('xp_to_next(2)', D.xp_to_next(2), 140)
H.check('xp_to_next(3)', D.xp_to_next(3), 270)
local mono = true
for l = 1, 29 do
  if not (D.xp_to_next(l) < D.xp_to_next(l + 1)) then mono = false end
end
H.check_true('단조 증가', mono)

H.done()
