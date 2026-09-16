# -*- coding: utf-8 -*-
"""위치 인코딩 — 사인·학습·RoPE (SPEC.md §3.2).

어텐션은 차례를 모른다. 토큰을 섞어 넣어도 (마스크만 빼면) 같은
가중합이 나온다. 그래서 "몇 번째인가" 를 벡터에 넣어 줘야 한다.

  · 사인: PE(p, 2i) = sin(p·ωᵢ), PE(p, 2i+1) = cos(p·ωᵢ),
    ωᵢ = 10000^{−2i/d}. 학습할 것이 없고, p + k 의 인코딩이 p 의
    인코딩을 **p 와 무관한 회전**으로 돌린 것이라 상대 위치를
    선형으로 읽을 수 있다(shift_matrix 가 그 회전이다).
  · 학습: 위치마다 벡터 하나를 그냥 배운다(GPT-2 가 이것).
  · RoPE: 더하지 않고 q·k 를 위치만큼 **돌린다**. 그러면
    ⟨R_m q, R_n k⟩ = ⟨q, R_{n−m} k⟩ 라 점수가 m − n 에만 달린다.

모두 O(n·d) 시간.
"""
import math

from transformerlib import tensor as T


def _omega(i, d):
    return 1.0 / 10000.0 ** (2.0 * i / d)


def sinusoidal(n, d):
    """(n, d) 표. 파라미터가 아니므로 기울기를 받지 않는다."""
    if d % 2:
        raise ValueError('사인 인코딩은 짝수 폭만 (d=%d)' % d)
    data = []
    for p in range(n):
        for i in range(d // 2):
            data.append(math.sin(p * _omega(i, d)))
            data.append(math.cos(p * _omega(i, d)))
    return T.Tensor(data, (n, d))


def shift_matrix(k, d):
    """PE(p + k) = M_k · PE(p) 인 M_k — 짝 (2i, 2i+1) 마다 회전 블록.

    sin(a + b) = sin a cos b + cos a sin b
    cos(a + b) = cos a cos b − sin a sin b   에서 b = k·ωᵢ.
    """
    M = [[0.0] * d for _ in range(d)]
    for i in range(d // 2):
        c, s = math.cos(k * _omega(i, d)), math.sin(k * _omega(i, d))
        a, b = 2 * i, 2 * i + 1
        M[a][a], M[a][b] = c, s
        M[b][a], M[b][b] = -s, c
    return M


def learned(n, d, rng):
    """SPEC §3.5 — normal() × 0.02, 행 우선 차례."""
    return T.randn((n, d), rng, 0.02, requires_grad=True)


def rope(x, offset=0):
    """x: (…, n, d_k). 위치 p = offset + 행 번호 만큼 짝을 돌린다.

    (a, b) → (a cos θ − b sin θ, a sin θ + b cos θ),
    θ = p · 10000^{−2i/d_k}. 역전파는 같은 각도로 거꾸로(−θ) 돌린다 —
    회전 행렬의 전치가 역행렬이기 때문이다.
    """
    n, dk = x.shape[-2], x.shape[-1]
    if dk % 2:
        raise ValueError('RoPE 는 짝수 폭만 (d_k=%d)' % dk)
    X = x.data
    Y = [0.0] * len(X)
    per = n * dk
    cs = [(math.cos((offset + p) * _omega(i, dk)),
           math.sin((offset + p) * _omega(i, dk)))
          for p in range(n) for i in range(dk // 2)]
    for base in range(0, len(X), per):
        for p in range(n):
            o = base + p * dk
            for i in range(dk // 2):
                c, s = cs[p * (dk // 2) + i]
                a, b = X[o + 2 * i], X[o + 2 * i + 1]
                Y[o + 2 * i] = a * c - b * s
                Y[o + 2 * i + 1] = a * s + b * c

    def back():
        g, gx = out.grad, T.need(x)
        for base in range(0, len(X), per):
            for p in range(n):
                o = base + p * dk
                for i in range(dk // 2):
                    c, s = cs[p * (dk // 2) + i]
                    ga, gb = g[o + 2 * i], g[o + 2 * i + 1]
                    gx[o + 2 * i] += ga * c + gb * s
                    gx[o + 2 * i + 1] += -ga * s + gb * c
    out = T.make(Y, x.shape, (x,), back, 'rope')
    return out


def rope_dot(q, m, k, n):
    """⟨R_m q, R_n k⟩ — 시험과 7부 4장의 표를 위한 것."""
    dk = len(q)
    rq = rope(T.Tensor(q, (1, dk)), offset=m).data
    rk = rope(T.Tensor(k, (1, dk)), offset=n).data
    return math.fsum(a * b for a, b in zip(rq, rk))
