# -*- coding: utf-8 -*-
"""객체 (SPEC.md §4.1 · §4.6) — 이름은 내용의 SHA-1 이다.

이름 = SHA-1("<형식> <크기>\\0" + 몸). 같은 내용은 어느 저장소에서
누가 만들어도 같은 이름을 얻는다 — git 이 "내용 주소 저장소" 인
까닭이 이 한 줄이다. 느슨한 객체는 그 바이트를 zlib 으로 눌러
.git/objects/<앞 2글자>/<나머지 38글자> 에 둔다.

팩 안의 객체는 11단계에서 read_object 가 함께 찾게 된다.
"""
import os
import tempfile

from mygit import GitError, zlib
from mygit.sha1 import sha1_hex

TYPES = ('blob', 'tree', 'commit', 'tag')


def header(type_, body):
    return b'%s %d\0' % (type_.encode(), len(body))


def hash_object(type_, body):
    """객체 이름(16진 40글자). 저장소를 건드리지 않는다."""
    return sha1_hex(header(type_, body) + body)


def object_path(gitdir, oid):
    return os.path.join(gitdir, 'objects', oid[:2], oid[2:])


def write_object(gitdir, type_, body):
    """느슨한 객체 하나를 쓰고 이름을 돌려준다.

    이미 있으면 아무것도 하지 않는다 — 이름이 같으면 내용도 같기
    때문이다(0444 라 덮어쓰려 하면 실패하기도 한다). 임시 파일에 다
    쓴 뒤 이름을 바꿔 넣어, 도중에 죽어도 반쯤 쓴 객체가 남지 않는다.
    """
    oid = hash_object(type_, body)
    path = object_path(gitdir, oid)
    if os.path.exists(path):
        return oid
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='tmp_obj_')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(zlib.compress(header(type_, body) + body))
        os.chmod(tmp, 0o444)
        os.rename(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return oid


def parse_raw(raw, oid):
    """풀린 바이트 → (형식, 몸). 머리의 크기가 몸과 다르면 오류."""
    head, sep, body = raw.partition(b'\0')
    parts = head.split(b' ')
    if not sep or len(parts) != 2 or not parts[1].isdigit():
        raise GitError('fatal: mygit: bad object header in %s' % oid)
    type_ = parts[0].decode('ascii', 'replace')
    if type_ not in TYPES or int(parts[1]) != len(body):
        raise GitError('fatal: mygit: object %s is corrupt' % oid)
    return type_, body


def read_object(gitdir, oid):
    """(형식, 몸). 없으면 GitError."""
    path = object_path(gitdir, oid)
    if not os.path.exists(path):
        raise GitError('fatal: mygit: object %s not found' % oid)
    with open(path, 'rb') as f:
        return parse_raw(zlib.decompress(f.read()), oid)


def all_loose(gitdir):
    """느슨한 객체의 이름 전부. objects/xx/ 디렉터리를 훑는다."""
    root = os.path.join(gitdir, 'objects')
    out = []
    for d in sorted(os.listdir(root)):
        if len(d) != 2:
            continue
        for f in sorted(os.listdir(os.path.join(root, d))):
            if len(f) == 38:
                out.append(d + f)
    return out


def find_object(gitdir, prefix):
    """앞부분(4글자 이상)으로 찾는다: 하나면 그 이름, 없으면 None.

    둘 이상이면 git 처럼 모호하다고 멈춘다. 4글자보다 짧으면 찾지
    않는다(git 의 최소 줄임 길이와 같다). O(느슨한 객체 수).
    """
    p = prefix.lower()
    if len(p) < 4 or any(c not in '0123456789abcdef' for c in p):
        return None
    if len(p) == 40:
        return p if os.path.exists(object_path(gitdir, p)) else None
    hits = [o for o in all_loose(gitdir) if o.startswith(p)]
    if len(hits) > 1:
        raise GitError('error: short object ID %s is ambiguous'
                       % prefix)
    return hits[0] if hits else None
