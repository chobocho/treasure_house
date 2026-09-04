# -*- coding: utf-8 -*-
"""적합도 검사 — 로그와 모델이 얼마나 맞는가.

   이 파일이 이 교재에서 가장 중요한 다리다. "로그가 모델에 맞는가"라는 질문이
   <최적화 문제>로 정확히 번역되기 때문이다.

       정렬(alignment) = 자취와 모델 실행을 가장 싸게 짝지어 주는 것
                       = 상태공간 위의 <최소비용 경로>
                       = 다익스트라 / A*  (그리고 실무에서는 LP 완화 휴리스틱)

   토큰 재생은 그보다 값싼 근사이고, 정렬은 정확하지만 비싸다. 둘의 차이를
   실측으로 보인다.
"""
import heapq

from py.pm import petri


# ---------------------------------------------------------------- 토큰 재생

def token_replay(net, m0, mf, trace, max_silent=8):
    """토큰 기반 재생 — 자취를 따라가며 부족한 토큰은 억지로 만들고(missing),
       끝에 남은 토큰은 세어 둔다(remaining).

           fitness = ½(1 − m/c) + ½(1 − r/p)
             p = 만든 토큰 수, c = 소비한 토큰 수, m = 없어서 만들어 준 토큰 수,
             r = 끝나고 남은 토큰 수

       값싸다(자취 길이에 선형). 그러나 <어디가 왜 틀렸는지>를 잘 설명하지 못하고,
       모델이 헐거우면 점수를 과대평가한다. 그래서 정렬로 넘어간다.
    """
    m = dict(m0)
    produced = consumed = missing = 0
    for p, c in m0.items():
        produced += c
    for act in trace:
        t = _find_fireable(net, m, act, max_silent)
        if t is None:
            # 라벨이 같은 전이를 아무거나 골라 부족한 토큰을 만들어 준다
            cands = net.transitions_with_label(act)
            if not cands:
                missing += 1                      # 모델에 없는 활동 — 로그 이동
                continue
            t = cands[0]
            need = net.ins.get(t, {})
            for p, c in need.items():
                have = m.get(p, 0)
                if have < c:
                    missing += c - have
                    m[p] = c
        else:
            m, extra = t
            produced += extra[0]
            consumed += extra[1]
            continue
        # 억지로 채운 뒤 발화
        need = net.ins.get(t, {})
        for p, c in need.items():
            m[p] -= c
            consumed += c
            if m[p] == 0:
                del m[p]
        for p, c in net.outs.get(t, {}).items():
            m[p] = m.get(p, 0) + c
            produced += c
    # 종료 마킹까지 τ 로 갈 수 있으면 간다
    endm = petri._to_final(net, m, mf, max_silent)
    if endm is not None:
        m = endm
    remaining = 0
    for p, c in m.items():
        remaining += max(0, c - mf.get(p, 0))
    for p, c in mf.items():
        consumed += c
        if m.get(p, 0) < c:
            missing += c - m.get(p, 0)
    f = 0.5 * (1 - missing / float(max(consumed, 1))) + \
        0.5 * (1 - remaining / float(max(produced, 1)))
    return {'fitness': max(0.0, min(1.0, f)), 'produced': produced,
            'consumed': consumed, 'missing': missing, 'remaining': remaining}


def _find_fireable(net, m, act, max_silent):
    """라벨이 act 인 전이를 (τ 를 거쳐서라도) 발화한다. 성공하면 (새 마킹, (생산, 소비))."""
    seen = {petri._key(m)}
    frontier = [(dict(m), 0, 0, 0)]
    while frontier:
        cur, depth, prod, cons = frontier.pop(0)
        for t in net.enabled(cur):
            if net.label_of(t) == act:
                nxt = net.fire(cur, t)
                c = sum(net.ins.get(t, {}).values())
                p = sum(net.outs.get(t, {}).values())
                return nxt, (prod + p, cons + c)
        if depth >= max_silent:
            continue
        for t in net.enabled(cur):
            if net.label_of(t) is None:
                nxt = net.fire(cur, t)
                k = petri._key(nxt)
                if k not in seen:
                    seen.add(k)
                    frontier.append((nxt, depth + 1,
                                     prod + sum(net.outs.get(t, {}).values()),
                                     cons + sum(net.ins.get(t, {}).values())))
    return None


# ---------------------------------------------------------------- 정렬

LOG_MOVE = 'log'
MODEL_MOVE = 'model'
SYNC_MOVE = 'sync'


def align(net, m0, mf, trace, max_states=200000, heuristic=True):
    """최소비용 정렬을 A* 로 찾는다.

       상태 = (자취에서 소비한 사건 수 i, 현재 마킹 m)
       이동 세 가지
         · 동기(sync)   : trace[i] 와 라벨이 같은 전이를 발화       비용 0
         · 로그(log)    : trace[i] 를 모델 없이 넘긴다              비용 1
         · 모델(model)  : 전이를 발화하되 로그와 짝이 없다          비용 1 (τ 는 0)
       목표 = i 가 자취 끝이고 마킹이 종료 마킹을 덮는 상태

       이것은 그래프 위의 <최소비용 경로>다. 비용이 음이 아니므로 다익스트라가
       정확하고, 여기에 허용 가능한 휴리스틱을 얹으면 A* 가 된다.

       휴리스틱: 남은 사건 중 <모델에 아예 없는 활동>의 개수. 그런 사건은
       반드시 로그 이동이 되어 각각 비용 1 을 치르므로 과대평가하지 않는다.
       실무 구현은 마킹 방정식의 LP 완화를 휴리스틱으로 쓴다(11부 46장).
    """
    labels = {net.label_of(t) for t in net.transitions if net.label_of(t) is not None}
    n = len(trace)

    def h(i):
        if not heuristic:
            return 0
        return sum(1 for a in trace[i:] if a not in labels)

    start = (0, petri._key(m0))
    markings = {start[1]: dict(m0)}
    dist = {start: 0}
    prev = {}
    pq = [(h(0), 0, start)]
    seen = 0
    while pq:
        f, g, state = heapq.heappop(pq)
        if g > dist.get(state, 1 << 30):
            continue
        seen += 1
        if seen > max_states:
            raise RuntimeError('탐색 상태가 너무 많다 (%d)' % seen)
        i, mk = state
        m = markings[mk]
        if i == n and petri._covers(m, mf):
            return _rebuild(prev, state, g, seen)

        # ① 동기 이동 / ③ 모델 이동
        for t in net.enabled(m):
            lab = net.label_of(t)
            nm = net.fire(m, t)
            nk = petri._key(nm)
            markings.setdefault(nk, nm)
            if i < n and lab == trace[i]:
                _push(pq, dist, prev, markings, (i + 1, nk), g, 0,
                      (SYNC_MOVE, trace[i], t), state, h(i + 1))
            cost = 0 if lab is None else 1
            _push(pq, dist, prev, markings, (i, nk), g, cost,
                  (MODEL_MOVE, None, t), state, h(i))
        # ② 로그 이동
        if i < n:
            _push(pq, dist, prev, markings, (i + 1, mk), g, 1,
                  (LOG_MOVE, trace[i], None), state, h(i + 1))
    raise RuntimeError('정렬을 찾지 못했다 — 모델이 종료할 수 없다')


def _push(pq, dist, prev, markings, nstate, g, cost, move, from_state, hval):
    ng = g + cost
    if ng < dist.get(nstate, 1 << 30):
        dist[nstate] = ng
        prev[nstate] = (from_state, move)
        heapq.heappush(pq, (ng + hval, ng, nstate))


def _rebuild(prev, state, cost, visited):
    moves = []
    while state in prev:
        state, move = prev[state]
        moves.append(move)
    moves.reverse()
    return {'cost': cost, 'moves': moves, 'visited': visited,
            'log_moves': sum(1 for m in moves if m[0] == LOG_MOVE),
            'model_moves': sum(1 for m in moves if m[0] == MODEL_MOVE
                               and m[2] is not None),
            'sync_moves': sum(1 for m in moves if m[0] == SYNC_MOVE)}


def alignment_fitness(net, m0, mf, trace, **kw):
    """정렬 기반 적합도:  1 − (정렬 비용) / (최악의 비용).

       최악의 비용은 "자취를 통째로 로그 이동으로 버리고 모델을 처음부터 끝까지
       혼자 실행하는" 경우다. 그래서 0 과 1 사이에 들어온다.
    """
    a = align(net, m0, mf, trace, **kw)
    empty = align(net, m0, mf, [], **kw)          # 모델만 실행하는 최소 비용
    worst = len(trace) + empty['cost']
    if worst == 0:
        return 1.0, a
    return 1.0 - a['cost'] / float(worst), a


def log_fitness(net, m0, mf, log, **kw):
    """로그 전체의 적합도 — 변형마다 한 번만 계산하고 빈도로 가중한다."""
    total_cost = total_worst = 0.0
    empty = align(net, m0, mf, [], **kw)['cost']
    per_variant = {}
    for seq, cnt in log.variants().items():
        a = align(net, m0, mf, list(seq), **kw)
        per_variant[seq] = a
        total_cost += cnt * a['cost']
        total_worst += cnt * (len(seq) + empty)
    return (1.0 - total_cost / total_worst if total_worst else 1.0), per_variant


# ---------------------------------------------------------------- 정밀도

def precision(net, m0, mf, log, max_silent=8):
    """탈출 간선(escaping edges) 기반 정밀도.

       로그의 각 접두사마다 "모델이 다음에 허용하는 활동"과 "로그에서 실제로
       관측된 다음 활동"을 비교한다. 허용하는데 관측되지 않은 것이 <탈출 간선>이다.

           precision = 1 − (탈출 간선 수) / (허용된 간선 수)

       플라워 모델은 모든 활동을 허용하므로 정밀도가 바닥이다. 반대로 로그의
       자취만 정확히 허용하는 모델은 정밀도 1 이지만 일반화가 0 이다.
    """
    # 접두사 -> 로그에서 관측된 다음 활동 집합
    obs = {}
    for t in log:
        acts = t.activities
        for i in range(len(acts)):
            obs.setdefault(acts[:i], set()).add(acts[i])
        obs.setdefault(acts, set())
    allowed_total = escaping = 0
    for prefix, nexts in obs.items():
        m = _marking_after(net, m0, prefix, max_silent)
        if m is None:
            continue
        allowed = _enabled_labels(net, m, max_silent)
        allowed_total += len(allowed)
        escaping += len(allowed - nexts)
    if allowed_total == 0:
        return 1.0
    return 1.0 - escaping / float(allowed_total)


def _marking_after(net, m0, prefix, max_silent):
    m = dict(m0)
    for a in prefix:
        r = _find_fireable(net, m, a, max_silent)
        if r is None:
            return None
        m = r[0]
    return m


def _enabled_labels(net, m, max_silent):
    """τ 를 거쳐서라도 지금 실행할 수 있는 <보이는> 활동들."""
    out = set()
    seen = {petri._key(m)}
    frontier = [(m, 0)]
    while frontier:
        cur, d = frontier.pop(0)
        for t in net.enabled(cur):
            lab = net.label_of(t)
            if lab is not None:
                out.add(lab)
            elif d < max_silent:
                nxt = net.fire(cur, t)
                k = petri._key(nxt)
                if k not in seen:
                    seen.add(k)
                    frontier.append((nxt, d + 1))
    return out


def simplicity(net):
    """단순성 — 호(arc)의 밀도로 재는 아주 거친 지표.

       모델이 복잡할수록 읽기 어렵고 과적합일 가능성이 높다. 정량화가 어려운
       축이라 여러 정의가 경쟁하는데, 여기서는 노드당 평균 호 수를 쓴다.
    """
    s = net.summary()
    nodes = s['places'] + s['transitions']
    return 1.0 / (1.0 + s['arcs'] / float(max(nodes, 1)))


# ---------------------------------------------------------------- LP 휴리스틱

def _incidence(net):
    """장소 x 전이 발생행렬 N. N[p][t] = (t 가 p 에 놓는 수) − (t 가 p 에서 빼는 수)."""
    places = sorted(net.places)
    trans = sorted(net.transitions)
    N = [[0.0] * len(trans) for _ in places]
    pi = {p: i for i, p in enumerate(places)}
    for j, t in enumerate(trans):
        for p, c in net.ins.get(t, {}).items():
            N[pi[p]][j] -= c
        for p, c in net.outs.get(t, {}).items():
            N[pi[p]][j] += c
    return places, trans, N


def lp_heuristic(net, marking, mf, remaining, cache=None):
    """마킹 방정식의 LP 완화로 남은 정렬 비용의 하한을 구한다.

       변수
           y_t ≥ 0   전이 t 를 몇 번 발화하는가 (정수 제약을 <완화>한다)
           s_a ≥ 0   라벨 a 에서 동기 이동을 몇 번 하는가
       제약
           마킹 방정식   m + N y = mf          ← 종료 마킹에 닿아야 한다
           s_a ≤ r_a                            ← 남은 사건 수보다 많이 맞출 수 없다
           s_a ≤ Σ_{label(t)=a} y_t             ← 발화한 만큼만 맞출 수 있다
       목적
           min  Σ r_a + Σ_{보이는 t} y_t − 2 Σ s_a

       왜 하한인가: 진짜 정렬은 이 제약을 모두 만족하는 <정수> 해 하나이고,
       그 비용이 목적식과 정확히 같다. 정수 제약을 풀어 준 LP 의 최적값은 그보다
       클 수 없다 — 7부에서 분지한정의 하한을 얻던 논리 그대로다.

       실무의 A* 정렬 구현이 쓰는 표준 휴리스틱이며, "프로세스 마이닝 안에 LP 가
       들어 있다"는 이 교재의 주장을 가장 직접적으로 보여 주는 자리다.
    """
    from py import lp as _lp
    key = (petri._key(marking), tuple(sorted(_count(remaining).items())))
    if cache is not None and key in cache:
        return cache[key]

    places, trans, N = _incidence(net)
    labels = sorted({net.label_of(t) for t in trans if net.label_of(t) is not None})
    rem = _count(remaining)
    lab_idx = {a: i for i, a in enumerate(labels)}
    nt, nl = len(trans), len(labels)
    nv = nt + nl

    A_eq, b_eq = [], []
    for i, p in enumerate(places):
        row = [0.0] * nv
        for j in range(nt):
            row[j] = N[i][j]
        A_eq.append(row)
        b_eq.append(float(mf.get(p, 0) - marking.get(p, 0)))
    A_ub, b_ub = [], []
    for a in labels:
        row = [0.0] * nv                                 # s_a ≤ r_a
        row[nt + lab_idx[a]] = 1.0
        A_ub.append(row)
        b_ub.append(float(rem.get(a, 0)))
        row = [0.0] * nv                                 # s_a − Σ y_t ≤ 0
        row[nt + lab_idx[a]] = 1.0
        for j, t in enumerate(trans):
            if net.label_of(t) == a:
                row[j] = -1.0
        A_ub.append(row)
        b_ub.append(0.0)
    c = [0.0] * nv
    for j, t in enumerate(trans):
        c[j] = 1.0 if net.label_of(t) is not None else 0.0
    for a in labels:
        c[nt + lab_idx[a]] = -2.0

    r = _lp.solve_lp(c, A_ub=A_ub or None, b_ub=b_ub or None,
                     A_eq=A_eq, b_eq=b_eq)
    if r.status != 'optimal':
        val = float('inf')                               # 종료 마킹에 닿을 수 없다
    else:
        val = max(0.0, sum(rem.values()) + r.obj)
    if cache is not None:
        cache[key] = val
    return val


def _count(seq):
    d = {}
    for a in seq:
        d[a] = d.get(a, 0) + 1
    return d


def align_lp(net, m0, mf, trace, max_states=100000):
    """LP 휴리스틱을 쓰는 A* 정렬. align() 과 같은 비용을 내야 한다."""
    n = len(trace)
    cache = {}
    start = (0, petri._key(m0))
    markings = {start[1]: dict(m0)}
    dist = {start: 0}
    prev = {}
    pq = [(lp_heuristic(net, m0, mf, trace, cache), 0, start)]
    seen = 0
    while pq:
        f, g, state = heapq.heappop(pq)
        if g > dist.get(state, 1 << 30):
            continue
        seen += 1
        if seen > max_states:
            raise RuntimeError('탐색 상태가 너무 많다')
        i, mk = state
        m = markings[mk]
        if i == n and petri._covers(m, mf):
            return _rebuild(prev, state, g, seen)

        def push(nstate, cost, move, ii, mm):
            h = lp_heuristic(net, mm, mf, trace[ii:], cache)
            if h == float('inf'):
                return
            _push(pq, dist, prev, markings, nstate, g, cost, move, state, h)

        for t in net.enabled(m):
            lab = net.label_of(t)
            nm = net.fire(m, t)
            nk = petri._key(nm)
            markings.setdefault(nk, nm)
            if i < n and lab == trace[i]:
                push((i + 1, nk), 0, (SYNC_MOVE, trace[i], t), i + 1, nm)
            push((i, nk), 0 if lab is None else 1, (MODEL_MOVE, None, t), i, nm)
        if i < n:
            push((i + 1, mk), 1, (LOG_MOVE, trace[i], None), i + 1, m)
    raise RuntimeError('정렬을 찾지 못했다')
