# -*- coding: utf-8 -*-
"""13부 — ex/shape_pgm.py 가 모양을 글자 PGM(P2)으로 바르게 쓰는가."""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'py'))
import shape_pgm as S  # noqa: E402
from droneshow import formation as F  # noqa: E402


def cells(text):
    return F._pgm(text)


class Pgm(unittest.TestCase):
    def test_header_and_size(self):
        w, h, px = cells(S.pgm(S.inside_heart, 40))
        self.assertEqual((w, h), (40, 40))
        self.assertEqual(len(px), 40)

    def test_values_are_0_or_255(self):
        text = S.pgm(S.inside_star, 20)
        body = text.split('\n', 3)[3].split()
        self.assertEqual(set(body), {'0', '255'})

    def test_heart_area_close_to_shape(self):
        # 칸 중심이 안쪽이면 밝다 — 칸이 촘촘하면 밝은 칸 비율이
        # 하트의 넓이 비율에 다가간다(작은 칸에서 ±5 %)
        w, h, px = cells(S.pgm(S.inside_heart, 80))
        lit = sum(v > 0.5 for row in px for v in row) / (w * h)
        self.assertAlmostEqual(lit, S.heart_area_fraction(), delta=0.05)

    def test_star_is_symmetric_left_right(self):
        w, h, px = cells(S.pgm(S.inside_star, 41))
        for row in px:
            self.assertEqual(row, row[::-1])

    def test_inside_tests_boundaries(self):
        # 가운데는 안, 네 귀퉁이는 밖
        for f in (S.inside_heart, S.inside_star):
            self.assertTrue(f(0.0, 0.0))
            for x, y in ((-0.99, -0.99), (0.99, 0.99), (-0.99, 0.99)):
                self.assertFalse(f(x, y))

    def test_too_small_is_refused(self):
        for n in (0, 1, 2):
            with self.assertRaises(ValueError):
                S.pgm(S.inside_heart, n)


if __name__ == '__main__':
    unittest.main()
