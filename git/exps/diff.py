# -*- coding: utf-8 -*-
"""diff — 편집 스크립트를 고르는 네 알고리즘과 그 친구들(9부).

같은 두 파일을 myers·minimal·patience·histogram 으로 견준다. 입력은
함수 하나(fact)를 지우고 다른 함수(fib)를 위에 새로 넣은 C 파일 —
"{" · "}" 만 있는 줄이 흔해서 myers 는 그 줄들을 같은 줄로 붙잡고,
patience 는 한 번씩만 나오는 줄만 닻으로 삼는다. 이어 단어 단위
diff, 공백 무시, blame 의 줄 옮김 추적, 곡괭이(-S/-G), bisect run.
"""
from exps.util import commit, tick

OLD = r'''#include <stdio.h>

// Frobs foo heartily
int frobnitz(int foo)
{
    int i;
    for(i = 0; i < 10; i++)
    {
        printf("Your answer is: ");
        printf("%d\n", foo);
    }
}

int fact(int n)
{
    if(n > 1)
    {
        return fact(n-1) * n;
    }
    return 1;
}

int main(int argc, char **argv)
{
    frobnitz(fact(10));
}
'''
NEW = r'''#include <stdio.h>

int fib(int n)
{
    if(n > 2)
    {
        return fib(n-1) + fib(n-2);
    }
    return 1;
}

// Frobs foo heartily
int frobnitz(int foo)
{
    int i;
    for(i = 0; i < 10; i++)
    {
        printf("%d\n", foo);
    }
}

int main(int argc, char **argv)
{
    frobnitz(fib(10));
}
'''


def run(ctx):
    r = ctx.repo('diff_algos')
    r.write('old.c', OLD)
    r.write('new.c', NEW)
    rows = []
    for algo in ('myers', 'minimal', 'patience', 'histogram'):
        cmd = ('git diff --no-index --diff-algorithm=%s old.c new.c'
               % algo)
        text = r.cap(cmd, ok=(1,))
        body = [l for l in text.split('\n')[4:] if l[:1] in '+-@']
        rows.append([algo, sum(l[:1] == '-' for l in body),
                     sum(l[:1] == '+' for l in body),
                     sum(l[:2] == '@@' for l in body), body])
    # 먼저 myers 의 줄들을 잡아 둔다 — 루프 안에서 rows[0][4] 를 바꾸면
    # 그 뒤 비교가 전부 '다르다' 가 된다(처음 판이 그랬다)
    first = rows[0][4]
    for row in rows:
        row[4] = '같다' if row[4] == first else '다르다'
    ctx.table('diff_algos', ['알고리즘', '지운 줄', '더한 줄', '덩어리',
                             'myers 와 출력'],
              rows, '같은 old.c → new.c 를 네 알고리즘으로')
    r.cap('git -c diff.indentHeuristic=false diff --no-index '
          'old.c new.c', ok=(1,))
    # 단어 단위 · 공백 무시 · 통계
    r = ctx.repo('diff_words')
    commit(r, 0, 'base', {'p.txt': 'the quick brown fox\n'
                                   'jumps over the lazy dog\n',
                          'q.py': 'def f(x):\n    return x+1\n'})
    r.write('p.txt', 'the quick red fox\njumps over the lazy cat\n')
    r.write('q.py', 'def f(x):\n        return x+1\n')
    r.cap('git diff --word-diff p.txt')
    r.cap('git diff --color-words p.txt | cat -v')
    r.cap('git diff q.py')
    r.cap('git diff -w q.py')
    r.cap('git diff --stat')
    r.cap('git diff --numstat')
    # blame — -M 은 파일 안에서 옮긴 줄, -C 는 다른 파일에서 온 줄.
    # 줄이 짧으면 감지 문턱(영숫자 -M 20자·-C 40자)에 못 미쳐 아무 일도
    # 없다(처음 판이 그랬다). 줄마다 영숫자를 넉넉히 넣는다.
    r = ctx.repo('blame')
    body = ''.join('line %d: the quick brown fox jumps over the lazy dog\n'
                   % i for i in range(1, 7))
    commit(r, 0, 'base', {'a.txt': body})
    commit(r, 1, 'append', {'a.txt': body + 'line 7\n'})
    moved = body.split('\n')
    moved = '\n'.join(moved[3:6] + moved[0:3]) + '\nline 7\n'
    commit(r, 2, 'move block', {'a.txt': moved})
    commit(r, 3, 'copy to b', {'b.txt': ''.join(body.split('\n')[i] + '\n'
                                              for i in range(3))})
    commit(r, 4, 'indent',
           {'a.txt': moved.replace('line 7', '  line 7')})
    r.cap('git blame -s a.txt')
    r.cap('git blame -s -w a.txt')
    r.cap('git blame -s -M a.txt')
    r.cap('git blame -s b.txt')
    r.cap('git blame -s -C b.txt')
    r.cap('git blame -s -C -C b.txt')
    # 곡괭이 — 문자열의 수가 바뀐 커밋(-S)과 줄이 맞는 커밋(-G)
    r.cap('git log --oneline -S "line 7"')
    r.cap('git log --oneline -G "line 7"')
    r.cap('git log --oneline --follow -- b.txt')
    # bisect run — 스크립트가 좋고 나쁨을 판정한다
    r = ctx.repo('bisect')
    for n in range(1, 17):
        commit(r, n, 'c%d' % n, {'value': '%d\n' % (0 if n < 11 else 1),
                                  'n': '%d\n' % n})
    r.write('../bisect-test.sh', '#!/bin/sh\n'
            '# 값이 0 이면 좋음(0), 1 이면 나쁨(1)\n'
            'exit $(cat value)\n', 0o755)
    r.cap('cat ../bisect-test.sh')
    r.cap('git bisect start HEAD HEAD~15')
    r.cap('git bisect run ../bisect-test.sh')
    r.cap('git bisect log')
    r.cap('git bisect reset')
