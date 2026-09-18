# -*- coding: utf-8 -*-
"""tree_sort — 트리 항목의 정렬 규칙(3부·부록 A 4단계).

디렉터리 a 는 "a/" 로 비교된다. 그래서 a-b(0x2d)·a.b(0x2e) 가 a/
(0x2f) 보다 앞이고, a=b(0x3d)·ab 는 뒤다. 이름만으로 정렬하면 a 가
맨 앞에 와서 다른 트리 — 다른 이름 — 가 된다.
"""


def run(ctx):
    r = ctx.repo('tree_sort')
    for name in ('ab', 'a=b', 'a.b', 'a-b', 'a/x'):
        r.write(name, name + '\n')
    r.cap('git add .')
    r.cap('git ls-files --stage')
    r.cap('git write-tree')
    r.cap('git ls-tree $(git write-tree)')
    r.cap('git cat-file -p $(git write-tree) | od -c | head -12')
    r.cap("printf 'a-b\\na.b\\na/\\na=b\\nab\\n' | LC_ALL=C sort")
    r.cap("printf 'a-b\\na.b\\na\\na=b\\nab\\n' | LC_ALL=C sort",
          label='tree_sort.plain')
    # 실행 비트와 모드 — 모드는 blob 이 아니라 트리에 적힌다
    r.write('run.sh', '#!/bin/sh\necho hi\n', 0o755)
    r.sh('ln -s ab link')
    r.cap('git add run.sh link', label='tree_sort.modes')
    r.cap('git ls-files --stage run.sh link ab')
    r.sh('git commit -q -m tree')
    r.cap('git ls-tree -r -t HEAD')
