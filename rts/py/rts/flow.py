# -*- coding: utf-8 -*-
"""흐름장·클리어런스·브러시파이어 (SPEC §11).

   A* 는 "한 유닛이 한 목표로" 가는 도구다. 무리 40기가 같은 깃발로 몰려갈 때
   A* 를 40번 부르는 것은 같은 답을 40번 계산하는 것이다. 적분장은 반대로
   목표에서 한 번 거꾸로 퍼뜨려 두고, 유닛은 자기 칸의 방향 하나만 읽는다.
   손익분기는 out/bench.txt 3절에 실측으로 남긴다.

   여기의 모든 장은 **지형만** 본다. 점유 비트를 넣으면 유닛이 움직일 때마다
   장을 다시 깔아야 하고, 그러면 애초에 장을 쓰는 이유가 없어진다.
"""

from . import fixed as F

INF = 65535                      # SPEC §11.1 — 세 언어가 같은 수를 찍어야 한다
NB = F.D_DIAG + 1                # 양동이 15개 (§8.4 와 같은 이유)
STOP = 255


def _dial(m, kind, seeds):
    """다중 시작점 다익스트라. seeds 는 (칸번호, 초기비용) 목록.

       O(칸수 × 8) 시간, O(칸수) 공간. 간선 비용이 10 과 14 둘뿐이라
       원형 양동이 15개로 힙 없이 돈다 — 정리 8.3 이 그대로 적용된다.
    """
    w, h = m.w, m.h
    dist = [INF] * (w * h)
    buckets = [[] for _ in range(NB)]
    pending = 0
    lo = INF
    for (i, c) in seeds:
        if c < dist[i]:
            dist[i] = c
            buckets[c % NB].append(i)
            pending += 1
            if c < lo:
                lo = c
    if not pending:
        return dist
    cur = lo
    while pending:
        b = buckets[cur % NB]
        while not b:
            cur += 1
            b = buckets[cur % NB]
        p = b.pop()
        pending -= 1
        if dist[p] != cur:                 # 낡은 항목 — 감소키는 만들지 않는다
            continue
        x, y = p % w, p // w
        for d in range(8):
            u, v = x + F.DX[d], y + F.DY[d]
            if not m.passable_terrain(u, v, kind):
                continue                   # 확장은 통행 가능한 칸으로만
            nd = cur + F.DCOST[d]
            j = v * w + u
            if nd < dist[j]:
                dist[j] = nd
                buckets[nd % NB].append(j)
                pending += 1
    return dist


# ── SPEC §11.1 적분장 ───────────────────────────────────────────────────────
def integration(m, kind, goals):
    """목표 집합에서 거꾸로 퍼뜨린 비용장. 도달 불가는 INF.

       막힌 목표는 무시한다(§11.1). 닿을 수 없는 칸을 0 으로 심으면 장 전체가
       그쪽으로 기울고, 그것은 §8.6 의 대체 목표가 맡을 몫이다.
    """
    seeds = []
    for (x, y) in goals:
        if m.passable_terrain(x, y, kind):
            seeds.append((y * m.w + x, 0))
    return _dial(m, kind, seeds)


# ── SPEC §11.2 경사장 ───────────────────────────────────────────────────────
def flow_dirs(m, kind, integ):
    """각 칸에서 갈 방향. 후보가 없으면 255(정지).

       동점은 **방향 번호가 작은 쪽**이다. 언어별 min 구현에 맡기면 대칭 맵에서
       무리가 좌우로 갈리고, 그 갈림은 PPM 바이트 비교에서 바로 잡힌다.
    """
    w, h = m.w, m.h
    out = [STOP] * (w * h)
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if integ[i] >= INF or not m.passable_terrain(x, y, kind):
                continue
            best, bd = INF, STOP
            for d in range(8):
                u, v = x + F.DX[d], y + F.DY[d]
                if not m.passable_terrain(u, v, kind):
                    continue
                c = integ[v * w + u]
                if c < best:               # 등호를 빼면 작은 d 가 이긴다
                    best, bd = c, d
            out[i] = bd
    return out


# ── SPEC §11.3 클리어런스 ───────────────────────────────────────────────────
def clearance(m, kind):
    """clear[i] = (x,y) 를 좌상단으로 하는 통행 가능 정사각형의 최대 변 (정리 11.1).

       O(칸수) 시간, O(칸수) 공간 — 오른쪽 아래에서 한 번만 훑는다.
       맵 밖은 0 이므로 오른쪽·아래 가장자리의 자유 칸은 1 이 된다.
    """
    w, h = m.w, m.h
    c = [0] * (w * h)
    for y in range(h - 1, -1, -1):
        for x in range(w - 1, -1, -1):
            if not m.passable_terrain(x, y, kind):
                continue
            if x + 1 >= w or y + 1 >= h:
                c[y * w + x] = 1
            else:
                r = c[y * w + x + 1]
                d = c[(y + 1) * w + x]
                q = c[(y + 1) * w + x + 1]
                c[y * w + x] = 1 + min(r, d, q)
    return c


def size_passable(clear, m, x, y, size):
    """크기 size 인 유닛이 (x,y) 를 좌상단으로 설 수 있는가."""
    if not m.in_map(x, y):
        return False
    return clear[y * m.w + x] >= size


# ── SPEC §11.4 브러시파이어 ─────────────────────────────────────────────────
def brushfire(m, kind):
    """가장 가까운 막힌 칸까지의 옥타일 비용. 막힌 칸은 0.

       맵 밖도 막힌 칸이다(§4.2 의 terrain_at 규약). 그래서 가장자리 자유 칸은
       10 이고, AI 는 맵 끝에 건물을 붙이지 않는다(§17.4).
    """
    w, h = m.w, m.h
    seeds = []
    for y in range(h):
        for x in range(w):
            if not m.passable_terrain(x, y, kind):
                seeds.append((y * w + x, 0))
                continue
            best = INF
            for d in range(8):             # 맵 밖 이웃은 비용 0 짜리 시작점이다
                if not m.in_map(x + F.DX[d], y + F.DY[d]):
                    if F.DCOST[d] < best:
                        best = F.DCOST[d]
            if best < INF:
                seeds.append((y * w + x, best))
    return _dial(m, kind, seeds)
