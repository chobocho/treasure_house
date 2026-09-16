# -*- coding: utf-8 -*-
"""3부 — CRC·해밍·컨볼루션 부호의 숫자."""
import itertools
import random

from wirelesslib import codes, fmt
from demo import report


def sec_crc():
    rows = [['이름', '차수', '생성 다항식(16진)', '쓰는 곳']]
    where = {'gsm_crc3': 'GSM 음성 Ia 등급',
             'crc6': 'NR 짧은 제어 정보',
             'crc8': 'LTE',
             'crc11': 'NR',
             'crc16': 'LTE·NR (CRC-CCITT 와 같은 다항식)',
             'crc24a': 'LTE·NR 전송 블록',
             'crc24b': 'LTE·NR 부호 블록',
             'crc24c': 'NR 제어 정보'}
    for name in ('gsm_crc3', 'crc6', 'crc8', 'crc11', 'crc16',
                 'crc24a', 'crc24b', 'crc24c'):
        length, poly = codes.CRC_POLYS[name]
        rows.append([name, str(length), '0x%X' % poly, where[name]])
    return fmt.table(rows, align='lrll')


def sec_crc_check():
    bits = []
    for ch in '123456789':
        bits += [(ord(ch) >> (7 - i)) & 1 for i in range(8)]
    v = 0
    for b in codes.crc(bits, 'crc16'):
        v = (v << 1) | b
    rnd = random.Random(20260916)
    msg = [rnd.getrandbits(1) for _ in range(40)]
    word = codes.crc_append(msg, 'crc24a')
    single = sum(1 for i in range(len(word))
                 if not _flip_ok(word, [i], 'crc24a'))
    double = sum(1 for i, j in itertools.combinations(
        range(len(word)), 2) if not _flip_ok(word, [i, j], 'crc24a'))
    rows = [['확인할 것', '값']]
    rows.append(["CRC-16 of '123456789'", '0x%04X' % v])
    rows.append(['CRC-24A 를 붙인 말의 나머지',
                 '0' * codes.crc_len('crc24a')])
    rows.append(['1비트 오류 %d가지 중 잡힌 수' % len(word),
                 str(single)])
    rows.append(['2비트 오류 %d가지 중 잡힌 수'
                 % (len(word) * (len(word) - 1) // 2), str(double)])
    return fmt.table(rows, align='lr')


def _flip_ok(word, idx, name):
    bad = list(word)
    for i in idx:
        bad[i] ^= 1
    return codes.crc_check(bad, name)


def sec_hamming():
    rows = [['메시지', '부호어', '3번 자리를 뒤집으면', '고친 자리']]
    for v in (0b0000, 0b1011, 0b0110, 0b1111):
        msg = [(v >> (3 - i)) & 1 for i in range(4)]
        cw = codes.hamming74_encode(msg)
        bad = list(cw)
        bad[3] ^= 1
        got, fixed = codes.hamming74_decode(bad)
        rows.append([''.join(map(str, msg)), ''.join(map(str, cw)),
                     ''.join(map(str, bad)), str(fixed)])
    return fmt.table(rows, align='llll')


def sec_conv():
    rows = [['부호', 'K', '부호율', '생성 다항식(8진)', '상태 수',
             '최소 거리(전수)']]
    for c, nmsg in ((codes.GSM_CONV, 12), (codes.IS95_CONV, 10),
                    (codes.LTE_CONV, 10)):
        rows.append([c.name, str(c.k), '1/%d' % c.n,
                     ' '.join('%o' % p for p in c.polys),
                     str(c.nstate), str(c.min_distance(nmsg))])
    return fmt.table(rows, align='lrrlrr')


def sec_viterbi():
    c = codes.GSM_CONV
    msg = [1, 0, 1, 1, 0, 0, 1, 0]
    cw = c.encode(msg, tail=True)
    dmin = c.min_distance(len(msg))
    t = (dmin - 1) // 2
    rows = [['던진 오류 무게', '경우의 수', '전부 고쳤나']]
    for w in range(1, t + 2):
        total = 0
        ok = 0
        for pos in itertools.combinations(range(len(cw)), w):
            bad = list(cw)
            for i in pos:
                bad[i] ^= 1
            total += 1
            if c.viterbi_hard(bad) == msg:
                ok += 1
        rows.append([str(w), str(total),
                     '%d/%d' % (ok, total)])
    return (fmt.table(rows, align='rrr')
            + '\n\n최소 거리 %d → 보장되는 정정 능력 %d비트'
            % (dmin, t))


def sec_interleave():
    rows, cols = 6, 8
    marks = [0] * (rows * cols)
    for i in range(5):
        marks[10 + i] = 1
    spread = codes.block_deinterleave(marks, rows, cols)
    pos = [i for i, v in enumerate(spread) if v]
    out = ['연집 오류 5개가 인터리버 앞에서는'
           ' 10~14 번 자리에 몰려 있다.',
           '디인터리브 뒤 자리: ' + ', '.join(map(str, pos)),
           '가장 가까운 두 오류의 간격: %d (행 수 %d, 열 수 %d)'
           % (min(b - a for a, b in zip(pos, pos[1:])), rows, cols)]
    return '\n'.join(out)


def main():
    return report.write('codes.txt', [
        ('3GPP 가 쓰는 CRC 다항식', sec_crc()),
        ('CRC 를 검산한다', sec_crc_check()),
        ('해밍(7,4)은 한 자리를 고친다', sec_hamming()),
        ('이 책이 다루는 컨볼루션 부호', sec_conv()),
        ('비터비는 보장된 만큼을 전부 고친다', sec_viterbi()),
        ('인터리버는 연집을 흩뿌린다', sec_interleave()),
    ])


if __name__ == '__main__':
    print(main())
