# -*- coding: utf-8 -*-
"""고정소수점·거리·방향 — 경계값과 오차 상계를 실제로 확인한다 (SPEC §1, §2)."""
from __future__ import print_function

import math

import harness as H
from rts import fixed as F

H.title('fixed')

# ---- floordiv / fmod : 음수에서도 내림인가
for a, b, q, r in [(7, 2, 3, 1), (-7, 2, -4, 1), (0, 3, 0, 0), (-1, 65536, -1, 65535),
                   (-65536, 65536, -1, 0), (-65537, 65536, -2, 65535)]:
    H.check('floordiv(%d,%d)' % (a, b), F.floordiv(a, b), q)
    H.check('fmod(%d,%d)' % (a, b), F.fmod(a, b), r)

# ---- 비트 연산의 산술 대체 (SPEC §1.1)
for v, k, want in [(0, 0, 0), (1, 0, 1), (2, 0, 0), (2, 1, 1), (255, 7, 1), (128, 7, 1)]:
    H.check('bit(%d,%d)' % (v, k), F.bit(v, k), want)
H.check('setbit(0,3)', F.setbit(0, 3), 8)
H.check('setbit(8,3)', F.setbit(8, 3), 8)
H.check('clrbit(9,3)', F.clrbit(9, 3), 1)
H.check('clrbit(1,3)', F.clrbit(1, 3), 1)
bad = 0
for a in range(256):
    for b in range(0, 256, 7):
        if F.xor8(a, b) != (a ^ b):
            bad += 1
H.check('xor8 == ^ (전수 근사)', bad, 0)
H.check('xor_low8(0x12345678, 0xFF)', F.xor_low8(0x12345678, 0xFF), 0x12345687)

# ---- fp 변환
H.check('fp(3)', F.fp(3), 196608)
H.check('fp_floor(-1)', F.fp_floor(-1), -1)
H.check('fp_round(32767)', F.fp_round(32767), 0)
H.check('fp_round(32768)', F.fp_round(32768), 1)
H.check('fp_frac(-1)', F.fp_frac(-1), 65535)
H.check('FP_DIAG', F.FP_DIAG, 46341)
H.check('FP_SQRT2M1', F.FP_SQRT2M1, 27146)

# ---- fp_mul : 분할 곱이 진짜 곱과 같은가
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
big = 0
for a, b in CASES:
    if F.fp_mul(a, b) != (a * b) // 65536:
        bad += 1
    ah = a // 65536
    al = a % 65536
    big = max(big, abs(ah * b), abs(al * b))
H.check('fp_mul == floor(a*b/65536) (%d개)' % len(CASES), bad, 0)
H.check_true('분할 곱 중간값 < 2^53 (최대 %d)' % big, big < 2 ** 53)

# ---- fp_div
bad = 0
for a, b in CASES:
    if b != 0 and abs(a) < 2 ** 27 and F.fp_div(a, b) != (a * 65536) // b:
        bad += 1
H.check('fp_div == floor(a*65536/b)', bad, 0)
try:
    F.fp_div(1, 0)
    H.check('fp_div(1,0) 은 터져야 한다', 'no raise', 'raise')
except ZeroDivisionError:
    H.check('fp_div(1,0) 은 터져야 한다', 'raise', 'raise')

# ---- isqrt
bad = 0
for n in list(range(0, 2000)) + [65535, 65536, 65537, 1000000, 2 ** 31 - 1, 2 ** 40]:
    r = F.isqrt(n)
    if not (r * r <= n < (r + 1) * (r + 1)):
        bad += 1
H.check('isqrt 는 floor(sqrt(n))', bad, 0)
H.check('fp_sqrt(fp(4))', F.fp_sqrt(F.fp(4)), F.fp(2))

# ---- 거리 척도 (SPEC §2.6) — 골든 1절과 대조
rows = [l for l in H.golden('prim.txt').split('\n')]
i = rows.index('== 1. 거리 척도 ==') + 2
bad = 0
n = 0
while rows[i].strip() and not rows[i].startswith('eu3'):
    v = [int(x) for x in rows[i].split()]
    dx, dy = v[0], v[1]
    got = [F.d1(dx, dy), F.dinf(dx, dy), F.d83(dx, dy), F.dab(dx, dy), F.doct(dx, dy)]
    if got != v[2:7]:
        bad += 1
        H.note('%d,%d 기대 %s 실제 %s', dx, dy, v[2:7], got)
    n += 1
    i += 1
H.check('거리 척도 %d줄이 골든과 같다' % n, bad, 0)
H.check('dab(1,0) 은 0 이 아니다', F.dab(1, 0), 1)
H.check('dinf 는 8방향 걸음 수', F.dinf(-7, 3), 7)

# ---- atan8 (SPEC §2.7)
i = rows.index('== 3. 8방향 판별 ==') + 2
bad = 0
n = 0
while i < len(rows) and rows[i].strip():
    p = rows[i].split()
    dx, dy, want = int(p[0]), int(p[1]), int(p[5])
    if F.atan8(dx, dy) != want:
        bad += 1
        H.note('atan8(%d,%d) 기대 %d 실제 %d', dx, dy, want, F.atan8(dx, dy))
    n += 1
    i += 1
H.check('atan8 %d줄이 골든과 같다' % n, bad, 0)
H.check('atan8(0,0) 은 E', F.atan8(0, 0), 2)
bad = 0
for d in range(8):
    if F.atan8(F.DX[d] * 9, F.DY[d] * 9) != d:
        bad += 1
H.check('여덟 방향의 대표 벡터가 자기 번호로 돌아온다', bad, 0)
H.note('경계각 tan22.5 ~ 5/12: (12,5)는 대각, (12,4)는 직각 방향')

H.done()
