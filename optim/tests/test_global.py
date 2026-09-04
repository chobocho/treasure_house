# -*- coding: utf-8 -*-
"""비평활·전역 최적화 — 기울기가 없거나 최소점이 여럿일 때."""
import math
import random
import unittest

from py import funcs
from py import global_opt as go
from py import linalg as la


class TestSubgradient(unittest.TestCase):
    def test_l1_converges(self):
        f = lambda x: abs(x[0] - 2.0) + abs(x[1] + 1.0)
        sg = lambda x: [1.0 if x[0] > 2 else (-1.0 if x[0] < 2 else 0.0),
                        1.0 if x[1] > -1 else (-1.0 if x[1] < -1 else 0.0)]
        r = go.subgradient(f, sg, [0.0, 0.0], step=lambda k: 1.0 / math.sqrt(k + 1),
                           iters=4000)
        self.assertLess(la.norm(la.vsub(r.x, [2.0, -1.0])), 0.05)

    def test_not_monotone(self):
        # 열경사법은 목적값이 단조 감소하지 않는다 — 하강 방향이 아닐 수 있다
        f = lambda x: abs(x[0]) + 0.1 * x[0] ** 2
        sg = lambda x: [(1.0 if x[0] > 0 else -1.0) + 0.2 * x[0]]
        r = go.subgradient(f, sg, [1.0], step=lambda k: 0.3, iters=60,
                           keep_history=True)
        fs = [h['f'] for h in r.history]
        self.assertTrue(any(fs[i + 1] > fs[i] for i in range(len(fs) - 1)))

    def test_best_so_far_is_monotone(self):
        f = lambda x: abs(x[0])
        sg = lambda x: [1.0 if x[0] > 0 else -1.0]
        r = go.subgradient(f, sg, [3.0], step=lambda k: 0.5 / math.sqrt(k + 1),
                           iters=200, keep_history=True)
        best = [h['best'] for h in r.history]
        for i in range(len(best) - 1):
            self.assertLessEqual(best[i + 1], best[i] + 1e-15)


class TestNelderMead(unittest.TestCase):
    def test_rosenbrock(self):
        p = funcs.Rosenbrock(2)
        r = go.nelder_mead(p.f, [-1.2, 1.0], maxiter=4000)
        self.assertLess(la.norm(la.vsub(r.x, [1.0, 1.0])), 1e-4)

    def test_no_gradient_needed(self):
        # 미분 불가능한 함수에서도 동작한다
        f = lambda x: abs(x[0] - 1.0) + abs(x[1] + 2.0) + 0.1 * (x[0] * x[1]) ** 2
        r = go.nelder_mead(f, [0.0, 0.0], maxiter=4000)
        self.assertLess(f(r.x), f([1.0, -2.0]) + 1e-3)

    def test_shrinks_simplex(self):
        p = funcs.Rosenbrock(2)
        r = go.nelder_mead(p.f, [-1.2, 1.0], maxiter=2000, keep_history=True)
        sizes = [h['size'] for h in r.history]
        self.assertLess(sizes[-1], sizes[0] * 1e-3)


class TestAnnealing(unittest.TestCase):
    def test_finds_global_on_multimodal(self):
        # 여러 국소 최소가 있는 1차원 함수
        f = lambda x: math.sin(3 * x[0]) + 0.1 * (x[0] - 2.0) ** 2
        best = min((f([-5 + 0.001 * i]), -5 + 0.001 * i) for i in range(10001))
        r = go.simulated_annealing(f, [-4.0], lo=[-5.0], hi=[5.0], iters=20000, seed=1)
        self.assertLess(r.fx, best[0] + 0.05)

    def test_accepts_worse_moves_early(self):
        f = lambda x: x[0] ** 2
        r = go.simulated_annealing(f, [3.0], lo=[-5.0], hi=[5.0], iters=2000,
                                   seed=2, keep_history=True)
        ups = sum(1 for i in range(len(r.history) - 1)
                  if r.history[i + 1]['f'] > r.history[i]['f'])
        self.assertGreater(ups, 0)          # 초반에는 나쁜 이동도 받아들인다

    def test_temperature_zero_is_greedy(self):
        f = lambda x: (x[0] - 1.0) ** 2
        r = go.simulated_annealing(f, [3.0], lo=[-5.0], hi=[5.0], iters=3000,
                                   seed=3, t0=1e-12, keep_history=True)
        fs = [h['f'] for h in r.history]
        for i in range(len(fs) - 1):
            self.assertLessEqual(fs[i + 1], fs[i] + 1e-12)


class TestGeneticAlgorithm(unittest.TestCase):
    def test_beats_random_search(self):
        p = funcs.Himmelblau()
        lo, hi = [-5.0, -5.0], [5.0, 5.0]
        rng = random.Random(0)
        best_rand = min(p.f([rng.uniform(-5, 5), rng.uniform(-5, 5)])
                        for _ in range(2000))
        r = go.genetic(p.f, lo, hi, pop=40, gens=50, seed=0)
        self.assertLess(r.fx, best_rand)
        self.assertLess(r.fx, 1e-2)

    def test_population_improves(self):
        p = funcs.Rosenbrock(2)
        r = go.genetic(p.f, [-3.0, -3.0], [3.0, 3.0], pop=30, gens=60, seed=4,
                       keep_history=True)
        best = [h['best'] for h in r.history]
        for i in range(len(best) - 1):
            self.assertLessEqual(best[i + 1], best[i] + 1e-12)     # 엘리트 보존


class TestGaussianProcess(unittest.TestCase):
    def test_interpolates_training_points(self):
        X = [[0.0], [1.0], [2.5], [4.0]]
        y = [0.0, 1.0, -0.5, 2.0]
        gp = go.GP(X, y, length=1.0, noise=1e-10)
        for i in range(len(X)):
            m, s = gp.predict(X[i])
            self.assertLess(abs(m - y[i]), 1e-5)
            self.assertLess(s, 1e-3)                    # 관측점에서는 불확실성이 0

    def test_uncertainty_grows_away_from_data(self):
        gp = go.GP([[0.0], [1.0]], [0.0, 1.0], length=0.5, noise=1e-8)
        _, s_near = gp.predict([0.5])
        _, s_far = gp.predict([5.0])
        self.assertGreater(s_far, s_near)

    def test_ei_is_nonnegative_and_peaks_in_gaps(self):
        gp = go.GP([[0.0], [1.0], [2.0]], [1.0, 0.2, 1.5], length=0.4, noise=1e-8)
        best = 0.2
        vals = [(go.expected_improvement(gp, [x * 0.02], best), x * 0.02)
                for x in range(101)]
        for v, _ in vals:
            self.assertGreaterEqual(v, -1e-12)
        top = max(vals)[1]
        self.assertGreater(top, 0.05)                   # 관측점 사이에서 최대


class TestBayesianOptimization(unittest.TestCase):
    def test_finds_min_within_budget(self):
        f = lambda x: (x[0] - 0.3) ** 2 + 0.3 * math.sin(12.0 * x[0])
        best = min((f([i * 0.001]), i * 0.001) for i in range(1001))
        r = go.bayes_opt(f, [0.0], [1.0], iters=25, seed=1)
        self.assertLess(r.fx, best[0] + 0.05)
        self.assertLessEqual(r.nfev, 30)

    def test_uses_far_fewer_evaluations_than_grid(self):
        f = lambda x: (x[0] - 0.62) ** 2 + 0.2 * math.sin(9.0 * x[0])
        r = go.bayes_opt(f, [0.0], [1.0], iters=20, seed=2)
        grid = min(f([i / 20.0]) for i in range(21))
        self.assertLessEqual(r.fx, grid + 1e-9)


if __name__ == '__main__':
    unittest.main()
