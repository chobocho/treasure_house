# -*- coding: utf-8 -*-
"""4부 — 셀 설계의 숫자."""
from wirelesslib import cellular, fmt
from demo import report


def sec_reuse():
    rows = [['클러스터 N', '재사용 거리비 √(3N)', 'SIR γ=3',
             'SIR γ=4', '셀당 채널(전체 395)']]
    for n in (1, 3, 4, 7, 9, 12, 13, 19, 21):
        rows.append([str(n), fmt.num(cellular.reuse_ratio(n), 3),
                     '%.1f dB' % cellular.sir_db(n, 3.0),
                     '%.1f dB' % cellular.sir_db(n, 4.0),
                     str(cellular.channels_per_cell(395, n))])
    return (fmt.table(rows, align='rrrrr')
            + '\n\nAMPS 가 요구한 18 dB 를 γ=4 에서 막 넘기는'
            + '것이 N=7 이다.')


def sec_sector():
    rows = [['섹터 수', '첫 고리 간섭원', 'SIR (N=7, γ=4)', '이득']]
    base = cellular.sir_db(7, 4.0, 6)
    for sectors, i0 in ((1, 6), (3, 2), (6, 1)):
        v = cellular.sir_db(7, 4.0, i0)
        rows.append([str(sectors), str(i0), '%.1f dB' % v,
                     '%+.1f dB' % (v - base)])
    return fmt.table(rows, align='rrrr')


def sec_erlangb():
    loads = [1, 5, 10, 20, 30]
    rows = [['회선 수'] + ['A=%d' % a for a in loads]]
    for n in (1, 5, 10, 15, 20, 30, 40):
        rows.append([str(n)] + [
            fmt.num(cellular.erlang_b(float(a), n), 4)
            for a in loads])
    return (fmt.table(rows, align='r' + 'r' * len(loads))
            + '\n\n표준 표의 확인점: A=10, N=15 → 0.0365')


def sec_trunking():
    rows = [['회선 수', '차단률 2 % 에서 감당하는 부하 [얼랑]',
             '회선당 효율']]
    for n in (1, 5, 10, 20, 50, 100, 200):
        a = cellular.offered_load(n, 0.02)
        rows.append([str(n), fmt.num(a, 3),
                     '%.1f %%' % (100.0 * a / n)])
    return (fmt.table(rows, align='rrr')
            + '\n\n회선을 한 통에 모을수록 회선당 실어 나르는'
            + '양이 는다.'
            + '\n이것이 트렁킹 이득이고, 셀을 크게 쓰고 싶은 이유다.')


def sec_erlangc():
    rows = [['부하 A', '회선 N', '얼랑 B (버림)', '얼랑 C (기다림)']]
    for a, n in ((5.0, 8), (10.0, 15), (20.0, 25), (30.0, 40)):
        rows.append([fmt.num(a, 0), str(n),
                     fmt.num(cellular.erlang_b(a, n), 4),
                     fmt.num(cellular.erlang_c(a, n), 4)])
    return fmt.table(rows, align='rrrr')


def sec_handoff():
    rows = [['히스테리시스 [dB]', '2000 걸음 동안의 핸드오프 수']]
    for h in (0.0, 1.0, 3.0, 6.0, 10.0):
        rows.append([fmt.num(h, 1),
                     str(cellular.ping_pong_count(h, seed=3))])
    return (fmt.table(rows, align='rr')
            + '\n\n문턱을 두면 핑퐁이 준다. 대신 넘기는 시점이'
            + '늦어진다.')


def sec_breathing():
    rows = [['부하 η', '상대 반지름 γ=3', 'γ=4', '상대 면적 γ=4']]
    for load in (0.0, 0.2, 0.4, 0.6, 0.8, 0.9):
        r3 = cellular.breathing_radius(load, 3.0)
        r4 = cellular.breathing_radius(load, 4.0)
        rows.append([fmt.num(load, 1), fmt.num(r3, 3),
                     fmt.num(r4, 3), fmt.num(r4 * r4, 3)])
    return (fmt.table(rows, align='rrrr')
            + '\n\nCDMA 셀은 사람이 늘면 작아진다 — 셀 호흡.')


def main():
    return report.write('cellular.txt', [
        ('클러스터 크기와 SIR', sec_reuse()),
        ('섹터화가 간섭원을 줄인다', sec_sector()),
        ('얼랑 B 표', sec_erlangb()),
        ('트렁킹 이득', sec_trunking()),
        ('얼랑 B 와 얼랑 C', sec_erlangc()),
        ('핸드오프 히스테리시스', sec_handoff()),
        ('CDMA 셀 호흡', sec_breathing()),
    ])


if __name__ == '__main__':
    print(main())
