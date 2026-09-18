# -*- coding: utf-8 -*-
"""pkgstat.py — dpkg 의 status 파일에서 패키지 수와 크기를 센다.

    python3 py/pkgstat.py $PREFIX/var/lib/dpkg/status

dpkg 는 설치한 패키지를 전부 한 파일(status)에 적는다. 빈 줄로 가른
문단 하나가 패키지 하나이고, 'Status: install ok installed' 인 것만이
지금 설치된 것이다(지웠어도 설정 파일이 남으면 'deinstall ok
config-files' 로 문단이 남는다). Installed-Size 는 KiB 단위다.
6부의 "이 기기의 패키지" 표가 이 셈에서 나온다.

시간 O(파일 크기 + 패키지 수 log 패키지 수).
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deb import parse_control, clip               # noqa: E402
import unicodedata                                  # noqa: E402


def parse_status(text):
    """문단마다 dict 하나. 필드 이어짐은 deb.parse_control 이 맡는다."""
    return [parse_control(p) for p in text.split('\n\n') if p.strip()]


def installed(pkgs):
    return [p for p in pkgs
            if p.get('Status', '').endswith('install ok installed')]


def _size(p):
    try:
        return int(p.get('Installed-Size', ''))
    except ValueError:
        return None


def summary(pkgs, top=10):
    sizes = [(p['Package'], _size(p)) for p in pkgs]
    have = [(n, s) for n, s in sizes if s is not None]
    arch = {}
    for p in pkgs:
        a = p.get('Architecture', '?')
        arch[a] = arch.get(a, 0) + 1
    return {
        'count': len(pkgs),
        'total_kib': sum(s for _n, s in have),
        'no_size': len(sizes) - len(have),
        'essential': sum(1 for p in pkgs
                         if p.get('Essential') == 'yes'),
        'arch': arch,
        'maintainer_termux': sum(1 for p in pkgs
                                 if p.get('Maintainer') == '@termux'),
        'top': sorted(have, key=lambda x: (-x[1], x[0]))[:top],
        'sizes': [s for _n, s in have],
    }


def _unit(kib):
    if kib % 1024 == 0:
        return kib // 1024, 'MiB'
    return kib, 'KiB'


def histogram(sizes, edges):
    """[(구간 이름, 개수)]. edges 는 KiB 경계, 오름차순."""
    counts = [0] * (len(edges) + 1)
    for s in sizes:
        k = 0
        while k < len(edges) and s >= edges[k]:
            k += 1
        counts[k] += 1
    names = []
    for k in range(len(edges) + 1):
        if k == 0:
            names.append('%d %s 미만' % _unit(edges[0]))
        elif k == len(edges):
            names.append('%d %s 이상' % _unit(edges[-1]))
        else:
            (a, ua), (b, ub) = _unit(edges[k - 1]), _unit(edges[k])
            names.append('%d–%d %s' % (a, b, ub) if ua == ub
                         else '%d %s–%d %s' % (a, ua, b, ub))
    return list(zip(names, counts))


EDGES = [100, 1024, 10240, 102400]


def pad(text, width):
    """칸 수로 왼쪽 맞춤 — 한글은 두 칸이라 %-16s 로는 어긋난다."""
    n = sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1
            for c in text)
    return clip(text, width) + ' ' * max(0, width - n)


def report(s):
    out = ['설치된 패키지 %d개 · 설치 크기 합 %s KiB'
           % (s['count'], '{:,}'.format(s['total_kib'])),
           '  Essential: yes %d개 · Maintainer @termux %d개'
           % (s['essential'], s['maintainer_termux']),
           '  아키텍처: ' + ' · '.join(
               '%s %d' % kv for kv in sorted(s['arch'].items()))]
    if s['no_size']:
        out.append('  크기 칸이 없는 것 %d개' % s['no_size'])
    out.append('  크기 분포:')
    for name, n in histogram(s['sizes'], EDGES):
        out.append('    %s %5d' % (pad(name, 16), n))
    out.append('  큰 것 %d개:' % len(s['top']))
    for name, kib in s['top']:
        out.append('    %-28s %10s KiB'
                   % (name[:28], '{:,}'.format(kib)))
    return '\n'.join(out)


def main(argv):
    if len(argv) != 1:
        print('사용법: pkgstat.py STATUS')
        return 2
    text = io.open(argv[0], encoding='utf-8').read()
    print(report(summary(installed(parse_status(text)))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
