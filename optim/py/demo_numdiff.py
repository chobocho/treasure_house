# -*- coding: utf-8 -*-
"""1부 데모 — 수치미분의 최적 스텝은 이론이 말한 자리에 정말로 있다."""
import cmath
import math

from py import fmt
from py import funcs
from py import numdiff as nd


def demo_step_size():
    print('■ 1. 차분 스텝 h 를 바꿔 가며 오차를 잰다   f(x)=eˣ, x=0.7, f′=e^0.7')
    f = lambda x: math.exp(x[0])
    x, exact = [0.7], math.exp(0.7)
    rows = [['h', '전진차분 오차', '중심차분 오차', '이론(전진) h/2·f″+2ε/h', '이론(중심) h²/6·f‴+ε/h']]
    eps = nd.EPS
    for k in range(1, 15):
        h = 10.0 ** (-k)
        ef = abs((f([x[0] + h]) - f(x)) / h - exact)
        ec = abs((f([x[0] + h]) - f([x[0] - h])) / (2 * h) - exact)
        tf = h / 2 * exact + 2 * eps * exact / h
        tc = h * h / 6 * exact + eps * exact / h
        rows.append(['1e-%02d' % k, '%.3e' % ef, '%.3e' % ec, '%.3e' % tf, '%.3e' % tc])
    print(fmt.table(rows, align='rrrrr'))
    print('  이론 최적:  전진 h* = 2√ε ≈ %.2e,  중심 h* = (3ε)^(1/3) ≈ %.2e'
          % (2 * math.sqrt(eps), (3 * eps) ** (1 / 3.0)))
    print('  표에서 오차가 가장 작은 줄이 각각 그 근처다 — 유도가 맞았다는 뜻이다.\n')


def demo_complex_step():
    print('■ 2. 복소 스텝 — 뺄셈이 없으면 h 를 0 으로 보내도 된다')
    fz = lambda z: cmath.exp(z[0]) / (cmath.sqrt(cmath.sin(z[0]) ** 3 + cmath.cos(z[0]) ** 3))
    x = [1.5]
    # 해석적 미분값(손으로 유도해 둔 것)
    s, c = math.sin(1.5), math.cos(1.5)
    den = math.sqrt(s ** 3 + c ** 3)
    exact = math.exp(1.5) * (den - (3 * s ** 2 * c - 3 * c ** 2 * s) / (2 * den)) / (den ** 2)
    rows = [['h', '중심차분 오차', '복소 스텝 오차']]
    for k in (2, 4, 6, 8, 10, 20, 30):
        h = 10.0 ** (-k)
        fr = lambda t: (fz([complex(t[0], 0.0)])).real
        ec = abs((fr([x[0] + h]) - fr([x[0] - h])) / (2 * h) - exact)
        ecs = abs(nd.grad_complex(lambda z: fz(z), x, h)[0] - exact)
        rows.append(['1e-%02d' % k, '%.3e' % ec, '%.3e' % ecs])
    print(fmt.table(rows, align='rrr'))
    print('  중심차분은 h 를 줄일수록 상쇄로 망가지고, 복소 스텝은 끝까지 정확하다.')
    print('  조건: f 가 복소수를 그대로 받아 해석적으로 계산돼야 한다(abs·max 금지).\n')


def demo_grad_check():
    print('■ 3. 기울기 검사 — 손으로 유도한 ∇f 를 기계가 채점한다')
    rows = [['문제', '점', 'check_grad', 'check_hess', '판정']]
    cases = [(funcs.Rosenbrock(2), [-1.2, 1.0]),
             (funcs.Rosenbrock(5), [0.3, -0.4, 0.9, 0.2, -1.0]),
             (funcs.Himmelblau(), [1.0, -2.0]),
             (funcs.Beale(), [1.0, 0.5]),
             (funcs.LogisticRegression.toy(seed=7, n=200, d=4), [0.5, -0.3, 0.8, 0.1])]
    for p, x in cases:
        gerr = nd.check_grad(p.f, p.grad, x)
        herr = nd.check_hess(p.grad, p.hess, x)
        rows.append([p.name, '[%s]' % ', '.join('%.1f' % v for v in x),
                     '%.2e' % gerr, '%.2e' % herr,
                     '통과' if gerr < 1e-6 and herr < 1e-4 else '실패'])
    # 일부러 틀린 기울기를 넣어 본다 — 검사가 실제로 잡아내는지 보여야 의미가 있다
    p = funcs.Rosenbrock(2)
    wrong = lambda x: [g * 1.001 for g in p.grad(x)]        # 0.1% 만 틀리게
    rows.append(['rosenbrock(2) ← 0.1% 틀린 ∇f', '[-1.2, 1.0]',
                 '%.2e' % nd.check_grad(p.f, wrong, [-1.2, 1.0]), '—', '실패'])
    print(fmt.table(rows))
    print('  0.1% 오차도 잡힌다. 이 검사를 통과하지 못한 도함수는 교재에 싣지 않았다.')


def main():
    demo_step_size()
    demo_complex_step()
    demo_grad_check()


if __name__ == '__main__':
    main()
