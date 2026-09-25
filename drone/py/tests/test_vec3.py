# -*- coding: utf-8 -*-
"""vec3 시험 — 벡터·3×3 행렬 도구와 7부 도구 정리의 증인."""
import math
import unittest

from droneshow import rng, vec3 as V


def rand_vec(g):
    return [g.uniform() * 4 - 2 for _ in range(3)]


class Vectors(unittest.TestCase):
    def setUp(self):
        self.g = rng.Rng(3)

    def test_dot_commutes(self):
        for _ in range(20):
            a, b = rand_vec(self.g), rand_vec(self.g)
            self.assertAlmostEqual(V.dot(a, b), V.dot(b, a), places=15)

    def test_cross_anticommutes(self):
        for _ in range(20):
            a, b = rand_vec(self.g), rand_vec(self.g)
            ab, ba = V.cross(a, b), V.cross(b, a)
            for i in range(3):
                self.assertAlmostEqual(ab[i], -ba[i], places=14)

    def test_cross_is_perpendicular(self):
        for _ in range(20):
            a, b = rand_vec(self.g), rand_vec(self.g)
            c = V.cross(a, b)
            self.assertAlmostEqual(V.dot(c, a), 0.0, places=13)
            self.assertAlmostEqual(V.dot(c, b), 0.0, places=13)

    def test_lagrange_identity(self):
        # |a×b|² + (a·b)² = |a|²|b|² — 외적의 크기가 |a||b|sinθ 인 까닭
        for _ in range(20):
            a, b = rand_vec(self.g), rand_vec(self.g)
            lhs = V.dot(V.cross(a, b), V.cross(a, b)) + V.dot(a, b) ** 2
            rhs = V.dot(a, a) * V.dot(b, b)
            self.assertAlmostEqual(lhs, rhs, places=12)

    def test_basis(self):
        self.assertEqual(V.cross([1, 0, 0], [0, 1, 0]), [0, 0, 1])

    def test_normalize(self):
        n = V.normalize([3.0, 0.0, 4.0])
        self.assertEqual(n, [0.6, 0.0, 0.8])
        self.assertAlmostEqual(V.norm(n), 1.0, places=15)


class Matrices(unittest.TestCase):
    def test_det_of_identity_and_swap(self):
        self.assertEqual(V.det3(V.eye3()), 1.0)
        swap = [[0, 1, 0], [1, 0, 0], [0, 0, 1]]
        self.assertEqual(V.det3(swap), -1.0)

    def test_det_is_triple_product(self):
        # det[a b c] (열) = a·(b×c)
        g = rng.Rng(5)
        for _ in range(20):
            a, b, c = rand_vec(g), rand_vec(g), rand_vec(g)
            m = V.from_cols(a, b, c)
            self.assertAlmostEqual(V.det3(m), V.dot(a, V.cross(b, c)),
                                   places=12)

    def test_matmul_associates_with_matvec(self):
        g = rng.Rng(6)
        a = [rand_vec(g) for _ in range(3)]
        b = [rand_vec(g) for _ in range(3)]
        x = rand_vec(g)
        lhs = V.matvec(V.matmul(a, b), x)
        rhs = V.matvec(a, V.matvec(b, x))
        for i in range(3):
            self.assertAlmostEqual(lhs[i], rhs[i], places=12)

    def test_transpose_twice(self):
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        self.assertEqual(V.transpose(V.transpose(m)), m)

    def test_inverse(self):
        m = [[2.0, 0.0, 1.0], [1.0, 3.0, 0.0], [0.0, 1.0, 4.0]]
        p = V.matmul(m, V.inv3(m))
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(p[i][j], float(i == j),
                                       places=14)

    def test_enu_ned_map_is_rotation(self):
        # ENU → NED 는 반사가 아니라 회전이다 (SPEC §1.2)
        m = V.ENU_TO_NED
        self.assertEqual(V.det3(m), 1.0)
        mt = V.matmul(V.transpose(m), m)
        self.assertEqual(mt, V.eye3())
        self.assertEqual(V.matvec(m, [1.0, 2.0, 3.0]), [2.0, 1.0, -3.0])


if __name__ == '__main__':
    unittest.main()
