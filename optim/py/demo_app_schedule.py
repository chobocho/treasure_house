# -*- coding: utf-8 -*-
"""13부 데모 — 스케줄링: 정렬 규칙 하나로 최적이 되는 문제와 NP-난해가 되는 문제."""
import random
import time

from py import fmt
from py.apps import schedule as S


def demo_wspt():
    print('■ 1. 단일 기계 가중 완료시간 — 정렬 한 번이면 최적이다')
    jobs = [('A', 6, 1), ('B', 2, 5), ('C', 4, 2), ('D', 1, 1)]
    rows = [['작업', '처리시간 p', '가중치 w', 'p/w', 'w/p']]
    for (nm, p, w) in jobs:
        rows.append([nm, '%d' % p, '%d' % w, '%.3f' % (p / w), '%.3f' % (w / p)])
    print(fmt.table(rows, align='lrrrr'))
    sched, total = S.wspt(jobs)
    order, best = S.brute_force_wspt(jobs)
    rows = [['순서', '완료시각 C', '가중치 w', 'w*C']]
    for (nm, c) in sched:
        w = dict((j[0], j[2]) for j in jobs)[nm]
        rows.append([nm, '%.0f' % c, '%d' % w, '%.0f' % (w * c)])
    rows.append(['합계', '', '', '%.0f' % total])
    print(fmt.table(rows, align='lrrr'))
    print('  WSPT 규칙(p/w 오름차순) 결과 %.0f, 전수 조사(%d! = %d가지) 최적 %.0f — 일치.'
          % (total, len(jobs), 24, best))
    print('  정렬 O(n log n) 으로 최적이 <증명>되는 드문 경우다. 증명은 교환 논법이며')
    print('  13부 52장에 있다.\n')


def demo_wspt_scale():
    print('■ 2. 규칙이 최적이면 크기는 문제가 되지 않는다')
    rows = [['작업 수 n', 'WSPT 시간(초)', '전수 조사 시간(초)', '두 값이 같은가']]
    rng = random.Random(7)
    for n in (5, 7, 9, 200, 20000):
        jobs = [('J%d' % i, rng.randint(1, 20), rng.randint(1, 20))
                for i in range(n)]
        t0 = time.time(); _, g = S.wspt(jobs); tw = time.time() - t0
        if n <= 9:
            t0 = time.time(); _, b = S.brute_force_wspt(jobs); tb = time.time() - t0
            same = '예' if abs(g - b) < 1e-9 else '아니오'
            tbs = '%.4f' % tb
        else:
            tbs, same = '불가 (n! 가지)', '-'
        rows.append(['%d' % n, '%.4f' % tw, tbs, same])
    print(fmt.table(rows, align='rrrl'))
    print('  n=20000 도 정렬 한 번이면 끝난다. 반면 전수 조사는 n=12 만 돼도 불가능하다.')
    print('  "구조를 알면 문제가 쉬워진다"의 가장 깨끗한 예다.\n')


def demo_jobshop():
    print('■ 3. 잡숍 makespan — 순서 결정이 이진 변수가 되는 순간')
    jobs = [[(0, 3), (1, 2)], [(1, 2), (0, 4)]]
    print('  작업 1: 기계0 에서 3시간 → 기계1 에서 2시간')
    print('  작업 2: 기계1 에서 2시간 → 기계0 에서 4시간')
    res, out = S.jobshop_milp(jobs, 2)
    rows = [['기계', '작업', '공정', '시작', '종료']]
    for d in out['schedule']:
        rows.append(['M%d' % d['machine'], 'J%d' % (d['job'] + 1),
                     '%d' % (d['op'] + 1), '%.1f' % d['start'], '%.1f' % d['end']])
    print(fmt.table(rows, align='llrrr'))
    print('  makespan = %.1f, 이진 변수 %d개, 분지한정 마디 %d개'
          % (out['makespan'], out['binaries'], out['nodes']))
    print('  전수 조사(기계별 순서 조합) 최적 = %.1f — 일치.' % S.jobshop_brute(jobs, 2))
    print()

    rows = [['작업 수', '공정 수', '이진 변수 수', 'makespan', 'B&B 마디', '전수 조사']]
    cases = [
        ([[(0, 3), (1, 2)], [(1, 2), (0, 4)]], 2),
        ([[(0, 2), (1, 3)], [(1, 2), (0, 2)], [(0, 1), (1, 1)]], 3),
        ([[(0, 2), (1, 3)], [(1, 2), (0, 2)], [(0, 1), (1, 4)],
          [(1, 3), (0, 1)]], 4),
    ]
    for jb, nj in cases:
        res, out = S.jobshop_milp(jb, 2, maxnodes=200000)
        bf = S.jobshop_brute(jb, 2)
        rows.append(['%d' % nj, '%d' % sum(len(s) for s in jb),
                     '%d' % out['binaries'], '%.1f' % out['makespan'],
                     '%d' % out['nodes'],
                     '%.1f' % bf if bf is not None else '-'])
    print(fmt.table(rows, align='rrrrrr'))
    print('  작업이 하나 늘 때마다 이진 변수가 빠르게 늘어난다 — 같은 기계 위의')
    print('  공정 쌍마다 "누가 먼저인가"를 정해야 하기 때문이다.')
    print('  이 배타적 선택은 6부의 LP 로는 적을 수 없고, 그래서 잡숍이 NP-난해가 된다.')
    print('  같은 "스케줄링"인데 1번 문제는 O(n log n), 이 문제는 지수적이다.')


def main():
    demo_wspt()
    demo_wspt_scale()
    demo_jobshop()


if __name__ == '__main__':
    main()
