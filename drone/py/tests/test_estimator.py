# -*- coding: utf-8 -*-
"""estimator 시험 — 상보 필터(T23), 칼만 이득(T24), 칼만 필터(T25)."""
import math
import unittest

from droneshow import estimator as E
from droneshow import quat as Q
from droneshow import rng


def rms(xs):
    return math.sqrt(sum(x * x for x in xs) / len(xs))


class Complementary1D(unittest.TestCase):
    """T23 — 자이로 적분은 표류하고 가속도계는 떨린다. 섞으면 둘보다
    낫다."""

    def run_axis(self, alpha, bias=0.02, sg=0.01, sa=0.05, secs=60.0,
                 dt=0.004, seed=7):
        g = rng.Rng(seed)
        th = est = gy_only = 0.0
        e_c, e_g, e_a = [], [], []
        for k in range(round(secs / dt)):
            t = k * dt
            rate = 0.5 * math.cos(0.5 * t)       # 참 각속도
            th_next = math.sin(0.5 * (t + dt))   # 참 각
            gyro = rate + bias + sg * g.normal()
            acc = th_next + sa * g.normal()
            est = E.complementary_1d(est, gyro, acc, alpha, dt)
            gy_only += gyro * dt
            th = th_next
            e_c.append(est - th)
            e_g.append(gy_only - th)
            e_a.append(acc - th)
        return rms(e_c), rms(e_g), rms(e_a)

    def test_beats_both_sensors(self):
        c, gy, ac = self.run_axis(0.98)
        self.assertLess(c, gy)
        self.assertLess(c, ac)

    def test_bias_error_formula(self):
        # 잡음이 없으면 정상상태 오차 = α·b·dt/(1−α) (유한하다)
        b, a, dt = 0.02, 0.98, 0.004
        est = 0.0
        for _ in range(20000):
            est = E.complementary_1d(est, b, 0.0, a, dt)
        self.assertAlmostEqual(est, a * b * dt / (1 - a), places=12)

    def test_gyro_alone_drifts_linearly(self):
        _c, gy, _a = self.run_axis(0.98, sg=0.0, sa=0.0, secs=10.0)
        _c, gy2, _a = self.run_axis(0.98, sg=0.0, sa=0.0, secs=20.0)
        self.assertAlmostEqual(gy2 / gy, 2.0, delta=0.05)


class Gain(unittest.TestCase):
    """T24 — 사후 분산 (1−K)²P + K²R 은 K = P/(P+R) 에서 가장 작다."""

    def test_gain_minimises_variance(self):
        for p, r in ((1.0, 1.0), (4.0, 0.5), (0.1, 3.0)):
            k = E.kalman_1d_gain(p, r)
            best = E.posterior_var(p, r, k)
            for dk in (-0.1, -0.01, 0.01, 0.1):
                self.assertGreater(E.posterior_var(p, r, k + dk), best)
            self.assertAlmostEqual(best, p * r / (p + r), places=14)

    def test_extremes(self):
        # 예측을 믿음
        self.assertEqual(E.kalman_1d_gain(0.0, 1.0), 0.0)
        # 측정을 믿음
        self.assertEqual(E.kalman_1d_gain(1.0, 0.0), 1.0)


class Kalman(unittest.TestCase):
    """T25 — 상수 속도 모델의 칼만 필터. 혁신(잔차)은 흰 잡음이어야
    한다."""

    def run_track(self, seed=11, n=4000, dt=0.1, q=0.01, r=0.25):
        g = rng.Rng(seed)
        kf = E.Kalman1D(q, r)
        x, v = 0.0, 1.0
        nis, inn, err = [], [], []
        for _ in range(n):
            v += math.sqrt(q * dt) * g.normal()
            x += v * dt
            z = x + math.sqrt(r) * g.normal()
            kf.predict(dt)
            y, s = kf.update(z)
            inn.append(y)
            nis.append(y * y / s)
            err.append(kf.x[0] - x)
        return nis, inn, err

    def test_innovation_consistent_and_white(self):
        nis, inn, _e = self.run_track()
        tail = nis[200:]
        self.assertAlmostEqual(sum(tail) / len(tail), 1.0, delta=0.1)
        m = inn[200:]
        mu = sum(m) / len(m)
        c0 = sum((a - mu) ** 2 for a in m)
        c1 = sum((a - mu) * (b - mu) for a, b in zip(m, m[1:]))
        self.assertLess(abs(c1 / c0), 0.06)

    def test_filter_beats_raw_measurement(self):
        _n, _i, err = self.run_track()
        self.assertLess(rms(err[200:]), math.sqrt(0.25))


class Attitude(unittest.TestCase):
    """쿼터니언 상보 필터 — 자이로 바이어스가 있어도 기울기가
    붙잡힌다."""

    def test_tilt_error_bounded_with_bias(self):
        truth = Q.from_euler(0.2, -0.1, 0.0)
        est_c = E.Complementary(k_c=1.0)
        est_g = E.Complementary(k_c=0.0)
        acc = Q.rotate(Q.conj(truth), [0.0, 0.0, 9.81])   # 몸체 비력
        gyro = [0.02, -0.01, 0.0]                          # 바이어스만
        for _ in range(5000):
            est_c.update(gyro, acc, 0.004)
            est_g.update(gyro, acc, 0.004)
        def tilt_err(q):
            a = Q.rotate(q, [0.0, 0.0, 1.0])
            b = Q.rotate(truth, [0.0, 0.0, 1.0])
            return math.acos(min(1.0, sum(x * y for x, y in zip(a, b))))
        self.assertLess(tilt_err(est_c.q), math.radians(2.0))
        self.assertGreater(tilt_err(est_g.q), math.radians(10.0))


if __name__ == '__main__':
    unittest.main()
