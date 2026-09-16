# -*- coding: utf-8 -*-
"""어텐션 — 질의·키·값에서 멀티헤드까지.

    Attention(Q, K, V) = softmax(Q Kᵀ / √d_k + 마스크) V

한 줄짜리 식이지만 이 파일의 세 함수가 각각 한 가지 질문에 답한다.

  · dot_variance — 왜 √d_k 로 나누나. q, k 의 성분이 독립이고 평균 0,
    분산 1 이면 q·k = Σ qᵢkᵢ 의 분산은 d_k 다(항마다 분산 1, 서로 독립).
    나누지 않으면 d_k 가 클수록 점수가 퍼져 소프트맥스가 한 칸으로
    쏠리고, 쏠린 소프트맥스는 기울기가 거의 0 이다.
  · scaled_dot_product — 식 그대로. 인과 마스크는 ops.causal_softmax.
  · multi_head_attention — 폭 d 를 h 조각으로 나눠 조각마다 따로
    어텐션하고 다시 잇는다. 한 행렬 Wqkv 로 q·k·v 를 한 번에 사영한다
    (SPEC §3). 비용은 점수 행렬이 O(B·h·n²·d_k) = O(B·n²·d),
    사영이 O(B·n·d²).

역전파는 tensor·ops 의 연산이 이미 알고 있으므로 여기서 따로 짜지
않는다. 시험이 전체를 차분과 견준다.
"""
import math

from transformerlib import ops
from transformerlib import tensor as T


def dot_variance(d, samples, rng):
    """(q·k 의 분산, (q·k)/√d 의 분산) — 표본 평균을 빼고 잰다."""
    raw = []
    for _ in range(samples):
        q = [rng.normal() for _ in range(d)]
        k = [rng.normal() for _ in range(d)]
        raw.append(math.fsum(a * b for a, b in zip(q, k)))

    def var(xs):
        m = math.fsum(xs) / len(xs)
        return math.fsum((x - m) ** 2 for x in xs) / len(xs)
    return var(raw), var([x / math.sqrt(d) for x in raw])


def max_weight_mean(d, n, trials, rng, scale=True):
    """질의 하나와 키 n 개의 소프트맥스에서 가장 큰 가중치의 평균.
    1 에 가까우면 어텐션이 사실상 argmax 가 된 것이다."""
    acc = 0.0
    for _ in range(trials):
        q = [rng.normal() for _ in range(d)]
        s = []
        for _ in range(n):
            k = [rng.normal() for _ in range(d)]
            dot = math.fsum(a * b for a, b in zip(q, k))
            s.append(dot / math.sqrt(d) if scale else dot)
        acc += max(ops.softmax(T.Tensor(s, (n,))).data)
    return acc / trials


def scaled_dot_product(q, k, v, causal=True):
    """q, k, v: (…, n, d_k). (출력 (…, n, d_k), 가중치 (…, n, n))."""
    dk = q.shape[-1]
    scores = T.mul(T.matmul(q, T.transpose(k, -1, -2)),
                   1.0 / math.sqrt(dk))
    w = ops.causal_softmax(scores) if causal else ops.softmax(scores)
    return T.matmul(w, v), w


def split_heads(x, h):
    """(B, n, d) → (B, h, n, d/h). 헤드 j 는 열 j·d_k ‥ (SPEC §3.1)."""
    B, n, d = x.shape
    if d % h:
        raise ValueError('폭 %d 를 헤드 %d 개로 못 나눈다' % (d, h))
    return T.permute(T.reshape(x, (B, n, h, d // h)), (0, 2, 1, 3))


def merge_heads(x):
    """(B, h, n, d_k) → (B, n, h·d_k). split_heads 의 역."""
    B, h, n, dk = x.shape
    return T.reshape(T.permute(x, (0, 2, 1, 3)), (B, n, h * dk))


def multi_head_attention(x, Wqkv, bqkv, Wo, bo, heads, causal=True,
                         rotate=None):
    """x: (B, n, d). (출력 (B, n, d), 가중치 (B, h, n, n)).

    rotate(t, 'q'|'k') 가 있으면 헤드로 나눈 q·k 에 적용한다 — RoPE 가
    쓰는 자리다(posenc.py). 값 v 는 돌리지 않는다.
    """
    d = x.shape[-1]
    qkv = T.add(T.matmul(x, Wqkv), bqkv)
    q = split_heads(T.slice_last(qkv, 0, d), heads)
    k = split_heads(T.slice_last(qkv, d, 2 * d), heads)
    v = split_heads(T.slice_last(qkv, 2 * d, 3 * d), heads)
    if rotate is not None:
        q = rotate(q, 'q')
        k = rotate(k, 'k')
    out, w = scaled_dot_product(q, k, v, causal)
    return T.add(T.matmul(merge_heads(out), Wo), bo), w
