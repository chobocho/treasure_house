#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""py/demo 의 데모를 전부 돌려 out/ 를 다시 채운다.

    python3 run_all.py            # 전부 돌린다
    python3 run_all.py --check    # 폭 검사와 manifest 대조만

덱에 실리는 캡처는 하나도 손으로 쓰지 않는다. 전부 여기서 나온다.
그래서 이 파일은 덱의 **증거 목록** 이기도 하다 — 무엇을 실제로
돌려 봤는지 알고 싶으면 여기를 읽으면 된다.

두 가지를 함께 본다.

  · **폭** — 캡처 한 줄이 108칸을 넘으면 폴더블 접힘에서 가로로
    비어져 나간다. 조립기도 같은 검사를 하지만, 표를 만든 자리에서
    잡는 편이 고치기 쉽다(한글은 두 칸으로 센다).
  · **재현** — out/manifest.json 에 파일마다 SHA-256 을 남긴다.
    tools/record.sh --check 가 세 번 돌려 이것이 같은지 본다.

데모는 시각을 재지 않는다. 시간을 찍으면 두 번 돌릴 때마다 값이
달라져 캡처가 증거 노릇을 못 하기 때문이다.
"""
import hashlib
import importlib
import io
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
DEMO = os.path.join(HERE, 'py', 'demo')
MAX_COLS = 108

sys.path.insert(0, os.path.join(HERE, 'py'))


def cells(s):
    """화면 칸 수. 한글·CJK 는 두 칸."""
    n = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def demo_names():
    return sorted(n[:-3] for n in os.listdir(DEMO)
                  if n.startswith('demo_') and n.endswith('.py'))


def run_all():
    made = []
    for name in demo_names():
        mod = importlib.import_module('demo.' + name)
        path = mod.main()
        made.append(os.path.basename(path))
        print('  %-22s → out/%s' % (name, os.path.basename(path)))
    return made


def width_problems():
    bad = []
    for name in sorted(os.listdir(OUT)):
        if not name.endswith('.txt'):
            continue
        text = io.open(os.path.join(OUT, name), encoding='utf-8').read()
        for i, line in enumerate(text.split('\n'), 1):
            w = cells(line)
            if w > MAX_COLS:
                bad.append('out/%s:%d %d칸 (최대 %d)'
                           % (name, i, w, MAX_COLS))
    return bad


def manifest():
    out = {}
    for name in sorted(os.listdir(OUT)):
        if not name.endswith('.txt'):
            continue
        raw = io.open(os.path.join(OUT, name), 'rb').read()
        out[name] = hashlib.sha256(raw).hexdigest()
    return out


def main(argv):
    if '--check' not in argv:
        print('데모를 돌린다 —')
        run_all()
    bad = width_problems()
    for line in bad:
        print('  ✗ ' + line)
    man = manifest()
    p = os.path.join(OUT, 'manifest.json')
    if '--check' in argv:
        old = json.load(io.open(p, encoding='utf-8')) \
            if os.path.exists(p) else {}
        if old != man:
            print('  ✗ out/manifest.json 이 캡처와 어긋난다')
            return 1
    else:
        io.open(p, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(man, indent=1, sort_keys=True) + '\n')
    print('캡처 %d개 · 108칸 넘는 줄 %d개' % (len(man), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
