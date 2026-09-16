# -*- coding: utf-8 -*-
"""텍스트 생성 — 확률에서 토큰으로, 그리고 KV 캐시 (SPEC.md §7).

  · 거르개: 온도로 로짓을 나누고, 확률 차례로 top-k·top-p 를 남긴 뒤
    남은 확률에서 난수 하나로 뽑는다. 온도 0 은 argmax.
  · KV 캐시: 새 토큰 하나를 더할 때 앞 토큰들의 키·값은 변하지 않는다
    (인과 마스크 덕분에 과거는 미래를 안 본다). 그러니 키·값을 저장해
    두고 새 토큰의 질의 하나만 계산하면 된다. 토큰당 비용이
    O(n·d² + n²·d) 에서 O(d² + n·d) 로 준다.

forward_cached 는 Tensor 를 쓰지 않고 float 리스트로 직접 계산한다.
학습이 아니라 추론이라 기울기가 필요 없고, c/sample.c 가 이 모양
그대로다. 곱셈을 더하는 차례를 tensor.matmul 과 같게 두어, 전체를
다시 계산한 로짓과 ≤ 1e-9 로 맞는다(시험).
"""
import math

from transformerlib import ops
from transformerlib import posenc
from transformerlib import tensor as T
from transformerlib.rng import Rng


# ---- 거르개와 뽑기 ----
def filtered(logits, temperature, top_k, top_p):
    """[(토큰, 확률)] — 확률 내림차순(같으면 작은 id), 합 1."""
    z = [v / temperature for v in logits]
    p = [0.0] * len(z)
    ops._softmax_row(z, 0, len(z), p)
    order = sorted(range(len(p)), key=lambda k: (-p[k], k))
    if top_k:
        order = order[:top_k]
    s = math.fsum(p[k] for k in order)
    kept = [(k, p[k] / s) for k in order]
    if top_p is not None:
        acc = 0.0
        for n, (_, q) in enumerate(kept):
            acc += q
            if acc >= top_p:
                kept = kept[:n + 1]
                break
        s = math.fsum(q for _, q in kept)
        kept = [(k, q / s) for k, q in kept]
    return kept


def sample_next(logits, temperature, top_k, top_p, rng):
    if temperature == 0.0:
        return max(range(len(logits)), key=lambda k: (logits[k], -k))
    kept = filtered(logits, temperature, top_k, top_p)
    u = rng.uniform()
    acc = 0.0
    for k, q in kept:
        acc += q
        if u < acc:
            return k
    return kept[-1][0]            # 반올림으로 합이 1 에 못 미친 경우


# ---- KV 캐시 ----
class KVCache(object):
    """블록마다 위치별 키·값(헤드를 이어 붙인 폭 d 벡터)."""

    def __init__(self, cfg):
        self.k = [[] for _ in range(cfg.L)]
        self.v = [[] for _ in range(cfg.L)]
        self.n = 0


def _linear(x, W, b, n_in, n_out):
    """y = x W + b. 더하는 차례가 tensor.matmul(i-k-j) 과 같다."""
    y = [0.0] * n_out
    for k in range(n_in):
        xk, row = x[k], k * n_out
        for j in range(n_out):
            y[j] += xk * W[row + j]
    return [y[j] + b[j] for j in range(n_out)]


def _layernorm(x, g, b):
    n = len(x)
    mu = math.fsum(x) / n
    var = math.fsum((v - mu) ** 2 for v in x) / n
    s = math.sqrt(var + ops.LN_EPS)
    return [g[j] * ((x[j] - mu) / s) + b[j] for j in range(n)]


def _gelu(v):
    t = math.tanh(ops.GELU_A * (v + ops.GELU_B * v * v * v))
    return 0.5 * v * (1.0 + t)


def forward_cached(params, cfg, token, cache):
    """토큰 하나를 더하고 그 위치의 로짓(길이 V)을 돌려준다."""
    pos = cache.n
    if pos >= cfg.T:
        raise ValueError('캐시가 문맥 %d 을 넘는다' % cfg.T)
    P = {k: t.data for k, t in params.items()}
    d, h, V = cfg.d, cfg.h, cfg.V
    dk = d // h
    x = P['wte'][token * d:(token + 1) * d]
    if cfg.pos == 'learned':
        x = [a + b for a, b in zip(x, P['wpe'][pos * d:(pos + 1) * d])]
    elif cfg.pos == 'sin':
        x = [a + b for a, b in zip(x, posenc.sinusoidal(pos + 1, d)
                                   .data[pos * d:])]
    for l in range(cfg.L):
        p = 'h%d.' % l
        a = _layernorm(x, P[p + 'ln1_g'], P[p + 'ln1_b'])
        qkv = _linear(a, P[p + 'Wqkv'], P[p + 'bqkv'], d, 3 * d)
        q, k, v = qkv[:d], qkv[d:2 * d], qkv[2 * d:]
        if cfg.pos == 'rope':
            q = posenc.rope(T.Tensor(q, (h, 1, dk)), offset=pos).data
            k = posenc.rope(T.Tensor(k, (h, 1, dk)), offset=pos).data
        cache.k[l].append(k)
        cache.v[l].append(v)
        out = [0.0] * d
        inv = 1.0 / math.sqrt(dk)
        for j in range(h):
            o = j * dk
            s = []
            for kt in cache.k[l]:
                acc = 0.0
                for c in range(dk):
                    acc += q[o + c] * kt[o + c]
                s.append(acc * inv)
            w = [0.0] * len(s)
            ops._softmax_row(s, 0, len(s), w)
            for t, vt in enumerate(cache.v[l]):
                for c in range(dk):
                    out[o + c] += w[t] * vt[o + c]
        o = _linear(out, P[p + 'Wo'], P[p + 'bo'], d, d)
        x = [a + b for a, b in zip(x, o)]
        m = _layernorm(x, P[p + 'ln2_g'], P[p + 'ln2_b'])
        f = [_gelu(u) for u in _linear(m, P[p + 'W1'], P[p + 'b1'], d,
                                       cfg.d_ff)]
        f = _linear(f, P[p + 'W2'], P[p + 'b2'], cfg.d_ff, d)
        x = [a + b for a, b in zip(x, f)]
    cache.n += 1
    x = _layernorm(x, P['lnf_g'], P['lnf_b'])
    # 묶인 출력 사영: 로짓[t] = x · wte[t]
    W = P['wte']
    logits = []
    for t in range(V):
        acc = 0.0
        for c in range(d):
            acc += x[c] * W[t * d + c]
        logits.append(acc)
    return logits


# ---- 생성 ----
def window(ctx, T_):
    """문맥이 T 에 닿으면 뒤쪽 ⌊T/2⌋ 만 남긴다 (SPEC §7)."""
    return ctx[-(T_ // 2):] if len(ctx) >= T_ else ctx


def generate(params, cfg, prompt, n_new, temperature, top_k, top_p,
             seed, use_cache=True):
    """프롬프트 뒤에 n_new 토큰을 붙인 전체 id 리스트."""
    from transformerlib import model as M
    rng = Rng(seed)
    ids = list(prompt)
    ctx = list(prompt)
    cache, fed = None, 0
    for _ in range(n_new):
        new_ctx = window(ctx, cfg.T)
        if new_ctx is not ctx or cache is None:
            ctx, cache, fed = list(new_ctx), KVCache(cfg), 0
        if use_cache:
            for tok in ctx[fed:]:
                row = forward_cached(params, cfg, tok, cache)
            fed = len(ctx)
        else:
            logits, _ = M.forward(params, cfg, [ctx])
            row = logits.data[len(logits.data) - cfg.V:]
        tok = sample_next(row, temperature, top_k, top_p, rng)
        ids.append(tok)
        ctx.append(tok)
    return ids
