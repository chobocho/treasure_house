# -*- coding: utf-8 -*-
"""맵 — LCG, 다이아몬드-스퀘어, 셀 패킹, RLE 왕복."""
from __future__ import print_function

import harness as H
from isorpg import gamemap as M
from isorpg import rng as R

H.title('gamemap')

# ---- LCG : 골든 앞 8개
r = R.Rng(1)
got = []
for _ in range(8):
    v = r.next()
    got.append((r.s, v))
H.check('seed 1 첫 상태', got[0], (22695478, 346))
H.check('seed 1 여덟째 상태', got[7], (420428313, 6415))
H.check('rand15 범위', all(0 <= v < 32768 for _, v in got), True)

# ---- 분할 곱이 진짜 곱과 같은가 (2^53 우회로 검증)
s = 1
bad = 0
for _ in range(20000):
    want = (R.LCG_A * s + R.LCG_C) % R.LCG_M
    s2 = R.Rng(s)
    s2.next()
    if s2.s != want:
        bad += 1
    s = want
H.check('분할 곱 == (a*s+c) mod 2^32 (2만 걸음)', bad, 0)

# ---- Hull-Dobell 조건
H.check('gcd(c, m) = 1', R.LCG_C % 2, 1)
H.check('(a-1) 이 2로 나누어짐', (R.LCG_A - 1) % 2, 0)
H.check('(a-1) 이 4로 나누어짐', (R.LCG_A - 1) % 4, 0)

# ---- 주기: 하위 비트는 주기가 짧다 (도스 시절의 유명한 함정)
seen = []
s = 1
for _ in range(16):
    s = (R.LCG_A * s + R.LCG_C) % R.LCG_M
    seen.append(s % 2)
H.check('상태 최하위 비트는 0,1 을 번갈아 (주기 2)', seen, [0, 1] * 8)

# ---- 셀 패킹
for t in range(16):
    for h in range(16):
        c = M.make_cell(t, h)
        H.check_true('패킹 t=%d h=%d' % (t, h),
                     M.terrain_of(c) == t and M.height_of(c) == h and 0 <= c < 256)

# ---- 다이아몬드-스퀘어 5x5 골든
mini = M.gen_height(4, [50, 60, 70, 80], 100, 1)
H.check('5x5 격자', mini,
        [[50, 58, 103, 41, 60], [29, 49, 51, 87, 29], [104, 114, 110, 73, 68],
         [137, 150, 171, 137, 81], [70, 152, 185, 114, 80]])
H.check('두 번 돌려도 같은가', M.gen_height(4, [50, 60, 70, 80], 100, 1), mini)

# ---- 실제 맵
m = M.gen_map()
H.check('맵 크기', (m.w, m.h, len(m.cells)), (48, 48, 48 * 48))
H.check_true('모든 셀이 0..255', all(0 <= c < 256 for c in m.cells))
H.check_true('높이는 0..15', all(M.height_of(c) <= 15 for c in m.cells))

# ---- 마을이 제대로 찍혔는가
H.check('마을 네 귀퉁이는 벽', [M.terrain_of(m.at(x, y))
                                for x, y in [(18, 18), (29, 18), (18, 29), (29, 29)]],
        [M.T_WALL] * 4)
H.check('남문은 길', M.terrain_of(m.at(24, 29)), M.T_ROAD)
H.check('마을 안 높이는 2', sorted(set(M.height_of(m.at(x, y))
                                      for y in range(18, 30) for x in range(18, 30))), [2])
H.check('마을 남쪽 길', [M.terrain_of(m.at(24, y)) for y in (31, 35, 40, 47)],
        [M.T_ROAD] * 4)

# ---- RLE 왕복
text = M.save_rle(m)
m2 = M.load_rle(text)
H.check('RLE 왕복', bytes(m2.cells), bytes(m.cells))
H.check('RLE 다시 저장해도 같은 글자', M.save_rle(m2), text)
H.check_true('RLE 가 원본보다 짧다 (%d바이트 -> %d바이트)'
             % (len(m.cells), len(text.encode('utf-8'))),
             len(text.encode('utf-8')) < len(m.cells) * 2)

# ---- 골든 파일과 같은가
H.check('golden/map.txt', text, H.golden('map.txt'))

H.done()
