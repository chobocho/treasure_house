# -*- coding: utf-8 -*-
"""limits — Git 이 잘하지 못하는 것들(14부).

큰 바이너리의 판마다 팩이 얼마나 자라는지(텍스트·압축된 바이너리와
견주어), 파일 수에 따른 인덱스와 트리의 크기, 대소문자·줄 끝·유니코드
정규화의 함정, 빈 디렉터리, 모드, 시간대 표시, SHA-256 저장소.

시간은 재지 않는다 — 매번 달라 캡처가 세 번 같을 수 없다(PLAN.md
§0.9). 규모는 결정적인 양(바이트·객체 수)으로만 싣는다.
"""
import os
import random
import unicodedata
import zlib

from exps.util import commit, tick

MB = 1 << 20


def packed(r):
    r.sh('git gc -q --aggressive')
    d = os.path.join(r.path, '.git', 'objects', 'pack')
    return sum(os.path.getsize(os.path.join(d, f))
               for f in os.listdir(d) if f.endswith('.pack'))


def churn(ctx, name, make, versions=4):
    """같은 파일의 판 넷을 커밋하고 → (원래 크기 합, 팩 크기)."""
    r = ctx.repo(name)
    r.sh('git config pack.threads 1')
    rng = random.Random(7)             # 판마다 같은 곳을 바꾸게
    total = 0
    data = None
    for v in range(versions):
        data = make(rng, data)
        total += len(data)
        tick(r, v)
        r.write('asset', data)
        r.sh('git add asset && git commit -q -m v%d' % v)
    return total, packed(r)


def raw_binary(rng, prev):
    """무작위 바이트 1 MiB, 판마다 1 % 자리만 바꾼다."""
    if prev is None:
        return rng.randbytes(MB)
    b = bytearray(prev)
    for _ in range(len(b) // 100):
        b[rng.randrange(len(b))] = rng.getrandbits(8)
    return bytes(b)


def text(rng, prev):
    """무작위 낱말로 된 글 1 MiB, 판마다 줄 1 % 를 바꾼다. 낱말이
    무작위라 zlib 으로 눌러도 절반쯤으로만 줄어든다."""
    if prev is None:
        words = ['%x' % rng.getrandbits(24) for _ in range(4096)]
        return ''.join(' '.join(rng.choice(words) for _ in range(8))
                       + '\n' for _ in range(MB // 56)).encode()
    lines = prev.split(b'\n')
    for _ in range(len(lines) // 100):
        k = rng.randrange(len(lines))
        lines[k] = b'changed %d' % rng.getrandbits(20)
    return b'\n'.join(lines)


def packed_text(rng, prev):
    """글을 zlib 으로 누른 것 — 조금 바꿔도 바이트가 온통 달라진다."""
    return zlib.compress(text(rng, prev and zlib.decompress(prev)), 6)


def run(ctx):
    rows = []
    for name, make, what in (('limits_text', text, '글(줄 1 % 수정)'),
                             ('limits_bin', raw_binary,
                              '무작위 바이너리(1 % 수정)'),
                             ('limits_zip', packed_text,
                              '압축된 글(줄 1 % 수정)')):
        total, pack = churn(ctx, name, make)
        rows.append((what, 4, '%.1f MiB' % (total / MB),
                     '%.2f MiB' % (pack / MB),
                     '%.0f%%' % (100.0 * pack / total)))
    ctx.table('limits_churn', ['내용', '판', '원래 크기 합', '팩 크기',
                               '비율'], rows,
              '1 MiB 안팎 파일(압축된 글은 그 글을 누른 것)의 판 넷을 '
              '커밋하고 '
              'gc --aggressive 한 뒤')
    # 파일 수 — 인덱스와 트리 객체
    rows = []
    for n in (1000, 5000, 20000):
        r = ctx.repo('limits_files')
        for k in range(n):
            r.write('d%02d/d%02d/f%05d' % (k % 20, k // 20 % 20, k),
                    '%d\n' % k)
        r.sh('git add -A && git commit -q -m files')
        trees = int(r.sh('git ls-tree -r -t -d HEAD | wc -l')) + 1
        rows.append((n, os.path.getsize(os.path.join(r.path, '.git',
                                                     'index')),
                     trees))
    ctx.table('limits_files', ['파일 수', '.git/index 바이트',
                               '트리 객체'], rows,
              '파일을 20×20 디렉터리에 고르게 나눠 한 번에 커밋')
    # 대소문자 — ignorecase 인 척하는 저장소에서 이름만 바꾸기
    r = ctx.repo('limits_case')
    commit(r, 0, 'base', {'README': 'x\n'})
    r.sh('git config core.ignorecase true')
    r.sh('mv README readme')
    r.cap('git status --short')
    r.cap('git ls-files')
    r.cap('git mv -f README readme 2>&1; git ls-files',
          label='limits_case.mv')
    # 줄 끝 — autocrlf 가 CRLF 를 LF 로 바꿔 넣는다
    r = ctx.repo('limits_crlf')
    r.sh('git config core.autocrlf input')
    r.write('win.txt', 'one\r\ntwo\r\n')
    r.cap('git add win.txt')
    r.cap('git ls-files --eol win.txt')
    r.cap('git cat-file -p :win.txt | od -c')
    # 유니코드 정규화 — 보기에는 같은 이름, 바이트는 다른 두 파일
    r = ctx.repo('limits_nfd')
    nfc = unicodedata.normalize('NFC', '한글.txt')
    nfd = unicodedata.normalize('NFD', '한글.txt')
    r.write(nfc, 'nfc\n')
    r.write(nfd, 'nfd\n')
    r.sh('git add -A')
    r.cap('git ls-files')
    r.cap('git -c core.quotepath=false ls-files')
    r.cap('git ls-files -z | od -c | head -6')
    # 빈 디렉터리는 없다 — 파일만 추적한다
    r = ctx.repo('limits_empty')
    os.makedirs(os.path.join(r.path, 'empty'))
    r.cap('git status --short --untracked-files=all')
    r.write('empty/.gitkeep', '')
    r.cap('git status --short --untracked-files=all',
          label='limits_empty.keep')
    # 모드 — 644·755·링크, 그리고 fileMode=false
    r = ctx.repo('limits_mode')
    r.write('plain', 'x\n', 0o644)
    r.write('run.sh', '#!/bin/sh\n', 0o755)
    r.sh('ln -s plain link && git add -A && git commit -q -m modes')
    r.cap('git ls-tree HEAD')
    r.sh('chmod 755 plain')
    r.cap('git diff')
    r.cap('git -c core.fileMode=false diff')
    # 시간대 — 같은 순간, 적힌 시간대 그대로 · UTC · 형식
    r = ctx.repo('limits_date')
    r.env['GIT_AUTHOR_DATE'] = '1700000000 -0700'
    r.sh('git commit -q --allow-empty -m tz')
    for fmt in ('default', 'iso', 'iso-strict', 'rfc', 'raw', 'short',
                'unix', 'format:%Y-%m-%d %H:%M %z'):
        r.cap('git log -1 --format=%%ad --date="%s"' % fmt)
    r.cap('TZ=Asia/Seoul git log -1 --format=%ad --date=local')
    # SHA-256 저장소 — 이름이 64 글자, SHA-1 저장소와 섞이지 않는다
    r = ctx.repo('limits_sha256', init=False)
    r.cap('git init -q --object-format=sha256 -b main && '
          'git rev-parse --show-object-format')
    r.write('f', 'hello\n')
    r.cap('git hash-object f')
    r.sh('git add f && git commit -q -m sha256')
    r.cap('git cat-file -p HEAD')
    r.cap('git fetch -q ../limits_mode main 2>&1', ok=(128,))
