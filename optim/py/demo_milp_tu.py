# -*- coding: utf-8 -*-
"""7부 데모 — 완전단모듈성: 어떤 정수 문제가 왜 쉬운가."""
import random

from py import fmt
from py import lp
from py import milp


def demo_tu_check():
    print('■ 1. 완전단모듈(TU) 인가 — 정의 그대로 확인한다')
    cases = [
        ('단위행렬 I2', [[1, 0], [0, 1]]),
        ('구간 행렬 (연속 1)', [[1, 1, 0], [0, 1, 1]]),
        ('이분그래프 접속행렬', [[1, 1, 0, 0], [0, 0, 1, 1], [1, 0, 1, 0], [0, 1, 0, 1]]),
        ('유향그래프 접속행렬', [[1, 1, 0], [-1, 0, 1], [0, -1, -1]]),
        ('홀수 순환 (3-cycle)', [[1, 1, 0], [0, 1, 1], [1, 0, 1]]),
        ('2 가 들어간 행렬', [[2, 1], [1, 1]]),
    ]
    rows = [['행렬', '크기', 'TU 인가', '뜻']]
    for name, A in cases:
        tu = milp.is_totally_unimodular(A)
        rows.append([name, '%dx%d' % (len(A), len(A[0])), '예' if tu else '아니오',
                     '정수 우변이면 LP 꼭짓점이 정수' if tu else '정수성 보장 없음'])
    print(fmt.table(rows))
    print('  홀수 순환이 TU 가 아닌 것이 결정적이다 — 그래서 이분그래프 매칭은 쉽고')
    print('  일반 그래프 매칭은 LP 만으로는 풀리지 않는다(홀수 집합 부등식이 더 필요하다).\n')


def demo_why_matters():
    print('■ 2. TU 이면 정수 제약이 공짜다 — 수송 문제로 확인')
    sup, dem = [30.0, 50.0, 20.0], [40.0, 25.0, 35.0]
    cost = [[4.0, 6.0, 9.0], [5.0, 3.0, 8.0], [7.0, 8.0, 2.0]]
    m, n = 3, 3
    A_eq, b_eq = [], []
    for i in range(m):
        row = [0.0] * (m * n)
        for j in range(n):
            row[i * n + j] = 1.0
        A_eq.append(row); b_eq.append(sup[i])
    for j in range(n):
        row = [0.0] * (m * n)
        for i in range(m):
            row[i * n + j] = 1.0
        A_eq.append(row); b_eq.append(dem[j])
    c = [cost[i][j] for i in range(m) for j in range(n)]
    r = lp.solve_lp(c, A_eq=A_eq, b_eq=b_eq)
    rows = [['공급지 \\ 수요지', 'D1', 'D2', 'D3', '합계', '공급량']]
    for i in range(m):
        vals = [r.x[i * n + j] for j in range(n)]
        rows.append(['S%d' % (i + 1)] + ['%.0f' % v for v in vals] +
                    ['%.0f' % sum(vals), '%.0f' % sup[i]])
    rows.append(['합계'] + ['%.0f' % sum(r.x[i * n + j] for i in range(m)) for j in range(n)]
                + ['%.0f' % sum(r.x), ''])
    rows.append(['수요량'] + ['%.0f' % v for v in dem] + ['', ''])
    print(fmt.table(rows, align='lrrrrr'))
    frac = sum(1 for v in r.x if abs(v - round(v)) > 1e-7)
    print('  총비용 %.1f,  분수인 성분 %d 개 — LP 만 풀었는데 전부 정수다.' % (r.obj, frac))
    print('  제약행렬이 TU 이고 우변(공급·수요)이 정수이기 때문이다.\n')


def demo_tu_vs_not():
    print('■ 3. TU 가 아니면 어떻게 되는가 — 같은 크기의 두 문제 비교')
    rng = random.Random(21)
    rows = [['문제', 'LP 완화', '정수 최적', '간격', 'B&B 마디 수']]
    # (a) 할당 문제 — TU
    n = 4
    C = [[rng.randint(1, 20) for _ in range(n)] for _ in range(n)]
    A_eq, b_eq = [], []
    for i in range(n):
        row = [0.0] * (n * n)
        for j in range(n):
            row[i * n + j] = 1.0
        A_eq.append(row); b_eq.append(1.0)
    for j in range(n):
        row = [0.0] * (n * n)
        for i in range(n):
            row[i * n + j] = 1.0
        A_eq.append(row); b_eq.append(1.0)
    c = [float(C[i][j]) for i in range(n) for j in range(n)]
    rel = lp.solve_lp(c, A_eq=A_eq, b_eq=b_eq)
    hc, _ = milp.hungarian(C)
    rows.append(['할당 (TU)', '%.3f' % rel.obj, '%d' % hc,
                 '%.3f' % (hc - rel.obj), '0 (완화가 곧 답)'])
    # (b) 일반 배낭형 — TU 아님
    c2 = [-8.0, -11.0, -6.0, -4.0]
    A2 = [[5.0, 7.0, 4.0, 3.0]]
    b2 = [14.0]
    rel2 = lp.solve_lp(c2, A_ub=A2, b_ub=b2, A_eq=None,
                       b_eq=None)
    r2 = milp.branch_and_bound(c2, A_ub=A2 + [[1.0 if j == k else 0.0 for j in range(4)]
                                              for k in range(4)],
                               b_ub=b2 + [1.0] * 4)
    rows.append(['0/1 배낭 (TU 아님)', '%.3f' % rel2.obj, '%.3f' % r2.obj,
                 '%.3f' % (r2.obj - rel2.obj), '%d' % r2.nodes])
    print(fmt.table(rows, align='lrrrr'))
    print('  TU 문제는 완화를 푸는 순간 끝난다. 아닌 문제는 간격이 생기고, 그 간격을')
    print('  좁히려고 분지·절단면·휴리스틱이 필요해진다.')
    print('  "정수 제약이 비싼가"는 문제의 구조가 결정한다 — 변수 개수가 아니다.')


def main():
    demo_tu_check()
    demo_why_matters()
    demo_tu_vs_not()


if __name__ == '__main__':
    main()
