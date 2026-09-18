# -*- coding: utf-8 -*-
"""cmds — 명령 해부(6부): 명령 하나가 세 영역을 어떻게 바꾸나.

state.py 가 경로마다 HEAD · 인덱스 · 작업 트리의 blob 이름(앞 7자리)을
한 줄에 찍는다. 명령마다 "전 → 명령 → 후" 를 찍으면 그 명령이 어느
칸을 바꾸는지가 표로 보인다. 모든 실험은 같은 출발점(파일 셋, 커밋
둘)에서 새로 시작한다 — 앞 명령의 흔적이 섞이지 않게.
"""
from exps.util import commit, tick

STATE = r'''import os, subprocess
# 경로마다 HEAD · 인덱스 · 작업 트리의 blob 이름(앞 7자리), 없으면 -
def run(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout
head, idx, wt = {}, {}, {}
for line in run("git", "ls-tree", "-r", "HEAD").splitlines():
    meta, path = line.split("\t")
    head[path] = meta.split()[2][:7]
for line in run("git", "ls-files", "-s").splitlines():
    meta, path = line.split("\t")
    stage = meta.split()[2]
    idx[path] = meta.split()[1][:7] + ("" if stage == "0" else ":" + stage)
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d != ".git"]
    for f in files:
        path = os.path.relpath(os.path.join(root, f), ".")
        wt[path] = run("git", "hash-object", path).strip()[:7]
print("%-10s %-9s %-9s %s" % ("path", "HEAD", "index", "worktree"))
for p in sorted(set(head) | set(idx) | set(wt)):
    print("%-10s %-9s %-9s %s" % (p, head.get(p, "-"), idx.get(p, "-"),
                                  wt.get(p, "-")))
'''
ST = 'python3 ../cmds-tools/state.py'


def start(ctx, name):
    """출발점: a·b·c 셋, 커밋 둘(두 번째에서 b 를 고침)."""
    r = ctx.repo(name)
    r.write('../cmds-tools/state.py', STATE)
    commit(r, 0, 'first', {'a': 'a1\n', 'b': 'b1\n', 'c': 'c1\n'})
    commit(r, 1, 'second', {'b': 'b2\n'})
    # 인덱스의 racy 항목을 없앤다(5부) — 캡처가 흔들리지 않게
    r.sh('touch -d @1700000000 a b c && git update-index --refresh')
    tick(r, 2)
    return r


def step(r, cmd, label, pre=None):
    """전 상태 → 명령 → 후 상태를 label.before/label.after 로."""
    if pre:
        r.sh(pre)
    r.cap(ST, label=label + '.before')
    r.cap(cmd, label=label, ok=None)
    r.cap(ST, label=label + '.after')


def basics(ctx):
    r = start(ctx, 'cmd_add')
    r.cap('cat ../cmds-tools/state.py')
    step(r, 'git add a', 'cmd_add', pre="printf 'a2\\n' > a")
    r = start(ctx, 'cmd_addnew')
    step(r, 'git add d', 'cmd_addnew', pre="printf 'd1\\n' > d")
    r = start(ctx, 'cmd_commit')
    step(r, 'git commit -q -m third && git log --oneline -1',
         'cmd_commit', pre="printf 'a2\\n' > a && git add a")
    r = start(ctx, 'cmd_commita')
    step(r, 'git commit -q -a -m third', 'cmd_commita',
         pre="printf 'a2\\n' > a && printf 'd1\\n' > d")
    r = start(ctx, 'cmd_rm')
    step(r, 'git rm -q a', 'cmd_rm')
    r = start(ctx, 'cmd_rmcached')
    step(r, 'git rm -q --cached a', 'cmd_rmcached')
    r = start(ctx, 'cmd_rmdirty')
    step(r, 'git rm a 2>&1', 'cmd_rmdirty', pre="printf 'a2\\n' > a")
    r = start(ctx, 'cmd_mv')
    step(r, 'git mv a z && git status --short', 'cmd_mv')


def restore(ctx):
    pre = "printf 'a2\\n' > a && git add a && printf 'a3\\n' > a"
    r = start(ctx, 'cmd_restore')
    step(r, 'git restore a', 'cmd_restore', pre=pre)
    r = start(ctx, 'cmd_restores')
    step(r, 'git restore --staged a', 'cmd_restores', pre=pre)
    r = start(ctx, 'cmd_restoresw')
    step(r, 'git restore --staged --worktree a', 'cmd_restoresw', pre=pre)
    r = start(ctx, 'cmd_restoresrc')
    step(r, 'git restore --source=HEAD~1 b', 'cmd_restoresrc')


def reset(ctx):
    pre = "printf 'a2\\n' > a && git add a && printf 'c2\\n' > c"
    for mode in ('soft', 'mixed', 'hard'):
        r = start(ctx, 'cmd_reset_' + mode)
        step(r, 'git reset -q --%s HEAD~1 && git log --oneline' % mode,
             'cmd_reset_' + mode, pre=pre)
    r = start(ctx, 'cmd_resetpath')
    step(r, 'git reset -q HEAD~1 -- b', 'cmd_resetpath')


def switching(ctx):
    r = start(ctx, 'cmd_switch')
    r.sh('git branch old HEAD~1')
    # 로컬 변경은 따라간다 — 두 브랜치에서 같은 파일이면
    step(r, 'git switch old 2>&1', 'cmd_switch', pre="printf 'a2\\n' > a")
    r = start(ctx, 'cmd_switchblock')
    r.sh('git branch old HEAD~1')
    # 두 브랜치에서 다른 파일(b)을 고쳐 두었으면 거절한다
    step(r, 'git switch old 2>&1', 'cmd_switchblock',
         pre="printf 'b3\\n' > b")
    r = start(ctx, 'cmd_checkoutfile')
    step(r, 'git checkout HEAD~1 -- b', 'cmd_checkoutfile')


def stash(ctx):
    r = start(ctx, 'cmd_stash')
    pre = ("printf 'a2\\n' > a && git add a && printf 'c2\\n' > c && "
           "printf 'n\\n' > new")
    step(r, 'git stash push -q && git stash list', 'cmd_stash', pre=pre)
    r.cap('git log --graph --oneline stash@{0}')
    r.cap('git cat-file -p stash@{0}')
    r.cap('git stash show -p stash@{0}')
    step(r, 'git stash pop --index 2>&1 | head -3', 'cmd_pop')
    r = start(ctx, 'cmd_stashu')
    step(r, 'git stash push -q -u && git stash list', 'cmd_stashu',
         pre="printf 'n\\n' > new")
    r.cap('git cat-file -p stash@{0} | grep ^parent')
    r.cap('git ls-tree stash@{0}^3')


def cleaning(ctx):
    r = start(ctx, 'cmd_clean')
    r.write('.gitignore', 'build/\n')
    r.sh('git add .gitignore && git commit -q -m ignore')
    r.write('junk.txt', 'j\n')
    r.write('build/out.o', 'o\n')
    r.cap('git clean -n')
    r.cap('git clean -n -d')
    r.cap('git clean -n -d -x')
    r.cap('git clean -f -d && ls -A')


def amend(ctx):
    r = start(ctx, 'cmd_amend')
    step(r, 'git commit -q --amend --no-edit && git log --oneline',
         'cmd_amend', pre="printf 'a2\\n' > a && git add a")
    r.cap('git reflog -2')


def viewing(ctx):
    r = start(ctx, 'cmd_view')
    r.cap('git log --oneline --stat')
    r.cap('git log -p -1')
    r.cap('git show --name-status HEAD')
    r.cap('git show HEAD~1:b')
    r.cap('git log --format="%h %an %ad %s" --date=short')
    r.sh("printf 'a2\\n' > a && git add a && printf 'a3\\n' > a")
    r.cap('git diff', label='cmd_view.dirty')
    r.cap('git diff --cached', label='cmd_view.dirty')
    r.cap('git diff HEAD', label='cmd_view.dirty')
    r.cap('git status', label='cmd_view.dirty')
    r.cap('git status --short --branch', label='cmd_view.dirty')


def run(ctx):
    basics(ctx)
    restore(ctx)
    reset(ctx)
    switching(ctx)
    stash(ctx)
    cleaning(ctx)
    amend(ctx)
    viewing(ctx)
