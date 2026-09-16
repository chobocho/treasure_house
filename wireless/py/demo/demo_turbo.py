# -*- coding: utf-8 -*-
"""3부 — 터보 부호의 숫자."""
from wirelesslib import fmt, turbo
from demo import report


def sec_encoder():
    rows = [['확인할 것', '값']]
    msg = [1, 0, 1, 1, 0, 0, 1, 0]
    sysb, par, tail = turbo.rsc_encode(msg)
    rows.append(['구성 부호', '8상태 RSC · g₀=1+D²+D³ · g₁=1+D+D³'])
    rows.append(['계통 비트', ''.join(map(str, sysb))])
    rows.append(['패리티', ''.join(map(str, par))])
    rows.append(['꼬리 6비트', ''.join(map(str, tail))])
    rows.append(['꼬리 뒤 상태',
                 str(turbo.rsc_final_state(msg, tail))])
    rows.append(['K=40 부호어 길이',
                 '%d (= 3K + 12)' % len(turbo.encode([0] * 40, 3, 10))])
    return fmt.table(rows, align='ll')


def sec_impulse():
    out = []
    for name, bits in (('되먹임 있음(RSC)', [1] + [0] * 19),):
        _s, par, _t = turbo.rsc_encode(bits)
        out.append('%s: 패리티 %s' % (name, ''.join(map(str, par))))
    out.append('1 하나만 넣어도 패리티가 멎지 않는다 —'
               ' 되먹임의 표시다.')
    out.append('비되먹임 부호라면 K−1 걸음 뒤 전부 0 이 된다.')
    return '\n'.join(out)


def sec_qpp():
    rows = [['K', 'f₁', 'f₂', '순열인가', 'Π(0..7)']]
    for k, f1, f2 in ((40, 3, 10), (48, 7, 12), (64, 7, 16),
                      (128, 15, 32), (512, 31, 64)):
        perm = turbo.qpp(k, f1, f2)
        ok = sorted(perm) == list(range(k))
        rows.append([str(k), str(f1), str(f2),
                     '예' if ok else '아니오',
                     ' '.join(str(v) for v in perm[:8])])
    return fmt.table(rows, align='rrrll')


def sec_iters():
    rows = [['Eb/N0 [dB]', 'K'] + ['%d회' % i for i in range(1, 7)]]
    for ebn0, k, f1, f2 in ((1.0, 40, 3, 10), (2.0, 40, 3, 10),
                            (1.0, 128, 15, 32), (2.0, 128, 15, 32)):
        e = turbo.ber_vs_iters(ebn0, 6, 40, k, f1, f2, seed=20260916)
        rows.append(['%.1f' % ebn0, str(k)]
                    + ['%.4f' % v for v in e])
    return (fmt.table(rows, align='rrrrrrrr')
            + '\n\n반복하면 크게 떨어진다. 다만 단조는 아니다 —'
            + '\n오류 마루 근처에서는 몇 프레임이 반복 사이를 오간다.')


def sec_maxlog():
    rows = [['복호 방식', 'Eb/N0 1 dB', 'Eb/N0 2 dB']]
    for name, ml in (('정확한 log-MAP', False),
                     ('max-log-MAP', True)):
        row = [name]
        for ebn0 in (1.0, 2.0):
            row.append('%.4f' % turbo.ber_vs_iters(
                ebn0, 6, 40, 128, 15, 32, seed=7, maxlog=ml)[-1])
        rows.append(row)
    return fmt.table(rows, align='lrr')


def main():
    return report.write('turbo.txt', [
        ('LTE 터보 부호기', sec_encoder()),
        ('되먹임 부호의 임펄스 응답', sec_impulse()),
        ('QPP 인터리버는 순열이다', sec_qpp()),
        ('반복 횟수와 BER', sec_iters()),
        ('log-MAP 과 max-log-MAP', sec_maxlog()),
    ])


if __name__ == '__main__':
    print(main())
