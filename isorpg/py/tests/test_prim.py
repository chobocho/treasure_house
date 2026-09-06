# -*- coding: utf-8 -*-
"""프리미티브 보고서가 골든과 바이트 단위로 같은가.

   같은 보고서를 루아·타입스크립트도 찍는다. 세 언어의 출력이 이 한 파일과
   전부 같으면 이식이 맞다는 뜻이다.
"""
from __future__ import print_function

import harness as H
from isorpg import main as MAIN

H.title('prim')

got = MAIN.prim_report()
want = H.golden('prim.txt')

gl, wl = got.split('\n'), want.split('\n')
H.check('줄 수', len(gl), len(wl))
bad = 0
for i in range(min(len(gl), len(wl))):
    if gl[i] != wl[i]:
        bad += 1
        if bad <= 5:
            print('  %d줄 다름' % (i + 1))
            print('    기대 %r' % wl[i])
            print('    실제 %r' % gl[i])
H.check('다른 줄', bad, 0)
H.check('전체 바이트', got == want, True)
H.note('보고서 %d줄 · %d바이트', len(gl), len(got.encode('utf-8')))

H.done()
