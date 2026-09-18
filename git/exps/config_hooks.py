# -*- coding: utf-8 -*-
"""config_hooks — 설정·속성·무시 규칙·훅·도구들(13부).

설정은 세 층(system·global·local)이 겹치고 뒤가 이긴다. 이 실험만
GIT_CONFIG_GLOBAL 을 scratch 의 파일로 바꿔 global 층을 보인다(다른
실험은 /dev/null). SSH 서명 키는 매번 새로 만들어 지문이 달라지므로
지문은 <지문> 으로 바꿔 적는다(캡션).
"""
import os
import re

from exps.util import commit, tick

HOOK_PRE = '''#!/bin/sh
# pre-commit: 스테이지된 내용에 TODO 가 있으면 커밋을 막는다
if git diff --cached | grep -q '^+.*TODO'; then
  echo "pre-commit: TODO 가 남아 있다" >&2
  exit 1
fi
'''
HOOK_MSG = '''#!/bin/sh
# commit-msg: 제목이 "type: " 으로 시작해야 한다
head -1 "$1" | grep -qE '^(feat|fix|docs): ' && exit 0
echo "commit-msg: 제목은 feat:/fix:/docs: 로 시작할 것" >&2
exit 1
'''
HOOK_PUSH = '''#!/bin/sh
# pre-push: 무엇을 어디로 보내는지 적기만 한다
while read local_ref local_oid remote_ref remote_oid; do
  echo "pre-push: $local_ref -> $1 $remote_ref" >&2
done
'''
CRED = '''#!/bin/sh
# 가짜 자격 증명 도우미 — 진짜 비밀은 없다
test "$1" = get || exit 0
echo username=demo
echo password=not-a-real-secret
'''


def run(ctx):
    r = ctx.repo('config')
    home = os.path.join(r.path, '..', 'config-home')
    os.makedirs(home, exist_ok=True)
    r.env['GIT_CONFIG_GLOBAL'] = os.path.join(home, 'gitconfig')
    r.cap('git config --global user.name "Global Name"')
    r.cap('git config user.name "Local Name"')
    r.cap('git config --show-origin --show-scope --get-all user.name')
    r.cap('git config user.name')
    r.cap('git -c user.name=Once config user.name')
    r.cap('cat .git/config')
    r.write('../config-home/work.inc',
            '[user]\n\temail = me@work.example\n')
    # 포함할 파일의 상대 경로는 포함하는 파일(global 설정)의 자리 기준
    r.cap('git config --global includeIf.gitdir:$PWD/.path work.inc')
    r.cap('git config --show-origin user.email')
    r.cap('git config --global alias.lg "log --oneline --graph"')
    commit(r, 0, 'base', {'f': 'x\n'})
    r.cap('git lg')
    # .gitattributes
    a = ctx.repo('attributes')
    a.write('.gitattributes', '*.txt text eol=crlf\n*.bin binary\n'
            '*.dat diff=hex\nkeep.cfg merge=ours\n'
            'secret-notes.md export-ignore\n')
    a.sh('git config diff.hex.textconv "od -An -tx1"')
    a.sh('git config merge.ours.driver true')
    commit(a, 0, 'base', {'a.txt': 'one\ntwo\n', 'b.bin': 'a\x00b',
                          'c.dat': 'AB', 'keep.cfg': 'mine\n',
                          'secret-notes.md': 'x\n'})
    a.cap('cat .gitattributes')
    a.cap('git config --get-regexp "^(diff|merge)\\."')
    a.cap('git ls-files --eol')
    # 작업 트리의 a.txt 는 git 이 아니라 이 스크립트가 LF 로 썼다 —
    # eol=crlf 는 git 이 꺼내 쓸 때(checkout) 적용되므로 다시 꺼내야 CRLF
    a.cap('rm a.txt && git checkout a.txt && git ls-files --eol a.txt')
    a.cap('od -c a.txt')
    a.cap('git cat-file -p HEAD:a.txt | od -c', label='attributes.blob')
    a.cap('git check-attr -a a.txt b.bin c.dat keep.cfg')
    a.write('c.dat', 'AC')
    a.cap('git diff c.dat')
    a.sh('git checkout -q c.dat')
    a.cap('git archive HEAD | tar t')
    a.sh('git switch -q -c other')
    commit(a, 1, 'theirs', {'keep.cfg': 'theirs\n'})
    a.sh('git switch -q main')
    commit(a, 2, 'ours', {'keep.cfg': 'ours\n'})
    tick(a, 3)
    a.cap('git merge --no-edit other && cat keep.cfg')
    # .gitignore 의 우선순위 — 가까운 파일과 부정(!)
    g = ctx.repo('ignore')
    g.write('.gitignore', '*.log\nbuild/\n')
    g.write('logs/.gitignore', '!keep.log\n')
    for p in ('a.log', 'logs/keep.log', 'logs/other.log', 'build/x.o',
              'src/main.c'):
        g.write(p, 'x\n')
    g.cap('cat .gitignore logs/.gitignore')
    g.cap('git status --short --untracked-files=all')
    g.cap('git check-ignore -v a.log logs/other.log build/x.o')
    g.cap('git check-ignore -v --non-matching logs/keep.log src/main.c',
          ok=(0, 1))
    g.cap('git status --short --ignored')
    # 훅
    h = ctx.repo('hooks')
    h.write('.git/hooks/pre-commit', HOOK_PRE, 0o755)
    h.write('.git/hooks/commit-msg', HOOK_MSG, 0o755)
    h.write('.git/hooks/pre-push', HOOK_PUSH, 0o755)
    h.cap('cat .git/hooks/pre-commit .git/hooks/commit-msg')
    h.write('a.txt', 'TODO: later\n')
    h.sh('git add a.txt')
    h.cap('git commit -m "feat: add a"', ok=(1,))
    h.write('a.txt', 'done\n')
    h.sh('git add a.txt')
    h.cap('git commit -m "add a"', ok=(1,), label='hooks.msg')
    h.cap('git commit -q -m "feat: add a" && git log --oneline',
          label='hooks.ok')
    h.cap('git commit --no-verify --allow-empty -q -m "no hooks" && '
          'git log --oneline', label='hooks.noverify')
    # 저장소 밖의 원격은 앞 실행이 남긴 것을 먼저 치운다 — 남아 있으면
    # push 할 것이 없어 pre-push 훅이 아예 돌지 않는다(깨끗한 실행과 달라짐)
    h.sh('rm -rf ../hooks-remote.git && git init -q --bare ../hooks-remote.git')
    h.cap('git push -q ../hooks-remote.git main')
    # worktree — 한 저장소, 작업 트리 둘
    w = ctx.repo('worktree')
    commit(w, 0, 'base', {'f': 'x\n'})
    w.cap('git worktree add -q ../worktree-hotfix -b hotfix')
    w.cap('git worktree list')
    w.cap('cat ../worktree-hotfix/.git')
    w.cap('git branch')
    w.cap('git worktree remove ../worktree-hotfix')
    # submodule 과 subtree
    lib = ctx.repo('sub_lib')
    commit(lib, 0, 'lib v1', {'lib.c': 'int lib;\n'})
    s = ctx.repo('sub_app')
    commit(s, 0, 'app', {'app.c': 'int app;\n'})
    s.env['GIT_CONFIG_PARAMETERS'] = "'protocol.file.allow=always'"
    s.cap('git submodule add -q ../sub_lib lib')
    s.cap('cat .gitmodules')
    s.cap('git ls-files --stage lib')
    tick(s, 1)
    s.sh('git commit -q -m "add lib"')
    s.cap('git submodule status')
    t = ctx.repo('subtree_app')
    commit(t, 0, 'app', {'app.c': 'int app;\n'})
    tick(t, 1)
    t.cap('git subtree add -q --prefix=vendor/lib ../sub_lib main')
    t.cap('git log --oneline --graph')
    t.cap('git ls-files')
    # credential — 도우미가 채운 값을 git credential fill 로 본다
    c = ctx.repo('credential')
    c.write('../credential-helper.sh', CRED, 0o755)
    c.sh('git config credential.helper "$PWD/../credential-helper.sh"')
    c.cap("printf 'protocol=https\\nhost=example.com\\n\\n' "
          "| git credential fill")
    # SSH 서명 — 버리는 키를 만들어 서명하고 확인한다
    k = ctx.repo('signing')
    k.sh('rm -f ../signing-key ../signing-key.pub && '
         'ssh-keygen -q -t ed25519 -N "" -C demo -f ../signing-key')
    k.sh('git config gpg.format ssh && '
         'git config user.signingkey "$PWD/../signing-key.pub"')
    k.sh('echo "author@example.com $(cat ../signing-key.pub)" '
         '> ../allowed_signers && git config '
         'gpg.ssh.allowedSignersFile "$PWD/../allowed_signers"')
    k.write('f', 'x\n')
    k.sh('git add f && git commit -q -S -m signed')
    fp = lambda t: re.sub(r'SHA256:[A-Za-z0-9+/]+', 'SHA256:<지문>', t)
    k.cap('git verify-commit HEAD', edit=fp)
    k.cap('git cat-file -p HEAD | head -4')
    k.cap('git log --show-signature -1 --format="%G? %GS %s"', edit=fp)
