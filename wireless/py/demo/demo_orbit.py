# -*- coding: utf-8 -*-
"""12부 — 궤도와 지연·도플러의 숫자."""
from wirelesslib import fmt, orbit
from demo import report

SHELLS = [('저궤도(스타링크 급)', 550.0),
          ('저궤도(이리듐)', 780.0),
          ('저궤도 상단', 1200.0),
          ('중궤도(GPS)', 20200.0),
          ('정지궤도', None)]


def _alt(h):
    return orbit.geo_altitude_km() if h is None else h


def sec_kepler():
    rows = [['궤도', '고도 [km]', '주기', '속도 [km/s]',
             '지평선 중심각 [도]']]
    import math
    for name, h in SHELLS:
        a = _alt(h)
        r = orbit.EARTH_EQ_R_KM if h is None else orbit.EARTH_R_KM
        t = orbit.period_s(a, r)
        rows.append([name, '%.0f' % a,
                     '%.1f 분' % (t / 60.0),
                     fmt.num(orbit.speed_ms(a) / 1000.0, 3),
                     fmt.num(math.degrees(math.acos(
                         orbit.EARTH_R_KM
                         / (orbit.EARTH_R_KM + a))), 2)])
    return (fmt.table(rows, align='lrrrr')
            + '\n\n정지궤도의 주기는 24시간이 아니라'
            + '항성일(23시간 56분)이다.')


def sec_third_law():
    rows = [['고도 [km]', '장반경 a [km]', '주기 T [s]', 'T²/a³']]
    for h in (200.0, 550.0, 1200.0, 8000.0, 20200.0, 35786.0):
        a = orbit.EARTH_R_KM + h
        t = orbit.period_s(h)
        rows.append([fmt.num(h, 0), fmt.num(a, 1), fmt.num(t, 1),
                     '%.6e' % (t * t / a ** 3)])
    return (fmt.table(rows, align='rrrr')
            + '\n\nT²/a³ 이 높이와 무관하게 같다 — 케플러 제3법칙.')


def sec_delay():
    rows = [['궤도', '천정 편도', '앙각 25°', '앙각 10°',
             '왕복(앙각 10°)']]
    for name, h in SHELLS:
        a = _alt(h)
        rows.append([name,
                     '%.2f ms' % orbit.one_way_delay_ms(a, 90.0),
                     '%.2f ms' % orbit.one_way_delay_ms(a, 25.0),
                     '%.2f ms' % orbit.one_way_delay_ms(a, 10.0),
                     '%.2f ms' % (2 * orbit.one_way_delay_ms(a,
                                                             10.0))])
    return fmt.table(rows, align='lrrrr')


def sec_doppler():
    rows = [['궤도', '2 GHz', '12 GHz', '28 GHz',
             '15 kHz 부반송파의 몇 배(2 GHz)']]
    for name, h in SHELLS:
        a = _alt(h)
        rot = h is None
        d2 = orbit.max_doppler_hz(a, 2.0e9, rot)
        rows.append([name,
                     '%.1f kHz' % (d2 / 1e3),
                     '%.1f kHz' % (orbit.max_doppler_hz(a, 12.0e9,
                                                        rot) / 1e3),
                     '%.1f kHz' % (orbit.max_doppler_hz(a, 28.0e9,
                                                        rot) / 1e3),
                     fmt.num(d2 / 15000.0, 2)])
    return (fmt.table(rows, align='lrrrr')
            + '\n\n정지궤도는 지구와 함께 도니 상대 각속도가 0 —'
            + '도플러가 없다.'
            + '\n저궤도는 부반송파 간격의 몇 배를 오간다. 그래서'
            + '미리 보정한다.')


def sec_footprint():
    rows = [['궤도', '앙각 10° 발자국 반지름 [km]', '앙각 25°',
             '앙각 40°']]
    for name, h in SHELLS:
        a = _alt(h)
        rows.append([name] + ['%.0f' % orbit.footprint_radius_km(a, e)
                              for e in (10.0, 25.0, 40.0)])
    return fmt.table(rows, align='lrrr')


def sec_ntn():
    rows = [['궤도', 'TA 범위(앙각 10~90°) [ms]', '폭',
             '가시 시간(앙각 25°)']]
    for name, h in SHELLS:
        a = _alt(h)
        lo, hi = orbit.ta_window_ms(a, 10.0, 90.0)
        vis = orbit.visibility_s(a, 25.0)
        rows.append([name, '%.2f ~ %.2f' % (lo, hi),
                     '%.2f ms' % (hi - lo),
                     '%.1f 분' % (vis / 60.0)])
    return (fmt.table(rows, align='lrrr')
            + '\n\n지상 셀에서는 이 폭이 수십 μs 다. 위성에서는'
            + 'ms 단위라'
            + '\nRel-17 NTN 이 공통 TA 를 따로 두었다.')


def main():
    return report.write('orbit.txt', [
        ('궤도 높이가 정하는 것들', sec_kepler()),
        ('케플러 제3법칙', sec_third_law()),
        ('전파 지연', sec_delay()),
        ('도플러 편이', sec_doppler()),
        ('발자국 크기', sec_footprint()),
        ('NTN 이 감당해야 하는 것', sec_ntn()),
    ])


if __name__ == '__main__':
    print(main())
