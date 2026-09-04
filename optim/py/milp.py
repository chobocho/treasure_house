# -*- coding: utf-8 -*-
"""정수·조합 최적화 — 변수 하나가 정수여야 한다는 조건이 만드는 세계.

   6부에서 LP 는 모든 것이 잘 돌아가는 세계였다. 여기에 x ∈ ℤ 를 더하면
     · 실행가능집합이 볼록성을 잃는다 (2부 정의 5.1 의 반례)
     · 최적해가 꼭짓점에 있다는 보장이 사라진다
     · 문제가 NP-난해가 된다
   그럼에도 실무에서 풀린다. 이유는 연속 완화가 좋은 하한을 주기 때문이다.
   그 하한으로 탐색 공간을 잘라 내는 것이 분지한정이고, 이 부의 뼈대다.
"""
import itertools
import math

from py import linalg as la
from py import lp

INF = float('inf')


class MILPResult(object):
    def __init__(self, status, x=None, obj=None, nodes=0, gap=None, msg='', history=None):
        self.status = status
        self.x = x or []
        self.obj = obj
        self.nodes = nodes
        self.gap = gap
        self.msg = msg
        self.history = history or []

    def __repr__(self):
        return '<MILP %s obj=%s nodes=%d>' % (self.status, self.obj, self.nodes)


# ---------------------------------------------------------------- 분지한정

def branch_and_bound(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None,
                     integer=None, ub=None, tol=1e-7, maxnodes=20000,
                     keep_history=False):
    """모든(또는 지정한) 변수가 정수인 MILP 를 분지한정으로 푼다.

       한 마디에서 하는 일:
         1. LP 완화를 푼다 → 하한 z_LP 를 얻는다
         2. z_LP ≥ 현재까지의 최선(incumbent) 이면 가지치기 — 더 볼 필요가 없다
         3. 해가 전부 정수면 incumbent 를 갱신한다
         4. 아니면 분수인 변수 xⱼ 를 골라 xⱼ ≤ ⌊v⌋ 와 xⱼ ≥ ⌈v⌉ 두 가지로 쪼갠다

       가지치기가 얼마나 잘 되는지가 전부다. 그래서 좋은 하한(완화)과 좋은
       incumbent(초기 해)를 빨리 얻는 것이 실무의 핵심이다.

       탐색은 깊이 우선 — 메모리가 O(깊이) 로 끝나고 incumbent 를 빨리 찾는다.
    """
    n = len(c)
    integer = set(range(n)) if integer is None else set(integer)
    A_ub = [list(map(float, r)) for r in (A_ub or [])]
    b_ub = [float(v) for v in (b_ub or [])]
    A_eq = [list(map(float, r)) for r in (A_eq or [])]
    b_eq = [float(v) for v in (b_eq or [])]

    best_obj, best_x = INF, None
    nodes = 0
    hist = []
    # 스택 원소: (추가 상한 dict, 추가 하한 dict)
    stack = [({}, {} if ub is None else {})]
    if ub is not None:
        stack = [({j: float(ub[j]) for j in range(n)}, {})]

    while stack:
        if nodes >= maxnodes:
            return MILPResult('maxnodes', best_x, best_obj, nodes,
                              msg='마디 수 상한 도달', history=hist)
        upper, lower = stack.pop()
        nodes += 1
        rows = list(A_ub)
        rhs = list(b_ub)
        for j, v in upper.items():                       # xⱼ ≤ v
            rows.append([1.0 if k == j else 0.0 for k in range(n)])
            rhs.append(v)
        for j, v in lower.items():                       # −xⱼ ≤ −v
            rows.append([-1.0 if k == j else 0.0 for k in range(n)])
            rhs.append(-v)
        r = lp.solve_lp(c, A_ub=rows or None, b_ub=rhs or None,
                        A_eq=A_eq or None, b_eq=b_eq or None)
        if keep_history:
            hist.append({'node': nodes, 'status': r.status, 'bound': r.obj,
                         'incumbent': best_obj, 'depth': len(upper) + len(lower)})
        if r.status != 'optimal':
            continue                                     # 실행불가능·비유계 → 가지치기
        if r.obj >= best_obj - tol:
            continue                                     # 하한이 이미 나쁘다 → 가지치기
        frac = -1
        for j in sorted(integer):
            if abs(r.x[j] - round(r.x[j])) > tol:
                frac = j
                break
        if frac < 0:                                     # 전부 정수 — 새 incumbent
            best_obj, best_x = r.obj, [round(v) if j in integer else v
                                       for j, v in enumerate(r.x)]
            continue
        v = r.x[frac]
        lo = dict(lower); lo[frac] = math.ceil(v - tol)
        hi = dict(upper); hi[frac] = math.floor(v + tol)
        stack.append((upper, lo))                        # xⱼ ≥ ⌈v⌉
        stack.append((hi, lower))                        # xⱼ ≤ ⌊v⌋

    if best_x is None:
        return MILPResult('infeasible', nodes=nodes, msg='정수 실행가능해가 없다',
                          history=hist)
    return MILPResult('optimal', best_x, best_obj, nodes, gap=0.0, history=hist)


# ---------------------------------------------------------------- 배낭

def knapsack_dp(values, weights, cap):
    """0/1 배낭의 동적계획.  O(n·cap) 시간, O(cap) 공간.

       "의사 다항(pseudo-polynomial)" — 입력 크기가 아니라 수의 크기에
       비례한다. cap 이 2^64 이면 이 표를 만들 수 없다. NP-난해가 사라진 것이
       아니라 다른 곳으로 옮겨 간 것이다.
    """
    n = len(values)
    if n == 0 or cap <= 0:
        return 0, []
    dp = [0] * (cap + 1)
    keep = [[False] * (cap + 1) for _ in range(n)]
    for i in range(n):
        w, v = weights[i], values[i]
        for cpy in range(cap, w - 1, -1):            # 역순 — 각 물건을 한 번만 쓴다
            if dp[cpy - w] + v > dp[cpy]:
                dp[cpy] = dp[cpy - w] + v
                keep[i][cpy] = True
    pick, cpy = [], cap
    for i in range(n - 1, -1, -1):
        if keep[i][cpy]:
            pick.append(i)
            cpy -= weights[i]
    pick.reverse()
    return dp[cap], pick


def knapsack_lp_bound(values, weights, cap):
    """분수 배낭(LP 완화)의 최적값 — 정수 배낭의 상한.

       단위 가치가 큰 것부터 담고 마지막 하나를 쪼갠다는 탐욕이 최적이라는 것이
       고전적 결과다. 분지한정의 가지치기 한계로 그대로 쓸 수 있다.
    """
    order = sorted(range(len(values)), key=lambda i: -values[i] / float(weights[i]))
    rest, tot = cap, 0.0
    for i in order:
        if weights[i] <= rest:
            rest -= weights[i]
            tot += values[i]
        else:
            tot += values[i] * rest / float(weights[i])
            break
    return tot


# ---------------------------------------------------------------- 할당 (헝가리안)

def hungarian(cost, return_dual=False):
    """정방 비용행렬의 최소비용 완전매칭.  O(n³).

       구현은 잠재값(potential)을 쓰는 표준 형태다. u, v 는 각각 행·열의 쌍대변수이며
       u_i + v_j ≤ c_ij 라는 쌍대 실행가능성을 언제나 유지한다. 등호가 성립하는
       간선(tight edge)만으로 완전매칭이 만들어지는 순간이 최적이고, 그것이 곧
       상보여유(6부 정리 25.3)다. 즉 헝가리안 알고리즘은 LP 쌍대성을 조합적으로
       구현한 것이다.
    """
    n = len(cost)
    if any(len(row) != n for row in cost):
        raise ValueError('정방행렬이어야 한다')
    INF_ = INF
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)          # p[j] = j열에 배정된 행
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF_] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], INF_, 0
            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j], way[j] = cur, j0
                if minv[j] < delta:
                    delta, j1 = minv[j], j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    assign = [0] * n
    for j in range(1, n + 1):
        assign[p[j] - 1] = j - 1
    total = sum(cost[i][assign[i]] for i in range(n))
    if return_dual:
        # 잠재값을 원래 첨자로 되돌린다. 규약상 u[i] + v[j] <= c[i][j] 이고
        # 매칭된 간선에서는 등호가 성립한다(상보여유).
        du = [u[i + 1] for i in range(n)]
        dv = [v[j + 1] for j in range(n)]
        return total, assign, du, dv
    return total, assign


# ---------------------------------------------------------------- 최소비용흐름

def min_cost_flow(nv, edges, src, dst, need):
    """연속 최단경로법. edges = [(u, v, capacity, cost), …]

       매번 비용이 가장 싼 증가 경로를 찾아 가능한 만큼 흘린다. 잔여망에
       음수 비용 간선이 생기므로 Bellman–Ford 로 최단경로를 구한다(잠재값을 쓰면
       Dijkstra 로 바꿀 수 있다).

       왜 이것이 최적인가: 매 단계에서 흐름이 음수 비용 순환을 갖지 않도록
       유지되기 때문이다. 음수 순환이 없다는 것이 최적성의 필요충분조건이고,
       그 조건은 LP 쌍대성(상보여유)의 그래프판이다.
    """
    graph = [[] for _ in range(nv)]
    where = []                                          # 원래 간선 k 가 graph 의 어디에 있는가

    def add(u, v, cap, cost):
        where.append((u, len(graph[u])))
        graph[u].append([v, cap, cost, len(graph[v])])
        graph[v].append([u, 0, -cost, len(graph[u]) - 1])

    for (u, v, cap, cst) in edges:
        add(u, v, cap, cst)

    total, left = 0, need
    while left > 0:
        dist = [INF] * nv
        inq = [False] * nv
        prevv = [-1] * nv
        preve = [-1] * nv
        dist[src] = 0
        queue = [src]
        inq[src] = True
        while queue:                                    # Bellman–Ford (SPFA 형태)
            u = queue.pop(0)
            inq[u] = False
            for i, e in enumerate(graph[u]):
                v, cap, cst, _ = e
                if cap > 0 and dist[u] + cst < dist[v] - 1e-12:
                    dist[v] = dist[u] + cst
                    prevv[v], preve[v] = u, i
                    if not inq[v]:
                        queue.append(v)
                        inq[v] = True
        if dist[dst] == INF:
            raise ValueError('용량이 모자라 %d 단위를 보낼 수 없다' % need)
        d = left
        v = dst
        while v != src:
            d = min(d, graph[prevv[v]][preve[v]][1])
            v = prevv[v]
        left -= d
        total += d * dist[dst]
        v = dst
        while v != src:
            e = graph[prevv[v]][preve[v]]
            e[1] -= d
            graph[v][e[3]][1] += d
            v = prevv[v]

    # 잔여 용량에서 간선별 유량을 되읽는다 (입력 순서를 유지한다)
    flow = [edges[k][2] - graph[u][idx][1] for k, (u, idx) in enumerate(where)]
    return total, flow


# ---------------------------------------------------------------- 고모리 절단

def _frac(v):
    """소수부. 음수에서도 0 ≤ frac < 1 이 되도록 floor 를 쓴다."""
    return v - math.floor(v + 1e-12)


def gomory_cuts(c, A_ub, b_ub, rounds=1, tol=1e-7, maxcuts=20):
    """LP 완화에 고모리 분수 절단을 붙여 하한을 끌어올린다.

       착상: 최종 타블로의 한 행이  x_B(i) + Σ_{j∈N} ā_ij x_j = b̄_i  이고
       모든 x 가 정수라면, 계수를 내림하여

           x_B(i) + Σ ⌊ā_ij⌋ x_j ≤ b̄_i     (왼쪽은 정수, 오른쪽은 그렇지 않을 수 있다)

       가 성립하고, 좌변이 정수이므로 우변을 내림해도 된다. 두 식을 빼면

           Σ_{j∈N} frac(ā_ij) x_j ≥ frac(b̄_i)        ← 고모리 절단

       이 부등식은 <모든 정수 실행가능해>가 만족하지만 현재 LP 해는 어긴다
       (비기저 변수가 전부 0 이라 좌변이 0 인데 우변은 양수이므로). 그래서
       정수해를 하나도 잃지 않으면서 현재 분수해를 잘라 낸다.

       여기서는 절단을 표준형 변수(원 변수 + 슬랙)로 만든 뒤, 슬랙을
       s_i = b_i − a_iᵀx 로 되돌려 원 변수만의 부등식으로 바꾼다.

       반환: (마지막 LP 결과, 추가된 절단 목록, [(라운드별 하한, 누적 절단 수), …])
    """
    rows = [list(map(float, r)) for r in A_ub]
    rhs = [float(v) for v in b_ub]
    bounds = []
    cuts = []
    r = lp.solve_lp(c, A_ub=rows, b_ub=rhs, return_tableau=True)
    bounds.append((r.obj, 0))
    for _ in range(rounds):
        if r.status != 'optimal':
            break
        T, basis, nx, ntot = r.tableau, r.basis, r.nx, r.nvars
        m = len(T) - 1
        made = 0
        newrows = []
        for i in range(m):
            if basis[i] >= nx:                     # 기저가 슬랙이면 정수성 요구가 없다
                continue
            bi = T[i][-1]
            if _frac(bi) < tol or _frac(bi) > 1 - tol:
                continue
            # 표준형 변수(원 변수 + 슬랙)에 대한 절단: Σ_{j∈N} frac(ā_ij) z_j ≥ frac(b̄_i)
            f = [0.0] * ntot
            for j in range(ntot):
                if j in basis:
                    continue
                f[j] = _frac(T[i][j])
            f0 = _frac(bi)
            # 슬랙을 s_k = b_k − a_kᵀx 로 되돌려 원 변수만의 부등식으로 바꾼다.
            coef = [f[j] for j in range(nx)]
            rhs0 = f0
            for k in range(len(rows)):
                fk = f[nx + k]
                if fk == 0.0:
                    continue
                rhs0 -= fk * rhs[k]
                for j in range(nx):
                    coef[j] -= fk * rows[k][j]
            if all(abs(v) < tol for v in coef):
                continue
            newrows.append(([-v for v in coef], -rhs0))    # ≥ 를 ≤ 로 뒤집는다
            made += 1
            if made >= maxcuts:
                break
        if not newrows:
            break
        for row, b_ in newrows:
            rows.append(row)
            rhs.append(b_)
            cuts.append((row, b_))
        r = lp.solve_lp(c, A_ub=rows, b_ub=rhs, return_tableau=True)
        bounds.append((r.obj, len(cuts)))
    return r, cuts, bounds


# ---------------------------------------------------------------- 완전단모듈성

def is_totally_unimodular(A):
    """모든 정사각 부분행렬의 행렬식이 0, ±1 인가 — 정의 그대로 확인한다.

       지수 시간이라 작은 행렬에만 쓸 수 있다(다항 시간 판정법이 있지만 훨씬 복잡하다).
       그래도 "왜 어떤 LP 는 정수해를 공짜로 주는가"를 눈으로 확인하는 데는 충분하다.
    """
    m, n = len(A), len(A[0])
    for v in (val for row in A for val in row):
        if v not in (-1, 0, 1):
            return False
    for k in range(1, min(m, n) + 1):
        for rows in itertools.combinations(range(m), k):
            for cols in itertools.combinations(range(n), k):
                sub = [[float(A[i][j]) for j in cols] for i in rows]
                d = la.det(sub)
                if abs(d) > 1e-9 and abs(abs(d) - 1.0) > 1e-9:
                    return False
    return True
