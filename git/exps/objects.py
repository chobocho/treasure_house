# -*- coding: utf-8 -*-
"""objects — 객체를 손으로 만들고 git 이 읽게 한다(3부).

"<형식> <크기>\\0<몸>" 의 SHA-1 이 이름이고, 그 바이트를 zlib 으로 싼
것이 파일이다. 파이썬 한 줄로 만든 객체를 git 이 제 것처럼 읽고,
한 바이트를 깨뜨리면 fsck 가 찾아낸다. 빈 blob 과 빈 트리의 이름은
어느 저장소에서나 같다.
"""
MKBLOB = r'''import hashlib, os, zlib
data = b"blob 6\0hello\n"            # 머리 + 몸
oid = hashlib.sha1(data).hexdigest()  # 이름 = 머리까지 넣은 SHA-1
d = ".git/objects/" + oid[:2]
os.makedirs(d, exist_ok=True)
with open(d + "/" + oid[2:], "wb") as f:
    f.write(zlib.compress(data))      # 파일 = zlib 으로 싼 바이트
print(oid)
'''
INFLATE = r'''import sys, zlib
raw = open(sys.argv[1], "rb").read()
sys.stdout.buffer.write(zlib.decompress(raw))
'''


def run(ctx):
    r = ctx.repo('objects')
    r.write('../objects-tools/mkblob.py', MKBLOB)
    r.write('../objects-tools/inflate.py', INFLATE)
    r.env['PATH'] = r.env['PATH']
    obj = '.git/objects/ce/013625030ba8dba906f756967f9e9ca394464a'
    # git 이 직접 쓴 파일부터 — 느슨한 객체의 기본 압축 수준은 1 이라
    # 78 01 로 시작한다. 아래 mkblob.py(파이썬 zlib 기본 수준 6)가 쓴
    # 파일은 78 9c 다. 첫 판은 파이썬이 쓴 파일을 "git 의 파일" 로 실었다.
    g = ctx.repo('objects_git')
    g.cap("printf 'hello\\n' | git hash-object -w --stdin")
    g.cap('od -A d -t x1 ' + obj)
    g.cap('python3 ../objects-tools/inflate.py %s | od -c' % obj)
    r.cap("printf 'blob 6\\0hello\\n' | sha1sum")
    r.cap("printf 'hello\\n' | git hash-object --stdin")
    r.cap('cat ../objects-tools/mkblob.py')
    r.cap('python3 ../objects-tools/mkblob.py')
    r.cap('git cat-file -t ce01362')
    r.cap('git cat-file -s ce01362')
    r.cap('git cat-file -p ce01362')
    r.cap('git fsck --strict')
    r.cap('od -A d -t x1 ' + obj)
    r.cap('git hash-object -t blob /dev/null')
    r.cap('git hash-object -t tree /dev/null')
    r.cap("printf '' | git mktree")
    # 한 바이트 깨뜨리기 — 파일 권한 0444 를 풀고 끝 바이트를 바꾼다
    r.sh('chmod 644 %s' % obj)
    r.sh("python3 -c 'p=\"%s\"; b=bytearray(open(p,\"rb\").read()); "
         "b[-1]^=1; open(p,\"wb\").write(b)'" % obj)
    r.cap('git fsck --strict 2>&1 | fold -w 96',
          label='objects.corrupt')
    r.cap('git fsck --strict >/dev/null 2>&1; echo $?',
          label='objects.corrupt')
    r.cap('git cat-file -p ce01362', label='objects.corrupt', ok=None)
