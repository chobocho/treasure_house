# -*- coding: utf-8 -*-
"""참조 (SPEC.md §6) — 브랜치는 40글자가 든 파일 하나다.

refs/heads/main 은 커밋 이름 한 줄이고, HEAD 는 보통 "ref: refs/heads/
main" 이라는 이름표를 가리키는 이름표다. 커밋이 생기면 브랜치 파일의
한 줄이 바뀔 뿐이다 — 브랜치를 만드는 값이 싼 까닭이 이것이다.

gc 뒤의 저장소는 참조를 packed-refs 한 파일에 모아 두므로 읽을 때는
둘 다 본다(느슨한 파일이 이긴다). 쓸 때는 느슨한 파일만 쓴다.
"""
import os

from mygit import GitError, objects

ZERO = '0' * 40
HEX = set('0123456789abcdef')


def _read(path):
    try:
        with open(path, 'rb') as f:
            return f.read().decode('utf-8', 'surrogateescape')
    except OSError:
        return None


def packed_refs(gitdir):
    """packed-refs → {이름: 40글자}. '#' 머리와 '^' 줄은 건너뛴다."""
    text = _read(os.path.join(gitdir, 'packed-refs'))
    out = {}
    for line in (text or '').split('\n'):
        if not line or line[0] in '#^':
            continue
        oid, _, name = line.partition(' ')
        out[name] = oid
    return out


def read_ref(gitdir, name):
    """('sym', 대상) · ('oid', 40글자) · None. 느슨한 파일이 먼저다."""
    text = _read(os.path.join(gitdir, name))
    if text is not None:
        text = text.strip()
        if text.startswith('ref: '):
            return ('sym', text[5:])
        return ('oid', text)
    oid = packed_refs(gitdir).get(name)
    return ('oid', oid) if oid else None


def resolve_ref(gitdir, name):
    """심볼릭 참조를 따라가 40글자. 없거나 태어나지 않았으면 None."""
    for _ in range(5):
        r = read_ref(gitdir, name)
        if r is None:
            return None
        if r[0] == 'oid':
            return r[1]
        name = r[1]
    raise GitError('fatal: mygit: symbolic ref loop at %s' % name)


def read_head(gitdir):
    """(HEAD 가 가리키는 브랜치 참조 이름 또는 None, 커밋 또는 None)."""
    r = read_ref(gitdir, 'HEAD')
    if r is None:
        raise GitError('fatal: mygit: HEAD is missing')
    if r[0] == 'sym':
        return r[1], resolve_ref(gitdir, r[1])
    return None, r[1]


def list_refs(gitdir, prefix='refs/'):
    """prefix 아래 참조 [(이름, 40글자)], 이름의 바이트 차례."""
    found = {n: o for n, o in packed_refs(gitdir).items()
             if n.startswith(prefix)}
    base = os.path.join(gitdir, prefix)
    for root, dirs, files in os.walk(base):
        dirs.sort()
        for f in files:
            if f.endswith('.lock'):
                continue
            name = os.path.relpath(os.path.join(root, f), gitdir)
            name = name.replace(os.sep, '/')
            oid = resolve_ref(gitdir, name)
            if oid:
                found[name] = oid
    return sorted(found.items(), key=lambda kv: kv[0].encode())


def _write_locked(path, text):
    """<경로>.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §6.1)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lock = path + '.lock'
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    except FileExistsError:
        raise GitError('fatal: mygit: unable to lock %s' % path)
    with os.fdopen(fd, 'w') as f:
        f.write(text)
    os.rename(lock, path)


def append_reflog(gitdir, name, old, new, ident, message):
    """reflog 한 줄(SPEC.md §6.3) — "옛 새 신원<TAB>메시지"."""
    path = os.path.join(gitdir, 'logs', name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8', newline='\n') as f:
        f.write('%s %s %s\t%s\n' % (old or ZERO, new or ZERO, ident,
                                   message))


def read_reflog(gitdir, name):
    """[(옛, 새, 신원, 메시지)], 오래된 것부터. 없으면 []."""
    text = _read(os.path.join(gitdir, 'logs', name)) or ''
    out = []
    for line in text.split('\n'):
        if not line:
            continue
        head, _, msg = line.partition('\t')
        old, new, ident = head.split(' ', 2)
        out.append((old, new, ident, msg))
    return out


def update_ref(gitdir, name, new, old, message, ident):
    """참조 하나를 바꾸고 reflog 를 남긴다. new=None 이면 지운다.

    HEAD 가 이 브랜치를 가리키고 있으면 HEAD 의 reflog 에도 같은 줄을
    남긴다 — git 과 같다(커밋 하나가 두 로그에 모두 보이는 까닭).
    packed-refs 에만 있는 참조를 지우는 일은 줄임이다(SPEC.md §6.1).
    """
    path = os.path.join(gitdir, name)
    if new is None:
        if not os.path.exists(path):
            raise GitError('fatal: mygit: cannot delete packed ref %s'
                           % name)
        os.remove(path)
        log = os.path.join(gitdir, 'logs', name)
        if os.path.exists(log):
            os.remove(log)
        return
    _write_locked(path, new + '\n')
    append_reflog(gitdir, name, old, new, ident, message)
    head = read_ref(gitdir, 'HEAD')
    if name != 'HEAD' and head == ('sym', name):
        append_reflog(gitdir, 'HEAD', old, new, ident, message)


def set_head(gitdir, target):
    """HEAD 를 브랜치(refs/heads/…)나 커밋(분리)으로. reflog 는 부르는
    쪽이 적는다 — 메시지가 명령마다 다르다(§6.3 의 표)."""
    if target.startswith('refs/'):
        _write_locked(os.path.join(gitdir, 'HEAD'),
                      'ref: %s\n' % target)
    else:
        _write_locked(os.path.join(gitdir, 'HEAD'), target + '\n')


# ── 이름 풀기 (SPEC.md §6.2) ───────────────────────────────────────
def _base(gitdir, name):
    """뒤붙이 없는 이름 → 40글자 또는 None. §6.2 의 1‥5 차례."""
    if len(name) == 40 and set(name) <= HEX:
        if os.path.exists(objects.object_path(gitdir, name)) or \
                objects.find_object(gitdir, name):
            return name
    if name in ('HEAD', 'ORIG_HEAD', 'MERGE_HEAD'):
        return resolve_ref(gitdir, name)
    if name.startswith('refs/'):
        oid = resolve_ref(gitdir, name)
        if oid:
            return oid
    for cand in ('refs/tags/%s', 'refs/heads/%s', 'refs/remotes/%s',
                 'refs/remotes/%s/HEAD'):
        oid = resolve_ref(gitdir, cand % name)
        if oid:
            return oid
    try:
        return objects.find_object(gitdir, name)
    except GitError:
        return None                      # 모호한 앞부분은 풀지 못한 것


def peel(gitdir, oid, want):
    """태그를 벗겨 want('commit'·'tree')를 얻는다. 못 얻으면 None."""
    for _ in range(10):
        t, body = objects.read_object(gitdir, oid)
        if t == want:
            return oid
        if t == 'tag':
            oid = body.split(b'\n', 1)[0][7:].decode()
        elif t == 'commit' and want == 'tree':
            oid = body.split(b'\n', 1)[0][5:].decode()
        else:
            return None
    return None


def _parents(gitdir, oid):
    _t, body = objects.read_object(gitdir, oid)
    head = body.split(b'\n\n', 1)[0].split(b'\n')
    return [l[7:].decode() for l in head if l.startswith(b'parent ')]


def rev_parse(gitdir, spec):
    """<rev> → 40글자 또는 None. ~n · ^n · ^0 · ^{tree} · ^{commit}.

    뒤붙이는 왼쪽부터 차례로 적용한다. O(뒤붙이의 길이 × 객체 읽기).
    """
    i = 0
    while i < len(spec) and spec[i] not in '~^':
        i += 1
    oid = _base(gitdir, spec[:i]) if i else None
    while oid and i < len(spec):
        op = spec[i]
        i += 1
        if op == '^' and spec[i:i + 1] == '{':
            end = spec.index('}', i)
            want, i = spec[i + 1:end], end + 1
            oid = peel(gitdir, oid, want or 'commit')
            continue
        j = i
        while j < len(spec) and spec[j].isdigit():
            j += 1
        n = int(spec[i:j]) if j > i else 1
        i = j
        oid = peel(gitdir, oid, 'commit')
        if oid is None:
            return None
        if op == '~':
            for _ in range(n):
                ps = _parents(gitdir, oid)
                oid = ps[0] if ps else None
                if oid is None:
                    return None
        elif n:
            ps = _parents(gitdir, oid)
            oid = ps[n - 1] if n <= len(ps) else None
    return oid


def valid_branch_name(name):
    """SPEC.md §9.2 의 브랜치 이름 규칙(check-ref-format 의 일부)."""
    bad = set(' ~^:?*[\\')
    if not name or name == '@' or '..' in name or '@{' in name:
        return False
    if any(c in bad or ord(c) < 32 or ord(c) == 127 for c in name):
        return False
    if name[0] in '-./' or name.endswith(('/', '.', '.lock')):
        return False
    return '//' not in name
