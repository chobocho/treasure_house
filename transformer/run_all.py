#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""py/demo 의 데모를 전부 차례로 돌려 out/ 를 다시 채운다.

    python3 run_all.py              # 전부
    python3 run_all.py --only c_add # 이름에 c_add 가 든 데모만
    python3 run_all.py --check      # 폭 검사와 manifest 대조만

덱에 실리는 캡처는 하나도 손으로 쓰지 않는다. 전부 여기서 나온다.
그래서 이 파일은 덱의 **증거 목록** 이기도 하다.

  · 차례: 파이썬 데모(가볍다) → 파이썬↔C 대조 → C 학습(무겁다) →
    학습된 체크포인트를 읽는 데모(어텐션 지도). 기계가 좁아 하나씩
    직렬로만 돈다(PLAN.md §0.7).
  · 폭: 캡처 한 줄이 108칸을 넘으면 폴더블 접힘에서 비어져 나간다.
  · 재현: out/manifest.json 에 파일마다 SHA-256 을 남긴다.
    tools/record.sh --check 가 세 번 돌려 같은지 본다. 시간을 재는
    bench.txt 하나만 그 대조에서 빠진다.

c/tfs 가 먼저 만들어져 있어야 한다(make cc). 돌리는 동안 c/tfs 를
다시 만들지 말 것 — 실행 중인 파일을 바꾸면 학습이 SIGBUS 로 죽는다.
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
MAX_COLS = 108
ORDER = ['scalar', 'gradcheck', 'ops', 'attention', 'posenc', 'params',
         'optim', 'tokenizer', 'kvcache', 'extras', 'py_tiny',
         'c_vs_py', 'c_bench', 'c_add', 'c_addplain', 'c_sort',
         'c_reverse', 'c_parity', 'c_ko', 'c_en', 'attnmaps']

sys.path.insert(0, os.path.join(HERE, 'py'))


def cells(s):
    n = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def run(only):
    for name in ORDER:
        if only and only not in name:
            continue
        mod = importlib.import_module('demo.demo_' + name)
        path = mod.main()
        print('  %-16s → out/%s' % (name, os.path.basename(path)))
        sys.stdout.flush()


def width_problems():
    bad = []
    for name in sorted(os.listdir(OUT)):
        if not name.endswith('.txt'):
            continue
        text = io.open(os.path.join(OUT, name), encoding='utf-8').read()
        for i, line in enumerate(text.split('\n'), 1):
            if name.startswith('curve_') or 'attnmaps' in name:
                continue            # 그림용 자료 — 덱에 안 싣는다
            w = cells(line)
            if w > MAX_COLS:
                bad.append('out/%s:%d %d칸 (최대 %d)'
                           % (name, i, w, MAX_COLS))
    return bad


def manifest():
    out = {}
    for name in sorted(os.listdir(OUT)):
        if name.endswith('.txt') or name.endswith('.html'):
            raw = io.open(os.path.join(OUT, name), 'rb').read()
            out[name] = hashlib.sha256(raw).hexdigest()
    return out


def main(argv):
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    if '--check' not in argv:
        print('데모를 돌린다 —')
        run(only)
    bad = width_problems()
    for line in bad:
        print('  ✗ ' + line)
    man = manifest()
    p = os.path.join(OUT, 'manifest.json')
    if '--check' in argv:
        old = json.load(io.open(p, encoding='utf-8')) \
            if os.path.exists(p) else {}
        stale = sorted(k for k in man if old.get(k) != man[k])
        for k in stale:
            print('  ✗ out/%s 가 manifest 와 어긋난다' % k)
        if stale:
            return 1
    else:
        io.open(p, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(man, indent=1, sort_keys=True) + '\n')
    print('캡처 %d개 · 108칸 넘는 줄 %d개' % (len(man), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
