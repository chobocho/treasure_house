# -*- coding: utf-8 -*-
"""그리기 순서 — SPEC §6. 화가 알고리즘을 DAG 로 푼다.

   바닥 타일은 (tx+ty) 오름차순이면 언제나 옳다(정리 6.1). 문제는 여러 칸을
   차지하는 물체다. '뒤에 있다' 는 관계가 반대칭이 아니라서, 순진하게
   비교 정렬을 돌리면 비교 함수가 모순을 일으킨다. 그래서 위상 정렬을 쓴다.
"""
from .proj import HH, HW, TZ

# 상자 = (id, x0, y0, z0, x1, y1, z1). 전부 반개구간 [a, b).
I_ID, I_X0, I_Y0, I_Z0, I_X1, I_Y1, I_Z1 = range(7)


def box_bbox(b):
    """상자의 화면 경계상자 (minx, miny, maxx, maxy).

       여덟 꼭짓점을 다 투영할 필요는 없지만, 그렇게 쓰면 왜 그 네 값인지가
       코드에서 사라진다. 상자 하나에 여덟 번은 싸다.
    """
    minx = miny = 1 << 30
    maxx = maxy = -(1 << 30)
    for x in (b[I_X0], b[I_X1]):
        for y in (b[I_Y0], b[I_Y1]):
            for z in (b[I_Z0], b[I_Z1]):
                sx = HW * (x - y)
                sy = HH * (x + y) - z * TZ
                if sx < minx:
                    minx = sx
                if sx > maxx:
                    maxx = sx
                if sy < miny:
                    miny = sy
                if sy > maxy:
                    maxy = sy
    return (minx, miny, maxx, maxy)


def bbox_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def behind(a, b):
    """a 를 b 보다 먼저 그려야 하는가.

       셋 중 하나만 성립해도 참이다. 이 느슨함이 화면에서는 대개 옳지만
       반대칭이 아니어서 순환을 만든다 — 덱 7부의 주제다.
    """
    return (a[I_X1] <= b[I_X0] or a[I_Y1] <= b[I_Y0] or a[I_Z1] <= b[I_Z0])


def depth_key(b):
    """동점을 가르는 기준. id 가 마지막에 들어가 결과가 완전히 결정적이다."""
    return (b[I_X0] + b[I_Y0], b[I_Z0], b[I_ID])


def topo_sort(items):
    """칸 알고리즘. 순환이 남으면 depth_key 가 가장 작은 것을 강제로 뽑는다.

       O(n^2) 로 간선을 만든다. 한 화면의 물체는 수십 개라 그게 가장 싸다.
       (n 이 커지면 화면 격자로 나눠 이웃만 비교해야 한다 — 덱 7부에서 다룬다.)
       반환: (id 순서, 순환을 자른 횟수)
    """
    n = len(items)
    bb = [box_bbox(b) for b in items]
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for i in range(n):
        for j in range(n):
            if i == j or not bbox_overlap(bb[i], bb[j]):
                continue
            # 양쪽 다 참이면 순서가 무의미하다 — 간선을 걸지 않는다 (보조정리 6.2)
            if behind(items[i], items[j]) and not behind(items[j], items[i]):
                adj[i].append(j)
                indeg[j] += 1
    done = [False] * n
    order = []
    breaks = 0
    while len(order) < n:
        pick = -1
        best = None
        for i in range(n):
            if done[i] or indeg[i] != 0:
                continue
            k = depth_key(items[i])
            if best is None or k < best:
                best = k
                pick = i
        if pick < 0:
            # 순환이다. 가장 뒤에 있어야 할 것을 강제로 방출하고 진입간선을 끊는다.
            breaks += 1
            for i in range(n):
                if done[i]:
                    continue
                k = depth_key(items[i])
                if best is None or k < best:
                    best = k
                    pick = i
            for i in range(n):
                if not done[i] and pick in adj[i]:
                    adj[i].remove(pick)
                    indeg[pick] -= 1
        done[pick] = True
        order.append(items[pick][I_ID])
        for j in adj[pick]:
            indeg[j] -= 1
        adj[pick] = []
    return (order, breaks)
