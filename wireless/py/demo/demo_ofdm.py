# -*- coding: utf-8 -*-
"""10·11부 — OFDM 과 NR 뉴머롤로지의 숫자."""
import math

from wirelesslib import fmt, ofdm
from demo import report


def sec_cp():
    rows = [['FFT 크기', 'CP 길이', '가장 긴 지연',
             '한 탭 등화 뒤 오차', 'CP 부담']]
    for nfft, ncp, taps in ((256, 16, [(0, 1.0), (5, 0.6),
                                       (12, 0.3)]),
                            (256, 16, [(0, 1.0), (15, 0.5)]),
                            (256, 4, [(0, 1.0), (9, 0.6)]),
                            (1024, 72, [(0, 1.0), (30, 0.7),
                                        (60, 0.3)])):
        err = ofdm.multipath_error(nfft, ncp, taps)
        rows.append([str(nfft), str(ncp),
                     str(max(d for d, _a in taps)),
                     '%.2e' % err,
                     '%.1f %%' % (100 * ofdm.cp_overhead(nfft, ncp))])
    return (fmt.table(rows, align='rrrrr')
            + '\n\nCP 가 지연보다 길면 오차가 0 이다 — 채널이 한'
            + '탭 곱셈이 된다.')


def sec_ici():
    rows = [['주파수 오차 ε (부반송파 대비)', '실측 ICI 전력',
             '(πε)²/3', '상대 오차']]
    for eps in (0.0, 0.01, 0.02, 0.05, 0.1, 0.2):
        got = ofdm.ici_power(256, eps)
        want = (math.pi * eps) ** 2 / 3.0
        rows.append([fmt.num(eps, 2), '%.3e' % got, '%.3e' % want,
                     '—' if eps == 0 else
                     '%+.1f %%' % (100.0 * (got - want) / want)])
    return fmt.table(rows, align='rrrr')


def sec_papr():
    rows = [['부반송파 수', 'OFDM 평균 PAPR', 'SC-FDMA 평균 PAPR',
             '차이']]
    for nfft in (64, 256, 1024):
        a = ofdm.mean_papr_db(nfft, 80, seed=5, scfdma=False)
        b = ofdm.mean_papr_db(nfft, 80, seed=5, scfdma=True)
        rows.append([str(nfft), '%.2f dB' % a, '%.2f dB' % b,
                     '%+.2f dB' % (b - a)])
    return (fmt.table(rows, align='rrrr')
            + '\n\nLTE 상향이 DFT 를 한 번 더 도는 이유가 이 차이다.')


def sec_ccdf():
    levels = [4.0, 6.0, 8.0, 10.0, 12.0]
    rows = [['PAPR 문턱 [dB]'] + ['%.0f' % v for v in levels]]
    for name, sc in (('OFDM', False), ('SC-FDMA', True)):
        rows.append([name] + [
            fmt.num(v, 3) for v in ofdm.papr_ccdf(
                256, levels, 200, seed=7, scfdma=sc)])
    return fmt.table(rows, align='l' + 'r' * len(levels))


def sec_numerology():
    rows = [['μ', 'SCS [kHz]', '유용 심볼 [μs]', '슬롯 [ms]',
             '서브프레임당 슬롯', 'PRB 폭 [kHz]', '확장 CP']]
    for mu in range(7):
        rows.append([str(mu), str(ofdm.scs_khz(mu)),
                     fmt.num(ofdm.useful_symbol_us(mu), 2),
                     fmt.num(ofdm.slot_ms(mu), 5),
                     str(ofdm.slots_per_subframe(mu)),
                     fmt.num(ofdm.prb_khz(mu), 0),
                     '가능' if ofdm.extended_cp_allowed(mu) else '—'])
    return (fmt.table(rows, align='rrrrrrl')
            + '\n\n유용 심볼 길이 × 부반송파 간격 = 1 — 이것이'
            + '직교 조건이다.')


def sec_grid():
    rows = [['μ', '대역폭 [MHz]', '최대 PRB 수(어림)',
             '부반송파 수', '슬롯당 자원 요소']]
    for mu, bw in ((0, 20.0), (1, 100.0), (3, 400.0)):
        prb = int(bw * 1000.0 * 0.9 / ofdm.prb_khz(mu))
        rows.append([str(mu), fmt.num(bw, 0), str(prb),
                     str(prb * 12), str(prb * ofdm.re_per_prb())])
    return (fmt.table(rows, align='rrrrr')
            + '\n\n0.9 는 보호 대역을 뺀 어림이다 — 규격의 정확한 표는'
            + '\nTS 38.101-1 표 5.3.2-1 에 있다.')


def main():
    return report.write('ofdm.txt', [
        ('순환 전치가 지연보다 길면 ISI 가 사라진다', sec_cp()),
        ('주파수 오차가 만드는 부반송파 간섭', sec_ici()),
        ('PAPR — OFDM 과 SC-FDMA', sec_papr()),
        ('PAPR 이 문턱을 넘을 확률', sec_ccdf()),
        ('NR 뉴머롤로지', sec_numerology()),
        ('자원 그리드의 크기', sec_grid()),
    ])


if __name__ == '__main__':
    print(main())
