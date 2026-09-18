# -*- coding: utf-8 -*-
"""make_golden.py — 진짜 git 으로 golden/ 을 만든다 (SPEC.md §16.2).

    python3 tools/make_golden.py            # golden/ 을 새로 만든다
    python3 tools/make_golden.py --check    # 다시 만들어 지금 것과 대조

다섯 언어의 시험은 전부 여기서 나온 바이트와 견준다. 그래서 이
스크립트에는 기대값을 만드는 **계산이 없다** — 입력
(tools/golden_cases.py)을 진짜 git 2.55.0 에 넣고 git 이 낸 것을
받아 적을 뿐이다. 유일한 예외는 SPEC 이 정한 줄임을 기대 출력에
옮기는 일(§16.4 의 표)과,
stat 칸을 0 으로 지우는 인덱스 정규화(§7.3)다.

모든 저장소는 scratch/golden/ 아래에서 새로 만들고, 환경은
tools/gitenv.sh 가 정한다. 같은 git 이면 몇 번을 돌려도 같은 바이트가
나와야 한다 — --check 가 그것을 본다(인덱스 원본처럼 stat 을 품은
파일은 정규화한 뒤에 견준다).
"""
import hashlib
import io
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gitenv                                          # noqa: E402
import golden_cases as cases                           # noqa: E402

SCRATCH = os.path.join(BASE, 'scratch', 'golden')
START_DATE = 1700000000
ROWS = []          # golden.tsv 의 줄: (파일, 기대값, 만든 명령)


# ── 재료 (SPEC.md §2.1 · §16.4) ────────────────────────────────────
def unescape(s):
    """text: 재료의 이스케이프 — \\n \\t \\\\ \\" \\xHH."""
    out, i = bytearray(), 0
    raw = s.encode('utf-8')
    while i < len(raw):
        c = raw[i:i + 1]
        if c == b'\\' and i + 1 < len(raw):
            n = raw[i + 1:i + 2]
            if n == b'x':
                out.append(int(raw[i + 2:i + 4], 16))
                i += 4
                continue
            out += {b'n': b'\n', b't': b'\t'}.get(n, n)
            i += 2
            continue
        out += c
        i += 1
    return bytes(out)


def make(recipe):
    """재료 한 줄 → 바이트. O(결과 길이)."""
    kind, _, arg = recipe.partition(':')
    if kind == 'empty':
        return b''
    if kind == 'text':
        return unescape(arg)
    if kind == 'repeat':
        byte, n = arg.split(':')
        return bytes([int(byte, 16)]) * int(n)
    if kind == 'counter':
        return bytes(i % 251 for i in range(int(arg)))
    if kind == 'seq':
        a, b = (int(x) for x in arg.split(':'))
        return b''.join(b'%d\n' % i for i in range(a, b + 1))
    if kind == 'golden':
        return open(os.path.join(BASE, 'golden', arg), 'rb').read()
    raise ValueError('모르는 재료: %s' % recipe)


# ── 도우미 ─────────────────────────────────────────────────────────
class Repo:
    """scratch/golden/<이름> 에 새 저장소 하나. 진짜 git 만 부른다."""

    def __init__(self, name, env, init=True):
        self.path = os.path.join(SCRATCH, name)
        os.makedirs(self.path)
        self.env = env
        if init:
            self.git('init', '-q', '-b', 'main')

    def git(self, *args, stdin=None, date=None):
        env = self.env
        if date is not None:
            env = dict(env, GIT_AUTHOR_DATE='%d +0900' % date,
                       GIT_COMMITTER_DATE='%d +0900' % date)
        return gitenv.git(env, self.path, *args, stdin=stdin)[1]

    def write(self, rel, data, mode=0o644):
        p = os.path.join(self.path, rel)
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data)
        os.chmod(p, mode)

    def objpath(self, oid):
        return os.path.join(self.path, '.git', 'objects',
                            oid[:2], oid[2:])


def out(rel, data, expect='', how=''):
    """golden/<rel> 에 쓴다. 바이트든 글자든."""
    p = os.path.join(GOLDEN, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(data, str):
        data = data.encode('utf-8')
    with open(p, 'wb') as f:
        f.write(data)
    if how:
        ROWS.append((rel, expect, how))


def tsv(rows):
    return ''.join('\t'.join(str(c) for c in r) + '\n' for r in rows)


# ── §2 SHA-1 ───────────────────────────────────────────────────────
def g_sha1(env):
    """입력 그대로의 SHA-1 은 coreutils sha1sum, blob 이름은 git."""
    r = Repo('sha1', env)
    rows = [('name', 'len', 'recipe', 'sha1', 'blob')]
    for name, recipe in cases.SHA1_VECTORS:
        data = make(recipe)
        s = subprocess.run(['sha1sum'], input=data, check=True,
                           stdout=subprocess.PIPE).stdout.split()[0]
        blob = r.git('hash-object', '--stdin', stdin=data).strip()
        rows.append((name, len(data), recipe, s.decode(),
                     blob.decode()))
    out('sha1.tsv', tsv(rows), '%d벡터' % (len(rows) - 1),
        'sha1sum · git hash-object --stdin')


# ── §3·§4 느슨한 객체 ───────────────────────────────────────────────
def g_objects(env):
    """git 이 쓴 느슨한 객체 파일을 바이트 그대로 가져온다.

    큰 글은 동적 허프만 블록(BTYPE=10)으로 눌리고 짧은 글은 고정
    허프만(BTYPE=01)으로 눌린다 — C++ 의 손 inflate 가 둘 다
    풀어야 한다.
    """
    r = Repo('objects', env)
    r.write('hello.txt', b'hello\n')
    words = b'git stores snapshots not differences '
    r.write('big.txt', b''.join(words[i % 7:] + b'%d\n' % i
                                for i in range(600)))
    r.write('src/a.py', b'print(1)\n')
    r.git('add', '.')
    r.git('commit', '-q', '-m', 'objects')
    r.git('tag', '-a', 'v1', '-m', 'tag message')
    rows = [('id', 'type', 'size', 'btype', 'what')]
    listing = r.git('rev-list', '--objects', '--all').decode()
    listing = listing.split('\n')
    tag = r.git('rev-parse', 'v1').decode().strip()
    ids = set([tag] + [l.split(' ')[0] for l in listing if l])
    for oid in sorted(ids):
        t = r.git('cat-file', '-t', oid).decode().strip()
        size = r.git('cat-file', '-s', oid).decode().strip()
        raw = open(r.objpath(oid), 'rb').read()
        btype = (raw[2] >> 1) & 3            # 첫 deflate 블록의 BTYPE
        what = {l.split(' ')[0]: l.partition(' ')[2]
                for l in listing if l}.get(oid, '') or t
        out('objects/%s' % oid, raw)
        rows.append((oid, t, size, btype, what))
    out('objects/objects.tsv', tsv(rows), '%d객체' % (len(rows) - 1),
        'git cat-file -t/-s · .git/objects 파일 복사')


def stored_zlib(data):
    """SPEC.md §3.1 의 C++ 이 쓸 꼴 — 저장 블록만, 65,535바이트씩."""
    parts = [data[i:i + 65535]
             for i in range(0, len(data), 65535)] or [b'']
    body = bytearray(b'\x78\x01')
    for k, p in enumerate(parts):
        body.append(1 if k == len(parts) - 1 else 0)
        body += struct.pack('<HH', len(p), len(p) ^ 0xffff) + p
    adler = zlib.adler32(data) & 0xffffffff
    return bytes(body) + struct.pack('>I', adler)


def g_stored(env):
    """저장 블록으로 싼 객체를 진짜 git 이 읽는가 (SPEC.md §3.1).

    C++ 구현이 생기기 전에, 그 꼴이 git 에게 받아들여진다는 것부터
    확인해 둔다. 여기 만든 파일은 C++ 의 시험이 바이트까지 견준다.
    """
    r = Repo('stored', env)
    items = [('blob', b'stored\n'), ('blob', b''),
             ('blob', bytes(i % 251 for i in range(70000)))]
    log = []
    for typ, body in items:
        full = b'%s %d\0' % (typ.encode(), len(body)) + body
        oid = hashlib.sha1(full).hexdigest()
        raw = stored_zlib(full)
        os.makedirs(os.path.dirname(r.objpath(oid)), exist_ok=True)
        open(r.objpath(oid), 'wb').write(raw)
        out('stored/%s' % oid, raw)
        t = r.git('cat-file', '-t', oid).decode().strip()
        s = r.git('cat-file', '-s', oid).decode().strip()
        log.append('%s %s %s' % (oid, t, s))
    tree_body = b''.join(b'100644 f%d\0' % k + bytes.fromhex(l[:40])
                         for k, l in enumerate(log))
    full = b'tree %d\0' % len(tree_body) + tree_body
    toid = hashlib.sha1(full).hexdigest()
    os.makedirs(os.path.dirname(r.objpath(toid)), exist_ok=True)
    open(r.objpath(toid), 'wb').write(stored_zlib(full))
    out('stored/%s' % toid, stored_zlib(full))
    ls = r.git('ls-tree', toid).decode()
    fsck = gitenv.git(env, r.path, 'fsck', '--strict', '--no-dangling',
                      '--no-progress', check=False)
    text = ('\n'.join(log) + '\n$ git ls-tree %s\n%s'
            '$ git fsck --strict\nexit=%d\n' % (toid, ls, fsck[0]))
    out('stored_ok.txt', text, 'fsck exit=%d' % fsck[0],
        'git cat-file · ls-tree · fsck --strict')


# ── §4.3 트리 ──────────────────────────────────────────────────────
def g_trees(env):
    """경우마다 (모드·blob·경로) 목록과 git write-tree 의 이름."""
    rows = [('case', 'tree')]
    for name, files in cases.TREE_CASES:
        r = Repo('tree-' + name, env)
        for path, recipe, mode in files:
            r.write(path, make(recipe), 0o755 if mode == 755 else 0o644)
        r.git('add', '.')
        tree = r.git('write-tree').decode().strip()
        stage = r.git('ls-files', '--stage', '-z').decode()
        ents = [e for e in stage.split('\0') if e]
        body = ''
        for e in ents:
            head, path = e.split('\t', 1)
            mode, oid = head.split(' ')[:2]
            body += '%s\t%s\t%s\n' % (mode, oid, path)
        out('trees/%s.tsv' % name, '# mode\tblob\tpath\n' + body)
        out('trees/%s.ls' % name,
            r.git('ls-tree', '-r', '-t', tree).decode())
        rows.append((name, tree))
    out('trees/trees.tsv', tsv(rows), '%d트리' % (len(rows) - 1),
        'git add · write-tree · ls-tree -r -t')


# ── §7 인덱스 ──────────────────────────────────────────────────────
def normalize_index(data):
    """SPEC.md §7.3 — 항목마다 0‥23·28‥35 를 0 으로, 끝 SHA-1 새로."""
    ver = struct.unpack('>I', data[4:8])[0]
    n = struct.unpack('>I', data[8:12])[0]
    buf = bytearray(data[:-20])
    pos = 12
    for _ in range(n):
        buf[pos:pos + 24] = bytes(24)
        buf[pos + 28:pos + 36] = bytes(8)
        flags = struct.unpack('>H', data[pos + 60:pos + 62])[0]
        extra = 2 if (ver >= 3 and flags & 0x4000) else 0
        namelen = flags & 0xfff
        pos += (62 + extra + namelen + 8) // 8 * 8
    return bytes(buf) + hashlib.sha1(bytes(buf)).digest()


def g_index(env):
    """git 이 쓴 인덱스 세 가지 — 확장 없음, TREE 확장, 판 3."""
    r = Repo('index', env)
    r.write('hello.txt', b'hello\n')
    r.write('run.sh', b'#!/bin/sh\n', 0o755)
    r.write('src/a.py', b'print(1)\n')
    r.write('한글.txt', '가\n'.encode())
    r.git('add', '.')
    idx = os.path.join(r.path, '.git', 'index')
    plain = open(idx, 'rb').read()
    out('index/plain.raw', plain)
    out('index/plain.bin', normalize_index(plain), 'stat 0 으로 정규화',
        'git add . (확장 없음)')
    out('index/ls-stage.txt', r.git('ls-files', '--stage').decode())
    r.git('commit', '-q', '-m', 'c')
    tree = open(idx, 'rb').read()
    assert b'TREE' in tree
    out('index/tree-ext.raw', tree, 'TREE 확장 포함', 'git commit')
    r.git('update-index', '--skip-worktree', 'run.sh')
    v3 = open(idx, 'rb').read()
    assert struct.unpack('>I', v3[4:8])[0] == 3
    out('index/v3.raw', v3, '판 3 · skip-worktree',
        'git update-index --skip-worktree run.sh')


# ── §10 역사 두 벌 ─────────────────────────────────────────────────
def copy_gitdir(repo, dest):
    """.git 의 HEAD·refs·objects(느슨한 것)·logs 를 golden 으로."""
    src = os.path.join(repo.path, '.git')
    for sub in ('HEAD', 'refs', 'objects', 'logs'):
        s = os.path.join(src, sub)
        for root, dirs, files in os.walk(s) if os.path.isdir(s) else [
                (src, [], [sub])]:
            dirs.sort()
            for f in sorted(files):
                p = os.path.join(root, f)
                rel = os.path.relpath(p, src)
                if rel.startswith('objects/info') or \
                        rel.startswith('objects/pack'):
                    continue
                out('%s/git/%s' % (dest, rel), open(p, 'rb').read())


def build_dag(env, name, dates):
    """10.1 의 역사: A B | C D (main) · E F (t) · M1 · G(main) H(t)
    · M2 · I.

    dates=False 면 모든 커밋의 날짜가 같다(차례 규칙이 전부를 정한다).
    """
    r = Repo(name, env)
    tick = [START_DATE]

    def d():
        if dates:
            tick[0] += 60
        return tick[0]

    def c(msg):
        r.write('f_' + msg, msg.encode() + b'\n')
        r.git('add', 'f_' + msg)
        r.git('commit', '-q', '-m', msg, date=d())
    for m in 'AB':
        c(m)
    r.git('branch', 't')
    c('C'), c('D')
    r.git('switch', '-q', 't')
    c('E'), c('F')
    r.git('switch', '-q', 'main')
    r.git('merge', '-q', '--no-edit', 't', date=d())
    c('G')
    r.git('switch', '-q', 't')
    c('H')
    r.git('switch', '-q', 'main')
    r.git('merge', '-q', '--no-edit', 't', date=d())
    c('I')
    return r


def build_criss_cross(env):
    """criss-cross — 가장 좋은 공통 조상이 둘. 날짜는 모두 다르다."""
    r = Repo('dag-criss', env)
    tick = [START_DATE]

    def d():
        tick[0] += 60
        return tick[0]

    def c(msg):
        r.write('f_' + msg, msg.encode() + b'\n')
        r.git('add', 'f_' + msg)
        r.git('commit', '-q', '-m', msg, date=d())
    c('R')
    r.git('branch', 'b')
    c('A1')
    r.git('switch', '-q', 'b')
    c('B1')
    r.git('switch', '-q', 'main')
    r.git('merge', '-q', '--no-edit', 'b~0', date=d())
    r.git('switch', '-q', 'b')
    r.git('merge', '-q', '--no-edit', 'main~1', date=d())
    c('B2')
    r.git('switch', '-q', 'main')
    c('A2')
    return r


def g_dag(env):
    for name, r in (('equal', build_dag(env, 'dag-equal', False)),
                    ('dated', build_dag(env, 'dag-dated', True)),
                    ('criss', build_criss_cross(env))):
        copy_gitdir(r, 'dag/' + name)
        txt = ''
        for args in (('log', '--oneline'), ('log', '--oneline', 't'),
                     ('log',), ('merge-base', '--all', 'main', 't'),
                     ('merge-base', 'main', 't'),
                     ('merge-base', '--all', 'main', 'b'),
                     ('merge-base', 'main', 'b')):
            code, so, _ = gitenv.git(env, r.path, *args, check=False)
            if code == 128:
                continue                   # 그 저장소에 없는 브랜치
            txt += '$ git %s\n%s= %d\n' % (' '.join(args), so.decode(),
                                          code)
        out('dag/%s/expect.txt' % name, txt, '%s 역사의 log·merge-base'
            % name, 'git log · merge-base')


# ── §13 팩 ─────────────────────────────────────────────────────────
PACK_CFG = ('-c', 'pack.threads=1', '-c', 'pack.window=10',
            '-c', 'pack.depth=50')


def g_pack(env):
    """델타가 든 팩 둘 — OFS_DELTA(repack) 와 REF_DELTA(pack-objects).

    한 파일이 여섯 판을 거치게 해 델타 사슬이 생기게 한다. 팩은 둘 다
    진짜 git 이 쓴 바이트 그대로이고, verify-pack -v · show-index 의
    출력이 시험의 답이다. 팩 결정론은 PACK_CFG(스레드 하나)로 얻는다.
    """
    r = Repo('pack', env)
    body = b''.join(b'line %d of a file that keeps growing\n' % i
                    for i in range(1, 121))
    for v in range(6):
        r.write('grow.txt', body + b''.join(b'extra %d.%d\n' % (v, k)
                                            for k in range(v * 3)))
        r.write('v.txt', b'version %d\n' % v)
        r.git('add', '.')
        r.git('commit', '-q', '-m', 'v%d' % v, date=START_DATE + 60 * v)
    r.git(*PACK_CFG, 'repack', '-a', '-d', '-f', '-q')
    pdir = os.path.join(r.path, '.git', 'objects', 'pack')
    base = [x for x in os.listdir(pdir) if x.endswith('.pack')][0][:-5]
    work = os.path.join(SCRATCH, 'pack-files')
    os.makedirs(work)
    for ext in ('pack', 'idx'):
        shutil.copy(os.path.join(pdir, base + '.' + ext),
                    os.path.join(work, 'ofs.' + ext))
    objs = r.git('rev-list', '--objects', '--all')
    ids = b''.join(l.split(b' ')[0] + b'\n'
                   for l in objs.split(b'\n') if l)
    p = subprocess.run(['git'] + list(PACK_CFG) +
                       ['pack-objects', os.path.join(work, 'ref')],
                       cwd=r.path, env=env, input=ids, check=True,
                       stdout=subprocess.PIPE)
    sha = p.stdout.decode().strip()
    for ext in ('pack', 'idx'):
        os.rename(os.path.join(work, 'ref-%s.%s' % (sha, ext)),
                  os.path.join(work, 'ref.' + ext))
    for name in ('ofs', 'ref'):
        for ext in ('pack', 'idx'):
            f = os.path.join(work, '%s.%s' % (name, ext))
            out('pack/%s.%s' % (name, ext), open(f, 'rb').read())
        idx = os.path.join(work, name + '.idx')
        vp = gitenv.git(env, work, 'verify-pack', '-v',
                        name + '.idx')[1]
        out('pack/%s.verify' % name, vp, 'verify-pack -v',
            'git verify-pack -v %s.idx' % name)
        si = subprocess.run(['git', 'show-index'], cwd=work, env=env,
                            stdin=open(idx, 'rb'),
                            stdout=subprocess.PIPE, check=True).stdout
        out('pack/%s.show-index' % name, si, '색인 항목(자리 이름 crc)',
            'git show-index < %s.idx' % name)
    src = [('commit', 'grow.txt lines', 'v.txt')]
    src += [('v%d' % v, 120 + v * 3, 'version %d' % v)
            for v in range(6)]
    out('pack/source.tsv', tsv(src))


# ── §11 diff 쌍 ────────────────────────────────────────────────────
def g_diff(env):
    """쌍마다 두 파일과 git 의 출력. 목록 둘(SPEC.md §11.2).

    agree 는 mygit 이 바이트까지 같아야 하는 쌍, tie 는 git 이 같은
    길이의 다른 스크립트를 고르는 것으로 알려진 쌍이다. 어느
    쪽인지는 입력과 함께 golden_cases.py 에 적혀 있고, 그 분류가
    맞는지는 부록 A 8단계의 Python 시험이 처음으로 확인한다.
    """
    work = os.path.join(SCRATCH, 'diff')
    os.makedirs(work)
    for listname, pairs in (('agree', cases.DIFF_PAIRS),
                            ('tie', cases.DIFF_TIE_PAIRS)):
        rows = [('name', 'minus', 'plus', 'exit')]
        for k, (name, a, b) in enumerate(pairs, 1):
            stem = '%s-%02d-%s' % (listname, k, name)
            fa, fb = stem + '.a', stem + '.b'
            for f, data in ((fa, a), (fb, b)):
                open(os.path.join(work, f), 'wb').write(data)
                out('diff/' + f, data)
            code, so, _ = gitenv.git(
                env, work, '-c', 'diff.indentHeuristic=false', 'diff',
                '--no-index', fa, fb, check=False)
            out('diff/%s.diff' % stem, so)
            body = [l for l in so.split(b'\n') if not l.startswith(
                (b'---', b'+++'))]
            minus = sum(1 for l in body if l.startswith(b'-'))
            plus = sum(1 for l in body if l.startswith(b'+'))
            rows.append((stem, minus, plus, code))
        n = len(rows) - 1
        out('diff/%s.tsv' % listname, tsv(rows), '%d쌍' % n,
            'git -c diff.indentHeuristic=false diff --no-index a b')


# ── §14 pkt-line 대화 ──────────────────────────────────────────────
def pkt(data):
    return b'%04x' % (len(data) + 4) + data


def render(data):
    """SPEC.md §14.3 의 기록 꼴 — 길이 4자리 + repr 식 이스케이프."""
    return '%04x%s' % (len(data) + 4, repr(data)[2:-1])


class Talk:
    """git upload-pack 과 v2 로 말하는 최소 클라이언트(SPEC.md §14.3).

    기대값을 계산하려는 것이 아니다 — SPEC 이 정한 요청을 그대로 보내고
    진짜 git 이 무엇을 돌려주는지 받아 적으려는 것이다.
    """

    def __init__(self, env, path):
        self.p = subprocess.Popen(
            ['git', 'upload-pack', path], env=dict(env, GIT_PROTOCOL=
                                                   'version=2'),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.log = []
        self.pack = bytearray()

    def send(self, items):
        buf = b''
        for it in items:
            if it in (b'0000', b'0001'):
                self.log.append('> ' + it.decode())
                buf += it
            else:
                self.log.append('> ' + render(it))
                buf += pkt(it)
        self.p.stdin.write(buf)
        self.p.stdin.flush()

    def read(self, sideband=False):
        """flush 까지의 패킷들. 사이드밴드 1 은 팩으로 모은다."""
        lines = []
        while True:
            n = int(self.p.stdout.read(4), 16)
            if n in (0, 1, 2):
                self.log.append('< %04x' % n)
                if n == 0:
                    return lines
                continue
            data = self.p.stdout.read(n - 4)
            if sideband and data[:1] == b'\x01':
                self.pack += data[1:]
                self.log.append('< %04x [pack %d bytes]' % (n, n - 5))
                continue
            self.log.append('< ' + render(data))
            if data == b'packfile\n':
                sideband = True
            lines.append(data)

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def fetch(env, src, refs, haves):
    t = Talk(env, src)
    t.read()                                   # 능력 광고
    t.send([b'command=ls-refs\n', b'object-format=sha1\n', b'0001',
             b'peel\n', b'symrefs\n'] +
            [b'ref-prefix %s\n' % r.encode() for r in refs] + [b'0000'])
    adv = {}
    for l in t.read():
        oid, name = l.decode().rstrip('\n').split(' ')[:2]
        adv[name] = oid
    wants = []
    for r in refs:
        if adv[r] not in wants:
            wants.append(adv[r])
    t.send([b'command=fetch\n', b'object-format=sha1\n', b'0001',
            b'ofs-delta\n', b'no-progress\n'] +
           [b'want %s\n' % w.encode() for w in wants] +
           [b'have %s\n' % h.encode() for h in haves] +
           [b'done\n', b'0000'])
    t.read()
    t.close()
    stdout = ''.join('%s %s\n' % (adv[r], r) for r in refs)
    return '\n'.join(t.log) + '\n', bytes(t.pack), stdout


def g_pkt(env):
    r = Repo('pkt-src', env)
    for v in range(3):
        r.write('f.txt', b'version %d\n' % v)
        r.git('add', '.')
        r.git('commit', '-q', '-m', 'v%d' % v, date=START_DATE + 60 * v)
        if v == 0:
            first = r.git('rev-parse', 'HEAD').decode().strip()
            r.git('branch', 'old')
    r.git('tag', '-a', 'v1', '-m', 'tag', date=START_DATE + 200)
    copy_gitdir(r, 'pkt/src')
    for name, refs, haves in (('full', ['refs/heads/main'], []),
                              ('two-refs', ['refs/heads/main',
                                            'refs/heads/old'], []),
                              ('have-first', ['refs/heads/main'],
                               [first])):
        log, pack, stdout = fetch(env, r.path, refs, haves)
        out('pkt/%s.log' % name, log, 'upload-pack 과의 대화',
            'git upload-pack (GIT_PROTOCOL=version=2)')
        out('pkt/%s.pack' % name, pack)
        out('pkt/%s.stdout' % name, stdout)
        out('pkt/%s.args' % name, ' '.join(refs) + '\n' +
            ' '.join(haves) + '\n')


# ── §16.4 장면 ─────────────────────────────────────────────────────
MYGIT_MERGE = 'Merge made by mygit (3-way, no renames).'
ORT = "Merge made by the 'ort' strategy."


def split_args(line):
    """공백으로 가르고 "…" 는 한 덩어리(안의 \\" \\\\ \\n 은
    이스케이프)."""
    args, cur, i, quoted = [], None, 0, False
    while i < len(line):
        c = line[i]
        if quoted:
            if c == '\\' and i + 1 < len(line):
                nxt = line[i + 1]
                cur += {'n': '\n', 't': '\t'}.get(nxt, nxt)
                i += 2
                continue
            if c == '"':
                quoted = False
            else:
                cur += c
        elif c == '"':
            quoted, cur = True, cur or ''
        elif c.isspace():
            if cur is not None:
                args.append(cur)
                cur = None
        else:
            cur = (cur or '') + c
        i += 1
    if cur is not None:
        args.append(cur)
    return args


def to_git(args, cwd):
    """mygit 명령 → 실제로 부를 git 인자 (SPEC.md §16.4 의 표).

    init 의 -b main 은 새로 만들 때만 붙인다 — 이미 있는 저장소에
    붙이면 git 이 "re-init: ignored --initial-branch" 경고를 더 낸다.
    """
    if args[0] == 'init':
        where = os.path.join(cwd, *(args[1:2] or ['.']))
        if os.path.isdir(os.path.join(where, '.git')):
            return args
        return ['init', '-b', 'main'] + args[1:]
    if args[0] == 'status':
        return ['status', '--porcelain'] + args[1:]
    if args[0] == 'diff':
        pre = ['-c', 'diff.indentHeuristic=false', 'diff']
        revs = [a for a in args[1:] if not a.startswith('-')]
        if len(revs) == 2 and '--no-index' not in args:
            pre.append('--no-renames')
        return pre + args[1:]
    return args


def trim(cmd, text):
    """SPEC 의 줄임을 기대 출력에 옮긴다 — 그 밖에는 손대지 않는다."""
    lines = text.split('\n')
    if cmd == 'commit' and text:
        return lines[0] + '\n'
    if cmd == 'merge':
        if 'Fast-forward' in lines:
            k = lines.index('Fast-forward') + 1
            return '\n'.join(lines[:k]) + '\n'
        if ORT in lines:
            keep = lines[:lines.index(ORT)] + [MYGIT_MERGE]
            return '\n'.join(keep) + '\n'
    if cmd == 'reflog':
        return text.replace(ORT, MYGIT_MERGE)
    return text


def expect_lines(prefix, text):
    if not text:
        return []
    body = text[:-1] if text.endswith('\n') else text
    rows = [prefix + l for l in body.split('\n')]
    if not text.endswith('\n'):
        rows.append('%noeol')
    return rows


def run_scenario(env, name, script):
    root = os.path.join(SCRATCH, 'scen-' + name)
    os.makedirs(root)
    env = dict(env, GIT_CEILING_DIRECTORIES=os.path.dirname(root))
    date, cwd = START_DATE, root
    rec = ['# 장면 %s — tools/golden_cases.py 의 명령을 진짜 git 2.55.0'
           ' 으로 돌려 채웠다.' % name, '# 손으로 고치지 말 것 '
           '(SPEC.md §16.4). 다시 만들기: make golden', '']
    for line in script.strip('\n').split('\n'):
        rec.append(line)
        if not line.strip() or line.startswith('#'):
            continue
        a = split_args(line)
        if a[0] == '@date':
            date = int(a[1])
            continue
        if a[0] == '@cd':
            cwd = os.path.normpath(os.path.join(root, a[1]))
            continue
        path = os.path.join(cwd, a[1]) if len(a) > 1 else None
        if a[0] in ('write', 'append'):
            if len(a) != 3:
                raise ValueError('재료에 공백이 있다(\\x20 을 쓸 것):'
                                 ' %s' % line)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'ab' if a[0] == 'append' else 'wb') as f:
                f.write(make(a[2]))
            continue
        if a[0] == 'chmod':
            os.chmod(path, int(a[2], 8))
            continue
        if a[0] == 'rm':
            os.remove(path)
            continue
        if a[0] == 'mkdir':
            os.makedirs(path, exist_ok=True)
            continue
        e = dict(env, GIT_AUTHOR_DATE='%d +0900' % date,
                 GIT_COMMITTER_DATE='%d +0900' % date)
        if a[0] == 'cat':
            so, se, code = open(path, 'rb').read(), b'', 0
        else:
            if a[0] == 'mygit':
                gargs = to_git(a[1:], cwd)
            elif a[0] == 'stage':
                gargs = ['ls-files', '--stage']
            elif a[0] == 'ref':
                gargs = ['rev-parse', a[1]]
            else:
                raise ValueError('모르는 장면 줄: %s' % line)
            code, so, se = gitenv.git(e, cwd, *gargs, stdin=b'',
                                      check=False)
        so = so.decode('utf-8').replace(root, '<ROOT>')
        se = se.decode('utf-8').replace(root, '<ROOT>')
        if a[0] == 'mygit':
            so = trim(a[1], so)
        rec += expect_lines('> ', so) + expect_lines('! ', se)
        if code:
            rec.append('= %d' % code)
    out('scen/%s.scn' % name, '\n'.join(rec) + '\n', '장면 기대 출력',
        'tools/golden_cases.py 의 명령을 git 으로')
    return rec


def g_scenarios(env):
    errs = [('command', 'stderr-first-line', 'exit')]
    for name in sorted(cases.SCENARIOS):
        rec = run_scenario(env, name, cases.SCENARIOS[name])
        if name != 'errors':
            continue
        for i, l in enumerate(rec):
            if not l.startswith('mygit '):
                continue
            nxt = rec[i + 1:]
            end = next((k for k, x in enumerate(nxt)
                        if not x[:2] in ('> ', '! ', '= ')), len(nxt))
            block = nxt[:end]
            errs_ = [x[2:] for x in block if x.startswith('! ')]
            codes = [x[2:] for x in block if x.startswith('= ')]
            first = errs_[0] if errs_ else ''
            code = codes[0] if codes else '0'
            if code != '0':
                errs.append((l[6:], first, code))
    out('errors.tsv', tsv(errs), '%d오류' % (len(errs) - 1),
        'errors 장면에서 뽑음')


# ── 전체 ───────────────────────────────────────────────────────────
STEPS = [g_sha1, g_objects, g_stored, g_trees, g_index, g_dag, g_diff,
         g_pack, g_pkt, g_scenarios]


def build(target):
    global GOLDEN
    GOLDEN = target
    del ROWS[:]
    if os.path.isdir(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    if os.path.isdir(target):
        shutil.rmtree(target)
    os.makedirs(target)
    env = gitenv.load(os.path.join(SCRATCH, 'home'))
    ver = gitenv.git(env, SCRATCH, '--version')[1].decode().strip()
    for step in STEPS:
        step(env)
    out('golden.tsv', '# %s · tools/make_golden.py 가 만든다\n' % ver
        + tsv([('file', 'expect', 'how')] + ROWS))


def comparable(rel, data):
    """--check 에서 견줄 바이트. stat 을 품은 인덱스 원본은
    정규화한다."""
    if rel.startswith('index/') and rel.endswith('.raw'):
        return normalize_index(data)
    return data


def main(argv):
    if '--check' not in argv:
        build(os.path.join(BASE, 'golden'))
        print('golden/ — %d개 기록' % len(ROWS))
        return 0
    fresh = os.path.join(SCRATCH + '-check')
    build(fresh)
    old = os.path.join(BASE, 'golden')
    bad = []
    names = set()
    for top in (old, fresh):
        for root, _d, files in os.walk(top):
            for f in files:
                names.add(os.path.relpath(os.path.join(root, f), top))
    for rel in sorted(names):
        a, b = os.path.join(old, rel), os.path.join(fresh, rel)
        if not (os.path.exists(a) and os.path.exists(b)):
            bad.append('%s — 한쪽에만 있다' % rel)
        elif comparable(rel, open(a, 'rb').read()) != \
                comparable(rel, open(b, 'rb').read()):
            bad.append('%s — 진짜 git 이 이제 다르게 낸다' % rel)
    shutil.rmtree(fresh)
    for line in bad:
        print('  ✗ ' + line)
    print('golden/ 파일 %d개 — 어긋남 %d건' % (len(names), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
