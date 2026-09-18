# -*- coding: utf-8 -*-
"""api_table.py — termux-* 명령 색인을 캡처에서 만든다.

    python3 tools/api_table.py      # data/api_cmds.tsv 를 다시 쓴다

주인 패키지와 "termux-api 를 부르나" 는 이 기기의 캡처에서 온다
(out/dpkg_stats.txt 3절, out/api_mechanism.txt 4절) — 손으로 적으면
패키지가 바뀔 때 조용히 어긋난다. 개인정보 등급은 PLAN.md §0.8 의
목록이고, 그 명령은 이 덱에서 **한 번도 실행하지 않는다**.
run-in-deck 은 실제로 돌린 곳이다: never · native(사용자가 네이티브
에서) · proot(이 세션의 캡처) · -(돌리지 않음).

시간 O(명령 수).
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# PLAN.md §0.8 — 절대 실행하지 않는 개인정보 명령
SENSITIVE = re.compile(
    r'^termux-(sms-.*|call-log|contact-list|location|camera-photo|'
    r'microphone-record|telephony-.*|notification-list|fingerprint|'
    r'keystore|nfc|usb)$')
# tools/native_facts.sh 가 네이티브에서 돌리는 읽기 명령
NATIVE = {'termux-battery-status', 'termux-sensor',
          'termux-camera-info', 'termux-tts-engines',
          'termux-audio-info', 'termux-wifi-connectioninfo',
          'termux-info'}
# 이 세션의 캡처(run_all.py)가 proot 안에서 돌린 것
PROOT = {'termux-info', 'termux-battery-status',
         'termux-fix-shebang'}
COLS = ['command', 'owner-package', 'needs-app', 'privacy',
        'run-in-deck', 'source']


def _body(capture):
    return [l for l in capture.split('\n')
            if l and not l.startswith(('== ', '$ ', '## tmx:'))]


def build(dpkg_capture, calls_capture, native, proot):
    """캡처 두 개 → [{칸: 값}], 명령 이름 차례."""
    owner = {}
    for line in _body(dpkg_capture):
        pkg, _, path = line.partition(': ')
        if path:
            owner[os.path.basename(path)] = pkg
    calls = set(_body(calls_capture))
    rows = []
    for cmd in sorted(owner):
        if SENSITIVE.match(cmd):
            run = 'never'
        elif cmd in native:
            run = 'native'
        elif cmd in proot:
            run = 'proot'
        else:
            run = '-'
        rows.append({'command': cmd, 'owner-package': owner[cmd],
                     'needs-app': 'yes' if cmd in calls else 'no',
                     'privacy': ('sensitive' if SENSITIVE.match(cmd)
                                 else 'safe'),
                     'run-in-deck': run,
                     'source': 'out/dpkg_stats.txt 3 · '
                               'out/api_mechanism.txt 4'})
    return rows


def to_tsv(rows):
    head = ['# termux-* 명령 색인 — tools/api_table.py 가 캡처에서'
            ' 만든다. 손으로 고치지 말 것.',
            '# privacy=sensitive 는 PLAN.md §0.8 — 이 덱은 실행하지'
            ' 않는다.', '\t'.join(COLS)]
    return '\n'.join(head + ['\t'.join(r[c] for c in COLS)
                             for r in rows]) + '\n'


def section(name, n):
    text = io.open(os.path.join(BASE, 'out', name),
                   encoding='utf-8').read()
    parts = re.split(r'(?m)^(?=== \d+\. )', text)
    for p in parts:
        if p.startswith('== %d. ' % n):
            return p
    raise LookupError('%s 에 %d절이 없다' % (name, n))


def main(argv):
    rows = build(section('dpkg_stats.txt', 3),
                 section('api_mechanism.txt', 4), NATIVE, PROOT)
    io.open(os.path.join(BASE, 'data', 'api_cmds.tsv'), 'w',
            encoding='utf-8', newline='\n').write(to_tsv(rows))
    print('명령 %d개 → data/api_cmds.tsv' % len(rows))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
