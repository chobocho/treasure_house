# -*- coding: utf-8 -*-
"""투영과 역투영 — 마스크 방식과 대수적 역이 화면 전체에서 같은가."""
from __future__ import print_function

import harness as H
from isorpg import proj as P

H.title('proj')

# ---- 기저와 행렬식
H.check('e_x', P.tile_to_screen(1, 0, 0), (16, 8))
H.check('e_y', P.tile_to_screen(0, 1, 0), (-16, 8))
H.check('det', 16 * 8 - (-16) * 8, 256)
H.check('높이 1단계', P.tile_to_screen(5, 3, 1), (32, 56))

# ---- 타일 -> 화면 -> 타일 왕복 (중심 픽셀)
bad = 0
for tx in range(-8, 56):
    for ty in range(-8, 56):
        sx, sy = P.tile_to_screen(tx, ty, 0)
        if P.screen_to_tile(sx, sy + 8) != (tx, ty):
            bad += 1
H.check('타일 중심 왕복 64x64', bad, 0)

# ---- 마름모 정의로 직접 찾은 것과 같은가
bad = 0
for px in range(-64, 65):
    for py in range(-40, 41):
        if P.screen_to_tile(px, py) != P.screen_to_tile_slow(px, py):
            bad += 1
H.check('대수적 역 == 마름모 전수 탐색 (129x81)', bad, 0)

# ---- 마스크가 골든과 같은가
want = H.golden('pick_mask.txt').rstrip('\n').split('\n')
got = [''.join(str(P.PICK_MASK[oy * 32 + ox]) for ox in range(32)) for oy in range(16)]
H.check('pick_mask.txt', got, want)
H.check('마스크 값은 0..3 뿐', sorted(set(P.PICK_MASK)), [0, 1, 2, 3])

# ---- 전수 확인: 화면 64,000픽셀 x 카메라 5개
CAMS = [(0, 0), (137, 91), (-137, -91), (768, 640), (-768, -120)]
bad = 0
for cx, cy in CAMS:
    for py in range(P.SCR_H):
        base = py + cy
        for px in range(P.SCR_W):
            if P.pick_mask(px + cx, base) != P.screen_to_tile(px + cx, base):
                bad += 1
H.check('마스크 == 대수적 역 (카메라 %d개 x 64,000픽셀)' % len(CAMS), bad, 0)

# ---- 마름모가 평면을 빈틈없이 덮는가: 각 타일이 정확히 256픽셀
from collections import Counter                                # noqa: E402
cnt = Counter()
for py in range(0, 160):
    for px in range(-160, 160):
        cnt[P.screen_to_tile(px, py)] += 1
inner = [v for k, v in cnt.items()
         if -3 <= k[0] <= 12 and -3 <= k[1] <= 12]
H.check('안쪽 타일은 모두 256픽셀', sorted(set(inner)), [256])

# ---- 가시 범위: 무식하게 센 것과 같은가
bad = 0
for cx, cy in [(0, 0), (100, 50), (-200, 300), (-700, 100)]:
    tx0, ty0, tx1, ty1 = P.visible_range(cx, cy, cx + P.SCR_W, cy + P.SCR_H)
    seen = set()
    for py in range(cy, cy + P.SCR_H):
        for px in range(cx, cx + P.SCR_W):
            seen.add(P.screen_to_tile(px, py))
    for tx, ty in seen:
        if 0 <= tx < 48 and 0 <= ty < 48:
            if not (tx0 <= tx <= tx1 and ty0 <= ty <= ty1):
                bad += 1
H.check('가시 범위가 화면에 나오는 타일을 모두 담는가', bad, 0)

H.done()
