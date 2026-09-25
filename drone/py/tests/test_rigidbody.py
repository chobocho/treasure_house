# -*- coding: utf-8 -*-
"""rigidbody 시험 — RK4 와 뉴턴-오일러 (T8, T21 의 증인)."""
import math
import unittest

from droneshow import quat as Q
from droneshow import rigidbody as RB
from droneshow import vec3 as V


def exp_error(step, dt):
    """x' = −x 를 t = 1 까지 풀어 exp(−1) 과의 차."""
    x = [1.0]
    for _ in range(round(1 / dt)):
        x = step(lambda s: [-s[0]], x, dt)
    return abs(x[0] - math.exp(-1))


class Integrators(unittest.TestCase):
    def test_euler_first_order(self):
        r = exp_error(RB.euler, 0.01) / exp_error(RB.euler, 0.005)
        self.assertAlmostEqual(r, 2.0, delta=0.05)

    def test_rk4_fourth_order(self):
        # 차수는 dt 가 작을 때의 이야기다 — 0.1 에서는 비가 16.7
        r = exp_error(RB.rk4, 0.04) / exp_error(RB.rk4, 0.02)
        self.assertAlmostEqual(r, 16.0, delta=0.5)

    def test_rk4_exact_for_cubic(self):
        # x' = 3t² 를 상태에 t 를 넣어 푼다 — RK4 는 3차까지 정확하다
        f = lambda s: [3 * s[1] ** 2, 1.0]
        x = [0.0, 0.0]
        for _ in range(10):
            x = RB.rk4(f, x, 0.1)
        self.assertAlmostEqual(x[0], 1.0, places=13)


class NewtonEuler(unittest.TestCase):
    J = [1.0, 2.0, 3.0]

    def test_no_torque_no_spin_change_about_principal_axis(self):
        w = [0.0, 0.0, 2.0]
        self.assertEqual(RB.omega_dot(self.J, w, [0.0, 0.0, 0.0]),
                         [0.0, 0.0, 0.0])

    def test_gyroscopic_term(self):
        # J ω̇ = τ − ω × Jω 를 손으로 한 번
        w = [1.0, 2.0, 3.0]
        jw = [1.0, 4.0, 9.0]
        c = V.cross(w, jw)
        got = RB.omega_dot(self.J, w, [0.0, 0.0, 0.0])
        self.assertEqual(got, [-c[0] / 1.0, -c[1] / 2.0, -c[2] / 3.0])

    def tumble(self, w0, secs, dt=0.002):
        s = [1.0, 0.0, 0.0, 0.0] + list(w0)
        f = lambda x: RB.attitude_deriv(self.J, x, [0.0, 0.0, 0.0])
        out = []
        for _ in range(round(secs / dt)):
            s = RB.rk4(f, s, dt)
            s[:4] = Q.normalize(s[:4])
            out.append(s)
        return out

    def test_torque_free_energy_and_momentum(self):
        # T8 증인 — 토크 없는 회전은 에너지와 각운동량 크기를 지킨다
        w0 = [0.3, 1.0, 0.2]
        e0 = RB.rot_energy(self.J, w0)
        h0 = V.norm(RB.ang_momentum(self.J, w0))
        s = self.tumble(w0, 10.0)[-1]
        e = RB.rot_energy(self.J, s[4:])
        self.assertLess(abs(e - e0) / e0, 1e-6)
        h = V.norm(RB.ang_momentum(self.J, s[4:]))
        self.assertLess(abs(h - h0) / h0, 1e-6)

    def test_world_momentum_vector_is_constant(self):
        # 몸체 좌표의 Jω 는 돌지만, 세계 좌표로 옮기면 멈춰 있다
        w0 = [0.3, 1.0, 0.2]
        h0 = RB.ang_momentum(self.J, w0)
        s = self.tumble(w0, 5.0)[-1]
        hw = Q.rotate(s[:4], RB.ang_momentum(self.J, s[4:]))
        for i in range(3):
            self.assertAlmostEqual(hw[i], h0[i], places=6)

    def test_intermediate_axis_is_unstable(self):
        # 가운데 관성축 둘레 회전은 작은 흔들림이 커진다 (자니베코프)
        rows = self.tumble([1e-3, 2.0, 1e-3], 10.0)
        self.assertGreater(max(abs(s[4]) for s in rows), 0.5)
        rows = self.tumble([1e-3, 1e-3, 2.0], 10.0)
        self.assertLess(max(abs(s[4]) for s in rows), 0.01)


if __name__ == '__main__':
    unittest.main()
