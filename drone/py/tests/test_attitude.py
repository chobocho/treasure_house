# -*- coding: utf-8 -*-
"""attitude 시험 — 추력 방향에서 자세로(T12), 쿼터니언 P
법칙(T18·T19)."""
import math
import unittest

from droneshow import attitude as A
from droneshow import quat as Q
from droneshow import rigidbody as RB
from droneshow import vec3 as V


def tilt_of(q):
    """몸체 z 축과 세계 z 축 사이의 각."""
    z = Q.rotate(q, [0.0, 0.0, 1.0])
    return math.acos(max(-1.0, min(1.0, z[2])))


class Desired(unittest.TestCase):
    def test_level_with_yaw(self):
        q = A.desired_attitude([0.0, 0.0, 9.81], 0.5)
        want = Q.from_axis_angle([0.0, 0.0, 1.0], 0.5)
        for a, b in zip(Q.canonical(q), want):
            self.assertAlmostEqual(a, b, places=14)

    def test_thrust_axis_follows_force(self):
        f = [1.0, -2.0, 9.0]
        q = A.desired_attitude(f, 1.2)
        z = Q.rotate(q, [0.0, 0.0, 1.0])
        for a, b in zip(z, V.normalize(f)):
            self.assertAlmostEqual(a, b, places=14)

    def test_heading_is_yaw(self):
        # 몸체 x 축을 수평면에 내린 방향이 요 각이다
        q = A.desired_attitude([0.5, 0.3, 9.0], -0.7)
        x = Q.rotate(q, [1.0, 0.0, 0.0])
        self.assertAlmostEqual(math.atan2(x[1], x[0]), -0.7, places=2)
        y = Q.rotate(q, [0.0, 1.0, 0.0])
        c = [math.cos(-0.7), math.sin(-0.7), 0.0]
        self.assertAlmostEqual(V.dot(y, c), 0.0, places=14)


class Flatness(unittest.TestCase):
    """T12 — 가가속도(jerk)로 몸체 각속도를 거꾸로 계산한다."""

    def traj(self, t):
        # 반지름 2 m, 각속도 0.8 rad/s 의 원 + 천천히 도는 요
        w, r = 0.8, 2.0
        a = [-r * w * w * math.cos(w * t), -r * w * w * math.sin(w * t),
             0.0]
        j = [r * w ** 3 * math.sin(w * t),
             -r * w ** 3 * math.cos(w * t), 0.0]
        return a, j, 0.3 * t, 0.3

    def test_rates_from_jerk_match_attitude_derivative(self):
        g, h = 9.81, 1e-5
        for t in (0.0, 1.0, 2.5):
            a, j, psi, dpsi = self.traj(t)
            w = A.flat_rates(a, j, psi, dpsi, g)
            a0, _j, p0, _d = self.traj(t - h)
            a1, _j, p1, _d = self.traj(t + h)
            q0 = A.desired_attitude(V.add(a0, [0, 0, g]), p0)
            q1 = A.desired_attitude(V.add(a1, [0, 0, g]), p1)
            dq = Q.canonical(Q.mul(Q.conj(q0), q1))
            w_num = [c / h for c in dq[1:]]      # 2·(벡터부)/(2h)
            for k in range(3):
                self.assertAlmostEqual(w[k], w_num[k], places=6)

    def test_thrust_from_acceleration(self):
        a, _j, _p, _d = self.traj(0.4)
        f = A.flat_thrust(0.5, a, 9.81)
        self.assertAlmostEqual(f, 0.5 * V.norm(V.add(a, [0, 0, 9.81])),
                               places=14)


class AttitudeLaw(unittest.TestCase):
    def test_full_weight_is_plain_law(self):
        # yaw_w = 1 이면 ω = 2k·sign(q_e,w)·q_e,xyz 그대로
        q = Q.from_euler(0.2, -0.1, 0.4)
        qd = Q.from_euler(-0.3, 0.2, -0.6)
        k = [8.0, 8.0, 8.0]
        w = A.att_law(q, qd, k, 1.0)
        qe = Q.canonical(Q.mul(Q.conj(q), qd))
        for i in range(3):
            self.assertAlmostEqual(w[i], 2 * k[i] * qe[i + 1],
                                   places=12)

    def test_sign_picks_short_way(self):
        # q_d 와 −q_d 는 같은 목표 — 같은 명령을 내야 한다
        q = Q.from_euler(0.0, 0.0, 0.0)
        qd = Q.from_axis_angle([0.0, 0.0, 1.0], 0.5)
        a = A.att_law(q, qd, [4.0] * 3, 1.0)
        b = A.att_law(q, [-c for c in qd], [4.0] * 3, 1.0)
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, places=14)

    def kinematic(self, q0, qd, k, yaw_w, secs, dt=1e-3):
        """각속도가 명령대로 곧장 나온다고 본 모델 — RK4 로 푼다."""
        f = lambda q: Q.qdot(q, A.att_law(q, qd, [k, k, k], yaw_w))
        q, out = list(q0), []
        for _ in range(round(secs / dt)):
            q = Q.normalize(RB.rk4(f, q, dt))
            out.append(q)
        return out

    def test_angle_decreases_like_closed_form(self):
        # T18: θ̇ = −2k sin(θ/2) 이고 tan(θ/4) = tan(θ₀/4)·e^(−kt)
        k, th0 = 3.0, 2.5
        qd = [1.0, 0.0, 0.0, 0.0]
        q0 = Q.from_axis_angle([0.3, -0.5, 0.8], th0)
        rows = self.kinematic(q0, qd, k, 1.0, 2.0)
        prev = th0
        for n, q in enumerate(rows, 1):
            _ax, th = Q.to_axis_angle(Q.mul(Q.conj(q), qd))
            self.assertLessEqual(th, prev + 1e-12)
            prev = th
            if n % 250 == 0:
                want = 4 * math.atan(math.tan(th0 / 4) *
                                     math.exp(-k * n * 1e-3))
                self.assertAlmostEqual(th, want, places=6)

    def test_axis_stays_fixed(self):
        qd = [1.0, 0.0, 0.0, 0.0]
        q0 = Q.from_axis_angle([0.3, -0.5, 0.8], 1.0)
        a0, _ = Q.to_axis_angle(Q.mul(Q.conj(q0), qd))
        q = self.kinematic(q0, qd, 3.0, 1.0, 0.5)[-1]
        a1, _ = Q.to_axis_angle(Q.mul(Q.conj(q), qd))
        for x, y in zip(a0, a1):
            self.assertAlmostEqual(x, y, places=9)

    def test_tilt_first_with_small_yaw_weight(self):
        # T19: 요 가중치를 줄이면 기울기 오차가 먼저 준다
        qd = [1.0, 0.0, 0.0, 0.0]
        q0 = Q.from_euler(0.5, 0.0, 2.5)
        slow = self.kinematic(q0, qd, 3.0, 1.0, 0.3)[-1]
        fast = self.kinematic(q0, qd, 3.0, 0.4, 0.3)[-1]
        self.assertLess(tilt_of(fast), tilt_of(slow))


if __name__ == '__main__':
    unittest.main()
