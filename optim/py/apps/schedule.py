# -*- coding: utf-8 -*-
"""스케줄링 — 순서를 정하는 문제.

   두 가지를 다룬다.
     1. 단일 기계 가중 완료시간 최소화 — 정렬 규칙 하나로 <최적>이 증명된다
     2. 잡숍 makespan 최소화 — 순서 결정이 이진 변수가 되는 전형적인 MILP

   같은 '스케줄링'이라도 하나는 O(n log n) 이고 하나는 NP-난해다. 그 경계가
   어디서 생기는지 보는 것이 이 파일의 목적이다.
"""
import itertools

from py import milp


def wspt(jobs):
    """단일 기계에서 Σ wⱼ Cⱼ 를 최소화한다. jobs = [(이름, 처리시간 p, 가중치 w), …]

       정리: p/w 가 작은 순서(= w/p 가 큰 순서)로 처리하는 것이 최적이다.
       증명은 교환 논법이다 — 인접한 두 작업의 순서를 바꿔 보면 어느 쪽이 나은지
       바로 나온다(13부 51장에서 증명).

       O(n log n) — 정렬 한 번이면 끝난다.
    """
    order = sorted(jobs, key=lambda j: (j[1] / float(j[2]), j[0]))
    t = 0.0
    total = 0.0
    sched = []
    for (name, p, w) in order:
        t += p
        total += w * t
        sched.append((name, t))
    return sched, total


def brute_force_wspt(jobs):
    """모든 순열을 다 해 보는 기준 구현 — 정리를 검증하기 위한 것."""
    best, bord = None, None
    for perm in itertools.permutations(jobs):
        t, tot = 0.0, 0.0
        for (name, p, w) in perm:
            t += p
            tot += w * t
        if best is None or tot < best - 1e-12:
            best, bord = tot, perm
    return bord, best


def jobshop_milp(jobs, machines, bigM=None, maxnodes=20000):
    """잡숍 makespan 최소화를 MILP 로 적는다.

       jobs[j] = [(기계, 처리시간), …]  — 작업 j 의 공정 순서
       변수
           s[j][k] ≥ 0     작업 j 의 k번째 공정 시작 시각
           C ≥ 0           makespan
           z[(a,b)] ∈{0,1} 같은 기계 위의 두 공정 a, b 중 누가 먼저인가
       제약
           공정 순서:  s[j][k] + p ≤ s[j][k+1]
           기계 배타:  s[a] + p_a ≤ s[b] + M z,   s[b] + p_b ≤ s[a] + M(1−z)
           makespan:   s[j][마지막] + p ≤ C
       목적:  min C

       "둘 중 하나"라는 배타적 선택이 이진 변수 z 로 들어오는 것이 요점이다 —
       6부의 LP 로는 표현할 수 없고, 그래서 이 문제가 NP-난해가 된다.
    """
    ops = []                                   # (작업, 공정 index, 기계, 처리시간)
    for j, seq in enumerate(jobs):
        for k, (m, p) in enumerate(seq):
            ops.append((j, k, m, float(p)))
    nops = len(ops)
    pairs = [(a, b) for a in range(nops) for b in range(a + 1, nops)
             if ops[a][2] == ops[b][2] and ops[a][0] != ops[b][0]]
    n = nops + 1 + len(pairs)                  # s[…], C, z[…]
    ci = nops
    zi = nops + 1
    total_p = sum(o[3] for o in ops)
    M = bigM if bigM is not None else total_p + 1.0

    A_ub, b_ub = [], []

    def row():
        return [0.0] * n

    for j, seq in enumerate(jobs):             # 공정 순서
        idx = [i for i, o in enumerate(ops) if o[0] == j]
        idx.sort(key=lambda i: ops[i][1])
        for a, b in zip(idx, idx[1:]):
            r = row()
            r[a] = 1.0
            r[b] = -1.0
            A_ub.append(r)
            b_ub.append(-ops[a][3])
    for i, o in enumerate(ops):                # makespan
        r = row()
        r[i] = 1.0
        r[ci] = -1.0
        A_ub.append(r)
        b_ub.append(-o[3])
    for t, (a, b) in enumerate(pairs):         # 기계 배타 (big-M)
        r = row()
        r[a] = 1.0
        r[b] = -1.0
        r[zi + t] = -M
        A_ub.append(r)
        b_ub.append(-ops[a][3])
        r = row()
        r[b] = 1.0
        r[a] = -1.0
        r[zi + t] = M
        A_ub.append(r)
        b_ub.append(M - ops[b][3])
    for t in range(len(pairs)):                # z ≤ 1
        r = row()
        r[zi + t] = 1.0
        A_ub.append(r)
        b_ub.append(1.0)
    for i in range(nops + 1):                  # 시작시각·makespan 상한 (유계화)
        r = row()
        r[i] = 1.0
        A_ub.append(r)
        b_ub.append(total_p)

    c = [0.0] * n
    c[ci] = 1.0
    res = milp.branch_and_bound(c, A_ub=A_ub, b_ub=b_ub,
                                integer=list(range(zi, n)), maxnodes=maxnodes)
    if res.status != 'optimal':
        return res, None
    sched = []
    for i, (j, k, m, p) in enumerate(ops):
        sched.append({'job': j, 'op': k, 'machine': m,
                      'start': res.x[i], 'end': res.x[i] + p})
    sched.sort(key=lambda d: (d['machine'], d['start']))
    return res, {'makespan': res.x[ci], 'schedule': sched, 'nodes': res.nodes,
                 'binaries': len(pairs)}


def jobshop_brute(jobs, machines):
    """모든 기계별 순서 조합을 시도하는 기준 구현 (아주 작은 예제용)."""
    ops = []
    for j, seq in enumerate(jobs):
        for k, (m, p) in enumerate(seq):
            ops.append((j, k, m, float(p)))
    by_machine = {}
    for i, o in enumerate(ops):
        by_machine.setdefault(o[2], []).append(i)
    keys = sorted(by_machine)
    best = None
    for combo in itertools.product(*[itertools.permutations(by_machine[m])
                                     for m in keys]):
        order = {}
        for m, perm in zip(keys, combo):
            for pos, i in enumerate(perm):
                order[i] = pos
        mk = _simulate(ops, by_machine, keys, combo)
        if mk is not None and (best is None or mk < best):
            best = mk
    return best


def _simulate(ops, by_machine, keys, combo):
    """주어진 기계별 순서로 가장 이른 시작 시각을 계산한다. 교착이면 None."""
    start = [None] * len(ops)
    prev_on_machine = {}
    for m, perm in zip(keys, combo):
        for a, b in zip(perm, perm[1:]):
            prev_on_machine[b] = a
    prev_in_job = {}
    for i, o in enumerate(ops):
        for k, o2 in enumerate(ops):
            if o2[0] == o[0] and o2[1] == o[1] - 1:
                prev_in_job[i] = k
    done = set()
    for _ in range(len(ops) + 1):
        progress = False
        for i in range(len(ops)):
            if i in done:
                continue
            deps = [d for d in (prev_on_machine.get(i), prev_in_job.get(i))
                    if d is not None]
            if all(d in done for d in deps):
                start[i] = max([0.0] + [start[d] + ops[d][3] for d in deps])
                done.add(i)
                progress = True
        if len(done) == len(ops):
            return max(start[i] + ops[i][3] for i in range(len(ops)))
        if not progress:
            return None
    return None
