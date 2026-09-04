# -*- coding: utf-8 -*-
"""정수·조합 최적화 — 전수 조사와 같은 답을 주는가, 하한이 정말 하한인가."""
import itertools
import math
import random
import unittest

from py import linalg as la
from py import lp
from py import milp


def brute_force_milp(c, A, b, ub):
    """작은 정수 문제를 전수 조사로 푼다 — 테스트의 기준점."""
    best, bx = None, None
    for x in itertools.product(*[range(u + 1) for u in ub]):
        if all(sum(A[i][j] * x[j] for j in range(len(c))) <= b[i] + 1e-9
               for i in range(len(A))):
            v = sum(c[j] * x[j] for j in range(len(c)))
            if best is None or v < best - 1e-12:
                best, bx = v, list(x)
    return best, bx


class TestBranchAndBound(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(3)
        for _ in range(12):
            n, m = 4, 3
            c = [-rng.randint(1, 9) for _ in range(n)]
            A = [[rng.randint(1, 5) for _ in range(n)] for _ in range(m)]
            b = [float(rng.randint(8, 20)) for _ in range(m)]
            ub = [4] * n
            want, _ = brute_force_milp(c, A, b, ub)
            r = milp.branch_and_bound([float(v) for v in c],
                                      A_ub=[[float(v) for v in row] for row in A] +
                                           [[1.0 if j == k else 0.0 for j in range(n)]
                                            for k in range(n)],
                                      b_ub=list(b) + [float(u) for u in ub])
            self.assertEqual(r.status, 'optimal')
            self.assertAlmostEqual(r.obj, want, places=6)
            for v in r.x:
                self.assertLess(abs(v - round(v)), 1e-6)

    def test_relaxation_is_lower_bound(self):
        c = [-5.0, -4.0]
        A = [[6.0, 4.0], [1.0, 2.0]]
        b = [24.0, 6.0]
        rel = lp.solve_lp(c, A_ub=A, b_ub=b)
        r = milp.branch_and_bound(c, A_ub=A, b_ub=b)
        self.assertLessEqual(rel.obj, r.obj + 1e-9)      # 완화가 하한
        self.assertGreater(r.obj - rel.obj, 1e-9)        # 이 예에서는 간격이 있다

    def test_infeasible_integer_problem(self):
        # 2x = 1 은 정수해가 없다
        r = milp.branch_and_bound([1.0], A_eq=[[2.0]], b_eq=[1.0], ub=[10.0])
        self.assertEqual(r.status, 'infeasible')

    def test_node_count_reasonable(self):
        c = [-3.0, -2.0, -4.0]
        A = [[1.0, 1.0, 2.0], [2.0, 1.0, 1.0]]
        b = [10.0, 12.0]
        r = milp.branch_and_bound(c, A_ub=A, b_ub=b, ub=[6.0] * 3)
        self.assertEqual(r.status, 'optimal')
        self.assertLess(r.nodes, 200)


class TestKnapsack(unittest.TestCase):
    def test_dp_matches_brute_force(self):
        rng = random.Random(11)
        for _ in range(20):
            n = 8
            v = [rng.randint(1, 30) for _ in range(n)]
            w = [rng.randint(1, 15) for _ in range(n)]
            cap = rng.randint(10, 40)
            best = 0
            for mask in range(1 << n):
                tw = sum(w[i] for i in range(n) if mask >> i & 1)
                if tw <= cap:
                    best = max(best, sum(v[i] for i in range(n) if mask >> i & 1))
            got, pick = milp.knapsack_dp(v, w, cap)
            self.assertEqual(got, best)
            self.assertLessEqual(sum(w[i] for i in pick), cap)
            self.assertEqual(sum(v[i] for i in pick), best)

    def test_lp_bound_dominates(self):
        # 분수 배낭(탐욕)의 값은 정수 배낭의 상한이다
        v = [60, 100, 120]
        w = [10, 20, 30]
        cap = 50
        exact, _ = milp.knapsack_dp(v, w, cap)
        bound = milp.knapsack_lp_bound(v, w, cap)
        self.assertGreaterEqual(bound + 1e-9, exact)
        self.assertAlmostEqual(bound, 240.0, places=9)
        self.assertEqual(exact, 220)

    def test_empty_and_zero_capacity(self):
        self.assertEqual(milp.knapsack_dp([], [], 10)[0], 0)
        self.assertEqual(milp.knapsack_dp([5], [3], 0)[0], 0)


class TestHungarian(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(5)
        for _ in range(20):
            n = rng.randint(2, 6)
            C = [[rng.randint(1, 20) for _ in range(n)] for _ in range(n)]
            best = min(sum(C[i][p[i]] for i in range(n))
                       for p in itertools.permutations(range(n)))
            cost, assign = milp.hungarian(C)
            self.assertEqual(cost, best)
            self.assertEqual(sorted(assign), list(range(n)))

    def test_known_example(self):
        C = [[4, 1, 3], [2, 0, 5], [3, 2, 2]]
        cost, assign = milp.hungarian(C)
        self.assertEqual(cost, 5)

    def test_rectangular_raises(self):
        with self.assertRaises(ValueError):
            milp.hungarian([[1, 2, 3], [4, 5, 6]])


class TestMinCostFlow(unittest.TestCase):
    def test_simple_network(self):
        # 0 → 1 → 3, 0 → 2 → 3.  비용이 싼 쪽부터 채운다
        edges = [(0, 1, 3, 1), (0, 2, 2, 2), (1, 3, 2, 1), (2, 3, 3, 1)]
        cost, flow = milp.min_cost_flow(4, edges, 0, 3, 4)
        self.assertEqual(cost, 2 * 2 + 2 * 3)          # 경로 0-1-3 두 단위, 0-2-3 두 단위
        self.assertEqual(sum(flow[i] for i in (2, 3)), 4)

    def test_matches_lp_relaxation(self):
        edges = [(0, 1, 4, 2), (0, 2, 3, 3), (1, 2, 2, 1), (1, 3, 3, 2), (2, 3, 4, 1)]
        cost, _ = milp.min_cost_flow(4, edges, 0, 3, 5)
        # 같은 문제를 LP 로 풀면 정수해가 나온다(완전단모듈성)
        ne = len(edges)
        A_eq, b_eq = [], []
        for v in range(1, 3):
            row = [0.0] * ne
            for k, (u, w, cap, c) in enumerate(edges):
                if u == v:
                    row[k] = 1.0
                if w == v:
                    row[k] = -1.0
            A_eq.append(row)
            b_eq.append(0.0)
        row = [0.0] * ne
        for k, (u, w, cap, c) in enumerate(edges):
            if u == 0:
                row[k] = 1.0
        A_eq.append(row)
        b_eq.append(5.0)
        A_ub = [[1.0 if j == k else 0.0 for j in range(ne)] for k in range(ne)]
        b_ub = [float(e[2]) for e in edges]
        r = lp.solve_lp([float(e[3]) for e in edges], A_ub=A_ub, b_ub=b_ub,
                        A_eq=A_eq, b_eq=b_eq)
        self.assertEqual(r.status, 'optimal')
        self.assertAlmostEqual(r.obj, cost, places=6)
        for v in r.x:                                   # LP 해가 이미 정수다
            self.assertLess(abs(v - round(v)), 1e-6)

    def test_insufficient_capacity(self):
        edges = [(0, 1, 1, 1)]
        with self.assertRaises(ValueError):
            milp.min_cost_flow(2, edges, 0, 1, 5)


class TestTotalUnimodularity(unittest.TestCase):
    def test_transportation_lp_is_integral(self):
        # 수송 문제의 제약행렬은 완전단모듈 → LP 해가 정수
        sup, dem = [3.0, 5.0], [4.0, 4.0]
        cost = [[2.0, 3.0], [4.0, 1.0]]
        n = 4
        A_eq, b_eq = [], []
        for i in range(2):
            row = [0.0] * n
            for j in range(2):
                row[2 * i + j] = 1.0
            A_eq.append(row); b_eq.append(sup[i])
        for j in range(2):
            row = [0.0] * n
            for i in range(2):
                row[2 * i + j] = 1.0
            A_eq.append(row); b_eq.append(dem[j])
        c = [cost[i][j] for i in range(2) for j in range(2)]
        r = lp.solve_lp(c, A_eq=A_eq, b_eq=b_eq)
        self.assertEqual(r.status, 'optimal')
        for v in r.x:
            self.assertLess(abs(v - round(v)), 1e-7)

    def test_is_tu_detects_small_cases(self):
        self.assertTrue(milp.is_totally_unimodular([[1, 0], [0, 1]]))
        self.assertTrue(milp.is_totally_unimodular([[1, 1, 0], [0, 1, 1]]))
        self.assertFalse(milp.is_totally_unimodular([[1, 1, 0], [0, 1, 1], [1, 0, 1]]))


if __name__ == '__main__':
    unittest.main()


class TestGomory(unittest.TestCase):
    def _problem(self):
        # max 5x + 4y  s.t. 6x+4y<=24, x+2y<=6  → LP 최적 (3, 1.5), 정수 최적 (4, 0)
        return [-5.0, -4.0], [[6.0, 4.0], [1.0, 2.0]], [24.0, 6.0]

    def test_bound_improves(self):
        c, A, b = self._problem()
        r, cuts, bounds = milp.gomory_cuts(c, A, b, rounds=6)
        self.assertGreater(len(cuts), 0)
        for i in range(len(bounds) - 1):
            self.assertGreaterEqual(bounds[i + 1][0], bounds[i][0] - 1e-9)  # 하한이 올라간다
        exact = milp.branch_and_bound(c, A_ub=A, b_ub=b)
        self.assertLessEqual(bounds[-1][0], exact.obj + 1e-7)
        self.assertEqual(bounds[0][1], 0)
        self.assertGreater(bounds[-1][1], 0)

    def test_never_cuts_integer_points(self):
        # 모든 정수 실행가능해가 추가된 절단을 만족해야 한다
        c, A, b = self._problem()
        _, cuts, _ = milp.gomory_cuts(c, A, b, rounds=4)
        for x in range(0, 6):
            for y in range(0, 6):
                if 6 * x + 4 * y <= 24 and x + 2 * y <= 6:
                    for row, rb in cuts:
                        self.assertLessEqual(row[0] * x + row[1] * y, rb + 1e-7,
                                             '정수해 (%d,%d) 가 잘렸다' % (x, y))

    def test_cut_separates_current_solution(self):
        c, A, b = self._problem()
        rel = lp.solve_lp(c, A_ub=A, b_ub=b)
        _, cuts, _ = milp.gomory_cuts(c, A, b, rounds=1)
        viol = max(cuts[k][0][0] * rel.x[0] + cuts[k][0][1] * rel.x[1] - cuts[k][1]
                   for k in range(len(cuts)))
        self.assertGreater(viol, 1e-7)          # 현재 분수해는 실제로 잘린다
