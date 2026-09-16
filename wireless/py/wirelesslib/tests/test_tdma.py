# -*- coding: utf-8 -*-
"""tdma 모듈의 증인 시험.

GSM 의 시간축은 분수로 딱 떨어지게 설계돼 있다. 1625/6 kbit/s 라는
변조율 하나에서 비트 길이·슬롯·프레임·멀티프레임·하이퍼프레임이 전부
유리수로 따라 나온다. 어림수로 적으면 어디선가 반드시 어긋나므로,
시험은 분수 그대로 확인한다.

  · 변조율 1625/6 kbit/s, 비트 길이 48/13 μs
  · 슬롯 156.25 비트 = 15/26 ms, 프레임 8슬롯 = 60/13 ms
  · 26 멀티프레임 = 120 ms 정확히, 51 멀티프레임 = 3060/13 ms
  · 하이퍼프레임 = 2,715,648 프레임 = 3시간 28분 53.76초
  · 버스트 다섯 종류의 칸이 모두 156.25 비트로 맞는가
  · 타이밍 어드밴스 한 걸음이 553 m, 최대 63 이면 35 km
  · GMSK 가 MSK 보다 대역 밖 전력이 작은가
"""
import math
import unittest

from fractions import Fraction

from wirelesslib import tdma


class TestTiming(unittest.TestCase):
    def test_modulation_rate(self):
        self.assertEqual(tdma.RATE_KBPS, Fraction(1625, 6))

    def test_bit_period(self):
        self.assertEqual(tdma.BIT_US, Fraction(48, 13))
        self.assertAlmostEqual(float(tdma.BIT_US), 3.6923, places=4)

    def test_slot_is_156_25_bits(self):
        self.assertEqual(tdma.SLOT_BITS, Fraction(625, 4))
        self.assertEqual(tdma.SLOT_MS, Fraction(15, 26))

    def test_frame_is_eight_slots(self):
        self.assertEqual(tdma.FRAME_MS, 8 * tdma.SLOT_MS)
        self.assertEqual(tdma.FRAME_MS, Fraction(60, 13))
        self.assertAlmostEqual(float(tdma.FRAME_MS), 4.6154, places=4)

    def test_traffic_multiframe_is_exactly_120ms(self):
        """26 프레임 × 60/13 ms = 120 ms — 13 이 딱 나눠떨어진다."""
        self.assertEqual(tdma.multiframe_ms(26), 120)

    def test_control_multiframe(self):
        self.assertEqual(tdma.multiframe_ms(51), Fraction(3060, 13))

    def test_superframe(self):
        self.assertEqual(tdma.SUPERFRAME_FRAMES, 26 * 51)
        self.assertEqual(tdma.superframe_ms(), 6120)

    def test_hyperframe(self):
        """2048 슈퍼프레임 = 3시간 28분 53.76초.

        A5 의 프레임 번호가 한 바퀴 도는 주기다.
        """
        self.assertEqual(tdma.HYPERFRAME_FRAMES, 2715648)
        s = tdma.hyperframe_seconds()
        self.assertEqual(s, Fraction(1253376, 100))
        h, m, sec = tdma.hyperframe_hms()
        self.assertEqual((h, m), (3, 28))
        self.assertAlmostEqual(sec, 53.76, places=6)

    def test_frame_number_wraps(self):
        self.assertEqual(tdma.next_fn(tdma.HYPERFRAME_FRAMES - 1), 0)


class TestBursts(unittest.TestCase):
    def test_every_burst_is_156_25_bits(self):
        for kind in tdma.BURSTS:
            total = sum(n for _name, n in tdma.burst_fields(kind))
            self.assertEqual(Fraction(total), tdma.SLOT_BITS, kind)

    def test_normal_burst_layout(self):
        f = dict(tdma.burst_fields('normal'))
        self.assertEqual(f['데이터1'], 57)
        self.assertEqual(f['데이터2'], 57)
        self.assertEqual(f['훈련열'], 26)
        self.assertEqual(f['가드'], Fraction(33, 4))

    def test_access_burst_has_long_guard(self):
        """임의접속 버스트는 거리를 모르는 채로 보내므로 가드가 길다."""
        f = dict(tdma.burst_fields('access'))
        self.assertGreater(f['가드'], dict(
            tdma.burst_fields('normal'))['가드'])

    def test_unknown_burst(self):
        with self.assertRaises(ValueError):
            tdma.burst_fields('magic')


class TestTimingAdvance(unittest.TestCase):
    def test_one_step_is_about_553m(self):
        """한 비트 왕복이 한 걸음 — 빛이 3.69 μs 에 가는 거리의 절반."""
        self.assertAlmostEqual(tdma.ta_distance_m(1), 553.46, places=2)

    def test_max_ta_is_35km(self):
        """TA 는 6비트(0~63)다.

        그래서 GSM 셀 반지름의 한계가 35 km 다.
        """
        self.assertAlmostEqual(tdma.ta_distance_m(63) / 1000.0, 34.87,
                               places=2)

    def test_roundtrip(self):
        for d in (0.0, 1000.0, 20000.0, 34000.0):
            ta = tdma.ta_from_distance(d)
            self.assertLessEqual(tdma.ta_distance_m(ta), d + 1e-6)

    def test_too_far_rejected(self):
        with self.assertRaises(ValueError):
            tdma.ta_from_distance(60000.0)


class TestGMSK(unittest.TestCase):
    def test_msk_phase_steps_by_quarter_turn(self):
        """MSK 의 위상은 비트마다 정확히 ±π/2 만큼 움직인다."""
        bits = [1, 0, 0, 1, 1, 1, 0]
        ph = tdma.msk_phase(bits, sps=8)
        for i in range(len(bits)):
            step = ph[(i + 1) * 8] - ph[i * 8]
            self.assertAlmostEqual(abs(step), math.pi / 2, places=9)

    def test_gaussian_pulse_is_normalised(self):
        for bt in (0.3, 0.5):
            g = tdma.gaussian_pulse(bt, sps=8, span=4)
            self.assertAlmostEqual(sum(g), 1.0, places=9)

    def test_smaller_bt_is_wider_in_time(self):
        """BT 가 작으면 시간 영역에서 길어진다 — 그 대가가 ISI 다."""
        a = tdma.pulse_width(tdma.gaussian_pulse(0.3, 8, 6))
        b = tdma.pulse_width(tdma.gaussian_pulse(0.9, 8, 6))
        self.assertGreater(a, b)

    def test_gmsk_is_narrower_than_msk(self):
        """GSM 이 BT=0.3 을 고른 이유 — 이웃 채널로 새는 전력이 준다."""
        msk = tdma.out_of_band_db(bt=None, seed=3)
        gmsk = tdma.out_of_band_db(bt=0.3, seed=3)
        self.assertLess(gmsk, msk - 3.0)

    def test_constant_envelope(self):
        """GMSK 는 포락선이 일정하다 — 증폭기를 포화시켜 써도 된다."""
        x = tdma.gmsk_modulate([1, 0, 1, 1, 0, 0, 1], bt=0.3, sps=8)
        for v in x:
            self.assertAlmostEqual(abs(v), 1.0, places=9)


if __name__ == '__main__':
    unittest.main()
