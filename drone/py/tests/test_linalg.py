# -*- coding: utf-8 -*-
"""linalg 시험 — 가우스 소거(풀이·계수).

믹서(T9·T10)와 최소 스냅(T27)이 쓴다."""
import unittest

from droneshow import linalg


class Solve(unittest.TestCase):
    def test_solve_small(self):
        a = [[2.0, 1.0], [1.0, 3.0]]
        x = linalg.solve(a, [3.0, 5.0])
        self.assertAlmostEqual(x[0], 0.8, places=14)
        self.assertAlmostEqual(x[1], 1.4, places=14)

    def test_needs_pivoting(self):
        # 첫 피벗이 0 — 줄을 바꾸지 않으면 0 으로 나눈다
        a = [[0.0, 1.0], [1.0, 1.0]]
        self.assertEqual(linalg.solve(a, [2.0, 3.0]), [1.0, 2.0])

    def test_singular_raises(self):
        with self.assertRaises(ValueError):
            linalg.solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_does_not_modify_input(self):
        a = [[2.0, 1.0], [1.0, 3.0]]
        b = [3.0, 5.0]
        linalg.solve(a, b)
        self.assertEqual(a, [[2.0, 1.0], [1.0, 3.0]])
        self.assertEqual(b, [3.0, 5.0])


class Rank(unittest.TestCase):
    def test_full_and_deficient(self):
        self.assertEqual(linalg.rank([[1, 0], [0, 1]]), 2)
        self.assertEqual(linalg.rank([[1, 2], [2, 4]]), 1)
        self.assertEqual(linalg.rank([[0, 0], [0, 0]]), 0)

    def test_tall_matrix(self):
        rows = [[1, 1, 1, 1], [0, 0, 0, 0], [1, -1, 1, -1],
                [0, 0, 0, 0], [1, 1, -1, -1], [2, 0, 0, 2]]
        self.assertEqual(linalg.rank(rows), 4)

    def test_det(self):
        self.assertAlmostEqual(linalg.det([[1, 2], [3, 4]]), -2.0)
        self.assertAlmostEqual(
            linalg.det([[2, 0, 0, 0], [0, 3, 0, 0], [0, 0, 1, 5],
                        [0, 0, 0, 4]]), 24.0)


if __name__ == '__main__':
    unittest.main()
