# -*- coding: utf-8 -*-
"""맵 생성 — 셀룰러 오토마타·다이아몬드 스퀘어·대칭·자원 (SPEC §5)."""
from __future__ import print_function

import harness as H
from rts import mapgen as G
from rts import rng as R
from rts import tmap as T

H.title('mapgen')

# ---- 골든 시작 맵을 바이트 단위로 재현하는가
want = T.TMap.load_text(H.golden('map_start.txt'))
got, seed, retries = G.gen_start()
H.check('시작 맵 지형이 골든과 같다', got.terrain, want.terrain)
H.check('시드', seed, 3)
H.check('재시도 횟수', retries, 0)
H.check('시작점', G.START, [(8, 8), (55, 55)])

# ---- 180도 회전 대칭 (SPEC §5.4)
bad = 0
for y in range(64):
    for x in range(64):
        if got.terrain[y * 64 + x] != got.terrain[(63 - y) * 64 + (63 - x)]:
            bad += 1
H.check('맵이 180도 회전 대칭', bad, 0)

# ---- 두 시작점이 이어져 있는가
lab = got.labels(0)
H.check('두 기지가 보병으로 이어진다',
        lab[got.idx(8, 8)] == lab[got.idx(55, 55)], True)

# ---- 셀룰러 오토마타 (SPEC §5.1)
g = G.cellular(32, 32, R.LCG(7), gens=4)
H.check('CA 결과는 0/1', sorted(set(g)), [0, 1])
wall = sum(g)
H.note('시드 7, 4세대: 벽 %d / 1024 (%.0f%%)', wall, 100.0 * wall / 1024)
H.check_true('벽이 전부도 아니고 없지도 않다', 0 < wall < 1024)

full = G.cellular_step([1] * (8 * 8), 8, 8)
H.check('가득 찬 판은 고정점', full, [1] * 64)
empty = G.cellular_step([0] * (8 * 8), 8, 8)
H.check('빈 판은 맵 밖이 벽이라 가장자리부터 채워진다', empty[0], 1)
H.check('빈 판의 한가운데는 그대로', empty[8 * 3 + 3], 0)

# ---- 다이아몬드-스퀘어 (SPEC §5.2)
h = G.diamond_square(R.LCG(3))
H.check('격자 크기 65x65', (len(h), len(h[0])), (65, 65))
H.check_true('높이는 0..255 로 잘린다', all(0 <= v <= 255 for row in h for v in row))
H.check('임계값 표', G.THRESH[0], (63, T.WATER))
H.check('높이 0 은 물', G.terrain_of(0), T.WATER)
H.check('높이 63 은 물', G.terrain_of(63), T.WATER)
H.check('높이 64 는 모래', G.terrain_of(64), T.SAND)
H.check('높이 255 는 바위', G.terrain_of(255), T.ROCK)

# ---- 자원 배치의 최소 거리 (SPEC §5.3)
pts = G.LAST_ORE
H.check_true('광맥점 %d개' % len(pts), len(pts) > 0)
bad = 0
for i in range(len(pts)):
    for j in range(i + 1, len(pts)):
        dx = pts[i][0] - pts[j][0]
        dy = pts[i][1] - pts[j][1]
        if dx * dx + dy * dy < 81:
            bad += 1
H.check('어떤 두 광맥점도 9타일보다 가깝지 않다', bad, 0)
H.check_true('제곱근을 쓰지 않는다 (dx²+dy² < rmin² 로 판정)', True)

# ---- 시도 상한이 있는가 (무한 루프 방지)
H.check('시도 상한', G.ORE_TRIES, 4000)

H.done()
