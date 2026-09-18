# -*- coding: utf-8 -*-
"""tree (SPEC.md §4.3) — 디렉터리 하나를 객체 하나로.

항목 = "<모드> <이름>\\0<객체 이름 20바이트>". 이름과 권한은 blob 이
아니라 트리가 갖는다 — 같은 내용의 파일 둘은 blob 하나를 나눠 쓴다.

**정렬 규칙이 전부다.** 항목은 이름의 바이트로 정렬하되 하위 트리는
이름 뒤에 '/' 가 붙은 것처럼 비교한다. 규칙을 한 글자만 어겨도
내용은 같고 이름이 다른 트리가 생기고, git 은 그것을 다른 역사로 본다.

이름·경로는 bytes 로 다룬다 — SPEC 은 비교를 바이트 비교로 정했고,
파일 이름이 올바른 UTF-8 이라는 보장도 없다.
"""
from mygit import GitError, objects

DIR = '40000'


def tree_entry_key(mode, name):
    """정렬 열쇠. 하위 트리는 이름에 '/' 를 붙여 비교한다."""
    return name + b'/' if mode == DIR else name


def parse_tree(body):
    """트리 몸 → [(모드, 이름, 객체 이름 16진)]. 적힌 차례 그대로.

    O(몸의 길이). 몸이 중간에 끊기면 오류다.
    """
    out, i = [], 0
    while i < len(body):
        sp = body.find(b' ', i)
        nul = body.find(b'\0', sp + 1)
        if sp < 0 or nul < 0 or nul + 21 > len(body):
            raise GitError('fatal: mygit: corrupt tree object')
        mode = body[i:sp].decode('ascii')
        oid = body[nul + 1:nul + 21].hex()
        out.append((mode, body[sp + 1:nul], oid))
        i = nul + 21
    return out


def serialize_tree(entries):
    """[(모드, 이름, 객체 이름)] → 트리 몸. 정렬은 여기서 한다.

    모드는 앞에 0 을 붙이지 않는다 — 디렉터리는 '40000' 다섯 글자다.
    '040000' 은 cat-file -p 가 찍어 보일 때의 꼴일 뿐이다.
    """
    ents = sorted(entries, key=lambda e: tree_entry_key(e[0], e[1]))
    return b''.join(b'%s %s\0' % (m.encode(), n) + bytes.fromhex(o)
                    for m, n, o in ents)


def write_tree(gitdir, entries):
    """[(모드, blob 이름, 경로 바이트)] → 뿌리 트리 이름.

    경로를 '/' 로 나눠 디렉터리마다 트리를 짓고, 아래에서 위로 쓴다.
    blob 이 저장소에 있는지는 보지 않는다(git write-tree 는 본다 —
    이 함수를 부르는 쪽이 인덱스에 올릴 때 이미 써 두었다).
    O(항목 수 × 깊이 + 정렬).
    """
    here, subdirs = [], {}
    for mode, oid, path in entries:
        head, sep, rest = path.partition(b'/')
        if sep:
            subdirs.setdefault(head, []).append((mode, oid, rest))
        else:
            here.append((mode, head, oid))
    for name, sub in subdirs.items():
        here.append((DIR, name, write_tree(gitdir, sub)))
    return objects.write_object(gitdir, 'tree', serialize_tree(here))


def flatten_tree(gitdir, oid, prefix=b''):
    """트리를 재귀로 펼쳐 [(모드, 이름, 경로 바이트)]. 하위 트리는
    항목으로 남기지 않고 그 안을 펼친다. 차례는 트리 차례이고,
    전체 경로의 바이트 차례와 같다(SPEC.md §4.3)."""
    type_, body = objects.read_object(gitdir, oid)
    if type_ != 'tree':
        raise GitError('fatal: mygit: %s is not a tree' % oid)
    out = []
    for mode, name, sub in parse_tree(body):
        path = prefix + name
        if mode == DIR:
            out.extend(flatten_tree(gitdir, sub, path + b'/'))
        else:
            out.append((mode, sub, path))
    return out


def type_of_mode(mode):
    """cat-file -p 가 찍는 형식 — 모드에서 정해진다."""
    if mode == DIR:
        return 'tree'
    if mode == '160000':
        return 'commit'
    return 'blob'
