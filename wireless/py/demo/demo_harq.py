# -*- coding: utf-8 -*-
"""3부 — HARQ 의 숫자."""
from wirelesslib import fmt, harq, info
from demo import report

K, ELEN = 40, 72


def sec_buffer():
    d = harq.streams(K, 3, 10, seed=1)
    buf = harq.circular_buffer(d)
    live = sum(1 for v in buf if v is not None)
    rows = [['확인할 것', '값']]
    rows.append(['줄기 길이 (K+6)', str(len(d[0]))])
    rows.append(['부블록 인터리버 뒤 Kπ',
                 str(len(harq.subblock_perm(len(d[0]))))])
    rows.append(['순환 버퍼 길이 (3·Kπ)', str(len(buf))])
    rows.append(['실제로 쓰는 자리', str(live)])
    rows.append(['32열 치환이 5비트 역순인가',
                 '예' if harq.COL_PERM == [
                     int('{:05b}'.format(j)[::-1], 2)
                     for j in range(32)] else '아니오'])
    return fmt.table(rows, align='ll')


def sec_rv():
    d = harq.streams(K, 3, 10, seed=1)
    buf = harq.circular_buffer(d)
    head = '내보낸 %d비트의 출처 (계통/패리티1/패리티2)' % ELEN
    rows = [['RV', head]]
    for rv in range(4):
        pos = harq.rate_match_positions(d, ELEN, rv)
        froms = [buf[p][0] for p in pos]
        rows.append([str(rv), '%d / %d / %d'
                     % (froms.count(0), froms.count(1),
                        froms.count(2))])
    return (fmt.table(rows, align='rl')
            + '\n\nRV0 은 계통 비트가 많아 혼자서도 복호된다.'
            + '\nRV1·RV2 는 패리티가 많아 증분 잉여로 쓰인다.'
            + '\nRV3 은 버퍼 끝에서 앞으로 되감겨 다시 계통이 많다.')


def sec_combine():
    rows = [['Eb/N0 [dB]', '방식', '전송 1회', '2회', '3회']]
    for ebn0 in (-2.0, -1.0, 0.0):
        for mode in ('chase', 'ir'):
            row = ['%.1f' % ebn0,
                   '체이스 결합' if mode == 'chase' else '증분 잉여']
            for t in (1, 2, 3):
                row.append(fmt.num(
                    harq.bler(ebn0, t, 40, K, ELEN, seed=5,
                              mode=mode), 3))
            rows.append(row)
    return (fmt.table(rows, align='rlrrr')
            + '\n\n같은 횟수라면 증분 잉여가 체이스 결합보다 '
            + '낫거나 같다.'
            + '\n체이스는 같은 자리를 다시 받아 연판정 값을 더할 '
            + '뿐이고,'
            + '\n증분 잉여는 처음에 안 보냈던 패리티를 더 보내 '
            + '부호율을 낮춘다.')


def sec_throughput():
    rows = [['Eb/N0 [dB]', '처리율 [bit/채널사용]', '부호율 K/E',
             '그 SNR 의 섀넌 용량']]
    import math
    rate = float(K) / ELEN
    for ebn0 in (0.0, 1.0, 2.0, 4.0, 6.0):
        th = harq.throughput(ebn0, 3, 30, K, ELEN, seed=9)
        esn0 = ebn0 + 10.0 * math.log10(rate)
        rows.append(['%.1f' % ebn0, fmt.num(th, 4), fmt.num(rate, 4),
                     fmt.num(info.capacity_awgn(esn0), 4)])
    return fmt.table(rows, align='rrrr')


def sec_processes():
    rtt = 8
    rows = [['프로세스 수 N', '닫힌 식 min(1, N/8)', '슬롯 800개 모사']]
    for n in (1, 2, 4, 6, 8, 16):
        u = 100 * harq.utilization(n, rtt)
        sim = 100 * harq.simulate_utilization(n, rtt, 800)
        rows.append([str(n), '%.1f %%' % u, '%.1f %%' % sim])
    return (fmt.table(rows, align='rrr')
            + '\n\n정지 대기(N=1)는 왕복 8 ms 중 1 ms 만 쓴다. '
            + 'N 이 왕복 길이에 이르면 링크가 찬다 —'
            + '\nLTE FDD 가 8 프로세스를 두는 셈법이 이것이다.')


def main():
    return report.write('harq.txt', [
        ('순환 버퍼의 구조', sec_buffer()),
        ('RV 마다 어디를 읽는가', sec_rv()),
        ('체이스 결합과 증분 잉여', sec_combine()),
        ('처리율은 용량을 넘지 않는다', sec_throughput()),
        ('정지 대기와 N-프로세스', sec_processes()),
    ])


if __name__ == '__main__':
    print(main())
