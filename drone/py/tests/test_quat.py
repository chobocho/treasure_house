# -*- coding: utf-8 -*-
"""quat 시험 — 회전행렬·오일러각·쿼터니언 (정리 T4–T7 의 증인)."""
import math
import unittest

from droneshow import quat as Q
from droneshow import rng
from droneshow import vec3 as V


def rand_quat(g):
    return Q.normalize([g.normal() for _ in range(4)])


def rand_vec(g):
    return [g.uniform() * 4 - 2 for _ in range(3)]


class Close(unittest.TestCase):
    def close(self, a, b, tol=1e-12):
        if isinstance(a[0], list):
            for ra, rb in zip(a, b):
                self.close(ra, rb, tol)
            return
        for x, y in zip(a, b):
            self.assertLessEqual(abs(x - y), tol, (a, b))


class Rotation(Close):
    """T4 — 회전행렬은 직교하고 행렬식이 1, 합성은 행렬 곱."""

    def test_rotation_orthogonal_det1(self):
        g = rng.Rng(11)
        for _ in range(20):
            r = Q.to_matrix(rand_quat(g))
            self.close(V.matmul(V.transpose(r), r), V.eye3())
            self.assertAlmostEqual(V.det3(r), 1.0, places=12)

    def test_composition_is_product(self):
        g = rng.Rng(12)
        for _ in range(20):
            a, b = rand_quat(g), rand_quat(g)
            self.close(Q.to_matrix(Q.mul(a, b)),
                       V.matmul(Q.to_matrix(a), Q.to_matrix(b)))

    def test_matrix_roundtrip(self):
        g = rng.Rng(13)
        for _ in range(20):
            q = Q.canonical(rand_quat(g))
            self.close(Q.canonical(Q.from_matrix(Q.to_matrix(q))), q)

    def test_axis_angle(self):
        q = Q.from_axis_angle([0.0, 0.0, 1.0], math.pi / 2)
        self.close(Q.rotate(q, [1.0, 0.0, 0.0]), [0.0, 1.0, 0.0])
        axis, ang = Q.to_axis_angle(q)
        self.close(axis, [0.0, 0.0, 1.0])
        self.assertAlmostEqual(ang, math.pi / 2, places=14)


class Euler(Close):
    """T5 — 오일러각의 비율 행렬과 짐벌 락."""

    def test_euler_roundtrip_away_from_lock(self):
        for r, p, y in [(0.1, 0.2, 0.3), (-1.0, 0.5, 2.0),
                        (0.7, -1.2, -2.5)]:
            got = Q.to_euler(Q.from_euler(r, p, y))
            self.close(got, [r, p, y])

    def test_rate_matrix_det_is_cos_pitch(self):
        for p in (0.0, 0.5, 1.0, 1.5):
            e = Q.euler_rate_matrix(0.3, p)
            self.assertAlmostEqual(V.det3(e), math.cos(p), places=14)

    def test_gimbal_lock_det_vanishes(self):
        e = Q.euler_rate_matrix(0.3, math.pi / 2)
        self.assertAlmostEqual(V.det3(e), 0.0, places=15)

    def test_lock_merges_roll_and_yaw(self):
        # 피치 90° 에서는 (롤, 요) 와 (롤+d, 요+d) 가 같은 자세다
        a = Q.to_matrix(Q.from_euler(0.2, math.pi / 2, 0.5))
        b = Q.to_matrix(Q.from_euler(0.2 + 0.3, math.pi / 2, 0.5 + 0.3))
        self.close(a, b, 1e-12)

    def test_rate_matrix_maps_euler_rates_to_body(self):
        # 오일러각을 조금 움직여 얻은 회전과 E·(φ̇,θ̇,ψ̇) 가 같아야 한다
        r, p, y = 0.3, 0.4, -0.7
        d = [0.2, -0.1, 0.3]
        h = 1e-6
        q0 = Q.from_euler(r, p, y)
        q1 = Q.from_euler(r + d[0] * h, p + d[1] * h, y + d[2] * h)
        dq = Q.mul(Q.conj(q0), q1)          # 몸체 좌표의 작은 회전
        w_num = [2 * c / h for c in dq[1:]]
        w = V.matvec(Q.euler_rate_matrix(r, p), d)
        self.close(w_num, w, 1e-6)


class Quaternion(Close):
    """T6 — q v q* 는 회전이고, q 와 −q 는 같은 회전."""

    def test_rotation_preserves_norm_and_dot(self):
        g = rng.Rng(21)
        for _ in range(20):
            q = rand_quat(g)
            a, b = rand_vec(g), rand_vec(g)
            ra, rb = Q.rotate(q, a), Q.rotate(q, b)
            self.assertAlmostEqual(V.dot(ra, rb), V.dot(a, b),
                                   places=12)
            self.assertAlmostEqual(V.norm(ra), V.norm(a), places=12)

    def test_minus_q_same_rotation(self):
        g = rng.Rng(22)
        for _ in range(20):
            q = rand_quat(g)
            self.close(Q.to_matrix(q), Q.to_matrix([-c for c in q]))

    def test_product_norm(self):
        g = rng.Rng(23)
        for _ in range(20):
            a = [g.normal() for _ in range(4)]
            b = [g.normal() for _ in range(4)]
            self.assertAlmostEqual(Q.norm(Q.mul(a, b)),
                                   Q.norm(a) * Q.norm(b), places=12)

    def test_not_commutative(self):
        a = Q.from_axis_angle([1.0, 0.0, 0.0], 0.5)
        b = Q.from_axis_angle([0.0, 1.0, 0.0], 0.5)
        self.assertGreater(max(abs(x - y) for x, y in
                               zip(Q.mul(a, b), Q.mul(b, a))), 0.01)

    def test_rotate_matches_matrix(self):
        g = rng.Rng(24)
        for _ in range(20):
            q, v = rand_quat(g), rand_vec(g)
            self.close(Q.rotate(q, v), V.matvec(Q.to_matrix(q), v))

    def test_shortest_arc(self):
        g = rng.Rng(25)
        for _ in range(20):
            a = V.normalize(rand_vec(g))
            b = V.normalize(rand_vec(g))
            q = Q.from_two_vectors(a, b)
            self.close(Q.rotate(q, a), b, 1e-12)
            _axis, ang = Q.to_axis_angle(q)
            self.assertAlmostEqual(ang, math.acos(V.dot(a, b)),
                                   places=9)


class Kinematics(Close):
    """T7 — q̇ = ½ q ⊗ (0, ω), 오일러 적분의 노름 표류와 정규화."""

    def test_euler_step_norm_drift_formula(self):
        # 한 걸음 뒤 |q|² = 1 + (dt·|ω|/2)² — 정확히
        q = Q.from_axis_angle([0.0, 0.6, 0.8], 0.4)
        w = [1.0, -2.0, 0.5]
        for dt in (0.01, 0.002):
            q1 = Q.step_euler(q, w, dt)
            want = 1 + (dt * V.norm(w) / 2) ** 2
            self.assertAlmostEqual(Q.norm(q1) ** 2, want, places=14)

    def test_drift_is_second_order(self):
        q = Q.from_axis_angle([1.0, 0.0, 0.0], 0.0)
        w = [0.0, 0.0, 3.0]
        e1 = Q.norm(Q.step_euler(q, w, 0.01)) - 1
        e2 = Q.norm(Q.step_euler(q, w, 0.005)) - 1
        self.assertAlmostEqual(e1 / e2, 4.0, delta=0.01)

    def test_constant_rate_exact_solution(self):
        # ω 가 일정하면 q(t) = q0 ⊗ exp(ω t / 2)
        # — 정규화한 오일러가 따라간다
        q0 = Q.from_axis_angle([0.0, 0.0, 1.0], 0.3)
        w = [0.0, 0.0, 2.0]
        q, dt = list(q0), 0.001
        for _ in range(1000):
            q = Q.normalize(Q.step_euler(q, w, dt))
        exact = Q.mul(q0, Q.from_axis_angle([0.0, 0.0, 1.0], 2.0))
        self.close(q, exact, 1e-6)

    def test_qdot_formula(self):
        q = Q.from_axis_angle([0.0, 1.0, 0.0], 0.7)
        w = [0.3, 0.1, -0.2]
        got = Q.qdot(q, w)
        want = [0.5 * c for c in Q.mul(q, [0.0] + w)]
        self.close(got, want, 1e-15)


if __name__ == '__main__':
    unittest.main()
