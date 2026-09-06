# -*- coding: utf-8 -*-
"""고정소수점 모듈 — 경계값과 오차 상계를 실제로 확인한다."""
from __future__ import print_function

import math

import harness as H
from isorpg import fixed as F

H.title('fixed')

# ---- floordiv / fmod : 음수에서도 내림인가
for a, b, q, r in [(7, 2, 3, 1), (-7, 2, -4, 1), (0, 3, 0, 0), (-1, 65536, -1, 65535),
                   (-65536, 65536, -1, 0), (-65537, 65536, -2, 65535)]:
    H.check('floordiv(%d,%d)' % (a, b), F.floordiv(a, b), q)
    H.check('fmod(%d,%d)' % (a, b), F.fmod(a, b), r)

# ---- fp 변환
H.check('fp(3)', F.fp(3), 196608)
H.check('fp_floor(-1)', F.fp_floor(-1), -1)
H.check('fp_round(32767)', F.fp_round(32767), 0)
H.check('fp_round(32768)', F.fp_round(32768), 1)
H.check('fp_frac(-1)', F.fp_frac(-1), 65535)

# ---- fp_mul : 분할 곱이 진짜 곱과 같은가 (전수는 못 하니 경계 + 무작위)
CASES = [(0, 0), (1, 1), (65536, 65536), (-65536, 65536), (65535, 65535),
         (-1, 1), (1, -1), (-1, -1), (2 ** 30, 3), (-(2 ** 30), 3),
         (46341, 46341), (13107, 46341), (2147483647, 5), (-2147483648, 5)]
rs = 12345
for _ in range(4000):
    rs = (1103515245 * rs + 12345) % (2 ** 31)
    a = rs % (2 ** 27) - 2 ** 26
    rs = (1103515245 * rs + 12345) % (2 ** 31)
    b = rs % (2 ** 27) - 2 ** 26
    CASES.append((a, b))
bad = 0
for a, b in CASES:
    if F.fp_mul(a, b) != (a * b) // 65536:
        bad += 1
H.check('fp_mul == floor(a*b/65536) (%d개)' % len(CASES), bad, 0)
H.note('중간값 상계 확인: |a|<2^31, |b|<2^37 에서 분할 곱의 항이 2^53 미만')

# ---- fp_div
bad = 0
for a, b in CASES:
    if b != 0 and abs(a) < 2 ** 27 and F.fp_div(a, b) != (a * 65536) // b:
        bad += 1
H.check('fp_div == floor(a*65536/b)', bad, 0)

# ---- isqrt : 0, 1, 완전제곱수 앞뒤, 큰 값
bad = 0
for n in list(range(0, 2000)) + [65535, 65536, 65537, 10 ** 6, 2 ** 32 - 1, 2 ** 43 - 1]:
    r = F.isqrt(n)
    if not (r * r <= n < (r + 1) * (r + 1)):
        bad += 1
H.check('isqrt 불변식 r^2 <= n < (r+1)^2', bad, 0)
H.check('isqrt(0)', F.isqrt(0), 0)
H.check('fp_sqrt(fp(1))', F.fp_sqrt(65536), 65536)
H.check('fp_sqrt(fp(2))', F.fp_sqrt(131072), 92681)

# ---- CORDIC : 참값과의 오차 상계 (테스트에서만 부동소수점을 쓴다)
mx = 0
for a in range(256):
    tc = int(round(65536 * math.cos(2 * math.pi * a / 256.0)))
    ts = int(round(65536 * math.sin(2 * math.pi * a / 256.0)))
    mx = max(mx, abs(F.COS[a] - tc), abs(F.SIN[a] - ts))
H.check_true('CORDIC 표 오차 <= 1 (실측 %d)' % mx, mx <= 1)
H.check('SIN[0]', F.SIN[0], 0)
H.check('COS[0]', F.COS[0], 65536)
H.check('SIN[32] == COS[32] == 46341', (F.SIN[32], F.COS[32]), (46341, 46341))
H.check('SIN[64]', F.SIN[64], 65536)
mx2 = max(abs(F.fp_mul(F.SIN[a], F.SIN[a]) + F.fp_mul(F.COS[a], F.COS[a]) - 65536)
          for a in range(256))
H.check_true('sin^2+cos^2 오차 <= 2/65536 (실측 %d)' % mx2, mx2 <= 2)

# ---- 팔각 거리 오차
lo, hi = 10 ** 9, -10 ** 9
for a in range(256):
    dx = F.floordiv(1000 * F.COS[a], 65536)
    dy = F.floordiv(1000 * F.SIN[a], 65536)
    ex = F.isqrt(dx * dx + dy * dy)
    if ex:
        e = F.floordiv((F.oct_dist(dx, dy) - ex) * 1000000, ex)
        lo, hi = min(lo, e), max(hi, e)
H.note('팔각 거리 상대오차 %d ~ %d ppm', lo, hi)
H.check_true('팔각 거리 오차가 ±5%% 안', -50000 < lo and hi < 50000)
H.check('oct_dist(3,4)', F.oct_dist(3, 4), 5)
H.check('oct_dist(0,0)', F.oct_dist(0, 0), 0)

# ---- xor16 : 표 없이 만든 배타적 논리합이 진짜 xor 인가
bad = 0
for a in range(0, 65536, 251):
    for b in range(0, 65536, 257):
        if F.xor16(a, b) != (a ^ b):
            bad += 1
H.check('xor16 == ^ (표본 %d쌍)' % (len(range(0, 65536, 251)) * len(range(0, 65536, 257))),
        bad, 0)

H.done()
