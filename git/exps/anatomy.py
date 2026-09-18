# -*- coding: utf-8 -*-
"""anatomy — 객체 모델(3부)을 바이트로 연다.

  · 네 형식의 느슨한 객체를 풀어 머리("<형식> <크기>\\0")와 몸을 본다.
  · 트리의 이진 형식 — "<모드> <이름>\\0" 뒤에 이름 20바이트(16진이 아님).
  · 같은 트리·부모·메시지·시각이면 커밋 이름도 같다. 시각 1초가 다르면
    다르다(결정론과 불변의 두 얼굴).
  · 태그 — 가벼운 것과 주석 붙은 것, blob 을 가리키는 태그, 태그의 태그.
  · 이름 줄이기 — 짧은 이름이 겹치면 git 이 거절한다.
  · fsck 가 잡는 형식 오류 — 차례가 틀린 트리, 0 을 앞에 붙인 모드,
    사라진 blob.
  · 압축 수준 — 같은 blob 을 core.compression 0 과 9 로 적었을 때.
"""
import hashlib

from exps.util import commit, tick

RAWOBJ = r'''import subprocess, sys, zlib
# 느슨한 객체 하나를 풀어 머리까지 그대로 낸다
oid = subprocess.check_output(["git", "rev-parse", sys.argv[1]])
oid = oid.decode().strip()
raw = open(".git/objects/%s/%s" % (oid[:2], oid[2:]), "rb").read()
sys.stdout.buffer.write(zlib.decompress(raw))
'''

MKTREE = r'''import sys
# 트리 몸을 손으로 짠다: 항목마다 "<모드> <이름>\0" + 이름 20바이트.
# 인자: 모드 이름 blob40 … (적힌 차례 그대로 — git 처럼 정렬하지 않는다)
a = sys.argv[1:]
body = b""
for k in range(0, len(a), 3):
    body += ("%s %s" % (a[k], a[k + 1])).encode() + b"\0"
    body += bytes.fromhex(a[k + 2])
sys.stdout.buffer.write(body)
'''


# 손으로 짠 트리 둘 — 해시가 길어 명령 줄 대신 스크립트에 적는다
UNSORTED = """a=$(git rev-parse HEAD:a.txt)
b=$(git rev-parse HEAD:b.txt)
# b.txt 를 a.txt 앞에 — git 이라면 이렇게 적지 않는다
python3 ../anatomy-tools/rawtree.py 100644 b.txt $b 100644 a.txt $a |
  git hash-object -t tree -w --stdin --literally
"""
PADDED = """a=$(git rev-parse HEAD:a.txt)
# 모드 앞에 0 을 붙인다 — git 은 이렇게 적지 않는다
python3 ../anatomy-tools/rawtree.py 0100644 a.txt $a |
  git hash-object -t tree -w --stdin --literally
"""


def tools(r):
    r.write('../anatomy-tools/rawobj.py', RAWOBJ)
    r.write('../anatomy-tools/rawtree.py', MKTREE)
    r.write('../anatomy-tools/unsorted.sh', UNSORTED)
    r.write('../anatomy-tools/padded.sh', PADDED)


def kinds(ctx):
    r = ctx.repo('anatomy')
    tools(r)
    commit(r, 0, 'first', {'hello.txt': 'hello\n',
                           'src/main.c': 'int main(void) { return 0; }\n'})
    r.write('run.sh', '#!/bin/sh\necho hi\n', 0o755)
    r.sh('ln -s hello.txt link')
    tick(r, 1)
    r.sh('git add -A && git commit -q -m "add run.sh and link"')
    tick(r, 2)
    r.sh('git tag -a v1 -m "version one"')
    r.cap('cat ../anatomy-tools/rawobj.py')
    loop = 'for o in HEAD HEAD^{tree} HEAD:hello.txt v1; do '
    r.cap(loop + 'git cat-file -t $o; done')
    r.cap(loop + 'git cat-file -s $o; done')
    raw = 'python3 ../anatomy-tools/rawobj.py '
    r.cap(raw + 'HEAD:hello.txt | od -c')
    r.cap(raw + 'HEAD | od -c | head -4')
    r.cap(raw + 'HEAD | tr "\\0" "@"')
    r.cap(raw + 'v1 | tr "\\0" "@"')
    # 트리 — 사람용 표시와 날 바이트
    r.cap('git cat-file -p HEAD^{tree}')
    r.cap(raw + 'HEAD^{tree} | od -c | head -8')
    r.cap(raw + 'HEAD^{tree} | od -A d -t x1 | head -4')
    r.cap('git rev-parse HEAD:hello.txt')
    r.cap('git cat-file tree HEAD^{tree} | wc -c')
    r.cap('git cat-file -p HEAD:link; echo')
    r.cap('git cat-file -p HEAD:src')
    # 이름으로 객체 찾기
    r.cap('git rev-parse HEAD^{tree} HEAD:src HEAD:src/main.c')
    r.cap('git rev-parse --short HEAD')
    r.cap('git rev-parse --short=4 HEAD')
    r.cap("printf 'HEAD\\nHEAD:hello.txt\\nv1\\n' | "
          "git cat-file --batch-check")
    r.cap("printf 'HEAD:hello.txt\\n' | git cat-file --batch")
    r.cap("printf 'HEAD first\\nv1 tag\\n' | git cat-file "
          "--batch-check='%(objecttype) %(objectsize) %(rest)'")
    return r


def commits(ctx):
    """커밋 이름을 정하는 것 — 트리·부모·사람·시각·메시지 전부."""
    r = ctx.repo('commit_id')
    commit(r, 0, 'base', {'f.txt': 'x\n'})
    # 시각은 환경(gitenv)으로 고정하고, 바꾸는 것만 명령 줄에 적는다
    tick(r, 1)
    ct = 'git commit-tree HEAD^{tree} -p HEAD -m same'
    r.cap(ct, label='commit_id.a')
    r.cap(ct, label='commit_id.b')
    r.cap("GIT_COMMITTER_DATE='1700000061 +0900' " + ct)
    r.cap('GIT_AUTHOR_NAME=Eve ' + ct)
    r.cap(ct.replace('-p HEAD ', ''))
    r.cap(ct.replace('same', 'Same'))
    # 인코딩 머리 — 메시지가 UTF-8 이 아니라고 적을 때
    tick(r, 3)
    r.sh("git -c i18n.commitEncoding=ISO-8859-1 commit -q "
         "--allow-empty -m latin1")
    r.cap('git cat-file -p HEAD')


def tags(ctx):
    r = ctx.repo('tagkinds')
    commit(r, 0, 'base', {'f.txt': 'x\n'})
    tick(r, 1)
    r.sh('git tag light')
    r.sh('git tag -a heavy -m "annotated"')
    r.sh('git tag -a blobtag -m "points at a blob" HEAD:f.txt')
    r.sh('git tag -a again -m "tag of a tag" heavy')
    r.cap('for t in light heavy blobtag again; do '
          'printf "%s " $t; git cat-file -t $t; done')
    r.cap('git cat-file -p blobtag')
    r.cap('git cat-file -p again')
    r.cap('git rev-parse again again^{} again^{commit}')
    r.cap('cat .git/refs/tags/light .git/refs/tags/heavy')


def ambiguous(ctx):
    """blob 을 여럿 만들어 앞 네 글자가 같은 둘을 찾는다. 내용이 정해져
    있으니 어느 둘이 겹칠지도 늘 같다."""
    r = ctx.repo('ambig')
    seen = {}
    pair = None
    for k in range(2000):
        data = ('blob %d\n' % k).encode()
        oid = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
        if oid[:4] in seen:
            pair = (seen[oid[:4]], k, oid[:4])
            break
        seen[oid[:4]] = k
    a, b, pre = pair
    for k in (a, b):
        r.sh("printf 'blob %d\\n' | git hash-object -w --stdin" % k)
    r.cap("printf 'blob %d\\n' | git hash-object --stdin; "
          "printf 'blob %d\\n' | git hash-object --stdin" % (a, b))
    r.cap('git rev-parse %s' % pre, ok=None)
    r.cap('git rev-parse --disambiguate=%s' % pre)


def broken(ctx):
    """fsck --strict 가 잡는 것 — 손으로 짠 트리 두 개와 사라진 blob."""
    r = ctx.repo('fsckcheck')
    tools(r)
    commit(r, 0, 'base', {'a.txt': 'a\n', 'b.txt': 'b\n'})
    blob_b = r.sh('git rev-parse HEAD:b.txt').strip()
    r.cap('cat ../anatomy-tools/rawtree.py')
    # b.txt 를 a.txt 앞에 — 차례가 틀린 트리
    r.cap('cat ../anatomy-tools/unsorted.sh')
    t1 = r.cap('sh ../anatomy-tools/unsorted.sh').strip()
    r.cap('git fsck --strict 2>&1 | grep %s' % t1[:7], ok=None,
          label='fsckcheck.unsorted')
    # 모드 앞에 0 — git 이 쓰지 않는 꼴
    r.cap('cat ../anatomy-tools/padded.sh')
    t2 = r.cap('sh ../anatomy-tools/padded.sh').strip()
    r.cap('git fsck --strict 2>&1 | grep %s' % t2[:7], ok=None,
          label='fsckcheck.padded')
    r.cap('git fsck 2>&1 | grep %s | fold -w 100' % t2[:7], ok=None,
          label='fsckcheck.padded')
    # 사라진 blob
    r.sh('rm -f .git/objects/%s/%s' % (blob_b[:2], blob_b[2:]))
    r.cap('git fsck --strict 2>&1 | grep -v dangling', ok=None,
          label='fsckcheck.missing')
    r.cap('git cat-file -p HEAD:b.txt', ok=None,
          label='fsckcheck.missing')


def compression(ctx):
    r = ctx.repo('zlevel')
    text = ''.join('line %04d of a fairly repetitive file\n' % k
                   for k in range(300))
    r.write('big.txt', text)
    r.cap('wc -c < big.txt')
    size = ('f=$(git hash-object big.txt); '
            'wc -c < .git/objects/${f%%${f#??}}/${f#??}')
    for lvl in (0, 1, 9):
        r.sh('rm -rf .git/objects/[0-9a-f][0-9a-f]')
        r.sh('git -c core.looseCompression=%d hash-object -w big.txt'
             % lvl)
        r.cap(size, label='zlevel.%d' % lvl)


def run(ctx):
    kinds(ctx)
    commits(ctx)
    tags(ctx)
    ambiguous(ctx)
    broken(ctx)
    compression(ctx)
