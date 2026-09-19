# -*- coding: utf-8 -*-
"""proto2 — 전송 프로토콜(11부)의 나머지.

  · pkt-line 의 날 바이트 — upload-pack 이 내는 광고를 그대로(v0 · v2).
  · fetch 의 협상 — 클라이언트가 이미 가진 것을 have 로 알린다.
  · push 가 보내는 것 — "옛 이름 새 이름 참조" 명령 줄과 report-status.
  · --atomic push — 하나라도 거절되면 아무것도 안 바뀐다.
  · 서버 쪽 pre-receive 훅의 거절.
  · 스마트 HTTP — git http-backend 를 CGI 로 직접 불러 응답을 본다.
"""
from exps.util import commit, tick


def origin(ctx, name):
    src = ctx.repo(name + '_src')
    for n in range(3):
        commit(src, n, 'c%d' % n, {'f.txt': 'v%d\n' % n})
    src.sh('git branch dev HEAD~1')
    o = ctx.repo(name, init=False)
    o.sh('git clone -q --bare ../%s_src .' % name)
    return src, o


def raw(ctx):
    _, o = origin(ctx, 'pkt_raw')
    o.cap('git upload-pack --advertise-refs . | head -c 200 | '
          'od -A d -c | head -6')
    o.cap("git upload-pack --advertise-refs . | tr '\\0' '@' | "
          "cut -c1-100")
    o.cap("GIT_PROTOCOL=version=2 git upload-pack --advertise-refs . | "
          "cut -c1-100")


def negotiate(ctx):
    src, o = origin(ctx, 'pkt_nego')
    w = ctx.repo('pkt_nego_work', init=False)
    w.sh('git clone -q file://$PWD/../pkt_nego .')
    # 원본에 새 커밋 둘 — 클라이언트는 옛 끝을 가지고 있다
    commit(src, 5, 'c5', {'f.txt': 'v5\n'})
    commit(src, 6, 'c6', {'f.txt': 'v6\n'})
    o.sh('git fetch -q ../pkt_nego_src main:main')
    w.cap('GIT_TRACE_PACKET=1 git fetch -q origin 2>&1 | '
          'grep -o "fetch[<>].*" | cut -c1-80')
    w.cap('git log --oneline -1 origin/main')


def pushing(ctx):
    src, o = origin(ctx, 'pkt_push')
    w = ctx.repo('pkt_push_work', init=False)
    w.sh('git clone -q file://$PWD/../pkt_push .')
    commit(w, 10, 'local', {'f.txt': 'local\n'})
    w.cap('GIT_TRACE_PACKET=1 git push -q origin main 2>&1 | '
          'grep -o "push[<>].*" | cut -c1-100')
    # --atomic: main 은 빨리 감기, dev 는 빨리 감기가 아니라 거부된다
    o.sh('git config receive.denyNonFastForwards true')
    tick(w, 11)
    w.sh('git switch -q -c dev origin/dev && '
         'git commit -q --allow-empty -m dev2 && git switch -q main')
    commit(w, 12, 'local2', {'f.txt': 'local2\n'})
    w.sh('git branch -f dev origin/dev~1')
    w.cap('git push --atomic origin main dev --force 2>&1', ok=None)
    w.cap('git -C ../pkt_push log --oneline -1 main')
    w.cap('git push origin main dev --force 2>&1', ok=None,
          label='pkt_push.nonatomic')
    w.cap('git -C ../pkt_push log --oneline -1 main',
          label='pkt_push.nonatomic')


HOOK = """#!/bin/sh
# 서버 쪽 훅 — 표준 입력으로 "옛 새 참조" 줄들을 받는다
while read old new ref; do
  if git log --format=%s "$new" -1 | grep -q WIP; then
    echo "거절: $ref 의 끝 커밋 제목에 WIP" >&2
    exit 1
  fi
done
"""


def hook(ctx):
    src, o = origin(ctx, 'pkt_hook')
    o.write('hooks/pre-receive', HOOK, 0o755)
    w = ctx.repo('pkt_hook_work', init=False)
    w.sh('git clone -q file://$PWD/../pkt_hook .')
    w.cap('cat ../pkt_hook/hooks/pre-receive')
    commit(w, 10, 'WIP half done', {'f.txt': 'wip\n'})
    w.cap('git push origin main 2>&1', ok=None)
    w.sh('git commit -q --amend -m "feature done"')
    w.cap('git push -q origin main 2>&1 && '
          'git -C ../pkt_hook log --oneline -1', label='pkt_hook.ok')


CGI = """export GIT_PROJECT_ROOT=$PWD/.. GIT_HTTP_EXPORT_ALL=1
export REQUEST_METHOD=GET PATH_INFO=/pkt_http/info/refs
export QUERY_STRING=service=git-upload-pack
git http-backend | tr '\\r\\0' ' @' | head -12 | cut -c1-90
"""


def http(ctx):
    _, o = origin(ctx, 'pkt_http')
    w = ctx.repo('pkt_http_client')
    w.write('../pkt-tools/cgi.sh', CGI)
    w.cap('cat ../pkt-tools/cgi.sh')
    w.cap('sh ../pkt-tools/cgi.sh')


def run(ctx):
    raw(ctx)
    negotiate(ctx)
    pushing(ctx)
    hook(ctx)
    http(ctx)
