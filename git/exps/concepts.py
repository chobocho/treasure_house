# -*- coding: utf-8 -*-
"""concepts — 개념 지도(2부)의 캡처.

  · 스냅숏: 파일 셋 중 하나만 바꿔 커밋하면 새 blob 은 하나뿐이고,
    나머지 둘은 앞 커밋과 같은 이름을 그대로 가리킨다.
  · 내용 주소: 같은 내용이면 파일 이름이 달라도 blob 은 하나다.
    한 글자만 달라도 이름은 전혀 다르다.
  · 불변: amend 는 커밋을 고치지 않고 새로 만든다 — 옛 것은 남는다.
  · 분산: clone 은 역사 전부를 가진 온전한 저장소다.
  · plumbing: porcelain(add·commit) 없이 객체·인덱스·참조를 한 겹씩
    손으로 쌓아 커밋 하나를 만든다.
"""
from exps.util import commit, tick

# 개수만 — 뒤의 킬로바이트는 파일시스템 블록 크기라 기계마다 다르다
COUNT = 'git count-objects | cut -d, -f1'


def snapshot(ctx):
    r = ctx.repo('snap')
    commit(r, 0, 'three files', {'a.txt': 'alpha\n', 'b.txt': 'beta\n',
                                 'c.txt': 'gamma\n'})
    r.cap(COUNT, label='snap.1')
    commit(r, 1, 'change b', {'b.txt': 'beta 2\n'})
    r.cap(COUNT, label='snap.2')
    r.cap('git ls-tree HEAD~1')
    r.cap('git ls-tree HEAD')
    r.cap('git cat-file -p HEAD')
    r.cap('git diff --stat HEAD~1 HEAD')
    # 이름만 바꾸면 — blob 은 그대로, 트리만 새로
    tick(r, 2)
    r.sh('git mv c.txt see.txt && git commit -q -m rename')
    r.cap('git ls-tree HEAD', label='snap.renamed')
    r.cap(COUNT, label='snap.3')
    # 같은 내용 두 벌
    r.write('twin.txt', 'alpha\n')
    r.sh('git add twin.txt')
    r.cap('git ls-files --stage a.txt twin.txt')
    r.cap("printf 'alpha\\n' | git hash-object --stdin")
    r.cap("printf 'alphb\\n' | git hash-object --stdin")
    return r


def immutable(ctx):
    r = ctx.repo('immut')
    commit(r, 0, 'first', {'f.txt': 'x\n'})
    commit(r, 1, 'typo', {'g.txt': 'y\n'})
    r.cap('git log --oneline')
    old = r.sh('git rev-parse HEAD').strip()
    tick(r, 2)
    r.cap('git commit -q --amend -m "fixed message" && '
          'git log --oneline')
    r.cap('git cat-file -t %s' % old[:7])
    r.cap('git log --oneline -1 %s' % old[:7])
    r.cap('git reflog -3')


def distributed(ctx):
    src = ctx.repo('dist_origin')
    commit(src, 0, 'one', {'f.txt': '1\n'})
    commit(src, 1, 'two', {'f.txt': '2\n'})
    r = ctx.repo('dist', init=False)
    r.cap('git clone -q ../dist_origin . && git log --oneline')
    r.cap('git count-objects -v | grep -E "^(count|in-pack|packs):"')
    r.cap('git remote -v')
    r.cap('git branch -a')
    # 원본을 지워도 복제본은 제 역사를 다 가진다
    r.sh('rm -rf ../dist_origin')
    commit(r, 2, 'offline', {'f.txt': '3\n'})
    r.cap('git log --oneline', label='dist.after')
    r.cap('git status -sb')
    r.cap('git fsck --strict; echo "exit $?"')


def plumbing(ctx):
    r = ctx.repo('plumb')
    tick(r, 0)
    blob = r.cap("printf 'hi\\n' | git hash-object -w --stdin").strip()
    r.cap('git update-index --add --cacheinfo 100644,%s,hi.txt' % blob)
    r.cap('git ls-files --stage')
    tree = r.cap('git write-tree').strip()
    r.cap('git cat-file -p %s' % tree)
    c = r.cap("echo 'made by plumbing' | git commit-tree %s" % tree).strip()
    r.cap('git update-ref refs/heads/main %s' % c)
    r.cap('git log --oneline')
    # 작업 트리에는 hi.txt 가 없다 — 커밋은 작업 트리를 거치지 않았다
    r.cap('git status --short')
    # 한 줄이 119칸이라 필드마다 줄을 나눠 싣는다(명령에 그대로 보인다)
    r.cap("git status --porcelain=v2 | tr ' ' '\\n'")
    r.cap('git checkout -- hi.txt && cat hi.txt')


def run(ctx):
    snapshot(ctx)
    immutable(ctx)
    distributed(ctx)
    plumbing(ctx)
