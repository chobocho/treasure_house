# -*- coding: utf-8 -*-
"""텐서 자동미분 — 모양이 있는 값과 그 기울기.

scalar.py 의 원리를 그대로 넓혔다. 달라진 것은 둘뿐이다.

  1. 값이 수 하나가 아니라 **행 우선으로 편 float 리스트 + 모양**이다
     (SPEC.md §2). (i, j) 는 i·열수 + j 번째 칸이다.
  2. 모양이 다른 둘을 더하면 작은 쪽이 **퍼진다**(브로드캐스팅).
     그래서 역전파는 퍼졌던 축을 따라 기울기를 **더해** 돌려준다.
     한 칸이 출력의 여러 칸에 쓰였으니, 스칼라에서 "두 번 쓴 노드의
     기울기는 더한다" 와 같은 규칙이다.

퍼짐은 "출력 칸 → 입력 칸" 색인표 하나로 푼다(_index_map). 순전파는
그 표로 값을 읽고, 역전파는 같은 표로 기울기를 쌓는다. 연산마다
O(출력 칸 수) 시간·공간이다. numpy 없이 짠 까닭은 PLAN.md §9 결정 2.

모듈 이름 sum·pow 가 내장 함수를 가리므로 이 파일 안에서는
builtins 의 것을 _bsum 으로 부른다.
"""
import builtins
import math

_bsum = builtins.sum

# 순전파 행렬곱이 실제로 한 곱셈 수. model.matmul_mults 의 식이 맞는지
# 시험이 이 계수기로 확인한다(7부의 FLOPs 계산).
MULTS = [0]


def numel(shape):
    n = 1
    for s in shape:
        n *= s
    return n


def strides(shape):
    """행 우선 보폭. (2, 3, 4) → (12, 4, 1)."""
    out, acc = [], 1
    for s in reversed(shape):
        out.append(acc)
        acc *= s
    return tuple(reversed(out))


def broadcast_shape(a, b):
    """오른쪽 끝부터 맞춘다. 크기가 같거나 한쪽이 1 이어야 한다."""
    n = max(len(a), len(b))
    a = (1,) * (n - len(a)) + tuple(a)
    b = (1,) * (n - len(b)) + tuple(b)
    out = []
    for x, y in zip(a, b):
        if x != y and 1 not in (x, y):
            raise ValueError('퍼질 수 없는 모양 %s · %s' % (a, b))
        out.append(max(x, y))
    return tuple(out)


def _index_map(src, out):
    """출력의 각 칸(행 우선)이 읽을 src 의 칸 번호. O(출력 칸 수).

    src 를 out 의 차원 수에 맞춰 앞에 1 을 붙이고, 크기 1 인 축은
    보폭을 0 으로 둔다 — 그 축을 따라 움직여도 같은 칸을 읽는다.
    """
    src = (1,) * (len(out) - len(src)) + tuple(src)
    st = strides(src)
    idx = [0]
    for d, n in enumerate(out):
        s = 0 if src[d] == 1 else st[d]
        idx = [base + k * s for base in idx for k in range(n)]
    return idx


class Tensor(object):
    __slots__ = ('data', 'shape', 'grad', 'requires_grad',
                 'prev', '_back', 'op')

    def __init__(self, data, shape, requires_grad=False):
        shape = tuple(shape)
        if len(data) != numel(shape):
            raise ValueError('값 %d개로 모양 %s 를 못 만든다'
                             % (len(data), shape))
        self.data = [float(x) for x in data]
        self.shape = shape
        self.requires_grad = requires_grad
        self.grad = None
        self.prev = ()
        self._back = None
        self.op = ''

    def __repr__(self):
        return 'Tensor(shape=%s, op=%s)' % (self.shape,
                                            self.op or 'leaf')

    def tolist(self):
        def build(off, dims):
            if not dims:
                return self.data[off]
            step = numel(dims[1:])
            return [build(off + i * step, dims[1:])
                    for i in range(dims[0])]
        return build(0, self.shape)

    def backward(self):
        """스칼라 출력에서 시작해 모든 조상의 기울기를 채운다."""
        if numel(self.shape) != 1:
            raise ValueError('backward 는 칸이 하나인 출력에서만')
        order = topo_order(self)
        for v in order:
            if v.requires_grad and v.grad is None:
                v.grad = [0.0] * len(v.data)
        self.grad = [1.0]
        for v in reversed(order):
            if v._back is not None:
                v._back()


def make(data, shape, prev, back, op):
    """연산 결과 노드. 입력 중 하나라도 기울기가 필요하면 기록한다."""
    out = Tensor.__new__(Tensor)
    out.data, out.shape = data, tuple(shape)
    out.requires_grad = any(p.requires_grad for p in prev)
    out.grad, out.op = None, op
    out.prev = prev if out.requires_grad else ()
    out._back = back if out.requires_grad else None
    return out


def need(t):
    """기울기를 쌓을 자리. 기울기가 필요 없는 입력이면 None."""
    if not t.requires_grad:
        return None
    if t.grad is None:
        t.grad = [0.0] * len(t.data)
    return t.grad


def topo_order(root):
    """입력이 먼저 오는 차례 — scalar.topo_order 와 같다. O(노드 수)."""
    order, seen, stack = [], set(), [(root, False)]
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
        v.grad = [0.0] * len(v.data) if v.requires_grad else None


# ---- 만들기 ----
def tensor(nested, requires_grad=False):
    shape, x = [], nested
    while isinstance(x, (list, tuple)):
        shape.append(len(x))
        x = x[0]
    flat = []

    def walk(v):
        if isinstance(v, (list, tuple)):
            for u in v:
                walk(u)
        else:
            flat.append(v)
    walk(nested)
    return Tensor(flat, shape, requires_grad)


def zeros(shape, requires_grad=False):
    return Tensor([0.0] * numel(shape), shape, requires_grad)


def randn(shape, rng, std, requires_grad=False):
    """SPEC §3.5 — 행 우선 차례로 normal() × std."""
    return Tensor([rng.normal() * std for _ in range(numel(shape))],
                  shape, requires_grad)


def lift(x):
    return x if isinstance(x, Tensor) else Tensor([x], ())


# ---- 원소별 연산 ----
def _binary(a, b, f, da, db, op):
    """f(x, y) 와 그 편미분 da(x, y), db(x, y) 로 이항 연산 하나."""
    a, b = lift(a), lift(b)
    shape = broadcast_shape(a.shape, b.shape)
    ia, ib = _index_map(a.shape, shape), _index_map(b.shape, shape)
    A, B = a.data, b.data
    data = [f(A[i], B[j]) for i, j in zip(ia, ib)]

    def back():
        g, ga, gb = out.grad, need(a), need(b)
        for k, (i, j) in enumerate(zip(ia, ib)):
            if ga is not None:
                ga[i] += da(A[i], B[j]) * g[k]     # 퍼진 칸은 더한다
            if gb is not None:
                gb[j] += db(A[i], B[j]) * g[k]
    out = make(data, shape, (a, b), back, op)
    return out


def add(a, b):
    return _binary(a, b, lambda x, y: x + y,
                   lambda x, y: 1.0, lambda x, y: 1.0, 'add')


def sub(a, b):
    return _binary(a, b, lambda x, y: x - y,
                   lambda x, y: 1.0, lambda x, y: -1.0, 'sub')


def mul(a, b):
    return _binary(a, b, lambda x, y: x * y,
                   lambda x, y: y, lambda x, y: x, 'mul')


def div(a, b):
    return _binary(a, b, lambda x, y: x / y,
                   lambda x, y: 1.0 / y,
                   lambda x, y: -x / (y * y), 'div')


def _unary(a, f, df, op):
    """df(x, y) — y 는 순전파 결과. exp·tanh 는 y 로 미분이 싸다."""
    X = a.data
    Y = [f(x) for x in X]

    def back():
        g, ga = out.grad, need(a)
        for k in range(len(X)):
            ga[k] += df(X[k], Y[k]) * g[k]
    out = make(Y, a.shape, (a,), back, op)
    return out


def neg(a):
    return _unary(a, lambda x: -x, lambda x, y: -1.0, 'neg')


def pow(a, k):
    return _unary(a, lambda x: x ** k,
                  lambda x, y: k * x ** (k - 1), 'pow')


def exp(a):
    return _unary(a, math.exp, lambda x, y: y, 'exp')


def log(a):
    return _unary(a, math.log, lambda x, y: 1.0 / x, 'log')


def tanh(a):
    return _unary(a, math.tanh, lambda x, y: 1.0 - y * y, 'tanh')


# ---- 행렬곱 ----
def matmul(a, b):
    """(…, n, m) @ (…, m, p) → (…, n, p). 앞의 배치 축은 퍼진다.

    루프 차례는 i-k-j 다. 안쪽 루프가 b 의 한 행을 앞에서부터 읽으므로
    캐시에 친절하다 — 9부에서 C 로 세 차례를 견준다.
    순전파 O(배치·n·m·p), 역전파도 같다.
    역전파:  dA = dY Bᵀ,   dB = Aᵀ dY   (배치로 퍼졌으면 더한다)
    """
    if len(a.shape) < 2 or len(b.shape) < 2:
        raise ValueError('matmul 은 2차원 이상')
    n, m = a.shape[-2:]
    m2, p = b.shape[-2:]
    if m != m2:
        raise ValueError('matmul 모양 %s @ %s' % (a.shape, b.shape))
    batch = broadcast_shape(a.shape[:-2], b.shape[:-2])
    ma = _index_map(a.shape[:-2], batch)
    mb = _index_map(b.shape[:-2], batch)
    A, B = a.data, b.data
    O = [0.0] * (numel(batch) * n * p)
    MULTS[0] += numel(batch) * n * m * p
    for t in range(numel(batch)):
        oa, ob, oo = ma[t] * n * m, mb[t] * m * p, t * n * p
        for i in range(n):
            ro = oo + i * p
            for k in range(m):
                aik = A[oa + i * m + k]
                rb = ob + k * p
                for j in range(p):
                    O[ro + j] += aik * B[rb + j]

    def back():
        g, ga, gb = out.grad, need(a), need(b)
        for t in range(numel(batch)):
            oa, ob, oo = ma[t] * n * m, mb[t] * m * p, t * n * p
            for i in range(n):
                ro = oo + i * p
                for k in range(m):
                    rb = ob + k * p
                    if ga is not None:
                        s = 0.0
                        for j in range(p):
                            s += g[ro + j] * B[rb + j]
                        ga[oa + i * m + k] += s
                    if gb is not None:
                        aik = A[oa + i * m + k]
                        for j in range(p):
                            gb[rb + j] += aik * g[ro + j]
    out = make(O, batch + (n, p), (a, b), back, 'matmul')
    return out


# ---- 모양 바꾸기 ----
def _gather(a, idx, shape, op):
    """출력 k 칸 = 입력 idx[k] 칸. 역전파는 같은 표로 되돌려 쌓는다."""
    A = a.data

    def back():
        g, ga = out.grad, need(a)
        for k, i in enumerate(idx):
            ga[i] += g[k]
    out = make([A[i] for i in idx], shape, (a,), back, op)
    return out


def permute(a, axes):
    st = strides(a.shape)
    shape = tuple(a.shape[d] for d in axes)
    idx = [0]
    for d, n in zip(axes, shape):
        idx = [base + k * st[d] for base in idx for k in range(n)]
    return _gather(a, idx, shape, 'permute')


def transpose(a, i, j):
    axes = list(range(len(a.shape)))
    axes[i], axes[j] = axes[j], axes[i]
    return permute(a, axes)


def reshape(a, shape):
    if numel(shape) != len(a.data):
        raise ValueError('reshape %s → %s' % (a.shape, shape))
    return _gather(a, list(range(len(a.data))), shape, 'reshape')


def slice_last(a, start, stop):
    """마지막 축의 [start, stop) — q·k·v 를 한 행렬에서 떼어 낸다."""
    last = a.shape[-1]
    outer = len(a.data) // last
    w = stop - start
    idx = [r * last + start + c for r in range(outer) for c in range(w)]
    return _gather(a, idx, a.shape[:-1] + (w,), 'slice')


# ---- 줄이기 ----
def sum(a, axis=None, keepdims=False):
    """axis 를 따라 더한다. 역전파는 더한 칸 모두에 같은 기울기를."""
    if axis is None:
        A = a.data

        def back_all():
            g0, ga = out_all.grad[0], need(a)
            for k in range(len(A)):
                ga[k] += g0
        out_all = make([math.fsum(A)], (), (a,), back_all, 'sum')
        return out_all
    axis %= len(a.shape)
    keep = a.shape[:axis] + (1,) + a.shape[axis + 1:]
    where = _index_map(keep, a.shape)      # 입력 칸 → 출력 칸
    O = [0.0] * numel(keep)
    for k, o in enumerate(where):
        O[o] += a.data[k]

    def back():
        g, ga = out.grad, need(a)
        for k, o in enumerate(where):
            ga[k] += g[o]
    shape = keep if keepdims else a.shape[:axis] + a.shape[axis + 1:]
    out = make(O, shape, (a,), back, 'sum')
    return out


def mean(a, axis=None, keepdims=False):
    n = len(a.data) if axis is None else a.shape[axis]
    return mul(sum(a, axis, keepdims), 1.0 / n)


# ---- 검증 도구 ----
def finite_difference(fn, x, h=1e-6):
    """fn() 의 x 에 대한 기울기를 중심 차분으로. 오차 O(h²).

    x.data 를 제자리에서 흔든다. fn 은 매번 그래프를 새로 만들어야
    한다 — 이미 만든 그래프의 값은 바뀌지 않는다. O(칸 수 × fn 비용).
    """
    grad = []
    for k in range(len(x.data)):
        v = x.data[k]
        x.data[k] = v + h
        fp = fn()
        x.data[k] = v - h
        fm = fn()
        x.data[k] = v
        grad.append((fp - fm) / (2.0 * h))
    return grad


def rel_error(a, b):
    """max|a−b| / max(max|a|, max|b|). 벡터 전체의 크기에 견준다 —
    칸마다 나누면 0 근처 칸의 차분 잡음이 부풀려진다."""
    diff = max(abs(x - y) for x, y in zip(a, b))
    scale = max(max(abs(x) for x in a), max(abs(y) for y in b), 1e-12)
    return diff / scale
