# -*- coding: utf-8 -*-
"""선형계획 — 심플렉스와 내부점이 같은 답을 주는가, 쌍대 정리가 성립하는가."""
import unittest

from py import linalg as la
from py import lp


class TestSimplexBasics(unittest.TestCase):
    def test_tiny_max(self):
        # max 3x + 2y  s.t. x+y<=4, x+3y<=6, x,y>=0  → (4,0), 값 12
        r = lp.solve_lp([-3.0, -2.0], A_ub=[[1.0, 1.0], [1.0, 3.0]], b_ub=[4.0, 6.0])
        self.assertEqual(r.status, 'optimal')
        self.assertAlmostEqual(r.obj, -12.0, places=9)
        self.assertAlmostEqual(r.x[0], 4.0, places=9)
        self.assertAlmostEqual(r.x[1], 0.0, places=9)

    def test_equality_form(self):
        # min x1 + x2 s.t. x1 + 2x2 = 4, x >= 0  → (4, 0), 값 4
        r = lp.solve_lp([1.0, 1.0], A_eq=[[1.0, 2.0]], b_eq=[4.0])
        self.assertEqual(r.status, 'optimal')
        self.assertAlmostEqual(r.obj, 2.0, places=9)     # (0,2) 가 더 싸다
        self.assertAlmostEqual(r.x[1], 2.0, places=9)

    def test_unbounded(self):
        # min −x s.t. −x + y <= 1, x,y >= 0 → x 를 무한히 키울 수 있다
        r = lp.solve_lp([-1.0, 0.0], A_ub=[[-1.0, 1.0]], b_ub=[1.0])
        self.assertEqual(r.status, 'unbounded')

    def test_infeasible(self):
        # x >= 2 이면서 x <= 1 은 불가능
        r = lp.solve_lp([1.0], A_ub=[[1.0], [-1.0]], b_ub=[1.0, -2.0])
        self.assertEqual(r.status, 'infeasible')

    def test_negative_rhs_needs_phase_one(self):
        # b 에 음수가 있어 슬랙 기저가 실행가능하지 않다 → 1단계가 필요
        r = lp.solve_lp([1.0, 1.0], A_ub=[[-1.0, -1.0]], b_ub=[-3.0])
        self.assertEqual(r.status, 'optimal')
        self.assertAlmostEqual(r.obj, 3.0, places=9)

    def test_all_vertices_are_basic(self):
        # 최적해의 0 이 아닌 성분 수가 제약 수를 넘지 않는다(기저해)
        r = lp.solve_lp([-1.0, -2.0, -3.0],
                        A_ub=[[1.0, 1.0, 1.0], [2.0, 1.0, 0.0]], b_ub=[10.0, 8.0])
        self.assertEqual(r.status, 'optimal')
        nz = sum(1 for v in r.x if abs(v) > 1e-9)
        self.assertLessEqual(nz, 2)


class TestDegeneracy(unittest.TestCase):
    def test_degenerate_terminates(self):
        # 퇴화가 있는 문제 — Bland 규칙이 순환을 막는지
        c = [-0.75, 150.0, -0.02, 6.0]
        A = [[0.25, -60.0, -0.04, 9.0],
             [0.5, -90.0, -0.02, 3.0],
             [0.0, 0.0, 1.0, 0.0]]
        b = [0.0, 0.0, 1.0]
        r = lp.solve_lp(c, A_ub=A, b_ub=b, rule='bland')
        self.assertEqual(r.status, 'optimal')
        self.assertLess(r.nit, 200)
        self.assertAlmostEqual(r.obj, -0.05, places=9)   # 알려진 Beale 예제의 최적값


class TestDuality(unittest.TestCase):
    def _problem(self):
        c = [-3.0, -5.0]
        A = [[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]]
        b = [4.0, 12.0, 18.0]
        return c, A, b

    def test_strong_duality(self):
        c, A, b = self._problem()
        r = lp.solve_lp(c, A_ub=A, b_ub=b)
        self.assertEqual(r.status, 'optimal')
        # 쌍대: max −bᵀy s.t. −Aᵀy ≤ ... 여기서는 y = r.dual 로 직접 검사
        self.assertAlmostEqual(r.obj, -la.dot(b, r.dual), places=8)

    def test_dual_feasibility(self):
        c, A, b = self._problem()
        r = lp.solve_lp(c, A_ub=A, b_ub=b)
        for v in r.dual:
            self.assertGreaterEqual(v, -1e-9)                 # y ≥ 0
        # Aᵀy ≥ −c  (min cᵀx, Ax ≤ b 의 쌍대 실행가능성)
        Aty = la.matvec(la.transpose(A), r.dual)
        for i in range(len(c)):
            self.assertGreaterEqual(Aty[i] + c[i], -1e-8)

    def test_complementary_slackness(self):
        c, A, b = self._problem()
        r = lp.solve_lp(c, A_ub=A, b_ub=b)
        slack = la.vsub(b, la.matvec(A, r.x))
        for i in range(len(b)):
            self.assertLess(abs(r.dual[i] * slack[i]), 1e-8)  # yᵢ·sᵢ = 0

    def test_dual_equals_shadow_price(self):
        # b 를 조금 늘렸을 때 최적값의 변화가 쌍대변수와 같아야 한다
        c, A, b = self._problem()
        r0 = lp.solve_lp(c, A_ub=A, b_ub=b)
        h = 1e-5
        for i in range(len(b)):
            bb = list(b)
            bb[i] += h
            r1 = lp.solve_lp(c, A_ub=A, b_ub=bb)
            self.assertAlmostEqual((r1.obj - r0.obj) / h, -r0.dual[i], places=5)


class TestInteriorPoint(unittest.TestCase):
    def test_matches_simplex(self):
        c = [-3.0, -5.0]
        A = [[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]]
        b = [4.0, 12.0, 18.0]
        rs = lp.solve_lp(c, A_ub=A, b_ub=b)
        ri = lp.solve_lp(c, A_ub=A, b_ub=b, method='interior')
        self.assertEqual(ri.status, 'optimal')
        self.assertLess(abs(rs.obj - ri.obj), 1e-6)
        self.assertLess(la.norm(la.vsub(rs.x, ri.x)), 1e-4)

    def test_interior_iterates_stay_positive(self):
        c = [-1.0, -1.0]
        A = [[1.0, 2.0], [3.0, 1.0]]
        b = [4.0, 6.0]
        r = lp.solve_lp(c, A_ub=A, b_ub=b, method='interior', keep_history=True)
        for h in r.history:
            self.assertGreater(min(h['x']), -1e-9)
            self.assertGreater(h['mu'], 0.0)
        # 상보성 잔차가 단조에 가깝게 줄어든다
        mus = [h['mu'] for h in r.history]
        self.assertLess(mus[-1], mus[0] * 1e-4)


class TestModeling(unittest.TestCase):
    def test_free_variable_split(self):
        # 부호 제한 없는 변수: min |x| 를 x = u − v, u,v ≥ 0 으로
        r = lp.solve_lp([1.0, 1.0], A_eq=[[1.0, -1.0]], b_eq=[-3.0])
        self.assertEqual(r.status, 'optimal')
        self.assertAlmostEqual(r.obj, 3.0, places=9)

    def test_l1_regression_as_lp(self):
        # min ‖Ax − b‖₁ 을 LP 로 — 잔차를 t 로 감싼다
        A = [[1.0, 1.0], [1.0, 2.0], [1.0, 3.0]]
        b = [2.0, 4.0, 5.5]
        x, obj = lp.l1_regression(A, b)
        # 세 점 중 두 점을 정확히 지나는 직선이 최적이어야 한다
        r = [abs(sum(A[i][j] * x[j] for j in range(2)) - b[i]) for i in range(3)]
        self.assertLess(sorted(r)[0] + sorted(r)[1], 1e-8)
        self.assertAlmostEqual(obj, sum(r), places=8)


if __name__ == '__main__':
    unittest.main()
