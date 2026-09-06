# -*- coding: utf-8 -*-
"""난수 — 주기·분할 곱·모듈로 편향 (SPEC §3)."""
from __future__ import print_function

import harness as H
from rts import rng as R

H.title('rng')

# ---- 골든 4절과 대조
rows = H.golden('prim.txt').split('\n')
i = rows.index('== 4. LCG ==') + 2
g = R.LCG(1)
bad = 0
for k in range(10):
    p = rows[i + k].split()
    v = g.next15()
    if g.s != int(p[1]) or v != int(p[2]):
        bad += 1
        H.note('%d번째: 기대 상태 %s next15 %s / 실제 %d %d', k + 1, p[1], p[2], g.s, v)
H.check('LCG 첫 10회가 골든과 같다', bad, 0)

# ---- 분할 곱이 직접 곱과 같은가 (파이썬에서만 확인할 수 있는 것)
g = R.LCG(12345)
bad = 0
direct = 12345
for _ in range(20000):
    g.next15()
    direct = (22695477 * direct + 1) % 4294967296
    if g.s != direct:
        bad += 1
        break
H.check('분할 곱 == (22695477*s+1) mod 2^32 (2만회)', bad, 0)

# ---- 중간값이 2^53 을 넘지 않는가
worst = 0
g = R.LCG(1)
for _ in range(5000):
    s = g.s
    worst = max(worst, 22695477 * (s % 65536), 22695477 * (s // 65536))
    g.next15()
H.check_true('분할 항의 최대 %d < 2^53' % worst, worst < 2 ** 53)

# ---- Hull–Dobell 세 조건 (SPEC 정리 3.2)
a, c, m = 22695477, 1, 2 ** 32
H.check('gcd(c, m) == 1', 1 if c == 1 else 0, 1)
H.check('m 의 소인수 2 가 a-1 을 나눈다', (a - 1) % 2, 0)
H.check('4 | m 이므로 4 | a-1', (a - 1) % 4, 0)

# ---- 하위 비트의 짧은 주기: 상태의 하위 k비트는 주기 2^k
bad = 0
for k in (1, 2, 3, 8):
    g = R.LCG(1)
    seen = []
    for _ in range(2 ** k * 3):
        g.next15()
        seen.append(g.s % (2 ** k))
    if seen[:2 ** k] != seen[2 ** k:2 ** k * 2]:
        bad += 1
H.check('상태 하위 k비트의 주기가 2^k', bad, 0)
H.note('그래서 next15 는 상위 15비트(비트 30..16)만 쓴다')

# ---- roll: 범위와 편향
g = R.LCG(2026)
bad = 0
for _ in range(20000):
    v = g.roll(7)
    if not (0 <= v < 7):
        bad += 1
H.check('roll(7) 범위', bad, 0)
H.check('roll(0)', R.LCG(1).roll(0), 0)
H.check('roll(1)', R.LCG(1).roll(1), 0)

i = rows.index('== 4. LCG ==')
line = [l for l in rows[i:i + 30] if l.startswith('roll(6) x20: ')][0]
want = [int(v) for v in line[len('roll(6) x20: '):].split()]
g = R.LCG(2026)
got = [g.roll(6) for _ in range(20)]
H.check('roll(6) 20회가 골든과 같다', got, want)
line = [l for l in rows[i:i + 30] if l.startswith('roll(6) x6000 도수: ')][0]
want = [int(v) for v in line[len('roll(6) x6000 도수: '):].split()]
g = R.LCG(2026)
hist = [0] * 6
for _ in range(6000):
    hist[g.roll(6)] += 1
H.check('roll(6) 6000회 도수가 골든과 같다', hist, want)
H.note('기각 %d회 — 기대 시도 횟수는 2 미만이어야 한다', g.rejects)
H.check_true('기각 횟수가 표본의 절반 미만', g.rejects < 3000)

# ---- 편향 실험: 기각 없이 나머지만 쓰면 어떻게 되는가
g = R.LCG(7)
biased = [0] * 3
n = 32768 * 4
for _ in range(n):
    biased[g.next15() % 3] += 1
H.note('나머지만 쓴 roll(3) 도수 %s (32768 이 3으로 나뉘지 않는다)', biased)
H.check_true('세 도수가 완전히 같지는 않다', len(set(biased)) > 1)

# ---- 상태 저장·복원
g = R.LCG(99)
for _ in range(50):
    g.next15()
s = g.save()
a = [g.next15() for _ in range(10)]
g.load(s)
b = [g.next15() for _ in range(10)]
H.check('save/load 후 같은 수열', a, b)

H.done()
