# -*- coding: utf-8 -*-
"""diff2 — diff 알고리즘(9부)의 나머지.

  · 이름 바꾸기 감지 — 닮은 정도(%)와 문턱(-M), 복사(-C,
    --find-copies-harder).
  · 덩어리 머리의 함수 이름 — "@@ … @@ int f(void)".
  · log -L — 한 함수(줄 범위)의 역사만.
  · bisect 를 손으로 — good · bad · skip 과 남은 걸음.
"""
from exps.util import commit, tick

BODY = ''.join('line %02d: some text that makes this file long enough\n'
               % i for i in range(1, 21))


def renames(ctx):
    r = ctx.repo('rename_score')
    commit(r, 0, 'base', {'a.txt': BODY, 'keep.txt': BODY})
    # 이름을 바꾸면서 20줄 중 몇 줄을 고친다
    r.sh('git mv a.txt b.txt')
    lines = BODY.split('\n')
    for k in (0, 1, 2, 3, 4, 5):
        lines[k] = 'changed %d' % k
    r.write('b.txt', '\n'.join(lines))
    r.sh('git add b.txt')
    tick(r, 1)
    r.sh('git commit -q -m "rename and edit"')
    r.cap('git diff --stat -M HEAD~1 HEAD')
    r.cap('git diff --name-status -M HEAD~1 HEAD')
    r.cap('git diff --name-status -M80% HEAD~1 HEAD')
    r.cap('git diff --name-status --no-renames HEAD~1 HEAD')
    # 복사 — 원본(keep.txt)은 이 커밋에서 바뀌지 않았다
    r.write('copy.txt', BODY)
    r.sh('git add copy.txt')
    tick(r, 2)
    r.sh('git commit -q -m copy')
    r.cap('git diff --name-status -C HEAD~1 HEAD', label='rename_score.c')
    r.cap('git diff --name-status -C --find-copies-harder HEAD~1 HEAD',
          label='rename_score.c')


C1 = '''#include <stdio.h>

int helper(int x)
{
    return x * 2;
}

int compute(int n)
{
    int total = 0;
    for (int i = 0; i < n; i++)
        total += helper(i);
    return total;
}
'''


def funcs(ctx):
    r = ctx.repo('funcname')
    commit(r, 0, 'base', {'calc.c': C1, '.gitattributes': '*.c diff=cpp\n'})
    commit(r, 1, 'faster', {'calc.c': C1.replace('total += helper(i);',
                                                 'total += i * 2;')})
    commit(r, 2, 'doubled', {'calc.c': C1.replace(
        'total += helper(i);', 'total += i * 2;').replace(
        'return x * 2;', 'return x + x;')})
    r.cap('git diff HEAD~2 HEAD~1')
    r.cap('git log --oneline -L :compute:calc.c | head -30')


def bisect_hand(ctx):
    r = ctx.repo('bisect_hand')
    for n in range(1, 9):
        commit(r, n, 'c%d' % n, {'value': '%d\n' % (0 if n < 6 else 1),
                                  'n': '%d\n' % n})
    r.cap('git bisect start && git bisect bad && git bisect good HEAD~7')
    r.cap('git bisect skip')
    r.cap('cat value && git bisect good')
    r.cap('cat value && git bisect bad | head -1')
    r.cap('git bisect visualize --oneline')
    r.cap('git bisect reset 2>&1 | tail -1')


def run(ctx):
    renames(ctx)
    funcs(ctx)
    bisect_hand(ctx)
