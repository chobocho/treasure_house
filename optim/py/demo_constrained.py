# -*- coding: utf-8 -*-
"""5부 데모 — 승수가 무엇인지, 페널티가 왜 부족한지, 쌍대 간격이 어떻게 닫히는지."""
import math

from py import constrained as cs
from py import convex as cx
from py import fmt
from py import linalg as la


def demo_multiplier_meaning():
    print('■ 1. 라그랑주 승수는 "제약을 한 단위 풀었을 때의 이득"이다')
    G = [[2.0, 0.5], [0.5, 4.0]]
    c = [1.0, -2.0]
    A = [[1.0, 2.0]]

    def val(bv):
        x, lam = cs.solve_eq_qp(G, c, A, [bv])
        return 0.5 * la.dot(x, la.matvec(G, x)) + la.dot(c, x), lam[0], x

    rows = [['b', '최적값 p*(b)', '승수 lam', '-dp*/db (수치미분)', '차이']]
    hstep = 1e-6
    for b in (1.0, 2.0, 3.0, 4.0, 5.0):
        p, lam, x = val(b)
        num = -(val(b + hstep)[0] - val(b - hstep)[0]) / (2 * hstep)
        rows.append(['%.1f' % b, '%.8f' % p, '%.8f' % lam, '%.8f' % num,
                     '%.2e' % abs(num - lam)])
    print(fmt.table(rows, align='rrrrr'))
    print('  승수가 최적값의 민감도와 소수점 여덟 자리까지 같다(정리 19.6).')
    print('  그래서 승수를 "그림자 가격(shadow price)"이라 부른다 — 제약을 완화할 때')
    print('  목적값이 얼마나 개선되는가를 그대로 말해 준다.\n')


def demo_kkt():
    print('■ 2. KKT 잔차 네 가지  min x^2 + y^2  s.t.  x + y >= 2')
    p = cs.Problem(f=lambda z: z[0] ** 2 + z[1] ** 2,
                   grad=lambda z: [2 * z[0], 2 * z[1]],
                   ineq=[lambda z: 2.0 - z[0] - z[1]],
                   ineq_grad=[lambda z: [-1.0, -1.0]])
    rows = [['후보 (x, y)', 'lam', '정류성', '원문제 실행가능', '쌍대 실행가능', '상보여유']]
    cands = [('참해 (1, 1)', [1.0, 1.0], [2.0]),
             ('승수 틀림', [1.0, 1.0], [0.5]),
             ('제약 위반 (0, 0)', [0.0, 0.0], [0.0]),
             ('내부점 (2, 2)', [2.0, 2.0], [0.0]),
             ('음의 승수', [1.0, 1.0], [-2.0])]
    for name, x, lam in cands:
        r = cs.kkt_residual(p, x, lam=lam)
        rows.append([name, '%.1f' % lam[0], '%.2e' % r['stationarity'],
                     '%.2e' % r['primal_feasibility'],
                     '%.2e' % r['dual_feasibility'],
                     '%.2e' % r['complementarity']])
    print(fmt.table(rows, align='lrrrrr'))
    print('  네 수가 모두 0 인 줄이 하나뿐이다. "수렴했다"를 말하려면 이 넷을 다 봐야 한다.')
    print('  내부점 (2,2) 는 제약을 만족하지만 정류성이 깨진다 — 최적이 아니다.\n')


def demo_methods():
    print('■ 3. 같은 문제, 세 가지 접근   min (x-3)^2 + (y+2)^2  s.t.  -1 <= x, y <= 1')
    f = lambda z: (z[0] - 3.0) ** 2 + (z[1] + 2.0) ** 2
    g = lambda z: [2 * (z[0] - 3.0), 2 * (z[1] + 2.0)]
    star = [1.0, -1.0]

    r1 = cs.projected_gradient(f, g, lambda z: cx.proj_box(z, -1.0, 1.0),
                               [0.0, 0.0], step=0.2, tol=1e-14, maxiter=5000)
    rows = [['방법', '하위문제 반복', '해', '오차', '실행가능?']]
    rows.append(['투영경사', '%d' % r1.nit, '(%.6f, %.6f)' % tuple(r1.x),
                 '%.2e' % la.norm(la.vsub(r1.x, star)), '항상'])

    # 부등식을 등식으로 바꿔 페널티/AL 을 적용한다(활성 제약을 안다고 가정)
    h = lambda z: [z[0] - 1.0, z[1] + 1.0]
    hj = lambda z: [[1.0, 0.0], [0.0, 1.0]]
    for name, fn, kw in (('페널티 mu=1e2', cs.penalty_method, dict(mu0=1e2, growth=1.0, outer=1)),
                         ('페널티 mu=1e4', cs.penalty_method, dict(mu0=1e4, growth=1.0, outer=1)),
                         ('페널티 mu=1e6', cs.penalty_method, dict(mu0=1e6, growth=1.0, outer=1)),
                         ('증강 라그랑주 mu=1e2', cs.augmented_lagrangian,
                          dict(mu0=1e2, growth=1.0, outer=20))):
        r = fn(f, g, h, hj, [0.0, 0.0], tol=1e-13, maxiter=4000, **kw)
        viol = max(abs(v) for v in h(r.x))
        rows.append([name, '%d' % r.inner, '(%.6f, %.6f)' % tuple(r.x),
                     '%.2e' % la.norm(la.vsub(r.x, star)),
                     '위반 %.1e' % viol])
    print(fmt.table(rows, align='lrlrl'))
    print('  페널티는 mu 를 100배 키울 때마다 오차가 100배 줄지만 결코 0 이 되지 않는다.')
    print('  같은 mu=1e2 에서 증강 라그랑주는 승수를 따로 추정해 정확히 도달한다.\n')


def demo_penalty_conditioning():
    print('■ 4. 페널티의 대가 — 벌을 키우면 하위 문제가 병조건화된다')
    print('  min x^2 + y^2  s.t.  x + y = 2.  페널티 목적은 정확히 이차함수이고')
    print('  헤세는 2I + mu*[[1,1],[1,1]], 고윳값은 2 와 2+2mu 다.')
    rows = [['mu', 'L = 2+2mu', 'mu_c = 2', 'kappa', '해의 오차 |x-1|',
             '경사하강 반복(실측)', '이론값 kappa*ln(1e6)/2']]
    f = lambda z: z[0] ** 2 + z[1] ** 2
    h = lambda z: [z[0] + z[1] - 2.0]
    for mu in (1.0, 10.0, 100.0, 1000.0, 10000.0):
        L, mc = 2.0 + 2.0 * mu, 2.0
        kappa = L / mc
        # 페널티 최소점: s = 2mu/(1+mu), x = y = s/2
        xs = mu / (1.0 + mu)
        star = [xs, xs]
        step = 2.0 / (L + mc)                       # 정리 9.7 의 최적 보폭
        x = [0.0, 0.0]
        e0 = la.norm(la.vsub(x, star))
        k = 0
        while la.norm(la.vsub(x, star)) > 1e-6 * e0 and k < 2000000:
            g = [2 * x[0] + mu * (x[0] + x[1] - 2.0),
                 2 * x[1] + mu * (x[0] + x[1] - 2.0)]
            x = la.axpy(-step, g, x)
            k += 1
        theory = kappa * math.log(1e6) / 2.0
        rows.append(['%.0e' % mu, '%.0f' % L, '%.0f' % mc, '%.1f' % kappa,
                     '%.2e' % abs(xs - 1.0), '%d' % k, '%.0f' % theory])
    print(fmt.table(rows, align='rrrrrrr'))
    print('  해의 오차는 mu 에 반비례해 줄고(1/(1+mu)), 그 대가로 조건수가 mu 에')
    print('  비례해 커져 경사하강 반복 수가 그만큼 늘어난다. 실측(69085)과')
    print('  이론값(69084)이 한 걸음 차이로 일치한다 — 3부 따름정리 9.6 의 확인이다.')
    print('  정확도를 계산량으로 사는 구조이고, 증강 라그랑주는 그 거래 자체를 없앤다.\n')


def demo_duality():
    print('■ 5. 쌍대 간격이 닫히는 모습   min 1/2||x||^2  s.t.  a^T x >= 1,  a = (3, 4)')
    a = [3.0, 4.0]
    na2 = la.dot(a, a)
    primal = 0.5 / na2
    rows = [['nu', '쌍대값 g(nu)', '원문제 최적값 p*', '쌍대 간격', '비고']]
    best = -1e300
    for nu in (0.0, 0.005, 0.01, 0.02, 1.0 / na2, 0.06, 0.1, 0.2):
        dual = nu - 0.5 * nu * nu * na2
        best = max(best, dual)
        note = '<- 최대 (nu* = 1/||a||^2)' if abs(nu - 1.0 / na2) < 1e-12 else ''
        rows.append(['%.4f' % nu, '%.8f' % dual, '%.8f' % primal,
                     '%.8f' % (primal - dual), note])
    print(fmt.table(rows, align='rrrrl'))
    print('  모든 nu >= 0 에서 g(nu) <= p* 다 — 약쌍대성(정리 21.2). 그리고 최댓값에서')
    print('  간격이 정확히 0 이 된다 — Slater 조건이 성립하므로 강쌍대성(정리 21.6).')
    print('  쌍대값은 언제나 하한이므로, 알고리즘의 정지 기준으로 쓸 수 있다.\n')


def demo_barrier():
    print('■ 6. 로그 배리어의 중심 경로   min (x-3)^2  s.t.  x <= 1')
    f = lambda z: (z[0] - 3.0) ** 2
    g = lambda z: [2.0 * (z[0] - 3.0)]
    gs = [lambda z: z[0] - 1.0]
    gj = [lambda z: [1.0]]
    rows = [['t', 'x*(t)', '최적해와의 차이', '보장 간격 m/t', '실제 간격 f(x)-f*']]
    fstar = f([1.0])
    for t in (1.0, 10.0, 100.0, 1e3, 1e4, 1e5):
        r = cs.log_barrier(f, g, gs, gj, [0.0], t0=t, mu=1.0, outer=1,
                           tol=1e-14, maxiter=3000)
        rows.append(['%.0e' % t, '%.10f' % r.x[0], '%.2e' % abs(r.x[0] - 1.0),
                     '%.2e' % (1.0 / t), '%.2e' % (f(r.x) - fstar)])
    print(fmt.table(rows, align='rrrrr'))
    print('  t 를 키우면 해가 경계 x=1 에 정확히 다가간다. 간격이 m/t 로 보장되므로')
    print('  "얼마나 더 가야 하는가"를 계산 없이 안다 — 6부 내부점법의 핵심이다.')


def main():
    demo_multiplier_meaning()
    demo_kkt()
    demo_methods()
    demo_penalty_conditioning()
    demo_duality()
    demo_barrier()


if __name__ == '__main__':
    main()
