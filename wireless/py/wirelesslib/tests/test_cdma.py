# -*- coding: utf-8 -*-
"""cdma 모듈의 증인 시험.

CDMA 의 주장은 셋이다. "직교 부호로 사용자를 가른다", "역확산이
처리 이득만큼 SNR 을 올린다", "다중경로는 잡음이 아니라 이득이다".
그리고 그 셋을 떠받치는 조건 하나 — 전력 제어. 각각을 확인한다.
"""
import math
import unittest

from wirelesslib import cdma, spread


class TestForwardLink(unittest.TestCase):
    def test_pilot_is_walsh_zero(self):
        self.assertEqual(cdma.CHANNELS['pilot'], 0)
        self.assertEqual(spread.walsh(64, 0), [1] * 64)

    def test_orthogonal_users_do_not_interfere(self):
        """잡음도 다중경로도 없으면 64명이 서로 전혀 안 밟는다."""
        for nusers in (1, 4, 16, 63):
            got = cdma.forward_roundtrip(nusers, 20, seed=3)
            self.assertEqual(got, 0, '%d명' % nusers)

    def test_despreading_gain_matches_processing_gain(self):
        """역확산 뒤 SNR 은 확산율만큼 오른다 — 21 dB 의 실체."""
        for sf in (16, 64, 128):
            got = cdma.despread_gain_db(sf, chips=200000, seed=11)
            want = spread.processing_gain_db(sf)
            self.assertLess(abs(got - want), 0.6,
                            'SF=%d got=%.2f want=%.2f'
                            % (sf, got, want))

    def test_more_users_costs_snr(self):
        a = cdma.multiuser_sinr_db(4, seed=5)
        b = cdma.multiuser_sinr_db(32, seed=5)
        self.assertGreater(a, b)


class TestRake(unittest.TestCase):
    def test_rake_beats_single_finger(self):
        """다중경로를 모으면 더 낫다 — RAKE 라는 이름의 뜻."""
        one = cdma.rake_ber(fingers=1, frames=60, ebn0_db=4.0, seed=7)
        two = cdma.rake_ber(fingers=2, frames=60, ebn0_db=4.0, seed=7)
        self.assertLess(two, one)

    def test_third_finger_helps_on_three_paths(self):
        two = cdma.rake_ber(fingers=2, frames=60, ebn0_db=4.0, seed=9,
                            paths=3)
        three = cdma.rake_ber(fingers=3, frames=60, ebn0_db=4.0,
                              seed=9, paths=3)
        self.assertLessEqual(three, two)

    def test_more_fingers_than_paths_does_not_hurt(self):
        a = cdma.rake_ber(fingers=2, frames=40, ebn0_db=6.0, seed=13,
                          paths=2)
        b = cdma.rake_ber(fingers=4, frames=40, ebn0_db=6.0, seed=13,
                          paths=2)
        self.assertLessEqual(b, a + 0.02)


class TestPowerControl(unittest.TestCase):
    def test_near_far_breaks_the_far_user(self):
        """전력 제어가 없으면 가까운 단말이 먼 단말을 묻어 버린다.

        켜면 둘이 같은 세기로 도착해 정확히 0 dB — 대등해진다.
        """
        off = cdma.near_far_sinr_db(control=False)
        on = cdma.near_far_sinr_db(control=True)
        self.assertLess(off, -30.0)
        self.assertAlmostEqual(on, 0.0, places=9)

    def test_loop_converges_to_target(self):
        hist = cdma.power_control_loop(target_db=7.0, steps=200,
                                       seed=17)
        tail = hist[-50:]
        mean = sum(tail) / len(tail)
        self.assertLess(abs(mean - 7.0), 1.0)

    def test_ripple_grows_with_fading_speed(self):
        """걸음 크기가 쫓을 수 있는 속도를 정한다.

        페이딩이 느리면 목표 둘레에 붙어 있고, 빨라지면 고리가 못
        따라가 떨림이 커진다. 이 맞바꿈이 800 Hz 라는 숫자의 이유다.
        """
        slow = cdma.power_control_loop(7.0, 300, step_db=1.0, seed=19,
                                       fade_db=0.5)[-100:]
        fast = cdma.power_control_loop(7.0, 300, step_db=1.0, seed=19,
                                       fade_db=6.0)[-100:]
        self.assertLess(max(slow) - min(slow), 6.0)
        self.assertGreater(max(fast) - min(fast),
                           max(slow) - min(slow))


class TestCapacity(unittest.TestCase):
    def test_gilhousen_worked_value(self):
        """W/R=128, Eb/N0=7 dB, 음성활동 0.4, 타 셀 0.6 → 40명 남짓."""
        n = cdma.pole_capacity(128.0, 7.0, activity=0.4, f_other=0.6)
        self.assertAlmostEqual(n, 40.9, delta=0.5)

    def test_sectoring_multiplies(self):
        a = cdma.pole_capacity(128.0, 7.0, sectors=1.0)
        b = cdma.pole_capacity(128.0, 7.0, sectors=2.55)
        self.assertAlmostEqual((b - 1) / (a - 1), 2.55, places=6)

    def test_voice_activity_helps(self):
        full = cdma.pole_capacity(128.0, 7.0, activity=1.0)
        half = cdma.pole_capacity(128.0, 7.0, activity=0.5)
        self.assertGreater(half, full)

    def test_better_coding_helps(self):
        a = cdma.pole_capacity(128.0, 7.0)
        b = cdma.pole_capacity(128.0, 4.0)
        self.assertGreater(b, a)

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            cdma.pole_capacity(128.0, 7.0, activity=0.0)


if __name__ == '__main__':
    unittest.main()
