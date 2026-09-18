# -*- coding: utf-8 -*-
"""rebase2 — 리베이스와 역사 재작성(8부)의 나머지.

  · 리베이스 중 충돌 — REBASE_HEAD, --continue · --skip · --abort.
  · rebase -i 의 명령 — reword · drop · 순서 바꾸기 · exec, 그리고 -x.
  · --rebase-merges 의 할 일 목록(label · reset · merge).
  · 이미 들어간 변경은 건너뛴다(patch-id 가 같은 커밋).
  · 리베이스는 author 시각을 두고 committer 시각만 새로 적는다.
  · range-diff — 리베이스 전후의 커밋 묶음을 짝지어 견준다.
  · cherry-pick -x 와 범위, revert.
  · 머지를 revert 한 뒤 다시 머지하면 — 되돌린 것을 되돌려야 한다.
  · filter-branch — 역사 전체에서 파일 하나 지우기(그리고 그 경고).
"""
from exps.util import commit, tick


def feature(ctx, name, conflict=False):
    """base → main(M1) · feature(F1 F2 F3). conflict 면 F2 가 M1 과
    같은 줄을 고친다."""
    r = ctx.repo(name)
    commit(r, 0, 'base', {'f': 'base\n', 'm': 'm0\n'})
    r.sh('git switch -q -c feature')
    commit(r, 1, 'F1', {'a': 'a\n'})
    commit(r, 2, 'F2', {'m': 'feature\n' if conflict else 'm0\n',
                        'b': 'b\n'})
    commit(r, 3, 'F3', {'c': 'c\n'})
    r.sh('git switch -q main')
    commit(r, 4, 'M1', {'m': 'main\n'})
    r.sh('git switch -q feature')
    tick(r, 5)
    return r


def conflicts(ctx):
    r = feature(ctx, 'rb_conflict', conflict=True)
    r.cap('git rebase main 2>&1', ok=None)
    r.cap('git status | head -8')
    r.cap('git log --oneline -1 REBASE_HEAD')
    r.cap('ls .git/rebase-merge | head -20')
    r.cap('cat .git/rebase-merge/done .git/rebase-merge/git-rebase-todo')
    r.sh("printf 'main+feature\\n' > m && git add m")
    r.cap('GIT_EDITOR=true git rebase --continue 2>&1')
    r.cap('git log --oneline --graph')
    # --skip 과 --abort
    r = feature(ctx, 'rb_skip', conflict=True)
    r.sh('git rebase main >/dev/null 2>&1 || true')
    r.cap('git rebase --skip 2>&1 && git log --oneline', ok=None)
    r = feature(ctx, 'rb_abort', conflict=True)
    r.sh('git rebase main >/dev/null 2>&1 || true')
    r.cap('git rebase --abort && git log --oneline --graph --all')


# reword: 할 일 목록의 첫 pick 을 reword 로, 메시지 편집기는 F1 을 고친다
SEQ = "sed -i '1s/^pick/reword/' \"$1\"\n"
MSG = "sed -i '1s/F1/F1: add a/' \"$1\"\n"
REWORD = """GIT_SEQUENCE_EDITOR="sh ../rb-tools/seq.sh" \\
GIT_EDITOR="sh ../rb-tools/msg.sh" git rebase -q -i main
"""
# filter-branch 한 줄은 길어 스크립트로
# 경고 뒤 10초를 기다리므로 파이프로 자르지 않고 끝까지 돌린 뒤 로그를 본다
RMSECRET = """git filter-branch \\
  --index-filter 'git rm -q --cached --ignore-unmatch secret.env' \\
  HEAD > ../fb.log 2>&1
head -4 ../fb.log; echo ...; tail -1 ../fb.log
"""
REORDER = """import sys
# 할 일 목록 편집기 대신: F3 를 맨 앞으로, F2 는 drop 으로
p = sys.argv[1]
f1, f2, f3 = [l for l in open(p) if l.startswith("pick")]
open(p, "w").write(f3 + f1 + f2.replace("pick", "drop", 1))
"""


def todo_cmds(ctx):
    r = feature(ctx, 'rb_todo')
    r.write('../rb-tools/reorder.py', REORDER)
    r.cap('cat ../rb-tools/reorder.py')
    r.cap('GIT_SEQUENCE_EDITOR="python3 ../rb-tools/reorder.py" '
          'git rebase -i main 2>&1 | tail -1', label='rb_todo.edit')
    r.cap('git log --oneline', label='rb_todo.edit')
    r = feature(ctx, 'rb_reword')
    r.write('../rb-tools/seq.sh', SEQ)
    r.write('../rb-tools/msg.sh', MSG)
    r.write('../rb-tools/reword.sh', REWORD)
    r.cap('cat ../rb-tools/seq.sh ../rb-tools/msg.sh '
          '../rb-tools/reword.sh')
    r.cap('sh ../rb-tools/reword.sh | head -1 && git log --oneline')
    r = feature(ctx, 'rb_exec')
    # 작은따옴표 — $(…) 가 바깥 셸이 아니라 커밋마다 exec 에서 펼쳐지게
    r.cap("git rebase -x 'git log -1 --format=\"exec 에서 본 HEAD: %s\"' "
          "main 2>&1")
    r.cap("GIT_SEQUENCE_EDITOR=cat git rebase -i -x true main "
          "2>/dev/null | grep -v '^#' | grep .", label='rb_exec.todo')


def merges(ctx):
    r = ctx.repo('rb_merges')
    commit(r, 0, 'base', {'f': 'base\n'})
    r.sh('git switch -q -c feature')
    commit(r, 1, 'F1', {'a': 'a\n'})
    r.sh('git switch -q -c sub')
    commit(r, 2, 'S1', {'s': 's\n'})
    r.sh('git switch -q feature')
    tick(r, 3)
    r.sh('git merge -q --no-ff --no-edit sub')
    commit(r, 4, 'F2', {'b': 'b\n'})
    r.sh('git switch -q main')
    commit(r, 5, 'M1', {'m': 'm\n'})
    r.sh('git switch -q feature')
    tick(r, 6)
    r.cap('git log --oneline --graph main feature')
    r.cap("GIT_SEQUENCE_EDITOR=cat git rebase -i --rebase-merges main "
          "2>/dev/null | grep -v '^#' | grep .")
    r.cap('git log --oneline --graph')
    r.sh('git reset -q --hard ORIG_HEAD')
    r.cap('git rebase -q main && git log --oneline --graph',
          label='rb_merges.flat')


def applied(ctx):
    """main 이 feature 의 F2 를 이미 cherry-pick 해 두었다면."""
    r = feature(ctx, 'rb_applied')
    r.sh('git switch -q main')
    tick(r, 6)
    r.sh('git cherry-pick feature~1 >/dev/null')
    r.sh('git switch -q feature')
    tick(r, 7)
    r.cap('git cherry -v main')
    r.cap('git rebase main 2>&1')
    r.cap('git log --oneline')


def dates(ctx):
    r = feature(ctx, 'rb_dates')
    fmt = 'git log --format="%h %s  author %at  committer %ct" -3'
    r.cap(fmt, label='rb_dates.before')
    tick(r, 30)
    r.sh('git rebase -q main')
    r.cap(fmt, label='rb_dates.after')
    r.cap('git range-diff ORIG_HEAD~3..ORIG_HEAD main..feature')


def picking(ctx):
    r = feature(ctx, 'rb_pick')
    r.sh('git switch -q main')
    tick(r, 6)
    r.cap('git cherry-pick -x feature~2 >/dev/null && '
          'git log -1 --format=%B')
    r.cap('git cherry-pick feature~1..feature 2>&1 | grep "^\\["')
    r.cap('git log --oneline')
    tick(r, 8)
    r.cap('git revert --no-edit HEAD 2>&1 | head -1 && '
          'git log --oneline -2 && ls')


def remerge(ctx):
    """머지를 revert 한 뒤 고쳐서 다시 머지하려 하면."""
    r = ctx.repo('rb_remerge')
    commit(r, 0, 'base', {'f': 'base\n'})
    r.sh('git switch -q -c topic')
    commit(r, 1, 'T1', {'t1': 't1\n'})
    r.sh('git switch -q main')
    tick(r, 2)
    r.sh('git merge -q --no-ff --no-edit topic')
    tick(r, 3)
    r.sh('git revert --no-edit -m 1 HEAD >/dev/null')
    r.sh('git switch -q topic')
    commit(r, 4, 'T2 fix', {'t2': 't2\n'})
    r.sh('git switch -q main')
    tick(r, 5)
    r.cap('git merge -q --no-edit topic && ls')
    r.cap('git log --oneline --graph')
    tick(r, 6)
    r.cap('git revert --no-edit HEAD~1 >/dev/null && ls',
          label='rb_remerge.fixed')


def filtering(ctx):
    r = ctx.repo('rb_filter')
    commit(r, 0, 'base', {'app.py': 'x\n'})
    commit(r, 1, 'oops', {'secret.env': 'KEY=dummy\n'})
    commit(r, 2, 'more', {'app.py': 'y\n'})
    r.cap('git log --oneline --stat | grep -v changed')
    r.write('../rb-tools/rmsecret.sh', RMSECRET)
    r.cap('cat ../rb-tools/rmsecret.sh')
    r.cap('sh ../rb-tools/rmsecret.sh')
    r.cap('git log --oneline --stat | grep -v changed',
          label='rb_filter.after')
    r.cap('git for-each-ref refs/original')
    r.cap('git filter-repo --help >/dev/null 2>&1; echo "exit $?"')


def run(ctx):
    conflicts(ctx)
    todo_cmds(ctx)
    merges(ctx)
    applied(ctx)
    dates(ctx)
    picking(ctx)
    remerge(ctx)
    filtering(ctx)
