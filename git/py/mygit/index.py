# -*- coding: utf-8 -*-
"""인덱스 (SPEC.md §7) — .git/index, 다음 커밋이 될 트리의 초안.

작업 트리와 저장소 사이의 이 파일 하나가 "스테이징" 의 실체다.
항목마다 경로·모드·blob 이름과 함께 파일의 stat 칸(시각·크기·inode)
을 적어 두는데, git 은 그것으로 "안 바뀐 파일" 을 해시 없이 가려낸다.
mygit 은 칸을 채워 두기만 하고 자신은 믿지 않는다(§7.2) — 늘 해시한다.

판 2 로 쓰고, 판 2·3 을 읽는다. 확장(TREE·REUC…)은 읽을 때 건너뛰고
쓰지 않는다. 수는 전부 빅 엔디언.
"""
import os
import struct

from mygit import GitError
from mygit.sha1 import Sha1, sha1

ENTRY = struct.Struct('>10I20sH')      # 62바이트: stat 10칸·이름·flags
MAX_NAME = 0xfff


class IndexEntry(object):
    """인덱스 항목 하나. 경로는 bytes, 이름은 16진 40글자."""

    def __init__(self, path, oid, mode, stage=0, size=0):
        self.path, self.oid, self.mode = path, oid, mode
        self.stage, self.size = stage, size
        self.ctime_s = self.ctime_ns = self.mtime_s = self.mtime_ns = 0
        self.dev = self.ino = self.uid = self.gid = 0
        self.assume_valid = self.skip_worktree = False

    def key(self):
        return (self.path, self.stage)


def entry_from_stat(path, abspath, oid):
    """작업 트리 파일의 stat 으로 항목을 채운다(SPEC.md §7.2).

    모드는 소유자 실행 비트만 본다 — git 과 같다(그룹·기타는 버린다).
    dev·ino·size 는 32비트로 자른다.
    """
    st = os.stat(abspath)
    mode = 0o100755 if st.st_mode & 0o100 else 0o100644
    e = IndexEntry(path, oid, mode, 0, st.st_size & 0xffffffff)
    e.ctime_s, e.ctime_ns = divmod(st.st_ctime_ns, 10 ** 9)
    e.mtime_s, e.mtime_ns = divmod(st.st_mtime_ns, 10 ** 9)
    e.dev, e.ino = st.st_dev & 0xffffffff, st.st_ino & 0xffffffff
    e.uid, e.gid = st.st_uid & 0xffffffff, st.st_gid & 0xffffffff
    return e


def parse_index(data):
    """인덱스 바이트 → [IndexEntry]. 끝 SHA-1 이 틀리면 오류.

    판 3 은 flags 의 비트 14 가 서 있는 항목 뒤에 2바이트 확장
    flags 가 더 있다(skip-worktree 가 거기 산다). O(파일 크기).
    """
    if len(data) < 32 or data[:4] != b'DIRC':
        raise GitError('fatal: mygit: index file corrupt')
    if sha1(data[:-20]) != data[-20:]:
        raise GitError('fatal: mygit: index file corrupt')
    ver, count = struct.unpack('>II', data[4:12])
    if ver == 4:
        raise GitError('fatal: mygit: index v4 unsupported')
    if ver not in (2, 3):
        raise GitError('fatal: mygit: index version %d' % ver)
    out, pos = [], 12
    for _ in range(count):
        f = ENTRY.unpack_from(data, pos)
        flags = f[11]
        e = IndexEntry(None, f[10].hex(), f[6], (flags >> 12) & 3, f[9])
        (e.ctime_s, e.ctime_ns, e.mtime_s, e.mtime_ns, e.dev,
         e.ino) = f[:6]
        e.uid, e.gid = f[7], f[8]
        e.assume_valid = bool(flags & 0x8000)
        start = pos + 62
        if flags & 0x4000:                     # 판 3 의 확장 flags
            ext = struct.unpack_from('>H', data, start)[0]
            e.skip_worktree = bool(ext & 0x4000)
            start += 2
        end = data.index(b'\0', start)          # 이름 길이 0xfff 넘어도
        e.path = data[start:end]
        pos += (start - pos + len(e.path) + 8) // 8 * 8
        out.append(e)
    return out


def serialize_index(entries):
    """[IndexEntry] → 판 2 인덱스 바이트. 경로·단계 차례로 정렬한다.

    항목 길이 = (62 + 이름 길이 + 8) & ~7 — 이름 뒤 NUL 이 1‥8 개.
    판 2 에는 확장 flags 가 없으므로 skip-worktree 는 여기서 사라진다
    (mygit 은 그 비트를 쓰지 않는다 — 읽기만 한다).
    """
    ents = sorted(entries, key=IndexEntry.key)
    out = [b'DIRC', struct.pack('>II', 2, len(ents))]
    for e in ents:
        flags = (e.stage << 12) | min(len(e.path), MAX_NAME)
        if e.assume_valid:
            flags |= 0x8000
        rec = ENTRY.pack(e.ctime_s, e.ctime_ns, e.mtime_s, e.mtime_ns,
                         e.dev, e.ino, e.mode, e.uid, e.gid, e.size,
                         bytes.fromhex(e.oid), flags) + e.path
        out.append(rec + b'\0' * (8 - len(rec) % 8))
    body = b''.join(out)
    return body + Sha1().update(body).digest()


def read_index(gitdir):
    """.git/index 를 읽는다. 없으면(첫 add 전) 빈 목록."""
    p = os.path.join(gitdir, 'index')
    if not os.path.exists(p):
        return []
    with open(p, 'rb') as f:
        return parse_index(f.read())


def write_index(gitdir, entries):
    """index.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §7.4)."""
    p = os.path.join(gitdir, 'index')
    lock = p + '.lock'
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    except FileExistsError:
        raise GitError('fatal: mygit: unable to lock %s' % p)
    with os.fdopen(fd, 'wb') as f:
        f.write(serialize_index(entries))
    os.rename(lock, p)
