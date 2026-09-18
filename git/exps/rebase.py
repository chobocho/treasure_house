# -*- coding: utf-8 -*-
"""rebase — 역사 다시 쓰기의 실체(8부).

rebase 는 커밋을 하나씩 새 바탕 위에 다시 만든다(cherry-pick 의
되풀이). 그래서 이름이 전부 바뀐다. -i 의 할 일 목록은
GIT_SEQUENCE_EDITOR 로 스크립트가 고친다 — 사람이 편집기를 여는
대신이다.
"""
from exps.util import commit, tick


def feature(ctx, name):
    r = ctx.repo(name)
    commit(r, 0, 'base', {'f': 'base\n'})
    r.sh('git switch -q -c feature')
    commit(r, 1, 'F1', {'a': '1\n'})
    commit(r, 2, 'F2', {'b': '2\n'})
    commit(r, 3, 'F3', {'c': '3\n'})
    r.sh('git switch -q main')
    commit(r, 4, 'M1', {'m': 'm\n'})
    r.sh('git switch -q feature')
    tick(r, 5)
    return r


def run(ctx):
    r = feature(ctx, 'rebase_basic')
    r.cap('git log --oneline --graph --all')
    r.cap('git rebase main')
    r.cap('git log --oneline --graph --all', label='rebase_basic.after')
    r.cap('git reflog -6')
    r.cap('git log --oneline ORIG_HEAD')
    # -i : 할 일 목록을 스크립트로 고친다(F2 를 F1 에 합치기)
    r = feature(ctx, 'rebase_i')
    r.cap('GIT_SEQUENCE_EDITOR=cat git rebase -i main')
    r.sh('git reset -q --hard ORIG_HEAD')
    r.cap("GIT_SEQUENCE_EDITOR=\"sed -i '2s/^pick/squash/'\" "
          "git rebase -i main")
    r.cap('git log --oneline --graph --all')
    r.cap('git log -1 --format=%B HEAD~1')
    # --autosquash : fixup! 커밋을 제자리로
    r = feature(ctx, 'rebase_autosquash')
    tick(r, 6)
    r.write('a', '1 fixed\n')
    r.sh('git add a')
    r.cap('git commit -q --fixup HEAD~2 && git log --oneline -4')
    tick(r, 7)
    r.cap('GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash main')
    r.cap('git log --oneline --graph --all')
    # --onto : 가지의 일부만 옮기기
    r = feature(ctx, 'rebase_onto')
    r.cap('git rebase --onto main feature~2 feature')
    r.cap('git log --oneline --graph --all')
    # --update-refs : 쌓인 가지들의 참조를 함께 옮긴다
    r = feature(ctx, 'rebase_update_refs')
    r.sh('git branch part1 feature~2 && git branch part2 feature~1')
    r.cap('git log --oneline --graph --all')
    r.cap('git rebase --update-refs main')
    r.cap('git log --oneline --graph --all',
          label='rebase_update_refs.after')
    # cherry-pick 과 충돌
    r = ctx.repo('cherry_pick')
    commit(r, 0, 'base', {'f': 'one\n'})
    r.sh('git switch -q -c topic')
    commit(r, 1, 'T1', {'f': 'topic\n'})
    commit(r, 2, 'T2', {'g': 'g\n'})
    r.sh('git switch -q main')
    commit(r, 3, 'M1', {'f': 'main\n'})
    tick(r, 4)
    r.cap('git cherry-pick topic')
    r.cap('git cherry-pick topic~1', ok=(1,))
    r.cap('git status --short')
    r.sh("printf 'main+topic\\n' > f && git add f")
    r.cap('git cherry-pick --continue --no-edit')
    r.cap('git log --oneline')
    r.cap('git log -1 --format=%B HEAD~1')
    # 머지의 revert — 어느 부모 쪽을 남길지 -m 으로 고른다
    r = ctx.repo('revert_merge')
    commit(r, 0, 'base', {'f': 'base\n'})
    r.sh('git switch -q -c topic')
    commit(r, 1, 'T', {'t': 't\n'})
    r.sh('git switch -q main')
    commit(r, 2, 'M', {'m': 'm\n'})
    tick(r, 3)
    r.sh('git merge -q --no-edit topic')
    tick(r, 4)
    r.cap('git revert --no-edit HEAD', ok=(128,))
    r.cap('git revert --no-edit -m 1 HEAD')
    r.cap('git log --oneline --graph')
    r.cap('ls')
    # amend — 마지막 커밋을 새로 만든다(이름이 바뀐다)
    r = ctx.repo('amend')
    commit(r, 0, 'fist commit', {'f': 'x\n'})
    r.cap('git log --oneline')
    tick(r, 1)
    r.cap('git commit --amend -q -m "first commit" && '
          'git log --oneline')
    r.cap('git reflog')
