# -*- coding: utf-8 -*-
"""6부 — GSM 시간축과 GMSK 의 숫자."""
from fractions import Fraction

from wirelesslib import fmt, tdma
from demo import report


def _fr(v, d=6):
    """분수를 '정확한 값 (어림값)' 으로."""
    if isinstance(v, Fraction):
        return '%s (%.*f)' % (v, d, float(v))
    return fmt.num(v, d)


def sec_timing():
    rows = [['이름', '정확한 값', '어림값']]
    items = [('변조율 [kbit/s]', tdma.RATE_KBPS, 'kbit/s'),
             ('비트 길이 [μs]', tdma.BIT_US, 'μs'),
             ('슬롯 [비트]', tdma.SLOT_BITS, '비트'),
             ('슬롯 [ms]', tdma.SLOT_MS, 'ms'),
             ('TDMA 프레임 [ms]', tdma.FRAME_MS, 'ms'),
             ('26 멀티프레임 [ms]', tdma.multiframe_ms(26), 'ms'),
             ('51 멀티프레임 [ms]', tdma.multiframe_ms(51), 'ms'),
             ('슈퍼프레임 [ms]', tdma.superframe_ms(), 'ms'),
             ('하이퍼프레임 [s]', tdma.hyperframe_seconds(), 's')]
    for name, v, unit in items:
        rows.append([name, '%s %s' % (v, unit), '%.6f' % float(v)])
    h, m, s = tdma.hyperframe_hms()
    rows.append(['하이퍼프레임',
                 '%d시간 %d분 %.2f초' % (h, m, s),
                 '%d 프레임' % tdma.HYPERFRAME_FRAMES])
    return (fmt.table(rows, align='lll')
            + '\n\n26 × 60/13 ms = 120 ms 가 정확히 떨어진다.'
            + '\n4.615 로 어림해 적고 26을 곱하면 120 이 안 나온다.')


def sec_bursts():
    """표로 짜면 108칸을 넘는다 — 버스트마다 여러 줄로 적는다."""
    out = []
    for kind in tdma.BURSTS:
        f = tdma.burst_fields(kind)
        total = sum(v for _n, v in f)
        cells = ['%s %s' % (n, v) for n, v in f]
        line = '  '
        lines = []
        for c in cells:
            if len(line) + len(c) > 64:
                lines.append(line.rstrip(' ·'))
                line = '  '
            line += c + ' · '
        lines.append(line.rstrip(' ·'))
        out.append('%-10s 합 %s 비트' % (kind, total))
        out += lines
        out.append('')
    out.append('다섯 종류 모두 156.25 비트다. 가드 구간의 길이가')
    out.append('그 버스트가 무엇을 모르는 채로 보내는지를 말해 준다.')
    return '\n'.join(out)


def sec_ta():
    rows = [['TA', '거리 [m]', '왕복 지연 [μs]']]
    for ta in (0, 1, 2, 10, 30, 63):
        d = tdma.ta_distance_m(ta)
        rows.append([str(ta), '%.1f' % d,
                     '%.2f' % (ta * float(tdma.BIT_US))])
    return (fmt.table(rows, align='rrr')
            + '\n\nTA 는 6비트(0~63)다. 그래서 GSM 셀 반지름의 한계가'
            + '\n35 km 인데, 그것을 정한 것은 전력이 아니라 '
            + '시간축이다.')


def sec_gmsk():
    rows = [['BT', '펄스 실효 폭(비트 단위)', '대역 밖 전력']]
    for bt in (None, 0.9, 0.5, 0.3, 0.2):
        name = 'MSK (필터 없음)' if bt is None else '%.1f' % bt
        width = ('—' if bt is None
                 else fmt.num(tdma.pulse_width(
                     tdma.gaussian_pulse(bt, 8, 6)) / 8.0, 3))
        rows.append([name, width,
                     '%.2f dB' % tdma.out_of_band_db(bt, seed=3)])
    return (fmt.table(rows, align='lrr')
            + '\n\nBT 를 낮추면 이웃 채널로 새는 전력이 준다.'
            + '\n대신 펄스가 길어져 ISI 가 는다. GSM 은 0.3 을 골랐다.')


def sec_phase():
    bits = [1, 0, 0, 1, 1, 1, 0]
    ph = tdma.msk_phase(bits, 8)
    rows = [['비트', '위상 변화 [rad]', 'π/2 의 몇 배']]
    import math
    for i, b in enumerate(bits):
        step = ph[(i + 1) * 8] - ph[i * 8]
        rows.append([str(b), fmt.num(step, 6),
                     '%+.0f' % (step / (math.pi / 2))])
    return fmt.table(rows, align='rrr')


def main():
    return report.write('tdma.txt', [
        ('GSM 시간축 — 어림수가 하나도 없다', sec_timing()),
        ('버스트 다섯 종류', sec_bursts()),
        ('타이밍 어드밴스와 거리', sec_ta()),
        ('BT 와 대역 밖 전력', sec_gmsk()),
        ('MSK 의 위상은 비트마다 ±π/2', sec_phase()),
    ])


if __name__ == '__main__':
    print(main())
