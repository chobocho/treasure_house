# -*- coding: utf-8 -*-
"""index — 스테이징의 실체 .git/index (5부).

항목마다 모드·blob 이름·경로와 함께 stat 칸이 적힌다. git 은 이
칸으로 "안 바뀐 파일" 을 해시 없이 가려내는데, 그 믿음이 틀릴 수
있는 자리(같은 크기·같은 시각)와 그것을 끄는 두 비트(assume-
unchanged·skip-worktree), sparse-checkout 을 보인다.
"""
from exps.util import commit, unstat


def run(ctx):
    r = ctx.repo('index')
    commit(r, 0, 'base', {'a.txt': 'aaaa\n', 'src/m.c': 'int m;\n',
                          'docs/x.md': '# x\n', 'docs/y.md': '# y\n'})
    r.cap('git ls-files --stage')
    r.sh('touch -d @1700000000 a.txt && git update-index --refresh')
    r.cap('git ls-files --debug a.txt', edit=unstat)
    r.cap('od -A d -t x1 -N 12 .git/index')
    r.cap('git ls-files --stage --abbrev')
    # stat 캐시: 같은 크기·같은 mtime 으로 내용만 바꾸면? ctime 까지
    # 보지 말라고 하면(trustctime=false) git 은 바뀐 것을 놓친다. 기본
    # 설정에서는 ctime 의 초가 갈리느냐에 달려 캡처가 흔들린다 — 그래서
    # 결정론적으로 놓치는 쪽만 싣는다.
    r.sh('git config core.trustctime false')
    r.sh("printf 'bbbb\\n' > a.txt && touch -d @1700000000 a.txt")
    r.cap('git status --short')
    r.cap('git hash-object a.txt')
    r.cap('git ls-files --stage a.txt')
    r.cap('touch a.txt && git status --short', label='index.touched')
    r.sh('git config --unset core.trustctime')
    r.sh('git checkout -- a.txt')
    # assume-unchanged: "바뀌지 않았다고 믿어라"
    r.cap('git update-index --assume-unchanged a.txt')
    # 같은 크기로 같은 초에 고치면 racy(5부)라 status 가 흔들린다 —
    # 고친 파일의 mtime 을 따로 못 박아 stat 이 늘 달라 보이게 한다
    r.sh("printf 'cccc\\n' > a.txt && touch -d @1700000100 a.txt")
    r.cap('git status --short', label='index.assumed')
    r.cap('git ls-files -v')
    r.cap('git update-index --no-assume-unchanged a.txt')
    r.cap('git status --short', label='index.unassumed')
    r.sh('git checkout -- a.txt')
    # skip-worktree: "작업 트리의 이 파일은 보지 마라"
    r.cap('git update-index --skip-worktree src/m.c')
    r.cap('git ls-files -v', label='index.skip')
    r.sh('git update-index --no-skip-worktree src/m.c')
    # sparse-checkout(원뿔 모드) — 인덱스의 skip-worktree 비트를 쓴다
    r.cap('git sparse-checkout set --cone docs')
    r.cap('git sparse-checkout list')
    r.cap('ls -R', label='index.sparse')
    r.cap('git ls-files -t', label='index.sparse')
    r.cap('git sparse-checkout disable')
    r.cap('ls -R', label='index.full')
