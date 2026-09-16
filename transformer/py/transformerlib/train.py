# -*- coding: utf-8 -*-
"""학습 — 배치를 뽑고, 한 스텝을 밟고, 체크포인트로 남긴다.

    배치(SPEC §6.1) → 순전파·손실 → 역전파 → 기울기 자르기(§6.3)
    → 학습률 일정(§6.4) → AdamW(§6.2)

이 파일의 차례가 곧 c/train.c 의 차례다. 파이썬은 설명을 맡고 아주
작은 모델만 학습한다(d ≤ 32, 문맥 ≤ 16). 실제 학습은 C 가 한다.

체크포인트는 SPEC §4 의 바이트 배치 그대로다. 파이썬의 float64 는
쓸 때 float32 로 반올림된다 — 읽어서 다시 쓰면 같은 바이트가 나온다
(float32 → float64 는 정확하고, 되돌리면 원래 float32 다).
"""
import io
import struct

from transformerlib import model as M
from transformerlib import optim
from transformerlib.rng import Rng


# ---- 배치 ----
def batch_starts(tokens, T, newline=None):
    """시작 가능 위치. newline 을 주면 줄 머리만(SPEC §6.1 aligned)."""
    last = len(tokens) - T - 1
    if last < 0:
        raise ValueError('토큰 %d개로는 길이 %d 창을 못 만든다'
                         % (len(tokens), T))
    if newline is None:
        return list(range(last + 1))
    return [i for i in range(last + 1)
            if i == 0 or tokens[i - 1] == newline]


def get_batch(tokens, starts, B, T, rng):
    """행마다 randint 하나. (입력 B×T, 정답 B×T) — 정답은 한 칸 뒤."""
    xs, ys = [], []
    for _ in range(B):
        s = starts[rng.randint(len(starts))]
        xs.append(tokens[s:s + T])
        ys.append(tokens[s + 1:s + T + 1])
    return xs, ys


# ---- 한 스텝 ----
def make_optimizer(params):
    return optim.AdamW(params, wd=0.1, beta1=0.9, beta2=0.95, eps=1e-8)


def step(params, cfg, opt, x, y, lr, clip=1.0):
    """(손실, 자르기 전 기울기 노름)."""
    for t in params.values():
        t.grad = None
    _, loss = M.forward(params, cfg, x, y)
    loss.backward()
    norm = optim.clip_grad_norm(params, clip)
    opt.step(params, lr)
    return loss.data[0], norm


def train(cfg, tokens, steps, B, lr_max, warmup, seed, lr_min=None,
          newline=None, on_step=None):
    """(파라미터, 기록 [(스텝, 손실, 학습률, 노름)]). 씨앗이 같으면
    같은 결과 — 초기화는 seed, 배치는 seed + 1 (SPEC §1.5)."""
    lr_min = lr_max / 10.0 if lr_min is None else lr_min
    params = M.init_params(cfg, seed)
    opt = make_optimizer(params)
    starts = batch_starts(tokens, cfg.T, newline)
    rng = Rng(seed + 1)
    log = []
    for t in range(1, steps + 1):
        x, y = get_batch(tokens, starts, B, cfg.T, rng)
        lr = optim.lr_schedule(t, lr_max, lr_min, warmup, steps)
        loss, norm = step(params, cfg, opt, x, y, lr)
        log.append((t, loss, lr, norm))
        if on_step is not None:
            on_step(t, loss, lr, norm)
    return params, log


def eval_loss(params, cfg, tokens, B, max_batches=None):
    """앞에서부터 겹치지 않는 창으로 잰 평균 손실. 뽑기가 없어 늘 같다.
    """
    T = cfg.T
    windows = list(range(0, len(tokens) - T, T))
    total, n = 0.0, 0
    for b in range(0, len(windows) - B + 1, B):
        if max_batches is not None and n >= max_batches:
            break
        xs = [tokens[s:s + T] for s in windows[b:b + B]]
        ys = [tokens[s + 1:s + T + 1] for s in windows[b:b + B]]
        total += M.forward(params, cfg, xs, ys)[1].data[0]
        n += 1
    return total / max(1, n)


def task_accuracy(params, cfg, examples, prompt_len):
    """과제 줄마다 앞 prompt_len 토큰을 주고 나머지를 greedy 로 만든다.
    (정답률, [(프롬프트, 만든 것, 정답)]). 전체를 매번 다시 계산한다 —
    KV 캐시는 10부(sample.py)의 일이다."""
    rows, good = [], 0
    for ex in examples:
        ids = list(ex[:prompt_len])
        want = list(ex[prompt_len:])
        made = []
        for _ in want:
            logits, _ = M.forward(params, cfg, [ids[-cfg.T:]])
            V, last = cfg.V, len(logits.data) - cfg.V
            row = logits.data[last:last + V]
            nxt = max(range(V), key=lambda k: (row[k], -k))
            made.append(nxt)
            ids.append(nxt)
        good += made == want
        rows.append((ex[:prompt_len], made, want))
    return float(good) / max(1, len(examples)), rows


# ---- 체크포인트 (SPEC §4) ----
def save_ckpt(path, cfg, params):
    flags = 1 | (M.POS_KINDS.index(cfg.pos) << 1)
    with io.open(path, 'wb') as f:
        f.write(struct.pack('<4s7i', b'TFS1', cfg.V, cfg.T, cfg.d,
                            cfg.L, cfg.h, cfg.d_ff, flags))
        for name in M.param_names(cfg):
            data = params[name].data
            f.write(struct.pack('<%df' % len(data), *data))


def load_ckpt(path):
    raw = io.open(path, 'rb').read()
    magic, V, T, d, L, h, d_ff, flags = struct.unpack('<4s7i', raw[:32])
    if magic != b'TFS1':
        raise ValueError('체크포인트가 아니다: %r' % magic)
    pos = M.POS_KINDS[(flags >> 1) & 3]
    cfg = M.Config(V, T, d, L, h, d_ff, pos=pos)
    params = M.init_params(cfg, 0)
    off = 32
    for name, shape, _ in M.shapes(cfg):
        n = len(params[name].data)
        params[name].data = list(struct.unpack('<%df' % n,
                                               raw[off:off + 4 * n]))
        off += 4 * n
    if off != len(raw):
        raise ValueError('체크포인트 길이가 설정과 맞지 않는다')
    return cfg, params


def save_opt(path, opt, cfg):
    with io.open(path, 'wb') as f:
        f.write(struct.pack('<4si', b'TFO1', opt.t))
        for table in (opt.m, opt.v):
            for name in M.param_names(cfg):
                f.write(struct.pack('<%df' % len(table[name]),
                                    *table[name]))


def load_opt(path, opt, cfg):
    raw = io.open(path, 'rb').read()
    magic, opt.t = struct.unpack('<4si', raw[:8])
    if magic != b'TFO1':
        raise ValueError('옵티마이저 상태가 아니다: %r' % magic)
    off = 8
    for table in (opt.m, opt.v):
        for name in M.param_names(cfg):
            n = len(table[name])
            table[name] = list(struct.unpack('<%df' % n,
                                             raw[off:off + 4 * n]))
            off += 4 * n
