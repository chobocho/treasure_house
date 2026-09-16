# -*- coding: utf-8 -*-
"""7·9부 — 확산 부호의 숫자."""
import math

from wirelesslib import fmt, spread
from demo import report


def sec_walsh():
    h = spread.hadamard(8)
    rows = [['부호'] + ['c%d' % i for i in range(8)]]
    for k in range(8):
        rows.append(['W%d' % k] + ['%+d' % v for v in h[k]])
    worst = max(abs(sum(a * b for a, b in zip(h[i], h[j])))
                for i in range(8) for j in range(8) if i != j)
    return (fmt.table(rows, align='l' + 'r' * 8)
            + '\n\n서로 다른 두 행의 상관 최댓값: %d (직교)' % worst)


def sec_ovsf():
    rows = [['SF', '부호 번호', '부호', '조상(SF=4)']]
    for sf, k in ((4, 1), (8, 2), (8, 3), (8, 4), (16, 9)):
        c = spread.ovsf(sf, k)
        anc = [i for i in range(4) if spread.is_ancestor(4, i, sf, k)]
        rows.append([str(sf), str(k),
                     ''.join('+' if v > 0 else '-' for v in c),
                     ','.join(map(str, anc)) or '—'])
    return fmt.table(rows, align='rrll')


def sec_primitive():
    rows = [['쓰는 곳', '차수', '다항식(16진)', '원시인가',
             '주기']]
    items = [('IS-95 숏 PN I', 15, spread.IS95_PN_I),
             ('IS-95 숏 PN Q', 15, spread.IS95_PN_Q),
             ('IS-95 롱코드', 42, spread.IS95_LONG),
             ('WCDMA 스크램블링 x', 18, spread.WCDMA_X),
             ('WCDMA 스크램블링 y', 18, spread.WCDMA_Y)]
    for name, m, poly in items:
        prim = spread.is_primitive(poly, m)
        rows.append([name, str(m), '0x%X' % poly,
                     '예' if prim else '아니오',
                     '2^%d−1 = %d' % (m, (1 << m) - 1)])
    return (fmt.table(rows, align='lrlll')
            + '\n\n2⁴²−1 은 돌려서 못 센다. x 의 곱셈 차수를 '
            + '대수로 확인했다.')


def sec_autocorr():
    rows = [['다항식', 'm', '주기', '자기상관이 갖는 값']]
    for poly, m in ((0b100101, 5), (0b1000011, 6), (0b10000011, 7)):
        s = spread.bipolar(spread.m_sequence(poly, m))
        n = len(s)
        vals = sorted(set(sum(s[i] * s[(i + lag) % n]
                              for i in range(n))
                          for lag in range(n)))
        rows.append(['0o%o' % poly, str(m),
                     str(spread.lfsr_period(poly, m)),
                     ' '.join(map(str, vals))])
    return fmt.table(rows, align='lrrl')


def sec_gold():
    m = 5
    codes = [spread.gold(0b100101, 0b111101, m, k) for k in range(6)]
    vals = set()
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            a = spread.bipolar(codes[i])
            b = spread.bipolar(codes[j])
            n = len(a)
            for lag in range(n):
                vals.add(sum(a[t] * b[(t + lag) % n]
                             for t in range(n)))
    rows = [['확인할 것', '값']]
    rows.append(['m', str(m)])
    rows.append(['부호 길이', str((1 << m) - 1)])
    rows.append(['집합 크기', str(len(spread.gold_family(
        0b100101, 0b111101, m)))])
    rows.append(['상호상관이 갖는 값',
                 ' '.join(str(v) for v in sorted(vals))])
    return fmt.table(rows, align='ll')


def sec_zc():
    rows = [['N', 'u', '진폭 최대 편차', '자기상관 최댓값(lag≠0)',
             '다른 근과의 상호상관']]
    for n, u, u2 in ((63, 25, 32), (139, 34, 1), (839, 1, 2)):
        x = spread.zadoff_chu(n, u)
        y = spread.zadoff_chu(n, u2)
        amp = max(abs(abs(v) - 1.0) for v in x)
        ac = max(abs(sum(x[i] * x[(i + lag) % n].conjugate()
                         for i in range(n)))
                 for lag in range(1, min(n, 40)))
        cc = max(abs(sum(x[i] * y[(i + lag) % n].conjugate()
                         for i in range(n)))
                 for lag in range(min(n, 40)))
        rows.append([str(n), str(u), '%.1e' % amp, '%.1e' % ac,
                     '%.3f (√N = %.3f)' % (cc, math.sqrt(n))])
    return fmt.table(rows, align='rrlll')


def sec_gain():
    rows = [['확산율', '처리 이득', '쓰는 곳']]
    for sf, where in ((4, 'WCDMA 최고 속도'), (64, 'IS-95 왈시'),
                      (128, 'IS-95 9.6 kbps 음성'),
                      (256, 'WCDMA 공통 채널'),
                      (512, 'WCDMA 최저 속도')):
        rows.append([str(sf), '%.2f dB' % spread.processing_gain_db(sf),
                     where])
    return fmt.table(rows, align='rrl')


def main():
    return report.write('spread.txt', [
        ('왈시 부호는 서로 직교한다', sec_walsh()),
        ('OVSF 나무와 조상 관계', sec_ovsf()),
        ('되먹임 다항식을 검산한다', sec_primitive()),
        ('m-수열의 자기상관은 두 값뿐이다', sec_autocorr()),
        ('골드 부호의 상호상관은 세 값뿐이다', sec_gold()),
        ('Zadoff-Chu 의 두 성질', sec_zc()),
        ('처리 이득', sec_gain()),
    ])


if __name__ == '__main__':
    print(main())
