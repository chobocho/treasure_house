# -*- coding: utf-8 -*-
"""2부 — 용량. 이 책의 잣대."""
from wirelesslib import fmt, info
from demo import report


def sec_awgn():
    rows = [['SNR [dB]', 'AWGN 용량', '레일리 에르고딕',
             '중단 용량 10 %', '중단 용량 1 %']]
    for snr in (-5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 30.0):
        rows.append([
            '%.0f' % snr,
            fmt.num(info.capacity_awgn(snr), 3),
            fmt.num(info.capacity_rayleigh_ergodic(snr), 3),
            fmt.num(info.capacity_rayleigh_outage(snr, 0.1), 3),
            fmt.num(info.capacity_rayleigh_outage(snr, 0.01), 3)])
    return fmt.table(rows, align='rrrrr')


def sec_mc():
    rows = [['SNR [dB]', '닫힌 식', '표본 평균(4만 개)', '상대 오차']]
    for snr in (0.0, 5.0, 10.0, 20.0):
        a = info.capacity_rayleigh_ergodic(snr)
        b = info.capacity_rayleigh_mc(snr, 40000, seed=20260916)
        rows.append(['%.0f' % snr, fmt.num(a, 4), fmt.num(b, 4),
                     '%+.2f %%' % (100.0 * (b - a) / a)])
    return fmt.table(rows, align='rrrr')


def sec_waterfill():
    gains = [8.0, 4.0, 1.0, 0.25, 0.1]
    rows = [['전력 P', '채널별 배분', '물채우기 용량',
             '균등 배분 용량']]
    for total in (0.5, 1.0, 2.0, 5.0, 10.0):
        p = info.waterfill(gains, total)
        eq = [total / len(gains)] * len(gains)
        rows.append([fmt.num(total, 1),
                     ' '.join(fmt.num(v, 2) for v in p),
                     fmt.num(info.capacity_parallel(gains, p), 3),
                     fmt.num(info.capacity_parallel(gains, eq), 3)])
    return (fmt.table(rows, align='rlrr')
            + '\n\n좋은 채널에 더 주고 나쁜 채널은 아예 끈다.'
            + '\n전력이 넉넉해지면 차이가 줄어든다.')


def sec_mimo():
    rows = [['SNR [dB]', '1×1', '1×2', '2×1', '2×2', '4×4']]
    for snr in (0.0, 10.0, 20.0, 30.0):
        row = ['%.0f' % snr]
        for nt, nr in ((1, 1), (1, 2), (2, 1), (2, 2), (4, 4)):
            row.append(fmt.num(
                info.mimo_capacity_mc(nt, nr, snr, 300, seed=11), 2))
        rows.append(row)
    return (fmt.table(rows, align='rrrrrr')
            + '\n\n1×2 는 이득만 붙고 기울기는 그대로지만,'
            + '\n2×2 는 기울기 자체가 두 배가 된다 — 다중화 이득.')


def main():
    return report.write('info.txt', [
        ('AWGN·레일리 용량', sec_awgn()),
        ('닫힌 식과 몬테카를로', sec_mc()),
        ('물채우기는 균등 배분보다 낫다', sec_waterfill()),
        ('MIMO 용량 — 다중화 이득이 기울기를 바꾼다', sec_mimo()),
    ])


if __name__ == '__main__':
    print(main())
