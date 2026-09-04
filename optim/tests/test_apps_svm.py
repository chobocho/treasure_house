# -*- coding: utf-8 -*-
"""SVM — 쌍대 해가 KKT 를 만족하고, 서포트 벡터가 기대대로 나오는가."""
import math
import random
import unittest

from py import linalg as la
from py.apps import svm as S


class TestProjection(unittest.TestCase):
    def test_satisfies_constraints(self):
        rng = random.Random(0)
        for _ in range(30):
            n = 6
            v = [rng.uniform(-3, 3) for _ in range(n)]
            a = [rng.choice([-1.0, 1.0]) for _ in range(n)]
            x = S.project_box_simplexlike(v, 0.0, 2.0, a, 0.0)
            self.assertLess(abs(la.dot(a, x)), 1e-6)
            for t in x:
                self.assertGreaterEqual(t, -1e-12)
                self.assertLessEqual(t, 2.0 + 1e-12)

    def test_is_nearest_point(self):
        # 제약을 만족하는 점을 <구성해서> 비교한다. 무작위로 뽑아 거르면
        # 초평면 위의 점이 확률 0 이라 아무것도 검사하지 못한다.
        rng = random.Random(1)
        v = [1.5, -0.5, 0.7, 2.0]
        a = [1.0, -1.0, 1.0, -1.0]
        x = S.project_box_simplexlike(v, 0.0, 1.0, a, 0.0)
        d = la.norm(la.vsub(v, x))
        checked = 0
        for _ in range(20000):
            z1, z2, z3 = (rng.uniform(0, 1) for _ in range(3))
            z4 = z1 - z2 + z3                       # a·z = 0 이 되도록
            if not (0.0 <= z4 <= 1.0):
                continue
            checked += 1
            self.assertGreaterEqual(la.norm(la.vsub(v, [z1, z2, z3, z4])), d - 1e-6)
        self.assertGreater(checked, 1000)

    def test_already_feasible_unchanged(self):
        v = [0.5, 0.5]
        a = [1.0, -1.0]
        x = S.project_box_simplexlike(v, 0.0, 1.0, a, 0.0)
        self.assertLess(la.norm(la.vsub(x, v)), 1e-6)


class TestDualSVM(unittest.TestCase):
    def setUp(self):
        self.X, self.y = S.separable_data(n=40, seed=2, margin=1.5)

    def test_constraints_hold(self):
        a, _ = S.train_dual(self.X, self.y, C=1.0, iters=1200)
        self.assertLess(abs(math.fsum(a[i] * self.y[i]
                                      for i in range(len(a)))), 1e-5)
        for v in a:
            self.assertGreaterEqual(v, -1e-9)
            self.assertLessEqual(v, 1.0 + 1e-9)

    def test_classifies_separable_data(self):
        a, _ = S.train_dual(self.X, self.y, C=10.0, iters=2000)
        f, b = S.decision_function(self.X, self.y, a, 10.0)
        wrong = sum(1 for i in range(len(self.X))
                    if self.y[i] * f(self.X[i]) < 0)
        self.assertEqual(wrong, 0)

    def test_support_vectors_are_few(self):
        a, _ = S.train_dual(self.X, self.y, C=10.0, iters=2000)
        sv = S.support_vectors(a, 10.0)
        self.assertGreater(sv['total'], 0)
        self.assertLess(sv['total'], len(self.X) * 0.5)   # 대부분은 서포트가 아니다

    def test_margin_points_have_functional_margin_one(self):
        a, _ = S.train_dual(self.X, self.y, C=10.0, iters=3000)
        f, _ = S.decision_function(self.X, self.y, a, 10.0)
        sv = S.support_vectors(a, 10.0)
        for i in sv['margin']:
            self.assertLess(abs(self.y[i] * f(self.X[i]) - 1.0), 0.05)

    def test_weights_from_dual(self):
        a, _ = S.train_dual(self.X, self.y, C=10.0, iters=2000)
        w = S.primal_weights(self.X, self.y, a)
        f, b = S.decision_function(self.X, self.y, a, 10.0)
        for x in self.X[:10]:
            self.assertLess(abs(la.dot(w, x) + b - f(x)), 1e-8)

    def test_small_C_allows_violations(self):
        X, y = S.separable_data(n=40, seed=3, margin=0.4)   # 겹치는 자료
        a, _ = S.train_dual(X, y, C=0.05, iters=1500)
        sv = S.support_vectors(a, 0.05)
        self.assertGreater(len(sv['bound']), 0)             # 마진을 넘는 점들이 생긴다

    def test_rbf_kernel_runs(self):
        X, y = S.separable_data(n=30, seed=4, margin=0.8)
        a, _ = S.train_dual(X, y, C=1.0, kernel=S.rbf_kernel(0.5), iters=800)
        f, _ = S.decision_function(X, y, a, 1.0, kernel=S.rbf_kernel(0.5))
        acc = sum(1 for i in range(len(X)) if y[i] * f(X[i]) > 0) / float(len(X))
        self.assertGreater(acc, 0.8)


if __name__ == '__main__':
    unittest.main()
