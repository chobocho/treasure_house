# -*- coding: utf-8 -*-
"""mixer 시험 — X 배치 믹서(T3, T9), 언더액추에이션(T10), 포화 처리."""
import unittest

from droneshow import linalg, mixer, params


class Matrix(unittest.TestCase):
    def setUp(self):
        self.p = params.load()
        self.m = mixer.matrix(self.p)

    def test_rows_orthogonal(self):
        for i in range(4):
            for j in range(4):
                if i != j:
                    d = sum(self.m[i][k] * self.m[j][k]
                            for k in range(4))
                    self.assertAlmostEqual(d, 0.0, places=15)

    def test_det_formula(self):
        # T9: det M = 16 a² c (행이 서로 수직이라)
        a = self.p['L'] / 2 ** 0.5
        c = self.p['kQ'] / self.p['kT']
        self.assertAlmostEqual(
            linalg.det(self.m) / (16 * a * a * c), 1.0, places=12)

    def test_inverse(self):
        mi = mixer.inverse(self.p)
        for i in range(4):
            for j in range(4):
                s = sum(self.m[i][k] * mi[k][j] for k in range(4))
                self.assertAlmostEqual(s, float(i == j), places=12)

    def test_hover_yaw_torque_cancels(self):
        # T3: 네 로터가 같은 속도면 반토크의 합은 0
        t = [1.0, 1.0, 1.0, 1.0]
        u = mixer.forward(self.p, t)
        self.assertEqual(u[1:], [0.0, 0.0, 0.0])
        self.assertEqual(u[0], 4.0)

    def test_yaw_from_imbalance(self):
        # 반시계(+z) 로터 1·3 을 세게 → 몸체는 시계(−z) 쪽 토크
        u = mixer.forward(self.p, [1.2, 1.0, 1.2, 1.0])
        self.assertLess(u[3], 0.0)
        self.assertAlmostEqual(u[1], 0.0, places=15)
        self.assertAlmostEqual(u[2], 0.0, places=15)

    def test_roll_from_left_right(self):
        # 왼쪽(y>0) 로터 1·2 를 세게 → +x 둘레(오른쪽이 내려감) 토크
        u = mixer.forward(self.p, [1.1, 1.1, 1.0, 1.0])
        self.assertGreater(u[1], 0.0)


class Underactuation(unittest.TestCase):
    def test_wrench_map_rank_four(self):
        # T10: 추력 넷 → 힘 셋·토크 셋(6차원). 계수는 4 — 옆 힘이 없다
        b = mixer.wrench_map(params.load())
        self.assertEqual(len(b), 6)
        self.assertEqual(b[0], [0.0] * 4)
        self.assertEqual(b[1], [0.0] * 4)
        self.assertEqual(linalg.rank(b), 4)


class Allocate(unittest.TestCase):
    def setUp(self):
        self.p = params.load()
        self.tmin = self.p['kT'] * self.p['omega_min'] ** 2
        self.tmax = self.p['kT'] * self.p['omega_max'] ** 2

    def alloc(self, u):
        return mixer.allocate(self.p, u, self.tmin, self.tmax)

    def test_inside_limits_is_exact(self):
        u = [5.0, 0.01, -0.02, 0.001]
        t, flags = self.alloc(u)
        back = mixer.forward(self.p, t)
        for i in range(4):
            self.assertAlmostEqual(back[i], u[i], places=12)
        self.assertEqual(flags, [])

    def test_yaw_is_sacrificed_first(self):
        u = [5.0, 0.0, 0.0, 0.2]
        t, flags = self.alloc(u)
        back = mixer.forward(self.p, t)
        self.assertIn('yaw_scaled', flags)
        self.assertAlmostEqual(back[0], 5.0, places=9)
        self.assertLess(abs(back[3]), 0.2)
        for x in t:
            self.assertTrue(self.tmin - 1e-12 <= x <= self.tmax + 1e-12)

    def test_roll_kept_collective_shifted(self):
        # 추력을 거의 다 쓰는 중 롤을 크게 — 롤을 지키고 추력을 내린다
        u = [4 * self.tmax - 0.1, 0.3, 0.0, 0.0]
        t, flags = self.alloc(u)
        back = mixer.forward(self.p, t)
        self.assertIn('shifted', flags)
        self.assertAlmostEqual(back[1], 0.3, places=9)
        self.assertLess(back[0], u[0])

    def test_always_within_limits(self):
        for u in ([100.0, 1.0, 1.0, 1.0], [-5.0, 0.0, 0.0, 0.0],
                  [2.0, -3.0, 2.0, -1.0]):
            t, _f = self.alloc(u)
            for x in t:
                self.assertTrue(
                    self.tmin - 1e-12 <= x <= self.tmax + 1e-12)


if __name__ == '__main__':
    unittest.main()
