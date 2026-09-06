# -*- coding: utf-8 -*-
"""골든 프리미티브 생성 — golden/prim.txt, golden/pick_mask.txt, golden/sortcase.txt.

   여기서 만든 텍스트를 세 언어의 `main prim` 이 **바이트 단위로** 다시 만들어야 한다.
   계산은 tools/ref_iso.py(독립 참조)로 하고, 엔진은 import 하지 않는다.

   실행:  python3 tools/gen_prim.py
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'tools'))
import ref_iso as R                                            # noqa: E402

GOLDEN = os.path.join(BASE, 'golden')
L = []


def w(s=''):
    L.append(s)


def sec(n, title):
    w('== %d. %s ==' % (n, title))


# ------------------------------------------------------------------ 1. 투영
sec(1, '타일 -> 화면')
w('tx ty h  sx sy')
CASES = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (2, 0, 0), (0, 2, 0),
         (5, 3, 0), (5, 3, 1), (5, 3, 7), (47, 47, 0), (-1, -1, 0), (24, 24, 15)]
for tx, ty, h in CASES:
    sx, sy = R.tile_to_screen(tx, ty, h)
    w('%d %d %d  %d %d' % (tx, ty, h, sx, sy))
w()
w('기저 e_x = (16, 8)   e_y = (-16, 8)   det = 256')
w('역행렬 * 256 = [[8, 16], [-8, 16]]')
w()

# ------------------------------------------------------------------ 2. 역투영
sec(2, '화면 -> 타일 (대수적 역)')
w('px py  tx ty')
PIX = [(0, 8), (15, 8), (16, 8), (17, 8), (0, 0), (31, 15), (32, 16),
       (-1, 0), (-1, -1), (-16, 8), (-17, 8), (16, 0), (16, 15),
       (159, 99), (319, 199), (-320, -200), (7, 3), (8, 4), (9, 4), (0, 16)]
for px, py in PIX:
    tx, ty = R.screen_to_tile(px, py)
    g = R.screen_to_tile_geometric(px, py)
    assert (tx, ty) == g, (px, py, (tx, ty), g)
    w('%d %d  %d %d' % (px, py, tx, ty))
w()
w('마름모 정의(|u| + 2|v| <= 16)로 직접 찾은 타일과 전부 일치')
w()

# ------------------------------------------------------------------ 3. 모서리 마스크
sec(3, '모서리 마스크 32x16')
for oy in range(16):
    w(''.join(str(R.PICK_MASK[oy * 32 + ox]) for ox in range(32)))
w()
cnt = [R.PICK_MASK.count(v) for v in range(4)]
w('값 분포  0:%d 1:%d 2:%d 3:%d  합 %d' % (cnt[0], cnt[1], cnt[2], cnt[3], sum(cnt)))
CAMS = [(0, 0), (137, 91), (-137, -91), (768, 640), (-768, -120)]
bad = 0
for cx, cy in CAMS:
    for py in range(0, R.SCR_H):
        for px in range(0, R.SCR_W):
            if R.pick_mask(px + cx, py + cy) != R.screen_to_tile(px + cx, py + cy):
                bad += 1
w('전수 확인  카메라 %d개 x %d픽셀 = %d  불일치 %d'
  % (len(CAMS), R.SCR_W * R.SCR_H, len(CAMS) * R.SCR_W * R.SCR_H, bad))
w()

# ------------------------------------------------------------------ 4. 가시 범위
sec(4, '가시 타일 범위')
w('camX camY  tx0 ty0 tx1 ty1')
for cx, cy in [(0, 0), (100, 50), (-200, 300), (700, 700), (-768, -120)]:
    r = R.visible_range(cx, cy, cx + R.SCR_W, cy + R.SCR_H)
    w('%d %d  %d %d %d %d' % (cx, cy, r[0], r[1], r[2], r[3]))
w()

# ------------------------------------------------------------------ 5. 고정소수점
sec(5, '고정소수점 16.16')
w('a b  fp_mul fp_div')
FPC = [(65536, 65536), (65536, 32768), (98304, 98304), (-65536, 32768),
       (-98304, 98304), (1, 65536), (65535, 65535), (46341, 46341),
       (3277, 46341), (-1, 65536), (123456, -654321), (2147483647, 3)]
for a, b in FPC:
    w('%d %d  %d %d' % (a, b, R.fp_mul(a, b), R.fp_div(a, b)))
w()
w('fp_floor  %d %d %d %d %d' % (65536 // 65536, (-1) // 65536, (-65536) // 65536,
                                (-65537) // 65536, 131071 // 65536))
w()

# ------------------------------------------------------------------ 6. 제곱근
sec(6, '정수 제곱근')
w('n  isqrt(n)')
for n in [0, 1, 2, 3, 4, 8, 15, 16, 17, 1000, 65535, 65536, 1000000, 4294967295,
          8796093022207]:
    w('%d  %d' % (n, R.isqrt(n)))
w()
w('x  fp_sqrt(x)')
for x in [65536, 131072, 196608, 262144, 32768, 6553600]:
    w('%d  %d' % (x, R.fp_sqrt(x)))
w()

# ------------------------------------------------------------------ 7. CORDIC
sec(7, 'CORDIC 사인/코사인 표')
w('a  COS SIN')
for a in [0, 8, 16, 24, 32, 40, 48, 56, 64, 96, 128, 160, 192, 224, 255]:
    w('%d  %d %d' % (a, R.COS[a], R.SIN[a]))
w()
w('sum COS = %d   sum SIN = %d' % (sum(R.COS), sum(R.SIN)))
mx = 0
for a in range(256):
    e = abs(R.fp_mul(R.SIN[a], R.SIN[a]) + R.fp_mul(R.COS[a], R.COS[a]) - 65536)
    mx = max(mx, e)
w('max |sin^2 + cos^2 - 1| = %d / 65536' % mx)
w()

# ------------------------------------------------------------------ 8. 팔각 거리
sec(8, '팔각 거리 근사')
w('dx dy  oct exact')
for dx, dy in [(3, 4), (100, 0), (0, 100), (100, 100), (1000, 414), (-7, 24),
               (65, 72), (1, 1), (0, 0)]:
    w('%d %d  %d %d' % (dx, dy, R.oct_dist(dx, dy), R.isqrt(dx * dx + dy * dy)))
w()
lo, hi = 10 ** 9, -10 ** 9
for a in range(256):
    dx = 1000 * R.COS[a] // 65536
    dy = 1000 * R.SIN[a] // 65536
    ex = R.isqrt(dx * dx + dy * dy)
    if ex == 0:
        continue
    e = (R.oct_dist(dx, dy) - ex) * 1000000 // ex
    lo, hi = min(lo, e), max(hi, e)
w('반지름 1000, 256방향  상대오차 %d ~ %d ppm' % (lo, hi))
w()

# ------------------------------------------------------------------ 9. LCG
sec(9, 'LCG (a=22695477, c=1, m=2^32)')
w('i  state rand15')
r = R.Rng(1)
for i in range(8):
    v = r.next()
    w('%d  %d %d' % (i + 1, r.s, v))
w()
r = R.Rng(12345)
w('seed 12345 의 처음 8개 rand15: ' + ' '.join(str(r.next()) for _ in range(8)))
w()

# ------------------------------------------------------------------ 10. 다이아몬드-스퀘어
sec(10, '다이아몬드-스퀘어 5x5 (n=4, seed=1, scale=100, corners 50/60/70/80)')
for row in R.gen_height(4, [50, 60, 70, 80], 100, 1):
    w(' '.join('%4d' % v for v in row))
w()

# ------------------------------------------------------------------ 11. 옥타일
sec(11, '옥타일 휴리스틱 (MIN_MOVE=8)')
w('ax ay bx by  h')
for ax, ay, bx, by in [(0, 0, 0, 0), (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 3, 0),
                       (0, 0, 3, 3), (0, 0, 5, 2), (10, 10, 2, 7), (0, 0, 47, 47)]:
    w('%d %d %d %d  %d' % (ax, ay, bx, by, R.octile(ax, ay, bx, by)))
w()

# ------------------------------------------------------------------ 12. 주사위
sec(12, '주사위 분포')
for n, m in [(1, 6), (2, 6), (3, 6), (2, 20)]:
    d = R.dice_dist(n, m)
    tot = sum(d)
    esum = sum(s * c for s, c in enumerate(d))
    w('%dd%d  경우의 수 %d = %d^%d  합계기대값*%d = %d' % (n, m, tot, m, n, tot, esum))
w()
w('2d6 분포: ' + ' '.join(str(v) for v in R.dice_dist(2, 6)[2:]))
w('3d6 분포: ' + ' '.join(str(v) for v in R.dice_dist(3, 6)[3:]))
w()

# ------------------------------------------------------------------ 13. CRC-16
sec(13, 'CRC-16/CCITT-FALSE')
w('표 앞 4개: %d %d %d %d' % tuple(R.CRC_TBL[:4]))
w('표 뒤 4개: %d %d %d %d' % tuple(R.CRC_TBL[-4:]))
# 라벨에 한글을 쓰지 않는다 — 루아의 string.format 은 %-10s 를 바이트 수로 채운다.
# 한글이 섞이면 세 언어의 칸 맞춤이 어긋나 파리티가 깨진다.
for data in [b'', b'A', b'123456789', b'ISORPG', bytes(range(16))]:
    hexs = ''.join('%02X' % b for b in data)
    w('crc16 [%s] = 0x%04X' % (hexs, R.crc16(data)))
w()

text = '\n'.join(L).rstrip('\n') + '\n'
io.open(os.path.join(GOLDEN, 'prim.txt'), 'w', encoding='utf-8').write(text)

mask = '\n'.join(''.join(str(R.PICK_MASK[oy * 32 + ox]) for ox in range(32))
                 for oy in range(16)) + '\n'
io.open(os.path.join(GOLDEN, 'pick_mask.txt'), 'w', encoding='utf-8').write(mask)

print('golden/prim.txt  %d줄' % len(text.split('\n')))
print('golden/pick_mask.txt  16줄')

# ------------------------------------------------------------------ 14. 상자 정렬
L2 = []
rows = [l.split() for l in
        io.open(os.path.join(GOLDEN, 'sortcase.txt'), encoding='utf-8').read()
        .strip().split('\n')]
i = 1
L2.append('== 14. 상자 정렬 사례 ==')
L2.append('case name  겹침쌍 상호쌍 순서 절단')
while i < len(rows):
    _, num, name, n = rows[i]
    n = int(n)
    i += 1
    items = [tuple(int(v) for v in rows[i + k]) for k in range(n)]
    i += n
    order, br = R.topo_sort(items)
    bb = [R.box_bbox(b) for b in items]
    ov = sum(1 for a in range(n) for b in range(a + 1, n)
             if R.bbox_overlap(bb[a], bb[b]))
    mu = sum(1 for a in range(n) for b in range(a + 1, n)
             if R.behind(items[a], items[b]) and R.behind(items[b], items[a]))
    L2.append('%s %s  %d %d  %s  %d'
              % (num, name, ov, mu, ' '.join(str(v) for v in order), br))
L2.append('')

text = io.open(os.path.join(GOLDEN, 'prim.txt'), encoding='utf-8').read()
text = text.rstrip('\n') + '\n\n' + '\n'.join(L2).rstrip('\n') + '\n'
io.open(os.path.join(GOLDEN, 'prim.txt'), 'w', encoding='utf-8').write(text)
print('14절 추가 — golden/prim.txt  %d줄' % len(text.split('\n')))
