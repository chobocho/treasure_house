# -*- coding: utf-8 -*-
"""시나리오 트레이스 — 골든과 한 줄도 어긋나지 않는가."""
from __future__ import print_function

import harness as H
from isorpg import game as G

H.title('trace')

got = G.run_script_trace()
want = H.golden('trace.jsonl')
gl = got.rstrip('\n').split('\n')
wl = want.rstrip('\n').split('\n')

H.check('줄 수', len(gl), len(wl))
bad = 0
for i in range(min(len(gl), len(wl))):
    if gl[i] != wl[i]:
        bad += 1
        if bad <= 3:
            print('  %d줄 다름' % (i + 1))
            print('    기대 %s' % wl[i])
            print('    실제 %s' % gl[i])
H.check('다른 줄', bad, 0)

# ---- 두 번 돌려도 같은가
H.check('재현성', G.run_script_trace(), got)

# ---- 트레이스가 실제로 뭔가를 했는가 (빈 시나리오 방지)
import json                                                    # noqa: E402
ticks = [json.loads(l) for l in gl if l.startswith('{"t"')]
marks = [json.loads(l) for l in gl if l.startswith('{"mark"')]
H.check('표식 개수', len(marks), 11)
H.check_true('222줄의 틱 (되돌린 뒤 다시 진행한 몫 포함)', len(ticks) == 222)
H.check_true('몬스터가 줄었다', ticks[-1]['mon'] < ticks[0]['mon'])
H.check_true('레벨이 올랐다', ticks[-1]['lv'] > ticks[0]['lv'])
H.check_true('되돌리기가 실제로 시간을 되돌렸다',
             any(ticks[i + 1]['t'] < ticks[i]['t'] for i in range(len(ticks) - 1)))
H.check_true('플레이어가 움직였다', ticks[0]['px'] != ticks[-1]['px']
             or ticks[0]['py'] != ticks[-1]['py'])
H.check_true('본 칸이 늘었다', ticks[-1]['seen'] > ticks[0]['seen'])
# 숫자 자리에 부동소수점 표기가 섞이면 언어마다 자릿수가 달라져 파리티가 깨진다.
import re                                                      # noqa: E402
numpat = re.compile(r'-?\d+$')
bad = 0
for l in gl:
    if not l.startswith('{"t"'):
        continue
    for tok in re.findall(r':\s*(-?[\d.eE+]+)', l):
        if not numpat.match(tok):
            bad += 1
H.check('정수가 아닌 숫자 토큰', bad, 0)

H.done()
