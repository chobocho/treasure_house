# -*- coding: utf-8 -*-
"""이동·예약·밀어내기·대형 — SPEC §13.

   이 모듈의 전부는 불변식 R 하나다: **어떤 타일도 두 엔티티에게 동시에
   예약되지 않는다.** 걸음을 시작할 때 도착 칸을 먼저 쥐고, 걸음이 끝나야
   출발 칸을 놓는다. 두 칸을 쥐는 구간이 있어야 두 유닛이 서로의 칸으로
   동시에 들어가는 사고가 없다.

   교착은 완전히 사라지지 않는다. 좁은 통로에서 마주 오는 두 무리는 24틱 뒤
   명령을 포기하는 것으로 풀린다 — 해결이 아니라 포기다(§13.3).
"""

import math

from . import const as C
from . import fixed as F
from . import path as P
from . import spatial as S

ARRIVE_R = 2                     # §13.4 도착 반경 (타일, 체비셰프)
REPATH_TICKS = 8                 # §13.3 이만큼 막히면 경로를 다시 찾는다
GIVEUP_TICKS = 24                # §13.3 이만큼 막히면 명령을 포기한다

LINE, COLUMN, BOX = 0, 1, 2      # §13.5 대형
STOP_DIR = 255


# ── SPEC §13.1 타일 사이 보간 ───────────────────────────────────────────────
_SQRT2 = math.sqrt(2.0)          # §19.4 의 주입 버그에서만 쓴다


def step_amount(speed, d, float_bug=False):
    """방향 d 로 한 틱에 늘어나는 진행률 (16.16).

       대각 보정을 빼면 유닛이 대각으로 √2 = 41 % 빨라진다. 도스 시절에도
       이 버그를 그대로 둔 게임이 있었고, 그래서 플레이어들이 지그재그로
       움직였다 — 14부에서 이 버그를 일부러 넣은 데모를 보여 준다.

       `float_bug` 는 §19.4 의 **일부러 넣은** 디싱크다. 1/√2 는 이진 소수로
       끝나지 않으므로 진행률이 정수가 아니게 되고, 그 누적 차이가 px·py 를
       통해 상태 해시에 바로 나타난다. 엔진의 다른 어느 곳도 실수를 쓰지 않는다.
    """
    st = F.fp_div(speed, F.fp(C.TILE))
    if F.DCOST[d] == F.D_DIAG:
        if float_bug:
            return st / _SQRT2
        return F.fp_mul(st, F.FP_DIAG)
    return st


def pos_of(w, m, i):
    """화면 위치는 상태가 아니라 from_t·to_t·prog 의 파생값이다 (§13.1)."""
    fx, fy = w.from_t[i] % m.w, w.from_t[i] // m.w
    tx, ty = w.to_t[i] % m.w, w.to_t[i] // m.w
    px = F.fp(fx * C.TILE) + F.fp_mul(F.fp((tx - fx) * C.TILE), w.prog[i])
    py = F.fp(fy * C.TILE) + F.fp_mul(F.fp((ty - fy) * C.TILE), w.prog[i])
    return px, py


# ── SPEC §13.5 회전과 대형 ──────────────────────────────────────────────────
def rot8(d, ox, oy):
    """이동 방향 d 로 오프셋을 돌린다. 행렬이 아니라 8방향 표다.

       45° 회전은 정수 격자를 보존하지 않으므로 대각은 이웃한 두 직교 방향의
       결과를 더해 2로 내림 나눗셈한다 — 근사이며, 그렇다고 적어 둔다.
    """
    if d == 0:
        return ox, oy
    if d == 2:
        return -oy, ox
    if d == 4:
        return -ox, -oy
    if d == 6:
        return oy, -ox
    ax, ay = rot8(d - 1, ox, oy)
    bx, by = rot8((d + 1) % 8, ox, oy)
    return F.floordiv(ax + bx, 2), F.floordiv(ay + by, 2)


def formation(n, shape, d, gx, gy, m, kind):
    """목표 주위 n 개의 슬롯 타일. 슬롯 순서 = 핸들 오름차순으로 나눠 준다.

       맵 밖이거나 통행 불가인 슬롯은 목표 타일 자체로 접는다. 슬롯을 다시
       찾아 주지는 않는다 — 반쯤 성공하는 재배치가 교착보다 나쁜 그림을 만든다.
    """
    out = []
    if n <= 0:
        return out
    side = F.isqrt(n - 1) + 1                  # ceil(sqrt(n)) — §2.5 정수 제곱근
    for k in range(n):
        if shape == LINE:
            ox, oy = k - F.floordiv(n - 1, 2), 0
        elif shape == COLUMN:
            ox, oy = 0, k
        else:
            ox = F.fmod(k, side) - F.floordiv(side - 1, 2)
            oy = F.floordiv(k, side)
        rx, ry = rot8(d, ox, oy)
        x, y = gx + rx, gy + ry
        if not m.passable_terrain(x, y, kind):
            x, y = gx, gy
        out.append((x, y))
    return out


# ── SPEC §13.3 밀어내기 ─────────────────────────────────────────────────────
def push_dir(mv, i, from_dir):
    """i 를 어느 방향으로 비키게 할지. 없으면 255.

       훑는 순서는 미는 쪽 진행 방향의 **반대에서 시작해 시계 방향**이다.
       순서를 명세로 고정하지 않으면 세 언어가 다른 칸을 고르고, 그 차이는
       한 틱 뒤 위치 차이가 되어 그대로 디싱크다.
    """
    w, m = mv.w, mv.m
    kind = C.MOVE_KIND[w.kind[i]]
    for k in range(8):
        d = F.fmod(from_dir + 4 + k, 8)
        u, v = w.tx[i] + F.DX[d], w.ty[i] + F.DY[d]
        if not m.passable_terrain(u, v, kind):
            continue
        if mv.resv[v * m.w + u] != 0:
            continue
        return d
    return STOP_DIR


class Movement(object):
    """예약판과 유닛별 경로. sim 이 하나만 들고 있는다 (§18.2 4단계)."""

    def __init__(self, world, tmap, float_bug=False):
        self.w = world
        self.m = tmap
        self.float_bug = float_bug
        self.resv = [0] * (tmap.w * tmap.h)
        self.blocked = [0] * C.MAX_ENT
        self.path = [[] for _ in range(C.MAX_ENT)]
        self.goal = [-1] * C.MAX_ENT
        self.cache = P.Cache()
        # 이번 틱에 타일을 넘은 유닛 (i, 이전 타일, 새 타일). sim 의 7단계가
        # 이것만 보고 시야를 remove/add 한다 — 전수 재계산을 피하는 유일한 길이다.
        self.crossed = []

    # ── SPEC §13.2 예약 ────────────────────────────────────────────────────
    def reserve(self, tile, h):
        cur = self.resv[tile]
        if cur != 0 and cur != h:
            return False
        self.resv[tile] = h
        return True

    def release(self, tile, h):
        if self.resv[tile] != h:
            return False
        self.resv[tile] = 0
        return True

    def claim(self, i):
        """엔티티가 선 칸을 예약한다. 건물은 발자국 전체를 영구히 쥔다."""
        w, m = self.w, self.m
        h = w.handle(i)
        f = C.FOOT[w.kind[i]]
        ok = True
        for dy in range(f):
            for dx in range(f):
                x, y = w.tx[i] + dx, w.ty[i] + dy
                if not m.in_map(x, y):
                    continue
                if not self.reserve(y * m.w + x, h):
                    ok = False
                if C.IS_BUILDING[w.kind[i]]:
                    m.set_building(x, y, True)
                else:
                    m.occupy(x, y, True)
        return ok

    def unclaim(self, i):
        """사망·철거. 건물은 잔해를 남기므로 통행이 지형에서 복구된다(§4.3)."""
        w, m = self.w, self.m
        h = w.handle(i)
        f = C.FOOT[w.kind[i]]
        for dy in range(f):
            for dx in range(f):
                x, y = w.tx[i] + dx, w.ty[i] + dy
                if not m.in_map(x, y):
                    continue
                self.release(y * m.w + x, h)
                if C.IS_BUILDING[w.kind[i]]:
                    m.set_building(x, y, False)
                else:
                    m.occupy(x, y, False)
        self.release(w.to_t[i], h)
        self.path[i] = []
        self.goal[i] = -1
        self.blocked[i] = 0

    # ── 명령 ───────────────────────────────────────────────────────────────
    def order(self, i, gx, gy):
        """목표 타일로 가는 경로를 깐다. 닿을 수 없으면 §8.6 의 대체 목표로."""
        if not self.m.in_map(gx, gy):
            return False
        self.blocked[i] = 0
        return self._plan(i, gx, gy)

    def _plan(self, i, gx, gy):
        """경로만 다시 깐다 — blocked 카운터는 건드리지 않는다(§13.3 재탐색)."""
        w, m = self.w, self.m
        kind = C.MOVE_KIND[w.kind[i]]
        s = (w.tx[i], w.ty[i])
        goal = P.closest_reachable(m, kind, s, (gx, gy))
        if goal is None:
            self.path[i] = []
            self.goal[i] = -1
            return False
        _cost, tiles = P.find(m, kind, s, goal, self.cache)
        self.path[i] = tiles[1:]
        self.goal[i] = goal[1] * m.w + goal[0] if self.path[i] else -1
        return True

    def stop(self, i):
        """§12.4 STOP — 아직 시작하지 않은 걸음의 예약만 반납한다(§13.2)."""
        w = self.w
        self.path[i] = []
        self.goal[i] = -1
        self.blocked[i] = 0
        if w.prog[i] == 0 and w.to_t[i] != w.from_t[i]:
            self.release(w.to_t[i], w.handle(i))
            w.to_t[i] = w.from_t[i]

    # ── SPEC §18.2 4단계: 핸들 오름차순으로 한 틱 ──────────────────────────
    def step(self):
        w = self.w
        self.crossed = []
        for i in range(1, C.MAX_ENT):
            if w.alive[i] == 1 and C.IS_BUILDING[w.kind[i]] == 0:
                self.step_one(i)

    def step_one(self, i):
        w, m = self.w, self.m
        h = w.handle(i)
        if w.prog[i] > 0:                       # 걸음 도중 — 끝까지 마친다
            w.prog[i] += step_amount(C.SPEED[w.kind[i]], w.dir[i],
                                     self.float_bug)
            if w.prog[i] >= F.FP_ONE:
                self._finish_step(i, h)
            w.px[i], w.py[i] = pos_of(w, m, i)
            return
        if not self.path[i]:
            return
        if self._arrived(i, h):
            return
        nxt = self.path[i][0]
        d = F.atan8(nxt % m.w - w.tx[i], nxt // m.w - w.ty[i])
        if not self.reserve(nxt, h):
            self._on_blocked(i, d)
            return
        self.blocked[i] = 0
        w.dir[i] = d
        w.to_t[i] = nxt
        w.prog[i] = step_amount(C.SPEED[w.kind[i]], d, self.float_bug)
        if w.prog[i] >= F.FP_ONE:               # 아주 빠른 유닛은 한 틱에 넘는다
            self._finish_step(i, h)
        w.px[i], w.py[i] = pos_of(w, m, i)

    def _finish_step(self, i, h):
        w, m = self.w, self.m
        old = w.from_t[i]
        self.release(old, h)
        m.occupy(old % m.w, old // m.w, False)
        w.from_t[i] = w.to_t[i]
        w.prog[i] = 0
        nx, ny = w.to_t[i] % m.w, w.to_t[i] // m.w
        w.move_tile(i, nx, ny)
        m.occupy(nx, ny, True)
        self.crossed.append((i, old, w.to_t[i]))
        if self.path[i] and self.path[i][0] == w.to_t[i]:
            self.path[i] = self.path[i][1:]
        if not self.path[i]:
            self.goal[i] = -1

    def _arrived(self, i, h):
        """§13.4 목표 칸이 남의 것이고 ARRIVE_R 안이면 도착으로 친다.

           이것이 없으면 무리의 마지막 한 기가 영원히 목표 칸을 두드린다.
        """
        w, m = self.w, self.m
        g = self.goal[i]
        if g < 0:
            return False
        taken = self.resv[g]
        if taken == 0 or taken == h:
            return False
        if F.dinf(g % m.w - w.tx[i], g // m.w - w.ty[i]) > ARRIVE_R:
            return False
        self.path[i] = []
        self.goal[i] = -1
        self.blocked[i] = 0
        return True

    def _on_blocked(self, i, d):
        """§13.3 막힘 — 8틱이면 재탐색, 24틱이면 포기."""
        w, m = self.w, self.m
        self.blocked[i] += 1
        nxt = self.path[i][0]
        other = self.resv[nxt]
        if w.valid(other):
            j = S.index(other)
            if (w.owner[j] == w.owner[i] and w.prog[j] == 0
                    and not self.path[j] and C.IS_BUILDING[w.kind[j]] == 0):
                pd = push_dir(self, j, d)       # 정지한 아군은 비켜 준다
                if pd != STOP_DIR:
                    self.path[j] = [(w.ty[j] + F.DY[pd]) * m.w
                                    + w.tx[j] + F.DX[pd]]
                    self.goal[j] = self.path[j][0]
        if self.blocked[i] >= GIVEUP_TICKS:
            self.path[i] = []
            self.goal[i] = -1
            self.blocked[i] = 0
        elif self.blocked[i] == REPATH_TICKS and self.goal[i] >= 0:
            g = self.goal[i]
            self._plan(i, g % m.w, g // m.w)
