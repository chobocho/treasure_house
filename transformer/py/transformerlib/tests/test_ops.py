# -*- coding: utf-8 -*-
"""ops 의 증인 시험 (PLAN.md §3.1 표 4행, §4 수식 정책).

식마다 증인이 있다.
  · 소프트맥스 야코비안 = diag(p) − p pᵀ          (차분 야코비안과)
  · 교차엔트로피의 로짓 기울기 = (p − y) / N       (따로 계산한 값과)
  · 레이어놈 역전파                                 (차분과)
  · GELU'(0) = 1/2, tanh 근사와 erf 정의의 차이      (닫힌 값과)
"""
import math
import unittest

from transformerlib import ops
from transformerlib import tensor as T
from transformerlib.rng import Rng
from transformerlib.tests.test_tensor import check, rand


class TestSoftmax(unittest.TestCase):
    def test_rows_sum_to_one(self):
        y = ops.softmax(T.tensor([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]]))
        for row in y.tolist():
            self.assertAlmostEqual(sum(row), 1.0, places=14)
        self.assertAlmostEqual(y.tolist()[1][0], 1 / 3, places=14)

    def test_stable_for_huge_logits(self):
        """최댓값을 빼지 않으면 exp(1000) 이 넘친다."""
        y = ops.softmax(T.tensor([1000.0, 1001.0, 999.0]))
        want = ops.softmax(T.tensor([1.0, 2.0, 0.0]))
        self.assertLess(T.rel_error(y.data, want.data), 1e-14)

    def test_jacobian_is_diag_minus_outer(self):
        x = [0.3, -1.2, 2.0, 0.5]
        J = ops.softmax_jacobian(ops.softmax(T.tensor(x)).data)
        h = 1e-6
        for j in range(4):
            up, dn = list(x), list(x)
            up[j] += h
            dn[j] -= h
            pu = ops.softmax(T.tensor(up)).data
            pd = ops.softmax(T.tensor(dn)).data
            for i in range(4):
                fd = (pu[i] - pd[i]) / (2 * h)
                self.assertAlmostEqual(J[i][j], fd, places=8)

    def test_backward(self):
        check(self, ops.softmax, [rand((2, 5), 1, -3, 3)])
        check(self, ops.log_softmax, [rand((3, 4), 2, -3, 3)])

    def test_log_softmax_matches_log_of_softmax(self):
        x = T.tensor([[0.1, 5.0, -2.0]])
        a = ops.log_softmax(x).data
        b = [math.log(v) for v in ops.softmax(x).data]
        self.assertLess(max(abs(u - v) for u, v in zip(a, b)), 1e-14)


class TestCrossEntropy(unittest.TestCase):
    def test_value_is_mean_negative_log_prob(self):
        logits = T.tensor([[2.0, 0.5, -1.0], [0.0, 0.0, 3.0]])
        loss = ops.cross_entropy(logits, [0, 2])
        p = ops.softmax(logits).tolist()
        want = -(math.log(p[0][0]) + math.log(p[1][2])) / 2
        self.assertAlmostEqual(loss.data[0], want, places=14)

    def test_gradient_is_p_minus_y(self):
        logits = rand((3, 5), 3, -2, 2)
        targets = [4, 0, 2]
        ops.cross_entropy(logits, targets).backward()
        p = ops.softmax(T.Tensor(list(logits.data), (3, 5))).data
        for r in range(3):
            for c in range(5):
                y = 1.0 if c == targets[r] else 0.0
                want = (p[r * 5 + c] - y) / 3
                self.assertAlmostEqual(logits.grad[r * 5 + c], want,
                                       places=15)

    def test_backward_by_difference(self):
        check(self, lambda z: ops.cross_entropy(z, [1, 3, 0]),
              [rand((3, 4), 4, -2, 2)])

    def test_uniform_logits_give_log_vocab(self):
        """학습 시작 직후 손실 ≈ ln V 의 뿌리."""
        loss = ops.cross_entropy(T.zeros((2, 7)), [3, 5])
        self.assertAlmostEqual(loss.data[0], math.log(7), places=14)

    def test_rejects_bad_targets(self):
        with self.assertRaises(ValueError):
            ops.cross_entropy(T.zeros((2, 3)), [0])
        with self.assertRaises(ValueError):
            ops.cross_entropy(T.zeros((2, 3)), [0, 3])


class TestLayerNorm(unittest.TestCase):
    def test_output_is_normalised(self):
        x = rand((2, 6), 5, -4, 4)
        g = T.Tensor([1.0] * 6, (6,))
        b = T.zeros((6,))
        y = ops.layernorm(x, g, b).tolist()
        for row in y:
            m = sum(row) / 6
            v = sum((u - m) ** 2 for u in row) / 6
            self.assertAlmostEqual(m, 0.0, places=12)
            # ε 1e-5 때문에 1 보다 조금 작다
            self.assertAlmostEqual(v, 1.0, places=4)

    def test_backward(self):
        x = rand((3, 5), 6, -2, 2)
        g = rand((5,), 7, 0.5, 1.5)
        b = rand((5,), 8)
        check(self, ops.layernorm, [x, g, b])

    def test_constant_row_does_not_blow_up(self):
        """분산 0 이어도 ε 때문에 0 으로 나누지 않는다."""
        x = T.tensor([[2.0, 2.0, 2.0]], requires_grad=True)
        g = T.Tensor([1.0] * 3, (3,), requires_grad=True)
        y = ops.layernorm(x, g, T.zeros((3,)))
        self.assertEqual(y.data, [0.0, 0.0, 0.0])
        T.sum(y).backward()
        self.assertTrue(all(math.isfinite(v) for v in x.grad))


class TestGelu(unittest.TestCase):
    def test_constants_pinned(self):
        """SPEC §3.3 — √(2/π) 를 16자리, 3차항 0.044715."""
        self.assertEqual(ops.GELU_A, 0.7978845608028654)
        self.assertEqual(ops.GELU_A, math.sqrt(2 / math.pi))
        self.assertEqual(ops.GELU_B, 0.044715)

    def test_derivative_at_zero_is_half(self):
        x = T.tensor([0.0], requires_grad=True)
        T.sum(ops.gelu(x)).backward()
        self.assertEqual(x.grad[0], 0.5)

    def test_tanh_approximation_is_close_to_erf(self):
        worst = 0.0
        for k in range(-600, 601):
            x = k / 100.0
            a = ops.gelu(T.tensor([x])).data[0]
            worst = max(worst, abs(a - ops.gelu_exact(x)))
        self.assertLess(worst, 1e-3)
        self.assertGreater(worst, 0.0)       # 근사이지 같은 식은 아니다

    def test_backward(self):
        check(self, ops.gelu, [rand((2, 6), 9, -3, 3)])


class TestEmbeddingDropoutMask(unittest.TestCase):
    def test_embedding_rows_and_scatter_add(self):
        w = rand((4, 3), 10)
        e = ops.embedding(w, [[2, 0], [2, 3]])
        self.assertEqual(e.shape, (2, 2, 3))
        self.assertEqual(e.tolist()[0][0], w.tolist()[2])
        T.sum(e).backward()
        # 2 번 행은 두 번 쓰였으니 기울기가 2
        self.assertEqual(w.grad, [1.0] * 3 + [0.0] * 3 + [2.0] * 3
                         + [1.0] * 3)

    def test_embedding_rejects_out_of_range(self):
        with self.assertRaises(IndexError):
            ops.embedding(T.zeros((4, 3)), [4])

    def test_dropout_p0_is_identity_and_draws_nothing(self):
        r = Rng(5)
        x = rand((2, 3), 11)
        y = ops.dropout(x, 0.0, r)
        self.assertIs(y, x)
        self.assertEqual(r.next(), Rng(5).next())

    def test_dropout_keeps_expectation(self):
        x = T.Tensor([1.0] * 20000, (20000,))
        y = ops.dropout(x, 0.25, Rng(6))
        zeros = sum(1 for v in y.data if v == 0.0)
        self.assertLess(abs(zeros / 20000 - 0.25), 0.02)
        self.assertLess(abs(sum(y.data) / 20000 - 1.0), 0.03)
        self.assertTrue(all(v in (0.0, 1 / 0.75) for v in y.data))

    def test_dropout_backward_uses_same_mask(self):
        x = rand((50,), 12)
        y = ops.dropout(x, 0.5, Rng(7))
        T.sum(y).backward()
        for k in range(50):
            self.assertEqual(x.grad[k], 0.0 if y.data[k] == 0 else 2.0)

    def test_causal_softmax_equals_minus_infinity_mask(self):
        s = rand((2, 4, 4), 13, -2, 2)
        a = ops.causal_softmax(s)
        n = 4
        masked = [v if (k % n) <= (k // n) % n else -math.inf
                  for k, v in enumerate(s.data)]
        b = ops.softmax(T.Tensor(masked, s.shape))
        self.assertLess(max(abs(u - v) for u, v in zip(a.data, b.data)),
                        1e-15)
        for row in range(n):
            for col in range(row + 1, n):
                self.assertEqual(a.data[row * n + col], 0.0)

    def test_causal_softmax_backward(self):
        check(self, ops.causal_softmax, [rand((2, 3, 3), 14, -2, 2)])

    def test_causal_row0_attends_only_to_itself(self):
        a = ops.causal_softmax(rand((3, 3), 15)).tolist()
        self.assertEqual(a[0], [1.0, 0.0, 0.0])


if __name__ == '__main__':
    unittest.main()
