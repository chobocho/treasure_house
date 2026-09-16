# -*- coding: utf-8 -*-
"""3부 — 폴라 부호의 숫자."""
from wirelesslib import fmt, polar
from demo import report


def sec_polarize():
    rows = [['N', 'I(W)', '용량 합', 'N·I(W)', 'I<0.1 인 채널',
             'I>0.9 인 채널']]
    for n in (2, 4, 16, 64, 256, 1024):
        for i0 in (0.5,):
            caps = polar.capacities(n, i0)
            rows.append([
                str(n), fmt.num(i0, 1), fmt.num(sum(caps), 6),
                fmt.num(n * i0, 6),
                '%d (%.0f %%)' % (sum(1 for c in caps if c < 0.1),
                                  100.0 * sum(1 for c in caps
                                              if c < 0.1) / n),
                '%d (%.0f %%)' % (sum(1 for c in caps if c > 0.9),
                                  100.0 * sum(1 for c in caps
                                              if c > 0.9) / n)])
    return fmt.table(rows, align='rrrrll')


def sec_splits():
    rows = [['단계', '쪼갠 채널의 용량 (I=0.5 에서)']]
    for n in (2, 4, 8):
        rows.append([str(n), ' '.join(
            fmt.num(c, 4) for c in polar.capacities(n, 0.5))])
    return fmt.table(rows, align='rl')


def sec_frozen():
    rows = [['N', 'K', '부호율', '정보 자리(앞 12개)']]
    for n, k in ((8, 4), (64, 32), (256, 128)):
        fz = polar.frozen_set(n, k, 0.5)
        good = [i for i in range(n) if i not in fz][:12]
        rows.append([str(n), str(k), fmt.num(k / float(n), 3),
                     ' '.join(map(str, good))])
    return fmt.table(rows, align='rrrl')


def sec_decode():
    rows = [['N', 'K', 'Eb/N0 [dB]', 'SC BLER', 'SCL(8) BLER',
             'CA-SCL(8) BLER']]
    for n, k, ebn0 in ((64, 32, 2.0), (64, 32, 3.0),
                       (128, 64, 1.5), (128, 64, 2.5)):
        rows.append([
            str(n), str(k), '%.1f' % ebn0,
            fmt.num(polar.bler(n, k, ebn0, 40, 1, seed=7), 3),
            fmt.num(polar.bler(n, k, ebn0, 40, 8, seed=7), 3),
            fmt.num(polar.bler(n, k, ebn0, 40, 8, seed=7,
                               crc_name='crc8'), 3)])
    return fmt.table(rows, align='rrrrrr')


def main():
    return report.write('polar.txt', [
        ('극화는 용량을 보존한다', sec_polarize()),
        ('쪼갠 채널의 용량', sec_splits()),
        ('얼리지 않는 자리', sec_frozen()),
        ('SC · SCL · CRC 보조 SCL', sec_decode()),
    ])


if __name__ == '__main__':
    print(main())
