# -*- coding: utf-8 -*-
"""scalar 의 증인 시험 — 스칼라 자동미분 (PLAN.md §3.1 표 2행).

역전파가 맞는지 확인하는 방법은 하나뿐이다. 식을 조금 흔들어 보고
(중심 차분) 값이 바뀐 만큼이 기울기와 같은지 본다. 12개 노드짜리 예제
그래프 — 3부가 손으로 풀어 보이는 바로 그 그래프 — 에서 확인한다.
"""
import math
import unittest

from transformerlib import scalar
from transformerlib.scalar import Value


def fd(f, xs, i, h=1e-6):
    """i 번째 입력으로 f 를 중심 차분한다. 오차 O(h²)."""
    up = list(xs)
    dn = list(xs)
    up[i] += h
    dn[i] -= h
    return (f(up) - f(dn)) / (2 * h)


def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


class TestExampleGraph(unittest.TestCase):
    def test_has_twelve_nodes(self):
        out, leaves = scalar.example_graph()
        self.assertEqual(len(scalar.topo_order(out)), 12)
        self.assertEqual(len(leaves), 3)

    def test_gradients_match_finite_differences(self):
        out, leaves = scalar.example_graph()
        out.backward()
        xs = [v.data for v in leaves]
        f = lambda z: scalar.example_graph(*z)[0].data
        for i, v in enumerate(leaves):
            self.assertLess(rel(v.grad, fd(f, xs, i)), 1e-6, i)

    def test_forward_value_by_hand(self):
        out, _ = scalar.example_graph()
        n5 = 0.5 * -1.5 + 2.0
        want = math.tanh(n5) * math.exp(0.5) + math.log(4.0)
        self.assertAlmostEqual(out.data, want, places=12)


class TestOps(unittest.TestCase):
    def check(self, build, xs):
        vals = [Value(x) for x in xs]
        out = build(*vals)
        out.backward()
        f = lambda z: build(*[Value(t) for t in z]).data
        for i, v in enumerate(vals):
            self.assertLess(rel(v.grad, fd(f, xs, i)), 1e-6,
                            'input %d' % i)

    def test_each_op(self):
        self.check(lambda a, b: a + b, [1.5, -2.0])
        self.check(lambda a, b: a - b, [1.5, -2.0])
        self.check(lambda a, b: a * b, [1.5, -2.0])
        self.check(lambda a, b: a / b, [1.5, -2.0])
        self.check(lambda a: a ** 3, [0.7])
        self.check(lambda a: a ** -0.5, [2.3])
        self.check(lambda a: a.exp(), [0.3])
        self.check(lambda a: a.log(), [0.3])
        self.check(lambda a: a.tanh(), [0.3])
        self.check(lambda a: -a, [0.3])
        self.check(lambda a: 2 * a + 1 - a / 4, [0.3])

    def test_relu_both_sides(self):
        self.check(lambda a: a.relu(), [0.8])
        self.check(lambda a: a.relu(), [-0.8])


class TestChainRule(unittest.TestCase):
    def test_reused_node_accumulates(self):
        """x 를 두 번 쓰면 기울기는 두 길의 합 — d(x·x)/dx = 2x."""
        x = Value(3.0)
        (x * x).backward()
        self.assertEqual(x.grad, 6.0)

    def test_diamond(self):
        """a → b, a → c, (b, c) → d 인 마름모. 덮어쓰면 틀린다."""
        a = Value(2.0)
        b = a * 3
        c = a.exp()
        d = b * c
        d.backward()
        self.assertAlmostEqual(a.grad, 3 * math.exp(2) * 3, places=9)

    def test_topo_order_puts_inputs_first(self):
        out, leaves = scalar.example_graph()
        order = scalar.topo_order(out)
        pos = dict((id(v), i) for i, v in enumerate(order))
        for v in order:
            for p in v.prev:
                self.assertLess(pos[id(p)], pos[id(v)])
        self.assertIs(order[-1], out)

    def test_deep_chain_has_no_recursion_limit(self):
        x = Value(0.001)
        y = x
        for _ in range(5000):
            y = y + x
        y.backward()
        self.assertEqual(x.grad, 5001.0)

    def test_backward_twice_needs_zero_grad(self):
        x = Value(1.0)
        y = x * 2
        y.backward()
        scalar.zero_grad(y)
        y.backward()
        self.assertEqual(x.grad, 2.0)


if __name__ == '__main__':
    unittest.main()
