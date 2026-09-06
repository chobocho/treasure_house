# -*- coding: utf-8 -*-
"""맵 생성 — 셀룰러 오토마타·다이아몬드 스퀘어·포아송 자원·대칭 (SPEC §5).

   생성기는 게임이 시작하기 전에 한 번만 돈다. 그래서 시뮬레이션 RNG 와
   **다른 인스턴스**를 쓴다(SPEC §3.3). 여기서 뽑은 난수가 시뮬 수열에
   끼어들면 두 기계가 같은 맵을 놓고도 다른 게임을 하게 된다.
"""

from . import rng as R
from . import tmap as T

MW = MH = 64
START = [(8, 8), (55, 55)]
ORE_TRIES = 4000
ORE_COUNT = 12
ORE_RMIN = 9

# 높이 → 지형 (SPEC §5.2). 위에서부터 처음 걸리는 것.
THRESH = [(63, T.WATER), (95, T.SAND), (175, T.DIRT), (207, T.HILL), (255, T.ROCK)]

LAST_ORE = []                    # 마지막 생성의 광맥 중심점 — 시험·덱용


def terrain_of(v):
    for lim, t in THRESH:
        if v <= lim:
            return t
    return T.ROCK


def _clamp(v):
    return 0 if v < 0 else (255 if v > 255 else v)


# ── SPEC §5.1 셀룰러 오토마타 ───────────────────────────────────────────────
def cellular_step(cur, w, h):
    """B5678/S45678 한 세대. 맵 밖은 벽으로 센다.

       살아 있는 벽은 이웃 벽이 4 이상이면 남고, 빈 칸은 5 이상이면 벽이 된다.
       2세대면 덩어리가 덜 뭉치고 6세대면 좁은 통로가 전부 막힌다 —
       4세대가 통로와 개활지가 함께 남는 자리다.
    """
    nxt = [0] * (w * h)
    for y in range(h):
        for x in range(w):
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    u, v = x + dx, y + dy
                    n += 1 if not (0 <= u < w and 0 <= v < h) else cur[v * w + u]
            if cur[y * w + x] == 1:
                nxt[y * w + x] = 1 if n >= 4 else 0
            else:
                nxt[y * w + x] = 1 if n >= 5 else 0
    return nxt


def cellular(w, h, rand, gens=4, fill=45):
    cur = [1 if rand.roll(100) < fill else 0 for _ in range(w * h)]
    for _ in range(gens):
        cur = cellular_step(cur, w, h)
    return cur


# ── SPEC §5.2 다이아몬드-스퀘어 ─────────────────────────────────────────────
def diamond_square(rand):
    """(2^6)+1 = 65 칸 격자. 평균은 반올림이 아니라 내림이다 — 명세다."""
    n = 65
    h = [[0] * n for _ in range(n)]
    for (x, y) in ((0, 0), (0, 64), (64, 0), (64, 64)):
        h[y][x] = rand.roll(256)
    step = 64
    while step > 1:
        half = step // 2
        amp = step * 255 // 128
        for y in range(0, n - 1, step):
            for x in range(0, n - 1, step):
                a = (h[y][x] + h[y][x + step]
                     + h[y + step][x] + h[y + step][x + step]) // 4
                h[y + half][x + half] = _clamp(a + rand.roll(2 * amp + 1) - amp)
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
                h[y][x] = _clamp(t // c + rand.roll(2 * amp + 1) - amp)
            row += 1
        step = half
    return h


# ── SPEC §5.3 정수 포아송 디스크 ────────────────────────────────────────────
def place_ore(m, rand, n=ORE_COUNT, rmin=ORE_RMIN):
    """앞쪽 절반에만 놓고 대칭 복사한다. 시도 상한이 반드시 있어야 한다 —
       상한 없는 재시도는 디싱크보다 나쁘다(맵 생성이 영원히 끝나지 않는다)."""
    pts, tries = [], 0
    while len(pts) < n and tries < ORE_TRIES:
        tries += 1
        x, y = rand.roll(MW), rand.roll(MH // 2)
        if m.terrain[y * MW + x] not in (T.DIRT, T.SAND):
            continue
        ok = True
        for (px, py) in pts:
            if (x - px) * (x - px) + (y - py) * (y - py) < rmin * rmin:
                ok = False
                break
        if ok:
            pts.append((x, y))
    for (px, py) in pts:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy > 4:
                    continue
                u, v = px + dx, py + dy
                if 0 <= u < MW and 0 <= v < MH and m.terrain[v * MW + u] in (T.DIRT, T.SAND):
                    m.terrain[v * MW + u] = T.ORE
                    m.terrain[(MH - 1 - v) * MW + (MW - 1 - u)] = T.ORE
    return pts, tries


# ── SPEC §5.4 대칭과 시작 지점 ──────────────────────────────────────────────
def symmetrize(m):
    """180도 회전 대칭. 앞쪽 절반이 원본이다."""
    for y in range(MH):
        for x in range(MW):
            if y * MW + x < MW * MH // 2:
                m.terrain[(MH - 1 - y) * MW + (MW - 1 - x)] = m.terrain[y * MW + x]


def clear_base(m):
    """시작 지점 5×5 를 흙으로 — 사령부 3×3 이 반드시 들어가야 한다."""
    for (bx, by) in START:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                u, v = bx + dx, by + dy
                if 0 <= u < MW and 0 <= v < MH:
                    m.terrain[v * MW + u] = T.DIRT


def gen_start(seed=3):
    """시드를 1씩 올리며 두 시작점이 이어질 때까지 다시 만든다.

       재시도가 필요하다는 것 자체가 명세의 일부다 — 다이아몬드-스퀘어는
       가끔 두 기지 사이를 물로 끊어 놓는다.
    """
    global LAST_ORE
    retries = 0
    while True:
        rand = R.LCG(seed)
        m = T.TMap(MW, MH)
        h = diamond_square(rand)
        for y in range(MH):
            for x in range(MW):
                m.terrain[y * MW + x] = terrain_of(h[y][x])
        symmetrize(m)
        pts, _tries = place_ore(m, rand)
        clear_base(m)
        for i in range(MW * MH):
            m._repass(i)
        m._bump()
        m.starts = list(START)
        lab = m.labels(0)
        if lab[m.idx(*START[0])] == lab[m.idx(*START[1])] >= 0:
            LAST_ORE = pts
            return m, seed, retries
        seed += 1
        retries += 1
