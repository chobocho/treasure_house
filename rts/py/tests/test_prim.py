# -*- coding: utf-8 -*-
"""`main prim` 이 골든을 바이트 단위로 재현하는가 (SPEC §24).

   이 한 시험이 엔진 전체와 **독립 참조 구현**(tools/gen_prim.py)의 대조다.
   앞선 시험들이 모듈을 따로 확인했다면, 이것은 열넷 절을 한꺼번에 맞춘다.
"""
from __future__ import print_function

import harness as H
from rts import main as MAIN

H.title('prim')

got = MAIN.cmd_prim().split('\n')
want = H.golden('prim.txt').split('\n')

H.check('줄 수', len(got), len(want))
bad = 0
first = -1
for k in range(min(len(got), len(want))):
    if got[k] != want[k]:
        bad += 1
        if first < 0:
            first = k
            H.note('%d행 기대 %r', k + 1, want[k])
            H.note('     실제 %r', got[k])
H.check('%d행 전부 일치' % len(want), bad, 0)

secs = [ln for ln in want if ln.startswith('== ')]
H.check('절 구분은 14개', len(secs), 14)
H.check('절 표시 형식', [s for s in secs if not s.endswith(' ==')], [])
H.check('덱 지시자가 자를 수 있는 형태', secs[0], '== 1. 거리 척도 ==')
H.check('출력은 줄바꿈으로 끝난다', MAIN.cmd_prim()[-1], '\n')

# 절 하나만 바뀌어도 잡히는가 — 시험 자체의 민감도 확인
H.check_true('절마다 내용이 다르다', len(set(secs)) == 14)

H.done()
