# -*- coding: utf-8 -*-
"""ex/imu_calib.py 시험 — 보정 식이 알고 있는 오차를 되찾는가."""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '..', 'py'))

import imu_calib as C  # noqa: E402
from droneshow import quat as Q  # noqa: E402

G = 9.81


def spiral(n):
    """구 위에 고르게 흩은 단위 벡터 n 개 (황금각 나선)."""
    out = []
    for k in range(n):
        z = 1 - 2 * (k + 0.5) / n
        r = math.sqrt(1 - z * z)
        a = k * math.pi * (3 - math.sqrt(5))
        out.append([r * math.cos(a), r * math.sin(a), z])
    return out


class Gyro(unittest.TestCase):
    def test_mean_per_axis(self):
        b = C.gyro_bias([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]])
        self.assertEqual(b, [2.0, 3.0, 4.0])

    def test_empty_is_an_error(self):
        with self.assertRaises(ValueError):
            C.gyro_bias([])


class Accel(unittest.TestCase):
    OFS = [0.12, -0.3, 0.05]
    SCL = [1.02, 0.97, 1.01]

    def read(self, true):
        return [self.SCL[i] * true[i] + self.OFS[i] for i in range(3)]

    def poses(self):
        up, down = [], []
        for i in range(3):
            e = [0.0, 0.0, 0.0]
            e[i] = G
            up.append(self.read(e))
            e[i] = -G
            down.append(self.read(e))
        return up, down

    def test_six_poses_recover_offset_and_scale(self):
        o, s = C.accel_six(*self.poses(), G)
        for i in range(3):
            self.assertAlmostEqual(o[i], self.OFS[i], places=12)
            self.assertAlmostEqual(s[i], self.SCL[i], places=12)

    def test_apply_undoes_the_error(self):
        o, s = C.accel_six(*self.poses(), G)
        v = C.apply(self.read([1.0, -2.0, 9.0]), o, s)
        for a, b in zip(v, [1.0, -2.0, 9.0]):
            self.assertAlmostEqual(a, b, places=12)


class Sphere(unittest.TestCase):
    def test_hard_iron_centre_and_radius(self):
        c, r = [0.3, -0.2, 0.1], 0.5
        pts = [[c[i] + r * d[i] for i in range(3)] for d in spiral(40)]
        c2, r2 = C.fit_sphere(pts)
        for a, b in zip(c2, c):
            self.assertAlmostEqual(a, b, places=9)
        self.assertAlmostEqual(r2, r, places=9)

    def test_too_few_points(self):
        with self.assertRaises(ValueError):
            C.fit_sphere(spiral(3))

    def test_axes_recover_scale(self):
        c, rad = [0.3, -0.2, 0.1], [0.55, 0.45, 0.5]
        pts = [[c[i] + rad[i] * d[i] for i in range(3)]
               for d in spiral(60)]
        c2, rad2 = C.fit_axes(pts)
        for a, b in zip(c2 + rad2, c + rad):
            self.assertAlmostEqual(a, b, places=9)

    def test_axes_on_a_sphere_are_equal(self):
        pts = [[0.5 * x for x in d] for d in spiral(30)]
        _c, rad = C.fit_axes(pts)
        for x in rad:
            self.assertAlmostEqual(x, 0.5, places=9)


class Line(unittest.TestCase):
    def test_exact_line(self):
        xs = [0.0, 5.0, 10.0, 20.0]
        k, b = C.fit_line(xs, [0.2 + 0.03 * x for x in xs])
        self.assertAlmostEqual(k, 0.03, places=12)
        self.assertAlmostEqual(b, 0.2, places=12)

    def test_one_x_value_is_an_error(self):
        with self.assertRaises(ValueError):
            C.fit_line([2.0, 2.0], [1.0, 3.0])


class Heading(unittest.TestCase):
    FIELD = [1.0, 0.0, -1.5]        # 수평 1, 아래로 1.5 (가정)

    def body(self, roll, pitch, yaw):
        q = Q.from_euler(roll, pitch, yaw)
        return Q.rotate(Q.conj(q), self.FIELD)

    def test_level(self):
        m = self.body(0.0, 0.0, 0.7)
        self.assertAlmostEqual(C.heading(m, 0.0, 0.0), 0.7, places=12)

    def test_tilt_compensated(self):
        m = self.body(0.2, -0.3, -2.0)
        self.assertAlmostEqual(C.heading(m, 0.2, -0.3), -2.0, places=12)

    def test_uncompensated_tilt_is_wrong(self):
        m = self.body(0.2, -0.3, -2.0)
        err = abs(C.heading(m, 0.0, 0.0) - (-2.0))
        self.assertGreater(err, math.radians(1.0))


if __name__ == '__main__':
    unittest.main()
