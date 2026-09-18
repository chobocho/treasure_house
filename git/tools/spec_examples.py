# -*- coding: utf-8 -*-
"""spec_examples.py — SPEC.md 의 바이트 예시를 진짜 git 으로 뜬다.

    python3 tools/spec_examples.py            # 예시 블록 전부를 찍는다
    python3 tools/spec_examples.py --fill     # SPEC.md 의 블록을 채운다
    python3 tools/spec_examples.py --check    # SPEC.md 의 블록과 대조만

SPEC.md 는 다섯 구현이 함께 지키는 약속이다. 거기 적힌 바이트가
기억으로 쓴 것이면 다섯 구현이 한꺼번에 틀린다. 그래서 예시는 전부
이 스크립트가 scratch/spec/ 에 새 저장소를 만들고 진짜 git 을 돌려
얻은 것이고, SPEC.md 에는 `<!--EX 이름-->` … `<!--/EX-->` 사이에 그대로
실린다. --check 는 두 쪽이 한 글자도 다르지 않은지 본다.

환경은 tools/gitenv.sh 가 정한다(시각·작성자 고정, 전역 설정 차단).
시간 O(예시 수), scratch/spec 밖은 건드리지 않는다.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gitenv                                          # noqa: E402

SCRATCH = os.path.join(BASE, 'scratch', 'spec')
SPEC = os.path.join(BASE, 'SPEC.md')


def hexdump(data):
    """16바이트씩 '오프셋  16진  |글자|'. 인쇄 못 하는 바이트는 '.'."""
    rows = []
    for off in range(0, len(data), 16):
        chunk = data[off:off + 16]
        hx = ' '.join('%02x' % b for b in chunk)
        tx = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        rows.append('%04x  %-47s  |%s|' % (off, hx, tx))
    return '\n'.join(rows)


def loose(repo, oid):
    """느슨한 객체 파일을 풀어 헤더까지 포함한 바이트를 돌려준다."""
    p = os.path.join(repo, '.git', 'objects', oid[:2], oid[2:])
    return zlib.decompress(open(p, 'rb').read())


class Repo:
    def __init__(self, env, name):
        self.env = env
        self.path = os.path.join(SCRATCH, name)
        os.makedirs(self.path)
        self.git('init', '-q', '-b', 'main')

    def git(self, *args, stdin=None):
        return gitenv.git(self.env, self.path, *args,
                          stdin=stdin)[1].decode()

    def write(self, rel, data, mode=0o644):
        p = os.path.join(self.path, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data)
        os.chmod(p, mode)

    def run(self, *args):
        """캡처용: '$ git …' 한 줄과 그 출력."""
        return '$ git %s\n%s' % (' '.join(args), self.git(*args))


def ex_empty(env):
    r = Repo(env, 'empty')
    return (r.run('hash-object', '-t', 'blob', '/dev/null')
            + r.run('hash-object', '-t', 'tree', '/dev/null')).rstrip()


def ex_blob(env):
    r = Repo(env, 'blob')
    oid = r.git('hash-object', '-w', '--stdin',
                stdin=b'hello\n').strip()
    return ('$ printf \'hello\\n\' | git hash-object -w --stdin\n%s\n'
            '# .git/objects/%s/%s 를 zlib 으로 푼 바이트\n%s'
            % (oid, oid[:2], oid[2:], hexdump(loose(r.path, oid))))


def small_repo(env, name):
    """hello.txt · run.sh(실행 권한) · src/a.py 세 파일짜리 저장소."""
    r = Repo(env, name)
    r.write('hello.txt', b'hello\n')
    r.write('run.sh', b'#!/bin/sh\necho hi\n', 0o755)
    r.write('src/a.py', b'print(1)\n')
    r.git('add', '.')
    return r


def ex_tree(env):
    r = small_repo(env, 'tree')
    oid = r.git('write-tree').strip()
    return ('%s\n# 트리 %s 를 푼 바이트 (id 는 20바이트 이진)\n%s'
            % (r.run('cat-file', '-p', oid).rstrip(), oid[:7],
               hexdump(loose(r.path, oid))))


def ex_tree_sort(env):
    r = Repo(env, 'sort')
    for name in ('a-b', 'a.b', 'a/x', 'ab', 'a=b'):
        r.write(name, b'%s\n' % name.encode())
    r.git('add', '.')
    oid = r.git('write-tree').strip()
    return (r.run('ls-files', '--stage').rstrip() + '\n'
            + r.run('ls-tree', oid).rstrip())


def ex_commit(env):
    r = small_repo(env, 'commit')
    r.git('commit', '-q', '-m', 'first')
    r.write('hello.txt', b'hello\nworld\n')
    r.git('commit', '-q', '-a', '-m', 'second\n\nbody line')
    oid = r.git('rev-parse', 'HEAD').strip()
    raw = loose(r.path, oid)
    return ('%s# 헤더: %r\n%s'
            % (r.run('cat-file', '-p', 'HEAD'),
               raw[:raw.index(b'\0') + 1].decode(),
               r.run('log', '--oneline').rstrip()))


def ex_tag(env):
    r = small_repo(env, 'tag')
    r.git('commit', '-q', '-m', 'first')
    r.git('tag', '-a', 'v1.0', '-m', 'release 1.0')
    return r.run('cat-file', '-p', 'v1.0').rstrip()


def normalized_index(data):
    """항목마다 ctime·mtime·dev·ino·uid·gid(앞 40바이트 중 mode 를
    뺀 칸)을 0 으로 지우고 끝의 SHA-1 을 다시 계산한다.
    판 2 · 확장 없음만 다룬다."""
    import hashlib
    import struct
    assert data[:4] == b'DIRC' and data[4:8] == b'\0\0\0\2'
    out = bytearray(data[:-20])
    n = struct.unpack('>I', data[8:12])[0]
    pos = 12
    for _ in range(n):
        # mode(24‥27)·size(36‥39) 는 남긴다
        for a, b in ((0, 24), (28, 36)):
            out[pos + a:pos + b] = bytes(b - a)
        flags = struct.unpack('>H', data[pos + 60:pos + 62])[0]
        namelen = flags & 0xfff
        pos += (62 + namelen + 8) // 8 * 8
    return bytes(out) + hashlib.sha1(bytes(out)).digest()


def ex_index(env):
    r = small_repo(env, 'index')
    data = open(os.path.join(r.path, '.git', 'index'), 'rb').read()
    return ('%s# .git/index — stat 칸을 0 으로 지우고'
            ' 끝 SHA-1 을 다시 계산\n%s'
            % (r.run('ls-files', '--stage'),
               hexdump(normalized_index(data))))


def ex_pack(env):
    r = Repo(env, 'pack')
    body = b''.join(b'line %d\n' % i for i in range(1, 41))
    r.write('f.txt', body)
    r.git('add', '.')
    r.git('commit', '-q', '-m', 'one')
    r.write('f.txt', body + b'line 41\n')
    r.git('commit', '-q', '-a', '-m', 'two')
    r.git('-c', 'pack.threads=1', '-c', 'pack.window=10',
          '-c', 'pack.depth=50', 'repack', '-a', '-d', '-f', '-q')
    pdir = os.path.join(r.path, '.git', 'objects', 'pack')
    idx = sorted(x for x in os.listdir(pdir) if x.endswith('.idx'))[0]
    pack = open(os.path.join(pdir, idx[:-4] + '.pack'), 'rb').read()
    ixb = open(os.path.join(pdir, idx), 'rb').read()
    vp = r.git('verify-pack', '-v', '.git/objects/pack/' + idx)
    vp = vp.replace(idx[:-4], 'pack-<체크섬>')
    return ('$ git verify-pack -v'
            ' .git/objects/pack/pack-<체크섬>.idx\n%s'
            '# .pack 앞 16바이트 (헤더 12 + 첫 항목)\n%s\n'
            '# .idx 앞 16바이트 (매직 · 판 · fanout[0])\n%s\n'
            '# 파일 이름의 체크섬 = .pack 끝 20바이트: %s'
            % (vp, hexdump(pack[:16]), hexdump(ixb[:16]),
               'yes' if pack[-20:].hex() == idx[5:-4] else 'no'))


def pkt(line):
    """pkt-line 하나. 길이 네 자리 16진은 자기 4바이트를 포함한다."""
    data = line.encode() if isinstance(line, str) else line
    return b'%04x' % (len(data) + 4) + data


def ex_pkt(env):
    r = small_repo(env, 'pkt')
    r.git('commit', '-q', '-m', 'first')
    req = (pkt('command=ls-refs\n') + pkt('object-format=sha1\n')
           + b'0001' + pkt('peel\n') + pkt('symrefs\n') + b'0000')
    e = dict(env, GIT_PROTOCOL='version=2')
    p = subprocess.run(['git', 'upload-pack', r.path],
                       input=req + b'0000', env=e,
                       stdout=subprocess.PIPE, check=True)
    return ('# 보낸 것 (ls-refs 요청)\n%s\n'
            '# 받은 것 (능력 광고 + 참조 목록)\n%s'
            % (pkt_lines(req), pkt_lines(p.stdout)))


def pkt_lines(data):
    """pkt-line 바이트열을 한 줄에 한 패킷으로. 0000·0001 은 그대로."""
    lines = []
    while data:
        n = int(data[:4], 16)
        if n < 4:
            lines.append(data[:4].decode())
            data = data[4:]
            continue
        lines.append(data[:4].decode() + repr(data[4:n].decode())[1:-1])
        data = data[n:]
    return '\n'.join(lines)


EXAMPLES = [('empty', ex_empty), ('blob', ex_blob), ('tree', ex_tree),
            ('tree-sort', ex_tree_sort), ('commit', ex_commit),
            ('tag', ex_tag), ('index', ex_index), ('pack', ex_pack),
            ('pkt', ex_pkt)]


def build():
    if os.path.isdir(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    env = gitenv.load(os.path.join(SCRATCH, 'home'))
    return [(name, fn(env)) for name, fn in EXAMPLES]


BLOCK = r'<!--EX %s-->\n(?:```text\n(.*?)\n```\n)?<!--/EX-->'


def block(name, text):
    return '<!--EX %s-->\n```text\n%s\n```\n<!--/EX-->' % (name, text)


def fill(made):
    """SPEC.md 의 <!--EX 이름--> … <!--/EX--> 사이를 새로 뜬 것으로
    바꾼다.

    비어 있는 표식(<!--EX 이름-->\n<!--/EX-->)도 채운다. SPEC 을 쓸 때는
    표식만 두고 이것을 돌린다 — 바이트를 손으로 옮기지 않기 위해서다.
    """
    spec = io.open(SPEC, encoding='utf-8').read()
    for name, text in made:
        pat = re.compile(BLOCK % re.escape(name), re.S)
        if not pat.search(spec):
            print('  (SPEC.md 에 %s 표식이 없어 건너뜀)' % name)
            continue
        spec = pat.sub(lambda m: block(name, text), spec)
    io.open(SPEC, 'w', encoding='utf-8', newline='\n').write(spec)
    print('SPEC 예시 %d개를 채웠다' % len(made))
    return 0


def main(argv):
    made = build()
    if '--fill' in argv:
        return fill(made)
    if '--check' not in argv:
        for name, text in made:
            print(block(name, text) + '\n')
        return 0
    spec = io.open(SPEC, encoding='utf-8').read()
    bad = 0
    for name, text in made:
        m = re.search(BLOCK % re.escape(name), spec, re.S)
        if not m or m.group(1) is None:
            print('  ✗ SPEC.md 에 예시 %s 가 없다' % name)
            bad += 1
        elif m.group(1) != text:
            print('  ✗ 예시 %s 가 진짜 git 과 다르다' % name)
            bad += 1
    print('SPEC 예시 %d개 — 어긋남 %d건' % (len(made), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
