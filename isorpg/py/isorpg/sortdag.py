# -*- coding: utf-8 -*-
"""그리기 순서 — SPEC §6. 화가 알고리즘을 DAG 로 푼다.

   바닥 타일은 (tx+ty) 오름차순이면 언제나 옳다(정리 6.1). 문제는 여러 칸을
   차지하는 물체다. '뒤에 있다' 는 관계가 반대칭이 아니라서, 순진하게
   비교 정렬을 돌리면 비교 함수가 모순을 일으킨다. 그래서 위상 정렬을 쓴다.
"""
import heapq

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

       간선은 화면 x 로 훑으며 만든다(쓸어내기). 정렬 자체는 O((V+E) log V).
       우선순위 큐의 키에 id 가 들어 있어 동점이 없다. 그래서 어떤 힙 구현을 써도
       결과가 같다 — 세 언어가 각자의 힙을 써도 되는 이유다.
       반환: (id 순서, 순환을 자른 횟수)
    """
    n = len(items)
    bb = [box_bbox(b) for b in items]
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    # 화면 x 로 훑는 쓸어내기. 모든 쌍을 보면 O(n^2) 인데, 한 화면에 상자가
    # 600개쯤 되면 18만 번이다. x 구간이 겹치는 것끼리만 보면 그 4분의 1로 준다.
    idx = sorted(range(n), key=lambda i: (bb[i][0], i))
    for a in range(n):
        i = idx[a]
        bi = bb[i]
        ii = items[i]
        ri = bi[2]
        for b in range(a + 1, n):
            j = idx[b]
            bj = bb[j]
            if bj[0] >= ri:
                break                      # 이후는 전부 오른쪽 — 더 볼 필요가 없다
            if bi[3] <= bj[1] or bj[3] <= bi[1]:
                continue
            jj = items[j]
            aij = behind(ii, jj)
            aji = behind(jj, ii)
            # 양쪽 다 참이면 순서가 무의미하다 — 간선을 걸지 않는다 (보조정리 6.2)
            if aij and not aji:
                adj[i].append(j)
                indeg[j] += 1
            elif aji and not aij:
                adj[j].append(i)
                indeg[i] += 1
    heap = []
    for i in range(n):
        if indeg[i] == 0:
            heapq.heappush(heap, (depth_key(items[i]), i))
    done = [False] * n
    order = []
    breaks = 0
    left = n
    while left > 0:
        if heap:
            _k, pick = heapq.heappop(heap)
            if done[pick]:
                continue
        else:
            # 순환이다. 남은 것 중 가장 뒤에 있어야 할 것을 강제로 방출한다.
            breaks += 1
            pick = -1
            best = None
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
        left -= 1
        order.append(items[pick][I_ID])
        for j in adj[pick]:
            indeg[j] -= 1
            if indeg[j] == 0 and not done[j]:
                heapq.heappush(heap, (depth_key(items[j]), j))
        adj[pick] = []
    return (order, breaks)
