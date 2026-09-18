# -*- coding: utf-8 -*-
"""refs — 참조는 파일 하나, HEAD 는 이름표의 이름표(4부).

브랜치 만들기가 40글자 파일 하나를 쓰는 일임을, 분리 HEAD, pack-refs
뒤의 packed-refs, symbolic-ref·update-ref, reflog 와 그 만료, 이름
풀기(~ ^ @{n} @{u})로 보인다.
"""


def commit(r, n, msg):
    secs = 1700000000 + 60 * n
    r.env['GIT_AUTHOR_DATE'] = r.env['GIT_COMMITTER_DATE'] = \
        '%d +0900' % secs
    r.write('f.txt', '%s\n' % msg)
    r.sh('git add f.txt && git commit -q -m "%s"' % msg)


def run(ctx):
    r = ctx.repo('refs')
    for n, msg in enumerate(['A', 'B', 'C']):
        commit(r, n, msg)
    r.cap('cat .git/HEAD')
    r.cap('cat .git/refs/heads/main')
    r.cap('git branch topic HEAD~1')
    r.cap('ls .git/refs/heads')
    r.cap('cat .git/refs/heads/topic')
    r.cap('git log --oneline --decorate --all')
    r.cap('git symbolic-ref HEAD')
    r.cap('git rev-parse HEAD HEAD~1 HEAD^ HEAD~2 main@{1}')
    r.cap('git rev-parse --abbrev-ref HEAD')
    r.cap('git switch --detach HEAD~2')
    r.cap('cat .git/HEAD', label='refs.detached')
    r.cap('git symbolic-ref HEAD', label='refs.detached', ok=(128,))
    r.cap('git status', label='refs.detached')
    r.sh('git switch -q main')
    r.cap('git update-ref refs/heads/topic HEAD')
    r.cap('git log --oneline --decorate --all', label='refs.updated')
    r.cap('git tag v1 HEAD~1')
    r.cap('git pack-refs --all')
    r.cap('cat .git/packed-refs')
    r.cap('ls .git/refs/heads .git/refs/tags', label='refs.packed')
    r.cap('git show-ref')
    r.cap('git reflog')
    r.cap("head -1 .git/logs/HEAD | sed 's/ /\\n/2; s/\\t/\\n/'")
    r.cap('git reflog expire --expire=now --all')
    r.cap('git reflog', label='refs.expired')
    # 이름 풀기의 차례: 태그 > 브랜치 (같은 이름이면 경고)
    r.sh('git branch v1 HEAD')
    r.cap('git rev-parse v1', label='refs.ambig')
    r.cap('git rev-parse refs/heads/v1 refs/tags/v1')
    r.cap('git check-ref-format --branch "a..b"', ok=(128,))
    r.cap('git check-ref-format --branch "feature/x"')
