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
        [[50, 40, 103, 132, 60], [86, 130, 106, 72, 72], [104, 73, 110, 94, 68],
         [82, 156, 116, 68, 130], [70, 88, 185, 145, 80]])
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
H.check('마을 바닥은 높이 2, 성벽은 4',
        sorted(set(M.height_of(m.at(x, y))
                   for y in range(18, 30) for x in range(18, 30))), [2, 4])
H.check('성벽 한 줄', [M.terrain_of(m.at(x, 18)) for x in range(19, 24)],
        [M.T_WALL] * 5)
H.check('마을 남쪽 길', [M.terrain_of(m.at(24, y)) for y in (31, 35, 40, 47)],
        [M.T_ROAD] * 4)
H.check_true('지형이 7종 이상 나온다',
             len(set(M.terrain_of(c) for c in m.cells)) >= 7)
H.check_true('높이가 5단계 이상 나온다',
             len(set(M.height_of(c) for c in m.cells)) >= 5)

# ---- RLE 왕복
text = M.save_rle(m)
m2 = M.load_rle(text)
H.check('RLE 왕복', bytes(m2.cells), bytes(m.cells))
H.check('RLE 다시 저장해도 같은 글자', M.save_rle(m2), text)
# 런 하나는 (개수, 값) 두 바이트다. 도스 파일 형식이라면 그렇게 저장한다.
# 여기 텍스트 형식은 사람이 읽으려고 늘려 쓴 것이라 원본보다 길다 — 정직하게 둘 다 센다.
runs = sum(len(l.split()) for l in text.strip().split('\n')[1:])
H.note('셀 %d개 -> 런 %d개 (이진 RLE %d바이트, 텍스트 %d바이트)',
       len(m.cells), runs, runs * 2, len(text.encode('utf-8')))
H.check_true('이진 RLE 는 원본보다 짧다', runs * 2 < len(m.cells))
H.check_true('평균 런 길이가 2.5 이상', len(m.cells) * 10 // runs >= 25)

# ---- 골든 파일과 같은가
H.check('golden/map.txt', text, H.golden('map.txt'))

H.done()
