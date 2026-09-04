# -*- coding: utf-8 -*-
"""4부 데모 — 같은 최소제곱 문제를 세 해법으로, 그리고 비선형으로 넘어간다."""
import math
import random

from py import fmt
from py import leastsq as ls
from py import linalg as la


def demo_three_solvers():
    print('■ 1. 세 해법의 정확도  (Lauchli 행렬, 정확해 x1 = 2/(2+eps^2))')
    rows = [['eps', 'cond(A)', 'cond(A^T A)', '정규방정식', 'QR', 'SVD']]
    for e in (1e-3, 1e-5, 1e-7, 1e-8, 1e-9):
        A = [[1.0, 1.0], [e, 0.0], [0.0, e]]
        b = [2.0, 0.0, 0.0]
        exact = 2.0 / (2.0 + e * e)
        def err(fn):
            try:
                return '%.2e' % abs(fn(A, b)[0] - exact)
            except la.SingularMatrix:
                return '특이'
        rows.append(['%.0e' % e, '%.1e' % la.cond(A),
                     '%.1e' % la.cond(la.matmul(la.transpose(A), A)),
                     err(ls.solve_normal), err(ls.solve_qr), err(ls.solve_svd)])
    print(fmt.table(rows, align='rrrrrr'))
    print('  eps=1e-3 에서 이미 정규방정식이 QR 보다 다섯 자리 나쁘고, eps>=1e-8 에서는')
    print('  1+eps^2 가 1 로 반올림되어 A^T A 가 아예 특이해진다 — 정보가 행렬을')
    print('  만드는 단계에서 사라진 것이다(정리 15.3). QR 과 SVD 는 끝까지 멀쩡하다.\n')


def demo_vandermonde():
    print('■ 2. 다항식 차수를 올리면 무슨 일이 생기는가  (구간 [0,1] 의 균등 격자 30점)')
    xs = [i / 29.0 for i in range(30)]
    ys = [math.sin(3.0 * x) + 0.5 * x for x in xs]
    rows = [['차수', 'cond(반데르몽드)', 'QR 잔차 norm', '정규방정식 잔차 norm', '판정']]
    for deg in (2, 4, 6, 8, 10, 12, 14):
        A = [[x ** k for k in range(deg + 1)] for x in xs]
        k = la.cond(A)
        cq = ls.solve_qr(A, ys)
        rq = la.norm(ls.residual(A, cq, ys))
        try:
            cn = ls.solve_normal(A, ys)
            rn = '%.3e' % la.norm(ls.residual(A, cn, ys))
        except la.SingularMatrix:
            rn = '특이'
        rows.append(['%d' % deg, '%.2e' % k, '%.3e' % rq, rn,
                     '안전' if k < 1e8 else ('주의' if k < 1e12 else '위험')])
    print(fmt.table(rows, align='rrrrl'))
    print('  차수를 2 올릴 때마다 조건수가 30배쯤 뛴다. 차수 12 부터는 정규방정식의')
    print('  잔차가 오히려 커지기 시작한다 — 더 좋은 모형인데 답이 더 나빠지는 것이다.')
    print('  실무에서 고차 다항식을 단항 기저로 맞추지 않고 직교다항식을 쓰는 이유다.\n')


def demo_ridge():
    print('■ 3. 릿지는 SVD 스펙트럼에 필터를 건다   필터 인자 s^2/(s^2 + lam)')
    A = [[3.0, 1.0, 0.2], [1.0, 2.0, 0.1], [0.0, 1.0, 0.05], [2.0, 0.5, 0.02]]
    b = [1.0, 2.0, 3.0, 1.5]
    U, s, V = la.svd(A)
    rows = [['lam', '||x||', '잔차 norm'] + ['필터 s%d=%.3f' % (i + 1, s[i]) for i in range(len(s))]]
    for lam in (0.0, 1e-4, 1e-2, 0.1, 1.0, 10.0):
        x = ls.ridge(A, b, lam)
        f = ['%.6f' % (v * v / (v * v + lam)) for v in s]
        rows.append(['%.0e' % lam if lam else '0', '%.4f' % la.norm(x),
                     '%.4f' % la.norm(ls.residual(A, x, b))] + f)
    print(fmt.table(rows, align='r' * (3 + len(s))))
    print('  큰 특잇값 방향은 거의 그대로 두고(필터 ~1), 작은 특잇값 방향만 눌린다.')
    print('  작은 s 방향이 곧 잡음에 민감한 방향이므로, 릿지는 "믿을 수 없는 방향을')
    print('  버리는" 연산이다. lam 이 커질수록 ||x|| 는 줄고 잔차는 늘어난다.\n')


def _exp_data(noise=0.0, seed=0):
    rng = random.Random(seed)
    ts = [0.25 * i for i in range(13)]
    ys = [2.5 * math.exp(-0.7 * t) + rng.gauss(0.0, noise) for t in ts]

    def resid(p):
        return [p[0] * math.exp(p[1] * t) - y for t, y in zip(ts, ys)]

    def jac(p):
        return [[math.exp(p[1] * t), p[0] * t * math.exp(p[1] * t)] for t in ts]
    return resid, jac


def demo_gn_vs_lm():
    print('■ 4. 가우스-뉴턴 vs Levenberg-Marquardt   모형 y = a exp(b t), 참값 (2.5, -0.7)')
    rows = [['출발점', '잡음', 'GN 반복', 'GN cost', 'GN ||J^T r||',
             'LM 반복', 'LM cost', 'LM ||J^T r||']]
    cases = [([2.0, -0.5], 0.0), ([1.0, -0.2], 0.0), ([0.05, 2.0], 0.0),
             ([5.0, 1.5], 0.0), ([1.0, -0.2], 0.05)]
    for x0, noise in cases:
        resid, jac = _exp_data(noise, seed=11)
        g = ls.gauss_newton(resid, jac, x0, tol=1e-10, maxiter=300)
        m = ls.levenberg_marquardt(resid, jac, x0, tol=1e-10, maxiter=300)
        gg = la.norm(la.matvec(la.transpose(jac(g.x)), resid(g.x)))
        mg = la.norm(la.matvec(la.transpose(jac(m.x)), resid(m.x)))
        rows.append(['(%.2f, %.2f)' % (x0[0], x0[1]), '%.2f' % noise,
                     '%d' % g.nit, '%.6e' % g.cost, '%.1e' % gg,
                     '%d' % m.nit, '%.6e' % m.cost, '%.1e' % mg])
    print(fmt.table(rows, align='lrrrrrrr'))
    print('  잡음이 없으면(잔차가 0 이면) 두 방법이 사실상 같다 — 2차 항을 버린')
    print('  근사가 정확하기 때문이다. 마지막 줄은 잡음이 있는 경우인데, 두 방법이')
    print('  같은 해(cost 가 소수 여섯 자리까지 같다)에 도달하지만 GN 은 ||J^T r|| 을')
    print('  1.7e-09 아래로 더 내리지 못하고 300회를 소진한다. 잔차가 0 이 아니면')
    print('  버린 2차 항이 남아 마지막 자릿수를 방해하는 것이다.\n')

    resid, jac = _exp_data(0.0, seed=11)
    r = ls.levenberg_marquardt(resid, jac, [0.05, 2.0], tol=1e-12, maxiter=300)
    rows = [['k', 'cost = 1/2||r||^2', '||J^T r||', 'lambda']]
    for h in r.history[:14]:
        rows.append(['%d' % h['k'], '%.6e' % h['cost'], '%.3e' % h['gnorm'], '%.1e' % h['lam']])
    print('  LM 의 lambda 가 어떻게 움직이는가 (출발점 (0.05, 2.0)):')
    print(fmt.table(rows, align='rrrr'))
    print('  실패한 걸음에서는 lambda 를 10배로 키워 조심스러워지고, 성공하면 10배로')
    print('  줄여 가우스-뉴턴에 가까워진다. 신뢰영역 반경의 역할을 감쇠가 대신한다.\n')


def demo_circle():
    print('■ 5. 원 맞추기 — 잔차가 파라미터에 비선형으로 들어가는 전형적인 예')
    cx, cy, r0 = 1.5, -0.5, 2.0
    rng = random.Random(4)
    pts = []
    for i in range(24):
        t = 2 * math.pi * i / 24.0
        pts.append((cx + r0 * math.cos(t) + rng.gauss(0, 0.02),
                    cy + r0 * math.sin(t) + rng.gauss(0, 0.02)))

    def resid(p):
        return [math.hypot(x - p[0], y - p[1]) - p[2] for x, y in pts]

    def jac(p):
        out = []
        for x, y in pts:
            d = math.hypot(x - p[0], y - p[1])
            out.append([-(x - p[0]) / d, -(y - p[1]) / d, -1.0])
        return out

    res = ls.levenberg_marquardt(resid, jac, [0.0, 0.0, 1.0], tol=1e-12, maxiter=300)
    rows = [['파라미터', '참값', '추정값', '오차']]
    for name, true, got in (('중심 x', cx, res.x[0]), ('중심 y', cy, res.x[1]),
                            ('반지름 r', r0, res.x[2])):
        rows.append([name, '%.4f' % true, '%.6f' % got, '%.2e' % abs(true - got)])
    print(fmt.table(rows, align='lrrr'))
    print('  잡음 표준편차 0.02, 점 24개. %d 회 반복, 최종 cost = %.6e'
          % (res.nit, res.cost))
    print('  점 하나의 잡음(0.02)보다 추정 오차가 작다 — 24개 점이 평균 효과를 내기 때문이다.')
    print('  잔차가 0 이 아닌 문제이므로 최종 cost 도 0 이 아니다. 그것이 정상이다.')


def main():
    demo_three_solvers()
    demo_vandermonde()
    demo_ridge()
    demo_gn_vs_lm()
    demo_circle()


if __name__ == '__main__':
    main()
