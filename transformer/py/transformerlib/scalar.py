# -*- coding: utf-8 -*-
"""스칼라 자동미분 — 값 하나와 그 기울기를 함께 든 수.

트랜스포머의 역전파는 결국 이 파일의 일을 텐서 단위로 하는 것이다.
여기서는 수 하나짜리로 원리만 본다.

  · 순전파: 연산을 할 때마다 결과 노드가 "누구에게서 왔나(prev)" 와
    "나를 흔들면 입력이 얼마나 흔들리나(_back)" 를 기억한다.
  · 역전파: 출력의 기울기를 1 로 두고, 노드를 위상정렬의 **역순**으로
    돌며 _back 을 부른다. 한 노드의 기울기가 다 모인 다음에만 그
    노드를 지나가야 하므로 역순이어야 한다.
  · 기울기는 **더한다**(+=). 한 노드가 여러 곳에 쓰이면 기울기는
    그 길들의 합이다(연쇄법칙의 다변수 꼴).

순전파·역전파 모두 노드 수에 대해 O(N) 시간, 그래프 저장에 O(N) 공간.
"""
import math


class Value(object):
    __slots__ = ('data', 'grad', 'prev', 'op', '_back')

    def __init__(self, data, prev=(), op=''):
        self.data = float(data)
        self.grad = 0.0
        self.prev = prev
        self.op = op
        self._back = None

    def __repr__(self):
        return 'Value(%.6g, grad=%.6g)' % (self.data, self.grad)

    # -- 이항 연산 --
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')

        def back():
            # 덧셈은 기울기를 그대로 나눠 준다
            self.grad += out.grad
            other.grad += out.grad
        out._back = back
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')

        def back():
            # 곱셈은 상대의 값을 곱해 돌려준다
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._back = back
        return out

    def __pow__(self, k):
        """지수는 상수만. x^y 에서 y 로도 미분하려면 exp·log 로 짠다."""
        assert isinstance(k, (int, float))
        out = Value(self.data ** k, (self,), '**%g' % k)

        def back():
            self.grad += k * self.data ** (k - 1) * out.grad
        out._back = back
        return out

    # -- 단항 연산 --
    def exp(self):
        e = math.exp(self.data)
        out = Value(e, (self,), 'exp')

        def back():
            # (eˣ)' = eˣ — 순전파의 값을 다시 쓴다
            self.grad += e * out.grad
        out._back = back
        return out

    def log(self):
        out = Value(math.log(self.data), (self,), 'log')

        def back():
            self.grad += out.grad / self.data
        out._back = back
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), 'tanh')

        def back():
            self.grad += (1.0 - t * t) * out.grad
        out._back = back
        return out

    def relu(self):
        y = self.data if self.data > 0 else 0.0
        out = Value(y, (self,), 'relu')

        def back():
            # 0 에서의 기울기는 0 으로 정한다(관례)
            self.grad += (1.0 if self.data > 0 else 0.0) * out.grad
        out._back = back
        return out

    # -- 나머지는 위의 것들로 --
    def __neg__(self):
        return self * -1.0

    def __sub__(self, other):
        return self + (-other)

    def __truediv__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return self * other ** -1.0

    def __radd__(self, other):
        return self + other

    def __rsub__(self, other):
        return Value(other) - self

    def __rmul__(self, other):
        return self * other

    def __rtruediv__(self, other):
        return Value(other) / self

    def backward(self):
        """이 노드를 출력으로 보고 모든 조상의 기울기를 채운다."""
        order = topo_order(self)
        self.grad = 1.0
        for v in reversed(order):
            if v._back is not None:
                v._back()


def topo_order(root):
    """입력이 늘 먼저 오는 차례. 재귀 대신 명시적 스택을 쓴다 —
    5000 단 사슬이면 파이썬 재귀 한도(1000)에 걸린다. O(N)."""
    order, seen = [], set()
    stack = [(root, False)]
    while stack:
        v, done = stack.pop()
        if done:
            order.append(v)
            continue
        if id(v) in seen:
            continue
        seen.add(id(v))
        stack.append((v, True))
        for p in v.prev:
            if id(p) not in seen:
                stack.append((p, False))
    return order


def zero_grad(root):
    for v in topo_order(root):
        v.grad = 0.0


def example_graph(x1=0.5, x2=-1.5, x3=2.0):
    """3부가 손으로 푸는 12노드 그래프. (출력, [x1, x2, x3]).

        n4 = x1·x2      n5 = n4 + x3     n6 = tanh n5
        n7 = exp x1     n8 = n6·n7       n9 = x3²
        n10 = log n9    n11 = n8 + n10   n12 = relu n11
    """
    a, b, c = Value(x1), Value(x2), Value(x3)
    n4 = a * b
    n5 = n4 + c
    n6 = n5.tanh()
    n7 = a.exp()
    n8 = n6 * n7
    n9 = c ** 2
    n10 = n9.log()
    n11 = n8 + n10
    n12 = n11.relu()
    return n12, [a, b, c]
