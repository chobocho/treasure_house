# -*- coding: utf-8 -*-
"""경로 탐색 — SPEC §8. 8방향 격자, 다익스트라(양동이 큐), A*(옥타일).

   비용은 전부 정수다. 직진 10, 대각 14 를 지형 이동비용과 곱해 10으로 나눈다.
   14 는 10*sqrt(2) = 14.142 의 정수 근사다 — 대각을 1.4배로 세는 관례.
"""
from . import gamemap as M

#        E  SE  S  SW  W  NW  N  NE
DIRX = [1, 1, 0, -1, -1, -1, 0, 1]
DIRY = [0, 1, 1, 1, 0, -1, -1, -1]
DIAG = [False, True, False, True, False, True, False, True]
STEP_BASE = [10, 14, 10, 14, 10, 14, 10, 14]
DIR_NAME = ['E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE']
CLIMB_MAX = 1
MIN_MOVE = M.MIN_MOVE           # 8 (ROAD)
BUCKET_N = 64                   # 최대 간선 비용 floordiv(14*20,10)=28 보다 크면 된다


def passable(m, x, y):
    return m.inside(x, y) and M.MOVE[m.terrain(x, y)] > 0


def step_ok(m, x, y, d):
    """(x,y) 에서 방향 d 로 한 칸 갈 수 있는가.

       마지막 조건이 '모서리 자르기 금지'다. 벽 두 장이 만나는 모서리를
       대각선으로 스쳐 지나가면 캐릭터가 벽을 뚫은 것처럼 보인다.
    """
    nx = x + DIRX[d]
    ny = y + DIRY[d]
    if not passable(m, nx, ny):
        return False
    dh = m.height(nx, ny) - m.height(x, y)
    if dh > CLIMB_MAX or dh < -CLIMB_MAX:
        return False
    if DIAG[d]:
        if not passable(m, nx, y) or not passable(m, x, ny):
            return False
    return True


def step_cost(m, nx, ny, d):
    """도착 칸의 지형으로 값을 매긴다. 떠나는 칸이 아니라."""
    return (STEP_BASE[d] * M.MOVE[m.terrain(nx, ny)]) // 10


STRAIGHT_MIN = (10 * MIN_MOVE) // 10          # 8  — 가장 싼 지형에서의 직진 비용
DIAG_MIN = (14 * MIN_MOVE) // 10              # 11 — 같은 지형에서의 대각 비용


def octile(ax, ay, bx, by):
    """가장 싼 지형만 밟았을 때의 정확한 8방향 최단거리. (정리 8.1, 8.2)

       흔히 쓰는 floordiv((10*(dx+dy) - 6*min) * 8, 10) 형태는 쓰지 않는다.
       내림이 두 번 들어가 h 의 감소량이 실제 걸음값보다 1 커질 수 있고,
       (47,47) 에서는 526 을 내놓는데 실제 최소 비용은 517 이라 허용성까지 깨진다.
       나눗셈 없이 8*hi + 3*lo 로 쓰면 그런 일이 아예 생기지 않는다.
    """
    dx = ax - bx
    if dx < 0:
        dx = -dx
    dy = ay - by
    if dy < 0:
        dy = -dy
    if dx < dy:
        hi, lo = dy, dx
    else:
        hi, lo = dx, dy
    return STRAIGHT_MIN * hi + (DIAG_MIN - STRAIGHT_MIN) * lo


class Bucket(object):
    """원형 양동이 큐. 간선 비용이 [0, BUCKET_N) 이면 이진 힙과 같은 순서를 준다.

       힙보다 빠른 이유는 비교가 없기 때문이다 — push 와 pop 이 O(1) 이고,
       커서가 한 바퀴 도는 비용만 전체에 걸쳐 O(최대키) 로 분산된다. (정리 8.3)
    """
    __slots__ = ('b', 'cur', 'n')

    def __init__(self):
        self.b = [[] for _ in range(BUCKET_N)]
        self.cur = 0
        self.n = 0

    def push(self, key, node):
        self.b[key % BUCKET_N].append((key, node))
        self.n += 1

    def pop_min(self):
        """커서부터 한 바퀴 돌며 처음 비지 않은 양동이의 마지막 원소를 꺼낸다."""
        if self.n == 0:
            return None
        for _ in range(BUCKET_N):
            q = self.b[self.cur]
            if q:
                self.n -= 1
                return q.pop()
            self.cur = (self.cur + 1) % BUCKET_N
        return None


def dijkstra(m, sx, sy):
    """시작점에서 모든 칸까지의 최소 비용. 못 가는 칸은 None."""
    w, h = m.w, m.h
    dist = [None] * (w * h)
    if not passable(m, sx, sy):
        return dist
    dist[sy * w + sx] = 0
    q = Bucket()
    q.push(0, sy * w + sx)
    while True:
        it = q.pop_min()
        if it is None:
            break
        g, idx = it
        if dist[idx] is not None and g > dist[idx]:
            continue
        x = idx % w
        y = idx // w
        for d in range(8):
            if not step_ok(m, x, y, d):
                continue
            nx = x + DIRX[d]
            ny = y + DIRY[d]
            ng = g + step_cost(m, nx, ny, d)
            ni = ny * w + nx
            if dist[ni] is None or ng < dist[ni]:
                dist[ni] = ng
                q.push(ng, ni)
    return dist


def astar(m, sx, sy, gx, gy):
    """(경로, 비용, 확장 노드 수). 못 가면 (None, None, 확장 수).

       f = g + h 를 같은 양동이 큐에 넣는다. h 가 일관적이므로 f 는 경로를 따라
       단조 증가하고 한 걸음에 최대 28 늘어난다 — 활성 폭이 BUCKET_N 미만이다.
    """
    w, h = m.w, m.h
    if not passable(m, sx, sy) or not passable(m, gx, gy):
        return (None, None, 0)
    gcost = [None] * (w * h)
    prev = [-1] * (w * h)
    closed = [False] * (w * h)
    si = sy * w + sx
    gi = gy * w + gx
    gcost[si] = 0
    q = Bucket()
    q.push(octile(sx, sy, gx, gy), si)
    expanded = 0
    while True:
        it = q.pop_min()
        if it is None:
            return (None, None, expanded)
        _f, idx = it
        if closed[idx]:
            continue
        closed[idx] = True
        expanded += 1
        if idx == gi:
            break
        x = idx % w
        y = idx // w
        g = gcost[idx]
        for d in range(8):
            if not step_ok(m, x, y, d):
                continue
            nx = x + DIRX[d]
            ny = y + DIRY[d]
            ni = ny * w + nx
            if closed[ni]:
                continue
            ng = g + step_cost(m, nx, ny, d)
            if gcost[ni] is None or ng < gcost[ni]:
                gcost[ni] = ng
                prev[ni] = idx
                q.push(ng + octile(nx, ny, gx, gy), ni)
    path = []
    i = gi
    while i != -1:
        path.append((i % w, i // w))
        i = prev[i]
    path.reverse()
    return (path, gcost[gi], expanded)
