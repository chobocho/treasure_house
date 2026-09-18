# -*- coding: utf-8 -*-
"""전송 (SPEC.md §14) — 저장소끼리 객체와 참조를 나누는 법.

pkt-line 은 "길이 네 자리 16진 + 데이터" 다. 길이가 자기 4바이트를
품는 까닭은 0000(flush)·0001(delim) 같은 특별한 값을 데이터와 헷갈리지
않게 하려는 것이다. 여기에는 두 가지가 있다: 협상 없이 객체 파일을
그대로 복사하는 "멍청한" 로컬 clone, 그리고 진짜 git upload-pack 을
자식으로 띄워 프로토콜 v2 로 말하는 fetch-pack(서버는 짜지 않는다 —
PLAN.md §9 결정 8).
"""
import os
import shutil
import subprocess

from mygit import GitError, objects, pack, refs, worktree

FLUSH, DELIM = b'0000', b'0001'


def pkt_line(data):
    """데이터 → pkt-line 한 개."""
    if len(data) > 65516:
        raise GitError('fatal: mygit: pkt-line too long')
    return b'%04x' % (len(data) + 4) + data


def render(data):
    """대화 기록의 꼴(SPEC.md §14.3) — 길이 + 파이썬 repr 식
    이스케이프."""
    return '%04x%s' % (len(data) + 4, repr(bytes(data))[2:-1])


# ── 멍청한 로컬 clone (SPEC.md §14.2) ─────────────────────────────
def _src_gitdir(src):
    g = os.path.join(src, '.git')
    return g if os.path.isdir(g) else src


def clone_local(src, dst, ident):
    """src 의 객체 파일을 그대로 복사하고 참조를 세운다. → 브랜치 이름.

    협상이 없다 — 받는 쪽이 이미 가진 것도 다시 복사한다. 그래도 객체의
    이름이 곧 내용이므로 옮긴 파일은 어느 저장소에서나 같은 객체다.
    """
    sg = _src_gitdir(src)
    g = os.path.join(dst, '.git')
    for root, _dirs, files in os.walk(os.path.join(sg, 'objects')):
        rel = os.path.relpath(root, sg)
        for f in files:
            if rel.endswith('pack') and \
                    not f.endswith(('.pack', '.idx')):
                continue
            os.makedirs(os.path.join(g, rel), exist_ok=True)
            shutil.copyfile(os.path.join(root, f),
                            os.path.join(g, rel, f))
    head = refs.read_ref(sg, 'HEAD')
    branch = head[1][len('refs/heads/'):] if head[0] == 'sym' else None
    for name, oid in refs.list_refs(sg, 'refs/'):
        if name.startswith('refs/heads/'):
            local = 'refs/remotes/origin/' + name[len('refs/heads/'):]
        elif name.startswith('refs/tags/'):
            local = name
        else:
            continue
        path = os.path.join(g, local)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(oid + '\n')
    if branch is None:
        raise GitError('fatal: mygit: source HEAD is detached')
    with open(os.path.join(g, 'refs', 'remotes', 'origin', 'HEAD'),
              'w') as f:
        f.write('ref: refs/remotes/origin/%s\n' % branch)
    oid = refs.resolve_ref(sg, 'refs/heads/' + branch)
    msg = 'clone: from %s' % os.path.abspath(src)
    refs.set_head(g, 'refs/heads/' + branch)
    refs.update_ref(g, 'refs/heads/' + branch, oid, None, msg, ident)
    with open(os.path.join(g, 'config'), 'a') as f:
        f.write('[remote "origin"]\n\turl = %s\n'
                '\tfetch = +refs/heads/*:refs/remotes/origin/*\n'
                '[branch "%s"]\n\tremote = origin\n'
                '\tmerge = refs/heads/%s\n'
                % (os.path.abspath(src), branch, branch))
    worktree.checkout_tree(dst, g, None, refs.peel(g, oid, 'tree'))
    return branch


# ── fetch-pack: 프로토콜 v2 (SPEC.md §14.3) ───────────────────────
class Wire(object):
    """자식 upload-pack 과의 pkt-line 대화. 기록은 SPEC §14.3 의 꼴."""

    def __init__(self, src, env, log_path):
        e = dict(env, GIT_PROTOCOL='version=2')
        self.p = subprocess.Popen(['git', 'upload-pack', src], env=e,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
        self.log = []
        self.log_path = log_path

    def send(self, items):
        buf = b''
        for it in items:
            if it in (FLUSH, DELIM):
                self.log.append('> ' + it.decode())
                buf += it
            else:
                self.log.append('> ' + render(it))
                buf += pkt_line(it)
        self.p.stdin.write(buf)
        self.p.stdin.flush()

    def _exact(self, n):
        data = self.p.stdout.read(n)
        if len(data) != n:
            raise GitError('fatal: mygit: remote hung up unexpectedly')
        return data

    def read(self, packbuf=None):
        """flush 까지의 패킷들. packfile 절 뒤의 사이드밴드 1 은
        packbuf 로 모은다(2 는 진행 안내, 3 은 원격의 오류)."""
        lines, side = [], False
        while True:
            n = int(self._exact(4), 16)
            if n < 4:
                self.log.append('< %04x' % n)
                if n == 0:
                    return lines
                continue
            data = self._exact(n - 4)
            if side and data[:1] == b'\x01':
                packbuf += data[1:]
                self.log.append('< %04x [pack %d bytes]' % (n, n - 5))
                continue
            if side and data[:1] == b'\x03':
                raise GitError('fatal: mygit: remote error: %s'
                               % data[1:].decode('utf-8', 'replace'))
            self.log.append('< ' + render(data))
            if data == b'packfile\n':
                side = packbuf is not None
            lines.append(data)

    def close(self):
        self.p.stdin.close()
        self.p.wait()
        if self.log_path:
            with open(self.log_path, 'w', encoding='utf-8',
                      newline='\n') as f:
                f.write('\n'.join(self.log) + '\n')


def fetch_pack(gitdir, src, want_refs, env, log_path=None):
    """want_refs 를 받아 팩을 저장한다. → [(이름, 참조)]. 참조는 고치지
    않는다 — 그것은 fetch 의 일이다(SPEC.md §14.3 의 5)."""
    w = Wire(src, env, log_path)
    caps = w.read()
    if not caps or caps[0] != b'version 2\n' or \
            not any(c.startswith(b'fetch') for c in caps):
        raise GitError('fatal: mygit: server does not speak '
                       'protocol v2')
    w.send([b'command=ls-refs\n', b'object-format=sha1\n', DELIM,
            b'peel\n', b'symrefs\n'] +
           [b'ref-prefix %s\n' % r.encode() for r in want_refs] +
           [FLUSH])
    adv = {}
    for line in w.read():
        oid, name = line.decode().rstrip('\n').split(' ')[:2]
        adv[name] = oid
    wants = []
    for r in want_refs:
        if r not in adv:
            raise GitError("fatal: mygit: no such remote ref %s" % r)
        if adv[r] not in wants:
            wants.append(adv[r])
    haves = []
    for _name, oid in refs.list_refs(gitdir, 'refs/'):
        if oid not in haves:
            haves.append(oid)
    w.send([b'command=fetch\n', b'object-format=sha1\n', DELIM,
            b'ofs-delta\n', b'no-progress\n'] +
           [b'want %s\n' % o.encode() for o in wants] +
           [b'have %s\n' % o.encode() for o in haves] +
           [b'done\n', FLUSH])
    buf = bytearray()
    w.read(buf)
    w.close()
    data = bytes(buf)
    ents = pack.read_pack(data,
                          lambda o: objects.read_object(gitdir, o))
    stem = os.path.join(gitdir, 'objects', 'pack',
                        'pack-%s' % data[-20:].hex())
    os.makedirs(os.path.dirname(stem), exist_ok=True)
    with open(stem + '.pack', 'wb') as f:
        f.write(data)
    with open(stem + '.idx', 'wb') as f:
        f.write(pack.write_idx(ents, data[-20:]))
    return [(adv[r], r) for r in want_refs]
