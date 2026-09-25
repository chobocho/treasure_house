# -*- coding: utf-8 -*-
"""ex/geofence.py 시험 — 원기둥·다각형 울타리 판정과 멈춤 거리."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import geofence as GF  # noqa: E402

SQUARE = [(0, 0), (10, 0), (10, 10), (0, 10)]
# ㄱ 자(오목) 다각형 — (7, 7) 은 파인 곳이라 밖이다
ELL = [(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]


class Fence(unittest.TestCase):
    def test_cylinder(self):
        self.assertTrue(GF.in_cylinder((3, 4, 10), (0, 0, 0), 5, 10))
        home = (0, 0, 0)
        self.assertFalse(GF.in_cylinder((3, 4.01, 10), home, 5, 10))
        self.assertFalse(GF.in_cylinder((0, 0, 10.01), home, 5, 10))

    def test_polygon_square(self):
        self.assertTrue(GF.in_polygon((5, 5), SQUARE))
        self.assertFalse(GF.in_polygon((11, 5), SQUARE))
        self.assertFalse(GF.in_polygon((-1, -1), SQUARE))

    def test_polygon_concave(self):
        self.assertTrue(GF.in_polygon((2, 8), ELL))
        self.assertTrue(GF.in_polygon((8, 2), ELL))
        self.assertFalse(GF.in_polygon((7, 7), ELL))

    def test_vertex_ray_counted_once(self):
        # 광선이 꼭짓점 (10, 4) 높이를 지나도 한 번만 센다
        self.assertTrue(GF.in_polygon((2, 4), ELL))

    def test_stop_distance(self):
        self.assertAlmostEqual(GF.stop_distance(5.0, 2.5), 5.0)
        self.assertAlmostEqual(GF.stop_distance(0.0, 2.0), 0.0)

    def test_first_breach(self):
        track = [(t, (t, 0.0, 5.0)) for t in range(10)]
        ok = lambda p: GF.in_cylinder(p, (0, 0, 0), 5.5, 20)  # noqa
        self.assertEqual(GF.first_breach(track, ok), 6)
        self.assertIsNone(GF.first_breach(track[:5], ok))


if __name__ == '__main__':
    unittest.main()
