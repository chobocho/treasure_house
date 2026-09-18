# -*- coding: utf-8 -*-
"""proto — 전송 프로토콜과 원격 저장소(11·12부).

origin(bare) 하나를 두고 로컬 경로·file:// 로 clone·fetch·push 한다.
GIT_TRACE_PACKET 이 찍는 pkt-line 대화로 v0 과 v2 를 견주고, dumb
HTTP 의 파일 배치, bundle, 얕은 clone, 부분 clone(promisor), 되감기
거부를 보인다. 패킷 추적 줄 앞의 시각은 명령 안의 grep -o 가 떼어 낸다.
"""
import re

from exps.util import commit, tick


def run(ctx):
    src = ctx.repo('proto_src')
    for n in range(5):
        commit(src, n, 'c%d' % n,
               {'f.txt': 'v%d\n' % n,
                'big/%d.bin' % n: 'x' * 2000 + str(n)})
    src.sh('git tag v1 HEAD~1 && git branch dev HEAD~2')
    o = ctx.repo('proto_origin', init=False)
    o.sh('git clone -q --bare ../proto_src .')
    o.sh('git config uploadpack.allowFilter true')
    w = ctx.repo('proto_work')
    w.cap('git ls-remote ../proto_origin')
    # 두 프로세스가 같은 stderr 에 적어 줄 차례가 흔들린다 — 클라이언트
    # (ls-remote·clone)의 줄만 거른다. 한 프로세스의 줄은 차례가 고정.
    for v, pat in (('0', 'ls-remote<.*" | fold -w 90'),
                   ('2', 'ls-remote[<>].*"')):
        w.cap('git config protocol.version %s' % v)
        w.cap('GIT_TRACE_PACKET=1 git ls-remote ../proto_origin 2>&1 '
              '| grep -o "%s' % pat, label='proto_work.v' + v)
    w.sh('git config --unset protocol.version')
    # 로컬 경로 clone 은 프로토콜 없이 객체를 복사한다 — file:// 로
    # 불러야 want/have 대화가 오간다
    w.cap('GIT_TRACE_PACKET=1 git clone -q file://$PWD/../proto_origin '
          'v2 2>&1 | grep -o "clone[<>].*" | cut -c1-90')
    w.cap('git -C v2 log --oneline --all --decorate')
    w.cap('git -C v2 branch -a')
    w.cap('cat v2/.git/config')
    # dumb HTTP 가 읽는 파일들 — 서버는 정적 파일만 준다
    w.cap('git -C ../proto_origin update-server-info && '
          'cat ../proto_origin/info/refs')
    w.cap('cat ../proto_origin/objects/info/packs',
          edit=lambda t: re.sub(r'pack-[0-9a-f]{40}', 'pack-<이름>', t))
    # bundle — 네트워크 없이 옮기는 팩 + 참조
    w.cap('git -C ../proto_origin bundle create ../proto.bundle --all '
          '2>&1')
    w.cap('git bundle verify ../proto.bundle')
    w.cap('git bundle list-heads ../proto.bundle')
    w.cap('git clone -q ../proto.bundle from-bundle && '
          'git -C from-bundle log --oneline')
    # 얕은 clone — 역사의 끝 하나만
    w.cap('git clone -q --depth 1 file://$PWD/../proto_origin shallow '
          '&& git -C shallow log --oneline')
    w.cap('cat shallow/.git/shallow')
    w.cap('git -C shallow fetch -q --deepen 2 && '
          'git -C shallow log --oneline', label='proto_work.deepen')
    # 부분 clone — blob 은 필요할 때 받는다(promisor)
    w.cap('git clone -q --filter=blob:none --no-checkout '
          'file://$PWD/../proto_origin partial')
    w.cap('git -C partial rev-list --objects --missing=print --all '
          '| grep -c "^?"')
    w.cap('git -C partial config --get remote.origin.promisor')
    w.cap('git -C partial config --get '
          'remote.origin.partialclonefilter')
    w.cap('git -C partial checkout -q main && '
          'git -C partial rev-list --objects --missing=print --all '
          '| grep -c "^?"', label='proto_work.checkout')
    # push 와 되감기 거부
    w.sh('git -C ../proto_origin config '
         'receive.denyNonFastForwards true')
    tick(w, 20)
    w.sh('git -C v2 commit -q --allow-empty -m pushed')
    w.cap('git -C v2 push origin main 2>&1')
    w.sh('git -C v2 reset -q --hard HEAD~2')
    tick(w, 21)
    w.sh('git -C v2 commit -q --allow-empty -m rewritten')
    w.cap('git -C v2 push origin main 2>&1', label='proto_work.nonff',
          ok=(1,))
    w.cap('git -C v2 push --force origin main 2>&1',
          label='proto_work.force', ok=(1,))
    w.cap('git -C v2 fetch origin && git -C v2 status -sb',
          label='proto_work.fetch')
