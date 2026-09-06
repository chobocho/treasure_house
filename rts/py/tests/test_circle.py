# -*- coding: utf-8 -*-
"""원 마스크 — 정의와 증분 계산이 같은 집합인가 (SPEC §6)."""
from __future__ import print_function

import harness as H
from rts import circle as C

H.title('circle')

# ---- 전수 비교: r = 1..64 에서 정의와 span 계산이 같은 집합인가
bad = 0
for r in range(1, 65):
    want = set((x, y) for y in range(-r, r + 1) for x in range(-r, r + 1)
               if x * x + y * y <= r * r)
    got = set(C.offsets(r))
    if want != got:
        bad += 1
        H.note('r=%d: 차집합 %s', r, sorted(want ^ got)[:8])
H.check('r=1..64 에서 disc_spans == {x²+y² <= r²}', bad, 0)

# ---- 가우스 원 문제의 개수 (SPEC 정리 6.1)
H.check('N(r), r=1..8', [len(C.offsets(r)) for r in range(1, 9)],
        [5, 13, 29, 49, 81, 113, 149, 197])

# ---- 골든 6절과 대조
rows = H.golden('prim.txt').split('\n')
i = rows.index('== 6. 원 마스크 ==') + 2
bad = 0
for r in range(1, 9):
    p = rows[i + r - 1].split()
    if int(p[1]) != len(C.offsets(r)):
        bad += 1
    if [int(v) for v in p[2:]] != C.spans(r):
        bad += 1
        H.note('r=%d span 기대 %s 실제 %s', r, p[2:], C.spans(r))
H.check('개수·span 이 골든과 같다', bad, 0)

# ---- 순회 순서가 고정인가 (SPEC §6.3)
o = C.offsets(3)
H.check('첫 원소', o[0], (0, -3))
H.check('마지막 원소', o[-1], (0, 3))
H.check_true('dy 오름차순, 같은 dy 안에서 dx 오름차순',
             all((o[k][1], o[k][0]) <= (o[k + 1][1], o[k + 1][0])
                 for k in range(len(o) - 1)))

# ---- 곱셈을 쓰지 않는가 (span 계산은 덧셈만)
H.check('spans(8)', C.spans(8), [8, 7, 7, 7, 6, 6, 5, 3, 0])
H.check('in_disc(3,3,5)', C.in_disc(3, 3, 5), True)
H.check('in_disc(4,4,5)', C.in_disc(4, 4, 5), False)

# ---- 고전 미드포인트 외곽선은 원 밖의 점을 찍는다 (SPEC §6.2)
out = C.midpoint_outline(2)
H.check_true('r=2 외곽선에 (2,1) 이 있다', (2, 1) in out)
H.check_true('그런데 (2,1) 은 원 밖이다', 2 * 2 + 1 * 1 > 2 * 2)
H.note('그래서 시야 마스크에 외곽선 알고리즘을 쓰면 개수가 가우스 값과 어긋난다')

# ---- 캐시가 같은 객체를 돌려주되 내용이 바뀌지 않는가
H.check('offsets 는 매번 같은 목록', C.offsets(5), C.offsets(5))

H.done()
