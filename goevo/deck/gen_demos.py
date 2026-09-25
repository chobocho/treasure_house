#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""데모 자료 → deck/demos.js (PLAN.md §3.6, §5 8단계).

데모 다섯(연표 훑기·어느 판에서 왔나·go 줄 사다리·API 증가·GODEBUG 찾기)은
자바스크립트지만, 자료는 전부 data/ 와 out/ 의 표에서 온다. 이 스크립트가
그 표를 JSON 한 줄(var DATA = …)로 옮기고, 손으로 쓴 데모 코드
deck/demos_src.js 를 뒤에 붙여 deck/demos.js 를 만든다. 조립기는 demos.js
를 덱 끝 <script> 에 그대로 넣는다.

    python3 deck/gen_demos.py           # demos.js 다시 만들기
    python3 deck/gen_demos.py --check   # 표와 demos.js 가 어긋났으면 실패

표를 고치고 이것을 안 돌리면 데모가 옛 자료를 보인다 — --check 가 잡는다.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cites                            # noqa: E402
from gen_tables import dict_rows        # noqa: E402

SRC = os.path.join(HERE, 'demos_src.js')
TARGET = os.path.join(HERE, 'demos.js')
LADDER = os.path.join(BASE, 'out', 'ladder_data.txt')
SAMPLE = 12      # API 데모가 보이는 표본 패키지 수 — 접힌 화면 한 줄 반


def short(version):
    """'go1' → '1.0', 'go1.21.0' → '1.21', 'go1.5' → '1.5'."""
    parts = version[2:].split('.')
    return '1.0' if parts == ['1'] else '.'.join(parts[:2])


def build_data(releases, timeline, features, ladder, godebug, api):
    """표들 → 데모가 쓰는 작은 JSON. 칸은 배열로(이름 없이) 줄여 싣는다.
    O(행 수)."""
    rel = [[short(r['version']), r['date']] for r in releases
           if r.get('kind') == 'major']
    majors = set(v for v, _ in rel)
    return {
        'rel': rel,
        'tl': [[r['date'], r['event']] for r in timeline],
        # 초안(1.28)의 항목은 '어느 판에서 왔나' 카드로 내지 않는다 — 아직 없는 판
        'feat': [[f['id'], f['version'], f['title'], f.get('slide-id', '')]
                 for f in features if f.get('version') in majors],
        'ladder': [list(r) for r in ladder],
        'godebug': [[g['setting'], g['package'], g['introduced-in'],
                     g['default-changed-in'], g['old-value']] for g in godebug],
        'api': [[a['version'], int(a['new-packages']), int(a['new-symbols']),
                 int(a['syscall-symbols']),
                 [p for p in a['sample-packages'].split(', ') if p][:SAMPLE]]
                for a in api],
    }


def render(data, src):
    head = ('"use strict";\n'
            '// 생성 파일 — deck/gen_demos.py 가 data/·out/ 의 표와 '
            'deck/demos_src.js 로 만든다.\n'
            '// 손으로 고치지 말 것. 데모 코드는 demos_src.js 에서 고친다.\n')
    line = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return head + 'var DATA = ' + line + ';\n' + src


def ladder_rows():
    with io.open(LADDER, encoding='utf-8') as f:
        return [tuple(l.rstrip('\n').split('\t')) for l in f if l.strip()]


def make():
    data = build_data(dict_rows('releases.tsv'), dict_rows('timeline.tsv'),
                      cites.feature_rows(BASE), ladder_rows(),
                      dict_rows('godebug.tsv'), dict_rows('api_added.tsv'))
    with io.open(SRC, encoding='utf-8') as f:
        return render(data, f.read())


def main(argv):
    js = make()
    if '--check' in argv:
        old = ''
        if os.path.exists(TARGET):
            with io.open(TARGET, encoding='utf-8') as f:
                old = f.read()
        if old != js:
            print('데모 자료: deck/demos.js 가 표와 어긋난다 — '
                  'python3 deck/gen_demos.py 를 돌릴 것')
            return 1
        print('데모 자료: deck/demos.js 가 표와 같다')
        return 0
    with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
        f.write(js)
    print('데모 자료 → deck/demos.js (%d바이트)' % len(js.encode('utf-8')))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
