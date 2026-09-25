# -*- coding: utf-8 -*-
"""assign 시험 — 헝가리안(T29), 교차(T30), 동기 직선 이동의
간격(T31)."""
import math
import unittest

from droneshow import assign as AS
from droneshow import collide
from droneshow import rng


def pts2(g, n, w=10.0):
    return [[g.uniform() * w, 0.0, g.uniform() * w] for _ in range(n)]


class Hungarian(unittest.TestCase):
    def test_small_known(self):
        c = [[4, 1, 3], [2, 0, 5], [3, 2, 2]]
        perm, total, _ops = AS.hungarian(c)
        self.assertEqual(total, 5)
        self.assertEqual(perm, [1, 0, 2])

    def test_equals_brute_force(self):
        # T29 — n ≤ 7 에서 모든 순열과 비교
        g = rng.Rng(9)
        for n in range(1, 8):
            for _ in range(10):
                c = [[g.uniform() for _ in range(n)] for _ in range(n)]
                _p, total, _o = AS.hungarian(c)
                _bp, best = AS.brute(c)
                self.assertAlmostEqual(total, best, places=12)

    def test_is_permutation(self):
        g = rng.Rng(10)
        c = [[g.uniform() for _ in range(30)] for _ in range(30)]
        perm, _t, _o = AS.hungarian(c)
        self.assertEqual(sorted(perm), list(range(30)))

    def test_ops_grow_at_most_cubically(self):
        g = rng.Rng(12)
        ops = []
        for n in (10, 20, 40):
            c = [[g.uniform() for _ in range(n)] for _ in range(n)]
            ops.append(AS.hungarian(c)[2])
        self.assertLessEqual(ops[2], 8 * 8 * ops[0])
        self.assertLessEqual(ops[2] / 40 ** 3, 2.0)


class Crossing(unittest.TestCase):
    """T30 — 그냥 거리 최적 할당은 평면에서 교차가 없다. 제곱은
    아니다."""

    def test_plain_cost_optimum_never_crosses(self):
        g = rng.Rng(21)
        for _ in range(60):
            a, b = pts2(g, 6), pts2(g, 6)
            perm, _t, _o = AS.hungarian(AS.cost_matrix(a, b, False))
            self.assertEqual(collide.crossings(a, b, perm), 0)

    def test_squared_cost_can_cross(self):
        c = 0.9
        u, w = [1.0, 0.0, 0.0], [c, 0.0, math.sqrt(1 - c * c)]
        a = [[-u[0], 0.0, -u[2]], [-10 * w[0], 0.0, -10 * w[2]]]
        b = [[10 * u[0], 0.0, 10 * u[2]], [w[0], 0.0, w[2]]]
        perm, _t, _o = AS.hungarian(AS.cost_matrix(a, b, True))
        self.assertEqual(perm, [0, 1])
        self.assertEqual(collide.crossings(a, b, perm), 1)

    def test_swap_rule(self):
        # 교환하면 제곱 비용이 −2(a1−a2)·(b1−b2) 만큼 줄어든다
        a = [[0.0, 0.0, 0.0], [3.0, 0.0, 1.0]]
        b = [[5.0, 0.0, 2.0], [1.0, 0.0, 4.0]]
        keep = AS.total(AS.cost_matrix(a, b, True), [0, 1])
        swap = AS.total(AS.cost_matrix(a, b, True), [1, 0])
        dab = sum((a[0][k] - a[1][k]) * (b[0][k] - b[1][k])
                  for k in range(3))
        self.assertAlmostEqual(keep - swap, -2 * dab, places=12)


class Synchronised(unittest.TestCase):
    """T31 — 제곱 최적이면 모든 쌍이 Δa·Δb ≥ 0, 그래서 거리 ≥ δ/√2."""

    def test_pairwise_monotone(self):
        g = rng.Rng(31)
        for _ in range(20):
            a, b = pts2(g, 8), pts2(g, 8)
            perm, _t, _o = AS.hungarian(AS.cost_matrix(a, b, True))
            for i in range(8):
                for j in range(i + 1, 8):
                    bi, bj = b[perm[i]], b[perm[j]]
                    d = sum((a[i][k] - a[j][k]) * (bi[k] - bj[k])
                            for k in range(3))
                    self.assertGreaterEqual(d, -1e-12)

    def test_distance_bound_holds(self):
        g = rng.Rng(32)
        for _ in range(10):
            a = [[x * 3.0, 0.0, z * 3.0] for x in range(4)
                 for z in range(4)]
            b = [[g.uniform() * 30, 0.0, g.uniform() * 30]
                 for _ in range(16)]
            delta = min(collide.min_distance(a)[0],
                        collide.min_distance(b)[0])
            perm, _t, _o = AS.hungarian(AS.cost_matrix(a, b, True))
            got = collide.check_transition(a, b, perm, lambda u: u, 200)
            self.assertGreaterEqual(got[0], delta / math.sqrt(2) - 1e-9)

    def test_plain_cost_can_collide(self):
        # 그냥 거리 최적은 동기 이동 중 부딪칠 수 있다 — 찾아낸다
        g = rng.Rng(33)
        worst = 1e9
        for _ in range(200):
            a, b = pts2(g, 6, 12.0), pts2(g, 6, 12.0)
            delta = min(collide.min_distance(a)[0],
                        collide.min_distance(b)[0])
            perm, _t, _o = AS.hungarian(AS.cost_matrix(a, b, False))
            got = collide.check_transition(a, b, perm, lambda u: u, 100)
            worst = min(worst, got[0] / delta)
        self.assertLess(worst, 1 / math.sqrt(2))


class Collide(unittest.TestCase):
    def test_min_distance_matches_brute(self):
        g = rng.Rng(41)
        p = [[g.uniform() * 20, g.uniform() * 20, g.uniform() * 5]
             for _ in range(120)]
        d, i, j = collide.min_distance(p)
        brute = min(math.dist(p[a], p[b]) for a in range(120)
                    for b in range(a + 1, 120))
        self.assertAlmostEqual(d, brute, places=12)
        self.assertAlmostEqual(math.dist(p[i], p[j]), d, places=12)

    def test_segments_cross(self):
        a = [[0.0, 0.0, 0.0], [0.0, 0.0, 2.0]]
        b = [[2.0, 0.0, 2.0], [2.0, 0.0, 0.0]]
        self.assertEqual(collide.crossings(a, b, [0, 1]), 1)
        self.assertEqual(collide.crossings(a, b, [1, 0]), 0)


if __name__ == '__main__':
    unittest.main()
