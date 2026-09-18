# -*- coding: utf-8 -*-
"""tools2 — 설정·훅·도구(13부)의 나머지.

  · 훅 스크립트의 모양과 설정으로 정하는 훅(hook.<이름>.command·event),
    git hook run.
  · 필터(clean/smudge) — 저장소에는 다른 바이트를, 작업 트리에는 원래
    바이트를. 큰 파일을 저장소 밖에 두는 LFS 가 쓰는 자리를 흉내 낸다.
  · 서브모듈 — clone --recurse-submodules, 원격이 앞서 나간 뒤의 update,
    서브모듈 안의 분리 HEAD.
  · worktree — 같은 브랜치를 두 곳에서 꺼내지 못한다.
  · credential store — 비밀을 평문 파일에 적는다.
  · maintenance register — 예약할 저장소 목록이 설정에 적힌다.
"""
from exps.util import commit, tick


def hooks(ctx):
    r = ctx.repo('hook_cfg')
    commit(r, 0, 'base', {'a.txt': 'a\n'})
    r.write('../hook-tools/lint.sh', '#!/bin/sh\n'
            'echo "lint: $(git diff --cached --name-only | wc -l) 파일"\n',
            0o755)
    r.cap('git config hook.lint.command "sh ../hook-tools/lint.sh"')
    r.cap('git config hook.lint.event pre-commit')
    r.cap('git config --get-regexp "^hook\\."')
    r.cap('git hook list pre-commit')
    r.write('b.txt', 'b\n')
    tick(r, 1)
    r.cap('git add b.txt && git commit -q -m b')
    r.cap('git hook run pre-commit')
    r.cap('ls .git/hooks | head -5; ls .git/hooks | wc -l')


ROT = "tr 'A-Za-z' 'N-ZA-Mn-za-m'"
STASH = r'''#!/bin/sh
# clean: 표준 입력의 내용을 저장소 밖(../lfs-store)에 두고,
# 저장소에는 그 SHA-256 을 적은 세 줄짜리 "포인터" 만 넘긴다
mkdir -p ../lfs-store
tmp=$(mktemp)
cat > "$tmp"
oid=$(sha256sum "$tmp" | cut -c1-64)
mv "$tmp" ../lfs-store/$oid
printf 'pointer\noid sha256:%s\nsize %s\n' $oid $(wc -c < ../lfs-store/$oid)
'''
FETCH = r'''#!/bin/sh
# smudge: 포인터를 읽어 저장소 밖의 내용을 꺼내 준다
oid=$(sed -n 's/^oid sha256://p')
cat ../lfs-store/$oid
'''


def filters(ctx):
    r = ctx.repo('filter_rot')
    r.write('.gitattributes', '*.secret filter=rot\n')
    r.sh('git config filter.rot.clean "%s" && '
         'git config filter.rot.smudge "%s"' % (ROT, ROT))
    r.write('note.secret', 'Hello Git\n')
    tick(r, 0)
    r.sh('git add -A && git commit -q -m rot')
    r.cap('cat note.secret')
    r.cap('git cat-file -p HEAD:note.secret')
    # 큰 파일을 밖으로 — LFS 흉내
    b = ctx.repo('filter_big')
    b.write('../big-tools/clean.sh', STASH, 0o755)
    b.write('../big-tools/smudge.sh', FETCH, 0o755)
    b.write('.gitattributes', '*.bin filter=big\n')
    b.sh('git config filter.big.clean "sh ../big-tools/clean.sh" && '
         'git config filter.big.smudge "sh ../big-tools/smudge.sh" && '
         'git config filter.big.required true')
    b.write('video.bin', 'x' * 100000)
    tick(b, 0)
    b.sh('git add -A && git commit -q -m video')
    b.cap('cat ../big-tools/clean.sh')
    b.cap('wc -c < video.bin')
    b.cap('git cat-file -p HEAD:video.bin')
    b.cap('git cat-file -s HEAD:video.bin')
    b.cap('rm video.bin && git checkout -- video.bin && wc -c < video.bin',
          label='filter_big.restored')


def submodules(ctx):
    lib = ctx.repo('sm_lib')
    commit(lib, 0, 'lib v1', {'lib.c': 'int v = 1;\n'})
    app = ctx.repo('sm_app')
    commit(app, 1, 'app', {'app.c': 'int main;\n'})
    tick(app, 2)
    app.sh('git -c protocol.file.allow=always submodule add -q '
           '../sm_lib lib && git commit -q -m "add lib"')
    c = ctx.repo('sm_clone', init=False)
    c.cap('git clone -q ../sm_app plain && ls plain/lib | wc -l')
    c.cap('git -c protocol.file.allow=always clone -q '
          '--recurse-submodules ../sm_app full && cat full/lib/lib.c')
    c.cap('git -C full/lib status | head -1')
    # 라이브러리가 앞서 나가도 앱은 옛 커밋을 가리킨다
    commit(lib, 3, 'lib v2', {'lib.c': 'int v = 2;\n'})
    c.cap('git -C full submodule status')
    c.cap('git -C full -c protocol.file.allow=always submodule update '
          '-q --remote && git -C full submodule status',
          label='sm_clone.remote')
    c.cap('git -C full status --short', label='sm_clone.remote')
    c.cap('git -C full diff --submodule=log', label='sm_clone.remote')


def worktrees(ctx):
    r = ctx.repo('wt_twice')
    commit(r, 0, 'base', {'a.txt': 'a\n'})
    r.sh('git branch topic')
    r.cap('git worktree add -q ../wt_twice-a topic && '
          'git worktree add ../wt_twice-b topic 2>&1', ok=None)
    r.cap('git switch topic 2>&1', ok=None)
    r.cap('git worktree list --porcelain | head -4')


def credentials(ctx):
    r = ctx.repo('cred_store')
    r.sh('git config credential.helper "store --file=../cred-store.txt"')
    # 가짜 비밀번호다 — 이 덱 어디에도 진짜 비밀은 없다
    r.write('../cred-in.txt', 'protocol=https\nhost=example.com\n'
            'username=demo\npassword=not-a-real-secret\n\n')
    r.cap('cat ../cred-in.txt')
    r.cap('git credential approve < ../cred-in.txt && '
          'cat ../cred-store.txt')
    r.cap("printf 'protocol=https\\nhost=example.com\\n\\n' | "
          "git credential fill")


def maint(ctx):
    r = ctx.repo('maint_reg')
    commit(r, 0, 'base', {'a.txt': 'a\n'})
    # 실험 환경은 전역 설정을 /dev/null 로 막아 둔다(gitenv) — 이
    # 실험만 따로 파일을 준다
    r.env['GIT_CONFIG_GLOBAL'] = r.path + '/../maint-gitconfig'
    r.cap('git maintenance register && '
          'git config --global --get-all maintenance.repo')
    r.cap('git config --get-regexp "^maintenance\\."')


def run(ctx):
    hooks(ctx)
    filters(ctx)
    submodules(ctx)
    worktrees(ctx)
    credentials(ctx)
    maint(ctx)
