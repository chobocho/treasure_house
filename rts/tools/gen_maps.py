# -*- coding: utf-8 -*-
"""경로 탐색 시험용 고정 맵 6장을 만든다 — golden/map_1..6.txt

   맵은 손으로 그리지 않는다. 그리면 세 언어 이식 중에 누군가 한 칸을 고치고,
   그 사실을 아무도 모른 채 골든이 조용히 갈린다. 여기서 규칙으로 찍어 낸다.

   형식(사람이 읽을 수 있게 일부러 단순하게 둔다):

       RTSMAP 1
       name 빈 들판
       size 32 32
       map
       ................................      '.' 통행 가능, '#' 막힘
       ...
       pairs 4
       1 1 30 30                              시험할 (출발 x y, 도착 x y)

   실행:  python3 tools/gen_maps.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')
W = H = 32

# SPEC §3.1 과 같은 LCG. 도구는 엔진을 import 하지 않는다 — 독립 참조여야 한다.
class LCG(object):
    def __init__(self, seed):
        self.s = seed

    def next15(self):
        self.s = (22695477 * self.s + 1) % 4294967296
        return (self.s // 65536) % 32768

    def roll(self, n):
        if n <= 1:
            return 0
        limit = 32768 - 32768 % n
        while True:
            r = self.next15()
            if r < limit:
                return r % n


def blank():
    return [['.'] * W for _ in range(H)]


def border(g):
    """가장자리 한 줄은 항상 막는다 — 경계 검사 버그가 경로 결과로 드러나게."""
    for x in range(W):
        g[0][x] = g[H - 1][x] = '#'
    for y in range(H):
        g[y][0] = g[y][W - 1] = '#'
    return g


def m1_open():
    return border(blank())


def m2_wall():
    """세로벽 하나에 문 하나. A* 가 문을 찾아 돌아가는지 본다."""
    g = border(blank())
    for y in range(1, H - 1):
        g[y][16] = '#'
    g[20][16] = '.'
    return g


def m3_comb():
    """빗살 미로 — 경로가 맵을 여러 번 왕복하게 만든다. 최악에 가까운 경우."""
    g = border(blank())
    for i, x in enumerate(range(4, W - 4, 4)):
        for y in range(1, H - 1):
            g[y][x] = '#'
        gap = 1 if i % 2 == 0 else H - 2
        g[gap][x] = '.'
    return g


def m4_rooms():
    """4×4 방 격자와 문. HPA* 의 클러스터 경계와 일부러 어긋나게 놓았다."""
    g = border(blank())
    for x in range(1, W - 1):
        for y in (10, 21):
            g[y][x] = '#'
    for y in range(1, H - 1):
        for x in (10, 21):
            g[y][x] = '#'
    for a in (10, 21):
        g[a][5] = g[a][16] = g[a][27] = '.'
        g[5][a] = g[16][a] = g[27][a] = '.'
    return g


def m5_island():
    """오른쪽 아래에 닿을 수 없는 섬. '가장 가까운 도달점' 규칙(SPEC §8.6)용."""
    g = border(blank())
    for y in range(22, 30):
        for x in range(22, 30):
            g[y][x] = '.' if 23 <= y <= 28 and 23 <= x <= 28 else '#'
    return g


def m6_cave():
    """SPEC §5.1 의 셀룰러 오토마타를 그대로 돌린 동굴. 시드 7."""
    rng = LCG(7)
    cur = [[1 if rng.roll(100) < 45 else 0 for _ in range(W)] for _ in range(H)]
    for _ in range(4):
        nxt = [[0] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                w = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        u, v = x + dx, y + dy
                        w += 1 if not (0 <= u < W and 0 <= v < H) else cur[v][u]
                if cur[y][x] == 1:
                    nxt[y][x] = 1 if w >= 4 else 0
                else:
                    nxt[y][x] = 1 if w >= 5 else 0
        cur = nxt
    g = [['#' if cur[y][x] else '.' for x in range(W)] for y in range(H)]
    g = border(g)
    # 가장 큰 통행 성분만 남긴다 — 나머지는 메운다(SPEC §5.1 3단계).
    seen = [[False] * W for _ in range(H)]
    best = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == '#' or seen[y][x]:
                continue
            comp, stack = [], [(x, y)]
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        u, v = cx + dx, cy + dy
                        if (0 <= u < W and 0 <= v < H and not seen[v][u]
                                and g[v][u] == '.'):
                            seen[v][u] = True
                            stack.append((u, v))
            if len(comp) > len(best):
                best = comp
    keep = set(best)
    for y in range(H):
        for x in range(W):
            if g[y][x] == '.' and (x, y) not in keep:
                g[y][x] = '#'
    return g


def pick_pairs(g, n, seed):
    """통행 가능한 칸에서 시험 쌍을 뽑는다. 규칙으로 뽑아야 재현된다."""
    free = [(x, y) for y in range(H) for x in range(W) if g[y][x] == '.']
    rng = LCG(seed)
    out = []
    while len(out) < n:
        a = free[rng.roll(len(free))]
        b = free[rng.roll(len(free))]
        if a != b and (a, b) not in out:
            out.append((a, b))
    return out


# ── 시작 맵 (64×64) — SPEC §5.2~§5.4 ─────────────────────────────────────────
MW = MH = 64
SAND, ROCK, WATER, DIRT, ORE, HILL, RUBBLE, ROAD = range(8)
CH = '.#~,*^;='
# 높이 → 지형 (SPEC §5.2)
THRESH = [(63, WATER), (95, SAND), (175, DIRT), (207, HILL), (255, ROCK)]
START = [(8, 8), (55, 55)]


def clamp(v):
    return 0 if v < 0 else (255 if v > 255 else v)


def diamond_square(rng):
    """65×65 에서 돌리고 왼쪽 위 64×64 를 쓴다 (SPEC §5.2)."""
    n = 65
    h = [[0] * n for _ in range(n)]
    for (x, y) in ((0, 0), (0, 64), (64, 0), (64, 64)):
        h[y][x] = rng.roll(256)
    step = 64
    while step > 1:
        half = step // 2
        amp = step * 255 // 128
        for y in range(0, n - 1, step):
            for x in range(0, n - 1, step):
                a = (h[y][x] + h[y][x + step] + h[y + step][x] + h[y + step][x + step]) // 4
                h[y + half][x + half] = clamp(a + rng.roll(2 * amp + 1) - amp)
        row = 0
        for y in range(0, n, half):
            start = half if row % 2 == 0 else 0
            for x in range(start, n, step):
                t, c = 0, 0
                for dx, dy in ((-half, 0), (half, 0), (0, -half), (0, half)):
                    u, v = x + dx, y + dy
                    if 0 <= u < n and 0 <= v < n:
                        t += h[v][u]
                        c += 1
                h[y][x] = clamp(t // c + rng.roll(2 * amp + 1) - amp)
            row += 1
        step = half
    return h


def terrain_from(h):
    g = [[SAND] * MW for _ in range(MH)]
    for y in range(MH):
        for x in range(MW):
            v = h[y][x]
            for lim, t in THRESH:
                if v <= lim:
                    g[y][x] = t
                    break
    return g


def symmetrize(g):
    """180도 회전 대칭 — 앞쪽 절반이 원본이다 (SPEC §5.4)."""
    for y in range(MH):
        for x in range(MW):
            if y * MW + x < MW * MH // 2:
                g[MH - 1 - y][MW - 1 - x] = g[y][x]
    return g


def place_ore(g, rng, n=12, rmin=9):
    """정수 포아송 디스크 (SPEC §5.3). 앞쪽 절반에만 놓고 대칭 복사한다."""
    pts, tries = [], 0
    while len(pts) < n and tries < 4000:
        tries += 1
        x, y = rng.roll(MW), rng.roll(MH // 2)
        if g[y][x] not in (DIRT, SAND):
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < rmin * rmin for px, py in pts):
            continue
        pts.append((x, y))
    span = [0, 1, 1, 2, 2]                    # 반경 2 원 마스크의 행별 최대 |i|
    for (px, py) in pts:
        for dy in range(-2, 3):
            for dx in range(-span[abs(dy)] * 0 - 2, 3):
                if dx * dx + dy * dy > 4:
                    continue
                u, v = px + dx, py + dy
                if 0 <= u < MW and 0 <= v < MH and g[v][u] in (DIRT, SAND):
                    g[v][u] = ORE
                    g[MH - 1 - v][MW - 1 - u] = ORE
    return pts, tries


def clear_base(g):
    """시작 지점 5×5 를 평지로 — 사령부 3×3 이 반드시 들어가야 한다."""
    for (bx, by) in START:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                u, v = bx + dx, by + dy
                if 0 <= u < MW and 0 <= v < MH:
                    g[v][u] = DIRT


def passable(t):
    return t not in (ROCK, WATER)


def connected(g, a, b):
    seen = [[False] * MW for _ in range(MH)]
    st = [a]
    seen[a[1]][a[0]] = True
    while st:
        x, y = st.pop()
        if (x, y) == b:
            return True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                u, v = x + dx, y + dy
                if (0 <= u < MW and 0 <= v < MH and not seen[v][u]
                        and passable(g[v][u])):
                    seen[v][u] = True
                    st.append((u, v))
    return False


def gen_start():
    """시드를 1씩 올리며 두 시작점이 이어질 때까지 다시 만든다 (SPEC §5.4)."""
    seed, retries = 3, 0
    while True:
        rng = LCG(seed)
        g = symmetrize(terrain_from(diamond_square(rng)))
        pts, tries = place_ore(g, rng)
        clear_base(g)
        if connected(g, START[0], START[1]):
            return g, seed, retries, pts, tries
        seed += 1
        retries += 1


def write_start():
    g, seed, retries, pts, tries = gen_start()
    lines = ['RTSMAP 1', 'name 시작 맵', 'size %d %d' % (MW, MH), 'terrain']
    lines += [''.join(CH[t] for t in row) for row in g]
    lines.append('start %d' % len(START))
    for (x, y) in START:
        lines.append('%d %d' % (x, y))
    lines.append('seed %d' % seed)
    lines.append('retries %d' % retries)
    lines.append('ore %d %d' % (len(pts), tries))
    io.open(os.path.join(GOLDEN, 'map_start.txt'), 'w',
            encoding='utf-8').write('\n'.join(lines) + '\n')
    hist = [0] * 8
    for row in g:
        for t in row:
            hist[t] += 1
    print('map_start.txt  시드 %d · 재시도 %d · 광맥점 %d(시도 %d)'
          % (seed, retries, len(pts), tries))
    print('  지형 도수: ' + ' '.join('%s=%d' % (CH[i], hist[i]) for i in range(8)))


MAPS = [
    (1, '빈 들판', m1_open, 4, 101),
    (2, '벽과 문', m2_wall, 4, 102),
    (3, '빗살 미로', m3_comb, 4, 103),
    (4, '방과 문', m4_rooms, 4, 104),
    (5, '닿을 수 없는 섬', m5_island, 4, 105),
    (6, '동굴', m6_cave, 4, 106),
]


def main():
    if not os.path.isdir(GOLDEN):
        os.makedirs(GOLDEN)
    for num, name, fn, npair, seed in MAPS:
        g = fn()
        rows = [''.join(r) for r in g]
        pairs = pick_pairs(g, npair, seed)
        # 5번 맵만은 '닿을 수 없는 쌍'을 반드시 하나 넣는다.
        if num == 5:
            pairs[0] = ((1, 1), (25, 25))
        lines = ['RTSMAP 1', 'name %s' % name, 'size %d %d' % (W, H), 'map']
        lines += rows
        lines.append('pairs %d' % len(pairs))
        for (ax, ay), (bx, by) in pairs:
            lines.append('%d %d %d %d' % (ax, ay, bx, by))
        p = os.path.join(GOLDEN, 'map_%d.txt' % num)
        io.open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        blocked = sum(r.count('#') for r in rows)
        print('map_%d.txt  %-16s 막힌 칸 %4d / %d' % (num, name, blocked, W * H))
    write_start()


if __name__ == '__main__':
    main()
