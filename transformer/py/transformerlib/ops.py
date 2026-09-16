# -*- coding: utf-8 -*-
"""트랜스포머의 부품 — 순전파와 **손으로 유도한** 역전파를 한 몸으로.

tensor.py 의 작은 연산을 이어 붙여도 같은 기울기가 나온다. 그래도
소프트맥스·교차엔트로피·레이어놈을 따로 짜는 까닭은 셋이다.

  1. 식이 짧아진다. CE 의 로짓 기울기는 결국 (p − y)/N 한 줄이다.
     작은 연산 열 개를 지나며 계산하면 같은 값을 돌아서 얻는다.
  2. 수치가 안정하다. exp 를 따로 하면 큰 로짓에서 넘친다.
  3. C 커널(c/ops.c)이 이 모양 그대로다. 파이썬과 C 가 같은 식을
     같은 차례로 계산해야 9부의 대조가 뜻을 갖는다.

모든 연산은 마지막 축을 따라 행마다 따로 계산한다.
시간은 전부 O(칸 수), 역전파도 같다.
"""
import math

from transformerlib import tensor as T

# SPEC.md §3.3 — √(2/π) 를 17자리로, 3차항은 Hendrycks·Gimpel §2.
GELU_A = 0.7978845608028654
GELU_B = 0.044715
LN_EPS = 1e-5


def _rows(x):
    """(행 수, 행 길이) — 마지막 축이 한 행이다."""
    n = x.shape[-1]
    return len(x.data) // n, n


def _softmax_row(z, off, n, out):
    """한 행의 소프트맥스. 최댓값을 먼저 빼 exp 가 넘치지 않게 한다.
    결과는 같다 — 분자·분모에 같은 e^{−max} 가 곱해질 뿐이다."""
    m = max(z[off:off + n])
    if m == -math.inf:
        raise ValueError('행 전체가 −∞ 다')
    e = [math.exp(z[off + j] - m) for j in range(n)]
    s = math.fsum(e)
    for j in range(n):
        out[off + j] = e[j] / s


def softmax(x):
    """pᵢ = e^{xᵢ} / Σⱼ e^{xⱼ}.

    역전파: J = diag(p) − p pᵀ 이므로 dx = p ⊙ (g − ⟨g, p⟩).
    야코비안 n×n 을 만들지 않고 내적 한 번으로 끝낸다 — O(n).
    """
    rows, n = _rows(x)
    P = [0.0] * len(x.data)
    for r in range(rows):
        _softmax_row(x.data, r * n, n, P)

    def back():
        g, gx = out.grad, T.need(x)
        for r in range(rows):
            o = r * n
            dot = math.fsum(g[o + j] * P[o + j] for j in range(n))
            for j in range(n):
                gx[o + j] += P[o + j] * (g[o + j] - dot)
    out = T.make(P, x.shape, (x,), back, 'softmax')
    return out


def softmax_jacobian(p):
    """∂pᵢ/∂xⱼ = pᵢ(δᵢⱼ − pⱼ). 시험과 2부의 표를 위한 것이다."""
    n = len(p)
    return [[p[i] * ((1.0 if i == j else 0.0) - p[j]) for j in range(n)]
            for i in range(n)]


def log_softmax(x):
    """log pᵢ = xᵢ − (m + log Σ e^{xⱼ − m}), m = max x — 로그합지수.

    역전파: dx = g − p · Σg.
    """
    rows, n = _rows(x)
    Y = [0.0] * len(x.data)
    P = [0.0] * len(x.data)
    for r in range(rows):
        o = r * n
        m = max(x.data[o:o + n])
        lse = m + math.log(math.fsum(math.exp(x.data[o + j] - m)
                                     for j in range(n)))
        for j in range(n):
            Y[o + j] = x.data[o + j] - lse
            P[o + j] = math.exp(Y[o + j])

    def back():
        g, gx = out.grad, T.need(x)
        for r in range(rows):
            o = r * n
            gs = math.fsum(g[o:o + n])
            for j in range(n):
                gx[o + j] += g[o + j] - P[o + j] * gs
    out = T.make(Y, x.shape, (x,), back, 'log_softmax')
    return out


def cross_entropy(logits, targets):
    """ℓ = −(1/N) Σ log p[정답] — 로그소프트맥스와 한 몸으로.

    역전파가 이 연산의 요점이다: ∂ℓ/∂로짓 = (p − y) / N.
    y 는 정답 칸만 1 인 원-핫. 유도는 4부에 있고, 시험이 이 한 줄과
    구현이 칸마다 같은지 본다. targets 는 행 차례의 정수 리스트.
    """
    rows, n = _rows(logits)
    if len(targets) != rows:
        raise ValueError('정답 %d개, 행 %d개' % (len(targets), rows))
    Z = logits.data
    P = [0.0] * len(Z)
    nll = []
    for r in range(rows):
        t = targets[r]
        if not 0 <= t < n:
            raise ValueError('정답 %d 가 어휘 %d 밖' % (t, n))
        o = r * n
        m = max(Z[o:o + n])
        lse = m + math.log(math.fsum(math.exp(Z[o + j] - m)
                                     for j in range(n)))
        nll.append(lse - Z[o + t])
        _softmax_row(Z, o, n, P)
    loss = math.fsum(nll) / rows

    def back():
        g0, gz = out.grad[0], T.need(logits)
        scale = g0 / rows
        for r in range(rows):
            o = r * n
            for j in range(n):
                y = 1.0 if j == targets[r] else 0.0
                gz[o + j] += (P[o + j] - y) * scale
    out = T.make([loss], (), (logits,), back, 'cross_entropy')
    return out


def layernorm(x, g, b, eps=LN_EPS):
    """y = g ⊙ x̂ + b,  x̂ = (x − μ)/σ,  σ = √(분산 + ε) — 행마다.

    역전파(4부에서 유도한다): d = dy ⊙ g 라 두면
        dx = (1/σ) · (d − mean(d) − x̂ · mean(d ⊙ x̂))
        dg = Σ dy ⊙ x̂,   db = Σ dy   (행을 따라 더한다)
    μ 와 σ 가 행의 모든 칸에 기대므로 칸마다의 기울기가 서로 섞인다 —
    mean(d) 와 mean(d ⊙ x̂) 두 항이 그 섞임이다.
    """
    rows, n = _rows(x)
    X, G, B = x.data, g.data, b.data
    Y = [0.0] * len(X)
    XH = [0.0] * len(X)
    SIG = [0.0] * rows
    for r in range(rows):
        o = r * n
        mu = math.fsum(X[o:o + n]) / n
        var = math.fsum((X[o + j] - mu) ** 2 for j in range(n)) / n
        s = math.sqrt(var + eps)
        SIG[r] = s
        for j in range(n):
            XH[o + j] = (X[o + j] - mu) / s
            Y[o + j] = G[j] * XH[o + j] + B[j]

    def back():
        dy, gx, gg, gb = out.grad, T.need(x), T.need(g), T.need(b)
        for r in range(rows):
            o = r * n
            d = [dy[o + j] * G[j] for j in range(n)]
            md = math.fsum(d) / n
            mdx = math.fsum(d[j] * XH[o + j] for j in range(n)) / n
            for j in range(n):
                if gx is not None:
                    gx[o + j] += (d[j] - md - XH[o + j] * mdx) / SIG[r]
                if gg is not None:
                    gg[j] += dy[o + j] * XH[o + j]
                if gb is not None:
                    gb[j] += dy[o + j]
    out = T.make(Y, x.shape, (x, g, b), back, 'layernorm')
    return out


def gelu(x):
    """GELU 의 tanh 근사 — ½x(1 + tanh(A(x + Bx³))), SPEC §3.3.

    미분: ½(1 + t) + ½x(1 − t²)·A(1 + 3Bx²),  t = tanh(A(x + Bx³)).
    x = 0 이면 t = 0 이라 정확히 ½ 이다.
    """
    X = x.data
    TT = [math.tanh(GELU_A * (v + GELU_B * v * v * v)) for v in X]
    Y = [0.5 * v * (1.0 + t) for v, t in zip(X, TT)]

    def back():
        g, gx = out.grad, T.need(x)
        for k, (v, t) in enumerate(zip(X, TT)):
            d = (0.5 * (1.0 + t) + 0.5 * v * (1.0 - t * t) * GELU_A
                 * (1.0 + 3.0 * GELU_B * v * v))
            gx[k] += d * g[k]
    out = T.make(Y, x.shape, (x,), back, 'gelu')
    return out


def gelu_exact(v):
    """정의 그대로: x·Φ(x) = ½x(1 + erf(x/√2)). 근사와 견주려고 둔다."""
    return 0.5 * v * (1.0 + math.erf(v / math.sqrt(2.0)))


def embedding(weight, ids):
    """weight[V, d] 에서 ids 의 행을 꺼낸다. ids 는 (중첩) 정수 리스트.

    역전파는 뽑아 간 행에 기울기를 **더해** 돌려준다(scatter-add).
    같은 토큰이 두 번 나오면 그 행은 두 몫을 받는다.
    """
    V, d = weight.shape
    shape, flat = [], []
    x = ids
    while isinstance(x, (list, tuple)):
        shape.append(len(x))
        x = x[0] if x else 0

    def walk(v):
        if isinstance(v, (list, tuple)):
            for u in v:
                walk(u)
        else:
            flat.append(v)
    walk(ids)
    W = weight.data
    data = []
    for t in flat:
        if not 0 <= t < V:
            raise IndexError('토큰 %d 가 어휘 %d 밖' % (t, V))
        data.extend(W[t * d:(t + 1) * d])

    def back():
        g, gw = out.grad, T.need(weight)
        for k, t in enumerate(flat):
            for j in range(d):
                gw[t * d + j] += g[k * d + j]
    out = T.make(data, tuple(shape) + (d,), (weight,), back,
                 'embedding')
    return out


def dropout(x, p, rng):
    """확률 p 로 칸을 0 으로, 살아남은 칸은 1/(1−p) 배 — 기댓값 유지.

    p = 0 이면 x 를 그대로 돌려주고 난수를 하나도 뽑지 않는다.
    기록 실행은 전부 p = 0 이다(SPEC §1.5) — 그래야 C 와 대조된다.
    """
    if p == 0.0:
        return x
    scale = 1.0 / (1.0 - p)
    M = [0.0 if rng.uniform() < p else scale for _ in x.data]

    def back():
        g, gx = out.grad, T.need(x)
        for k in range(len(M)):
            gx[k] += M[k] * g[k]
    out = T.make([v * m for v, m in zip(x.data, M)], x.shape, (x,),
                 back, 'dropout')
    return out


def causal_softmax(s):
    """(…, n, n) 점수의 i 행을 j ≤ i 칸에서만 소프트맥스한다.

    j > i 칸에 −∞ 를 더하고 소프트맥스한 것과 같다(시험이 확인한다).
    −∞ 를 실제로 더하지 않고 그 칸을 건너뛰는 편이 C 에서도 싸다.
    역전파는 softmax 와 같은 식을 j ≤ i 칸에서만.
    """
    n = s.shape[-1]
    if len(s.shape) < 2 or s.shape[-2] != n:
        raise ValueError('causal_softmax 는 (…, n, n)')
    rows = len(s.data) // n
    P = [0.0] * len(s.data)
    for r in range(rows):
        i = r % n
        _softmax_row(s.data, r * n, i + 1, P)

    def back():
        g, gs = out.grad, T.need(s)
        for r in range(rows):
            o, i = r * n, r % n
            dot = math.fsum(g[o + j] * P[o + j] for j in range(i + 1))
            for j in range(i + 1):
                gs[o + j] += P[o + j] * (g[o + j] - dot)
    out = T.make(P, s.shape, (s,), back, 'causal_softmax')
    return out
