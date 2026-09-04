# -*- coding: utf-8 -*-
"""골든 프리미티브 벡터 생성기 — 엔진 구현과 '다른 방법'으로 답을 구한다.

   같은 사람이 쓴 구현끼리 맞춰 보는 것은 증명이 아니다. 그래서 이 오라클은
   일부러 다른 알고리즘을 쓴다.
     · 거리      : 공식이 아니라 이웃 그래프 BFS 로 잰다
     · 링        : 걸어서 만든 순서를 BFS 거리로 검증한다
     · 라인      : 고정소수가 아니라 부동소수 보간으로 구한다
     · 픽킹      : 마스크 테이블이 아니라 육각형 점-포함 판정으로 구한다
   LCG·FNV 는 표준 알고리즘이라 정의 그대로 계산한다.
"""
import io, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]   # SPEC §1.5

# ---- 좌표 변환 (SPEC §1.3 / §1.4) -------------------------------------------
def axial_to_oddr(q, r):  return (q + ((r - (r & 1)) >> 1), r)
def oddr_to_axial(c, w):  return (c - ((w - (w & 1)) >> 1), w)
def axial_to_oddq(q, r):  return (q, r + ((q - (q & 1)) >> 1))
def oddq_to_axial(c, w):  return (c, w - ((c - (c & 1)) >> 1))

# ---- 거리: BFS 로 잰다 (공식을 쓰지 않는다) ---------------------------------
def bfs_dist(a, b, limit=14):
    if a == b: return 0
    seen = {a}; frontier = [a]; d = 0
    while d < limit:
        d += 1; nxt = []
        for (q, r) in frontier:
            for (dq, dr) in DIRS:
                n = (q + dq, r + dr)
                if n in seen: continue
                if n == b: return d
                seen.add(n); nxt.append(n)
        frontier = nxt
    raise RuntimeError('거리 한계 초과')

# ---- 링: 정의대로 걷는다 -----------------------------------------------------
def ring(center, n):
    if n == 0: return [center]
    q, r = center[0] + DIRS[4][0] * n, center[1] + DIRS[4][1] * n
    out = []
    for d in range(6):
        for _ in range(n):
            out.append((q, r)); q += DIRS[d][0]; r += DIRS[d][1]
    return out

# ---- 라인: 부동소수 보간 + 부동소수 큐브 반올림 -----------------------------
def cube(q, r):    return (q, -q - r, r)
def cube_round_f(x, y, z):
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz: rx = -ry - rz
    elif dy > dz:           ry = -rx - rz
    else:                   rz = -rx - ry
    return (rx, ry, rz)

def line_f(a, b):
    n = bfs_dist(a, b)
    ax, ay, az = cube(*a); bx, by, bz = cube(*b)
    ax += 1 / 1024.0; ay += 1 / 1024.0; az += -2 / 1024.0   # SPEC §9.1 넛지
    out = []
    for i in range(n + 1):
        t = 0.0 if n == 0 else i / float(n)
        x = ax + (bx - ax) * t; y = ay + (by - ay) * t; z = az + (bz - az) * t
        rx, ry, rz = cube_round_f(x, y, z)
        out.append((rx, rz))
    return out

# ---- 픽킹: 육각형 점-포함 판정 (SPEC §4.2) ----------------------------------
HEX_W, HEX_H, ROW_STEP, ODD_SHIFT = 32, 32, 24, 16
def inside_hex(px, py):
    if py < 0:  return False
    if py < 8:  return 16 - 2 * py <= px < 16 + 2 * py
    if py < 24: return 0 <= px < 32
    if py < 32: return 2 * (py - 24) <= px < 32 - 2 * (py - 24)
    return False

def pick_ref(mx, my, camx, camy, w=24, h=18):
    """맵 안의 모든 헥스를 훑어 점을 품는 것을 찾는다 — 느리지만 독립적이다."""
    x, y = mx + camx, my + camy
    for row in range(h):
        for col in range(w):
            L = col * HEX_W + (row & 1) * ODD_SHIFT
            T = row * ROW_STEP
            if inside_hex(x - L, y - T): return (col, row)
    return None

# ---- 난수·해시 (표준 정의 그대로) -------------------------------------------
M32 = 0xFFFFFFFF
def lcg_seq(seed, n):
    s, out = seed & M32, []
    for _ in range(n):
        s = (s * 1664525 + 1013904223) & M32
        out.append(s)
    return out

def fnv1a(data):
    h = 2166136261
    for b in data:
        h = ((h ^ b) * 16777619) & M32
    return h

# ---- 벡터 조립 ---------------------------------------------------------------
# 출력은 JSON 이 아니라 '키 + 정수 나열' 한 줄짜리 형식이다. 루아·타입스크립트
# 테스트가 JSON 파서 없이도 읽을 수 있어야 하고, 무엇보다 눈으로 읽힌다.
def main():
    L = []

    def line(key, *nums):
        L.append(key + ' ' + ' '.join(str(int(n)) for n in nums))

    line('dirs', *[c for d in DIRS for c in d])

    samples = [(0, 0), (1, 0), (0, 1), (3, -2), (-4, 5), (-1, -1), (7, -3), (-5, -6)]
    for q, r in samples:
        line('oddr', q, r, *axial_to_oddr(q, r))
        line('oddq', q, r, *axial_to_oddq(q, r))
    assert all(oddr_to_axial(*axial_to_oddr(q, r)) == (q, r) for q, r in samples)
    assert all(oddq_to_axial(*axial_to_oddq(q, r)) == (q, r) for q, r in samples)

    pairs = [((0, 0), (0, 0)), ((0, 0), (3, 0)), ((0, 0), (0, 3)), ((0, 0), (3, -3)),
             ((0, 0), (2, -1)), ((-2, 3), (4, -2)), ((1, 1), (-3, 2)), ((5, -5), (-5, 5))]
    for a, b in pairs:
        line('dist', a[0], a[1], b[0], b[1], bfs_dist(a, b))

    for q, r in [(0, 0), (2, -1), (-3, 4)]:
        line('neighbors', q, r, *[c for (dq, dr) in DIRS for c in (q + dq, r + dr)])

    for n in (1, 2, 3):
        rg = ring((0, 0), n)
        assert len(rg) == 6 * n and len(set(rg)) == 6 * n
        assert all(bfs_dist((0, 0), h) == n for h in rg), n
        line('ring', n, *[c for h in rg for c in h])
    for n in range(5):
        line('spiral', n, 1 + 3 * n * (n + 1))

    lines = [((0, 0), (4, 0)), ((0, 0), (0, 4)), ((0, 0), (4, -2)), ((0, 0), (-3, -1)),
             ((2, 2), (-2, -1)), ((-1, 4), (5, -3))]
    for a, b in lines:
        hexes = line_f(a, b)
        line('line', a[0], a[1], b[0], b[1], len(hexes), *[c for h in hexes for c in h])

    pts = [(0, 0), (16, 0), (31, 7), (16, 16), (0, 23), (40, 5), (48, 30),
           (100, 60), (255, 167), (17, 3), (15, 3), (200, 100)]
    for (mx, my) in pts:
        for (cx, cy) in ((0, 0), (32, 24)):
            h = pick_ref(mx, my, cx, cy)
            line('pick', mx, my, cx, cy, h[0] if h else -1, h[1] if h else -1)

    line('lcg', 0x1BADB002, *lcg_seq(0x1BADB002, 8))
    line('d6', *[((s >> 16) % 6) + 1 for s in lcg_seq(0x1BADB002, 8)])

    for s in ('', 'a', 'hexwar', '0,0,0,0,0,10,6,6,0\n'):
        raw = s.encode('utf-8')
        L.append('fnv %s %d' % (raw.hex() if raw else '-', fnv1a(raw)))

    for (t, e, rd) in ((0, 0, 0), (1, 2, 0), (7, 7, 1), (4, 3, 1), (15, 5, 0)):
        line('cell', t, e, rd, (rd << 7) | (e << 4) | t)

    out = os.path.join(BASE, 'golden', 'prim.txt')
    io.open(out, 'w', encoding='utf-8').write(
        ';; 골든 프리미티브 — tools/gen_prim.py 가 만든다 (오라클은 구현과 다른 알고리즘)\n'
        + '\n'.join(L) + '\n')
    print('wrote %s (%d줄)' % (out, len(L)))

    mask = []
    for oy in range(24):
        mask.append(''.join('1' if (oy < 8 and ox < 16 - 2 * oy) else
                            '2' if (oy < 8 and ox >= 16 + 2 * oy) else '0'
                            for ox in range(32)))
    io.open(os.path.join(BASE, 'golden', 'pick_mask.txt'), 'w',
            encoding='utf-8').write('\n'.join(mask) + '\n')
    print('wrote golden/pick_mask.txt')


if __name__ == '__main__':
    main()
