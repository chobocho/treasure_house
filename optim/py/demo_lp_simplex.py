# -*- coding: utf-8 -*-
"""6부 데모 — 심플렉스의 발자국"""
import itertools
import math
import random

from py import fmt
from py import linalg as la
from py import lp


PROB = dict(
    c=[-3.0, -5.0],
    A=[[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]],
    b=[4.0, 12.0, 18.0],
)


def demo_simplex_steps():
    print('■ 2. 심플렉스의 발자국  (표준형 변수: x1 x2, 슬랙 s1 s2 s3)')
    r = lp.solve_lp(PROB['c'], A_ub=PROB['A'], b_ub=PROB['b'], keep_history=True)
    names = ['x1', 'x2', 's1', 's2', 's3']
    rows = [['단계', '기저', '목적값(최소화)', '들어오는 열', '나가는 열', '축소비용 (x1, x2)']]
    for h in r.history:
        rows.append(['%d' % h['k'],
                     '{%s}' % ', '.join(names[i] for i in sorted(h['basis'])),
                     '%.4f' % (h['obj'] + 0.0),
                     names[h['enter']] if h['enter'] is not None else '-',
                     names[h['leave']] if h['leave'] is not None else '-',
                     '%.3f, %.3f' % (h['rc'][0], h['rc'][1])])
    print(fmt.table(rows, align='rlrlll'))
    print('  기저가 바뀔 때마다 다른 꼭짓점으로 옮겨 간다. 축소비용이 모두 0 이상이')
    print('  되는 순간이 최적이다 — 어느 방향으로도 더 내려갈 수 없다는 뜻이다.')
    print('  최적해 x = (%.2f, %.2f), 최적값 %.2f (최대화로는 %.2f)\n'
          % (r.x[0], r.x[1], r.obj, -r.obj))


def main():
    demo_simplex_steps()


if __name__ == '__main__':
    main()
