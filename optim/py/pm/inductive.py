# -*- coding: utf-8 -*-
"""인덕티브 마이너 — 로그를 재귀적으로 쪼개어 프로세스 트리를 만든다.

   알파 알고리즘은 풋프린트 표를 한 번 보고 페트리넷을 <조립>했다. 그래서 결과가
   건전하지 않을 수 있고 잡음에 약하다. 인덕티브 마이너는 반대로 간다:

       1. 직접후행 그래프에서 <컷(cut)>을 찾는다 — 활동 집합을 의미 있게 쪼개는 방법
       2. 컷의 종류(순차·선택·병렬·루프)가 곧 트리의 연산자가 된다
       3. 로그를 그 컷에 따라 나누고, 각 조각에서 재귀한다
       4. 아무 컷도 못 찾으면 <플라워 모델>로 물러선다 (무엇이든 허용)

   구조적으로 트리를 만들기 때문에 결과가 <반드시 건전>하다. 이것이 이 방법이
   실무 표준이 된 이유다.
"""
from py.pm import tree as T


def _project(traces, keep):
    """자취에서 keep 에 속한 활동만 남긴다 (병렬 컷에서 쓴다)."""
    out = []
    for tr in traces:
        p = tuple(a for a in tr if a in keep)
        out.append(p)
    return out


def _dfg(traces):
    d = {}
    for tr in traces:
        for i in range(len(tr) - 1):
            k = (tr[i], tr[i + 1])
            d[k] = d.get(k, 0) + 1
    return d


def _acts(traces):
    s = set()
    for tr in traces:
        s.update(tr)
    return s


def _starts(traces):
    return {tr[0] for tr in traces if tr}


def _ends(traces):
    return {tr[-1] for tr in traces if tr}


def _reachable(acts, edges):
    """DFG 위의 도달 가능성 — 워셜 알고리즘. O(|A|³)."""
    reach = {a: set() for a in acts}
    for (a, b) in edges:
        if a in reach and b in acts:
            reach[a].add(b)
    for k in acts:
        for i in acts:
            if k in reach[i]:
                reach[i] |= reach[k]
    return reach


def _components(acts, adj):
    """무향 인접 관계의 연결 성분."""
    seen, comps = set(), []
    for a in sorted(acts):
        if a in seen:
            continue
        stack, comp = [a], set()
        while stack:
            v = stack.pop()
            if v in comp:
                continue
            comp.add(v)
            for w in adj.get(v, ()):
                if w not in comp:
                    stack.append(w)
        seen |= comp
        comps.append(comp)
    return comps


def _xor_cut(acts, edges):
    """배타적 선택 컷: 서로 간선이 전혀 없는 덩어리로 쪼개진다."""
    adj = {a: set() for a in acts}
    for (a, b) in edges:
        if a in acts and b in acts:
            adj[a].add(b)
            adj[b].add(a)
    comps = _components(acts, adj)
    return comps if len(comps) > 1 else None


def _seq_cut(acts, edges):
    """순차 컷: 도달 가능성이 한 방향으로만 흐르는 덩어리들의 사슬."""
    reach = _reachable(acts, edges)
    # 서로 도달 가능하거나 서로 도달 불가능하면 같은 덩어리
    adj = {a: set() for a in acts}
    for a in acts:
        for b in acts:
            if a == b:
                continue
            ab, ba = b in reach[a], a in reach[b]
            if (ab and ba) or (not ab and not ba):
                adj[a].add(b)
                adj[b].add(a)
    comps = _components(acts, adj)
    if len(comps) < 2:
        return None
    # 덩어리들을 도달 순서로 정렬한다
    def before(c1, c2):
        return any(b in reach[a] for a in c1 for b in c2)
    order = sorted(comps, key=lambda c: sum(1 for d in comps if before(d, c)))
    # 사슬인지 확인: i<j 이면 앞→뒤 방향만 존재해야 한다
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            if before(order[j], order[i]):
                return None
    return order


def _and_cut(acts, edges, starts, ends):
    """병렬 컷: 서로 양방향으로 이어진 덩어리들. 각 덩어리가 시작·종료를 모두 가져야 한다."""
    pair = set()
    for (a, b) in edges:
        if a in acts and b in acts:
            pair.add((a, b))
    adj = {a: set() for a in acts}
    for a in acts:
        for b in acts:
            if a == b:
                continue
            if not ((a, b) in pair and (b, a) in pair):
                adj[a].add(b)          # 양방향이 아니면 같은 덩어리로 묶는다
                adj[b].add(a)
    comps = _components(acts, adj)
    if len(comps) < 2:
        return None
    for c in comps:
        if not (c & starts) or not (c & ends):
            return None
    return comps


def _loop_cut(acts, edges, starts, ends):
    """루프 컷: 몸통 하나와 되돌림 부분들."""
    body = set(starts) | set(ends)
    if not body or body == acts:
        return None
    rest = acts - body
    if not rest:
        return None
    # 몸통과 나머지 사이의 간선이 '끝→되돌림 시작', '되돌림 끝→몸통 시작' 뿐이어야 한다
    for (a, b) in edges:
        if a in body and b in rest and a not in ends:
            return None
        if a in rest and b in body and b not in starts:
            return None
    adj = {a: set() for a in rest}
    for (a, b) in edges:
        if a in rest and b in rest:
            adj[a].add(b)
            adj[b].add(a)
    comps = _components(rest, adj)
    return [body] + comps


def _split_xor(traces, comps):
    """각 자취를 그 활동이 속한 덩어리로 보낸다."""
    out = [[] for _ in comps]
    for tr in traces:
        if not tr:
            out[0].append(tr)
            continue
        for i, c in enumerate(comps):
            if set(tr) <= c:
                out[i].append(tr)
                break
        else:
            # 여러 덩어리에 걸친 자취 — 가장 많이 겹치는 곳으로 (잡음)
            i = max(range(len(comps)), key=lambda k: len(set(tr) & comps[k]))
            out[i].append(tuple(a for a in tr if a in comps[i]))
    return out


def _split_seq(traces, comps):
    """자취를 덩어리 경계에서 자른다."""
    out = [[] for _ in comps]
    idx = {}
    for i, c in enumerate(comps):
        for a in c:
            idx[a] = i
    for tr in traces:
        parts = [[] for _ in comps]
        for a in tr:
            parts[idx.get(a, 0)].append(a)
        for i in range(len(comps)):
            out[i].append(tuple(parts[i]))
    return out


def _split_and(traces, comps):
    return [_project(traces, c) for c in comps]


def _split_loop(traces, comps):
    """몸통 실행과 되돌림 실행으로 나눈다."""
    body = comps[0]
    out = [[] for _ in comps]
    idx = {}
    for i, c in enumerate(comps):
        for a in c:
            idx[a] = i
    for tr in traces:
        cur, cur_i = [], 0
        for a in tr:
            i = idx.get(a, 0)
            if i != cur_i:
                out[cur_i].append(tuple(cur))
                cur, cur_i = [], i
            cur.append(a)
        out[cur_i].append(tuple(cur))
    for i in range(len(comps)):
        if not out[i]:
            out[i].append(())
    return out


def _flower(acts):
    """플라워 모델 — 어떤 순서든 허용한다. 적합도는 1 이지만 정밀도가 최악이다."""
    return T.Node(T.LOOP, children=[T.tau(),
                                    T.Node(T.XOR, children=[T.act(a)
                                                            for a in sorted(acts)])])


def discover(traces, depth=0, maxdepth=20):
    """자취(활동 튜플들의 리스트)에서 프로세스 트리를 찾는다."""
    acts = _acts(traces)
    if not acts:
        return T.tau()
    if len(acts) == 1:
        a = next(iter(acts))
        # 같은 활동이 반복되면 루프다
        if any(len(tr) > 1 for tr in traces):
            return T.Node(T.LOOP, children=[T.act(a), T.tau()])
        if any(len(tr) == 0 for tr in traces):
            return T.Node(T.XOR, children=[T.act(a), T.tau()])
        return T.act(a)
    if depth >= maxdepth:
        return _flower(acts)

    edges = set(_dfg(traces))
    starts, ends = _starts(traces), _ends(traces)

    c = _xor_cut(acts, edges)
    if c:
        return T.Node(T.XOR, children=[discover(s, depth + 1, maxdepth)
                                       for s in _split_xor(traces, c)])
    c = _seq_cut(acts, edges)
    if c:
        return T.Node(T.SEQ, children=[discover(s, depth + 1, maxdepth)
                                       for s in _split_seq(traces, c)])
    c = _and_cut(acts, edges, starts, ends)
    if c:
        return T.Node(T.AND, children=[discover(s, depth + 1, maxdepth)
                                       for s in _split_and(traces, c)])
    c = _loop_cut(acts, edges, starts, ends)
    if c and len(c) > 1:
        return T.Node(T.LOOP, children=[discover(s, depth + 1, maxdepth)
                                        for s in _split_loop(traces, c)])
    return _flower(acts)


def mine(log, min_count=1):
    """이벤트 로그에서 프로세스 트리를 찾는다. min_count 로 희귀 변형을 걸러낸다."""
    lg = log.filter_variants(min_count) if min_count > 1 else log
    traces = [t.activities for t in lg]
    return discover(traces)
