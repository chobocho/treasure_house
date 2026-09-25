# -*- coding: utf-8 -*-
"""ex/ 예제 시험 — 덱이 인용하는 작은 프로그램들이 식대로 도는가."""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'py'))

import battery_time  # noqa: E402
import gps_trilateration as GT  # noqa: E402
import hover_power  # noqa: E402
import mavlink_parse as MP  # noqa: E402
import routh  # noqa: E402
from droneshow import motor, params  # noqa: E402


class Mavlink(unittest.TestCase):
    def test_crc_check_value(self):
        # CRC-16/MCRF4XX 의 표준 검사값: '123456789' → 0x6F91
        self.assertEqual(MP.x25(b'123456789'), 0x6F91)

    def test_crc_extra_of_heartbeat(self):
        # C 라이브러리 minimal.h 의 MAVLINK_MESSAGE_CRCS 에 적힌 50
        self.assertEqual(MP.EXTRA, 50)

    def test_roundtrip(self):
        f = MP.pack(7, 1, 1, (0, 2, 12, 0x81, 4, 3))
        self.assertEqual(f[0], 0xFD)
        want = (7, 1, 1, (0, 2, 12, 0x81, 4, 3))
        self.assertEqual(MP.unpack(f), want)

    def test_trailing_zeros_truncated(self):
        f = MP.pack(0, 1, 1, (0, 2, 12, 0, 0, 0))
        self.assertEqual(f[1], 6)                 # 9 → 6 바이트
        self.assertEqual(MP.unpack(f)[3], (0, 2, 12, 0, 0, 0))

    def test_bit_flip_detected(self):
        f = bytearray(MP.pack(7, 1, 1, (0, 2, 12, 0x81, 4, 3)))
        f[12] ^= 1
        with self.assertRaises(ValueError):
            MP.unpack(bytes(f))

    def test_field_order_matters(self):
        # 전송 순서를 XML 순서로 잘못 두면 CRC_EXTRA 가 달라진다
        xml = [MP.FIELDS[1], MP.FIELDS[2], MP.FIELDS[3], MP.FIELDS[0],
               MP.FIELDS[4], MP.FIELDS[5]]
        self.assertNotEqual(MP.crc_extra('HEARTBEAT', xml), 50)


class Hover(unittest.TestCase):
    """T1 — 식으로 푼 값과 motor.py 가 같다."""

    def test_matches_motor(self):
        p = params.load()
        self.assertAlmostEqual(hover_power.P1, motor.ideal_power(
            hover_power.T, p['rho'], hover_power.A), places=12)
        self.assertAlmostEqual(hover_power.v * hover_power.T,
                               hover_power.P1, places=12)


class Battery(unittest.TestCase):
    """T2 — 적분한 기계 일률 / 효율 ≈ 성능지수로 줄인 모멘텀 일률."""

    def test_integrated_power_is_steady(self):
        p = params.load()
        pm = battery_time.mech_power_hover(p, secs=2.0)
        oh = params.derived(p)['omega_hover']
        self.assertAlmostEqual(pm, 4 * p['kQ'] * oh ** 3, places=6)

    def test_implied_figure_of_merit(self):
        # 모멘텀 이상 일률 / 모델의 기계 일률 = 이 모델의 성능 지수
        p = params.load()
        d = params.derived(p)
        ideal = 4 * motor.ideal_power(d['T_hover'], p['rho'], d['area'])
        mech = 4 * p['kQ'] * d['omega_hover'] ** 3
        # params.tsv 의 kQ 는 이 값이 표의 fm 과 맞도록 골랐다
        self.assertAlmostEqual(ideal / mech, p['fm'], delta=0.005)


class Routh(unittest.TestCase):
    """T16 — 경계 kd·kp 를 넘으면 흔들림이 커진다."""

    def test_swing_on_both_sides(self):
        self.assertLess(routh.swing(3.0, 2.0, 5.5), 0.5)
        self.assertGreater(routh.swing(3.0, 2.0, 6.5), 1.0)


class Gnss(unittest.TestCase):
    """T26 — 의사거리로 위치와 시계 오차를 되찾는다."""

    def test_recovers_position(self):
        truth, bias = [1200.0, -800.0, 300.0], 45_000.0
        sv = GT.sats()
        rho = [math.dist(s, truth) + bias for s in sv]
        x, hist = GT.solve(sv, rho)
        for a, b in zip(x, truth + [bias]):
            self.assertAlmostEqual(a, b, places=4)
        self.assertLess(hist[-1][1], 1e-6)

    def test_four_satellites_enough(self):
        truth, bias = [10.0, 20.0, -5.0], 300.0
        sv = GT.sats()[:4]
        rho = [math.dist(s, truth) + bias for s in sv]
        x, _h = GT.solve(sv, rho)
        self.assertAlmostEqual(x[3], bias, places=3)

    def test_newton_converges_fast(self):
        # 가까워지면 잔차가 한 걸음에 제곱으로 준다
        truth, bias = [1200.0, -800.0, 300.0], 45_000.0
        sv = GT.sats()
        rho = [math.dist(s, truth) + bias for s in sv]
        _x, hist = GT.solve(sv, rho)
        res = [h[1] for h in hist]
        self.assertLess(res[2], 1e-2 * res[1])


if __name__ == '__main__':
    unittest.main()
