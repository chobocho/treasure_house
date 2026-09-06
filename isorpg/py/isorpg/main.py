# -*- coding: utf-8 -*-
"""CLI — SPEC §13.

   prim / trace / render 의 출력은 세 언어에서 바이트 단위로 같아야 한다.
   그래서 이 파일의 서식 문자열 하나하나가 명세다. 칸 맞춤에 한글을 쓰지 않는 것도
   그 때문이다 — 루아의 string.format 은 %-10s 를 바이트 수로 채운다.
"""
from __future__ import print_function

import io
import os
import sys

from . import dice as DICE
from . import fixed as F
from . import gamemap as M
from . import path as P
from . import proj as PR
from . import save as SV
from . import sortdag as SD
from .game import Game, run_script_trace
from .rng import Rng

_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN = os.path.join(_HERE, 'golden')

TILE_CASES = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (2, 0, 0), (0, 2, 0),
              (5, 3, 0), (5, 3, 1), (5, 3, 7), (47, 47, 0), (-1, -1, 0),
              (24, 24, 15)]
PIX_CASES = [(0, 8), (15, 8), (16, 8), (17, 8), (0, 0), (31, 15), (32, 16),
             (-1, 0), (-1, -1), (-16, 8), (-17, 8), (16, 0), (16, 15),
             (159, 99), (319, 199), (-320, -200), (7, 3), (8, 4), (9, 4), (0, 16)]
CAM_CASES = [(0, 0), (137, 91), (-137, -91), (768, 640), (-768, -120)]
VIS_CASES = [(0, 0), (100, 50), (-200, 300), (700, 700), (-768, -120)]
FP_CASES = [(65536, 65536), (65536, 32768), (98304, 98304), (-65536, 32768),
            (-98304, 98304), (1, 65536), (65535, 65535), (46341, 46341),
            (3277, 46341), (-1, 65536), (123456, -654321), (2147483647, 3)]
SQRT_N = [0, 1, 2, 3, 4, 8, 15, 16, 17, 1000, 65535, 65536, 1000000,
          4294967295, 8796093022207]
SQRT_X = [65536, 131072, 196608, 262144, 32768, 6553600]
TRIG_A = [0, 8, 16, 24, 32, 40, 48, 56, 64, 96, 128, 160, 192, 224, 255]
OCT_CASES = [(3, 4), (100, 0), (0, 100), (100, 100), (1000, 414), (-7, 24),
             (65, 72), (1, 1), (0, 0)]
OCTILE_CASES = [(0, 0, 0, 0), (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 3, 0),
                (0, 0, 3, 3), (0, 0, 5, 2), (10, 10, 2, 7), (0, 0, 47, 47)]
CRC_CASES = [b'', b'A', b'123456789', b'ISORPG', bytes(bytearray(range(16)))]


def prim_report():
    """골든 프리미티브 보고서. golden/prim.txt 와 한 글자도 달라선 안 된다."""
    L = []
    w = L.append

    w('== 1. 타일 -> 화면 ==')
    w('tx ty h  sx sy')
    for tx, ty, h in TILE_CASES:
        sx, sy = PR.tile_to_screen(tx, ty, h)
        w('%d %d %d  %d %d' % (tx, ty, h, sx, sy))
    w('')
    w('기저 e_x = (16, 8)   e_y = (-16, 8)   det = 256')
    w('역행렬 * 256 = [[8, 16], [-8, 16]]')
    w('')

    w('== 2. 화면 -> 타일 (대수적 역) ==')
    w('px py  tx ty')
    same = True
    for px, py in PIX_CASES:
        tx, ty = PR.screen_to_tile(px, py)
        if PR.screen_to_tile_slow(px, py) != (tx, ty):
            same = False
        w('%d %d  %d %d' % (px, py, tx, ty))
    w('')
    w('마름모 정의(|u| + 2|v| <= 16)로 직접 찾은 타일과 %s'
      % ('전부 일치' if same else '어긋남'))
    w('')

    w('== 3. 모서리 마스크 32x16 ==')
    for oy in range(16):
        w(''.join(str(PR.PICK_MASK[oy * 32 + ox]) for ox in range(32)))
    w('')
    cnt = [0, 0, 0, 0]
    for v in PR.PICK_MASK:
        cnt[v] += 1
    w('값 분포  0:%d 1:%d 2:%d 3:%d  합 %d'
      % (cnt[0], cnt[1], cnt[2], cnt[3], cnt[0] + cnt[1] + cnt[2] + cnt[3]))
    bad = 0
    for cx, cy in CAM_CASES:
        for py in range(PR.SCR_H):
            for px in range(PR.SCR_W):
                if PR.pick_mask(px + cx, py + cy) != PR.screen_to_tile(px + cx, py + cy):
                    bad += 1
    w('전수 확인  카메라 %d개 x %d픽셀 = %d  불일치 %d'
      % (len(CAM_CASES), PR.SCR_W * PR.SCR_H,
         len(CAM_CASES) * PR.SCR_W * PR.SCR_H, bad))
    w('')

    w('== 4. 가시 타일 범위 ==')
    w('camX camY  tx0 ty0 tx1 ty1')
    for cx, cy in VIS_CASES:
        r = PR.visible_range(cx, cy, cx + PR.SCR_W, cy + PR.SCR_H)
        w('%d %d  %d %d %d %d' % (cx, cy, r[0], r[1], r[2], r[3]))
    w('')

    w('== 5. 고정소수점 16.16 ==')
    w('a b  fp_mul fp_div')
    for a, b in FP_CASES:
        w('%d %d  %d %d' % (a, b, F.fp_mul(a, b), F.fp_div(a, b)))
    w('')
    w('fp_floor  %d %d %d %d %d'
      % (F.fp_floor(65536), F.fp_floor(-1), F.fp_floor(-65536),
         F.fp_floor(-65537), F.fp_floor(131071)))
    w('')

    w('== 6. 정수 제곱근 ==')
    w('n  isqrt(n)')
    for n in SQRT_N:
        w('%d  %d' % (n, F.isqrt(n)))
    w('')
    w('x  fp_sqrt(x)')
    for x in SQRT_X:
        w('%d  %d' % (x, F.fp_sqrt(x)))
    w('')

    w('== 7. CORDIC 사인/코사인 표 ==')
    w('a  COS SIN')
    for a in TRIG_A:
        w('%d  %d %d' % (a, F.COS[a], F.SIN[a]))
    w('')
    sc = 0
    ss = 0
    for a in range(256):
        sc += F.COS[a]
        ss += F.SIN[a]
    w('sum COS = %d   sum SIN = %d' % (sc, ss))
    mx = 0
    for a in range(256):
        e = F.fp_mul(F.SIN[a], F.SIN[a]) + F.fp_mul(F.COS[a], F.COS[a]) - 65536
        if e < 0:
            e = -e
        if e > mx:
            mx = e
    w('max |sin^2 + cos^2 - 1| = %d / 65536' % mx)
    w('')

    w('== 8. 팔각 거리 근사 ==')
    w('dx dy  oct exact')
    for dx, dy in OCT_CASES:
        w('%d %d  %d %d' % (dx, dy, F.oct_dist(dx, dy), F.isqrt(dx * dx + dy * dy)))
    w('')
    lo = 1000000000
    hi = -1000000000
    for a in range(256):
        dx = F.floordiv(1000 * F.COS[a], 65536)
        dy = F.floordiv(1000 * F.SIN[a], 65536)
        ex = F.isqrt(dx * dx + dy * dy)
        if ex == 0:
            continue
        e = F.floordiv((F.oct_dist(dx, dy) - ex) * 1000000, ex)
        if e < lo:
            lo = e
        if e > hi:
            hi = e
    w('반지름 1000, 256방향  상대오차 %d ~ %d ppm' % (lo, hi))
    w('')

    w('== 9. LCG (a=22695477, c=1, m=2^32) ==')
    w('i  state rand15')
    r = Rng(1)
    for i in range(8):
        v = r.next()
        w('%d  %d %d' % (i + 1, r.s, v))
    w('')
    r = Rng(12345)
    w('seed 12345 의 처음 8개 rand15: '
      + ' '.join(str(r.next()) for _ in range(8)))
    w('')

    w('== 10. 다이아몬드-스퀘어 5x5 '
      '(n=4, seed=1, scale=100, rough 58/100, corners 50/60/70/80) ==')
    for row in M.gen_height(4, [50, 60, 70, 80], 100, 1):
        w(' '.join('%4d' % v for v in row))
    w('')

    w('== 11. 옥타일 휴리스틱 (MIN_MOVE=8) ==')
    w('ax ay bx by  h')
    for ax, ay, bx, by in OCTILE_CASES:
        w('%d %d %d %d  %d' % (ax, ay, bx, by, P.octile(ax, ay, bx, by)))
    w('')

    w('== 12. 주사위 분포 ==')
    for n, m in [(1, 6), (2, 6), (3, 6), (2, 20)]:
        d = DICE.dist(n, m)
        tot = 0
        esum = 0
        for s in range(len(d)):
            tot += d[s]
            esum += s * d[s]
        w('%dd%d  경우의 수 %d = %d^%d  합계기대값*%d = %d'
          % (n, m, tot, m, n, tot, esum))
    w('')
    w('2d6 분포: ' + ' '.join(str(v) for v in DICE.dist(2, 6)[2:]))
    w('3d6 분포: ' + ' '.join(str(v) for v in DICE.dist(3, 6)[3:]))
    w('')

    w('== 13. CRC-16/CCITT-FALSE ==')
    w('표 앞 4개: %d %d %d %d' % tuple(SV.CRC_TBL[:4]))
    w('표 뒤 4개: %d %d %d %d' % tuple(SV.CRC_TBL[252:]))
    for data in CRC_CASES:
        hexs = ''.join('%02X' % b for b in bytearray(data))
        w('crc16 [%s] = 0x%04X' % (hexs, SV.crc16(data)))
    w('')

    w('== 14. 상자 정렬 사례 ==')
    w('case name  겹침쌍 상호쌍 순서 절단')
    rows = [l.split() for l in io.open(os.path.join(GOLDEN, 'sortcase.txt'),
                                       encoding='utf-8').read().strip().split('\n')]
    i = 1
    while i < len(rows):
        num, name, n = rows[i][1], rows[i][2], int(rows[i][3])
        i += 1
        items = [tuple(int(v) for v in rows[i + k]) for k in range(n)]
        i += n
        order, br = SD.topo_sort(items)
        bb = [SD.box_bbox(b) for b in items]
        ov = 0
        mu = 0
        for a in range(n):
            for b in range(a + 1, n):
                if SD.bbox_overlap(bb[a], bb[b]):
                    ov += 1
                if SD.behind(items[a], items[b]) and SD.behind(items[b], items[a]):
                    mu += 1
        w('%s %s  %d %d  %s  %d'
          % (num, name, ov, mu, ' '.join(str(v) for v in order), br))
    w('')
    return '\n'.join(L).rstrip('\n') + '\n'


def bench():
    """구간별 성능. 기계마다 다르므로 파리티 대상이 아니다."""
    import time
    out = []

    def t(name, fn, n):
        s = time.time()
        for _ in range(n):
            fn()
        d = time.time() - s
        # 칸 맞춤에 한글을 쓰지 않는다 — 루아의 %-22s 는 바이트 수로 채운다.
        out.append('%-22s %6d x  %8.1f ms  %10.1f us/call'
                   % (name, n, d * 1000, d * 1000000 / n))

    g = Game()
    m = g.map
    t('screen_to_tile x1000', lambda: [PR.screen_to_tile(x, x % 200)
                                       for x in range(1000)], 20)
    t('pick_mask x1000', lambda: [PR.pick_mask(x, x % 200)
                                  for x in range(1000)], 20)
    t('fp_mul x1000', lambda: [F.fp_mul(x * 7919, 46341) for x in range(1000)], 20)
    t('isqrt x1000', lambda: [F.isqrt(x * 104729) for x in range(1000)], 20)
    t('astar (24,34)->(24,20)', lambda: P.astar(m, 24, 34, 24, 20), 50)
    t('dijkstra 48x48', lambda: P.dijkstra(m, 24, 34), 10)
    t('fog update r=9', lambda: g.fog.update(m, 24, 25), 100)
    t('game tick', lambda: g.tick(), 200)
    t('render frame', lambda: g.render(), 20)
    t('pack_state + crc16', lambda: SV.pack_state(g), 100)
    return '\n'.join(out) + '\n'


def main(argv):
    cmd = argv[1] if len(argv) > 1 else 'prim'
    if cmd == 'prim':
        sys.stdout.write(prim_report())
        return 0
    if cmd == 'trace':
        sys.stdout.write(run_script_trace())
        return 0
    if cmd == 'render':
        path = argv[2]
        steps = int(argv[3]) if len(argv) > 3 else -1
        g = Game()
        g.run_script(limit=None if steps < 0 else steps)
        io.open(path, 'wb').write(g.render_ppm())
        return 0
    if cmd == 'bench':
        sys.stdout.write(bench())
        return 0
    sys.stderr.write('모르는 명령: %s\n' % cmd)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
