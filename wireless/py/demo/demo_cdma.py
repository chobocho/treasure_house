# -*- coding: utf-8 -*-
"""7부 — IS-95 의 숫자."""
from wirelesslib import cdma, fmt, spread
from demo import report


def sec_forward():
    rows = [['동시 사용자 수', '잡음 없는 링크에서 틀린 심볼']]
    for n in (1, 4, 16, 32, 63):
        bad = cdma.forward_roundtrip(n, 20, seed=3)
        rows.append([str(n), str(bad)])
    return (fmt.table(rows, align='rr')
            + '\n\n기지국이 한꺼번에 내보내므로 왈시가 완벽히 직교한다.'
            + '\n역방향은 도착 시각이 달라 이렇게 안 된다.')


def sec_channels():
    rows = [['채널', '왈시 번호', '하는 일']]
    rows.append(['파일럿', '0', '위상 기준과 셀 탐색'])
    rows.append(['동기', '32', '시스템 시각과 롱코드 상태'])
    rows.append(['페이징', '1~7', '착신 호출과 시스템 정보'])
    rows.append(['트래픽', '8~63', '통화'])
    return fmt.table(rows, align='lll')


def sec_gain():
    rows = [['확산율', '실측 역확산 이득', '이론 10·log₁₀(SF)', '차이']]
    for sf in (16, 64, 128):
        got = cdma.despread_gain_db(sf, 200000, seed=11)
        want = spread.processing_gain_db(sf)
        rows.append([str(sf), '%.2f dB' % got, '%.2f dB' % want,
                     '%+.2f dB' % (got - want)])
    return fmt.table(rows, align='rrrr')


def sec_rake():
    rows = [['갈래(finger) 수', '경로 2개', '경로 3개']]
    for f in (1, 2, 3, 4):
        rows.append([str(f),
                     fmt.num(cdma.rake_ber(f, 60, 4.0, seed=7,
                                           paths=2), 4),
                     fmt.num(cdma.rake_ber(f, 60, 4.0, seed=9,
                                           paths=3), 4)])
    return (fmt.table(rows, align='rrr')
            + '\n\n갈래를 늘리면 좋아진다. 경로보다 많이 두면'
            + '더는 안 좋아진다.')


def sec_nearfar():
    rows = [['전력 제어', '먼 단말이 보는 신호 대 간섭비']]
    rows.append(['끔', '%.1f dB' % cdma.near_far_sinr_db(False)])
    rows.append(['켬', '%.1f dB' % cdma.near_far_sinr_db(True)])
    hist = cdma.power_control_loop(7.0, 300, 1.0, seed=17, fade_db=0.5)
    tail = hist[-100:]
    rows.append(['닫힌 고리 수렴값(느린 페이딩)',
                 '%.2f dB (목표 7.0)' % (sum(tail) / len(tail))])
    rows.append(['그때의 떨림 폭',
                 '%.2f dB' % (max(tail) - min(tail))])
    fast = cdma.power_control_loop(7.0, 300, 1.0, seed=19,
                                   fade_db=6.0)[-100:]
    rows.append(['빠른 페이딩에서의 떨림 폭',
                 '%.2f dB' % (max(fast) - min(fast))])
    return fmt.table(rows, align='ll')


def sec_capacity():
    rows = [['W/R', 'Eb/N0', '음성 활동률', '타 셀 간섭 f', '섹터 이득',
             '셀당 사용자']]
    cases = [(128.0, 7.0, 1.0, 0.0, 1.0),
             (128.0, 7.0, 0.4, 0.0, 1.0),
             (128.0, 7.0, 0.4, 0.6, 1.0),
             (128.0, 7.0, 0.4, 0.6, 2.55),
             (128.0, 5.0, 0.4, 0.6, 2.55)]
    for wr, e, v, f, g in cases:
        rows.append([fmt.num(wr, 0), '%.1f dB' % e, fmt.num(v, 1),
                     fmt.num(f, 1), fmt.num(g, 2),
                     '%.1f' % cdma.pole_capacity(wr, e, v, f, g)])
    return fmt.table(rows, align='rrrrrr')


def sec_softcap():
    rows = [['동시 사용자 수', '비동기 역방향 SINR']]
    for n in (1, 4, 8, 16, 32, 64):
        rows.append([str(n),
                     '%.2f dB' % cdma.multiuser_sinr_db(n, seed=5)])
    return (fmt.table(rows, align='rr')
            + '\n\n한 명 더 받으면 모두가 조금씩 나빠질 뿐,'
            + '거절당하지 않는다.'
            + '\n이것이 CDMA 의 부드러운 용량이다.')


def main():
    return report.write('cdma.txt', [
        ('순방향은 완벽히 직교한다', sec_forward()),
        ('IS-95 순방향의 왈시 배정', sec_channels()),
        ('역확산 이득 = 처리 이득', sec_gain()),
        ('RAKE — 다중경로를 모은다', sec_rake()),
        ('원근 문제와 전력 제어', sec_nearfar()),
        ('길하우젠 용량식', sec_capacity()),
        ('부드러운 용량', sec_softcap()),
    ])


if __name__ == '__main__':
    print(main())
