# -*- coding: utf-8 -*-
"""merge2 — 브랜치와 머지(7부)의 나머지.

  · -s ours 와 -X ours 는 다르다 — 충돌 없는 그쪽 변경을 버리느냐.
  · 충돌의 종류 — add/add, 바이너리, 수정/삭제.
  · 충돌 중에 쓰는 것 — MERGE_HEAD, diff --base/--ours/--theirs,
    checkout --ours/--theirs, log --merge, AUTO_MERGE.
  · --ff-only 의 거절, --no-commit.
  · merge-tree — 작업 트리를 건드리지 않는 머지.
  · merge-file — 파일 셋으로 하는 3-way.
  · 브랜치 다루기 — branch -d 의 거절, -m, --set-upstream-to.
"""
from exps.util import commit, tick

LINES = ''.join('line %d\n' % i for i in range(1, 9))


def fork(ctx, name, base, ours, theirs):
    """base → topic(theirs) · main(ours). 각 인자는 {경로: 내용}."""
    r = ctx.repo(name)
    commit(r, 0, 'base', base)
    r.sh('git switch -q -c topic')
    commit(r, 1, 'theirs', theirs)
    r.sh('git switch -q main')
    commit(r, 2, 'ours', ours)
    tick(r, 3)
    return r


def ours_vs_ours(ctx):
    # 그쪽은 4번과 8번 줄을, 우리는 4번 줄만 고쳤다
    theirs = LINES.replace('line 4', 'theirs 4').replace('line 8',
                                                         'theirs 8')
    ours = LINES.replace('line 4', 'ours 4')
    r = fork(ctx, 'merge_xours', {'f.txt': LINES}, {'f.txt': ours},
             {'f.txt': theirs})
    r.cap('git merge -q -X ours --no-edit topic && sed -n "4p;8p" f.txt')
    r = fork(ctx, 'merge_sours', {'f.txt': LINES}, {'f.txt': ours},
             {'f.txt': theirs})
    r.cap('git merge -q -s ours --no-edit topic && sed -n "4p;8p" f.txt')
    r.cap('git log --oneline --graph')


def kinds(ctx):
    r = fork(ctx, 'merge_addadd', {'base.txt': 'b\n'},
             {'new.txt': 'ours\n'}, {'new.txt': 'theirs\n'})
    r.cap('git merge topic 2>&1', ok=None)
    r.cap('git ls-files --stage --abbrev new.txt')
    r = fork(ctx, 'merge_binary', {'img.bin': 'P\x00\x01base'},
             {'img.bin': 'P\x00\x01ours'}, {'img.bin': 'P\x00\x01theirs'})
    r.cap('git merge topic 2>&1', ok=None)
    r.cap('git diff 2>&1 | head -4')
    r.cap('git checkout --theirs img.bin && od -c img.bin | head -1')
    r = fork(ctx, 'merge_moddel', {'f.txt': LINES, 'g.txt': 'g\n'},
             {'g.txt': 'g2\n'},
             {'f.txt': LINES.replace('line 2', 'LINE 2')})
    r.sh('git rm -q f.txt && git commit -q -m "delete f"')
    tick(r, 4)
    r.cap('git merge topic 2>&1 | fold -w 100', ok=None)
    r.cap('git status --short')


def during(ctx):
    theirs = LINES.replace('line 4', 'theirs 4')
    ours = LINES.replace('line 4', 'ours 4').replace('line 1', 'ours 1')
    r = fork(ctx, 'merge_during', {'f.txt': LINES}, {'f.txt': ours},
             {'f.txt': theirs})
    r.cap('git merge topic', ok=(1,))
    r.cap('cat .git/MERGE_HEAD && git rev-parse topic')
    r.cap('git log --oneline --merge')
    r.cap('git diff --base f.txt')
    r.cap('git diff --ours f.txt')
    r.cap('git diff --theirs f.txt')
    # AUTO_MERGE = git 이 충돌 표시까지 써 넣은 트리. 손으로 푼 뒤
    # 견주면 "내가 git 의 결과에서 무엇을 바꿨나" 가 보인다
    r.cap('git diff AUTO_MERGE -- f.txt', label='merge_during.raw')
    r.sh("sed -i '/^<<<<<<< /,/^>>>>>>> /c\\merged 4' f.txt")
    r.cap('git diff AUTO_MERGE -- f.txt')
    r.cap('git checkout -m f.txt && git status --short',
          label='merge_during.redo')
    r.cap('git checkout --ours f.txt && sed -n "1p;4p" f.txt')
    r.cap('git checkout -m f.txt && git status --short',
          label='merge_during.again')
    r.cap('git commit -q --no-edit 2>&1', ok=None)


def ff_policies(ctx):
    r = fork(ctx, 'merge_ffonly', {'f.txt': LINES},
             {'o.txt': 'o\n'}, {'t.txt': 't\n'})
    r.cap('git merge --ff-only topic 2>&1', ok=None)
    r.cap('git merge --no-commit --no-ff topic 2>&1 && '
          'git status --short && ls .git/MERGE_HEAD', ok=None)
    r.cap('git merge --abort && git log --oneline -1')


def tree_only(ctx):
    theirs = LINES.replace('line 4', 'theirs 4')
    ours = LINES.replace('line 4', 'ours 4')
    r = fork(ctx, 'merge_tree', {'f.txt': LINES, 'g.txt': 'g\n'},
             {'f.txt': ours}, {'f.txt': theirs, 'g.txt': 'g2\n'})
    r.cap('git merge-tree --write-tree main topic', ok=None)
    r.cap('git merge-tree --write-tree --name-only main topic', ok=None)
    r.cap('git status --short && git log --oneline -1')
    r2 = fork(ctx, 'merge_tree_ok', {'f.txt': LINES, 'g.txt': 'g\n'},
              {'f.txt': ours}, {'g.txt': 'g2\n'})
    t = r2.cap('git merge-tree --write-tree main topic').strip()
    r2.cap('git ls-tree %s' % t)


def merge_file(ctx):
    r = ctx.repo('merge_file')
    r.write('base.txt', LINES)
    r.write('ours.txt', LINES.replace('line 2', 'ours 2'))
    r.write('theirs.txt', LINES.replace('line 7', 'theirs 7'))
    r.cap('git merge-file -p ours.txt base.txt theirs.txt')
    r.write('clash.txt', LINES.replace('line 2', 'clash 2'))
    r.cap('git merge-file -p ours.txt base.txt clash.txt; '
          'echo "exit $?"', ok=None)


def branches(ctx):
    r = fork(ctx, 'branch_ops', {'f.txt': LINES},
             {'o.txt': 'o\n'}, {'t.txt': 't\n'})
    r.cap('git branch -d topic 2>&1', ok=None)
    r.cap('git branch -m topic feature && git branch --list')
    r.cap('git branch -v')
    r.sh('git init -q --bare ../branch_ops_remote && '
         'git remote add origin ../branch_ops_remote && '
         'git push -q origin main feature')
    r.cap('git branch --set-upstream-to=origin/feature feature && '
          'git branch -vv')
    r.cap('git config --get-regexp "^branch\\."')


def run(ctx):
    ours_vs_ours(ctx)
    kinds(ctx)
    during(ctx)
    ff_policies(ctx)
    tree_only(ctx)
    merge_file(ctx)
    branches(ctx)
