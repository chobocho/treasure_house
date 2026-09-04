# -*- coding: utf-8 -*-
"""7부 데모 — 고모리 절단이 하한을 어떻게 끌어올리는가."""
from py import fmt
from py import lp
from py import milp


C = [-5.0, -4.0]
A = [[6.0, 4.0], [1.0, 2.0]]
B = [24.0, 6.0]


def demo_rounds():
    print('■ 1. 절단을 붙일수록 하한이 정수 최적값에 다가간다')
    print('  max 5x + 4y  s.t.  6x + 4y <= 24,  x + 2y <= 6,  x, y >= 0 정수')
    exact = milp.branch_and_bound(C, A_ub=A, b_ub=B)
    r, cuts, bounds = milp.gomory_cuts(C, A, B, rounds=8)
    rows = [['라운드', '누적 절단 수', 'LP 하한(최소화)', '최대화로 읽으면',
             '정수 최적과의 간격']]
    for k, (bd, nc) in enumerate(bounds):
        rows.append(['%d' % k, '%d' % nc, '%.6f' % bd, '%.6f' % (-bd),
                     '%.6f' % (exact.obj - bd)])
    print(fmt.table(rows, align='rrrrr'))
    print('  정수 최적값은 %.1f (최대화로 %.1f), 초기 LP 하한은 %.4f 였다.'
          % (exact.obj, -exact.obj, bounds[0][0]))
    print('  절단은 정수해를 하나도 잘라 내지 않으면서 분수해만 도려낸다.\n')


def demo_cut_shape():
    print('■ 2. 만들어진 절단은 어떤 부등식인가')
    rel = lp.solve_lp(C, A_ub=A, b_ub=B)
    r, cuts, bounds = milp.gomory_cuts(C, A, B, rounds=3)
    print('  LP 완화 최적해: x = (%.4f, %.4f)' % (rel.x[0], rel.x[1]))
    rows = [['#', '절단 부등식', '현재 LP 해에서의 좌변', '우변', '잘리는가']]
    for k, (row, rb) in enumerate(cuts[:6]):
        lhs = row[0] * rel.x[0] + row[1] * rel.x[1]
        rows.append(['%d' % (k + 1),
                     '%.4f x + %.4f y <= %.4f' % (row[0], row[1], rb),
                     '%.6f' % lhs, '%.6f' % rb,
                     '예' if lhs > rb + 1e-9 else '아니오'])
    print(fmt.table(rows, align='rlrrl'))
    print('  첫 절단은 반드시 현재 분수해를 자른다 — 비기저 변수가 모두 0 이라')
    print('  좌변이 0 인데 우변(frac(b)) 이 양수이기 때문이다.\n')


def demo_all_integer_points_survive():
    print('■ 3. 정수해는 하나도 잘리지 않는다 — 전수 확인')
    _, cuts, _ = milp.gomory_cuts(C, A, B, rounds=5)
    pts = [(x, y) for x in range(0, 5) for y in range(0, 4)
           if 6 * x + 4 * y <= 24 and x + 2 * y <= 6]
    rows = [['정수해 (x, y)', '5x+4y', '모든 절단 만족?', '가장 빡빡한 여유']]
    for (x, y) in pts:
        slacks = [cuts[k][1] - (cuts[k][0][0] * x + cuts[k][0][1] * y)
                  for k in range(len(cuts))]
        ok = all(v > -1e-7 for v in slacks)
        rows.append(['(%d, %d)' % (x, y), '%d' % (5 * x + 4 * y),
                     '예' if ok else '아니오',
                     ('%.4f' % (min(slacks) + 0.0)) if slacks else '-'])
    print(fmt.table(rows, align='lrlr'))
    print('  실행가능한 정수해 %d개가 모두 살아남았다. 절단면법이 "정확한" 방법인' % len(pts))
    print('  이유가 이것이다 — 근사가 아니라 "같은 정수 문제"를 더 조인 것이다.')
    print('  실무의 branch-and-cut 은 분지 나무의 각 마디에서 이 절단을 함께 쓴다.')


def main():
    demo_rounds()
    demo_cut_shape()
    demo_all_integer_points_survive()


if __name__ == '__main__':
    main()
