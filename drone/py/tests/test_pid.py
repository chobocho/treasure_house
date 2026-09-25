# -*- coding: utf-8 -*-
"""pid 시험 — PID 한 개와 2차 계의 공식 (T14–T17, T22 의 증인)."""
import math
import unittest

from droneshow import pid
from droneshow import rigidbody as RB


def run_pd_step(kp, kd, secs=10.0, dt=1e-3):
    """x'' = kp(1 − x) − kd x' 의 계단 응답을 RK4 로. 최댓값을
    돌려준다."""
    f = lambda s: [s[1], kp * (1 - s[0]) - kd * s[1]]
    s, top = [0.0, 0.0], 0.0
    for _ in range(round(secs / dt)):
        s = RB.rk4(f, s, dt)
        top = max(top, s[0])
    return top, s


class Scalar(unittest.TestCase):
    def test_p_only(self):
        c = pid.PID(2.0, 0.0, 0.0)
        self.assertEqual(c.update(0.5, 0.0, 0.01), 1.0)

    def test_integral_accumulates_and_clamps(self):
        c = pid.PID(0.0, 1.0, 0.0, i_max=0.25)
        for _ in range(10):
            u = c.update(1.0, 0.0, 0.1)
        self.assertAlmostEqual(u, 0.25, places=15)

    def test_derivative_on_measurement(self):
        # 목표가 튀어도 D 는 튀지 않는다 — 측정값의 변화만 본다
        c = pid.PID(0.0, 0.0, 1.0)
        self.assertEqual(c.update(0.0, 0.0, 0.1), 0.0)   # 첫 호출
        self.assertEqual(c.update(5.0, 0.0, 0.1), 0.0)   # 목표만 바뀜
        self.assertAlmostEqual(c.update(5.0, 0.2, 0.1), -2.0, places=12)

    def test_derivative_filter(self):
        c = pid.PID(0.0, 0.0, 1.0, tau_d=0.1)
        c.update(0.0, 0.0, 0.1)
        u = c.update(0.0, 0.2, 0.1)
        self.assertAlmostEqual(u, -2.0 * 0.1 / 0.2, places=12)

    def test_reset(self):
        c = pid.PID(1.0, 1.0, 1.0)
        c.update(1.0, 0.0, 0.1)
        c.reset()
        self.assertEqual(c.update(0.0, 0.0, 0.1), 0.0)

    def test_vector(self):
        c = pid.VecPID([1.0, 2.0, 3.0], [0.0] * 3, [0.0] * 3)
        self.assertEqual(c.update([1.0, 1.0, 1.0], [0.0] * 3, 0.01),
                         [1.0, 2.0, 3.0])


class SecondOrder(unittest.TestCase):
    """T14 — s² + kd s + kp: ζ = kd/(2√kp), 초과량 e^(−πζ/√(1−ζ²))."""

    def test_zeta_and_wn(self):
        z, wn = pid.second_order(4.0, 2.0)
        self.assertEqual((z, wn), (0.5, 2.0))

    def test_overshoot_matches_formula(self):
        for kp, kd in ((4.0, 2.0), (9.0, 1.8), (25.0, 3.0)):
            top, _s = run_pd_step(kp, kd)
            z, _wn = pid.second_order(kp, kd)
            self.assertAlmostEqual(top - 1.0, pid.overshoot(z),
                                   places=5)

    def test_critical_damping_no_overshoot(self):
        top, _s = run_pd_step(4.0, 4.0)
        self.assertLessEqual(top, 1.0 + 1e-12)
        self.assertEqual(pid.overshoot(1.0), 0.0)


class Integral(unittest.TestCase):
    """T15 — 일정한 외란 d 아래 PD 는 d/kp 만큼 모자라고, I 가
    지운다."""

    def settle(self, ki, d=-0.5, secs=40.0, dt=1e-3, umax=None):
        kp, kd = 4.0, 3.0
        f = lambda s: [s[1], s[3] + d, 1.0 - s[0], 0.0]
        s = [0.0, 0.0, 0.0, 0.0]            # x, x', ∫e, u
        top = 0.0
        for _ in range(round(secs / dt)):
            u = kp * (1 - s[0]) - kd * s[1] + ki * s[2]
            if umax is not None:
                u = max(-umax, min(umax, u))
            s[3] = u
            s = RB.rk4(f, s, dt)
            top = max(top, s[0])
        return s[0], top

    def test_pd_leaves_offset(self):
        x, _t = self.settle(0.0)
        self.assertAlmostEqual(x, 1.0 - 0.5 / 4.0, places=6)

    def test_pid_removes_offset(self):
        x, _t = self.settle(2.0)
        self.assertAlmostEqual(x, 1.0, places=6)

    def test_windup_overshoot(self):
        # 출력이 포화되면 적분이 쌓여 크게 넘친다(되감기 없음)
        _x, free = self.settle(2.0)
        _x, sat = self.settle(2.0, umax=0.8)
        self.assertGreater(sat - 1.0, 2 * (free - 1.0))


class Routh(unittest.TestCase):
    """T16 — s³ + a2 s² + a1 s + a0 은 모두 양수이고 a2·a1 > a0 일 때만
    안정."""

    def test_rule(self):
        self.assertTrue(pid.routh3(2.0, 3.0, 5.0))
        self.assertFalse(pid.routh3(2.0, 3.0, 7.0))
        self.assertFalse(pid.routh3(-1.0, 3.0, 1.0))

    def response(self, ki, secs=60.0, dt=2e-3):
        # 이중 적분기 + PID: s³ + kd s² + kp s + ki
        kp, kd = 3.0, 2.0
        f = lambda s: [s[1], kp * (-s[0]) - kd * s[1] - ki * s[2], s[0]]
        s = [1.0, 0.0, 0.0]
        big = 0.0
        for k in range(round(secs / dt)):
            s = RB.rk4(f, s, dt)
            if k * dt > secs - 5:
                big = max(big, abs(s[0]))
        return big

    def test_gain_scan_crosses_exactly_at_bound(self):
        # 경계 kd·kp = 6 — 바로 아래는 줄고, 바로 위는 커진다
        self.assertLess(self.response(5.5), 0.5)
        self.assertGreater(self.response(6.5), 1.0)


class Cascade(unittest.TestCase):
    """T17 — 안쪽 루프가 b, 바깥이 k. s² + b s + b k 의 느린 극은 −k 에
    가깝다."""

    def test_slow_pole_approaches_outer_gain(self):
        k = 1.0
        for ratio, tol in ((10.0, 0.13), (100.0, 0.011)):
            p = pid.cascade_poles(k, ratio * k)
            slow = max(p)
            self.assertLess(abs(slow + k) / k, tol)

    def test_equal_speeds_overshoot(self):
        # 안쪽과 바깥이 같은 빠르기면 ζ = 0.5 — 16 % 넘친다
        z, _wn = pid.second_order(1.0, 1.0)
        self.assertAlmostEqual(z, 0.5)
        self.assertAlmostEqual(pid.overshoot(z), 0.163, places=3)


class Filter(unittest.TestCase):
    """T22 — D항은 주파수 ω 에 비례해 키우고, 1차 필터가 1/√(1+(ωτ)²) 로
    누른다."""

    def amplitude(self, w, tau, dt=1e-4, secs=4.0):
        y, top = 0.0, 0.0
        n = round(secs / dt)
        for k in range(n):
            u = math.sin(w * k * dt)
            y += (u - y) * dt / (tau + dt)
            if k > n // 2:
                top = max(top, abs(y))
        return top

    def test_lowpass_gain(self):
        tau = 0.01
        for w in (10.0, 100.0, 1000.0):
            want = pid.lowpass_gain(w, tau)
            self.assertAlmostEqual(self.amplitude(w, tau), want,
                                   delta=2e-3)

    def test_derivative_gain_grows_with_frequency(self):
        self.assertEqual(pid.derivative_gain(100.0), 100.0)
        self.assertAlmostEqual(
            pid.derivative_gain(100.0) * pid.lowpass_gain(100.0, 0.01),
            100.0 / math.sqrt(2.0), places=12)


if __name__ == '__main__':
    unittest.main()
