# -*- coding: utf-8 -*-
"""quadrotor 시험 — 6자유도 모델(SPEC §4.3)과 호버 선형화(T11)."""
import math
import unittest

from droneshow import params
from droneshow import quadrotor as QR
from droneshow import quat as Q


class Model(unittest.TestCase):
    def setUp(self):
        self.p = params.load()
        self.oh = params.derived(self.p)['omega_hover']

    def test_state_layout(self):
        s = QR.hover_state(self.p, [1.0, 2.0, 3.0])
        self.assertEqual(len(s), 17)
        self.assertEqual(QR.pos(s), [1.0, 2.0, 3.0])
        self.assertEqual(QR.att(s), [1.0, 0.0, 0.0, 0.0])
        self.assertEqual(QR.motors(s), [self.oh] * 4)

    def test_hover_is_equilibrium(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 10.0])
        d = QR.deriv(self.p, s, [self.oh] * 4)
        for x in d:
            self.assertAlmostEqual(x, 0.0, places=12)

    def test_free_fall(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 10.0])
        s[13:17] = [0.0] * 4
        d = QR.deriv(self.p, s, [0.0] * 4)
        self.assertAlmostEqual(d[5], -self.p['g'], places=15)

    def test_hover_holds_for_a_second(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 10.0])
        for _ in range(500):
            s = QR.step(self.p, s, [self.oh] * 4, 0.002)
        self.assertAlmostEqual(QR.pos(s)[2], 10.0, places=9)

    def test_motor_lag_in_model(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 10.0])
        cmd = [self.oh * 1.1] * 4
        for _ in range(15):                      # 0.03 s = tau_m
            s = QR.step(self.p, s, cmd, 0.002)
        want = self.oh + 0.1 * self.oh * (1 - math.exp(-1))
        # RK4 의 걸음당 오차 (dt/τ)⁵/120 가 15걸음 쌓여 약 1e-5
        self.assertAlmostEqual(QR.motors(s)[0], want, places=4)

    def test_quaternion_stays_unit(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 10.0])
        cmd = [self.oh * 1.05, self.oh, self.oh * 0.95, self.oh]
        for _ in range(500):
            s = QR.step(self.p, s, cmd, 0.002)
        self.assertAlmostEqual(Q.norm(QR.att(s)), 1.0, places=14)

    def test_yaw_imbalance_spins_body(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 10.0])
        cmd = [self.oh * 1.05, self.oh * 0.95] * 2
        s[13:17] = cmd
        d = QR.deriv(self.p, s, cmd)
        self.assertLess(d[12], 0.0)             # ω̇_z < 0
        self.assertAlmostEqual(d[10], 0.0, places=12)


class SmallAngle(unittest.TestCase):
    """T11 — 호버 근처에서 x'' ≈ gθ, y'' ≈ −gφ, 오차는 O(각²)."""

    def setUp(self):
        self.p = params.load()

    def errors(self, ang):
        ex = QR.accel_tilted(self.p, 0.0, ang)
        lx = QR.accel_small_angle(self.p, 0.0, ang)
        ey = QR.accel_tilted(self.p, ang, 0.0)
        ly = QR.accel_small_angle(self.p, ang, 0.0)
        return (abs(ex[0] - lx[0]) / abs(lx[0]),
                abs(ey[1] - ly[1]) / abs(ly[1]),
                abs(ex[2] - lx[2]))

    def test_signs(self):
        a = QR.accel_small_angle(self.p, 0.1, 0.2)
        self.assertGreater(a[0], 0.0)           # 피치 + → 동쪽(+x)
        self.assertLess(a[1], 0.0)              # 롤 + → 남쪽(−y)

    def test_error_quarters_when_angle_halves(self):
        e1 = self.errors(0.1)
        e2 = self.errors(0.05)
        for a, b in zip(e1, e2):
            self.assertAlmostEqual(a / b, 4.0, delta=0.02)

    def test_tilted_uses_full_model(self):
        # 추력 mg 를 기울인 몸체 z 로 — 모델의 deriv 와 같아야 한다
        s = QR.hover_state(self.p, [0.0, 0.0, 10.0])
        s[6:10] = Q.from_euler(0.0, 0.3, 0.0)
        oh = params.derived(self.p)['omega_hover']
        d = QR.deriv(self.p, s, [oh] * 4)
        a = QR.accel_tilted(self.p, 0.0, 0.3)
        for i in range(3):
            self.assertAlmostEqual(d[3 + i], a[i], places=12)


if __name__ == '__main__':
    unittest.main()
