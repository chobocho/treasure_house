# -*- coding: utf-8 -*-
"""tensor 의 증인 시험 (PLAN.md §3.1 표 3행).

모든 연산의 역전파를 중심 차분과 견준다(상대오차 ≤ 1e-5). 출력이
스칼라가 아닌 연산은 고정된 난수 가중치 w 와 곱해 더한 Σ w·f(x) 로
만들어 본다 — 그러면 야코비안의 모든 칸이 한 번에 시험된다.
"""
import unittest

from transformerlib import tensor as T
from transformerlib.rng import Rng

TOL = 1e-5


def rand(shape, seed, lo=-1.0, hi=1.0):
    r = Rng(seed)
    n = T.numel(shape)
    return T.Tensor([lo + (hi - lo) * r.uniform() for _ in range(n)],
                    shape, requires_grad=True)


def check(test, f, inputs, seed=99):
    """f(*inputs) 의 역전파를 차분과 견준다.

    같은 입력을 여러 check 에 되풀이해 쓰므로 기울기를 먼저 비운다 —
    안 비우면 앞 check 의 기울기가 쌓여 틀린 것처럼 보인다.
    """
    for x in inputs:
        x.grad = None
    out = f(*inputs)
    w = rand(out.shape, seed)
    w.requires_grad = False
    loss = T.sum(T.mul(out, w))
    loss.backward()
    for k, x in enumerate(inputs):
        num = T.finite_difference(
            lambda: T.sum(T.mul(f(*inputs), w)).data[0], x)
        err = T.rel_error(x.grad, num)
        test.assertLess(err, TOL, '입력 %d 오차 %.2e' % (k, err))


class TestShapes(unittest.TestCase):
    def test_broadcast_shape(self):
        self.assertEqual(T.broadcast_shape((2, 3), (3,)), (2, 3))
        self.assertEqual(T.broadcast_shape((4, 1, 3), (2, 1)),
                         (4, 2, 3))
        with self.assertRaises(ValueError):
            T.broadcast_shape((2, 3), (4,))

    def test_tensor_rejects_wrong_size(self):
        with self.assertRaises(ValueError):
            T.Tensor([1.0, 2.0, 3.0], (2, 2))

    def test_tolist_and_from_nested(self):
        t = T.tensor([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(t.shape, (2, 3))
        self.assertEqual(t.tolist(), [[1, 2, 3], [4, 5, 6]])

    def test_row_major(self):
        """(r, c) 는 r·열수 + c 번째 (SPEC §2)."""
        t = T.tensor([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(t.data[1 * 3 + 2], 6)


class TestForward(unittest.TestCase):
    def test_matmul_by_hand(self):
        a = T.tensor([[1, 2], [3, 4], [5, 6]])
        b = T.tensor([[1, 0, -1], [2, 1, 0]])
        self.assertEqual(T.matmul(a, b).tolist(),
                         [[5, 2, -1], [11, 4, -3], [17, 6, -5]])

    def test_matmul_shape_error(self):
        with self.assertRaises(ValueError):
            T.matmul(T.zeros((2, 3)), T.zeros((2, 3)))

    def test_add_broadcast_bias(self):
        x = T.tensor([[1, 2, 3], [4, 5, 6]])
        b = T.tensor([10, 20, 30])
        self.assertEqual(T.add(x, b).tolist(),
                         [[11, 22, 33], [14, 25, 36]])

    def test_sum_axes(self):
        x = T.tensor([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(T.sum(x, 0).tolist(), [5, 7, 9])
        self.assertEqual(T.sum(x, 1, keepdims=True).tolist(),
                         [[6], [15]])
        self.assertEqual(T.sum(x).data, [21])
        self.assertEqual(T.mean(x, -1).tolist(), [2, 5])

    def test_transpose_reshape(self):
        x = T.tensor([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(T.transpose(x, 0, 1).tolist(),
                         [[1, 4], [2, 5], [3, 6]])
        self.assertEqual(T.reshape(x, (3, 2)).tolist(),
                         [[1, 2], [3, 4], [5, 6]])
        y = T.permute(T.reshape(x, (1, 2, 3)), (2, 0, 1))
        self.assertEqual(y.shape, (3, 1, 2))
        self.assertEqual(y.tolist(), [[[1, 4]], [[2, 5]], [[3, 6]]])

    def test_slice_last(self):
        x = T.tensor([[1, 2, 3, 4], [5, 6, 7, 8]])
        self.assertEqual(T.slice_last(x, 1, 3).tolist(),
                         [[2, 3], [6, 7]])


class TestBackward(unittest.TestCase):
    def test_elementwise(self):
        a, b = rand((2, 3), 1), rand((2, 3), 2, 0.5, 2.0)
        check(self, T.add, [a, b])
        check(self, T.sub, [a, b])
        check(self, T.mul, [a, b])
        check(self, T.div, [a, b])
        check(self, T.neg, [a])
        check(self, lambda x: T.pow(x, 3), [a])
        check(self, T.exp, [a])
        check(self, T.log, [b])
        check(self, T.tanh, [a])

    def test_broadcast_backward_sums_over_axes(self):
        x, bias = rand((4, 3), 3), rand((3,), 4)
        check(self, T.add, [x, bias])
        col = rand((4, 1), 5)
        check(self, T.mul, [x, col])
        # 편향의 기울기는 행을 따라 더한 값이어야 한다
        x2 = rand((4, 3), 6)
        b2 = rand((3,), 7)
        T.sum(T.add(x2, b2)).backward()
        self.assertEqual(b2.grad, [4.0, 4.0, 4.0])

    def test_scalar_operand(self):
        a = rand((2, 2), 8)
        check(self, lambda x: T.mul(T.add(x, 2.0), 0.5), [a])

    def test_matmul(self):
        check(self, T.matmul, [rand((3, 4), 9), rand((4, 2), 10)])

    def test_batched_matmul(self):
        check(self, T.matmul,
              [rand((2, 3, 4), 11), rand((2, 4, 5), 12)])
        # 뒤가 2차원이면 배치 축으로 퍼진다 — 기울기는 배치로 더한다
        check(self, T.matmul, [rand((2, 3, 4), 13), rand((4, 5), 14)])

    def test_shape_ops(self):
        a = rand((2, 3, 4), 15)
        check(self, lambda x: T.transpose(x, 1, 2), [a])
        check(self, lambda x: T.permute(x, (2, 0, 1)), [a])
        check(self, lambda x: T.reshape(x, (6, 4)), [a])
        check(self, lambda x: T.slice_last(x, 1, 3), [a])

    def test_reductions(self):
        a = rand((2, 3, 4), 16)
        check(self, lambda x: T.sum(x, 1), [a])
        check(self, lambda x: T.sum(x, -1, keepdims=True), [a])
        check(self, lambda x: T.mean(x, 0), [a])

    def test_reuse_accumulates(self):
        a = rand((2, 2), 17)
        check(self, lambda x: T.mul(x, x), [a])
        check(self, lambda x: T.add(T.matmul(x, x), x), [a])

    def test_zero_grad_and_no_grad_leaf(self):
        a = rand((2, 2), 18)
        c = T.tensor([[1, 2], [3, 4]])
        loss = T.sum(T.mul(a, c))
        loss.backward()
        self.assertIsNone(c.grad)
        first = list(a.grad)
        T.zero_grad(loss)
        loss.backward()
        self.assertEqual(a.grad, first)


class TestHelpers(unittest.TestCase):
    def test_rel_error(self):
        self.assertEqual(T.rel_error([1.0, 2.0], [1.0, 2.0]), 0.0)
        # 최대 차이 0.2 를 두 벡터 중 큰 크기 2.2 로 나눈다
        got = T.rel_error([1.0, 2.0], [1.0, 2.2])
        self.assertAlmostEqual(got, 0.2 / 2.2)

    def test_randn_uses_spec_rng(self):
        t = T.randn((2, 2), Rng(42), 1.0)
        want = [Rng(42).normal()]
        self.assertEqual(t.data[0], want[0])


if __name__ == '__main__':
    unittest.main()
