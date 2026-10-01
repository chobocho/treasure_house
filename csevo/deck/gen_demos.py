#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""데모 자료 → deck/demos.js (PLAN.md §4 7단계).

데모 넷(연표 훑기·langversion 사다리·어느 버전에서 왔나·시대 갤러리)은
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


SRC = os.path.join(HERE, 'demos_src.js')
TARGET = os.path.join(HERE, 'demos.js')


def build_data():
    """표들 → 데모가 쓰는 작은 JSON. 7단계에서 데모를 붙이며 채운다
    (PLAN.md §4 7단계 — 연표·langversion 사다리·어느 버전 퀴즈·시대 갤러리)."""
    return {}


def render(data, src):
    head = ('"use strict";\n'
            '// 생성 파일 — deck/gen_demos.py 가 data/·out/ 의 표와 '
            'deck/demos_src.js 로 만든다.\n'
            '// 손으로 고치지 말 것. 데모 코드는 demos_src.js 에서 고친다.\n')
    line = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return head + 'var DATA = ' + line + ';\n' + src


def make():
    with io.open(SRC, encoding='utf-8') as f:
        return render(build_data(), f.read())


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
