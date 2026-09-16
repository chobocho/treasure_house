# -*- coding: utf-8 -*-
"""10부 — KV 캐시는 전체 재계산과 같은 로짓을 더 싸게 낸다."""
from demo import report
from transformerlib import fmt
from transformerlib import model as M
from transformerlib import sample as S


def sec_equal():
    rows = [['위치 방식', '위치 n', 'max|캐시 로짓 − 전체 로짓|']]
    for pos in ('learned', 'sin', 'rope'):
        cfg = M.Config(V=13, T=6, d=8, L=2, h=2, d_ff=16, pos=pos)
        p = M.init_params(cfg, 3)
        for t in p.values():
            t.data[:] = [v * 30 for v in t.data]
        ids = [3, 7, 1, 12, 0, 5]
        cache = S.KVCache(cfg)
        for n in range(1, 7):
            row = S.forward_cached(p, cfg, ids[n - 1], cache)
            full, _ = M.forward(p, cfg, [ids[:n]])
            want = full.data[(n - 1) * cfg.V:n * cfg.V]
            if n in (1, 3, 6):
                rows.append([pos, str(n), '%.1e' % max(
                    abs(a - b) for a, b in zip(row, want))])
    return fmt.table(rows, align='lrr')


def sec_cost():
    """토큰 하나를 더 만들 때 행렬곱 곱셈 수 — 캐시 없이 / 캐시로."""
    c = M.Config(V=50257, T=1024, d=768, L=12, h=12, d_ff=3072)
    d, f = c.d, c.d_ff
    rows = [['지금 길이 n', '다시 계산', 'KV 캐시', '비']]
    for n in (16, 128, 512, 1024):
        full = M.matmul_mults(c, n)
        one = c.L * ((4 * d * d + 2 * d * f) + 2 * n * d) + d * c.V
        rows.append([str(n), '{:,}'.format(full), '{:,}'.format(one),
                     '%.0f' % (float(full) / one)])
    return (fmt.table(rows, align='rrrr')
            + '\n\nGPT-2 small 모양. 캐시는 새 토큰의 사영과 그 질의'
            + ' 하나의'
            + '\n점수·가중합(2·n·d)만 계산한다. 키·값 2·L·n·d 개를 들고'
            + ' 있다.')


def main():
    return report.write('kvcache.txt', [
        ('캐시 로짓 = 전체 로짓', sec_equal()),
        ('토큰 하나의 곱셈 수', sec_cost()),
    ])


if __name__ == '__main__':
    print(main())
