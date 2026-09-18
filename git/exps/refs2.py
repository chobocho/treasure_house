# -*- coding: utf-8 -*-
"""refs2 — 참조(4부)의 나머지.

  · 조상 표기: 머지 커밋에서 ^1 · ^2 · ~2 가 가리키는 곳.
  · @{-1}(바로 전 브랜치), @{u}(upstream), 원격 추적 참조.
  · 특수 참조 — ORIG_HEAD · FETCH_HEAD, 태어나지 않은 브랜치.
  · 이름 규칙 — check-ref-format 이 거절하는 꼴들.
  · 잠금 — .lock 파일이 있으면 갱신이 멈춘다. 옛 값을 맞춰야
    바꾸는(update-ref 의 셋째 인자) 비교 후 교체, --stdin 트랜잭션.
  · reftable — 참조를 파일 대신 표 하나에. files 에서 옮기기.
  · for-each-ref 로 참조를 골라 보기.
"""
from exps.util import commit, tick


def ancestry(ctx):
    r = ctx.repo('ancestry')
    commit(r, 0, 'A', {'f': 'A\n'})
    commit(r, 1, 'B', {'f': 'B\n'})
    r.sh('git switch -q -c side HEAD~1')
    commit(r, 2, 'C', {'g': 'C\n'})
    commit(r, 3, 'D', {'g': 'D\n'})
    r.sh('git switch -q main')
    tick(r, 4)
    r.sh('git merge -q --no-edit side')
    commit(r, 5, 'E', {'f': 'E\n'})
    r.cap('git log --graph --oneline')
    fmt = ('for x in HEAD HEAD~1 HEAD^ HEAD~1^1 HEAD~1^2 HEAD~2 '
           'HEAD~1^2~1; do git log -1 --format="$x = %s" $x; done')
    r.cap(fmt)
    r.cap('git rev-parse HEAD~1^@ | cut -c1-7')
    r.cap('git log --oneline HEAD~1^!')


def moving(ctx):
    """@{-1}, upstream, 원격 추적 참조, 특수 참조."""
    src = ctx.repo('up_origin')
    commit(src, 0, 'one', {'f': '1\n'})
    commit(src, 1, 'two', {'f': '2\n'})
    r = ctx.repo('upstream', init=False)
    r.sh('git clone -q ../up_origin .')
    r.sh('git switch -q -c work')
    r.sh('git switch -q main')
    r.cap('git rev-parse --abbrev-ref @{-1}')
    r.cap('git switch - 2>&1 && git switch - 2>&1')
    r.cap('git rev-parse --abbrev-ref main@{u}')
    r.cap('git rev-parse --symbolic-full-name @{u}')
    r.cap('git for-each-ref --format="%(refname)" refs/remotes')
    r.cap('cat .git/refs/remotes/origin/HEAD')
    r.cap('git rev-parse --abbrev-ref origin')
    # 원격이 앞서 나간 뒤 받아 오면
    commit(src, 2, 'three', {'f': '3\n'})
    r.cap('git fetch -q && cat .git/FETCH_HEAD')
    r.cap('git status -sb')
    r.cap('git log --oneline main..@{u}')
    # ORIG_HEAD — 위험한 이동 앞에 git 이 남겨 두는 표시
    tick(r, 3)
    r.cap('git reset -q --hard HEAD~1 && cat .git/ORIG_HEAD')
    r.cap('git log --oneline -1 ORIG_HEAD')
    # 태어나지 않은 브랜치
    r.cap('git switch -q --orphan fresh && cat .git/HEAD')
    r.cap('git rev-parse --verify -q HEAD; echo "exit $?"')
    r.cap('git log 2>&1', ok=None)


NAMES = ['feature/x', 'a..b', 'a b', 'x.lock', '.hidden',
         'end/', 'a~1', 'a^b', 'a:b', 'wip?', 'a@{b', '@', '-dash',
         'HEAD', '한글']


CHECK = """while read -r n; do
  if git check-ref-format --branch "$n" >/dev/null 2>&1
  then echo "ok  $n"; else echo "no  $n"; fi
done < names.txt
"""


def names(ctx):
    r = ctx.repo('refnames')
    r.write('names.txt', ''.join(n + '\n' for n in NAMES))
    r.write('check.sh', CHECK)
    r.cap('cat check.sh')
    r.cap('sh check.sh')


def locking(ctx):
    r = ctx.repo('reflock')
    commit(r, 0, 'A', {'f': 'A\n'})
    commit(r, 1, 'B', {'f': 'B\n'})
    old = r.sh('git rev-parse HEAD~1').strip()
    # 다른 git 이 참조를 바꾸는 중인 척 — 잠금 파일을 먼저 만든다
    r.sh('touch .git/refs/heads/main.lock')
    tick(r, 2)
    r.write('f', 'C\n')
    r.cap('git commit -qam C 2>&1', ok=None, label='reflock.locked')
    r.sh('rm .git/refs/heads/main.lock')
    # 옛 값이 맞아야만 바꾼다
    r.cap('git update-ref refs/heads/main HEAD~1 %s 2>&1 | fold -w 100'
          % old[:7], ok=None, label='reflock.cas')
    r.cap('git update-ref refs/heads/main HEAD~1 HEAD && '
          'git log --oneline -1')
    # 여러 참조를 한꺼번에 — 하나라도 실패하면 아무것도 안 바뀐다
    r.write('tx.txt', 'create refs/heads/x HEAD\n'
                      'create refs/heads/main HEAD\n')
    r.cap('cat tx.txt')
    r.cap('git update-ref --stdin < tx.txt 2>&1; git branch --list',
          ok=None, label='reflock.tx')
    r.cap('git update-ref -d refs/heads/x 2>&1; git branch --list',
          ok=None, label='reflock.del')


def reftable(ctx):
    r = ctx.repo('reftab', init=False)
    r.cap('git init -q --ref-format=reftable -b main && '
          'git rev-parse --show-ref-format')
    commit(r, 0, 'A', {'f': 'A\n'})
    r.sh('git tag v1 && git branch topic')
    r.cap('ls .git .git/reftable | sed "s/[0-9a-f]\\{8\\}\\.ref/'
          '<조각>.ref/"')
    r.cap('cat .git/HEAD; cat .git/refs/heads')
    r.cap('git for-each-ref')
    r.cap('git refs verify; echo "exit $?"')
    # files 저장소를 reftable 로 옮기기
    m = ctx.repo('refmigrate')
    commit(m, 0, 'A', {'f': 'A\n'})
    m.sh('git branch topic && git tag v1')
    m.cap('git rev-parse --show-ref-format')
    m.cap('git refs migrate --ref-format=reftable && '
          'git rev-parse --show-ref-format')
    m.cap('git for-each-ref --format="%(refname)"')


def listing(ctx):
    r = ctx.repo('refsort')
    commit(r, 0, 'A', {'f': 'A\n'})
    r.sh('git branch old')
    commit(r, 1, 'B', {'f': 'B\n'})
    r.sh('git branch mid')
    commit(r, 2, 'C', {'f': 'C\n'})
    r.sh('git tag -a v1 -m v1 mid')
    r.cap('git for-each-ref --sort=-committerdate '
          '--format="%(refname:short) %(subject)" refs/heads')
    r.cap('git for-each-ref --format="%(refname:short) %(objecttype) '
          '%(*objecttype)" refs/tags')
    r.cap('git branch --contains mid')
    r.cap('git branch --merged old')
    r.cap('git branch -v --no-merged old')
    r.cap('git reflog show mid')
    r.cap('git branch -D -q old && ls .git/logs/refs/heads')


def run(ctx):
    ancestry(ctx)
    moving(ctx)
    names(ctx)
    locking(ctx)
    reftable(ctx)
    listing(ctx)
