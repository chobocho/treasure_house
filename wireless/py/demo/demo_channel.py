# -*- coding: utf-8 -*-
"""2부 — 경로손실과 페이딩의 숫자."""
import math

from wirelesslib import channel, fmt
from demo import report


def sec_pathloss():
    rows = [['거리 [km]', '자유공간 2 GHz', '하타 도심 900 MHz',
             'COST-231 1800 MHz', 'TR 38.901 UMa LOS 2 GHz']]
    for d in (1.0, 2.0, 5.0, 10.0, 20.0):
        rows.append([
            fmt.num(d, 1),
            '%.1f dB' % channel.fspl_db(d * 1000.0, 2.0e9),
            '%.1f dB' % channel.hata_db(900.0, 30.0, 1.5, d),
            '%.1f dB' % channel.cost231_db(1800.0, 30.0, 1.5, d),
            '%.1f dB' % channel.tr38901_db('uma', d * 1000.0, 2.0,
                                           los=True)])
    return fmt.table(rows, align='rrrrr')


def sec_reference():
    rows = [['확인할 것', '값']]
    rows.append(['자유공간 1 km · 2 GHz',
                 '%.2f dB' % channel.fspl_db(1000.0, 2.0e9)])
    rows.append(['거리 두 배',
                 '%+.2f dB' % (channel.fspl_db(2000.0, 2.0e9)
                               - channel.fspl_db(1000.0, 2.0e9))])
    rows.append(['주파수 두 배',
                 '%+.2f dB' % (channel.fspl_db(1000.0, 4.0e9)
                               - channel.fspl_db(1000.0, 2.0e9))])
    rows.append(['하타 900 MHz·30 m·1.5 m·1 km',
                 '%.2f dB' % channel.hata_db(900.0, 30.0, 1.5, 1.0)])
    rows.append(['교외 보정',
                 '%+.2f dB' % (channel.hata_db(900.0, 30.0, 1.5, 1.0,
                                               'suburban')
                               - channel.hata_db(900.0, 30.0, 1.5,
                                                 1.0))])
    return fmt.table(rows, align='lr')


def sec_rayleigh():
    h = channel.rayleigh(40000, seed=20260916)
    rows = [['문턱 r', '실측 P(|h| ≤ r)', '이론 1 − e^{−r²}', '차이']]
    for r in (0.2, 0.5, 0.8, 1.0, 1.5, 2.0):
        emp = sum(1 for v in h if abs(v) <= r) / float(len(h))
        want = 1.0 - math.exp(-r * r)
        rows.append([fmt.num(r, 1), fmt.num(emp, 4), fmt.num(want, 4),
                     '%+.4f' % (emp - want)])
    return fmt.table(rows, align='rrrr')


def sec_doppler():
    rows = [['속도 [km/h]', '900 MHz', '2 GHz', '3.5 GHz', '28 GHz']]
    for v in (3.0, 30.0, 60.0, 120.0, 300.0):
        ms = v / 3.6
        rows.append([fmt.num(v, 0)] + [
            '%.0f Hz' % channel.doppler_hz(ms, f)
            for f in (900e6, 2e9, 3.5e9, 28e9)])
    return fmt.table(rows, align='rrrrr')


def sec_coherence():
    rows = [['도플러 [Hz]', '간섭성 시간', '지연 확산 [ns]',
             '간섭성 대역폭']]
    for fd, tau in ((5.0, 50.0), (50.0, 250.0), (200.0, 1000.0),
                    (500.0, 3000.0)):
        rows.append([fmt.num(fd, 0),
                     '%.2f ms' % (channel.coherence_time_s(fd) * 1e3),
                     fmt.num(tau, 0),
                     '%.0f kHz' % (channel.coherence_bw_hz(tau * 1e-9)
                                   / 1e3)])
    return fmt.table(rows, align='rrrr')


def sec_lcr():
    fd, fs, n = 100.0, 4000.0, 80000
    h = channel.jakes(n, fd, fs, seed=3, nsin=32)
    rms = math.sqrt(sum(abs(v) ** 2 for v in h) / n)
    rows = [['ρ (실효값 대비)', '실측 LCR [회/s]', '이론값',
             '상대 오차']]
    for rho in (0.3, 0.5, 1.0, 1.5):
        got = channel.level_crossing_rate(h, rho * rms, fs)
        want = (math.sqrt(2 * math.pi) * fd * rho
                * math.exp(-rho * rho))
        rows.append([fmt.num(rho, 1), fmt.num(got, 2),
                     fmt.num(want, 2),
                     '%+.1f %%' % (100.0 * (got - want) / want)])
    return fmt.table(rows, align='rrrr')


def main():
    return report.write('channel.txt', [
        ('경로손실 모형 비교', sec_pathloss()),
        ('되짚어 볼 기준값들', sec_reference()),
        ('레일리 포락선의 분포', sec_rayleigh()),
        ('도플러 편이 — 속도와 반송파', sec_doppler()),
        ('간섭성 시간과 간섭성 대역폭', sec_coherence()),
        ('레벨 교차율 — 페이딩의 빠르기', sec_lcr()),
    ])


if __name__ == '__main__':
    print(main())
