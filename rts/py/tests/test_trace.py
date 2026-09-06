# -*- coding: utf-8 -*-
"""트레이스·해시·리플레이·락스텝 부명령 (SPEC §18.3, §19, §20, §24)."""
from __future__ import print_function

import os

import harness as H
from rts import main as MAIN

H.title('trace')

N = 40
tr = MAIN.cmd_trace(N).split('\n')[:-1]
H.check('틱마다 한 줄', len(tr), N)
H.check('첫 줄의 틱', tr[0][:6], '{"t":1')
H.check('마지막 줄의 틱', tr[-1].startswith('{"t":%d,' % N), True)
H.check('키 순서가 명세대로',
        [k for k in ('"t":', '"h":', '"cr":', '"su":', '"sc":', '"n":', '"ev":')
         if k not in tr[0]], [])
H.check('공백이 없다', ' ' in tr[0], False)
H.check('해시는 8자리 대문자 16진',
        len([1 for ln in tr
             if not (ln.split('"h":"')[1][:8].upper()
                     == ln.split('"h":"')[1][:8])]), 0)
H.check('두 번 돌려도 같다', MAIN.cmd_trace(N).split('\n')[:-1], tr)

hs = MAIN.cmd_hashes(N).split('\n')[:-1]
H.check('해시 줄 수', len(hs), N)
H.check('형식은 "틱 해시"', hs[0].split()[0], '1')
H.check('트레이스의 해시와 같다',
        [ln.split()[1] for ln in hs],
        [ln.split('"h":"')[1][:8] for ln in tr])
H.check_true('해시가 변한다', len(set(hs)) == N)

out = MAIN.cmd_lockstep(60)
H.check_true('락스텝 60틱 일치', '락스텝 60틱 일치' in out)
H.check_true('float_bug 실험 결과가 한 줄 나온다', 'float_bug:' in out)
H.note('%s', out.strip().split('\n')[-2])

tmp = os.path.join(os.path.dirname(H.GOLDEN), 'out')
if not os.path.isdir(tmp):
    os.makedirs(tmp)
path = os.path.join(tmp, 'test_replay.bin')
msg = MAIN.cmd_replay(path, 60)
H.check_true('리플레이 재생이 일치한다', msg.strip().endswith('일치'))
H.check_true('리플레이는 작다 (%s)' % msg.strip(),
             os.path.getsize(path) < 4096)
H.check('상태는 저장하지 않는다 — 파일에 머리 넷 글자',
        open(path, 'rb').read()[:4], b'RTSR')
os.remove(path)

H.done()
