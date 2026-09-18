# -*- coding: utf-8 -*-
"""merge (SPEC.md §12) — 공통 조상 B 에서 갈라진 O(우리)와 T(그들).

파일 하나의 합치기는 git 의 xdl_merge(ZEALOUS 수준)를 따른다:
  1. B→O, B→T 의 바뀐 곳을 B 좌표로 짝지어 훑는다. 엄격히 앞선 쪽은
     그대로 받고, 겹치거나 **맞닿으면** 충돌 후보다(같은 수정이면
     한 번만).
  2. 충돌마다 O 쪽과 T 쪽을 다시 diff 해 같은 줄을 표지 밖으로 뺀다.
  3. 사이가 바뀌지 않은 줄 3개 이하인 이웃 충돌은 하나로 붙인다.
진짜 git merge 로 경계를 확인한 규칙들이다(golden/scen/merge-*.scn).
"""
from mygit import GitError, objects
from mygit.diff import build_changes, edit_flags, split_lines

JOIN = 3                         # 이만큼 가까운 충돌은 하나로 붙인다
UNDECIDED = object()             # 세 줄 규칙이 못 고름(None 은 "없음")


def _changes(a, b):
    return build_changes(*edit_flags(a, b))


def _side_range(changes, start, end):
    """B 의 [start, end) 에 맞는 한쪽 파일의 범위.

    start 앞에서 시작한 바뀐 곳들의 길이 차를 더하면 시작 자리가,
    end 이하에서 시작한 것까지 더하면 끝 자리가 나온다 — 이 범위에
    걸친 바뀐 곳은 짝 맞추기가 전부 이 범위에 넣어 두었다.
    """
    s = start + sum(c[3] - c[2] for c in changes if c[0] < start)
    e = end + sum(c[3] - c[2] for c in changes if c[0] <= end)
    return s, e


def _pair(base, ours, theirs):
    """1 단계 — [(종류, B 시작, B 끝, O 줄들, T 줄들)]. 종류는 'o'
    (O 쪽 변경 받기), 't', 'c'(충돌 후보). 바뀌지 않은 곳은 빠진다."""
    c1, c2 = _changes(base, ours), _changes(base, theirs)
    out, i, j = [], 0, 0
    while i < len(c1) or j < len(c2):
        x = c1[i] if i < len(c1) else None
        y = c2[j] if j < len(c2) else None
        if y is None or (x is not None and x[0] + x[2] < y[0]):
            out.append(('o', x[0], x[0] + x[2], ours[x[1]:x[1] + x[3]],
                        None))
            i += 1
            continue
        if x is None or y[0] + y[2] < x[0]:
            out.append(('t', y[0], y[0] + y[2], None,
                        theirs[y[1]:y[1] + y[3]]))
            j += 1
            continue
        if x[0] == y[0] and x[2] == y[2] and \
                ours[x[1]:x[1] + x[3]] == theirs[y[1]:y[1] + y[3]]:
            out.append(('o', x[0], x[0] + x[2], ours[x[1]:x[1] + x[3]],
                        None))            # 양쪽이 같은 수정 — 한 번만
            i, j = i + 1, j + 1
            continue
        start = min(x[0], y[0])
        end = max(x[0] + x[2], y[0] + y[2])
        i, j = i + 1, j + 1
        while True:                       # 맞닿는 것까지 넓힌다
            if i < len(c1) and c1[i][0] <= end:
                end = max(end, c1[i][0] + c1[i][2])
                i += 1
            elif j < len(c2) and c2[j][0] <= end:
                end = max(end, c2[j][0] + c2[j][2])
                j += 1
            else:
                break
        os_, oe = _side_range(c1, start, end)
        ts, te = _side_range(c2, start, end)
        out.append(('c', start, end, ours[os_:oe], theirs[ts:te]))
    return out


def _refine(o, t):
    """2 단계 — 충돌 하나를 O·T 의 diff 로 쪼갠다.

    [('same', 줄들) 또는 ('conf', O 줄들, T 줄들)]. 같은 줄은 표지
    밖으로 나온다. O == T 면 충돌이 아니다.
    """
    if o == t:
        return [('same', o)]
    out, p1 = [], 0
    for i1, i2, n1, n2 in _changes(o, t):
        if i1 > p1:
            out.append(('same', o[p1:i1]))
        out.append(('conf', o[i1:i1 + n1], t[i2:i2 + n2]))
        p1 = i1 + n1
    if p1 < len(o):
        out.append(('same', o[p1:]))
    return out


def merge3(base, ours, theirs, label):
    """세 판의 바이트 → (합친 바이트, 충돌 수). SPEC.md §12.3.

    O(줄 수 × 편집 거리) — diff 두 번과 충돌마다 diff 한 번.
    """
    if ours == theirs or base == theirs:
        return ours, 0
    if base == ours:
        return theirs, 0
    b = split_lines(base)
    o, t = split_lines(ours), split_lines(theirs)
    pieces, pos = [], 0
    for kind, s, e, olines, tlines in _pair(b, o, t):
        if s > pos:
            pieces.append(('same', b[pos:s]))
        if kind == 'o':
            pieces.append(('clean', olines))
        elif kind == 't':
            pieces.append(('clean', tlines))
        else:
            pieces += _refine(olines, tlines)
        pos = e
    if pos < len(b):
        pieces.append(('same', b[pos:]))
    # 3 단계 — 바뀌지 않은 줄 JOIN 개 이하로 떨어진 충돌을 붙인다
    joined = []
    for p in pieces:
        near = len(joined) >= 2 and joined[-1][0] == 'same' and \
            joined[-2][0] == 'conf' and len(joined[-1][1]) <= JOIN
        if p[0] == 'conf' and near:
            mid = joined.pop()[1]
            prev = joined.pop()
            p = ('conf', prev[1] + mid + p[1], prev[2] + mid + p[2])
        elif p[0] == 'same' and joined and joined[-1][0] == 'same':
            p = ('same', joined.pop()[1] + p[1])
        joined.append(p)
    out, n = [], 0
    for p in joined:
        if p[0] == 'conf':
            n += 1
            out += [b'<<<<<<< HEAD\n'] + p[1] + [b'=======\n']
            out += p[2] + [b'>>>>>>> %s\n' % label.encode()]
        else:
            out += p[1]
    return b''.join(out), n


def merge_trees(gitdir, base, ours, theirs, label):
    """트리 단위 합치기(SPEC.md §12.2). base·ours·theirs 는
    {경로: (모드, 이름)}. → (결과 {경로: 항목}, 안내 줄들, 충돌 경로).

    항목은 ('clean', 모드, 이름) · ('gone',) · ('conflict', 합친 바이트,
    {단계: (모드, 이름)}, 모드). 모드는 내용과 따로 같은 세 줄 규칙.
    """
    def pick(bv, ov, tv):
        """세 줄 규칙. 없음(None)도 값이다 — 한쪽만 지웠으면 지움이
        이긴다. 규칙이 못 고르면 UNDECIDED."""
        if ov == tv or bv == tv:
            return ov
        if bv == ov:
            return tv
        return UNDECIDED

    result, notes, conflicts = {}, [], []
    for p in sorted(set(base) | set(ours) | set(theirs)):
        bv, ov, tv = base.get(p), ours.get(p), theirs.get(p)
        whole = pick(bv, ov, tv)
        if whole is not UNDECIDED:
            result[p] = ('clean',) + whole if whole else ('gone',)
            continue
        if ov is None or tv is None:
            raise GitError('fatal: mygit: unsupported merge case '
                           '(modify/delete) in %s'
                           % p.decode('utf-8', 'replace'))
        mode = pick(bv[0] if bv else None, ov[0], tv[0])
        if mode is UNDECIDED:
            name = p.decode('utf-8', 'replace')
            raise GitError('fatal: mygit: unsupported merge case '
                           '(mode) in %s' % name)
        notes.append('Auto-merging %s' % p.decode('utf-8', 'replace'))
        data = [objects.read_object(gitdir, v[1])[1] if v else b''
                for v in (bv, ov, tv)]
        text, n = merge3(data[0], data[1], data[2], label)
        if n:
            kind = 'content' if bv else 'add/add'
            notes.append('CONFLICT (%s): Merge conflict in %s'
                         % (kind, p.decode('utf-8', 'replace')))
            stages = {k: v for k, v in ((1, bv), (2, ov), (3, tv)) if v}
            result[p] = ('conflict', text, stages, mode)
            conflicts.append(p)
        else:
            oid = objects.write_object(gitdir, 'blob', text)
            result[p] = ('clean', mode, oid)
    return result, notes, conflicts
