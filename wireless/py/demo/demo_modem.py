# -*- coding: utf-8 -*-
"""2부 — 변조와 오류율의 숫자."""
import math

from wirelesslib import fmt, info, modem
from demo import report

NAMES = ['bpsk', 'qpsk', '8psk', '16qam', '64qam', '256qam']


def sec_constellations():
    rows = [['이름', '비트/심볼', '점 수', '최소 거리', '평균 에너지']]
    for name in NAMES + ['1024qam']:
        c = modem.constellation(name)
        dmin = min(abs(c.points[i] - c.points[j])
                   for i in range(c.m) for j in range(i + 1, c.m))
        e = sum(abs(p) ** 2 for p in c.points) / c.m
        rows.append([name, str(c.k), str(c.m), fmt.num(dmin, 4),
                     fmt.num(e, 4)])
    return fmt.table(rows, align='lrrrr')


def sec_ber():
    rows = [['변조', 'Eb/N0 [dB]', '몬테카를로 BER', '닫힌 식',
             '상대 오차']]
    cases = [('bpsk', 2.0, 120000), ('bpsk', 4.0, 360000),
             ('qpsk', 4.0, 360000), ('8psk', 9.0, 300000),
             ('16qam', 8.0, 200000), ('64qam', 12.0, 300000)]
    for name, ebn0, nbits in cases:
        got = modem.ber_sim(name, ebn0, nbits, seed=20260916)
        want = modem.ber_theory(name, ebn0)
        rows.append([name, '%.1f' % ebn0, '%.4e' % got, '%.4e' % want,
                     '%+.1f %%' % (100.0 * (got - want) / want)])
    return fmt.table(rows, align='lrrrr')


def sec_required():
    rows = [['변조', 'BER 1e-3 에 필요한 Eb/N0',
             'BER 1e-6 에 필요한 Eb/N0', '스펙트럼 효율']]
    for name in NAMES:
        c = modem.constellation(name)
        a = _invert(name, 1e-3)
        b = _invert(name, 1e-6)
        rows.append([name, '%.2f dB' % a, '%.2f dB' % b,
                     '%d bit/s/Hz' % c.k])
    return fmt.table(rows, align='lrrr')


def _invert(name, ber, lo=-5.0, hi=60.0):
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if modem.ber_theory(name, mid) > ber:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def sec_mi():
    rows = [['SNR [dB]', '섀넌 용량'] + NAMES[:5]]
    for snr in (0.0, 5.0, 10.0, 15.0, 20.0, 25.0):
        row = ['%.0f' % snr, fmt.num(info.capacity_awgn(snr), 3)]
        for name in NAMES[:5]:
            row.append(fmt.num(
                info.constellation_mi(name, snr, 1500, seed=7), 3))
        rows.append(row)
    return fmt.table(rows, align='r' * (len(NAMES[:5]) + 2))


def sec_limit():
    rows = [['스펙트럼 효율 [bit/s/Hz]', '필요한 최소 Eb/N0 [dB]']]
    for eff in (0.001, 0.1, 0.5, 1.0, 2.0, 4.0, 8.0):
        rows.append([fmt.num(eff, 3), '%.3f' % info.ebn0_min_db(eff)])
    rows.append(['→ 0 (극한)', '%.4f' % modem.shannon_limit_db()])
    return fmt.table(rows, align='rr')


def main():
    return report.write('modem.txt', [
        ('성상도의 제원', sec_constellations()),
        ('몬테카를로 BER 과 닫힌 식', sec_ber()),
        ('목표 BER 에 필요한 Eb/N0', sec_required()),
        ('성상도가 실어 나를 수 있는 양(상호정보)', sec_mi()),
        ('섀넌 한계 — 효율을 0 으로 보내면 −1.59 dB', sec_limit()),
    ])


if __name__ == '__main__':
    print(main())
