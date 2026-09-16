# -*- coding: utf-8 -*-
"""옵티마이저 — SGD 에서 AdamW 까지, 그리고 학습률 일정 (SPEC.md §6).

파라미터는 {이름: Tensor} 이고 .grad 에 기울기가 들어 있다. 모든
옵티마이저는 원소마다 따로 도는 식이라 O(파라미터 수) 시간이다.
Adam 류는 원소마다 m·v 두 개를 더 들고 다닌다 — 메모리가 3배.

  · SGD:     θ ← θ − η g
  · 모멘텀:  v ← βv + g;  θ ← θ − η v   — 골짜기를 따라 속도를 모은다
  · Adam:    m, v 는 g, g² 의 지수이동평균. 처음엔 0 에서 출발해 작게
             치우치므로 1 − βᵗ 로 나눠 편다(편향 보정). 그러면 첫 스텝의
             갱신 크기가 g 의 크기와 무관하게 η 가 된다.
  · AdamW:   감쇠 wd·θ 를 m̂/√v̂ 옆에 **따로** 더한다. L2 를 g 에 더하면
             √v̂ 로 나뉘어 파라미터마다 감쇠가 달라진다 — 떼어 낸다.
"""
import math

DECAY_NAMES = ('wte', 'wpe', 'Wqkv', 'Wo', 'W1', 'W2')


def decays(name):
    """SPEC §6.2 — 행렬만 감쇠한다. 편향과 LN 은 줄이면 해만 된다."""
    return name.split('.')[-1] in DECAY_NAMES


def sgd_step(params, lr):
    for t in params.values():
        for k, g in enumerate(t.grad):
            t.data[k] -= lr * g


class Momentum(object):
    def __init__(self, beta=0.9):
        self.beta = beta
        self.v = {}

    def step(self, params, lr):
        for name, t in params.items():
            v = self.v.setdefault(name, [0.0] * len(t.data))
            for k, g in enumerate(t.grad):
                v[k] = self.beta * v[k] + g
                t.data[k] -= lr * v[k]


class AdamW(object):
    """wd = 0 이면 그냥 Adam 이다."""

    def __init__(self, params, wd=0.1, beta1=0.9, beta2=0.95, eps=1e-8,
                 bias_correction=True):
        self.wd, self.b1, self.b2, self.eps = wd, beta1, beta2, eps
        self.bias_correction = bias_correction
        self.m = dict((n, [0.0] * len(t.data))
                      for n, t in params.items())
        self.v = dict((n, [0.0] * len(t.data))
                      for n, t in params.items())
        self.t = 0

    def step(self, params, lr):
        self.t += 1
        b1, b2, eps = self.b1, self.b2, self.eps
        c1 = 1.0 - b1 ** self.t if self.bias_correction else 1.0
        c2 = 1.0 - b2 ** self.t if self.bias_correction else 1.0
        for name, t in params.items():
            m, v = self.m[name], self.v[name]
            wd = self.wd if decays(name) else 0.0
            for k, g in enumerate(t.grad):
                m[k] = b1 * m[k] + (1.0 - b1) * g
                v[k] = b2 * v[k] + (1.0 - b2) * g * g
                upd = (m[k] / c1) / (math.sqrt(v[k] / c2) + eps)
                t.data[k] -= lr * (upd + wd * t.data[k])


def clip_grad_norm(params, max_norm=1.0):
    """전체 L2 노름 n 이 max_norm 을 넘으면 max_norm/(n + 1e-6) 배.
    (자르기 전의) n 을 돌려준다 — 학습 기록에 적으려고. SPEC §6.3."""
    sq = 0.0
    for t in params.values():
        for g in t.grad:
            sq += g * g
    n = math.sqrt(sq)
    if n > max_norm:
        s = max_norm / (n + 1e-6)
        for t in params.values():
            t.grad[:] = [g * s for g in t.grad]
    return n


def lr_schedule(t, lr_max, lr_min, warmup, total):
    """워밍업(직선) 뒤 코사인으로 lr_min 까지. t 는 1 부터.
    SPEC §6.4."""
    if t <= warmup:
        return lr_max * t / warmup
    p = (t - warmup) / max(1, total - warmup)
    cos = 1.0 + math.cos(math.pi * p)
    return lr_min + 0.5 * (lr_max - lr_min) * cos


def noam(t, d_model, warmup):
    """Vaswani 외 식 (3) — 비교용.
    d^{−½}·min(t^{−½}, t·warmup^{−1.5})."""
    return d_model ** -0.5 * min(t ** -0.5, t * warmup ** -1.5)
