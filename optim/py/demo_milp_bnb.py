# -*- coding: utf-8 -*-
"""7부 데모 — 분지한정이 실제로 무엇을 잘라 내는가."""
import random

from py import fmt
from py import lp
from py import milp


def demo_gap():
    print('■ 1. 완화는 하한을 준다 — 그리고 그 간격이 문제의 난이도다')
    rows = [['문제', 'LP 완화 최적값', '정수 최적값', '간격', '탐색 마디 수']]
    cases = [
        ('작은 배낭형', [-5.0, -4.0], [[6.0, 4.0], [1.0, 2.0]], [24.0, 6.0], None),
        ('생산 계획', [-3.0, -2.0, -4.0], [[1.0, 1.0, 2.0], [2.0, 1.0, 1.0]],
         [10.0, 12.0], [6.0] * 3),
        ('빡빡한 자원', [-7.0, -9.0], [[3.0, 5.0], [4.0, 2.0]], [17.0, 13.0], None),
    ]
    for name, c, A, b, ub in cases:
        rel = lp.solve_lp(c, A_ub=A, b_ub=b)
        r = milp.branch_and_bound(c, A_ub=A, b_ub=b, ub=ub)
        rows.append([name, '%.4f' % rel.obj, '%.4f' % r.obj,
                     '%.4f' % (r.obj - rel.obj), '%d' % r.nodes])
    print(fmt.table(rows, align='lrrrr'))
    print('  간격이 0 이면 완화만 풀어도 끝난다(6부의 완전단모듈 문제가 그렇다).')
    print('  간격이 클수록 가지치기가 덜 되고 마디 수가 늘어난다.\n')


def demo_tree():
    print('■ 2. 분지한정 나무의 발자국')
    c = [-5.0, -4.0]
    A = [[6.0, 4.0], [1.0, 2.0]]
    b = [24.0, 6.0]
    r = milp.branch_and_bound(c, A_ub=A, b_ub=b, keep_history=True)
    rows = [['마디', '깊이', 'LP 상태', '하한(LP 값)', '그때의 최선', '판정']]
    for h in r.history:
        if h['status'] != 'optimal':
            verdict = '실행불가 — 가지치기'
        elif h['incumbent'] < float('inf') and h['bound'] >= h['incumbent']:
            verdict = '하한이 나쁘다 — 가지치기'
        else:
            verdict = '분지 또는 갱신'
        rows.append(['%d' % h['node'], '%d' % h['depth'], h['status'],
                     '%.4f' % h['bound'] if h['bound'] is not None else '-',
                     '%.4f' % h['incumbent'] if h['incumbent'] < float('inf') else '없음',
                     verdict])
    print(fmt.table(rows, align='rrlrll'))
    print('  최적해 x = %s, 목적값 %.4f, 탐색 마디 %d개'
          % (r.x, r.obj, r.nodes))
    print('  전수 조사라면 x1 in 0..4, x2 in 0..3 만 해도 20가지다. 마디 수가 그보다')
    print('  적다는 것이 가지치기가 실제로 일한다는 증거다.\n')


def demo_growth():
    print('■ 3. 크기가 커지면 — 마디 수의 증가 (n 마다 무작위 8개 평균)')
    rows = [['변수 n', '평균 간격', '평균 마디 수', '최대 마디 수', '전수 조사 후보 수']]
    for n in (3, 5, 7, 9, 11, 13):
        rng = random.Random(1000 + n)
        gaps, nodes = [], []
        for _ in range(8):
            m = 3
            c = [-float(rng.randint(2, 9)) for _ in range(n)]
            A = [[float(rng.randint(1, 6)) for _ in range(n)] for _ in range(m)]
            b = [float(rng.randint(10, 25)) for _ in range(m)]
            rel = lp.solve_lp(c, A_ub=A, b_ub=b)
            r = milp.branch_and_bound(c, A_ub=A, b_ub=b, ub=[5.0] * n, maxnodes=200000)
            if r.obj is None or rel.obj is None:
                continue
            gaps.append(r.obj - rel.obj)
            nodes.append(r.nodes)
        rows.append(['%d' % n, '%.3f' % (sum(gaps) / len(gaps)),
                     '%.1f' % (sum(nodes) / float(len(nodes))), '%d' % max(nodes),
                     '%.1e' % (6.0 ** n)])
    print(fmt.table(rows, align='rrrrr'))
    print('  전수 조사 후보는 6^n 으로 폭발하지만(n=13 이면 1.3e10), 분지한정이 실제로')
    print('  펼치는 마디는 그보다 훨씬 적다. 그래도 n 이 커질수록 늘어난다 — 이것이')
    print('  NP-난해의 실물이다. 실무 솔버는 절단면·휴리스틱·전처리로 이 나무를 줄인다.')


def main():
    demo_gap()
    demo_tree()
    demo_growth()


if __name__ == '__main__':
    main()
