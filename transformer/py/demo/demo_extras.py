# -*- coding: utf-8 -*-
"""11부 — 온라인 소프트맥스, GQA, LoRA 를 숫자로."""
import math

from demo import report
from transformerlib import extras as X
from transformerlib import fmt, ops
from transformerlib import model as M
from transformerlib import tensor as T
from transformerlib.rng import Rng


def sec_online():
    r = Rng(1)
    n, dv = 37, 5
    xs = [r.normal() * 4 for _ in range(n)]
    vs = [[r.normal() for _ in range(dv)] for _ in range(n)]
    p = [0.0] * n
    ops._softmax_row(xs, 0, n, p)
    want = [math.fsum(p[j] * vs[j][c] for j in range(n))
            for c in range(dv)]
    rows = [['타일 크기', '동시에 드는 가중치', 'max|오차|']]
    for tile in (1, 4, 16, 37):
        got = X.online_attention_row(xs, vs, tile)
        err = max(abs(a - b) for a, b in zip(got, want))
        rows.append([str(tile), str(tile), '%.1e' % err])
    return (fmt.table(rows, align='rrr')
            + '\n\n키 37개. 한 번에 다 드는 대신 조각씩 읽어도 같은'
            + ' 가중합이다.')


def sec_gqa():
    rows = [['설정', '키·값 헤드 g', 'KV 캐시 float 수', 'MHA 대비']]
    c = M.Config(V=50257, T=1024, d=768, L=12, h=12, d_ff=3072)
    full = X.kv_cache_floats(c, 1024, 12)
    for name, g in (('MHA', 12), ('GQA 4', 4), ('GQA 2', 2),
                    ('MQA', 1)):
        n = X.kv_cache_floats(c, 1024, g)
        rows.append([name, str(g), '{:,}'.format(n),
                     '%.3f' % (float(n) / full)])
    return (fmt.table(rows, align='lrrr')
            + '\n\nGPT-2 small 모양에 문맥 1024. 질의 헤드는 12개'
            + ' 그대로다.')


def sec_lora():
    r = Rng(20)

    def rand(shape, s=1.0):
        return T.Tensor([r.normal() * s for _ in range(T.numel(shape))],
                        shape, requires_grad=True)
    x, W, b = rand((3, 6)), rand((6, 5)), rand((5,))
    A = rand((6, 2), 0.1)
    B = T.zeros((2, 5), requires_grad=True)
    y = X.lora_linear(x, W, b, A, B, 4, 2)
    T.sum(y).backward()
    base = T.add(T.matmul(x, W), b).data
    rows = [['', '값']]
    diff = max(abs(a - c) for a, c in zip(y.data, base))
    rows.append(['B = 0 일 때 출력 − 원래 출력의 최대', '%.1e' % diff])
    rows.append(['A 기울기의 최대 |·|', '%.1e' % max(map(abs, A.grad))])
    rows.append(['B 기울기의 최대 |·|', '%.3f' % max(map(abs, B.grad))])
    rows2 = [['d_in = d_out', 'r', 'LoRA 파라미터', '원래 W', '비율']]
    for d in (768, 4096):
        for rr in (4, 16):
            n = X.lora_params(d, d, rr)
            rows2.append([str(d), str(rr), '{:,}'.format(n),
                          '{:,}'.format(d * d), '%.4f' % (n / d / d)])
    return (fmt.table(rows, align='lr')
            + '\n\nB 가 0 이면 ∂ℓ/∂A = xᵀ·g·Bᵀ = 0. B 가 먼저 움직여야'
            + ' A 가 배운다.'
            + '\n\n' + fmt.table(rows2, align='rrrrr'))


def main():
    return report.write('extras.txt', [
        ('온라인 소프트맥스 — 조각씩 읽어도 같다', sec_online()),
        ('GQA·MQA 의 KV 캐시', sec_gqa()),
        ('LoRA', sec_lora()),
    ])


if __name__ == '__main__':
    print(main())
