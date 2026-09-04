# -*- coding: utf-8 -*-
"""1부 데모 — 선형대수가 최적화에서 하는 일을 눈으로 본다."""
import math

from py import fmt
from py import funcs
from py import linalg as la


def demo_condition():
    print('■ 1. 조건수가 커지면 유효숫자를 잃는다   (힐베르트 행렬 Hᵢⱼ = 1/(i+j−1))')
    rows = [['n', '조건수 κ₂(H)', '‖x̂ − 1‖∞', '잃은 자릿수', 'log₁₀κ']]
    for n in (3, 5, 8, 10, 12):
        H = [[1.0 / (i + j + 1) for j in range(n)] for i in range(n)]
        b = la.matvec(H, [1.0] * n)
        x = la.solve(H, b)
        err = max(abs(v - 1.0) for v in x)
        k = la.cond(H)
        lost = 0.0 if err == 0 else math.log10(err / 2.220446049250313e-16)
        rows.append(['%d' % n, '%.3e' % k, '%.3e' % err, '%.1f' % lost, '%.1f' % math.log10(k)])
    print(fmt.table(rows, align='rrrrr'))
    print('  → 잃은 자릿수가 log₁₀κ 를 따라간다. 오차 한계 ‖Δx‖/‖x‖ ≲ κ·ε 의 실측이다.\n')


def demo_normal_vs_qr():
    print('■ 2. 정규방정식 vs QR — 같은 최소제곱 문제, 다른 운명   (Läuchli 행렬)')
    rows = [['ε', 'κ₂(A)', 'κ₂(AᵀA)', '정규방정식 x₁', 'QR x₁']]
    for e in (1e-4, 1e-6, 1e-8, 1e-9):
        A = [[1.0, 1.0], [e, 0.0], [0.0, e]]
        b = [2.0, 0.0, 0.0]
        exact = 2.0 / (2.0 + e * e)
        AtA = la.matmul(la.transpose(A), A)
        Atb = la.matvec(la.transpose(A), b)
        try:
            ne = '%.12f' % la.solve(AtA, Atb)[0]
        except la.SingularMatrix:
            ne = '특이 — 풀지 못함'
        qr = la.lstsq(A, b)[0]
        rows.append(['%.0e' % e, '%.2e' % la.cond(A), '%.2e' % la.cond(AtA),
                     ne, '%.12f' % qr])
    print(fmt.table(rows, align='rrrrr'))
    print('  정확해 x₁ = 2/(2+ε²) ≈ 1.  ε=1e-9 면 1+ε² 가 반올림돼 AᵀA 의 두 행이')
    print('  똑같아진다 — 정보가 행렬을 만드는 단계에서 이미 사라졌다. QR 은 멀쩡하다.\n')


def demo_cholesky_as_test():
    print('■ 3. 촐레스키는 2차 최적성 조건을 공짜로 검사해 준다')
    r = funcs.Rosenbrock(2)
    rows = [['점', '고윳값 λ₁, λ₂', '양의 정부호?', '뜻']]
    for label, x in (('(1, 1) 최소점', [1.0, 1.0]),
                     ('(0, 1)', [0.0, 1.0]),
                     ('(−1.2, 1) 출발점', [-1.2, 1.0])):
        H = r.hess(x)
        vals, _ = la.eigh(H)
        # 판정 문구를 손으로 적지 않는다 — 고윳값 부호에서 그대로 만들어 낸다.
        pd = la.is_pos_def(H)
        mean = ('아래로 볼록 — 뉴턴 방향이 하강 방향임이 보장된다' if pd
                else '부정부호 — 뉴턴 방향이 오르막일 수 있어 수정이 필요하다')
        rows.append([label, '%.4g, %.4g' % (vals[0], vals[1]),
                     '예' if pd else '아니오', mean])
    print(fmt.table(rows))
    H = r.hess([1.0, 1.0])
    print('  최소점에서 κ₂(∇²f) = %.1f — 3부에서 경사하강이 (κ−1)/(κ+1) 비율로'
          % la.cond(H))
    print('  느려진다는 것을 증명한다. 여기서는 그 수가 %.5f 이다.\n'
          % ((la.cond(H) - 1) / (la.cond(H) + 1)))


def demo_svd():
    print('■ 4. SVD — 어떤 행렬이든 회전·늘이기·회전으로 쪼갠다')
    A = [[3.0, 1.0], [1.0, 3.0], [0.0, 2.0]]
    U, s, V = la.svd(A)
    print('  A = ' + str(A))
    print('  특잇값 σ = [%s]' % ', '.join('%.6f' % v for v in s))
    R = la.matmul(la.matmul(U, la.diag(s)), la.transpose(V))
    err = max(abs(R[i][j] - A[i][j]) for i in range(3) for j in range(2))
    print('  ‖UΣVᵀ − A‖∞ = %.2e,  κ₂(A) = σ₁/σ₂ = %.6f' % (err, s[0] / s[-1]))
    print('  UᵀU = I 확인: 대각 %.12f, 비대각 %.2e'
          % (la.matmul(la.transpose(U), U)[0][0],
             abs(la.matmul(la.transpose(U), U)[0][1])))


def main():
    demo_condition()
    demo_normal_vs_qr()
    demo_cholesky_as_test()
    demo_svd()


if __name__ == '__main__':
    main()
