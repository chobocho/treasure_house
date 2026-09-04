# -*- coding: utf-8 -*-
"""자동미분 — 손으로 도함수를 유도하지 않는 방법.

   수치미분(1부 4장)은 절단오차와 반올림오차 사이에서 타협해야 했다. 자동미분은
   그 타협이 없다. 미분은 근사가 아니라 <b>연쇄법칙을 기계적으로 적용한 것</b>이고,
   결과는 손으로 유도한 식과 기계정밀도까지 같다.

   두 가지 방식이 있고, 비용 구조가 정반대다.

     전방(forward)  · 입력 변수 하나마다 한 번씩 훑는다.  ℝⁿ→ℝᵐ 에서 O(n) 회 평가.
                      구현이 아주 단순하다(이중수 하나면 끝).  n 이 작을 때 유리.
     역방(reverse)  · 값을 한 번 계산하며 계산 그래프를 기록하고, 거꾸로 훑으며
                      민감도를 전파한다.  O(1) 회 평가로 기울기 전체를 얻는다.
                      n 이 클 때 — 곧 기계학습에서 — 유일한 선택. 역전파가 이것이다.

   이 파일은 두 방식을 각각 60줄 남짓으로 구현한다. 실제 라이브러리와 다른 점은
   벡터화·그래프 최적화·메모리 관리뿐이고, 수학은 정확히 이것이다.
"""
import math


# ================================================================ 전방 모드

class Dual(object):
    """이중수 a + bε  (ε² = 0).

       테일러 전개 f(a + bε) = f(a) + b f′(a) ε + (b²/2)f″(a)ε² + …  에서
       ε² = 0 이므로 뒤가 전부 사라진다. 즉 이중수로 계산하면 실수부에 함숫값이,
       ε 부에 도함수가 <b>정확히</b> 담긴다. 근사가 아니다.
    """

    __slots__ = ('a', 'b')

    def __init__(self, a, b=0.0):
        self.a = float(a)
        self.b = float(b)

    # 산술 — 각 규칙이 곧 미분 공식이다
    def __add__(self, o):
        o = _dual(o)
        return Dual(self.a + o.a, self.b + o.b)

    def __radd__(self, o):
        return _dual(o) + self

    def __sub__(self, o):
        o = _dual(o)
        return Dual(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        return _dual(o) - self

    def __mul__(self, o):                       # (uv)′ = u′v + uv′
        o = _dual(o)
        return Dual(self.a * o.a, self.b * o.a + self.a * o.b)

    def __rmul__(self, o):
        return _dual(o) * self

    def __truediv__(self, o):                   # (u/v)′ = (u′v − uv′)/v²
        o = _dual(o)
        return Dual(self.a / o.a, (self.b * o.a - self.a * o.b) / (o.a * o.a))

    def __rtruediv__(self, o):
        return _dual(o) / self

    def __neg__(self):
        return Dual(-self.a, -self.b)

    def __pow__(self, k):                       # (uᵏ)′ = k uᵏ⁻¹ u′  (k 는 상수)
        return Dual(self.a ** k, k * self.a ** (k - 1) * self.b)

    def __repr__(self):
        return 'Dual(%g, %g)' % (self.a, self.b)


def _dual(v):
    return v if isinstance(v, Dual) else Dual(v)


# 초등함수 — Dual 과 float 을 모두 받는다. 그래야 같은 코드를 두 방식에 다 쓴다.
def _lift(fx, dfx):
    def wrapper(v):
        if isinstance(v, Dual):
            return Dual(fx(v.a), dfx(v.a) * v.b)
        if isinstance(v, Node):
            return _node_unary(v, fx, dfx)
        return fx(v)
    return wrapper


exp = _lift(math.exp, math.exp)
log = _lift(math.log, lambda t: 1.0 / t)
sin = _lift(math.sin, math.cos)
cos = _lift(math.cos, lambda t: -math.sin(t))
sqrt = _lift(math.sqrt, lambda t: 0.5 / math.sqrt(t))
tanh = _lift(math.tanh, lambda t: 1.0 - math.tanh(t) ** 2)


def fsum(seq):
    """math.fsum 의 자동미분 대응판.

       math.fsum 은 float 만 받는다. 그런데 이 교재의 시험함수들은 반올림 오차를
       없애려고 math.fsum 을 쓴다. 둘을 함께 쓰려면 형에 따라 갈라야 한다:
       실수면 math.fsum(정확한 합), 이중수·그래프 마디면 보통의 덧셈.
       자동미분을 기존 코드에 얹을 때 실제로 부딪히는 종류의 문제라서
       숨기지 않고 그대로 둔다.
    """
    items = list(seq)
    if any(isinstance(v, (Dual, Node)) for v in items):
        acc = items[0] if items else 0.0
        for v in items[1:]:
            acc = acc + v
        return acc
    return math.fsum(items)


def grad_forward(f, x):
    """전방 모드 기울기. f 를 len(x) 번 호출한다.

       i 번째 호출에서 xᵢ 의 ε 부만 1 로 두면, 결과의 ε 부가 ∂f/∂xᵢ 다.
    """
    n = len(x)
    g = [0.0] * n
    for i in range(n):
        args = [Dual(x[j], 1.0 if j == i else 0.0) for j in range(n)]
        out = f(args)
        g[i] = out.b if isinstance(out, Dual) else 0.0
    return g


# ================================================================ 역방향 모드

class Node(object):
    """계산 그래프의 한 마디. 값과 '부모에 대한 국소 도함수'를 함께 들고 있다.

       역전파는 이 그래프를 위상 역순으로 훑으며 adjoint ∂f/∂(이 마디) 를 쌓는다.
       메모리를 값 하나가 아니라 '계산 전체'만큼 쓴다는 것이 역방향의 대가다.
    """

    __slots__ = ('v', 'parents', 'grad')

    def __init__(self, v, parents=()):
        self.v = float(v)
        self.parents = parents        # ((부모 Node, ∂self/∂부모), …)
        self.grad = 0.0

    def __add__(self, o):
        o = _node(o)
        return Node(self.v + o.v, ((self, 1.0), (o, 1.0)))

    def __radd__(self, o):
        return _node(o) + self

    def __sub__(self, o):
        o = _node(o)
        return Node(self.v - o.v, ((self, 1.0), (o, -1.0)))

    def __rsub__(self, o):
        return _node(o) - self

    def __mul__(self, o):
        o = _node(o)
        return Node(self.v * o.v, ((self, o.v), (o, self.v)))

    def __rmul__(self, o):
        return _node(o) * self

    def __truediv__(self, o):
        o = _node(o)
        return Node(self.v / o.v, ((self, 1.0 / o.v), (o, -self.v / (o.v * o.v))))

    def __rtruediv__(self, o):
        return _node(o) / self

    def __neg__(self):
        return Node(-self.v, ((self, -1.0),))

    def __pow__(self, k):
        return Node(self.v ** k, ((self, k * self.v ** (k - 1)),))

    def __repr__(self):
        return 'Node(%g)' % self.v


def _node(v):
    return v if isinstance(v, Node) else Node(v)


def _node_unary(v, fx, dfx):
    return Node(fx(v.v), ((v, dfx(v.v)),))


def _topo(root):
    """그래프를 위상 정렬한다. 재귀 대신 명시적 스택 — 깊은 그래프에서 파이썬의
       재귀 한도(기본 1000)에 걸리지 않게 하려는 것이다."""
    order, seen = [], set()
    stack = [(root, False)]
    while stack:
        node, done = stack.pop()
        if done:
            order.append(node)
            continue
        if id(node) in seen:
            continue
        seen.add(id(node))
        stack.append((node, True))
        for parent, _ in node.parents:
            if id(parent) not in seen:
                stack.append((parent, False))
    return order


def grad_reverse(f, x):
    """역방향 모드 기울기. f 를 <b>한 번만</b> 호출한다.

       O(그래프 크기) 시간·공간. n 이 아무리 커도 평가 한 번이면 되는 것이
       신경망 학습이 가능한 이유다.
    """
    nodes = [Node(v) for v in x]
    out = f(nodes)
    out = _node(out)
    for nd in _topo(out):
        nd.grad = 0.0
    out.grad = 1.0
    for nd in reversed(_topo(out)):
        for parent, local in nd.parents:
            parent.grad += nd.grad * local     # 연쇄법칙: ∂f/∂p += ∂f/∂n · ∂n/∂p
    return [nd.grad for nd in nodes]
