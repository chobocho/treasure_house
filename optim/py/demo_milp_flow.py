# -*- coding: utf-8 -*-
"""7부 데모 — 최소비용흐름과 정수성."""
from py import fmt
from py import lp
from py import milp


NET = [
    # (출발, 도착, 용량, 단위비용)
    (0, 1, 4, 2), (0, 2, 3, 3), (1, 2, 2, 1),
    (1, 3, 3, 2), (2, 3, 4, 1), (2, 4, 2, 4), (3, 4, 5, 1),
]
NV = 5


def demo_network():
    print('■ 1. 최소비용흐름 — 5개 노드, 7개 간선, 0 -> 4 로 4단위')
    rows = [['간선', '용량', '단위비용', '보낸 유량', '든 비용']]
    cost, flow = milp.min_cost_flow(NV, NET, 0, 4, 4)
    for k, (u, v, cap, c) in enumerate(NET):
        rows.append(['%d -> %d' % (u, v), '%d' % cap, '%d' % c,
                     '%d' % flow[k], '%d' % (flow[k] * c)])
    rows.append(['합계', '', '', '', '%d' % cost])
    print(fmt.table(rows, align='lrrrr'))
    print('  연속 최단경로법은 매번 "가장 싼 증가 경로"를 찾아 채운다.')
    print('  잔여망에 음수 비용 간선이 생기므로 Bellman-Ford 로 최단경로를 구한다.')
    print('  최적성의 근거: 남은 흐름에 음수 비용 순환이 없다는 것 — 상보여유의 그래프판이다.\n')


def demo_integrality():
    print('■ 2. 같은 문제를 LP 로 — 정수 제약 없이도 정수해가 나온다')
    ne = len(NET)
    A_eq, b_eq = [], []
    for v in range(1, NV - 1):                      # 중간 노드의 유량 보존
        row = [0.0] * ne
        for k, (a, b_, cap, c) in enumerate(NET):
            if a == v:
                row[k] += 1.0
            if b_ == v:
                row[k] -= 1.0
        A_eq.append(row); b_eq.append(0.0)
    row = [0.0] * ne                                 # 출발 노드에서 4단위 나간다
    for k, (a, b_, cap, c) in enumerate(NET):
        if a == 0:
            row[k] += 1.0
        if b_ == 0:
            row[k] -= 1.0
    A_eq.append(row); b_eq.append(4.0)
    A_ub = [[1.0 if j == k else 0.0 for j in range(ne)] for k in range(ne)]
    b_ub = [float(e[2]) for e in NET]
    r = lp.solve_lp([float(e[3]) for e in NET], A_ub=A_ub, b_ub=b_ub,
                    A_eq=A_eq, b_eq=b_eq)
    cost, flow = milp.min_cost_flow(NV, NET, 0, 4, 4)
    rows = [['간선', 'LP 해', '흐름 알고리즘', '정수인가']]
    for k, (u, v, cap, c) in enumerate(NET):
        rows.append(['%d -> %d' % (u, v), '%.6f' % r.x[k], '%d' % flow[k],
                     '예' if abs(r.x[k] - round(r.x[k])) < 1e-7 else '아니오'])
    print(fmt.table(rows, align='lrrl'))
    print('  LP 최적값 %.4f, 흐름 알고리즘 %d — 같다.' % (r.obj, cost))
    print('  흐름 문제의 제약행렬(노드-간선 접속행렬)은 완전단모듈이라,')
    print('  우변이 정수이면 LP 의 꼭짓점이 자동으로 정수가 된다(정리 30.3).\n')


def demo_bottleneck():
    print('■ 3. 용량을 늘리면 어디가 이득인가 — 그림자 가격의 그래프판  (수요 6단위)')
    need = 6
    base, _ = milp.min_cost_flow(NV, NET, 0, 4, need)
    rows = [['용량을 +1 한 간선', '새 최소비용', '절감액', '병목인가']]
    for k, (u, v, cap, c) in enumerate(NET):
        mod = list(NET)
        mod[k] = (u, v, cap + 1, c)
        try:
            new, _ = milp.min_cost_flow(NV, mod, 0, 4, need)
        except ValueError:
            new = None
        if new is None:
            rows.append(['%d -> %d' % (u, v), '-', '-', '-'])
        else:
            rows.append(['%d -> %d' % (u, v), '%d' % new, '%d' % (base - new),
                         '예' if base - new > 0 else '아니오'])
    print(fmt.table(rows, align='lrrl'))
    print('  기준 비용 %d. 대부분의 간선은 용량을 늘려도 아무 이득이 없다 —' % base)
    print('  여유가 남아 있기 때문이다(상보여유). 3 -> 4 만 절감이 생기는데,')
    print('  그 간선이 이 수요 수준에서의 병목이라는 뜻이다.')
    print('  수요를 4 나 5 로 낮추면 병목이 아예 사라진다 — 병목은 문제에 고정된')
    print('  성질이 아니라 부하 수준에 따라 옮겨 다니는 것이다.')
    print('  이 실험이 곧 5부 정리 19.8(승수 = 민감도)의 조합적 버전이다.')
    print('  12부에서 프로세스의 병목을 찾을 때 정확히 같은 사고를 쓴다.')


def main():
    demo_network()
    demo_integrality()
    demo_bottleneck()


if __name__ == '__main__':
    main()
