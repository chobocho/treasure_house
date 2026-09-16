# -*- coding: utf-8 -*-
"""3부 — LDPC 의 숫자."""
from wirelesslib import fmt, ldpc
from demo import report

BASE = ldpc.NR_LIKE


def sec_graph():
    rows = [['리프팅 z', '부호어 길이 n', '검사 수 m', '정보 비트 k',
             '부호율', '4-순환']]
    for z in (4, 8, 16, 32):
        h = ldpc.lift(BASE, z)
        rows.append([str(z), str(h.n), str(h.m), str(h.k),
                     fmt.num(h.k / float(h.n), 3),
                     str(ldpc.count_four_cycles(h))])
    return fmt.table(rows, align='rrrrrr')


def sec_base():
    rows = [['행', '이 행이 보는 (열, 이동량)']]
    for r, row in enumerate(BASE.rows):
        rows.append([str(r),
                     ' '.join('(%d,%d)' % (c, s) for c, s in row)])
    return fmt.table(rows, align='rl')


def sec_encode():
    h = ldpc.lift(BASE, 16)
    enc = ldpc.Encoder(h)
    import random
    rnd = random.Random(20260916)
    rows = [['확인할 것', '값']]
    ok = 0
    for _ in range(20):
        msg = [rnd.getrandbits(1) for _ in range(h.k)]
        if ldpc.syndrome_is_zero(h, enc.encode(msg)):
            ok += 1
    rows.append(['부호어 길이', str(h.n)])
    rows.append(['H·c = 0 인 부호어', '%d/20' % ok])
    zero_ok = enc.encode([0] * h.k) == [0] * h.n
    rows.append(['0 메시지 → 0 부호어',
                 '예' if zero_ok else '아니오'])
    return fmt.table(rows, align='ll')


def sec_decode():
    h = ldpc.lift(BASE, 16)
    enc = ldpc.Encoder(h)
    rows = [['Eb/N0 [dB]', '합곱 프레임오류', '최소합 프레임오류',
             '홍수 평균 반복', '계층 평균 반복']]
    for ebn0 in (0.0, 1.0, 2.0, 3.0):
        rows.append([
            '%.1f' % ebn0,
            '%d/40' % ldpc.frame_errors(h, enc, ebn0, 40, 20, 11,
                                        False),
            '%d/40' % ldpc.frame_errors(h, enc, ebn0, 40, 20, 11,
                                        True),
            fmt.num(ldpc.mean_iters(h, enc, ebn0, 25, 30, 13,
                                    False, False), 2),
            fmt.num(ldpc.mean_iters(h, enc, ebn0, 25, 30, 13,
                                    False, True), 2)])
    return fmt.table(rows, align='rrrrr')


def main():
    return report.write('ldpc.txt', [
        ('기저 행렬을 리프팅한 결과', sec_graph()),
        ('기저 행렬 (씨앗 고정 생성기가 만든 것)', sec_base()),
        ('부호화는 앞먹임 한 번으로 끝난다', sec_encode()),
        ('합곱·최소합·일정(schedule) 비교', sec_decode()),
    ])


if __name__ == '__main__':
    print(main())
