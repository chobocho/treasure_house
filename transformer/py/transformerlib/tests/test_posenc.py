# -*- coding: utf-8 -*-
"""posenc 의 증인 시험 (PLAN.md §3.1 표 7행).

  · 사인 인코딩이 논문 식 그대로인가 — 정해 둔 (pos, i) 에서.
  · 사인 인코딩의 선형 이동 성질: PE(p + k) = M_k · PE(p), M_k 는 p 와
    무관한 블록 회전 — "상대 위치를 선형으로 읽을 수 있다" 의 뜻.
  · RoPE: ⟨R_m q, R_n k⟩ 는 m − n 에만 달려 있다(≤ 1e-9).
"""
import math
import unittest

from transformerlib import posenc as P
from transformerlib import tensor as T
from transformerlib.rng import Rng
from transformerlib.tests.test_tensor import check, rand


class TestSinusoidal(unittest.TestCase):
    def test_formula_at_pinned_points(self):
        pe = P.sinusoidal(50, 8).tolist()
        self.assertEqual(pe[0], [0.0, 1.0] * 4)
        self.assertEqual(pe[1][0], math.sin(1.0))
        self.assertEqual(pe[1][1], math.cos(1.0))
        # i = 1 → 주파수 10000^(−2/8)
        w = 1.0 / 10000 ** (2 / 8)
        self.assertAlmostEqual(pe[37][2], math.sin(37 * w), places=15)
        self.assertAlmostEqual(pe[37][3], math.cos(37 * w), places=15)

    def test_values_bounded(self):
        pe = P.sinusoidal(64, 16)
        self.assertTrue(all(-1.0 <= v <= 1.0 for v in pe.data))

    def test_linear_shift_property(self):
        d, pe = 8, P.sinusoidal(40, 8).tolist()
        for k in (1, 5, 13):
            M = P.shift_matrix(k, d)
            for p in (0, 3, 20):
                got = [math.fsum(M[r][c] * pe[p][c] for c in range(d))
                       for r in range(d)]
                for r in range(d):
                    self.assertAlmostEqual(got[r], pe[p + k][r],
                                           places=12)

    def test_rejects_odd_width(self):
        with self.assertRaises(ValueError):
            P.sinusoidal(4, 7)


class TestLearned(unittest.TestCase):
    def test_uses_spec_init(self):
        w = P.learned(3, 4, Rng(9))
        self.assertEqual(w.shape, (3, 4))
        self.assertEqual(w.data[0], Rng(9).normal() * 0.02)
        self.assertTrue(w.requires_grad)


class TestRope(unittest.TestCase):
    def test_position_zero_is_identity(self):
        x = rand((1, 1, 1, 6), 1)
        y = P.rope(x)
        self.assertEqual(y.data, x.data)

    def test_rotation_by_hand(self):
        x = T.Tensor([1.0, 0.0, 0.0, 1.0] * 2, (1, 2, 4))
        y = P.rope(x).tolist()[0]
        t0, t1 = 1.0, 1.0 / 10000 ** (2 / 4)
        self.assertEqual(y[1][0], math.cos(t0))
        self.assertEqual(y[1][1], math.sin(t0))
        self.assertAlmostEqual(y[1][2], -math.sin(t1), places=15)
        self.assertAlmostEqual(y[1][3], math.cos(t1), places=15)

    def test_preserves_norm(self):
        x = rand((2, 5, 8), 2)
        y = P.rope(x)
        for r in range(10):
            a = x.data[r * 8:(r + 1) * 8]
            b = y.data[r * 8:(r + 1) * 8]
            na = math.fsum(v * v for v in a)
            nb = math.fsum(v * v for v in b)
            self.assertAlmostEqual(na, nb, places=13)

    def test_dot_depends_only_on_offset(self):
        r = Rng(3)
        dk = 8
        q = [r.normal() for _ in range(dk)]
        k = [r.normal() for _ in range(dk)]
        for gap in (0, 1, 4):
            vals = []
            for m in (gap, gap + 3, gap + 11):
                n = m - gap
                vals.append(P.rope_dot(q, m, k, n))
            for v in vals[1:]:
                self.assertLess(abs(v - vals[0]), 1e-9)

    def test_offset_argument_matches_longer_sequence(self):
        """KV 캐시에서 한 토큰씩 늘릴 때 쓰는 offset — 10부."""
        x = rand((1, 6, 4), 4)
        full = P.rope(x)
        last = P.rope(T.Tensor(x.data[20:], (1, 1, 4)), offset=5)
        self.assertEqual(last.data, full.data[20:])

    def test_backward(self):
        check(self, P.rope, [rand((1, 2, 3, 4), 5)])


if __name__ == '__main__':
    unittest.main()
