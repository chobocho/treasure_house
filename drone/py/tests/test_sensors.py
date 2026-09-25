# -*- coding: utf-8 -*-
"""sensors 시험 — 센서 모델이 스펙의 식대로 값을 낸다 (SPEC §6)."""
import unittest

from droneshow import params
from droneshow import quadrotor as QR
from droneshow import quat as Q
from droneshow import rng
from droneshow import sensors as S


class Models(unittest.TestCase):
    def setUp(self):
        self.p = params.load()
        zero = {k: 0.0 for k in ('sigma_g', 'sigma_bg', 'sigma_a',
                                 'sigma_b', 'sigma_p')}
        self.quiet = S.Sensors(dict(self.p, **zero), rng.Rng(1))

    def test_hover_accelerometer_reads_plus_g(self):
        # 떠 있는 드론의 가속도계는 +g 를 잰다 — 자유낙하에서만 0
        s = QR.hover_state(self.p, [0.0, 0.0, 5.0])
        oh = params.derived(self.p)['omega_hover']
        d = QR.deriv(self.p, s, [oh] * 4)
        a = self.quiet.accel(s, d)
        self.assertAlmostEqual(a[2], self.p['g'], places=12)
        self.assertAlmostEqual(a[0], 0.0, places=12)

    def test_free_fall_accelerometer_reads_zero(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 5.0])
        s[13:17] = [0.0] * 4
        d = QR.deriv(self.p, s, [0.0] * 4)
        for x in self.quiet.accel(s, d):
            self.assertAlmostEqual(x, 0.0, places=12)

    def test_tilted_accelerometer_in_body_frame(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 5.0])
        s[6:10] = Q.from_euler(0.3, 0.0, 0.0)
        d = [0.0] * 17                        # 정지(가속도 0) 라고 가정
        a = self.quiet.accel(s, d)
        want = Q.rotate(Q.conj(s[6:10]), [0.0, 0.0, self.p['g']])
        for x, y in zip(a, want):
            self.assertAlmostEqual(x, y, places=12)

    def test_gyro_bias_is_fixed(self):
        sen = S.Sensors(dict(self.p, sigma_g=0.0), rng.Rng(3))
        s = QR.hover_state(self.p, [0.0, 0.0, 5.0])
        self.assertEqual(sen.gyro(s), sen.gyro(s))
        self.assertNotEqual(sen.gyro(s), [0.0, 0.0, 0.0])

    def test_noise_is_seeded(self):
        s = QR.hover_state(self.p, [0.0, 0.0, 5.0])
        a = S.Sensors(self.p, rng.Rng(9))
        b = S.Sensors(self.p, rng.Rng(9))
        self.assertEqual([a.gnss(s) for _ in range(5)],
                         [b.gnss(s) for _ in range(5)])
        self.assertEqual(a.baro(s), b.baro(s))


if __name__ == '__main__':
    unittest.main()
