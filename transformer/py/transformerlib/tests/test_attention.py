# -*- coding: utf-8 -*-
"""attention 의 증인 시험 (PLAN.md §3.1 표 6행).

  · 1/√d 의 까닭 — 성분이 독립이고 분산 1 이면 q·k 의 분산은 d.
    1만 쌍을 뽑아 분산이 d 에 가깝고, √d 로 나누면 1 에 가까운지 본다.
  · 인과 마스크 — 미래 칸의 가중치는 정확히 0 이고, 미래 토큰을
    바꿔도 과거 위치의 출력은 한 비트도 안 바뀐다.
  · 역전파 — 멀티헤드 어텐션 전체를 차분과.
"""
import math
import unittest

from transformerlib import attention as A
from transformerlib import tensor as T
from transformerlib.rng import Rng
from transformerlib.tests.test_tensor import check, rand


class TestScaling(unittest.TestCase):
    def test_dot_product_variance_grows_with_d(self):
        # d = 256 도 맞지만 정규분포 510만 개를 뽑느라 30초가 든다
        for d in (4, 16, 64):
            raw, scaled = A.dot_variance(d, 10000, Rng(d))
            self.assertLess(abs(raw / d - 1.0), 0.1, 'd=%d' % d)
            self.assertLess(abs(scaled - 1.0), 0.1, 'd=%d' % d)

    def test_unscaled_softmax_saturates(self):
        """d 가 크면 나누지 않은 점수의 소프트맥스가 한 칸에 쏠린다."""
        big = A.max_weight_mean(256, 8, 100, Rng(1), scale=False)
        ok = A.max_weight_mean(256, 8, 100, Rng(1), scale=True)
        self.assertGreater(big, 0.8)
        self.assertLess(ok, 0.6)


class TestSdpa(unittest.TestCase):
    def test_weights_rows_sum_to_one_and_future_is_zero(self):
        q, k = rand((1, 5, 4), 1), rand((1, 5, 4), 2)
        v = rand((1, 5, 4), 3)
        _, w = A.scaled_dot_product(q, k, v, causal=True)
        rows = w.tolist()[0]
        for i, row in enumerate(rows):
            self.assertAlmostEqual(sum(row), 1.0, places=13)
            for j in range(i + 1, 5):
                self.assertEqual(row[j], 0.0)

    def test_matches_formula_by_hand(self):
        q = T.tensor([[[1.0, 0.0]]])
        k = T.tensor([[[1.0, 0.0], [0.0, 1.0]]])
        v = T.tensor([[[10.0, 0.0], [0.0, 10.0]]])
        out, w = A.scaled_dot_product(q, k, v, causal=False)
        a = math.exp(1 / math.sqrt(2))
        p = a / (a + 1)
        self.assertAlmostEqual(w.data[0], p, places=14)
        self.assertAlmostEqual(out.data[0], 10 * p, places=13)

    def test_backward(self):
        f = lambda q, k, v: A.scaled_dot_product(q, k, v)[0]
        check(self, f, [rand((2, 3, 4), 4), rand((2, 3, 4), 5),
                        rand((2, 3, 4), 6)])


class TestMultiHead(unittest.TestCase):
    def params(self, d, seed):
        return (rand((d, 3 * d), seed), rand((3 * d,), seed + 1),
                rand((d, d), seed + 2), rand((d,), seed + 3))

    def test_split_merge_round_trip(self):
        x = rand((2, 3, 8), 7)
        s = A.split_heads(x, 4)
        self.assertEqual(s.shape, (2, 4, 3, 2))
        # 헤드 j 는 열 j·d_k ‥ (j+1)·d_k − 1 (SPEC §3.1)
        self.assertEqual(s.tolist()[1][2][0], x.tolist()[1][0][4:6])
        self.assertEqual(A.merge_heads(s).data, x.data)

    def test_rejects_indivisible_width(self):
        with self.assertRaises(ValueError):
            A.split_heads(rand((1, 2, 6), 8), 4)

    def test_future_tokens_cannot_change_the_past(self):
        W = self.params(8, 20)
        x = rand((1, 6, 8), 9)
        y1, _ = A.multi_head_attention(x, *W, heads=2)
        x2 = T.Tensor(list(x.data), x.shape)
        for j in range(8):                   # 마지막 위치만 바꾼다
            x2.data[5 * 8 + j] += 3.0
        y2, _ = A.multi_head_attention(x2, *W, heads=2)
        self.assertEqual(y1.data[:5 * 8], y2.data[:5 * 8])
        self.assertNotEqual(y1.data[5 * 8:], y2.data[5 * 8:])

    def test_weights_shape(self):
        W = self.params(8, 30)
        _, w = A.multi_head_attention(rand((2, 5, 8), 10), *W, heads=4)
        self.assertEqual(w.shape, (2, 4, 5, 5))

    def test_backward_through_everything(self):
        W = self.params(4, 40)
        f = lambda x, a, b, c, e: A.multi_head_attention(
            x, a, b, c, e, heads=2)[0]
        check(self, f, [rand((1, 3, 4), 11)] + list(W))

    def test_rotate_hook_is_applied_to_q_and_k_only(self):
        W = self.params(4, 50)
        x = rand((1, 3, 4), 12)
        seen = []

        def rot(t, which):
            seen.append(which)
            return t
        A.multi_head_attention(x, *W, heads=2, rotate=rot)
        self.assertEqual(seen, ['q', 'k'])


if __name__ == '__main__':
    unittest.main()
