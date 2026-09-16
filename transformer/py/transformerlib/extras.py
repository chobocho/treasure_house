# -*- coding: utf-8 -*-
"""더 나아가기 — 큰 모델로 가는 길목의 기법 넷 (11부).

  · 온라인 소프트맥스 / 타일 어텐션: 가중치 n 개를 한꺼번에 들지 않고
    조각(타일)씩 읽으며 (지금까지의 최댓값 m, e^{x−m} 의 합 s,
    가중평균 o) 셋만 갱신한다. 조각이 새 최댓값을 가져오면 옛 합을
    e^{m−m′} 로 다시 잰다. FlashAttention 이 메모리를 O(n²) 에서 O(n)
    으로 줄이는 핵심이 이 갱신이다(GPU 메모리 계층은 다루지 않는다).
  · GQA/MQA: 질의 헤드는 h 개 그대로, 키·값 헤드는 g 개만 두고 나눠
    쓴다. KV 캐시가 h/g 배 준다. g = h 면 MHA, g = 1 이면 MQA.
  · LoRA: 얼린 W 옆에 낮은 계수 갱신 (α/r)·A·B 를 붙여 A, B 만 배운다.
    B 를 0 으로 시작하면 처음 출력은 원래 모델과 같다.
  · MLM: 토큰의 15% 를 가리고 양방향으로 맞힌다(BERT). 손실은 가린
    자리에서만.
"""
import math

from transformerlib import attention
from transformerlib import model as M
from transformerlib import ops
from transformerlib import tensor as T


# ---- 온라인 소프트맥스 ----
def _online(xs, vs, tile):
    """(m, s, o) — o 는 vs 가 없으면 None. O(n) 시간, O(tile) 공간."""
    m, s, o = -math.inf, 0.0, None
    if vs is not None:
        o = [0.0] * len(vs[0])
    for a in range(0, len(xs), tile):
        chunk = xs[a:a + tile]
        m2 = max(m, max(chunk))
        old = s * math.exp(m - m2) if s > 0.0 else 0.0
        e = [math.exp(x - m2) for x in chunk]
        s2 = old + math.fsum(e)
        if vs is not None:
            dv = len(o)
            o = [(o[c] * old + math.fsum(e[j] * vs[a + j][c]
                                         for j in range(len(e)))) / s2
                 for c in range(dv)]
        m, s = m2, s2
    return m, s, o


def online_logsumexp(xs, tile):
    m, s, _ = _online(xs, None, tile)
    return m + math.log(s)


def online_attention_row(xs, vs, tile):
    """Σⱼ softmax(x)ⱼ·vⱼ 를 조각씩 읽으며."""
    return _online(xs, vs, tile)[2]


def tiled_attention(q, k, v, tile):
    """(B, n, d_k) 인과 어텐션 출력을 행마다 조각씩. 값 리스트로."""
    B, n, dk = q.shape
    inv = 1.0 / math.sqrt(dk)
    Q, K, Vd = q.data, k.data, v.data
    out = []
    for b in range(B):
        o = b * n * dk
        vs = [Vd[o + j * dk:o + (j + 1) * dk] for j in range(n)]
        for i in range(n):
            xs = []
            for j in range(i + 1):
                acc = 0.0
                for c in range(dk):
                    acc += Q[o + i * dk + c] * K[o + j * dk + c]
                xs.append(acc * inv)
            out.extend(online_attention_row(xs, vs[:i + 1], tile))
    return out


# ---- GQA / MQA ----
def split_qkv(Wqkv, d):
    """[d, 3d] → Wq [d, d], Wkv [d, 2d] — 열을 나눈다."""
    rows = [Wqkv.data[r * 3 * d:(r + 1) * 3 * d] for r in range(d)]
    Wq = T.Tensor([x for row in rows for x in row[:d]], (d, d))
    Wkv = T.Tensor([x for row in rows for x in row[d:]], (d, 2 * d))
    return Wq, Wkv


def repeat_heads(t, rep):
    """(B, g, n, d_k) → (B, g·rep, n, d_k).
    질의 헤드 j 는 키 헤드 j//rep 를 쓴다."""
    B, g, n, dk = t.shape
    per = n * dk
    idx = [(b * g + hh // rep) * per + e
           for b in range(B) for hh in range(g * rep)
           for e in range(per)]
    return T._gather(t, idx, (B, g * rep, n, dk), 'repeat_heads')


def grouped_query_attention(x, Wq, bq, Wkv, bkv, Wo, bo, heads, groups):
    if heads % groups:
        raise ValueError('헤드 %d 를 그룹 %d 로 못 나눈다'
                         % (heads, groups))
    d = x.shape[-1]
    dk = d // heads
    q = attention.split_heads(M.linear(x, Wq, bq), heads)
    kv = M.linear(x, Wkv, bkv)
    k = attention.split_heads(T.slice_last(kv, 0, groups * dk), groups)
    v = attention.split_heads(T.slice_last(kv, groups * dk,
                                           2 * groups * dk), groups)
    rep = heads // groups
    out, _ = attention.scaled_dot_product(q, repeat_heads(k, rep),
                                          repeat_heads(v, rep))
    return M.linear(attention.merge_heads(out), Wo, bo)


def kv_cache_floats(cfg, n, groups):
    """길이 n 까지 캐시할 float 수: 키·값 × 블록 × 위치 × g × d_k."""
    return 2 * cfg.L * n * groups * (cfg.d // cfg.h)


# ---- LoRA ----
def lora_linear(x, W, b, A, B, alpha, r):
    """y = xW + b + (α/r)·(xA)B.  A [입력, r], B [r, 출력]."""
    base = T.add(T.matmul(x, W), b)
    delta = T.mul(T.matmul(T.matmul(x, A), B), alpha / r)
    return T.add(base, delta)


def lora_merge(W, A, B, alpha, r):
    """학습이 끝나면 W′ = W + (α/r)·AB 로 합쳐 추론 비용을 없앤다."""
    return T.add(W, T.mul(T.matmul(A, B), alpha / r))


def lora_params(d_in, d_out, r):
    return r * (d_in + d_out)


# ---- MLM ----
def mlm_mask(ids, rng, vocab, mask_id, p=0.15):
    """자리마다 확률 p 로 고른다. 고른 자리는 80% [MASK] · 10% 아무
    토큰 · 10% 그대로 (Devlin 외 3.1절). (입력, 고른 자리)."""
    inp, pos = list(ids), []
    for i in range(len(ids)):
        if rng.uniform() < p:
            pos.append(i)
            u = rng.uniform()
            if u < 0.8:
                inp[i] = mask_id
            elif u < 0.9:
                inp[i] = rng.randint(vocab)
    return inp, pos


def mlm_loss(params, cfg, ids, rng, mask_id, p_mask=0.15):
    """(손실, 입력, 고른 자리). 인과 마스크 없이 양방향으로 본다."""
    inp, pos = mlm_mask(ids, rng, cfg.V, mask_id, p_mask)
    if not pos:
        raise ValueError('가린 자리가 하나도 없다')
    logits, _ = M.forward(params, cfg, [inp], causal=False)
    V = cfg.V
    idx = [i * V + c for i in pos for c in range(V)]
    rows = T._gather(logits, idx, (len(pos), V), 'mlm_rows')
    return ops.cross_entropy(rows, [ids[i] for i in pos]), inp, pos
