# -*- coding: utf-8 -*-
"""diff (SPEC.md §11) — 두 줄 목록 사이의 가장 짧은 편집 스크립트.

세 단계다. (1) 앞뒤의 같은 줄을 떼어 둔다. (2) 남은 가운데서 Myers 의
탐욕 탐색으로 가장 짧은 스크립트를 찾는다. (3) 바뀐 줄 묶음을 git 처럼
위아래로 밀어 자리를 정한다 — 같은 줄이 되풀이되는 곳에서는 어디를
바뀐 줄로 칠지가 여럿이라, 이 단계가 없으면 git 과 덩어리 자리가
달라진다. 다섯 언어가 같은 세 단계를 밟는다.

줄은 bytes 이고 줄바꿈까지 품는다 — 끝 줄바꿈이 없는 줄은 있는 줄과
다른 줄이다. rchg 는 줄마다 "바뀌었나" 의 bool 목록이다.
"""
from mygit import objects
from mygit.worktree import quote_path

CONTEXT = 3
BINARY_PROBE = 8000


def split_lines(data):
    """바이트 → 줄 목록. 줄마다 '\\n' 을 품고, 마지막 줄만 없을 수
    있다."""
    if not data:
        return []
    parts = data.split(b'\n')
    lines = [p + b'\n' for p in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


# ── 2 단계: Myers 앞방향 탐욕 탐색 (SPEC.md §11.2) ─────────────────
def _forward(a, b):
    """가운데 a·b 의 (ra, rb). 대각선 k 마다 가장 멀리 간 x 를 V[k] 에.

    d 마다 V 의 사본을 남겨 두었다가 (N, M) 에서 거꾸로 같은 판정을
    되밟아 편집을 표시한다. O((N+M)·D) 시간, O((N+M)·D) 공간 — 공간을
    줄인 변형이 myers_linear 다.
    """
    n, m = len(a), len(b)
    v = {1: 0}
    trace = []
    for d in range(n + m + 1):
        trace.append(dict(v))
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v[k - 1] < v[k + 1]):
                x = v[k + 1]                    # 아래로: b 의 줄을 끼움
            else:
                x = v[k - 1] + 1                # 오른쪽: a 의 줄을 지움
            y = x - k
            while x < n and y < m and a[x] == b[y]:
                x, y = x + 1, y + 1
            v[k] = x
            if x >= n and y >= m:
                return _backtrack(trace, n, m, d)
    raise AssertionError('Myers 탐색이 끝나지 않았다')


def _backtrack(trace, n, m, dfin):
    ra, rb = [False] * n, [False] * m
    x, y = n, m
    for d in range(dfin, 0, -1):
        v = trace[d]
        k = x - y
        down = k == -d or (k != d and v[k - 1] < v[k + 1])
        pk = k + 1 if down else k - 1
        px = v[pk]
        py = px - pk
        if down:
            rb[py] = True
        else:
            ra[px] = True
        x, y = px, py
    return ra, rb


# ── 결정 7: 선형 공간 변형 (Myers 1986 §4b, middle snake) ──────────
def _middle(a, b, left, top, right, bottom):
    """가운데 뱀: ((sx, sy), (fx, fy), 앞방향인가). 양끝에서 동시에
    탐색해 두 경로가 겹치는 곳을 찾는다. O(N+M) 공간."""
    w, h = right - left, bottom - top
    delta = w - h
    vf, vb = {1: left}, {1: bottom}
    for d in range((w + h + 1) // 2 + 1):
        for k in range(d, -d - 1, -2):
            c = k - delta
            if k == -d or (k != d and vf[k - 1] < vf[k + 1]):
                px = x = vf[k + 1]
            else:
                px = vf[k - 1]
                x = px + 1
            y = top + (x - left) - k
            py = y if (d == 0 or x != px) else y - 1
            while x < right and y < bottom and a[x] == b[y]:
                x, y = x + 1, y + 1
            vf[k] = x
            if delta % 2 and -(d - 1) <= c <= d - 1 and y >= vb[c]:
                return (px, py), (x, y), True
        for c in range(d, -d - 1, -2):
            k = c + delta
            if c == -d or (c != d and vb[c - 1] > vb[c + 1]):
                py = y = vb[c + 1]
            else:
                py = vb[c - 1]
                y = py - 1
            x = left + (y - top) + k
            px = x if (d == 0 or y != py) else x + 1
            while x > left and y > top and a[x - 1] == b[y - 1]:
                x, y = x - 1, y - 1
            vb[c] = y
            if delta % 2 == 0 and -d <= k <= d and x <= vf[k]:
                return (x, y), (px, py), False
    raise AssertionError('가운데 뱀을 못 찾았다')


def _linear(a, b, left, top, right, bottom, ra, rb):
    while left < right and top < bottom and a[left] == b[top]:
        left, top = left + 1, top + 1
    while left < right and top < bottom and \
            a[right - 1] == b[bottom - 1]:
        right, bottom = right - 1, bottom - 1
    if left == right:
        for y in range(top, bottom):
            rb[y] = True
        return
    if top == bottom:
        for x in range(left, right):
            ra[x] = True
        return
    (sx, sy), (fx, fy), fwd = _middle(a, b, left, top, right, bottom)
    _linear(a, b, left, top, sx, sy, ra, rb)
    dx, dy = fx - sx, fy - sy
    if dx != dy:                    # 뱀 안의 편집 한 걸음
        if dx > dy:
            ra[sx if fwd else fx - 1] = True
        else:
            rb[sy if fwd else fy - 1] = True
    _linear(a, b, fx, fy, right, bottom, ra, rb)


def myers_linear(a, b):
    """선형 공간 Myers(PLAN.md §9 결정 7, Python 만). 같은 길이의
    스크립트가 여럿이면 앞방향과 다른 것을 고를 수 있다."""
    ra, rb = [False] * len(a), [False] * len(b)
    _linear(a, b, 0, 0, len(a), len(b), ra, rb)
    return ra, rb


def myers(a, b):
    """1·2 단계 — 앞뒤를 깎고 가운데를 앞방향 Myers 로."""
    n, m = len(a), len(b)
    s = 0
    while s < n and s < m and a[s] == b[s]:
        s += 1
    e = 0
    while e < n - s and e < m - s and a[n - 1 - e] == b[m - 1 - e]:
        e += 1
    ra, rb = _forward(a[s:n - e], b[s:m - e])
    return ([False] * s + ra + [False] * e,
            [False] * s + rb + [False] * e)


# ── 3 단계: 밀어 붙이기 (git 의 xdl_change_compact, 휴리스틱 없이) ──
class _Group(object):
    """바뀐 줄 묶음 [start, end). 빈 묶음(start == end)도 자리다."""

    def __init__(self, chg):
        self.chg, self.n = chg, len(chg) - 1     # 끝의 가짜 줄 하나
        self.start = self.end = 0
        while self.end < self.n and chg[self.end]:
            self.end += 1

    def next(self):
        if self.end == self.n:
            return False
        self.start = self.end = self.end + 1
        while self.end < self.n and self.chg[self.end]:
            self.end += 1
        return True

    def previous(self):
        if self.start == 0:
            return False
        self.end = self.start = self.start - 1
        while self.start > 0 and self.chg[self.start - 1]:
            self.start -= 1
        return True

    def slide_down(self, recs):
        if self.end < self.n and recs[self.start] == recs[self.end]:
            self.chg[self.start], self.chg[self.end] = False, True
            self.start, self.end = self.start + 1, self.end + 1
            while self.end < self.n and self.chg[self.end]:
                self.end += 1
            return True
        return False

    def slide_up(self, recs):
        s, e = self.start, self.end
        if s > 0 and recs[s - 1] == recs[e - 1]:
            self.start, self.end = self.start - 1, self.end - 1
            self.chg[self.start], self.chg[self.end] = True, False
            while self.start > 0 and self.chg[self.start - 1]:
                self.start -= 1
            return True
        return False


def compact(recs, rchg, orecs, ochg):
    """한 쪽 파일의 바뀐 줄 묶음을 밀어 자리를 정한다(SPEC.md §11.2).

    묶음마다 위로 끝까지, 다시 아래로 끝까지 민다(밀다가 이웃 묶음과
    붙으면 처음부터). 상대 파일의 바뀐 묶음과 끝이 맞는 자리가 있었으면
    그리로 되올리고, 없으면 맨 아래에 둔다. 상대 쪽 묶음 표지 go 는
    묶음과 발을 맞춰 움직인다. O(줄 수 × 미는 거리).
    """
    chg = list(rchg) + [False]
    g = _Group(chg)
    go = _Group(list(ochg) + [False])
    while True:
        if g.end != g.start:
            while True:
                size = g.end - g.start
                match_end = -1
                while g.slide_up(recs):
                    go.previous()
                earliest = g.end
                if go.end > go.start:
                    match_end = g.end
                while g.slide_down(recs):
                    go.next()
                    if go.end > go.start:
                        match_end = g.end
                if size == g.end - g.start:
                    break
            if g.end != earliest and match_end != -1:
                while go.end == go.start:
                    g.slide_up(recs)
                    go.previous()
        if not g.next():
            break
        go.next()
    return chg[:-1]


def edit_flags(a, b, linear=False):
    """세 단계를 다 거친 (ra, rb) — 계약의 전부(SPEC.md §11.2)."""
    ra, rb = (myers_linear if linear else myers)(a, b)
    ra = compact(a, ra, b, rb)
    rb = compact(b, rb, a, ra)
    return ra, rb


def build_changes(ra, rb):
    """바뀐 곳 [(a 자리, b 자리, a 줄 수, b 줄 수)], 앞에서부터.

    끝에서 앞으로 훑으며 같은 자리에서 만나는 지운 묶음과 끼운 묶음을
    한 바뀐 곳으로 묶는다(git 의 xdl_build_script).
    """
    out = []
    i1, i2 = len(ra), len(rb)
    while i1 > 0 or i2 > 0:
        if (i1 > 0 and ra[i1 - 1]) or (i2 > 0 and rb[i2 - 1]):
            l1, l2 = i1, i2
            while i1 > 0 and ra[i1 - 1]:
                i1 -= 1
            while i2 > 0 and rb[i2 - 1]:
                i2 -= 1
            out.append((i1, i2, l1 - i1, l2 - i2))
        else:
            i1, i2 = i1 - 1, i2 - 1
    out.reverse()
    return out


def _is_func(line):
    """git 기본 드라이버의 함수 줄 — 첫 바이트가 영문자·'_'·'$'."""
    c = line[:1]
    return bool(c) and (c.isalpha() or c in (b'_', b'$'))


def _span(start, count):
    first = start + 1 if count else start
    return b'%d' % first if count == 1 else b'%d,%d' % (first, count)


def unified_diff(a, b):
    """덩어리들(SPEC.md §11.3). 같으면 b''."""
    ra, rb = edit_flags(a, b)
    ch = build_changes(ra, rb)
    out = []
    i = 0
    while i < len(ch):
        j = i
        while j + 1 < len(ch) and \
                ch[j + 1][0] - (ch[j][0] + ch[j][2]) <= 2 * CONTEXT:
            j += 1
        first, last = ch[i], ch[j]
        s1, s2 = max(first[0] - CONTEXT, 0), max(first[1] - CONTEXT, 0)
        e1 = min(last[0] + last[2] + CONTEXT, len(a))
        e2 = min(last[1] + last[3] + CONTEXT, len(b))
        func = b''
        for q in range(s1 - 1, -1, -1):
            if _is_func(a[q]):
                func = b' ' + a[q].rstrip()[:80].rstrip()
                break
        out.append(b'@@ -%s +%s @@%s\n'
                   % (_span(s1, e1 - s1), _span(s2, e2 - s2), func))
        p1 = s1
        for k in range(i, j + 1):
            c = ch[k]
            out += [b' ' + a[q] for q in range(p1, c[0])]
            out += [b'-' + a[q] for q in range(c[0], c[0] + c[2])]
            out += [b'+' + b[q] for q in range(c[1], c[1] + c[3])]
            p1 = c[0] + c[2]
        out += [b' ' + a[q] for q in range(p1, e1)]
        i = j + 1
    return b''.join(line if line.endswith(b'\n') else
                    line + b'\n\\ No newline at end of file\n'
                    for line in out)


def _q(prefix, path):
    return quote_path(prefix + path).encode('utf-8', 'surrogateescape')


def file_diff(path_a, path_b, old, new):
    """파일 하나의 diff 전체(SPEC.md §11.4). old·new 는 (모드, 이름,
    바이트) 또는 None(새로 생김·지워짐). 같으면 b''."""
    if old and new and old[:2] == new[:2]:
        return b''
    rows = [b'diff --git ' + _q(b'a/', path_a) + b' ' +
            _q(b'b/', path_b)]
    z = b'0000000'
    if old is None:
        rows += [b'new file mode %06o' % new[0],
                 b'index %s..%s' % (z, new[1][:7].encode())]
    elif new is None:
        rows += [b'deleted file mode %06o' % old[0],
                 b'index %s..%s' % (old[1][:7].encode(), z)]
    else:
        if old[0] != new[0]:
            rows += [b'old mode %06o' % old[0],
                     b'new mode %06o' % new[0]]
        if old[1] == new[1]:
            return b'\n'.join(rows) + b'\n'          # 모드만 바뀜
        idx = b'index %s..%s' % (old[1][:7].encode(),
                                 new[1][:7].encode())
        if old[0] == new[0]:
            idx += b' %06o' % old[0]
        rows.append(idx)
    da = old[2] if old else b''
    db = new[2] if new else b''
    name_a = _q(b'a/', path_a) if old else b'/dev/null'
    name_b = _q(b'b/', path_b) if new else b'/dev/null'
    if b'\0' in da[:BINARY_PROBE] or b'\0' in db[:BINARY_PROBE]:
        rows.append(b'Binary files %s and %s differ' % (name_a, name_b))
        return b'\n'.join(rows) + b'\n'
    rows += [b'--- ' + name_a, b'+++ ' + name_b]
    return b'\n'.join(rows) + b'\n' + unified_diff(split_lines(da),
                                                   split_lines(db))


def blob_side(gitdir, mode, oid):
    """(모드, 이름, 바이트) — 저장소의 blob 에서."""
    return mode, oid, objects.read_object(gitdir, oid)[1]
