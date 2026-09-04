# -*- coding: utf-8 -*-
"""3부 데모 — 미분을 얻는 네 가지 방법을 나란히 놓고 잰다."""
import math
import time

from py import autodiff as ad
from py import fmt
from py import funcs
from py import linalg as la
from py import numdiff as nd


def demo_accuracy():
    print('■ 1. 같은 기울기를 네 가지 방법으로  (로젠브록 4차원, x = [0.3, -0.7, 1.4, 0.2])')
    p = funcs.Rosenbrock(4)
    x = [0.3, -0.7, 1.4, 0.2]
    exact = p.grad(x)
    rows = [['방법', 'g[0]', '오차 ||g - g_exact||', 'f 평가 횟수', '비고']]
    rows.append(['해석적 (손으로 유도)', '%.12f' % exact[0], '0', '0', '기준'])
    for name, g, ncall, note in (
            ('전진차분', nd.grad_forward(p.f, x), len(x) + 1, 'O(h) 절단오차'),
            ('중심차분', nd.grad(p.f, x), 2 * len(x), 'O(h^2) 절단오차'),
            ('자동미분 전방', ad.grad_forward(p.f, x), len(x), '절단오차 없음'),
            ('자동미분 역방', ad.grad_reverse(p.f, x), 1, '절단오차 없음')):
        rows.append([name, '%.12f' % g[0], '%.3e' % la.norm(la.vsub(g, exact)),
                     '%d' % ncall, note])
    print(fmt.table(rows, align='lrrrl'))
    print('  자동미분의 오차 1e-13 은 절단오차가 아니라 덧셈 순서가 달라 생긴 반올림')
    print('  차이다(해석적 구현은 math.fsum 을, 자동미분은 보통 덧셈을 쓴다).')
    print('  수치미분의 1e-5 ~ 1e-8 은 성격이 다르다 — h 를 아무리 잘 골라도 남는')
    print('  절단오차이고, 1부 정리 4.1 이 그 한계를 예측한 그대로다.\n')


def demo_cost():
    print('■ 2. 비용 구조가 정반대다  (로젠브록 n 차원, 기울기 한 번)')
    rows = [['n', '전방 AD (초)', '역방 AD (초)', '전방/역방', '전방 f 평가', '역방 f 평가']]
    for n in (4, 16, 64, 256):
        p = funcs.Rosenbrock(n)
        x = [0.3 + 0.01 * i for i in range(n)]
        t0 = time.time(); ad.grad_forward(p.f, x); tf = time.time() - t0
        t0 = time.time(); ad.grad_reverse(p.f, x); tr = time.time() - t0
        rows.append(['%d' % n, '%.4f' % tf, '%.4f' % tr, '%.1f' % (tf / max(tr, 1e-9)),
                     '%d' % n, '1'])
    print(fmt.table(rows, align='rrrrrr'))
    print('  전방은 입력 변수 하나마다 한 번씩 훑으므로 n 에 비례해 느려진다.')
    print('  역방은 몇 개든 한 번이면 된다 — 신경망 학습이 가능한 이유가 이것이다.')
    print('  대신 역방은 계산 그래프를 통째로 들고 있어야 해서 메모리를 더 쓴다.\n')


def demo_dual_trace():
    print('■ 3. 이중수는 무엇을 들고 다니는가   f(x) = exp(x) / (1 + x^2),  x = 0.5')
    x = ad.Dual(0.5, 1.0)                       # 실수부 = 값, ε 부 = dx/dx = 1
    t1 = ad.exp(x)
    t2 = x ** 2
    t3 = 1.0 + t2
    t4 = t1 / t3
    exact = math.exp(0.5) * (1 - 2 * 0.5 / (1 + 0.25)) / (1 + 0.25)
    rows = [['단계', '실수부 (값)', 'ε 부 (도함수)', '적용된 규칙']]
    rows.append(['x', '%.10f' % x.a, '%.10f' % x.b, '씨앗 dx/dx = 1'])
    rows.append(['t1 = exp(x)', '%.10f' % t1.a, '%.10f' % t1.b, "(e^u)' = e^u u'"])
    rows.append(['t2 = x^2', '%.10f' % t2.a, '%.10f' % t2.b, "(u^k)' = k u^(k-1) u'"])
    rows.append(['t3 = 1 + t2', '%.10f' % t3.a, '%.10f' % t3.b, "(u+v)' = u' + v'"])
    rows.append(['t4 = t1 / t3', '%.10f' % t4.a, '%.10f' % t4.b, "(u/v)' = (u'v - uv')/v^2"])
    print(fmt.table(rows, align='lrrl'))
    print('  손으로 유도한 도함수 = %.10f  → 마지막 줄의 ε 부와 자릿수까지 같다.' % exact)
    print('  이중수는 값과 도함수를 나란히 들고 다닐 뿐이고, 연산자 오버로딩이')
    print('  연쇄법칙을 대신 적용해 준다. 이것이 자동미분의 전부다.')


def main():
    demo_accuracy()
    demo_cost()
    demo_dual_trace()


if __name__ == '__main__':
    main()
