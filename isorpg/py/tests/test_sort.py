# -*- coding: utf-8 -*-
"""상자 정렬 — 부분순서, 순환, 보조정리 6.2 를 실제로 확인한다."""
from __future__ import print_function

import harness as H
from isorpg import sortdag as S

H.title('sortdag')


def load_cases():
    rows = [l.split() for l in H.golden('sortcase.txt').strip().split('\n')]
    out = []
    i = 1
    while i < len(rows):
        _, num, name, n = rows[i]
        n = int(n)
        i += 1
        out.append((int(num), name,
                    [tuple(int(v) for v in rows[i + k]) for k in range(n)]))
        i += n
    return out


CASES = load_cases()
H.check('사례 개수', len(CASES), 6)

EXPECT = {1: ([0, 1], 0), 2: ([0, 1], 0), 3: ([0, 1], 0),
          4: ([2, 0, 1], 0), 5: ([0, 1], 0), 6: ([0, 1, 2], 1)}
for num, name, items in CASES:
    order, breaks = S.topo_sort(items)
    H.check('case %d %s' % (num, name), (order, breaks), EXPECT[num])

# ---- 6번은 진짜 3-순환인가 (간선이 정확히 세 개, 한 방향씩)
items = dict((n, it) for n, _, it in CASES)[6]
bb = [S.box_bbox(b) for b in items]
edges = set()
for i in range(3):
    for j in range(3):
        if i != j and S.bbox_overlap(bb[i], bb[j]):
            if S.behind(items[i], items[j]) and not S.behind(items[j], items[i]):
                edges.add((i, j))
H.check('3-순환 간선', sorted(edges), [(0, 1), (1, 2), (2, 0)])

# ---- 5번은 상호 관계인데 화면에서 겹치는가
items5 = dict((n, it) for n, _, it in CASES)[5]
b5 = [S.box_bbox(b) for b in items5]
H.check_true('5번 경계상자 겹침', S.bbox_overlap(b5[0], b5[1]))
H.check_true('5번 상호 behind', S.behind(items5[0], items5[1])
             and S.behind(items5[1], items5[0]))

# ---- 보조정리 6.2 : x/y 상호는 겹칠 수 없다
rs = 999
def rnd(n):
    global rs
    rs = (1103515245 * rs + 12345) % (2 ** 31)
    return rs % n

viol = xy_mutual = 0
for _ in range(60000):
    a = (0, rnd(6), rnd(6), rnd(4), 0, 0, 0)
    a = (0, a[1], a[2], a[3], a[1] + 1 + rnd(3), a[2] + 1 + rnd(3), a[3] + 1 + rnd(2))
    b = (1, rnd(6), rnd(6), rnd(4), 0, 0, 0)
    b = (1, b[1], b[2], b[3], b[1] + 1 + rnd(3), b[2] + 1 + rnd(3), b[3] + 1 + rnd(2))
    if (a[4] <= b[1] and b[5] <= a[2]) or (b[4] <= a[1] and a[5] <= b[2]):
        xy_mutual += 1
        if S.bbox_overlap(S.box_bbox(a), S.box_bbox(b)):
            viol += 1
H.note('x/y 상호 사례 %d건 생성', xy_mutual)
H.check('보조정리 6.2 반례', viol, 0)

# ---- 정렬 결과는 결정적인가 (같은 입력 -> 같은 출력)
for num, name, items in CASES:
    H.check('결정성 case %d' % num, S.topo_sort(items), S.topo_sort(items))

# ---- 순환이 없으면 위상 순서가 실제로 모든 간선을 지키는가
for num, name, items in CASES:
    order, breaks = S.topo_sort(items)
    if breaks:
        continue
    pos = dict((v, i) for i, v in enumerate(order))
    bad = 0
    bbs = [S.box_bbox(b) for b in items]
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and S.bbox_overlap(bbs[i], bbs[j]):
                if S.behind(items[i], items[j]) and not S.behind(items[j], items[i]):
                    if pos[items[i][0]] > pos[items[j][0]]:
                        bad += 1
    H.check('case %d 간선 위반' % num, bad, 0)

H.done()
