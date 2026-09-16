# -*- coding: utf-8 -*-
"""7·11부 — 사인 인코딩과 RoPE 의 성질."""
import math

from demo import report
from transformerlib import fmt, posenc
from transformerlib.rng import Rng


def sec_table():
    pe = posenc.sinusoidal(8, 8).tolist()
    rows = [['p', 'i=0 sin', 'i=0 cos', 'i=1 sin', 'i=1 cos',
             'i=3 sin']]
    for p in range(8):
        r = pe[p]
        rows.append([str(p)] + ['%+.4f' % v for v in
                               (r[0], r[1], r[2], r[3], r[6])])
    return (fmt.table(rows, align='rrrrrr')
            + '\n\nd = 8. i 가 커질수록 주파수 10000^(−2i/d) 가'
            + ' 느려진다.')


def sec_shift():
    d, pe = 8, posenc.sinusoidal(40, 8).tolist()
    rows = [['이동 k', '위치 p', 'max|M_k·PE(p) − PE(p+k)|']]
    for k in (1, 5, 13):
        M = posenc.shift_matrix(k, d)
        for p in (0, 20):
            got = [math.fsum(M[r][c] * pe[p][c] for c in range(d))
                   for r in range(d)]
            err = max(abs(a - b) for a, b in zip(got, pe[p + k]))
            rows.append([str(k), str(p), '%.1e' % err])
    return (fmt.table(rows, align='rrr')
            + '\n\nM_k 는 p 와 무관한 회전이다 — 상대 위치를 선형으로'
            + ' 읽는다.')


def sec_rope():
    r = Rng(3)
    q = [r.normal() for _ in range(8)]
    k = [r.normal() for _ in range(8)]
    rows = [['m', 'n', 'm − n', '⟨R_m q, R_n k⟩']]
    for m, n in ((0, 0), (5, 5), (40, 40), (3, 0), (8, 5), (43, 40),
                 (0, 3), (37, 40)):
        rows.append([str(m), str(n), '%+d' % (m - n),
                     '%.12f' % posenc.rope_dot(q, m, k, n)])
    return (fmt.table(rows, align='rrrr')
            + '\n\nm − n 이 같으면 값이 같다. 절대 위치는 사라지고'
            + ' 차이만 남는다.')


def main():
    return report.write('posenc.txt', [
        ('사인 인코딩 표', sec_table()),
        ('선형 이동 성질', sec_shift()),
        ('RoPE — 점수는 거리에만 달린다', sec_rope()),
    ])


if __name__ == '__main__':
    print(main())
