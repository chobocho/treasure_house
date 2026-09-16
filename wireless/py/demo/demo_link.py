# -*- coding: utf-8 -*-
"""2부 — 링크 버짓의 숫자."""
from wirelesslib import channel, fmt, link, modem
from demo import report


def sec_noise():
    rows = [['대역폭', '290 K 열잡음', 'NF 3 dB', 'NF 7 dB',
             'NF 1.5 dB']]
    for bw, name in ((180e3, '1 PRB (180 kHz)'),
                     (1.4e6, 'LTE 1.4 MHz'),
                     (10e6, 'LTE 10 MHz'),
                     (20e6, 'LTE 20 MHz'),
                     (100e6, 'NR 100 MHz')):
        rows.append([name,
                     '%.2f dBm' % link.thermal_noise_dbm(bw),
                     '%.2f dBm' % link.noise_floor_dbm(bw, 3.0),
                     '%.2f dBm' % link.noise_floor_dbm(bw, 7.0),
                     '%.2f dBm' % link.noise_floor_dbm(bw, 1.5)])
    return (fmt.table(rows, align='lrrrr')
            + '\n\n1 Hz·290 K 에서 −173.98 dBm — 이 책에서 가장 '
            + '자주 쓰는 상수.')


def sec_nf():
    rows = [['잡음지수 [dB]', '등가 잡음온도 [K]', '되짚은 잡음지수']]
    for nf in (0.3, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0):
        t = link.noise_temp_k(nf)
        rows.append([fmt.num(nf, 1), fmt.num(t, 1),
                     fmt.num(link.noise_figure_db(t), 3)])
    return (fmt.table(rows, align='rrr')
            + '\n\n위성 쪽은 dB 대신 K 로 말한다. 0.5 dB 가 35 K 인데,'
            + '\n하늘의 잡음온도(수십 K)와 견주면 작지 않은 값이다.')


def sec_budget():
    b = link.budget(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=18.0,
                    path_loss_db=channel.fspl_db(1000.0, 2.0e9),
                    bw_hz=1.0e7, nf_db=3.0, required_snr_db=10.0)
    rows = [['항', '값']]
    order = [('eirp_dbm', 'EIRP', 'dBm'),
             ('path_loss_db', '경로손실(자유공간 1 km·2 GHz)', 'dB'),
             ('grx_dbi', '수신 안테나 이득', 'dBi'),
             ('prx_dbm', '수신 전력', 'dBm'),
             ('noise_dbm', '잡음 바닥(10 MHz, NF 3 dB)', 'dBm'),
             ('snr_db', 'SNR', 'dB'),
             ('required_snr_db', '요구 SNR', 'dB'),
             ('margin_db', '여유', 'dB')]
    for key, name, unit in order:
        rows.append([name, '%+.2f %s' % (b[key], unit)])
    return fmt.table(rows, align='lr')


def sec_presets():
    rows = [['링크', 'EIRP', '경로손실', '수신 전력', '잡음 바닥',
             'SNR', '여유']]
    for name in ('lte_uplink', 'nr_downlink', 'geo_downlink'):
        b = link.preset_budget(name)
        rows.append([name] + ['%+.1f' % b[k] for k in
                              ('eirp_dbm', 'path_loss_db', 'prx_dbm',
                               'noise_dbm', 'snr_db', 'margin_db')])
    return (fmt.table(rows, align='lrrrrrr')
            + '\n\n숫자는 설계 예시다. 규격이 못 박은 값이 아니다.')


def sec_range():
    rows = [['경로손실 지수 n', '여유 0 이 되는 거리 [m]']]
    for n in (2.0, 2.5, 3.0, 3.5, 4.0):
        d = link.max_range_m(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=18.0,
                             f_hz=2.0e9, bw_hz=1.0e7, nf_db=3.0,
                             required_snr_db=10.0, n=n)
        rows.append([fmt.num(n, 1), '%.0f' % d])
    return (fmt.table(rows, align='rr')
            + '\n\n지수가 2 에서 4 로 바뀌면 같은 여유로 갈 수 '
            + '있는 거리가'
            + '\n자릿수로 줄어든다. 셀 설계에서 n 을 잘못 잡는 것이'
            + '\n가장 비싼 실수인 이유다.')


def sec_required():
    rows = [['변조', 'BER 1e-3', 'BER 1e-5', 'BER 1e-6']]
    for name in ('bpsk', 'qpsk', '8psk', '16qam', '64qam', '256qam'):
        rows.append([name] + ['%.2f dB' % link.required_ebn0_db(
            name, b) for b in (1e-3, 1e-5, 1e-6)])
    return (fmt.table(rows, align='lrrr')
            + '\n\n링크 버짓의 "요구 SNR" 칸은 이렇게 정해진다.')


def sec_sensitivity():
    rows = [['대역폭', 'NF', '요구 SNR', '수신 감도']]
    cases = [(180e3, 3.0, 0.0), (10e6, 3.0, -1.0),
             (20e6, 7.0, 5.0), (100e6, 7.0, 5.0)]
    for bw, nf, snr in cases:
        rows.append(['%.3g Hz' % bw, '%.1f dB' % nf,
                     '%+.1f dB' % snr,
                     '%.2f dBm' % link.sensitivity_dbm(bw, nf, snr)])
    return fmt.table(rows, align='rrrr')


def main():
    return report.write('link.txt', [
        ('열잡음 바닥', sec_noise()),
        ('잡음지수와 잡음온도', sec_nf()),
        ('링크 버짓 한 판 — 항마다 이름표', sec_budget()),
        ('미리 담아 둔 링크들', sec_presets()),
        ('여유가 0 이 되는 거리', sec_range()),
        ('목표 BER 에 필요한 Eb/N0', sec_required()),
        ('수신 감도', sec_sensitivity()),
    ])


if __name__ == '__main__':
    print(main())
