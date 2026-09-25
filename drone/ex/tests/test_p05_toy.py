# -*- coding: utf-8 -*-
"""5부 9장 — ex/toy_imu.py: 완구용 대체 펌웨어의 6축 상보 필터와
헤드리스."""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import toy_imu as T  # noqa: E402

G = 9.81


def deg(x):
    return math.degrees(x)


class Coeff(unittest.TestCase):
    def test_matches_lpfcalc(self):
        # 펌웨어 lpfcalc: exp(−1/((1/dt)·T)) = exp(−dt/T)
        self.assertAlmostEqual(T.coeff(0.004, 2.0), math.exp(-0.002),
                               places=15)

    def test_edges(self):
        # dt ≤ 0 이면 0(새 값만), T ≤ 0 이면 1(옛 값만) — 펌웨어 그대로
        self.assertEqual(T.coeff(0.0, 2.0), 0.0)
        self.assertEqual(T.coeff(-1.0, 2.0), 0.0)
        self.assertEqual(T.coeff(0.004, 0.0), 1.0)


class Filter(unittest.TestCase):
    def test_level_and_still_stays_level(self):
        f = T.ToyIMU()
        for _ in range(1000):
            f.update([0.0, 0.0, 0.0], [0.0, 0.0, G], 0.004)
        self.assertLess(f.tilt(), 1e-12)

    def test_gyro_alone_integrates_rotation(self):
        # 가속도를 창 밖(0 g)으로 두면 자이로만으로 0.5 rad 기운다
        f = T.ToyIMU()
        for _ in range(125):
            f.update([1.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.004)
        self.assertAlmostEqual(f.tilt(), 0.5, delta=0.005)

    def test_accel_pulls_with_time_constant(self):
        # 10° 틀린 추정이 시간 상수(2 초) 뒤 e⁻¹ 만큼 남는다
        f = T.ToyIMU(filtertime=2.0)
        th = math.radians(10)
        f.est = [0.0, G * math.sin(th), G * math.cos(th)]
        for _ in range(500):                      # 2 초
            f.update([0.0, 0.0, 0.0], [0.0, 0.0, G], 0.004)
        self.assertAlmostEqual(deg(f.tilt()), 10 * math.exp(-1),
                               delta=0.05)

    def test_gate_is_exclusive(self):
        # 0.7 g·1.3 g 는 받지 않는다(펌웨어는 > 와 <), 1.0 g 는 받는다
        for scale, used in ((0.5, False), (0.7, False), (1.0, True),
                            (1.3, False), (1.4, False)):
            f = T.ToyIMU()
            f.est = [0.0, G, 0.0]                 # 옆으로 누운 추정
            f.update([0.0, 0.0, 0.0], [0.0, 0.0, scale * G], 0.004)
            moved = f.est != [0.0, G, 0.0]
            self.assertEqual(moved, used, scale)

    def test_coordinated_acceleration_fools_it(self):
        # 기운 채 가속하는 멀티로터의 가속도계는 몸체 z 만 본다 —
        # 필터는 "수평" 쪽으로 끌려간다(L20). 2 초 뒤 참 20° 가
        # 20°·e⁻¹ 로 줄어 보인다
        th = math.radians(20)
        f = T.ToyIMU(filtertime=2.0)
        f.est = [0.0, G * math.sin(th), G * math.cos(th)]
        for _ in range(500):
            f.update([0.0, 0.0, 0.0], [0.0, 0.0, G / math.cos(th)],
                     0.004)
        self.assertAlmostEqual(deg(f.tilt()), 20 * math.exp(-1),
                               delta=0.1)

    def test_roll_pitch_signs(self):
        # 롤 + 는 몸체 x 축 둘레 오른손 회전 — 왼쪽(+y)이 올라가고,
        # 몸체에서 본 '위'(Rᵀe₃)는 (0, sin φ, cos φ) 가 된다
        f = T.ToyIMU()
        th = math.radians(15)
        f.est = [0.0, G * math.sin(th), G * math.cos(th)]
        r, p = f.roll_pitch()
        self.assertAlmostEqual(deg(r), 15.0, places=9)
        self.assertAlmostEqual(p, 0.0, places=12)


class Headless(unittest.TestCase):
    def test_bias_drifts_linearly(self):
        h = T.Headless()
        for _ in range(2500):                     # 10 초
            h.update(0.01, 0.004)
        self.assertAlmostEqual(h.yaw, 0.1, places=9)

    def test_wraps_to_pi(self):
        h = T.Headless()
        h.yaw = 3.1
        h.update(0.1, 1.0)
        self.assertAlmostEqual(h.yaw, 3.2 - 2 * math.pi, places=9)

    def test_stick_rotation(self):
        # 요가 90° 돌았다고 믿으면 스틱 (1, 0) 은 (0, 1) 로 간다
        h = T.Headless()
        h.yaw = math.pi / 2
        x, y = h.rotate(1.0, 0.0)
        self.assertAlmostEqual(x, 0.0, places=12)
        self.assertAlmostEqual(y, 1.0, places=12)

    def test_reset(self):
        h = T.Headless()
        h.update(1.0, 1.0)
        h.reset()
        self.assertEqual(h.yaw, 0.0)


if __name__ == '__main__':
    unittest.main()
