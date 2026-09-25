# -*- coding: utf-8 -*-
"""motor 시험 — 모멘텀 이론(T1), 비행시간(T2), 1차 지연(T13)."""
import math
import unittest

from droneshow import motor, params


class Momentum(unittest.TestCase):
    def setUp(self):
        self.p = params.load()

    def test_ideal_power_formula(self):
        # T1: P = T^(3/2) / √(2ρA), v = √(T / (2ρA)), P = T·v
        t, rho, area = 1.2, 1.225, math.pi * 0.0635 ** 2
        v = motor.induced_velocity(t, rho, area)
        self.assertAlmostEqual(motor.ideal_power(t, rho, area), t * v,
                               places=12)
        self.assertAlmostEqual(v, math.sqrt(t / (2 * rho * area)),
                               places=12)

    def test_power_grows_as_three_halves(self):
        a = motor.ideal_power(1.0, 1.225, 0.01)
        b = motor.ideal_power(4.0, 1.225, 0.01)
        self.assertAlmostEqual(b / a, 8.0, places=12)

    def test_bigger_disc_less_power(self):
        a = motor.ideal_power(1.0, 1.225, 0.01)
        b = motor.ideal_power(1.0, 1.225, 0.04)
        self.assertAlmostEqual(a / b, 2.0, places=12)

    def test_hover_electric_power(self):
        pw = motor.hover_power(self.p)
        t = self.p['m'] * self.p['g'] / 4
        area = math.pi * self.p['r_prop'] ** 2
        want = 4 * motor.ideal_power(t, self.p['rho'], area) / (
            self.p['fm'] * self.p['eta_e'])
        self.assertAlmostEqual(pw, want, places=12)


class FlightTime(unittest.TestCase):
    def setUp(self):
        self.p = params.load()

    def test_time_formula(self):
        # T2: t = C·V·η / P (C 는 쓸 수 있는 용량)
        p = self.p
        e_j = p['batt_Ah'] * 3600 * p['batt_V'] * p['batt_use']
        want = e_j / (motor.hover_power(p) + p['led_W'])
        self.assertAlmostEqual(motor.flight_time(p), want, places=9)

    def test_half_mass_is_not_double_time(self):
        # 호버 전력은 m^(3/2) 에 비례 — 무게를 반으로 줄이면
        # 전력은 2^(3/2) 배 줄지만 LED 전력은 그대로다
        p = dict(self.p, led_W=0.0)
        q = dict(p, m=p['m'] / 2)
        r = motor.flight_time(q) / motor.flight_time(p)
        self.assertAlmostEqual(r, 2 ** 1.5, places=12)
        p2 = dict(self.p)
        q2 = dict(p2, m=p2['m'] / 2)
        r2 = motor.flight_time(q2) / motor.flight_time(p2)
        self.assertLess(r2, 2 ** 1.5)


class Lag(unittest.TestCase):
    def test_step_response_matches_exponential(self):
        # T13: τ Ω' = Ω_cmd − Ω 의 계단 응답은 1 − e^(−t/τ)
        tau, dt = 0.03, 0.0005
        w = 0.0
        for k in range(1, 201):
            w = motor.lag_exact(w, 1.0, tau, dt)
            self.assertAlmostEqual(w, 1 - math.exp(-k * dt / tau),
                                   places=12)

    def test_time_constant_is_63_percent(self):
        self.assertAlmostEqual(motor.lag_exact(0.0, 1.0, 0.03, 0.03),
                               1 - math.exp(-1), places=15)

    def test_clamp(self):
        p = params.load()
        self.assertEqual(motor.clamp_omega(5000.0, p), 2000.0)
        self.assertEqual(motor.clamp_omega(-3.0, p), 200.0)
        self.assertAlmostEqual(
            motor.omega_for_thrust(1.2e-6 * 1000.0 ** 2, p), 1000.0,
            places=9)


if __name__ == '__main__':
    unittest.main()
