# -*- coding: utf-8 -*-
"""주사위 — 합성곱 분포, 기대값·분산을 정수 항등식으로."""
from __future__ import print_function

import harness as H
from isorpg import dice as D
from isorpg import rng as R

H.title('dice')

H.check('0면? 1d1', D.dist(1, 1), [0, 1])
H.check('1d6', D.dist(1, 6), [0, 1, 1, 1, 1, 1, 1])
H.check('2d6', D.dist(2, 6)[2:], [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])
H.check('3d6', D.dist(3, 6)[3:],
        [1, 3, 6, 10, 15, 21, 25, 27, 27, 25, 21, 15, 10, 6, 3, 1])

for n in range(1, 5):
    for mm in (4, 6, 8, 20):
        c = D.dist(n, mm)
        H.check('경우의 수 %dd%d' % (n, mm), sum(c), mm ** n)
        # 기대값 n(m+1)/2 를 정수 항등식으로: 2*sum(s*c[s]) == n*(m+1)*m^n
        H.check('기대값 %dd%d' % (n, mm),
                2 * sum(s * v for s, v in enumerate(c)), n * (mm + 1) * mm ** n)
        # 분산 n(m^2-1)/12 : 12*(sum(s^2 c) * m^n - (sum(s c))^2) == n(m^2-1) * m^(2n)
        s1 = sum(s * v for s, v in enumerate(c))
        s2 = sum(s * s * v for s, v in enumerate(c))
        H.check('분산 %dd%d' % (n, mm),
                12 * (s2 * mm ** n - s1 * s1), n * (mm * mm - 1) * mm ** (2 * n))
        H.check('%dd%d 분포는 좌우 대칭' % (n, mm), c[n:], list(reversed(c[n:])))

# ---- 명중률
H.check('to_hit(atk=0, def=0)', D.to_hit(0, 0), 11)
H.check('명중 눈의 수 (0,0)', D.p_hit(0, 0), 10)
H.check('아주 센 공격도 19/20 이 상한', D.p_hit(100, 0), 19)
H.check('아주 약한 공격도 1/20 은 남는다', D.p_hit(0, 100), 1)

# ---- 실제 굴림 분포가 이론과 어긋나지 않는가 (골든 난수)
r = R.Rng(4242)
cnt = [0] * 13
for _ in range(36000):
    cnt[D.roll(r, 2, 6)] += 1
exp = D.dist(2, 6)
worst = 0
for s in range(2, 13):
    e = exp[s] * 1000
    worst = max(worst, abs(cnt[s] - e) * 1000 // e)
H.note('2d6 36,000회 — 이론 대비 최대 편차 %d/1000', worst)
H.check_true('편차가 10%% 안', worst < 100)

# ---- 성장 곡선
H.check('xp_to_next(1)', D.xp_to_next(1), 50)
H.check('xp_to_next(2)', D.xp_to_next(2), 140)
H.check('xp_to_next(3)', D.xp_to_next(3), 270)
H.check_true('단조 증가', all(D.xp_to_next(l) < D.xp_to_next(l + 1) for l in range(1, 30)))

H.done()
