# -*- coding: utf-8 -*-
"""세 언어 공통의 아주 작은 테스트 하네스.

   프레임워크를 쓰지 않는 이유는 하나다. 같은 테스트를 루아와 타입스크립트로도
   옮겨야 하는데, 프레임워크가 다르면 출력이 달라지고 출력이 달라지면
   덱에 실을 로그도 달라진다. 그래서 '이름 · 기대 · 실제' 만 찍는다.
"""
from __future__ import print_function

import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN = os.path.join(BASE, 'golden')
sys.path.insert(0, os.path.join(BASE, 'py'))

_state = {'ok': 0, 'bad': 0, 'name': '?'}


def title(name):
    _state['name'] = name
    print('== %s ==' % name)


def check(what, got, want):
    if got == want:
        _state['ok'] += 1
    else:
        _state['bad'] += 1
        print('  실패 %s' % what)
        print('    기대 %r' % (want,))
        print('    실제 %r' % (got,))
    return got == want


def check_true(what, cond):
    return check(what, bool(cond), True)


def note(fmt, *a):
    print('  ' + (fmt % a if a else fmt))


def golden(name):
    return io.open(os.path.join(GOLDEN, name), encoding='utf-8').read()


def done():
    print('%s: 통과 %d · 실패 %d' % (_state['name'], _state['ok'], _state['bad']))
    sys.exit(1 if _state['bad'] else 0)
