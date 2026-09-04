# -*- coding: utf-8 -*-
"""포트폴리오 — KKT 해가 제약을 만족하고, 경계가 볼록한가."""
import math
import random
import unittest

from py.apps import portfolio as P
from py import linalg as la


def toy(seed=0, n=300, d=4):
    rng = random.Random(seed)
    base = [0.10, 0.06, 0.03, 0.08][:d]
    vol = [0.25, 0.12, 0.05, 0.20][:d]
    rets = []
    for _ in range(n):
        common = rng.gauss(0, 0.4)
        rets.append([base[j] + vol[j] * (0.6 * common + rng.gauss(0, 0.8))
                     for j in range(d)])
    return P.stats(rets)


class TestStats(unittest.TestCase):
    def test_covariance_symmetric_psd(self):
        mu, S = toy()
        self.assertTrue(la.is_symmetric(S))
        vals, _ = la.eigh(S)
        self.assertGreater(vals[0], -1e-12)

    def test_mean_close_to_truth(self):
        mu, S = toy(seed=1, n=4000)
        for got, want in zip(mu, [0.10, 0.06, 0.03, 0.08]):
            self.assertLess(abs(got - want), 0.02)


class TestMinVariance(unittest.TestCase):
    def test_constraints_satisfied(self):
        mu, S = toy(seed=2)
        for target in (0.04, 0.06, 0.09):
            x, _ = P.min_variance(S, mu, target)
            self.assertAlmostEqual(math.fsum(x), 1.0, places=8)
            self.assertAlmostEqual(la.dot(mu, x), target, places=8)

    def test_is_optimal_by_kkt(self):
        mu, S = toy(seed=3)
        x, lam = P.min_variance(S, mu, 0.07)
        # 정류조건: Σx + λ1 μ + λ2 1 = 0
        g = la.matvec(S, x)
        r = [g[j] + lam[0] * mu[j] + lam[1] for j in range(len(x))]
        self.assertLess(la.norm(r), 1e-8)

    def test_beats_random_portfolios(self):
        mu, S = toy(seed=4)
        target = 0.07
        x, _ = P.min_variance(S, mu, target)
        best = P.risk(S, x)
        rng = random.Random(0)
        for _ in range(2000):
            w = [rng.uniform(-1, 2) for _ in range(len(mu))]
            s = math.fsum(w)
            if abs(s) < 1e-9:
                continue
            w = [v / s for v in w]
            if abs(la.dot(mu, w) - target) < 1e-3:
                self.assertGreaterEqual(P.risk(S, w), best - 1e-9)

    def test_frontier_is_convex(self):
        mu, S = toy(seed=5)
        fr = P.frontier(S, mu, n=9)
        risks = [f['risk'] for f in fr]
        k = min(range(len(risks)), key=lambda i: risks[i])
        for i in range(k, len(risks) - 1):          # 최소 위험 오른쪽은 증가
            self.assertLessEqual(risks[i], risks[i + 1] + 1e-9)
        for i in range(k):                          # 왼쪽은 감소
            self.assertGreaterEqual(risks[i], risks[i + 1] - 1e-9)


class TestLongOnly(unittest.TestCase):
    def test_no_negative_weights(self):
        mu, S = toy(seed=6)
        x = P.min_variance_long_only(S, mu, 0.07)
        self.assertGreater(min(x), -1e-9)
        self.assertAlmostEqual(math.fsum(x), 1.0, places=6)

    def test_long_only_risk_is_higher(self):
        mu, S = toy(seed=7)
        target = 0.07
        free, _ = P.min_variance(S, mu, target)
        constrained = P.min_variance_long_only(S, mu, target)
        # 제약이 더 많으므로 위험이 낮을 수는 없다 (같은 수익률에서)
        self.assertGreaterEqual(P.risk(S, constrained), P.risk(S, free) - 1e-6)

    def test_unconstrained_may_short(self):
        mu, S = toy(seed=8)
        fr = P.frontier(S, mu, n=7)
        self.assertTrue(any(f['min_weight'] < -1e-6 for f in fr))


if __name__ == '__main__':
    unittest.main()
