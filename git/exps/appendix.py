# -*- coding: utf-8 -*-
"""appendix — 부록 A(19부)의 단계마다 "시험이 초록이다" 를 보이는 캡처.

Python 구현의 시험을 모듈 하나씩 -v 로 돌려 시험 이름과 결과를 남긴다.
걸린 시간(" in 0.123s")은 실행마다 달라 지우고, 시험 이름 뒤의
"(mygit.tests.…)" 꼬리는 108칸을 넘어 지운다 — 무엇을 지웠는지는
t.sh 를 cat 한 캡처가 보여 준다. -W ignore 는 시험 코드가 닫지 않은
파일에 대한 ResourceWarning 을 끈다(결과와 무관한 경고 한 줄).

저장소 안에 py/ 와 golden/ 을 가리키는 심볼릭 링크를 두어, 캡처의
명령 줄에 이 기계의 절대 경로가 나오지 않게 한다.
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

T_SH = r'''#!/bin/sh
# 시험 모듈 하나를 -v 로 돌린다. 시간과 긴 꼬리만 지운다.
cd py && python3 -W ignore -m unittest -v "mygit.tests.test_$1" 2>&1 |
  sed -E 's/ \(mygit[^)]*\)//; s/ in [0-9.]+s$//'
'''

MODULES = ['sha1', 'objects', 'blob', 'tree', 'commit', 'index', 'walk',
           'diff', 'checkout', 'merge', 'pack', 'transport', 'scenes']

# 손으로 짠 SHA-1 을 표준 입력에 — 한 줄로 쓰면 108칸을 넘어 파일로
SHA1_PY = '''import sys
from mygit.sha1 import sha1_hex
print(sha1_hex(sys.stdin.buffer.read()))
'''
ONE = 'PYTHONPATH=py python3 sha1.py'


def run(ctx):
    r = ctx.repo('appendix', init=False)
    r.sh('ln -s %s/py py && ln -s %s/golden golden' % (HERE, HERE))
    r.write('t.sh', T_SH, 0o755)
    r.write('sha1.py', SHA1_PY)
    r.cap('cat t.sh')
    r.cap('cat sha1.py')
    for m in MODULES:
        r.cap('./t.sh %s' % m)
    # 손으로 짠 SHA-1 과 이 기계의 sha1sum
    r.cap("printf 'abc' | " + ONE)
    r.cap("printf 'abc' | sha1sum")
    r.cap("printf 'blob 6\\0hello\\n' | " + ONE)
    r.cap('cut -f1,2,4 golden/sha1.tsv | head -9')
    r.cap('wc -l < golden/sha1.tsv')
