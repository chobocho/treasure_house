# -*- coding: utf-8 -*-
"""GPT 형 디코더 — 부품을 쌓아 언어 모델 한 대 (SPEC.md §3).

    x = wte[토큰] + 위치
    블록마다:  x = x + Attn(LN1(x))
               x = x + FFN(LN2(x))
    로짓 = LNf(x) · wteᵀ

  · 잔차 스트림: 블록은 x 를 바꾸지 않고 **더한다**. 역전파에서 덧셈은
    기울기를 그대로 통과시키므로 깊어져도 기울기 길이 끊기지 않는다.
  · pre-LN: 정규화를 블록 **앞**에 둔다(GPT-2). 잔차 길 위에는 아무
    연산도 없다 — 7부에서 post-LN 과 견준다.
  · 출력 사영을 임베딩과 묶는다: 로짓 = h · wteᵀ. 파라미터 V·d 개를
    아끼고, "토큰의 뜻" 을 들어올 때와 나갈 때 같은 표로 읽는다.

파라미터 이름과 차례가 곧 체크포인트 차례다(SPEC §4). C 가 같은
차례로 읽고 쓴다.
"""
import math

from transformerlib import attention
from transformerlib import ops
from transformerlib import posenc
from transformerlib import tensor as T
from transformerlib.rng import Rng

POS_KINDS = ('learned', 'sin', 'rope')      # flags 비트 1‥2 의 0·1·2


class Config(object):
    """V 어휘 · T 최대 문맥 · d 폭 · L 블록 · h 헤드 · d_ff FFN 폭."""

    def __init__(self, V, T, d, L, h, d_ff, pos='learned'):
        if d % h:
            raise ValueError('d=%d 를 h=%d 로 못 나눈다' % (d, h))
        if pos not in POS_KINDS:
            raise ValueError('위치 방식 %r' % pos)
        if pos != 'learned' and (d // h) % 2:
            raise ValueError('sin·rope 는 헤드 폭이 짝수여야 한다')
        self.V, self.T, self.d, self.L = V, T, d, L
        self.h, self.d_ff, self.pos = h, d_ff, pos

    def __repr__(self):
        return ('Config(V=%d, T=%d, d=%d, L=%d, h=%d, d_ff=%d, pos=%s)'
                % (self.V, self.T, self.d, self.L, self.h, self.d_ff,
                   self.pos))


def shapes(cfg):
    """[(이름, 모양, 초기화)] — SPEC §4 의 체크포인트 차례 그대로.
    초기화: 'w' normal·0.02 · 'r' normal·0.02/√(2L) · 'one' · 'zero'."""
    d, f = cfg.d, cfg.d_ff
    out = [('wte', (cfg.V, d), 'w')]
    if cfg.pos == 'learned':
        out.append(('wpe', (cfg.T, d), 'w'))
    for l in range(cfg.L):
        p = 'h%d.' % l
        out += [(p + 'ln1_g', (d,), 'one'), (p + 'ln1_b', (d,), 'zero'),
                (p + 'Wqkv', (d, 3 * d), 'w'),
                (p + 'bqkv', (3 * d,), 'zero'),
                (p + 'Wo', (d, d), 'r'), (p + 'bo', (d,), 'zero'),
                (p + 'ln2_g', (d,), 'one'), (p + 'ln2_b', (d,), 'zero'),
                (p + 'W1', (d, f), 'w'), (p + 'b1', (f,), 'zero'),
                (p + 'W2', (f, d), 'r'), (p + 'b2', (d,), 'zero')]
    out += [('lnf_g', (d,), 'one'), ('lnf_b', (d,), 'zero')]
    return out


def param_names(cfg):
    return [n for n, _, _ in shapes(cfg)]


def count_params(cfg):
    """V·d + T·d(learned) + L·(블록) + 2d.
    d_ff = 4d 면 블록은 12d² + 13d.

    블록 = LN 둘(4d) + Wqkv·bqkv(3d² + 3d) + Wo·bo(d² + d)
          + W1·b1(d·d_ff + d_ff) + W2·b2(d_ff·d + d)
    """
    d, f = cfg.d, cfg.d_ff
    block = 4 * d + 3 * d * d + 3 * d + d * d + d + 2 * d * f + f + d
    pos = cfg.T * d if cfg.pos == 'learned' else 0
    return cfg.V * d + pos + cfg.L * block + 2 * d


def bert_params(V, T, d, L, types=2):
    """BERT 인코더(post-LN) — GPT 식과 어디가 다른지 7부가 짚는다.

    임베딩 셋(토큰 V·d, 위치 T·d, 문장 종류 types·d) + 임베딩 LN(2d)
    + 블록 L·(12d² + 13d) + 풀러(d² + d). 출력 사영은 세지 않는다.
    """
    return (V * d + T * d + types * d + 2 * d
            + L * (12 * d * d + 13 * d) + d * d + d)


def init_params(cfg, seed):
    """{이름: Tensor}. 초기화 생성기에서 차례로 뽑는다(SPEC §3.5)."""
    r = Rng(seed)
    res = 0.02 / math.sqrt(2 * cfg.L)
    out = {}
    for name, shape, how in shapes(cfg):
        n = T.numel(shape)
        if how == 'w':
            data = [r.normal() * 0.02 for _ in range(n)]
        elif how == 'r':
            data = [r.normal() * res for _ in range(n)]
        else:
            data = [1.0 if how == 'one' else 0.0] * n
        out[name] = T.Tensor(data, shape, requires_grad=True)
    return out


def linear(x, W, b):
    """Y = X W + b — 가중치는 [입력, 출력] (SPEC §2)."""
    return T.add(T.matmul(x, W), b)


def forward(params, cfg, ids, targets=None, attn_out=None, causal=True):
    """ids: B×n 정수. (로짓 (B, n, V), 손실 또는 None).

    attn_out 에 리스트를 주면 블록마다 어텐션 가중치 (B, h, n, n) 를
    담아 준다 — 6부의 어텐션 지도가 이것이다. causal=False 는 BERT 식
    인코더(11부 extras.mlm_loss)가 미래까지 보게 할 때만 쓴다.
    """
    B, n = len(ids), len(ids[0])
    if n > cfg.T:
        raise ValueError('길이 %d 가 문맥 %d 보다 길다' % (n, cfg.T))
    P = params
    x = ops.embedding(P['wte'], ids)
    if cfg.pos == 'learned':
        x = T.add(x, ops.embedding(P['wpe'], [list(range(n))]))
    elif cfg.pos == 'sin':
        x = T.add(x, posenc.sinusoidal(n, cfg.d))
    rotate = None
    if cfg.pos == 'rope':
        rotate = lambda t, which: posenc.rope(t)
    for l in range(cfg.L):
        p = 'h%d.' % l
        a = ops.layernorm(x, P[p + 'ln1_g'], P[p + 'ln1_b'])
        o, w = attention.multi_head_attention(
            a, P[p + 'Wqkv'], P[p + 'bqkv'], P[p + 'Wo'], P[p + 'bo'],
            cfg.h, causal=causal, rotate=rotate)
        if attn_out is not None:
            attn_out.append(w)
        x = T.add(x, o)
        m = ops.layernorm(x, P[p + 'ln2_g'], P[p + 'ln2_b'])
        f = linear(ops.gelu(linear(m, P[p + 'W1'], P[p + 'b1'])),
                   P[p + 'W2'], P[p + 'b2'])
        x = T.add(x, f)
    x = ops.layernorm(x, P['lnf_g'], P['lnf_b'])
    logits = T.matmul(x, T.transpose(P['wte'], 0, 1))
    if targets is None:
        return logits, None
    flat = [t for row in targets for t in row]
    loss = ops.cross_entropy(T.reshape(logits, (B * n, cfg.V)), flat)
    return logits, loss


def matmul_mults(cfg, n):
    """길이 n 한 줄의 순전파에서 행렬곱이 하는 곱셈 수 — 정확히.

    블록마다  사영 n·(3d² + d² + 2·d·d_ff)
             점수 Q Kᵀ 와 가중합 W V 가 각각 h·n²·d_k = n²·d
    출력 사영 n·d·V
    (tensor.MULTS 계수기로 시험이 확인한다.)
    """
    d, f = cfg.d, cfg.d_ff
    per_block = n * (4 * d * d + 2 * d * f) + 2 * n * n * d
    return cfg.L * per_block + n * d * cfg.V


def train_flops_per_token(cfg, n):
    """토큰 하나를 학습하는 FLOPs.

    곱셈 하나 + 덧셈 하나를 2 FLOPs 로 치면 순전파는 곱셈 수의 2배,
    역전파는 순전파의 2배(입력 쪽·가중치 쪽 기울기 둘)라 합이 3배.
    그래서 6 × (토큰당 곱셈 수). 곱셈 수가 대략 N 이라 "6N" 이다.
    """
    return 6.0 * matmul_mults(cfg, n) / n
