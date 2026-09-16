# -*- coding: utf-8 -*-
"""2부 — 신호와 스펙트럼, 펄스 성형의 숫자."""
import random

from wirelesslib import dsp, fmt
from demo import report


def sec_fft():
    rnd = random.Random(20260916)
    rows = [['N', '최대 오차(FFT−DFT)', '곱셈 수 비(N²/N log₂N)']]
    for n in (8, 32, 128, 512):
        x = [complex(rnd.gauss(0, 1), rnd.gauss(0, 1))
             for _ in range(n)]
        err = max(abs(a - b) for a, b in zip(dsp.fft(x), dsp.dft(x)))
        import math
        rows.append([str(n), '%.2e' % err,
                     '%.1f' % (n / math.log2(n))])
    return fmt.table(rows, align='rrr')


def sec_rc():
    rows = [['β', '꼭대기', 'T 에서', '2T 에서', '3T 에서']]
    for beta in (0.0, 0.22, 0.35, 1.0):
        h = dsp.rc(beta, 8, 10)
        mid = len(h) // 2
        rows.append(['%.2f' % beta, fmt.num(h[mid], 4)]
                    + [fmt.num(h[mid + k * 8], 4) for k in (1, 2, 3)])
    return fmt.table(rows, align='rrrrr')


def sec_rrc():
    rows = [['자른 길이(심볼)', '남는 최대 ISI(상대)']]
    for span in (8, 12, 16, 24, 32):
        g = dsp.rrc(0.25, 8, span)
        y = dsp.conv(g, g)
        mid = len(y) // 2
        worst = max(abs(y[mid + k * 8] / y[mid]) for k in range(1, 5))
        rows.append([str(span), '%.2e' % worst])
    return fmt.table(rows, align='rr')


def main():
    return report.write('dsp.txt', [
        ('FFT 와 정의대로의 DFT 는 같은 답을 낸다', sec_fft()),
        ('상승 코사인은 심볼 순간마다 0 이다', sec_rc()),
        ('RRC 쌍의 ISI 는 자른 길이 탓이다', sec_rrc()),
    ])


if __name__ == '__main__':
    print(main())
