# -*- coding: utf-8 -*-
"""덱에 인용할 수치를 실제로 재서 out/measure.txt 로 남긴다.
   '대략 몇 배 빠르다'는 말을 쓰지 않기 위한 도구다. 전부 이 기계에서 잰 값이다."""
import io
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'py'))

from hexwar import hexcoord as H              # noqa: E402
from hexwar import path as P                  # noqa: E402
from hexwar import scenario                   # noqa: E402
from hexwar.hexmap import MAP_H, MAP_W, TERRAIN_MASK, T_MOVE   # noqa: E402
from hexwar.rng import Rng                    # noqa: E402

OUT = []


def say(s=''):
    OUT.append(s)
    print(s)


def bench(fn, n):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) * 1e6 / n      # 마이크로초/회


def heap_reachable(m, pool, unit):
    """비교용 — 같은 일을 이진 힙으로 한다. 결과 자료구조까지 똑같이 만들어야
       공정하다. 그러지 않으면 '탐색'이 아니라 '결과 조립'을 재게 된다."""
    import heapq
    start = m.axial_idx(unit.q, unit.r)
    budget = unit.mp
    best = [P.UNREACHED] * (m.w * m.h)
    best[start] = 0
    zoc = P.zoc_mask(m, pool, unit.side)
    pq = [(0, start)]
    while pq:
        c, cur = heapq.heappop(pq)
        if c != best[cur]:
            continue
        if cur != start and zoc[cur]:
            continue
        for _d, ni in m.neighbors_with_dir(cur):
            sc = P.step_cost(m, pool, unit.side, cur, ni)
            if sc < 0:
                continue
            nc = c + sc
            if nc <= budget and nc < best[ni]:
                best[ni] = nc
                heapq.heappush(pq, (nc, ni))
    cost, came, lst = {}, {}, []
    for i in range(m.w * m.h):
        if best[i] != P.UNREACHED:
            cost[i] = best[i]
            came[i] = -1
            lst.append(i)
    return P.Reach(cost, came, lst)


def main():
    m, pool, obj = scenario.load()
    u = pool.get(2)

    say('== 1. 이동 범위: 양동이 큐(Dial) vs 이진 힙 ==')
    a = bench(lambda: P.reachable(m, pool, u), 300)
    b = bench(lambda: heap_reachable(m, pool, u), 300)
    ra = P.reachable(m, pool, u)
    rb = heap_reachable(m, pool, u)
    same = ra.list == rb.list and all(ra.cost[i] == rb.cost[i] for i in ra.list)
    say('   양동이 큐 %8.1f us/회' % a)
    say('   이진 힙   %8.1f us/회   (%.2f배)' % (b, b / a))
    say('   두 결과가 같은가: %s' % ('예' if same else '아니오'))

    say()
    say('== 2. 맵 훑기: 평행 배열(SoA) vs 구조체 배열(AoS) ==')
    n = MAP_W * MAP_H
    soa = m.cells                                    # 바이트 배열
    aos = [{'terrain': m.cells[i] & TERRAIN_MASK, 'fog': m.fog[i],
            'occ': m.occupant[i], 'pad': 0} for i in range(n)]

    def scan_soa():
        t = 0
        for i in range(n):
            t += T_MOVE[soa[i] & TERRAIN_MASK]
        return t

    def scan_aos():
        t = 0
        for i in range(n):
            t += T_MOVE[aos[i]['terrain']]
        return t

    sa = bench(scan_soa, 2000)
    sb = bench(scan_aos, 2000)
    say('   SoA(바이트 배열) %8.2f us/회' % sa)
    say('   AoS(딕트 배열)   %8.2f us/회   (%.2f배)' % (sb, sb / sa))
    say('   같은 합인가: %s' % ('예' if scan_soa() == scan_aos() else '아니오'))

    say()
    say('== 3. 좌표를 무엇으로 키를 삼을 것인가 ==')
    flat = [0] * n
    dic = {}
    for row in range(MAP_H):
        for col in range(MAP_W):
            dic[(col, row)] = 0

    def use_flat():
        s = 0
        for row in range(MAP_H):
            base = row * MAP_W
            for col in range(MAP_W):
                s += flat[base + col]
        return s

    def use_dict():
        s = 0
        for row in range(MAP_H):
            for col in range(MAP_W):
                s += dic[(col, row)]
        return s

    fa = bench(use_flat, 2000)
    fb = bench(use_dict, 2000)
    say('   정수 인덱스 배열 %8.2f us/회' % fa)
    say('   (col,row) 튜플 키 %7.2f us/회   (%.2f배)' % (fb, fb / fa))

    say()
    say('== 4. 반올림: 파이썬 round() 는 짝수로 붙는다 ==')
    for v in (0.5, 1.5, 2.5, -0.5, -1.5):
        say('   round(%5.1f) = %-5s   round_div(%d, 2) = %d'
            % (v, round(v), int(v * 2), H.round_div(int(v * 2), 2)))
    say('   → 0.5 를 짝수로 붙이는 규칙(은행가 반올림)이라 언어마다 답이 갈린다.')

    say()
    say('== 5. LCG 하위 비트의 주기 ==')
    r = Rng(1)
    low = [r.next() & 1 for _ in range(16)]
    r = Rng(1)
    low3 = [r.next() & 7 for _ in range(16)]
    r = Rng(1)
    hi = [(r.next() >> 16) % 6 + 1 for _ in range(16)]
    say('   state & 1  : %s' % ' '.join(str(x) for x in low))
    say('   state & 7  : %s' % ' '.join(str(x) for x in low3))
    say('   (state>>16)%%6+1 : %s' % ' '.join(str(x) for x in hi))
    say('   → 최하위 비트는 주기 2, 하위 3비트는 주기 8. 주사위는 상위 비트에서 뽑아야 한다.')

    say()
    say('== 6. 화면 갱신량: 더티 사각형 vs 전체 ==')
    from hexwar.render import Dirty
    d = Dirty()
    d.add(64, 48, 32, 32)
    d.add(96, 72, 32, 32)
    d.add(180, 40, 32, 32)
    say('   더티 3장 합계 %5d 픽셀' % d.area())
    say('   전체 화면      %5d 픽셀   (%.1f배)' % (320 * 200, 320 * 200 / max(1, d.area())))
    say('   병합 후 사각형 수: %d' % len(d.rects))

    say()
    say('== 7. 거리 공식과 BFS 가 모든 쌍에서 같은가 ==')
    # 오라클은 공식을 쓰지 않는다 — 이웃 그래프를 너비 우선으로 걸어 걸음 수를 센다.
    # 원점에서 각 칸까지의 BFS 거리를 한 번 구해 두고(평행 이동 불변), 모든 쌍을 대조한다.
    bfs = {(0, 0): 0}
    frontier = [(0, 0)]
    d = 0
    while d < 16:                     # 범위 ±4 이면 최대 거리 16
        d += 1
        nxt = []
        for (q, r) in frontier:
            for (dq, dr) in H.DIRS:
                n = (q + dq, r + dr)
                if n not in bfs:
                    bfs[n] = d
                    nxt.append(n)
        frontier = nxt
    bad = 0
    tested = 0
    for aq in range(-4, 5):
        for ar in range(-4, 5):
            for bq in range(-4, 5):
                for br in range(-4, 5):
                    tested += 1
                    if H.distance(aq, ar, bq, br) != bfs[(bq - aq, br - ar)]:
                        bad += 1
    say('   축좌표 공식 vs BFS 걸음 수: %d쌍 중 불일치 %d' % (tested, bad))

    say()
    say('== 8. 2d6 분포와 전투 결과표 ==')
    r = Rng(0x1BADB002)
    hist = [0] * 13
    N = 60000
    for _ in range(N):
        hist[r.d6() + r.d6()] += 1
    say('   합  확률(이론)  실측(%d회)' % N)
    for v in range(2, 13):
        theo = (6 - abs(7 - v)) / 36.0
        say('   %2d   %6.2f%%     %6.2f%%   %s'
            % (v, theo * 100, hist[v] * 100.0 / N, '#' * int(hist[v] * 200.0 / N)))
    say()
    say('   전력차 d 에 따른 방어측 손실 기댓값 (2d6 기준)')
    say('   d(공격−방어)   손실3   손실2   손실1   손실0   기댓값')
    for d in range(-6, 7):
        cnt = [0, 0, 0, 0]
        for a in range(1, 7):
            for b in range(1, 7):
                sc = d + a + b - 7
                if sc >= 4:
                    cnt[0] += 1
                elif sc >= 1:
                    cnt[1] += 1
                elif sc >= -2:
                    cnt[2] += 1
                else:
                    cnt[3] += 1
        exp = (cnt[0] * 3 + cnt[1] * 2 + cnt[2] * 1) / 36.0
        say('   %+3d          %5.1f%% %5.1f%% %5.1f%% %5.1f%%   %.2f'
            % (d, cnt[0] * 100 / 36.0, cnt[1] * 100 / 36.0,
               cnt[2] * 100 / 36.0, cnt[3] * 100 / 36.0, exp))

    io.open(os.path.join(BASE, 'out', 'measure.txt'), 'w',
            encoding='utf-8').write('\n'.join(OUT) + '\n')


if __name__ == '__main__':
    main()
