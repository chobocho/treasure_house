# -*- coding: utf-8 -*-
"""ex/frame_mixer.py 시험 — 프레임 기하에서 믹서를 만들면 (4부 1장)."""
import itertools
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'py'))

import frame_mixer as FM  # noqa: E402
from droneshow import linalg, mixer, params  # noqa: E402

P = params.load()
C = P['kQ'] / P['kT']
MG = P['m'] * P['g']


class Geometry(unittest.TestCase):
    def test_quad_x_is_the_part8_mixer(self):
        # 8부 mixer.matrix 와 같은 행렬이어야 한다 — 같은 배치이므로
        got = FM.matrix(FM.rotors('quad_x', P['L']), C)
        want = mixer.matrix(P)
        for r in range(4):
            for k in range(4):
                self.assertAlmostEqual(got[r][k], want[r][k], places=12)

    def test_every_frame_has_rank_four(self):
        for name in FM.NAMES:
            m = FM.matrix(FM.rotors(name, P['L']), C)
            self.assertEqual(linalg.rank(m), 4, name)

    def test_equal_thrust_gives_no_torque(self):
        # 같은 추력이면 롤·피치·요가 모두 0 — 요가 0 인 것이 정리 T3
        for name in FM.NAMES:
            rs = FM.rotors(name, P['L'])
            u = FM.equal_split(FM.matrix(rs, C), MG)
            self.assertAlmostEqual(u[0], MG, places=12)
            for k in (1, 2, 3):
                self.assertLess(abs(u[k]), 1e-12, (name, k))

    def test_same_spin_loses_yaw(self):
        rs = [(x, y, 1) for x, y, _s in FM.rotors('quad_x', P['L'])]
        self.assertEqual(linalg.rank(FM.matrix(rs, C)), 3)

    def test_plus_needs_root2_more_for_roll(self):
        mx = FM.matrix(FM.rotors('quad_x', P['L']), C)
        mp = FM.matrix(FM.rotors('quad_plus', P['L']), C)
        rx = FM.cost(mx, 1)
        rp = FM.cost(mp, 1)
        self.assertAlmostEqual(rp / rx, math.sqrt(2), places=12)
        self.assertAlmostEqual(rx, 1 / (4 * P['L'] / math.sqrt(2)),
                               places=12)

    def test_min_norm_solves(self):
        m = FM.matrix(FM.rotors('hexa_x', P['L']), C)
        u = [MG, 0.02, -0.01, 0.003]
        t = FM.min_norm(m, u)
        got = [sum(r[k] * t[k] for k in range(6)) for r in m]
        for a, b in zip(got, u):
            self.assertAlmostEqual(a, b, places=12)


class EngineOut(unittest.TestCase):
    def test_quad_cannot_hover_on_three(self):
        m = FM.matrix(FM.rotors('quad_x', P['L']), C)
        self.assertIsNone(FM.engine_out(m, 0, MG))

    def test_alternating_hexa_has_zero_margin(self):
        m = FM.matrix(FM.rotors('hexa_x', P['L']), C)
        for k in range(6):
            self.assertLess(abs(FM.engine_out(m, k, MG)), 1e-9, k)

    def test_other_hexa_keeps_margin_for_four(self):
        # 처음 시험은 "여섯 경우 모두 여유" 라고 짐작했지만 틀렸다 —
        # 로터 5·6 이 멈추면 여유 0. 아래 시험이 그 까닭을 넓힌다.
        m = FM.matrix(FM.rotors('hexa_x_ppnnpn', P['L']), C)
        g = [FM.engine_out(m, k, MG) for k in range(6)]
        self.assertEqual([x > 0.1 for x in g], [True] * 4 + [False] * 2)
        self.assertLess(max(abs(x) for x in g[4:]), 1e-9)

    def test_no_hexa_pattern_survives_every_failure(self):
        # 반시계 셋·시계 셋의 20 가지 배치를 모두 본다
        worst = []
        for sp in set(itertools.permutations((1, 1, 1, -1, -1, -1))):
            rs = [(x, y, s) for (x, y, _), s
                  in zip(FM.rotors('hexa_x', P['L']), sp)]
            m = FM.matrix(rs, C)
            worst.append(min(FM.engine_out(m, k, MG) for k in range(6)))
        self.assertEqual(len(worst), 20)
        self.assertLess(max(worst), 1e-9)

    def test_margin_is_a_real_solution(self):
        # 여유를 주는 추력 넷이 실제로 평형을 만든다
        m = FM.matrix(FM.rotors('hexa_x_ppnnpn', P['L']), C)
        g, t = FM.engine_out(m, 2, MG, full=True)
        self.assertEqual(t[2], 0.0)
        got = [sum(r[k] * t[k] for k in range(6)) for r in m]
        for a, b in zip(got, [MG, 0.0, 0.0, 0.0]):
            self.assertAlmostEqual(a, b, places=9)
        rest = [x for i, x in enumerate(t) if i != 2]
        self.assertAlmostEqual(min(rest), g, places=12)


if __name__ == '__main__':
    unittest.main()
