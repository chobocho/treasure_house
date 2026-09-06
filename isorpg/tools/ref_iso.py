# -*- coding: utf-8 -*-
"""엔진과 **독립된** 참조 구현 — 골든 벡터를 만드는 쪽.

   엔진(py/isorpg)은 세 언어 이식을 염두에 두고 분할 곱셈·정수 나눗셈 같은
   우회로를 쓴다. 여기서는 파이썬의 임의 정밀도 정수와 math 모듈을 그대로 써서
   같은 명세를 **다른 방식으로** 계산한다. 두 결과가 같아야 엔진의 우회로가 옳다.

   그래서 이 파일은 엔진을 import 하지 않는다. 절대로.
"""
import math

# ---------------------------------------------------------------- 상수 (SPEC §0)
TW, TH, TZ = 32, 16, 8
SCR_W, SCR_H = 320, 200
MAP_W, MAP_H = 48, 48
MAXH = 15
FP_ONE = 65536
LCG_A, LCG_C, LCG_M = 22695477, 1, 1 << 32
OCT_A, OCT_B = 983, 407
N_ITER, GUARD = 20, 8
K_INV = 10188014
ATAN_BRAD = [round(math.atan(2.0 ** -i) / (2 * math.pi) * 256 * 65536)
             for i in range(N_ITER)]


# ---------------------------------------------------------------- 고정소수점
def fp_mul(a, b):
    """분할 없이 그냥 곱한다 — 파이썬 정수는 자릿수 제한이 없다.

       엔진은 2^53 을 넘기지 않으려고 a 를 상·하위로 쪼개 두 번 곱한다.
       여기서는 그럴 이유가 없으니 곧이곧대로 곱하고 내림한다. 둘이 같아야 한다.
    """
    return (a * b) // 65536


def fp_div(a, b):
    return (a * 65536) // b


def isqrt(n):
    return math.isqrt(n)


def fp_sqrt(x):
    return math.isqrt(x * 65536)


def oct_dist(dx, dy):
    ax, ay = abs(dx), abs(dy)
    hi, lo = max(ax, ay), min(ax, ay)
    return (OCT_A * hi + OCT_B * lo) // 1024


def cordic(theta):
    t = theta % (256 * 65536)
    quad = t // (64 * 65536)
    t -= quad * 64 * 65536
    x, y, z = K_INV, 0, t
    for i in range(N_ITER):
        d = 1 if z >= 0 else -1
        nx = x - d * (y // (1 << i))
        ny = y + d * (x // (1 << i))
        z -= d * ATAN_BRAD[i]
        x, y = nx, ny
    x = (x + 128) // 256
    y = (y + 128) // 256
    return [(x, y), (-y, x), (-x, -y), (y, -x)][quad]


SIN = [cordic(a * 65536)[1] for a in range(256)]
COS = [cordic(a * 65536)[0] for a in range(256)]


# ---------------------------------------------------------------- 투영 (SPEC §3)
def tile_to_screen(tx, ty, h):
    return (16 * (tx - ty), 8 * (tx + ty) - h * TZ)


def world_to_screen(fx, fy, h):
    return ((fx - fy) * 16 // 65536, (fx + fy) * 8 // 65536 - h * TZ)


def screen_to_tile(px, py):
    """마름모 정의로부터 직접 — 나눗셈 식을 믿지 않고 기하로 푼다."""
    return ((px + 2 * py) // 32, (2 * py - px) // 32)


def screen_to_tile_geometric(px, py):
    """|u| + 2|v| <= 16 을 만족하는 타일을 실제로 찾아 본다 (O(9) 탐색).

       경계에서는 여러 타일이 조건을 만족한다. floor 규칙과 같은 것을 고르려면
       a = px+2py, b = 2py-px 가 큰 쪽을 택해야 한다.
    """
    best = None
    for tx in range(screen_to_tile(px, py)[0] - 2, screen_to_tile(px, py)[0] + 3):
        for ty in range(screen_to_tile(px, py)[1] - 2, screen_to_tile(px, py)[1] + 3):
            cx, cy = 16 * (tx - ty), 8 * (tx + ty) + 8
            u, v = px - cx, py - cy
            if abs(u) + 2 * abs(v) <= 16:
                if best is None or (tx + ty, tx) > (best[0] + best[1], best[0]):
                    best = (tx, ty)
    return best


PICK_MASK = [0] * 512
for _oy in range(16):
    for _ox in range(32):
        _A = (_ox + 2 * _oy) // 32
        _B = (2 * _oy - _ox) // 32
        PICK_MASK[_oy * 32 + _ox] = 2 * _A + (_B + 1)


def pick_mask(px, py):
    rc, rr = px // 32, py // 16
    ox, oy = px - 32 * rc, py - 16 * rr
    m = PICK_MASK[oy * 32 + ox]
    return (rc + rr + m // 2, rr - rc + m % 2 - 1)


MARGIN_X = TW // 2
MARGIN_Y = TH // 2 + MAXH * TZ + 32


def visible_range(x0, y0, x1, y1):
    X0, X1 = x0 - MARGIN_X, x1 + MARGIN_X
    Y0, Y1 = y0 - MARGIN_Y, y1 + MARGIN_Y
    tx0 = (X0 + 2 * Y0) // 32
    tx1 = (X1 + 2 * Y1) // 32
    ty0 = (2 * Y0 - X1) // 32
    ty1 = (2 * Y1 - X0) // 32
    return (max(tx0, 0), max(ty0, 0), min(tx1, MAP_W - 1), min(ty1, MAP_H - 1))


# ---------------------------------------------------------------- 난수 (SPEC §5.2)
class Rng(object):
    def __init__(self, seed):
        self.s = seed % LCG_M

    def next(self):
        self.s = (LCG_A * self.s + LCG_C) % LCG_M      # 분할 없이 한 번에
        return (self.s >> 16) & 0x7FFF


def dice_dist(n, m):
    c = [1]
    for _ in range(n):
        c2 = [0] * (len(c) + m)
        for s, v in enumerate(c):
            if v:
                for f in range(1, m + 1):
                    c2[s + f] += v
        c = c2
    return c


# ---------------------------------------------------------------- CRC (SPEC §11.1)
def crc16_table():
    tbl = []
    for i in range(256):
        c = i << 8
        for _ in range(8):
            c = ((c << 1) & 0xFFFF) ^ (0x1021 if c & 0x8000 else 0)
        tbl.append(c)
    return tbl


CRC_TBL = crc16_table()


def crc16(data):
    c = 0xFFFF
    for b in data:
        c = ((c << 8) & 0xFFFF) ^ CRC_TBL[((c >> 8) ^ b) & 0xFF]
    return c


# ---------------------------------------------------------------- 다이아몬드-스퀘어
def gen_height(n, corners, scale, seed, rough_num=58, rough_den=100):
    size = n + 1
    h = [[0] * size for _ in range(size)]
    h[0][0], h[0][n], h[n][0], h[n][n] = corners
    r = Rng(seed)
    step = n
    while step > 1:
        half = step // 2
        for y in range(half, size, step):
            for x in range(half, size, step):
                s = (h[y - half][x - half] + h[y - half][x + half]
                     + h[y + half][x - half] + h[y + half][x + half])
                h[y][x] = s // 4 + (r.next() % (2 * scale + 1) - scale)
        for y in range(0, size, half):
            xs = half if (y // half) % 2 == 0 else 0
            for x in range(xs, size, step):
                s = n2 = 0
                for dx, dy in ((-half, 0), (half, 0), (0, -half), (0, half)):
                    if 0 <= x + dx < size and 0 <= y + dy < size:
                        s += h[y + dy][x + dx]
                        n2 += 1
                h[y][x] = s // n2 + (r.next() % (2 * scale + 1) - scale)
        step = half
        scale = scale * rough_num // rough_den
    return [[max(0, min(1023, v)) for v in row] for row in h]


# ---------------------------------------------------------------- 경로 휴리스틱
MIN_MOVE = 8


def octile(ax, ay, bx, by):
    dx, dy = abs(ax - bx), abs(ay - by)
    hi, lo = max(dx, dy), min(dx, dy)
    return 8 * hi + 3 * lo


# ---------------------------------------------------------------- 정렬 (SPEC §6)
def box_bbox(b):
    """상자의 화면 경계상자. b = (id, x0,y0,z0, x1,y1,z1)"""
    _, x0, y0, z0, x1, y1, z1 = b
    xs, ys = [], []
    for x in (x0, x1):
        for y in (y0, y1):
            for z in (z0, z1):
                xs.append(16 * (x - y))
                ys.append(8 * (x + y) - z * TZ)
    return (min(xs), min(ys), max(xs), max(ys))


def bbox_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def behind(a, b):
    return a[4] <= b[1] or a[5] <= b[2] or a[6] <= b[3]


def depth_key(b):
    return (b[1] + b[2], b[3], b[0])


def topo_sort(items):
    """칸 알고리즘 + 순환 강제 절단. (순서, 절단 횟수) 를 돌려준다."""
    n = len(items)
    bb = [box_bbox(b) for b in items]
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for i in range(n):
        for j in range(n):
            if i == j or not bbox_overlap(bb[i], bb[j]):
                continue
            if behind(items[i], items[j]) and not behind(items[j], items[i]):
                adj[i].append(j)
                indeg[j] += 1
    done = [False] * n
    order, breaks = [], 0
    while len(order) < n:
        cand = [i for i in range(n) if not done[i] and indeg[i] == 0]
        if not cand:
            cand = [i for i in range(n) if not done[i]]
            breaks += 1
            pick = min(cand, key=lambda i: depth_key(items[i]))
            for i in range(n):
                if not done[i] and pick in adj[i]:
                    adj[i].remove(pick)
                    indeg[pick] -= 1
        else:
            pick = min(cand, key=lambda i: depth_key(items[i]))
        done[pick] = True
        order.append(items[pick][0])
        for j in adj[pick]:
            indeg[j] -= 1
        adj[pick] = []
    return order, breaks
