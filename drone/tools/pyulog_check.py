# -*- coding: utf-8 -*-
"""ex/ulog_mini.py 가 쓴 ULog 를 공식 파서 pyulog 로 다시 읽는다 (6부).

pyulog 는 numpy 가 필요해, numpy 가 있는 파이썬으로 돌린다(이 기계는
Termux 쪽 python3). 우리 읽기 함수(ulog_mini.read)와 값이 같은지 본다.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'ex'))
import ulog_mini as U  # noqa: E402
from pyulog import ULog  # noqa: E402


def main():
    w = U.Writer(1000)
    w.info('sys_name', 'droneshow')
    w.format('pos', [('uint64_t', 'timestamp'), ('float', 'x'),
                     ('float', 'y')])
    w.subscribe('pos')
    for k in range(5):
        w.data('pos', [20000 * (k + 1), 1.5 * k, -0.5 * k])
    w.text('4', 60000, 'fence breach')
    b = w.bytes()
    p = os.path.join(tempfile.mkdtemp(), 'mini.ulg')
    with open(p, 'wb') as f:
        f.write(b)
    u = ULog(p)
    d = u.data_list[0]
    ours = U.read(b)
    print('파일 %d 바이트 — pyulog 로 읽음' % len(b))
    print('시작 시각 %d µs · 정보 %s' % (u.start_timestamp,
                                      u.msg_info_dict))
    print('형식 %s · 줄 %d' % (d.name, len(d.data['timestamp'])))
    ts, xs, ys = d.data['timestamp'], d.data['x'], d.data['y']
    for k in range(len(ts)):
        print('  %6d  x %.1f  y %.1f' % (ts[k], xs[k], ys[k]))
    m = u.logged_messages[0]
    print('글: 수준 %s · %d µs · "%s"' % (chr(m.log_level), m.timestamp,
                                        m.message))
    same = all(int(d.data['timestamp'][k]) == r['timestamp']
               and float(d.data['x'][k]) == r['x']
               and float(d.data['y'][k]) == r['y']
               for k, r in enumerate(ours['data']['pos']))
    print('ulog_mini.read 와 같은 값: %s' % same)
    return 0 if same else 1


if __name__ == '__main__':
    sys.exit(main())
