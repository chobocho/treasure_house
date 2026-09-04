# -*- coding: utf-8 -*-
"""경로 문제 — 정확해·휴리스틱·하한이 서로 맞물리는가."""
import itertools
import unittest

from py.apps import routing as R


class TestExact(unittest.TestCase):
    def test_matches_brute_force(self):
        for seed in range(6):
            pts = R.random_points(7, seed=seed)
            D = R.distance_matrix(pts)
            best, tour = R.held_karp(D)
            brute = min(R.tour_length(D, [0] + list(p))
                        for p in itertools.permutations(range(1, 7)))
            self.assertAlmostEqual(best, brute, places=9)
            self.assertEqual(sorted(tour), list(range(7)))

    def test_tour_is_valid(self):
        D = R.distance_matrix(R.random_points(9, seed=1))
        best, tour = R.held_karp(D)
        self.assertEqual(sorted(tour), list(range(9)))
        self.assertAlmostEqual(R.tour_length(D, tour), best, places=9)

    def test_trivial_sizes(self):
        self.assertEqual(R.held_karp([[0.0]])[0], 0.0)
        D = [[0.0, 3.0], [3.0, 0.0]]
        self.assertAlmostEqual(R.held_karp(D)[0], 6.0)


class TestHeuristics(unittest.TestCase):
    def test_two_opt_improves_nearest_neighbor(self):
        wins = 0
        for seed in range(10):
            D = R.distance_matrix(R.random_points(20, seed=seed))
            nn, tour = R.nearest_neighbor(D)
            imp, _ = R.two_opt(D, tour)
            self.assertLessEqual(imp, nn + 1e-9)
            if imp < nn - 1e-9:
                wins += 1
        self.assertGreater(wins, 7)

    def test_two_opt_is_local_optimum(self):
        D = R.distance_matrix(R.random_points(15, seed=2))
        _, tour = R.nearest_neighbor(D)
        best, t = R.two_opt(D, tour)
        n = len(t)
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b = t[i - 1], t[i]
                c, d = t[j], t[(j + 1) % n]
                self.assertGreaterEqual(D[a][c] + D[b][d] - D[a][b] - D[c][d], -1e-9)

    def test_heuristics_above_exact(self):
        for seed in range(5):
            D = R.distance_matrix(R.random_points(10, seed=seed))
            exact, _ = R.held_karp(D)
            nn, tour = R.nearest_neighbor(D)
            imp, _ = R.two_opt(D, tour)
            self.assertGreaterEqual(nn, exact - 1e-9)
            self.assertGreaterEqual(imp, exact - 1e-9)


class TestLowerBound(unittest.TestCase):
    def test_mst_is_lower_bound(self):
        for seed in range(8):
            D = R.distance_matrix(R.random_points(9, seed=seed))
            exact, _ = R.held_karp(D)
            lb = R.mst_lower_bound(D)
            self.assertLessEqual(lb, exact + 1e-9)

    def test_bound_is_informative(self):
        # 하한이 최적값의 절반 이상은 되어야 쓸모가 있다
        D = R.distance_matrix(R.random_points(10, seed=4))
        exact, _ = R.held_karp(D)
        self.assertGreater(R.mst_lower_bound(D) / exact, 0.5)


if __name__ == '__main__':
    unittest.main()
