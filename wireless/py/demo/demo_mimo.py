# -*- coding: utf-8 -*-
"""10·11부 — 다중 안테나의 숫자."""
import math

from wirelesslib import fmt, info, mimo
from demo import report


def sec_diversity():
    rows = [['Eb/N0 [dB]', '1×1 레일리 BER', '알라무티 2×1 BER']]
    pts = []
    for ebn0 in (8.0, 11.0, 14.0, 17.0, 20.0):
        a = mimo.siso_rayleigh_ber(ebn0, 20000, seed=5)
        b = mimo.alamouti_ber(ebn0, 4000, seed=3)
        pts.append((ebn0, a, b))
        rows.append(['%.0f' % ebn0, '%.4e' % a, '%.4e' % b])
    s1 = math.log10(pts[0][1] / pts[-1][1]) / ((20.0 - 8.0) / 10.0)
    s2 = math.log10(pts[0][2] / pts[-1][2]) / ((20.0 - 8.0) / 10.0)
    note = ('\n\n기울기(10배 SNR 당 자릿수):'
            ' SISO %.2f · 알라무티 %.2f' % (s1, s2))
    return (fmt.table(rows, align='rrr') + note
            + '\n다이버시티 차수가 곧 그 기울기다.')


def sec_detect():
    rows = [['SNR [dB]', 'ZF 평균 제곱 오차', 'MMSE 평균 제곱 오차']]
    for snr in (0.0, 5.0, 10.0, 20.0):
        rows.append(['%.0f' % snr,
                     fmt.num(mimo.detect_mse(snr, 400, seed=11,
                                             kind='zf'), 4),
                     fmt.num(mimo.detect_mse(snr, 400, seed=11,
                                             kind='mmse'), 4)])
    return (fmt.table(rows, align='rrr')
            + '\n\nZF 는 간섭을 완전히 지우는 대신 잡음을 키운다.')


def sec_svd():
    import random
    rnd = random.Random(20260916)
    rows = [['시도', '특잇값', 'Σσ²', '‖H‖²_F', 'log₂det 용량',
             '특잇값 용량']]
    for t in range(4):
        h = [[complex(rnd.gauss(0, 0.7), rnd.gauss(0, 0.7))
              for _ in range(2)] for _ in range(2)]
        sv = mimo.singular_values(h)
        fro = sum(abs(v) ** 2 for row in h for v in row)
        rows.append([str(t + 1),
                     ' '.join(fmt.num(s, 3) for s in sv),
                     fmt.num(sum(s * s for s in sv), 5),
                     fmt.num(fro, 5),
                     fmt.num(info.mimo_capacity(h, 12.0), 5),
                     fmt.num(mimo.capacity_from_sv(sv, 2, 12.0), 5)])
    return (fmt.table(rows, align='rlrrrr')
            + '\n\n두 모듈이 서로를 검산한다 — 같은 값이 나와야 한다.')


def sec_array():
    rows = [['소자 수 N', '배열 이득', '널 대 널 빔폭 [도]', '널 개수']]
    for n in (2, 4, 8, 16, 64, 256):
        rows.append([str(n), '%.2f dB' % mimo.array_gain_db(n),
                     fmt.num(math.degrees(mimo.beamwidth_rad(n, 0.5)),
                             2),
                     str(mimo.count_nulls(n, 0.5))])
    return fmt.table(rows, align='rrrr')


def sec_pattern():
    n = 8
    rows = [['각도 [도]', '|AF| (N=8, d=λ/2, 조향 0°)']]
    for deg in range(-90, 91, 10):
        v = abs(mimo.array_factor(n, 0.5, math.radians(deg), 0.0))
        rows.append([str(deg), fmt.num(v, 3)])
    return fmt.table(rows, align='rr')


def sec_hardening():
    rows = [['안테나 수 N', '‖h‖²/N 평균', '분산', '분산 × N']]
    for n in (1, 2, 4, 16, 64, 256):
        m = mimo.hardening_mean(n, 4000, seed=19)
        v = mimo.hardening_variance(n, 4000, seed=19)
        rows.append([str(n), fmt.num(m, 4), fmt.num(v, 5),
                     fmt.num(v * n, 4)])
    return (fmt.table(rows, align='rrrr')
            + '\n\n분산이 1/N 로 준다 — 채널이 굳는다(channel '
            + 'hardening).')


def main():
    return report.write('mimo.txt', [
        ('다이버시티 — BER 곡선의 기울기', sec_diversity()),
        ('ZF 와 MMSE', sec_detect()),
        ('특잇값과 용량', sec_svd()),
        ('균일 선형 배열', sec_array()),
        ('배열 인자의 모양', sec_pattern()),
        ('채널 경화', sec_hardening()),
    ])


if __name__ == '__main__':
    print(main())
