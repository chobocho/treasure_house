# -*- coding: utf-8 -*-
"""7부 연습 문제의 답이 정의에서 따로 계산한 값과 같은가."""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import exercises7 as E  # noqa: E402


class Seven(unittest.TestCase):
    def test_ch1_by_definition(self):
        r = E.ch1()
        self.assertEqual(r['|a|'], 3.0)
        self.assertEqual(r['a·b'], 1 * 2 + 2 * -1 + 2 * 0)
        self.assertEqual(r['a×b'], [2 * 0 - 2 * -1, 2 * 2 - 1 * 0,
                                    1 * -1 - 2 * 2])

    def test_ch2_solution_satisfies(self):
        r = E.ch2()
        m = [[1, 2, 0], [0, 1, 3], [2, 0, 1]]
        want = 1 * 1 - 2 * (0 - 6) + 0
        self.assertAlmostEqual(r['det'], want, places=12)
        for row, want in zip(m, [3, 4, 3]):
            got = sum(c * x for c, x in zip(row, r['x']))
            self.assertAlmostEqual(got, want, places=12)

    def test_ch3_error_within_bound(self):
        r = E.ch3()
        self.assertLess(r['오차'], r['한계 x³/6'])

    def test_ch4_ninety_five_percent(self):
        t = E.ch4()['95% 시간[s]']
        self.assertAlmostEqual(1 - math.exp(-t / 0.03), 0.95, places=12)

    def test_ch5_roots(self):
        self.assertEqual(E.ch5()['근'], '-1 ± 2i')

    def test_ch6_torque_axis(self):
        t = E.ch6()['τ = r×F']
        self.assertAlmostEqual(t[0], 0.0849 * 1.2, places=12)
        self.assertAlmostEqual(t[1], -0.0849 * 1.2, places=12)

    def test_ch7_one_step(self):
        r = E.ch7()
        self.assertEqual(r['오일러'], 0.5)
        h = 0.5
        self.assertAlmostEqual(r['RK4'], 1 - h + h * h / 2 - h ** 3 / 6
                               + h ** 4 / 24, places=15)

    def test_ch8(self):
        r = E.ch8()
        self.assertEqual(r['k*'], 1.0)
        self.assertEqual(r['Var((X+Y)/2)'], 0.5)


if __name__ == '__main__':
    unittest.main()


import exercises8 as E8  # noqa: E402


class Eight(unittest.TestCase):
    def test_ch1_ned(self):
        self.assertEqual(E8.ch1()['NED'], [4.0, 3.0, -5.0])

    def test_ch2_gyro(self):
        r = E8.ch2()
        # ω×Jω = (1,1,0)×(1,2,0) = (0, 0, 1)
        self.assertEqual(r['ω×Jω'], [0.0, 0.0, 1.0])
        self.assertEqual(r['에너지'], 0.5 * (1 + 2))

    def test_ch3_rpm(self):
        om = math.sqrt(0.5 * 9.81 / 4 / 1.2e-6)
        self.assertAlmostEqual(E8.ch3()['호버 rpm'],
                               om * 60 / (2 * math.pi), places=9)

    def test_ch4_mixer(self):
        u = E8.ch4()['u']
        a = 0.12 / math.sqrt(2)
        self.assertAlmostEqual(u[0], 4.8, places=12)
        self.assertAlmostEqual(u[1], a * (1.3 + 1.2 - 1.1 - 1.2),
                               places=12)

    def test_ch5_tilt(self):
        r = E8.ch5()
        self.assertAlmostEqual(r['x 가속도'],
                               9.81 * math.sin(math.radians(10)),
                               places=12)

    def test_ch6_circle(self):
        r = E8.ch6()
        self.assertAlmostEqual(r['구심 가속도'], 1.28, places=12)
