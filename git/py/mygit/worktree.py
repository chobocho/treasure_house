# -*- coding: utf-8 -*-
"""작업 트리 (SPEC.md §8) — 경로 따옴표, 훑기, status.

status 는 세 가지를 견준다: HEAD 트리, 인덱스, 디스크의 파일. 두 칸
글자(XY)가 곧 "어느 두 곳이 다른가" 다 — X 는 HEAD 와 인덱스, Y 는
인덱스와 작업 트리. 6부가 이 세 영역을 명령마다 캡처로 보인다.
"""
import os

from mygit import GitError, index, objects, refs, tree

# \a \b \t \n \v \f \r 와 따옴표·역슬래시는 두 글자로 쓴다
_SHORT = {7: 'a', 8: 'b', 9: 't', 10: 'n', 11: 'v', 12: 'f', 13: 'r',
          34: '"', 92: '\\'}


def quote_path(path, space=False):
    """경로 바이트 → git 이 사람에게 찍는 꼴 (core.quotePath=true).

    제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
    전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space=True 는
    status 의 규칙 — 공백만 있어도 감싼다(공백 자체는 그대로).
    한글은 UTF-8 여섯 바이트가 \\355\\225… 로 찍힌다. O(경로 길이).
    """
    need = space and 32 in path
    body = []
    for b in path:
        if b in _SHORT:
            body.append('\\' + _SHORT[b])
            need = True
        elif b < 32 or b >= 127:
            body.append('\\%03o' % b)
            need = True
        else:
            body.append(chr(b))
    s = ''.join(body)
    return '"%s"' % s if need else s



def walk_worktree(root):
    """작업 트리의 보통 파일 [경로 바이트], 전체 경로의 바이트 차례.

    어느 깊이에서든 '.git' 은 건너뛰고, 심볼릭 링크와 장치 파일은
    없는 것으로 본다(SPEC.md §8.1). 빈 디렉터리는 아무것도 아니다.
    O(파일 수 · log).
    """
    out = []

    def visit(d, prefix):
        with os.scandir(d) as it:
            for ent in it:
                if ent.name == b'.git':
                    continue
                if ent.is_symlink():
                    continue
                if ent.is_dir():
                    visit(ent.path, prefix + ent.name + b'/')
                elif ent.is_file():
                    out.append(prefix + ent.name)
    visit(os.fsencode(root), b'')
    return sorted(out)


def file_state(root, path):
    """(모드, blob 이름) 또는 파일이 없으면 None. 늘 해시한다 —
    stat 캐시를 믿지 않으니 racy git 이 없다(SPEC.md §7.2)."""
    p = os.path.join(os.fsencode(root), path)
    if not os.path.isfile(p) or os.path.islink(p):
        return None
    with open(p, 'rb') as f:
        data = f.read()
    mode = 0o100755 if os.stat(p).st_mode & 0o100 else 0o100644
    return mode, objects.hash_object('blob', data)


# 충돌 경로의 두 글자 — (단계 1, 2, 3 이 있는가) → XY (git 과 같다)
UNMERGED = {(False, True, True): 'AA', (True, True, True): 'UU',
            (True, True, False): 'UD', (True, False, True): 'DU',
            (False, True, False): 'AU', (False, False, True): 'UA',
            (True, False, False): 'DD'}


def untracked(files, tracked):
    """추적하지 않는 파일들을 git 의 normal 모드로 접는다(§8.3).

    파일마다 위쪽 디렉터리부터 보며, 그 아래에 인덱스 항목이 하나도
    없는 첫 디렉터리가 있으면 "그 디렉터리/" 로 접는다. O(파일 × 깊이).
    """
    dirs = set()
    for t in tracked:
        parts = t.split(b'/')
        for i in range(1, len(parts)):
            dirs.add(b'/'.join(parts[:i]))
    out = set()
    for f in files:
        if f in tracked:
            continue
        parts = f.split(b'/')
        shown = f
        for i in range(1, len(parts)):
            d = b'/'.join(parts[:i])
            if d not in dirs:
                shown = d + b'/'
                break
        out.add(shown)
    return sorted(out)


def status(root, gitdir):
    """git status --porcelain 과 같은 줄들(SPEC.md §8.3).

    X = HEAD 트리 ↔ 인덱스, Y = 인덱스 ↔ 작업 트리. 추적 중인 것을
    경로 차례로 먼저, 그다음 '?? ' 줄들. O(파일 수 × 해시).
    """
    _br, head = refs.read_head(gitdir)
    base = {}
    if head:
        t = refs.peel(gitdir, head, 'tree')
        base = {p: (int(m, 8), o) for m, o, p in
                tree.flatten_tree(gitdir, t)}
    stage0, stages = {}, {}
    for e in index.read_index(gitdir):
        if e.stage:
            stages.setdefault(e.path, set()).add(e.stage)
        else:
            stage0[e.path] = (e.mode, e.oid)
    rows = []
    for p in sorted(set(base) | set(stage0) | set(stages)):
        if p in stages:
            got = stages[p]
            xy = UNMERGED[(1 in got, 2 in got, 3 in got)]
        else:
            if p not in stage0:
                x = 'D'
            elif p not in base:
                x = 'A'
            else:
                x = 'M' if stage0[p] != base[p] else ' '
            y = ' '
            if p in stage0:
                now = file_state(root, p)
                if now is None:
                    y = 'D'
                elif now != stage0[p]:
                    y = 'M'
            xy = x + y
        if xy != '  ':
            rows.append('%s %s' % (xy, quote_path(p, space=True)))
    tracked = set(stage0) | set(stages)
    for p in untracked(walk_worktree(root), tracked):
        rows.append('?? %s' % quote_path(p, space=True))
    return rows



def tree_map(gitdir, tree_oid):
    """트리 → {경로: (모드, 이름)}. 트리가 없으면(첫 커밋 전) {}."""
    if not tree_oid:
        return {}
    return {p: (int(m, 8), o) for m, o, p in
            tree.flatten_tree(gitdir, tree_oid)}


OVERWRITE = ('error: Your local changes to the following files would '
             'be overwritten by checkout:')
UNTRACKED = ('error: The following untracked working tree files would '
             'be overwritten by checkout:')


def _write_file(root, path, mode, data):
    full = os.path.join(os.fsencode(root), path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        os.remove(full)
    # 0666/0777 로 열고 umask 를 따른다 — git 과 같다(SPEC.md §9.3)
    perm = 0o777 if mode & 0o100 else 0o666
    fd = os.open(full, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, perm)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)


def _remove_file(root, path):
    """파일을 지우고, 그래서 비게 된 디렉터리들도 지운다."""
    base = os.fsencode(root)
    full = os.path.join(base, path)
    if os.path.lexists(full):
        os.remove(full)
    d = os.path.dirname(full)
    while d != base and os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)
        d = os.path.dirname(d)


def checkout_tree(root, gitdir, old_tree, new_tree):
    """두 갈래 합치기로 작업 트리·인덱스를 old → new 로(SPEC.md §9.3).

    경로마다: 옛 트리와 새 트리에서 같으면 손대지 않는다(손댄 내용이
    따라온다). 다르면 인덱스가 옛 트리와 같고 작업 트리가 인덱스와
    같아야 한다. 옛 트리에 없던 경로에 추적 안 하는 파일이 있으면
    그것도 막는다. 하나라도 걸리면 아무것도 바꾸지 않고 멈춘다.
    O(경로 수 × 해시).
    """
    old, new = tree_map(gitdir, old_tree), tree_map(gitdir, new_tree)
    ents = index.read_index(gitdir)
    idx = {e.path: e for e in ents if e.stage == 0}
    unmerged = set(e.path for e in ents if e.stage)
    local, stray = [], []
    for p in sorted(set(old) | set(new) | set(idx) | unmerged):
        if old.get(p) == new.get(p):
            continue
        cur = idx.get(p)
        cur = (cur.mode, cur.oid) if cur else None
        disk = file_state(root, p)
        if p in unmerged:
            local.append(p)
        elif cur is None and old.get(p) is None:
            if disk is not None and new.get(p) is not None:
                stray.append(p)
        elif cur != old.get(p) or disk != cur:
            local.append(p)
    if local or stray:
        rows = []
        for head, paths in ((OVERWRITE, local), (UNTRACKED, stray)):
            if paths:
                rows.append(head)
                rows += ['\t' + quote_path(q) for q in paths]
                rows.append('')
        raise GitError('\n'.join(rows + ['Aborting']), 1)
    for p in sorted(set(old) | set(new)):
        if old.get(p) == new.get(p):
            continue
        if new.get(p) is None:
            _remove_file(root, p)
            idx.pop(p, None)
            continue
        mode, oid = new[p]
        _write_file(root, p, mode, objects.read_object(gitdir, oid)[1])
        full = os.path.join(os.fsencode(root), p)
        idx[p] = index.entry_from_stat(p, full, oid)
    index.write_index(gitdir, list(idx.values()))


def local_changes(root, gitdir, head_tree):
    """바꾼 뒤 남은 변경 — "M\t경로" 줄들(SPEC.md §9.3 끝).

    새 HEAD 트리와 견주어 인덱스나 작업 트리가 다른 추적 경로. M 은
    내용·모드, D 는 작업 트리에 없음, A 는 인덱스에만 있음.
    """
    head = tree_map(gitdir, head_tree)
    rows = []
    for e in index.read_index(gitdir):
        if e.stage:
            continue
        disk = file_state(root, e.path)
        if disk is None:
            letter = 'D'
        elif e.path not in head:
            letter = 'A'
        elif head[e.path] != (e.mode, e.oid) or disk != (e.mode, e.oid):
            letter = 'M'
        else:
            continue
        rows.append('%s\t%s' % (letter, quote_path(e.path)))
    return rows
